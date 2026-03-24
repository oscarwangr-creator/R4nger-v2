"""
RTF v2.0 — Reports: HTML Reporter (full implementation)
Generates a self-contained single-file HTML report.
"""
from __future__ import annotations
import html as html_lib, json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

SEV_ORDER  = {"critical":0,"high":1,"medium":2,"low":3,"info":4}
SEV_COLORS = {"critical":"#dc2626","high":"#ea580c","medium":"#d97706","low":"#65a30d","info":"#0284c7"}
SEV_BG     = {"critical":"#fef2f2","high":"#fff7ed","medium":"#fffbeb","low":"#f0fdf4","info":"#eff6ff"}
SEV_BADGE  = {"critical":"🔴","high":"🟠","medium":"🟡","low":"🟢","info":"🔵"}
MITRE_MAP  = {
    "recon":"TA0043","scan":"TA0007","osint":"TA0043","web":"TA0001",
    "sqli":"T1190","xss":"T1059.007","cred":"TA0006","privesc":"TA0004",
    "lateral":"TA0008","exfil":"TA0010","ad":"T1558","cloud":"T1580",
    "crypto":"T1110","wireless":"T1557",
}
_E = html_lib.escape

class HtmlReporter:
    def generate(self, data: Dict[str, Any], output_path: str) -> str:
        p = Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
        findings = data.get("findings", [])
        target   = _E(str(data.get("target","")))
        profile  = _E(str(data.get("profile","")))
        pid      = _E(str(data.get("pipeline_id","")))
        gen_at   = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        operator = _E(str(data.get("operator","RTF")))
        entities = data.get("entities", {})
        stages   = data.get("stage_results", {})
        ai_anal  = data.get("ai_analysis", {})
        attack_ps= data.get("attack_paths", [])

        findings_sorted = sorted(findings, key=lambda f: SEV_ORDER.get(str(f.get("severity","info")).lower(),4))
        by_sev = {s:0 for s in SEV_ORDER}
        for f in findings:
            s = str(f.get("severity","info")).lower()
            by_sev[s] = by_sev.get(s,0)+1
        risk_score = by_sev["critical"]*10+by_sev["high"]*5+by_sev["medium"]*2+by_sev["low"]
        risk_color = "#dc2626" if risk_score>=20 else "#ea580c" if risk_score>=10 else "#d97706" if risk_score>=5 else "#65a30d"
        mitre_hits = {}
        for f in findings:
            for tag in f.get("tags",[]):
                for kw,tid in MITRE_MAP.items():
                    if kw in str(tag).lower(): mitre_hits[tid]=kw

        rows = ""
        for i,f in enumerate(findings_sorted):
            sev=str(f.get("severity","info")).lower()
            col=SEV_COLORS.get(sev,"#6b7280"); badge=SEV_BADGE.get(sev,"⚪")
            title=_E(str(f.get("title",""))[:120]); tgt=_E(str(f.get("target","")))
            desc=_E(str(f.get("description",""))[:400])
            tags="".join(f'<span class="tag">{_E(str(t))}</span>' for t in f.get("tags",[])[:5])
            ev=f.get("evidence",{}); ev_str=_E(json.dumps(ev,default=str)[:300]) if ev else ""
            rows+=f"""<tr onclick="t({i})" style="cursor:pointer"><td><span class="badge" style="background:{col}20;color:{col}">{badge} {sev.upper()}</span></td><td><strong>{title}</strong><br><small class="dim">{tgt}</small></td><td>{tags}</td></tr>
<tr id="d{i}" style="display:none"><td colspan=3 style="background:#1e293b;padding:12px 20px"><p>{desc}</p>{f"<p><code>{ev_str}</code></p>" if ev_str else ""}</td></tr>"""

        ent_html="".join(f'<div class="eg"><h4>{_E(k.title())}</h4><ul>{"".join(f"<li>{_E(str(v))}</li>" for v in list(vs)[:30])}</ul></div>' for k,vs in entities.items() if vs)
        srows="".join(f'<tr><td><b>Stage {_E(sid)}</b></td><td>{"✅" if isinstance(sd,dict) and sd.get("success",True) else "⚠️"}</td><td>{_E(str(sd)[:80])}</td></tr>' for sid,sd in stages.items())
        mtags="".join(f'<span class="mtag">{_E(tid)}</span>' for tid in mitre_hits) or '<span class="dim">None</span>'
        total=max(sum(by_sev.values()),1)
        sbars="".join(f'<div class="sr"><span class="sl">{sev.upper()}</span><div class="sb"><div style="width:{int(c*100/total)}%;background:{SEV_COLORS[sev]};height:100%;border-radius:7px"></div></div><span style="color:{SEV_COLORS[sev]};width:30px;text-align:right;font-weight:700">{c}</span></div>' for sev,c in by_sev.items())
        ai_html=""
        if ai_anal:
            conf=ai_anal.get("confidence_score","N/A"); rl=_E(str(ai_anal.get("risk_level","")))
            summ=_E(str(ai_anal.get("executive_summary",ai_anal.get("identity_summary","")))[:500])
            pivs="".join(f"<li>{_E(str(p))}</li>" for p in ai_anal.get("top_pivots",[])[:5])
            ai_html=f'<div class="card"><h2>🤖 AI Analysis</h2><p>Confidence: <b>{conf}/100</b> &nbsp; Risk: <b style="color:{risk_color}">{rl}</b></p><p>{summ}</p>{"<ul>"+pivs+"</ul>" if pivs else ""}</div>'
        ap_html="".join(f'<div class="ap">{"→".join(f"<span class=\"step\">{_E(str(s))}</span>" for s in ap.get("steps",[]))}</div>' for ap in attack_ps[:5])

        html_out = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>RTF Report — {target}</title>
