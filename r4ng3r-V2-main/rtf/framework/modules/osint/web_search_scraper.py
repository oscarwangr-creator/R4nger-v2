"""
RedTeam Framework v2.0 - Module: osint/web_search_scraper
Multi-Engine Web Search & Result Scraper

Searches for a target name/username/email across:
  - DuckDuckGo (HTML scraping - no key required)
  - Bing       (HTML scraping - no key required)
  - Google     (HTML scraping with rotating UA / optional CSE API key)
  - Brave      (HTML scraping / optional Search API key)
  - Yahoo      (HTML scraping)
  - Yandex     (HTML scraping)
  - StartPage  (Google proxy, no tracking)

For each result the scraper also optionally fetches and parses the target page
to extract profile data (bio, emails, phones, social links, metadata).

Used by identity_fusion Stage B3 but also runnable standalone.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus, urljoin, urlparse

from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

# ─────────────────────────────────────────────────────────────────────────────
# User-agent pool  (rotate to reduce blocks)
# ─────────────────────────────────────────────────────────────────────────────

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

_ua_index = 0

def _next_ua() -> str:
    global _ua_index
    ua = USER_AGENTS[_ua_index % len(USER_AGENTS)]
    _ua_index += 1
    return ua


# ─────────────────────────────────────────────────────────────────────────────
# Search result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    engine:   str
    query:    str
    rank:     int
    title:    str
    url:      str
    snippet:  str = ""
    # filled after optional page fetch
    page_fetched: bool = False
    page_emails:  List[str] = field(default_factory=list)
    page_phones:  List[str] = field(default_factory=list)
    page_social:  List[str] = field(default_factory=list)
    page_meta_desc: str = ""
    page_title:  str = ""
    error:       str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


# ─────────────────────────────────────────────────────────────────────────────
# Per-engine scrape config
# ─────────────────────────────────────────────────────────────────────────────

EMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE  = re.compile(r"\+?[\d\-\(\)\s]{9,20}")
SOCIAL_RE = re.compile(
    r"https?://(?:www\.)?(?:twitter|x|instagram|github|linkedin|facebook|"
    r"tiktok|youtube|reddit|mastodon|twitch|telegram)\.(?:com|org|tv|io)/[^\s\"'<>]{2,60}"
)

# Strip HTML tags
_TAG_RE = re.compile(r"<[^>]+>")

def _strip(text: str) -> str:
    return _TAG_RE.sub(" ", text).strip()

def _decode_entities(text: str) -> str:
    return (text.replace("&amp;", "&").replace("&lt;","<").replace("&gt;",">")
                .replace("&quot;",'"').replace("&#39;","'").replace("&nbsp;"," "))


# ─────────────────────────────────────────────────────────────────────────────
# Engine scrapers
# ─────────────────────────────────────────────────────────────────────────────

async def _scrape_duckduckgo(query: str, num: int, timeout: int) -> List[SearchResult]:
    """DuckDuckGo HTML scrape — most reliable, no API key needed."""
    results: List[SearchResult] = []
    try:
        import httpx
        headers = {
            "User-Agent": _next_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
        }
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return results
            html = resp.text
            # DDG HTML results: <div class="result__body">
            # Links: <a class="result__a" href="...">title</a>
            # Snippet: <a class="result__snippet">...</a>
            link_re   = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
            snip_re   = re.compile(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', re.DOTALL)
            links   = link_re.findall(html)
            snippets= snip_re.findall(html)
            for i, (href, title) in enumerate(links[:num]):
                snippet = snippets[i] if i < len(snippets) else ""
                # DDG returns redirect URLs — extract real URL
                real_url = href
                uddg_match = re.search(r"uddg=([^&]+)", href)
                if uddg_match:
                    from urllib.parse import unquote
                    real_url = unquote(uddg_match.group(1))
                results.append(SearchResult(
                    engine="duckduckgo", query=query, rank=i+1,
                    title=_decode_entities(_strip(title)).strip(),
                    url=real_url,
                    snippet=_decode_entities(_strip(snippet))[:300],
                ))
    except Exception as exc:
        pass  # Graceful degradation — return whatever we have
    return results


async def _scrape_bing(query: str, num: int, timeout: int) -> List[SearchResult]:
    """Bing HTML scrape."""
    results: List[SearchResult] = []
    try:
        import httpx
        headers = {
            "User-Agent": _next_ua(),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Cookie": "SRCHD=AF=NOFORM; SRCHUID=V=2; SRCHUSR=DOB=20200101",
        }
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count={min(num, 50)}&setlang=en"
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return results
            html = resp.text
            # Bing result blocks: <li class="b_algo">
            block_re = re.compile(r'<li[^>]+class="b_algo"[^>]*>(.*?)</li>', re.DOTALL)
            title_re = re.compile(r'<h2[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
            snip_re  = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL)
            blocks = block_re.findall(html)
            for i, block in enumerate(blocks[:num]):
                tm = title_re.search(block)
                if not tm:
                    continue
                href  = tm.group(1)
                title = _decode_entities(_strip(tm.group(2))).strip()
                sm    = snip_re.search(block)
                snip  = _decode_entities(_strip(sm.group(1)))[:300] if sm else ""
                results.append(SearchResult(
                    engine="bing", query=query, rank=i+1,
                    title=title, url=href, snippet=snip,
                ))
    except Exception:
        pass
    return results


async def _scrape_brave(query: str, num: int, timeout: int, api_key: str = "") -> List[SearchResult]:
    """Brave Search — API if key provided, else HTML scrape."""
    results: List[SearchResult] = []
    try:
        import httpx
        if api_key:
            # Official Brave Search API
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            }
            url = f"https://api.search.brave.com/res/v1/web/search?q={quote_plus(query)}&count={min(num,20)}"
            async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for i, item in enumerate(data.get("web", {}).get("results", [])[:num]):
                        results.append(SearchResult(
                            engine="brave", query=query, rank=i+1,
                            title=item.get("title",""),
                            url=item.get("url",""),
                            snippet=item.get("description","")[:300],
                        ))
                    return results
        # HTML scrape fallback
        headers = {
            "User-Agent": _next_ua(),
            "Accept": "text/html,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        url = f"https://search.brave.com/search?q={quote_plus(query)}&source=web"
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return results
            html = resp.text
            # Brave result format: <div class="snippet"> containing <a class="result-header">
            block_re = re.compile(r'<div[^>]+class="[^"]*snippet[^"]*"[^>]*>(.*?)</div>', re.DOTALL)
            title_re = re.compile(r'<span[^>]+class="[^"]*snippet-title[^"]*"[^>]*>(.*?)</span>', re.DOTALL)
            url_re   = re.compile(r'href="(https?://[^"]+)"')
            snip_re  = re.compile(r'<p[^>]+class="[^"]*snippet-description[^"]*"[^>]*>(.*?)</p>', re.DOTALL)
            blocks = block_re.findall(html)
            rank = 1
            for block in blocks[:num]:
                tm = title_re.search(block)
                um = url_re.search(block)
                sm = snip_re.search(block)
                if tm and um:
                    results.append(SearchResult(
                        engine="brave", query=query, rank=rank,
                        title=_decode_entities(_strip(tm.group(1))).strip(),
                        url=um.group(1),
                        snippet=_decode_entities(_strip(sm.group(1)))[:300] if sm else "",
                    ))
                    rank += 1
    except Exception:
        pass
    return results


async def _scrape_google(query: str, num: int, timeout: int, api_key: str = "", cx: str = "") -> List[SearchResult]:
    """Google — Custom Search API if keys provided, else HTML scrape."""
    results: List[SearchResult] = []
    try:
        import httpx
        if api_key and cx:
            # Official Google Custom Search API
            url = (f"https://www.googleapis.com/customsearch/v1"
                   f"?q={quote_plus(query)}&key={api_key}&cx={cx}&num={min(num,10)}")
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for i, item in enumerate(data.get("items", [])[:num]):
                        results.append(SearchResult(
                            engine="google", query=query, rank=i+1,
                            title=item.get("title",""),
                            url=item.get("link",""),
                            snippet=item.get("snippet","")[:300],
                        ))
                    return results
        # HTML scrape fallback (note: Google actively blocks scrapers)
        headers = {
            "User-Agent": _next_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Referer": "https://www.google.com/",
        }
        url = f"https://www.google.com/search?q={quote_plus(query)}&num={min(num,20)}&hl=en&gl=us"
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True,
                                      verify=False) as client:
            await asyncio.sleep(1.0)  # Rate-limit politeness delay
            resp = await client.get(url)
            if resp.status_code != 200:
                return results
            html = resp.text
            # Google result blocks: <div class="g"> or <div data-sokoban-container>
            # Multiple patterns for different Google HTML versions
            patterns = [
                re.compile(r'<div[^>]+class="[^"]*?(?:\bg\b)[^"]*?"[^>]*>(.*?)</div>\s*</div>', re.DOTALL),
                re.compile(r'<div[^>]+data-sokoban-container[^>]*>(.*?)</div>', re.DOTALL),
            ]
            title_re  = re.compile(r'<h3[^>]*>(.*?)</h3>', re.DOTALL)
            url_re    = re.compile(r'<a[^>]+href="(/url\?q=|https?://[^"]+)"')
            snip_re   = re.compile(r'<span[^>]+class="[^"]*(?:st|aCOpRe|MUxGbd)[^"]*"[^>]*>(.*?)</span>', re.DOTALL)
            rank = 1
            for pat in patterns:
                blocks = pat.findall(html)
                for block in blocks[:num]:
                    tm = title_re.search(block)
                    um = url_re.search(block)
                    sm = snip_re.search(block)
                    if tm and um:
                        href = um.group(1)
                        # Handle /url?q= redirects
                        if href.startswith("/url?q="):
                            from urllib.parse import unquote
                            href = unquote(href[7:].split("&")[0])
                        if href.startswith("http"):
                            results.append(SearchResult(
                                engine="google", query=query, rank=rank,
                                title=_decode_entities(_strip(tm.group(1))).strip(),
                                url=href,
                                snippet=_decode_entities(_strip(sm.group(1)))[:300] if sm else "",
                            ))
                            rank += 1
                if results:
                    break
    except Exception:
        pass
    return results


async def _scrape_yahoo(query: str, num: int, timeout: int) -> List[SearchResult]:
    """Yahoo Search HTML scrape."""
    results: List[SearchResult] = []
    try:
        import httpx
        headers = {
            "User-Agent": _next_ua(),
            "Accept": "text/html,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        url = f"https://search.yahoo.com/search?p={quote_plus(query)}&n={min(num,30)}"
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return results
            html = resp.text
            block_re = re.compile(r'<div[^>]+class="[^"]*algo[^"]*"[^>]*>(.*?)</li>', re.DOTALL)
            title_re = re.compile(r'<h3[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
            snip_re  = re.compile(r'<p[^>]+class="[^"]*lh-16[^"]*"[^>]*>(.*?)</p>', re.DOTALL)
            blocks = block_re.findall(html)
            for i, block in enumerate(blocks[:num]):
                tm = title_re.search(block)
                if not tm:
                    continue
                href  = tm.group(1)
                # Yahoo redirect: /ru=...
                ru_match = re.search(r"/ru=([^/]+)/", href)
                if ru_match:
                    from urllib.parse import unquote
                    href = unquote(ru_match.group(1))
                sm   = snip_re.search(block)
                results.append(SearchResult(
                    engine="yahoo", query=query, rank=i+1,
                    title=_decode_entities(_strip(tm.group(2))).strip(),
                    url=href,
                    snippet=_decode_entities(_strip(sm.group(1)))[:300] if sm else "",
                ))
    except Exception:
        pass
    return results


async def _scrape_startpage(query: str, num: int, timeout: int) -> List[SearchResult]:
    """StartPage (Google proxy, privacy-respecting)."""
    results: List[SearchResult] = []
    try:
        import httpx
        headers = {
            "User-Agent": _next_ua(),
            "Accept": "text/html,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        url = f"https://www.startpage.com/search?q={quote_plus(query)}&num={min(num,10)}"
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return results
            html = resp.text
            block_re = re.compile(r'<div[^>]+class="[^"]*w-gl__result[^"]*"[^>]*>(.*?)</div>\s*</div>', re.DOTALL)
            title_re = re.compile(r'<a[^>]+class="[^"]*result-title[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
            snip_re  = re.compile(r'<p[^>]+class="[^"]*description[^"]*"[^>]*>(.*?)</p>', re.DOTALL)
            blocks = block_re.findall(html)
            for i, block in enumerate(blocks[:num]):
                tm = title_re.search(block)
                if not tm:
                    continue
                sm = snip_re.search(block)
                results.append(SearchResult(
                    engine="startpage", query=query, rank=i+1,
                    title=_decode_entities(_strip(tm.group(2))).strip(),
                    url=tm.group(1),
                    snippet=_decode_entities(_strip(sm.group(1)))[:300] if sm else "",
                ))
    except Exception:
        pass
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Page fetcher — scrape individual result URLs for extra data
# ─────────────────────────────────────────────────────────────────────────────

async def _fetch_result_page(result: SearchResult, timeout: int) -> SearchResult:
    """Fetch a search result URL and extract emails, phones, social links."""
    try:
        import httpx
        headers = {"User-Agent": _next_ua(), "Accept": "text/html,*/*;q=0.8"}
        async with httpx.AsyncClient(timeout=timeout, headers=headers,
                                      follow_redirects=True, verify=False) as client:
            resp = await client.get(result.url)
            if resp.status_code != 200:
                result.error = f"HTTP {resp.status_code}"
                return result
            html = resp.text[:60000]
            result.page_fetched   = True
            result.page_emails    = list(dict.fromkeys(EMAIL_RE.findall(html)))[:10]
            result.page_phones    = list(dict.fromkeys(
                p.strip() for p in PHONE_RE.findall(html)
                if len(re.sub(r"\D","",p)) >= 8
            ))[:5]
            result.page_social    = list(dict.fromkeys(SOCIAL_RE.findall(html)))[:15]
            # Meta description
            meta_m = re.search(
                r'<meta[^>]+(?:name|property)=["\']description["\'][^>]+content=["\']([^"\']{10,300})["\']',
                html, re.I
            )
            if meta_m:
                result.page_meta_desc = _decode_entities(meta_m.group(1)).strip()
            # Page title
            title_m = re.search(r"<title[^>]*>([^<]{3,150})</title>", html, re.I)
            if title_m:
                result.page_title = _decode_entities(title_m.group(1)).strip()
    except Exception as exc:
        result.error = str(exc)[:100]
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Main WebSearchScraperModule
# ─────────────────────────────────────────────────────────────────────────────

class WebSearchScraperModule(BaseModule):
    """
    Search multiple engines (DuckDuckGo, Bing, Brave, Google, Yahoo, StartPage)
    for a target name/username/email and optionally scrape each result page.
    """

    def info(self) -> Dict[str, Any]:
        return {
            "name": "web_search_scraper",
            "description": (
                "Multi-engine web search & page scraper: search Google, Bing, Brave, "
                "DuckDuckGo, Yahoo, and StartPage for a target. Optionally scrape "
                "each result page for emails, phones, and social links."
            ),
            "author": "RTF Core Team",
            "category": "osint",
            "version": "1.0",
            "tags": ["osint", "search", "scraping", "google", "bing", "duckduckgo"],
        }

    def _declare_options(self) -> None:
        self._register_option("query",        "Search query (name, username, email, phrase)", required=True)
        self._register_option("engines",      "Comma-separated: duckduckgo,bing,brave,google,yahoo,startpage",
                              required=False, default="duckduckgo,bing,brave")
        self._register_option("results_per_engine", "Results per engine",    required=False, default=10, type=int)
        self._register_option("fetch_pages",  "Scrape each result page",     required=False, default=False, type=bool)
        self._register_option("max_fetch",    "Max result pages to scrape",  required=False, default=5,  type=int)
        self._register_option("timeout",      "HTTP timeout per request",    required=False, default=20, type=int)
        self._register_option("delay",        "Delay between engine requests (seconds)",
                              required=False, default=1.5, type=float)
        self._register_option("output_file",  "Save JSON results to file",   required=False, default="")
        self._register_option("google_api_key","Google CSE API key (optional)",  required=False, default="")
        self._register_option("google_cx",    "Google CSE CX ID (optional)",     required=False, default="")
        self._register_option("brave_api_key","Brave Search API key (optional)", required=False, default="")
        self._register_option("deduplicate",  "Remove duplicate URLs across engines", required=False, default=True, type=bool)

    async def run(self) -> ModuleResult:
        query     = self.get("query")
        engines   = [e.strip().lower() for e in self.get("engines").split(",") if e.strip()]
        num       = self.get("results_per_engine")
        fetch     = self.get("fetch_pages")
        max_fetch = self.get("max_fetch")
        timeout   = self.get("timeout")
        delay     = self.get("delay")
        out_file  = self.get("output_file")
        dedup     = self.get("deduplicate")
        google_key= self.get("google_api_key")
        google_cx = self.get("google_cx")
        brave_key = self.get("brave_api_key")

        all_results: List[SearchResult] = []
        engine_stats: Dict[str, int] = {}

        # Run engines sequentially with delay to avoid rate-limits
        engine_funcs = {
            "duckduckgo": lambda: _scrape_duckduckgo(query, num, timeout),
            "bing":        lambda: _scrape_bing(query, num, timeout),
            "brave":       lambda: _scrape_brave(query, num, timeout, brave_key),
            "google":      lambda: _scrape_google(query, num, timeout, google_key, google_cx),
            "yahoo":       lambda: _scrape_yahoo(query, num, timeout),
            "startpage":   lambda: _scrape_startpage(query, num, timeout),
        }

        for engine in engines:
            fn = engine_funcs.get(engine)
            if not fn:
                self.log.warning(f"Unknown engine: {engine}")
                continue
            self.log.info(f"  Searching {engine} for: {query!r}")
            try:
                results = await fn()
                engine_stats[engine] = len(results)
                all_results.extend(results)
                self.log.info(f"  {engine}: {len(results)} results")
            except Exception as exc:
                self.log.warning(f"  {engine} error: {exc}")
                engine_stats[engine] = 0
            if delay > 0:
                await asyncio.sleep(delay)

        # Deduplicate by URL
        if dedup:
            seen_urls: Set[str] = set()
            deduped: List[SearchResult] = []
            for r in all_results:
                norm = r.url.rstrip("/").lower()
                if norm not in seen_urls:
                    seen_urls.add(norm)
                    deduped.append(r)
            all_results = deduped

        # Optionally fetch individual pages
        if fetch and all_results:
            to_fetch = all_results[:max_fetch]
            self.log.info(f"  Fetching {len(to_fetch)} result pages…")
            sem = asyncio.Semaphore(4)
            async def _fetch_guarded(r: SearchResult) -> SearchResult:
                async with sem:
                    return await _fetch_result_page(r, timeout)
            fetched = await asyncio.gather(*[_fetch_guarded(r) for r in to_fetch])
            for orig, upd in zip(to_fetch, fetched):
                idx = all_results.index(orig)
                all_results[idx] = upd

        # Aggregate extracted data across all results
        all_emails: List[str] = []
        all_phones: List[str] = []
        all_social: List[str] = []
        for r in all_results:
            all_emails.extend(r.page_emails)
            all_phones.extend(r.page_phones)
            all_social.extend(r.page_social)
        all_emails = list(dict.fromkeys(all_emails))
        all_phones = list(dict.fromkeys(all_phones))
        all_social = list(dict.fromkeys(all_social))

        output = {
            "query": query,
            "engines_used": engines,
            "engine_stats": engine_stats,
            "total_results": len(all_results),
            "deduplicated": dedup,
            "results": [r.to_dict() for r in all_results],
            "aggregated": {
                "emails": all_emails,
                "phones": all_phones,
                "social_links": all_social,
                "unique_domains": list(dict.fromkeys(
                    urlparse(r.url).netloc for r in all_results if r.url
                ))[:30],
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

        if out_file:
            Path(out_file).parent.mkdir(parents=True, exist_ok=True)
            Path(out_file).write_text(json.dumps(output, indent=2), encoding="utf-8")

        # Build findings
        findings: List[Finding] = []
        for r in all_results[:30]:
            findings.append(self.make_finding(
                title=f"Search result [{r.engine}]: {r.title[:60]}",
                target=query,
                severity=Severity.INFO,
                description=f"{r.snippet[:200]}",
                evidence={"url": r.url, "engine": r.engine, "rank": r.rank,
                          "emails": r.page_emails, "social": r.page_social},
                tags=["osint", "web_search", r.engine],
            ))
        for email in all_emails:
            findings.append(self.make_finding(
                title=f"Email found in search results: {email}",
                target=query,
                severity=Severity.LOW,
                description=f"Email address scraped from web search results for: {query}",
                evidence={"email": email},
                tags=["osint", "email", "web_search"],
            ))

        self.log.info(
            f"Web search complete: {len(all_results)} results from {len(engines)} engines | "
            f"{len(all_emails)} emails | {len(all_social)} social links"
        )
        return ModuleResult(success=True, output=output, findings=findings)
