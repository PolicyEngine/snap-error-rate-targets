"""Properties of the three cut measures, checked in exact rational arithmetic."""

from fractions import Fraction

from hypothesis import given, strategies as st

from snap_targets import (
    THRESHOLD,
    cut_against_file,
    cut_fixed_layer,
    cut_proportional,
)

rates = st.fractions(min_value=Fraction(1, 100), max_value=100, max_denominator=10_000)
above = st.fractions(
    min_value=Fraction(THRESHOLD) + Fraction(1, 10_000), max_value=100, max_denominator=10_000
)
at_or_below = st.fractions(min_value=0, max_value=THRESHOLD, max_denominator=10_000)


@given(above)
def test_file_cut_lands_on_the_threshold(f):
    assert f * (1 - cut_against_file(f)) == THRESHOLD


@given(above)
def test_proportional_cut_lands_on_the_threshold(o):
    # The official rate scales with file-visible error when the layer shrinks in proportion.
    assert o * (1 - cut_proportional(o)) == THRESHOLD


@given(rates, above)
def test_fixed_layer_cut_lands_on_the_threshold(f, o):
    # Removing the cut's share of file-visible error lowers the official rate by f * cut.
    assert o - f * cut_fixed_layer(f, o) == THRESHOLD


@given(at_or_below, at_or_below, rates)
def test_no_cut_at_or_below_the_threshold(f, o, any_file_rate):
    assert cut_against_file(f) == 0
    assert cut_proportional(o) == 0
    assert cut_fixed_layer(any_file_rate, o) == 0


@given(rates, rates)
def test_bounds(f, o):
    assert 0 <= cut_against_file(f) < 1
    assert 0 <= cut_proportional(o) < 1
    assert cut_fixed_layer(f, o) >= 0


@given(rates, rates)
def test_ordering_when_the_official_rate_exceeds_the_file_rate(a, b):
    f, o = min(a, b), max(a, b)
    assert cut_against_file(f) <= cut_proportional(o) <= cut_fixed_layer(f, o)


@given(rates)
def test_measures_agree_when_the_layer_is_zero(r):
    assert cut_against_file(r) == cut_proportional(r) == cut_fixed_layer(r, r)


@given(rates, above)
def test_fixed_layer_out_of_reach_exactly_when_the_layer_reaches_the_threshold(f, o):
    assert (cut_fixed_layer(f, o) >= 1) == (o - f >= THRESHOLD)


@given(rates, rates, rates)
def test_monotonicity(f, a, b):
    lo, hi = min(a, b), max(a, b)
    assert cut_against_file(lo) <= cut_against_file(hi)
    assert cut_proportional(lo) <= cut_proportional(hi)
    assert cut_fixed_layer(f, lo) <= cut_fixed_layer(f, hi)
    # A larger file-visible share of the official rate needs a smaller cut of it.
    assert cut_fixed_layer(hi, f) <= cut_fixed_layer(lo, f)
