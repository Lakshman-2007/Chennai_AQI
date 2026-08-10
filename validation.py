"""
validation.py

Automated checks on the generated dataset before it's accepted
(FR-11, PRD section 17). Outliers are flagged, never auto-deleted
(PRD section 17 Check 4, Rule 5).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# A conservative outlier bound for NO2 tropospheric column density (mol/m^2).
# This is a sanity-check bound, not a scientific threshold — flagged values
# should be reviewed, not silently trusted or discarded.
_OUTLIER_BOUNDS = {
    "NO2": (0.0, 0.001),
}


@dataclass
class ValidationReport:
    row_count: int = 0
    missing_count: int = 0
    missing_percentage: float = 0.0
    duplicate_dates: list[str] = field(default_factory=list)
    invalid_numeric_rows: list[str] = field(default_factory=list)
    flagged_outliers: list[dict[str, Any]] = field(default_factory=list)
    passed: bool = True
    issues: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"row_count={self.row_count}",
            f"missing={self.missing_count} ({self.missing_percentage:.1f}%)",
            f"duplicate_dates={len(self.duplicate_dates)}",
            f"invalid_numeric_rows={len(self.invalid_numeric_rows)}",
            f"flagged_outliers={len(self.flagged_outliers)}",
            f"passed={self.passed}",
        ]
        if self.issues:
            lines.append("issues:")
            lines.extend(f"  - {i}" for i in self.issues)
        return "\n".join(lines)


def validate_observations(
    observations: list[dict[str, Any]], variable: str
) -> ValidationReport:
    report = ValidationReport(row_count=len(observations))

    # Check 1: duplicate dates
    seen: set[str] = set()
    dupes: set[str] = set()
    for obs in observations:
        if obs["date"] in seen:
            dupes.add(obs["date"])
        seen.add(obs["date"])
    report.duplicate_dates = sorted(dupes)
    if report.duplicate_dates:
        report.passed = False
        report.issues.append(f"Duplicate dates found: {report.duplicate_dates}")

    # Check 2 & 3: valid pixel count and missing values
    missing = 0
    for obs in observations:
        if obs.get("valid_pixel_count", 0) < 0:
            report.passed = False
            report.issues.append(f"Negative valid_pixel_count on {obs['date']}")
        if obs["value"] is None:
            missing += 1
    report.missing_count = missing
    report.missing_percentage = (
        100.0 * missing / report.row_count if report.row_count else 0.0
    )

    # Check 4: numerical sanity (NaN/Infinity/impossible negatives/outliers)
    bounds = _OUTLIER_BOUNDS.get(variable)
    for obs in observations:
        val = obs["value"]
        if val is None:
            continue
        if val != val:  # NaN check without importing math
            report.invalid_numeric_rows.append(obs["date"])
            continue
        if val in (float("inf"), float("-inf")):
            report.invalid_numeric_rows.append(obs["date"])
            continue
        if bounds:
            low, high = bounds
            if val < low or val > high:
                report.flagged_outliers.append({"date": obs["date"], "value": val})

    if report.invalid_numeric_rows:
        report.passed = False
        report.issues.append(
            f"Invalid numeric values (NaN/Inf) on: {report.invalid_numeric_rows}"
        )
    if report.flagged_outliers:
        # Flagged, not fatal — PRD says flag first, don't auto-reject.
        report.issues.append(
            f"{len(report.flagged_outliers)} value(s) flagged as outliers "
            "for manual review (not removed)."
        )

    return report
