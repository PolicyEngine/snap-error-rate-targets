"""Error-dollar cuts that bring a state's SNAP payment error rate to 6%.

From fiscal year 2028, each state pays a share of its SNAP benefit costs that
rises with its official payment error rate (7 U.S.C. 2013(a)(2)(B)). A state
pays nothing with a rate below 6%, 5% from 6%, 10% from 8% and 15% from 10%.

Rates from the QC public-use file run below the official rates in 47 of the 49
jurisdictions in scope. USDA leaves households that reviewers found ineligible
out of the public file but counts their payments in the official rate, and it
folds federal re-reviews of a subsample of each state's cases into the
official rate.

Three measures of the required cut, as a share of the error dollars the file
records:

- ``cut_against_file``: (f - 6) / f, against the file rate f.
- ``cut_proportional``: 1 - 6 / o, against the official rate o, if the
  official-minus-file layer shrinks in proportion to the error the file
  records.
- ``cut_fixed_layer``: (o - 6) / f, against o if that layer stays put. At 1 or
  more, removing every error dollar the file records leaves o at or above 6%.

Run ``python snap_targets.py`` to rebuild ``results/``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "inputs" / "component_targets.json"
RESULTS = ROOT / "results"

# PolicyEngine/snap-qc-sim analysis/component_targets.json at commit 718fac9.
INPUT_SHA256 = "17ee725df9450907fe8f64a49f0672ee573fcb8860bf18019dd8c4b69dedeaad"
INPUT_SCHEMA = "snap_qc_sim.component_targets.v1"

THRESHOLD = 6

# Chohlas-Wood (2026), arXiv 2611.03213, studies the 48 contiguous states and
# DC, so this analysis leaves out Alaska, Hawaii, Guam and the Virgin Islands.
OUTSIDE_SCOPE = frozenset({"AK", "HI", "GU", "VI"})

# The 27 jurisdictions in Figure 2 of arXiv 2611.03213: those that begin at or
# above 6% on rates computed from the public file.
PAPER_27 = frozenset(
    {
        "AL", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "IL", "MA", "MD",
        "ME", "MI", "MN", "MS", "NC", "ND", "NM", "NV", "NY", "OK", "OR", "PA",
        "RI", "TX", "VA",
    }
)


def cut_against_file(file_rate, threshold=THRESHOLD):
    """Share of the file's error dollars to remove so the file rate falls to the threshold."""
    if file_rate <= threshold:
        return 0
    return (file_rate - threshold) / file_rate


def cut_proportional(official_rate, threshold=THRESHOLD):
    """Required cut against the official rate if the official-minus-file layer shrinks in proportion."""
    if official_rate <= threshold:
        return 0
    return 1 - threshold / official_rate


def cut_fixed_layer(file_rate, official_rate, threshold=THRESHOLD):
    """Required cut against the official rate if the official-minus-file layer stays put.

    At 1 or more, the layer alone keeps the official rate at or above the
    threshold.
    """
    if official_rate <= threshold:
        return 0
    if file_rate <= 0:
        return math.inf
    return (official_rate - threshold) / file_rate


@dataclass(frozen=True)
class Jurisdiction:
    code: str
    file_fy2024: float
    official_fy2024: float
    official_fy2025: float

    @property
    def layer(self) -> float:
        return self.official_fy2024 - self.file_fy2024

    @property
    def cuts(self) -> tuple[float, float, float]:
        return (
            cut_against_file(self.file_fy2024),
            cut_proportional(self.official_fy2024),
            cut_fixed_layer(self.file_fy2024, self.official_fy2024),
        )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path = INPUT) -> list[Jurisdiction]:
    data = json.loads(path.read_text())
    if data.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"{path}: expected schema {INPUT_SCHEMA}, found {data.get('schema')}")
    file_side = data["file_side"]["fy2024"]
    registry = data["registry"]
    rows = [
        Jurisdiction(
            code=code,
            file_fy2024=file_side[code]["total_pct"],
            official_fy2024=registry[code]["fy2024"]["total_pct"],
            official_fy2025=registry[code]["fy2025"]["total_pct"],
        )
        for code in sorted(file_side)
        if code not in OUTSIDE_SCOPE
    ]
    if len(rows) != 49:
        raise ValueError(f"expected the 48 contiguous states and DC, found {len(rows)}")
    return rows


