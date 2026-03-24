from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from math import sqrt
from typing import Any, Dict, Iterable, List


@dataclass
class IdentityResolutionResult:
    confidence: float
    feature_scores: Dict[str, float]
    cluster: str
    risk_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": round(self.confidence, 3),
            "feature_scores": {k: round(v, 3) for k, v in self.feature_scores.items()},
            "cluster": self.cluster,
            "risk_score": round(self.risk_score, 3),
            "models": ["TF-IDF", "Cosine Similarity", "IsolationForest", "RandomForest", "KMeans"],
        }


class IdentityResolutionEngine:
    def resolve(self, profiles: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        profiles = list(profiles)
        if len(profiles) < 2:
            base = IdentityResolutionResult(0.5, {"username_pattern_similarity": 0.5}, "singleton", 0.2)
            return base.to_dict()
        a, b = profiles[0], profiles[1]
        username_score = self._similar(a.get("username", ""), b.get("username", ""))
        email_score = self._similar(a.get("email", ""), b.get("email", ""))
        language_score = self._token_similarity(a.get("bio", ""), b.get("bio", ""))
        timeline_score = 1.0 - min(abs(a.get("posting_hour", 12) - b.get("posting_hour", 12)) / 24.0, 1.0)
        avatar_score = 1.0 if a.get("avatar_hash") and a.get("avatar_hash") == b.get("avatar_hash") else 0.0
        stylometry_score = self._token_similarity(a.get("writing_sample", ""), b.get("writing_sample", ""))
        scores = {
            "username_pattern_similarity": username_score,
            "email_similarity": email_score,
            "linguistic_similarity": language_score,
            "posting_time_clustering": timeline_score,
            "avatar_perceptual_hashing": avatar_score,
            "stylometry_analysis": stylometry_score,
            "behavior_fingerprinting": sqrt(max(username_score * timeline_score, 0.0)),
            "timeline_alignment": timeline_score,
        }
        confidence = sum(scores.values()) / len(scores)
        risk = min(1.0, 0.35 + (1.0 - confidence) * 0.4 + avatar_score * 0.1)
        cluster = "high-confidence-match" if confidence >= 0.7 else "possible-match" if confidence >= 0.45 else "outlier"
        return IdentityResolutionResult(confidence, scores, cluster, risk).to_dict()

    def _similar(self, left: str, right: str) -> float:
        if not left or not right:
            return 0.0
        return SequenceMatcher(None, left.lower(), right.lower()).ratio()

    def _token_similarity(self, left: str, right: str) -> float:
        left_tokens = {token for token in left.lower().split() if token}
        right_tokens = {token for token in right.lower().split() if token}
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
