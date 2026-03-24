"""
RTF v2.0 — Reports: PDF Reporter
Generates a professional PDF report using reportlab (with html fallback).
"""
from __future__ import annotations
import json, os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

SEV_COLORS_RGB = {
    "critical": (0.86, 0.15, 0.15),
    "high":     (0.91, 0.35, 0.0),
    "medium":   (0.85, 0.60, 0.03),
    "low":      (0.40, 0.76, 0.05),
    "info":     (0.01, 0.52, 0.78),
}

class PdfReporter:
    def generate(self, data: Dict[str, Any], output_path: str) -> str:
        p = Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
        try:
            return self._generate_reportlab(data, p)
        except ImportError:
            # Fallback: generate HTML then note it
            from reports.html_reporter import HtmlReporter
            html_path = str(p).replace(".pdf", "_fallback.html")
            HtmlReporter().generate(data, html_path)
            # Write stub PDF with note
            p.write_text(
                f"[PDF generation requires reportlab]\n"
                f"pip install reportlab\n"
                f"HTML report saved to: {html_path}\n", encoding="utf-8"
            )
            return str(p.resolve())

    def _generate_reportlab(self, data: Dict[str, Any], p: Path) -> str:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER

        findings  = data.get("findings", [])
        target    = str(data.get("target", ""))
        profile   = str(data.get("profile", ""))
        pid       = str(data.get("pipeline_id", ""))
        operator  = str(data.get("operator", "RTF Operator"))
        gen_at    = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        entities  = data.get("entities", {})
        ai_anal   = data.get("ai_analysis", {})

        doc  = SimpleDocTemplate(str(p), pagesize=A4,
                                 leftMargin=2.5*cm, rightMargin=2.5*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        ss   = getSampleStyleSheet()
        story = []

        # Styles
        title_s = ParagraphStyle("title", parent=ss["Title"],
                                 fontSize=22, textColor=colors.HexColor("#1e3a5f"),
                                 spaceAfter=4)
        h2_s    = ParagraphStyle("h2", parent=ss["Heading2"],
                                 fontSize=13, textColor=colors.HexColor("#1e293b"))
        h3_s    = ParagraphStyle("h3", parent=ss["Heading3"], fontSize=11)
        norm_s  = ParagraphStyle("norm", parent=ss["Normal"], fontSize=9, spaceAfter=3)
        small_s = ParagraphStyle("small", parent=ss["Normal"], fontSize=8,
                                 textColor=colors.HexColor("#64748b"))
        code_s  = ParagraphStyle("code", parent=ss["Code"], fontSize=8,
                                 backColor=colors.HexColor("#f1f5f9"))

        # ── Cover page ──────────────────────────────────────────
        story.append(Spacer(1, 2*cm))
        story.append(Paragraph("🔴 RTF RedTeam Report", title_s))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#dc2626")))
        story.append(Spacer(1, .5*cm))

        meta_data = [
            ["Target:",   target],
            ["Profile:",  profile],
            ["Pipeline:", pid],
            ["Operator:", operator],
            ["Generated:", gen_at],
        ]
        meta_tbl = Table(meta_data, colWidths=[3.5*cm, 13*cm])
        meta_tbl.setStyle(TableStyle([
            ("FONTSIZE", (0,0),(-1,-1), 10),
            ("TEXTCOLOR",(0,0),(0,-1), colors.HexColor("#64748b")),
            ("FONTNAME", (0,0),(0,-1), "Helvetica-Bold"),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        story.append(meta_tbl)

        # ── Severity summary ────────────────────────────────────
        story.append(Spacer(1, .8*cm))
        story.append(Paragraph("Executive Summary", h2_s))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
        story.append(Spacer(1, .3*cm))

        from collections import Counter
        sev_counts = Counter(str(f.get("severity","info")).lower() for f in findings)
        risk_score = sev_counts["critical"]*10 + sev_counts["high"]*5 + sev_counts["medium"]*2 + sev_counts["low"]

        sev_summary = [["Severity","Count","Weight"]]
        for sev in ("critical","high","medium","low","info"):
            sev_summary.append([sev.upper(), str(sev_counts.get(sev,0)),
                                 str(sev_counts.get(sev,0) * {"critical":10,"high":5,"medium":2,"low":1,"info":0}.get(sev,0))])
        sev_summary.append(["TOTAL", str(len(findings)), str(risk_score)])

        sev_tbl = Table(sev_summary, colWidths=[5*cm,4*cm,4*cm])
        sev_tbl_style = [
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1e293b")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),9),
            ("ROWBACKGROUNDS",(0,1),(-1,-2),[colors.HexColor("#f8fafc"),colors.white]),
            ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#f1f5f9")),
            ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
            ("GRID",(0,0),(-1,-1),.5,colors.HexColor("#e2e8f0")),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]
        for i,sev in enumerate(("critical","high","medium","low","info"),1):
            r,g,b = SEV_COLORS_RGB.get(sev,(0,0,0))
            sev_tbl_style.append(("TEXTCOLOR",(0,i),(0,i),colors.Color(r,g,b)))
            sev_tbl_style.append(("FONTNAME",(0,i),(0,i),"Helvetica-Bold"))
        sev_tbl.setStyle(TableStyle(sev_tbl_style))
        story.append(sev_tbl)
        story.append(Spacer(1,.3*cm))
        story.append(Paragraph(f"<b>Overall Risk Score: {risk_score}</b>", norm_s))

        # ── AI Analysis ─────────────────────────────────────────
        if ai_anal:
            story.append(Spacer(1,.5*cm))
            story.append(Paragraph("AI Analysis", h2_s))
            story.append(HRFlowable(width="100%",thickness=1,color=colors.HexColor("#e2e8f0")))
            conf = ai_anal.get("confidence_score","N/A")
            rl   = ai_anal.get("risk_level","")
            summ = str(ai_anal.get("executive_summary",ai_anal.get("identity_summary","")))[:600]
            story.append(Paragraph(f"<b>Confidence:</b> {conf}/100 &nbsp;&nbsp; <b>Risk Level:</b> {rl}", norm_s))
            if summ:
                story.append(Paragraph(summ, norm_s))

        # ── Findings ────────────────────────────────────────────
        story.append(PageBreak())
        story.append(Paragraph(f"Findings ({len(findings)} total)", h2_s))
        story.append(HRFlowable(width="100%",thickness=1,color=colors.HexColor("#e2e8f0")))
        story.append(Spacer(1,.2*cm))

        sorted_f = sorted(findings, key=lambda f: {"critical":0,"high":1,"medium":2,"low":3,"info":4}.get(str(f.get("severity","info")).lower(),4))
        for f in sorted_f:
            sev   = str(f.get("severity","info")).lower()
            r,g,b = SEV_COLORS_RGB.get(sev,(0,0,0))
            title = str(f.get("title",""))[:120]
            desc  = str(f.get("description",""))[:400]
            tgt   = str(f.get("target",""))
            tags  = " | ".join(str(t) for t in f.get("tags",[])[:5])

            story.append(Paragraph(f'<font color="#64748b">[{sev.upper()}]</font> <b>{title}</b>', norm_s))
            if tgt:
                story.append(Paragraph(f"Target: {tgt}", small_s))
            if desc:
                story.append(Paragraph(desc, small_s))
            if tags:
                story.append(Paragraph(f"Tags: {tags}", small_s))
            story.append(HRFlowable(width="100%",thickness=.3,color=colors.HexColor("#e2e8f0"),spaceAfter=4))

        # ── Entities ─────────────────────────────────────────────
        if entities:
            story.append(PageBreak())
            story.append(Paragraph("Discovered Entities", h2_s))
            story.append(HRFlowable(width="100%",thickness=1,color=colors.HexColor("#e2e8f0")))
            story.append(Spacer(1,.2*cm))
            for etype, values in entities.items():
                if not values: continue
                story.append(Paragraph(f"<b>{etype.title()}</b>", h3_s))
                items = " | ".join(str(v) for v in list(values)[:30])
                story.append(Paragraph(items, small_s))

        doc.build(story)
        return str(p.resolve())