def summarize(rows: list[Jurisdiction]) -> dict:
    at_file = {r.code for r in rows if r.file_fy2024 >= THRESHOLD}
    at_official_24 = {r.code for r in rows if r.official_fy2024 >= THRESHOLD}
    at_official_25 = {r.code for r in rows if r.official_fy2025 >= THRESHOLD}
    paper = [r for r in rows if r.code in PAPER_27]
    out_of_reach = sorted(
        (r for r in rows if r.cuts[2] >= 1), key=lambda r: (-r.cuts[2], r.code)
    )
    by_code = {r.code: r for r in rows}

    def rounded(cuts):
        return [round(c, 6) for c in cuts]

    return {
        "jurisdictions_in_scope": len(rows),
        "at_or_above_6_file_fy2024": len(at_file),
        "file_set_matches_paper_27": at_file == PAPER_27,
        "at_or_above_6_official_fy2024": len(at_official_24),
        "at_or_above_6_official_fy2025": len(at_official_25),
        "official_fy2024_only": sorted(at_official_24 - at_file),
        "file_only": sorted(at_file - at_official_24),
        "out_of_reach_with_fixed_layer": [r.code for r in out_of_reach],
        "paper_27_median_cut": {
            "against_file": round(statistics.median(r.cuts[0] for r in paper), 6),
            "proportional": round(statistics.median(r.cuts[1] for r in paper), 6),
            "fixed_layer": round(statistics.median(r.cuts[2] for r in paper), 6),
        },
        "featured_cuts": {
            code: rounded(by_code[code].cuts) for code in ("CA", "MA", "DC")
        },
    }


CSV_COLUMNS = [
    "jurisdiction",
    "file_rate_fy2024",
    "official_rate_fy2024",
    "official_rate_fy2025",
    "official_minus_file_fy2024",
    "cut_against_file",
    "cut_proportional",
    "cut_fixed_layer",
    "fixed_layer_reachable",
    "in_paper_27",
]


def to_csv(rows: list[Jurisdiction]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for r in rows:
        cut_file, cut_prop, cut_fixed = r.cuts
        writer.writerow(
            [
                r.code,
                f"{r.file_fy2024:.8f}",
                f"{r.official_fy2024:.2f}",
                f"{r.official_fy2025:.2f}",
                f"{r.layer:.8f}",
                f"{cut_file:.6f}",
                f"{cut_prop:.6f}",
                f"{cut_fixed:.6f}",
                "yes" if cut_fixed < 1 else "no",
                "yes" if r.code in PAPER_27 else "no",
            ]
        )
    return buffer.getvalue()


def to_text(summary: dict) -> str:
    med = summary["paper_27_median_cut"]
    lines = [
        f"Jurisdictions in scope: {summary['jurisdictions_in_scope']}",
        f"At or above 6% on FY2024 file rates: {summary['at_or_above_6_file_fy2024']}"
        f" (matches the paper's 27: {summary['file_set_matches_paper_27']})",
        f"At or above 6% on official FY2024 rates: {summary['at_or_above_6_official_fy2024']}",
        f"At or above 6% on official FY2025 rates: {summary['at_or_above_6_official_fy2025']}",
        f"Official FY2024 only: {', '.join(summary['official_fy2024_only'])}",
        f"File only: {', '.join(summary['file_only'])}",
        "Out of reach if the layer stays put: "
        + ", ".join(summary["out_of_reach_with_fixed_layer"]),
        "Median cut for the paper's 27: "
        f"{100 * med['against_file']:.0f}% against the file rate, "
        f"{100 * med['proportional']:.0f}% proportional, "
        f"{100 * med['fixed_layer']:.0f}% with the layer fixed",
    ]
    for code, cuts in summary["featured_cuts"].items():
        lines.append(
            f"{code}: {100 * cuts[0]:.0f}% against the file rate, "
            f"{100 * cuts[1]:.0f}% to {100 * cuts[2]:.0f}% against the official rate"
        )
    return "\n".join(lines) + "\n"


def build(path: Path = INPUT) -> dict[str, str]:
    """Return the contents of every results file, keyed by file name."""
    if sha256(path) != INPUT_SHA256:
        raise ValueError(f"{path} does not match the pinned snap-qc-sim artifact")
    rows = load(path)
    summary = summarize(rows)
    return {
        "targets_fy2024.csv": to_csv(rows),
        "summary.json": json.dumps(summary, indent=2, sort_keys=True) + "\n",
        "summary.txt": to_text(summary),
    }


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    for name, content in build().items():
        (RESULTS / name).write_text(content)
    sys.stdout.write((RESULTS / "summary.txt").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
