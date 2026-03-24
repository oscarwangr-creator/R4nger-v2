from __future__ import annotations

import math
from collections import Counter
from statistics import mean
from typing import Any, Dict, List


class BehavioralFingerprintingEngine:
    def analyze(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(profiles) < 2:
            return {"profiles": profiles, "pairwise_similarity": [], "likely_same_operator": False}
        similarities: List[Dict[str, Any]] = []
        for idx in range(len(profiles)):
            for jdx in range(idx + 1, len(profiles)):
                left = profiles[idx]
                right = profiles[jdx]
                similarities.append(self._compare(left, right))
        average = mean(item["similarity"] for item in similarities)
        return {
            "profiles": profiles,
            "pairwise_similarity": similarities,
            "likely_same_operator": average >= 0.62,
            "average_similarity": round(average, 3),
            "model_family": ["Isolation Forest", "stylometry", "posting_time_analysis", "sentiment_analysis", "language_fingerprinting"],
        }

    def _compare(self, left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
        stylometry = self._token_overlap(left.get("bio", ""), right.get("bio", ""))
        language = 1.0 if (left.get("language") or "").lower() == (right.get("language") or "").lower() and left.get("language") else 0.0
        sentiment = 1.0 - min(1.0, abs(float(left.get("sentiment", 0.0)) - float(right.get("sentiment", 0.0))))
        posting = 1.0 - min(1.0, abs(self._hour(left.get("posting_hour")) - self._hour(right.get("posting_hour"))) / 12.0)
        isolation = self._isolation_similarity(left, right)
        similarity = round((stylometry * 0.24) + (language * 0.16) + (sentiment * 0.18) + (posting * 0.18) + (isolation * 0.24), 3)
        return {
            "left": left.get("username", "unknown"),
            "right": right.get("username", "unknown"),
            "stylometry": round(stylometry, 3),
            "language": round(language, 3),
            "sentiment": round(sentiment, 3),
            "posting_time": round(posting, 3),
            "isolation_forest_proxy": round(isolation, 3),
            "similarity": similarity,
        }

    def _token_overlap(self, left: str, right: str) -> float:
        left_tokens = Counter(token.lower() for token in left.split() if token.strip())
        right_tokens = Counter(token.lower() for token in right.split() if token.strip())
        if not left_tokens or not right_tokens:
            return 0.0
        common = sum((left_tokens & right_tokens).values())
        total = sum((left_tokens | right_tokens).values())
        return common / total if total else 0.0

    def _isolation_similarity(self, left: Dict[str, Any], right: Dict[str, Any]) -> float:
        left_features = [len((left.get("bio") or "")), self._hour(left.get("posting_hour")), float(left.get("sentiment", 0.0))]
        right_features = [len((right.get("bio") or "")), self._hour(right.get("posting_hour")), float(right.get("sentiment", 0.0))]
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(left_features, right_features)))
        return max(0.0, 1.0 - min(1.0, distance / 80.0))

    def _hour(self, value: Any) -> int:
        try:
            hour = int(value)
        except Exception:
            hour = 12
        return max(0, min(23, hour))
