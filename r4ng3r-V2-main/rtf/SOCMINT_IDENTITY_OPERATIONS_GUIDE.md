# SOCMINT / Identity Investigation Operations Guide v2.0

This guide expands the `osint/identity_fusion` operating model and is intended for analysts running authorized identity-centric investigations, attribution support, exposure discovery, or cross-platform entity correlation.

## Recommended use cases

Use this playbook when you need to:

- pivot from a seed username, email, phone number, full name, or domain
- correlate online identities across multiple platforms
- enrich a lead with breach, code, metadata, and domain intelligence
- produce a structured report for an internal investigation or authorized client engagement

## Pre-engagement checklist

Before starting an investigation:

1. Confirm written authorization and scope boundaries.
2. Define the primary seed(s): username, email, phone, name, domain, or profile URL.
3. Decide whether you want a **fast**, **balanced**, or **aggressive** collection profile.
4. Decide whether AI correlation should be enabled.
5. Choose the desired report format: JSON, CSV, XLSX, PDF, or HTML.
6. Validate the availability of high-value tools and API keys.

## Pipeline Stages

### Stage A — Seed & Baseline
Input one or more seeds: username, email, full name, phone, domain.

**Goal:** normalize identity anchors before pivots begin.

### Stage B — Username Sweep (14+ tools)
sherlock, maigret, nexfil, blackbird, socialscan, whatsmyname, social-analyzer,
checkusernames, namechk, snoop, username-anarchy, osrframework, seekr, profil3r,
peekyou-cli, usersearch, sherlock-project

**Goal:** identify likely accounts and naming patterns across platforms.

### Stage C — Email Pivot & Breach (9 tools)
holehe, h8mail, emailrep, ignorant, dehashed-cli, breach-parse, emailfinder,
haveibeenpwned, h8mail (local breach)

**Goal:** determine account registrations, breach exposure, and email reputation.

### Stage D — Social Media Deep Dive (9 tools)
instaloader, toutatis, twint, tinfoleak, socid-extractor, osintgram,
twscrape, snscrape, reddit-user-analyser

**Goal:** pull profile metadata, posting context, linked accounts, and social clues.

### Stage E — Domain & Name Intelligence (20+ tools)
theHarvester, spiderfoot, metagoofil, dnstwist, linkedin2username, crosslinked,
photon, recon-ng, sublist3r, subfinder, gau, waybackurls, amass, dnsdumpster,
spyonweb, onyphe, netlas, fullhunt, zoomeye, shodan, censys, urlscan, wigle

**Goal:** pivot from identities into infrastructure, employer, and organizational context.

### Stage F — Code/Secrets Forensics (7 tools)
gitfive, octosuite, trufflehog, gitleaks, gitrecon, gharchive, intelowl

**Goal:** locate developer footprints, public repositories, exposed secrets, or commit-linked identities.

### Stage G — Phone OSINT (2 tools)
phoneinfoga, email2phonenumber

**Goal:** enrich phone-based pivots where lawful and in-scope.

### Stage H — Dark Web & Breach (4 tools)
intelx, pwndb-cli, dehashed, skymem

**Goal:** identify historical exposures, aliases, and breach-linked artifacts.

### Stage I — Geolocation/Metadata (22 tools)
creepy, waybackpack, ghunt, sn0int, buster, osintgram, exiftool, foca, maltego,
recon-ng, archivebox, phantombuster, harpoon, cybelangel, tineye, netlytic,
social-searcher, mentionmapp, clearbit, fullcontact, pipl, linky-lady, shlink, hunter, waymore

**Goal:** surface metadata, location clues, historic content, and media-derived context.

### Stage J — Claude AI Correlation
Automated analysis of all gathered entities using Claude `claude-sonnet-4-20250514`.
Produces: confidence score, identity summary, cross-platform connections,
anomalies, risk assessment, next investigative steps.

**Goal:** synthesize fragmented evidence into a prioritized analyst narrative.

### Stage K — Multi-Format Report
JSON / CSV / XLSX / PDF / HTML with auto-fallback chain.

**Goal:** produce deliverables that can be reviewed, archived, or passed to stakeholders.

## Operating profiles

### Fast
Use when you need a quick validation pass and minimal external lookups.

### Balanced
Use for standard investigations where you want breadth without maximum collection cost.

### Aggressive
Use when scope allows deeper scraping, more pivots, and higher collection time.

## Example commands

```bash
# Core investigation (fast)
python rtf.py module run osint/identity_fusion   --options '{"username":"target","output_format":"json"}'

# Full aggressive with AI
python rtf.py module run osint/identity_fusion   --options '{"username":"target","email":"t@example.com","domain":"example.com","tool_profile":"aggressive","use_ai":true,"output_format":"html"}'

# Via workflow
python rtf.py workflow run identity_fusion   --options '{"username":"target","output_format":"xlsx"}'
```

## Suggested investigation flow

1. Start with the strongest available seed.
2. Run a username and email pivot first.
3. Confirm likely matches before escalating to deep scraping.
4. Expand into domain, code, and metadata pivots only where they add investigative value.
5. Use AI correlation after collecting enough entities to avoid low-signal summaries.
6. Export a report and manually review confidence before distribution.

## Output review checklist

Review the final report for:

- duplicate identities or false-positive joins
- recycled usernames belonging to different people
- stale breach data that may no longer be relevant
- unsupported AI inferences that need analyst confirmation
- sensitive material that should be redacted before sharing

## Related documentation

- `README.md` for the overall project overview and quick start
- `rtf/USER_GUIDE.md` for CLI, workflow, API, dashboard, and reporting details
