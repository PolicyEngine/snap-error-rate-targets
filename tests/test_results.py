"""Pinned results for the FY2024 input, and a check that results/ is current."""

import json

import pytest

from snap_targets import INPUT, INPUT_SHA256, PAPER_27, RESULTS, build, load, sha256, summarize


@pytest.fixture(scope="module")
def rows():
    return load()


@pytest.fixture(scope="module")
def summary(rows):
    return summarize(rows)


def test_input_matches_the_pinned_artifact():
    assert sha256(INPUT) == INPUT_SHA256


def test_committed_results_match_a_fresh_build():
    for name, content in build().items():
        assert (RESULTS / name).read_text() == content, f"rerun snap_targets.py: {name} is stale"


def test_scope_is_the_48_contiguous_states_and_dc(rows):
    codes = {r.code for r in rows}
    assert len(codes) == 49
    assert "DC" in codes
    assert not codes & {"AK", "HI", "GU", "VI"}


def test_rates_are_percentages(rows):
    for r in rows:
        for rate in (r.file_fy2024, r.official_fy2024, r.official_fy2025):
            assert 0 <= rate <= 100


def test_file_rates_reproduce_the_papers_27(rows, summary):
    assert summary["at_or_above_6_file_fy2024"] == 27
    assert summary["file_set_matches_paper_27"]
    assert {r.code for r in rows if r.file_fy2024 >= 6} == PAPER_27


def test_official_rate_counts(summary):
    assert summary["at_or_above_6_official_fy2024"] == 41
    assert summary["at_or_above_6_official_fy2025"] == 40


def test_states_that_cross_6_only_on_official_rates(summary):
    assert summary["official_fy2024_only"] == [
        "AR", "IA", "IN", "KS", "KY", "LA", "MO", "MT",
        "NH", "NJ", "OH", "SC", "TN", "WA", "WV",
    ]
    assert summary["file_only"] == ["NV"]


def test_out_of_reach_if_the_layer_stays_put(rows, summary):
    out = summary["out_of_reach_with_fixed_layer"]
    assert set(out) == {"NJ", "FL", "KS", "NY", "DE"}
    for r in rows:
        assert (r.code in out) == (r.layer >= 6)


def test_median_cuts_for_the_papers_27(summary):
    med = summary["paper_27_median_cut"]
    assert [round(100 * med[k]) for k in ("against_file", "proportional", "fixed_layer")] == [
        24, 45, 60,
    ]


@pytest.mark.parametrize(
    "code, expected",
    [("CA", [25, 45, 63]), ("MA", [44, 57, 76]), ("DC", [57, 65, 81])],
)
def test_featured_cuts(summary, code, expected):
    assert [round(100 * c) for c in summary["featured_cuts"][code]] == expected


def test_summary_json_round_trips(summary):
    assert json.loads(json.dumps(summary)) == summary
