# SNAP error-rate targets

From fiscal year 2028, each state pays a share of its SNAP benefit costs that rises with its official payment error rate ([7 U.S.C. 2013(a)(2)](https://www.law.cornell.edu/uscode/text/7/2013)). A state pays nothing with a rate below 6%, 5% from 6%, 10% from 8% and 15% from 10%. We compute how much of its payment error each state must remove to bring its rate to 6%. We cover the 48 contiguous states and DC, as [Chohlas-Wood (2026)](https://arxiv.org/abs/2611.03213) does.

Rates from the QC public-use file run below the official rates in 47 of these 49 jurisdictions. USDA leaves households that reviewers found ineligible out of the public file but counts their payments in the official rate. It also folds federal re-reviews of a subsample of each state's cases into the official rate. We measure each required cut as a share of the error dollars the file records, in three ways:

| Measure | Formula | The official-minus-file layer |
|---|---|---|
| Against the file rate | (f − 6) / f | Plays no part |
| Proportional | 1 − 6 / o | Shrinks in proportion to the error the file records |
| Fixed layer | (o − 6) / f | Stays put, so a state that needs a cut of 1 or more can't get below 6% |

Here f is the FY2024 rate from the public file and o the official FY2024 rate, both in percent.

## Results

- On file rates, 27 jurisdictions start at or above 6%, the same 27 as in the paper's Figure 2.
- On official rates, 41 start at or above 6% in FY2024 and 40 in FY2025. Fifteen cross 6% only on official FY2024 rates: AR, IA, IN, KS, KY, LA, MO, MT, NH, NJ, OH, SC, TN, WA and WV. Nevada runs the other way, at 6.14% on the file and 5.94% official.
- Those 27 need a median cut of 24% of the error dollars the file records to reach 6% on the file rate. To reach 6% on the official rate, the median rises to 45% if the layer shrinks in proportion and to 60% if it stays put.
- If the layer stays put, NJ, FL, KS, NY and DE can't get below 6% even by removing every error the file records.

For example, California, Massachusetts and the District of Columbia, which the paper discusses in detail, need these cuts:

| Jurisdiction | Against the file rate | Proportional | Fixed layer |
|---|---|---|---|
| California | 25% | 45% | 63% |
| Massachusetts | 44% | 57% | 76% |
| District of Columbia | 57% | 65% | 81% |

[`results/targets_fy2024.csv`](results/targets_fy2024.csv) lists every jurisdiction, and [`results/summary.json`](results/summary.json) holds the counts above.

## Data

[`inputs/component_targets.json`](inputs/component_targets.json) comes from [PolicyEngine/snap-qc-sim](https://github.com/PolicyEngine/snap-qc-sim) at commit [`718fac9`](https://github.com/PolicyEngine/snap-qc-sim/blob/718fac92da2508ed6e04405fbd4d52d7172adeb1/analysis/component_targets.json), under the Apache License 2.0. We build it there with [`build_component_targets.py`](https://github.com/PolicyEngine/snap-qc-sim/blob/718fac92da2508ed6e04405fbd4d52d7172adeb1/analysis/build_component_targets.py) from the FY2024 SNAP QC public-use file and USDA's FY2024 and FY2025 payment error rate reports. To compute each file rate, we weight households by `HWGT` and divide error dollars by issued benefits (`RAWBEN`). We count a case's error dollars (`AMTERR`) when they exceed the $56 tolerance and reviewers found the case overpaid or underpaid (`STATUS` 2 or 3). `fetch_inputs.py --check` confirms that the committed copy matches the pinned commit.

## Reproduce

```bash
uv run python snap_targets.py
uv run pytest
```

The tests pin the results above and check, in exact arithmetic, that:

- each cut brings its rate to 6%;
- the three cuts rise in the table's order when the official rate exceeds the file rate;
- the fixed-layer cut reaches 1 when, and only when, the layer reaches 6 points.

## Limits

- When states step up review, the layer could move by more or less than either measure assumes. In its payment error rate reports, USDA doesn't split the layer between ineligible households and federal re-reviews.
- Both rates come from samples, and we use point estimates. In our [SNAP payment error simulator](https://www.policyengine.org/us/snap-payment-error-simulator), we model sampling noise and estimate each state's odds of landing in each cost-share tier.
- For FY2028, each state elects its FY2025 or FY2026 rate, and from FY2029 the Secretary uses the rate from three years earlier. Congress set a later start for a state whose FY2025 rate times 1.5 reaches 20% (FY2029) or whose FY2026 rate does (FY2030). We compute cuts on FY2024 rates, the latest year with a public file.

## License

We release the code under the MIT License. The input file keeps snap-qc-sim's Apache License 2.0.
