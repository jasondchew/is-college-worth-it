"""Break the pooled 1972-2024 GSS job-satisfaction figures out by decade, per
occupation group - the original business question asked "has this changed
over time?" and the headline README figures answered with one whole-period
percentage per group, which can't say anything about a trend by construction.

Kept as its own script, separate from trajectory.py, because satisfaction is
a deliberately separate dimension from the financial trajectory (see the
README's methodology notes on why GSS/BLS/Scorecard aren't force-joined) -
this doesn't feed into earnings_by_year, it's its own output.

Bins by decade rather than year: GSS doesn't survey every year, and annual
group sizes run ~5-15 respondents - too sparse for a stable percentage.
Decade bins give ~30-150 respondents per occupation_group per decade -
better, but still modest, so every row also gets a 95% Wilson score
confidence interval (see _wilson_ci) rather than reporting the point
percentage alone. Also emits one pooled "ALL" row per group (the full
1972-2024 period), with its own interval, matching the whole-period figures
already in the README's "Sourced Figures So Far" table.
"""

import math
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

Z_95 = 1.96


def _wilson_ci(successes: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion. Chosen over the
    plainer normal-approximation (Wald) interval because Wald behaves badly
    at exactly the sample sizes and proportions this data has - small n
    (as low as ~30) and proportions well away from 50%, where Wald can
    produce a lower bound below 0% or an upper bound above 100%. Wilson
    stays valid at both ends without that failure mode."""
    if n == 0:
        return (float("nan"), float("nan"))
    p_hat = successes / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    margin = z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - margin) * 100, min(1.0, center + margin) * 100)


def _summarize(sub: pd.DataFrame) -> dict:
    n = len(sub)
    successes = int(sub["very_satisfied"].sum())
    pct = round(successes / n * 100, 1) if n else float("nan")
    ci_low, ci_high = _wilson_ci(successes, n)
    return {"n": n, "very_satisfied_pct": pct, "ci_low_95": round(ci_low, 1), "ci_high_95": round(ci_high, 1)}


def build() -> None:
    df = pd.read_csv(RAW_DIR / "gss_satisfaction_extract.csv")
    df["decade"] = (df["year"] // 10) * 10
    df["very_satisfied"] = (df["satjob"] == "very satisfied").astype(int)

    rows = []
    for group, sub in df.groupby("occupation_group"):
        rows.append({"occupation_group": group, "decade": "ALL", "decade_is_partial": False, **_summarize(sub)})
        for decade, decade_sub in sub.groupby("decade"):
            rows.append(
                {
                    "occupation_group": group,
                    "decade": str(decade),
                    # The 2020s bin only has 3 of GSS's usual ~5 survey waves so
                    # far (2021, 2022, 2024 - fieldwork for the rest of the
                    # decade hasn't happened yet), not comparable to a full decade.
                    "decade_is_partial": decade == 2020,
                    **_summarize(decade_sub),
                }
            )

    trend = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trend.to_csv(OUT_DIR / "satisfaction_by_decade.csv", index=False)
    print(f"Wrote {len(trend)} rows to {OUT_DIR / 'satisfaction_by_decade.csv'}")


if __name__ == "__main__":
    build()