<style>:root{{--bg:#0f172a;--card:#1e293b;--bd:#334155;--tx:#f1f5f9;--dm:#94a3b8}}*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--tx);font-size:14px;line-height:1.6}}.hdr{{background:linear-gradient(135deg,#1e3a5f,#0f172a);padding:32px 40px;border-bottom:2px solid var(--bd)}}.hdr h1{{font-size:1.8rem;font-weight:800}}.meta{{color:var(--dm);font-size:.85rem;margin-top:6px}}.nav{{position:sticky;top:0;background:#0f172a;border-bottom:1px solid var(--bd);padding:10px 32px;display:flex;gap:18px;z-index:100}}.nav a{{color:var(--dm);text-decoration:none;font-size:.85rem}}.nav a:hover{{color:var(--tx)}}.ctr{{max-width:1400px;margin:0 auto;padding:24px 32px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:20px 0}}.sc{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:18px;text-align:center}}.sn{{font-size:2.2rem;font-weight:900;line-height:1}}.sl2{{font-size:.78rem;color:var(--dm);text-transform:uppercase;letter-spacing:.5px;margin-top:4px}}.card{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:22px;margin-bottom:18px}}h2{{font-size:1.2rem;font-weight:700;margin-bottom:12px}}h4{{font-size:.9rem;font-weight:600;margin:8px 0 4px}}table{{width:100%;border-collapse:collapse}}th{{background:#0f172a;padding:9px 14px;text-align:left;font-size:.78rem;text-transform:uppercase;color:var(--dm);border-bottom:1px solid var(--bd)}}td{{padding:10px 14px;border-bottom:1px solid #1e293b;vertical-align:top}}.badge{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.74rem;font-weight:700}}.tag{{display:inline-block;background:#1e3a5f;color:#93c5fd;padding:1px 7px;border-radius:10px;font-size:.72rem;margin:1px}}.dim{{color:var(--dm)}}code{{background:#0f172a;padding:2px 6px;border-radius:4px;font-family:monospace;font-size:.8rem;word-break:break-all}}.eg{{display:inline-block;vertical-align:top;margin:6px 14px 6px 0;min-width:150px}}.eg ul{{list-style:none;padding:0}}.eg li{{font-size:.84rem;color:var(--dm);padding:1px 0}}.sr{{display:flex;align-items:center;gap:10px;margin:5px 0}}.sl{{width:65px;font-size:.76rem;font-weight:700;text-transform:uppercase}}.sb{{flex:1;height:13px;background:#1e293b;border-radius:7px;overflow:hidden}}.mtag{{display:inline-block;background:#1e3a5f;color:#93c5fd;padding:3px 10px;border-radius:6px;font-size:.76rem;margin:2px;font-weight:600}}.ap{{background:#0f172a;border-radius:8px;padding:10px 14px;margin:5px 0;overflow-x:auto;white-space:nowrap}}.step{{display:inline-block;background:#1e293b;border:1px solid var(--bd);padding:4px 9px;border-radius:5px;font-size:.8rem;margin:0 3px}}@media print{{.nav{{display:none}}body{{background:#fff;color:#000}}}}</style></head>
<body>
<div class="hdr"><h1>🔴 RTF RedTeam Report</h1><div class="meta">Target: <b>{target}</b> &nbsp;|&nbsp; Profile: <b>{profile}</b> &nbsp;|&nbsp; Pipeline: <code>{pid}</code> &nbsp;|&nbsp; Operator: <b>{operator}</b> &nbsp;|&nbsp; {gen_at}</div></div>
<nav class="nav"><a href="#sum">Summary</a><a href="#fin">Findings ({len(findings)})</a><a href="#ent">Entities</a><a href="#stg">Stages</a><a href="#mtr">MITRE</a>{"<a href='#ai'>AI</a>" if ai_anal else ""}{"<a href='#ap'>Attacks</a>" if ap_html else ""}</nav>
<div class="ctr">
<section id="sum"><div class="grid"><div class="sc"><div class="sn" style="color:#ef4444">{by_sev['critical']}</div><div class="sl2">Critical</div></div><div class="sc"><div class="sn" style="color:#f97316">{by_sev['high']}</div><div class="sl2">High</div></div><div class="sc"><div class="sn" style="color:#f59e0b">{by_sev['medium']}</div><div class="sl2">Medium</div></div><div class="sc"><div class="sn" style="color:#84cc16">{by_sev['low']}</div><div class="sl2">Low</div></div><div class="sc"><div class="sn" style="color:#38bdf8">{by_sev['info']}</div><div class="sl2">Info</div></div><div class="sc"><div class="sn" style="color:{risk_color}">{risk_score}</div><div class="sl2">Risk Score</div></div></div><div class="card"><h2>Severity Distribution</h2>{sbars}</div></section>
<section id="fin"><div class="card"><h2>Findings ({len(findings_sorted)} total)</h2><table><thead><tr><th>Severity</th><th>Finding</th><th>Tags</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section id="ent"><div class="card"><h2>Discovered Entities</h2>{ent_html or '<p class="dim">None.</p>'}</div></section>
<section id="stg"><div class="card"><h2>Pipeline Stages</h2>{f"<table><thead><tr><th>Stage</th><th>Status</th><th>Details</th></tr></thead><tbody>{srows}</tbody></table>" if srows else '<p class="dim">No stage data.</p>'}</div></section>
<section id="mtr"><div class="card"><h2>🗺 MITRE ATT&amp;CK</h2>{mtags}</div></section>
{f'<section id="ai">{ai_html}</section>' if ai_html else ''}
{f'<section id="ap"><div class="card"><h2>⚔️ Attack Paths</h2>{ap_html}</div></section>' if ap_html else ''}
</div>
<script>function t(i){{const r=document.getElementById('d'+i);r.style.display=(r.style.display==='none'?'table-row':'none')}}</script>
</body></html>"""
        p.write_text(html_out, encoding="utf-8")
        return str(p.resolve())
