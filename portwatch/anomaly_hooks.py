"""High-level hooks that integrate anomaly detection into the scan pipeline."""

from __future__ import annotations

from typing import List, Optional

from portwatch.alerts import PortChange
from portwatch.anomaly import AnomalyRule, AnomalyResult, detect_anomalies

_rules: List[AnomalyRule] = []


def load_rules(rules: List[dict]) -> None:
    """Populate the global rule list from raw config dicts."""
    global _rules
    _rules = [AnomalyRule.from_dict(r) for r in rules]


def get_rules() -> List[AnomalyRule]:
    return list(_rules)


def reset_rules() -> None:
    global _rules
    _rules = []


def run_anomaly_detection(
    changes: List[PortChange],
    extra_rules: Optional[List[AnomalyRule]] = None,
) -> AnomalyResult:
    """Run anomaly detection using the global rule list plus any extra rules."""
    rules = _rules + (extra_rules or [])
    return detect_anomalies(changes, rules)


def flagged_summary(result: AnomalyResult) -> str:
    """Return a short human-readable summary of flagged anomalies."""
    if not result.has_anomalies:
        return ""
    parts = []
    for change, rule in result.flagged:
        tag = f"{change.host}:{change.port}/{change.protocol}"
        note = f" ({rule.reason})" if rule.reason else ""
        parts.append(f"{tag}{note}")
    return "Anomalous changes: " + ", ".join(parts)
