"""RTF v2.0 — AI: Anomaly Detection"""
from __future__ import annotations
import json, statistics
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

class AnomalyDetector:
    def detect_finding_anomalies(self, findings: List[Dict]) -> List[Dict]:
        anomalies = []
        if not findings: return anomalies
        sev = Counter(str(f.get("severity","info")).lower() for f in findings)
        # Spike detection
        if sev["critical"] > len(findings) * 0.3:
            anomalies.append({"type":"severity_spike","message":
                f"Unusually high critical ratio: {sev['critical']}/{len(findings)}","severity":"high"})
        # Duplicate detection
        titles = [f.get("title","") for f in findings]
        title_counts = Counter(titles)
        for t, c in title_counts.items():
            if c > 3:
                anomalies.append({"type":"duplicate_finding","message":
                    f"Finding '{t[:50]}' appears {c}x — possible scanner noise","severity":"info"})
        # Target concentration
        targets = Counter(f.get("target","") for f in findings if f.get("target"))
        if targets:
            top_target, top_count = targets.most_common(1)[0]
            if top_count > len(findings) * 0.6:
                anomalies.append({"type":"target_concentration","message":
                    f"60%+ of findings on single target: {top_target}","severity":"medium"})
        return anomalies

    def detect_osint_anomalies(self, entities: Dict, profiles: List[Dict]) -> List[Dict]:
        anomalies = []
        usernames = list(entities.get("usernames",[]))
        emails = list(entities.get("emails",[]))
        # Username count anomaly
        if len(usernames) > 20:
            anomalies.append({"type":"username_volume","message":
                f"Unusually high username count: {len(usernames)}","severity":"medium"})
        # Email domain diversity
        domains = [e.split("@")[-1] for e in emails if "@" in e]
        if len(set(domains)) > 5:
            anomalies.append({"type":"email_domain_diversity","message":
                f"{len(set(domains))} unique email domains found","severity":"low"})
        # Bio inconsistency across profiles
        locations = [p.get("data",{}).get("location","") for p in profiles if p.get("data",{}).get("location")]
        if len(set(l.lower() for l in locations if l)) > 3:
            anomalies.append({"type":"location_inconsistency","message":
                f"Multiple locations detected across profiles: {set(locations)}","severity":"medium"})
        return anomalies
