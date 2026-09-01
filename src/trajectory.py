"""Build the cumulative financial trajectory comparison: three bachelor's
degree fields (Computer Science, Finance, Psychology) vs. the electrician
apprenticeship path, over a 10-year horizon from the start of school/training.

Reads the already-sourced/cleaned extracts in data/raw/ and writes three
tidy tables to data/processed/, matching the programs / program_costs /
earnings_by_year schema sketched in the project plan:
    - programs.csv
    - program_costs.csv
    - earnings_by_year.csv

The output's `cumulative_earnings_net_of_debt` column is deliberately named
that, not "net worth" or "wealth" - it's gross cumulative earnings minus the
outstanding (interest-accruing) debt balance, nothing more. It does NOT
model taxes, cost of living, spending, saving, investment growth, or any
other assets/liabilities. It answers "which path has earned more money in
total by year N, net of student debt" - a narrower and more precise claim
than "wealth accumulation," and worth being exact about if asked.

Methodology (deliberately simple for a v1 - see each constant/comment for
the specific assumption and why):

- Nominal dollars, not inflation-adjusted. Real dollars are the more
  rigorous choice for a multi-year comparison, but adjusting requires a
  CPI projection assumption on top of everything else already being
  assumed here. Flagged as a known simplification, not an oversight -
  a real fast-follow if the horizon gets extended much past 10 years.
- Student debt is modeled as a standing liability that accrues interest
  every year it's outstanding, not an active repayment schedule. There's
  no assumption here about what fraction of income goes to loan payments
  (that would need its own assumption about repayment plan choice) - the
  debt balance is just netted against cumulative earnings each year, a
  snapshot rather than a cash-flow model.
- Apprentice wages are netted in during the training years - the whole
  point of comparing against college is that trades pay *while* training,
  so leaving that out would silently bias the comparison toward college.
- No forced join between Scorecard (degree-grain) and BLS/GSS
  (occupation-grain) - each path's earnings curve is built from its own
  native source instead (Scorecard's own post-grad earnings for college,
  BLS's own wage percentiles for the trade). See the README's Open
  Methodology Questions section for the full reasoning.
- Both paths' post-training earnings are modeled flat (no assumed raise
  schedule) rather than growing at different assumed rates - an arbitrary
  asymmetric growth assumption between the two paths would bias whichever
  one got the more generous curve. Flat-and-symmetric is the more
  defensible simplification even though it understates real wage growth
  for both.
- Completion risk: the DOL 48.82% trades completion rate is still recorded
  in program_costs for context only, not applied to the electrician curve.
  The college side, however, now gets a second, explicitly-labeled
  "_expected" program per field: a completion-rate-weighted blend of the
  "completes" curve (unchanged, still in the plain cs/finance/psychology
  rows) and a "doesn't complete" curve, using NCES's 64% national 6-year
  bachelor's completion rate and BLS's median earnings for "some college,
  no degree" as the non-completion outcome. This is a real, if still
  simplified, answer to the single sharpest criticism of the v1 model:
  Scorecard's own figures only cover people who finished, so the plain
  curves silently assumed 100% completion. See _dropout_earnings_curve for
  the specific dropout-timing and debt-proration assumptions. Applying the
  same treatment to the trades side (its own completion rate is already on
  hand) is a natural next step, not done here - scoped to the specific
  criticism raised, not a general "add every possible ==_expected row" pass.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

HORIZON_YEARS = 30  # years_since_start = 0..30 - long enough to see whether Finance/Psychology
# ever catch up to the electrician path under the flat post-training earnings assumption,
# not just where the comparison happens to be cut off at year 10

# Sourced 2026-08-20 from FSA Partners: Direct Unsubsidized, loans first
# disbursed July 2025-June 2026. https://fsapartners.ed.gov/knowledge-center/
# library/electronic-announcements/2025-05-30/interest-rates-direct-loans-
# first-disbursed-between-july-1-2025-and-june-30-2026
DEBT_INTEREST_RATE = 0.0639

# DOL Registered Apprenticeship (per README): non-union IEC/ABC path, the
# more common of the two documented paths (union IBEW is 5yr/10,000 hrs).
APPRENTICE_YEARS = 4
DOL_COMPLETION_RATE = 0.4882  # FY2024, Construction/electrician-related, informational only (see module docstring)

SCHOOL_YEARS = 4  # years 0-3: in school, no earnings, no debt drawn until graduation (year 4)

# Sourced 2026-08-20, NCES Fast Facts #40: 6-year completion rate for
# first-time, full-time students who began seeking a bachelor's degree at a
# 4-year institution in fall 2014. https://nces.ed.gov/fastfacts/display.asp?id=40
# One national rate applied to all three fields - Scorecard doesn't give a
# field-specific completion rate, so this doesn't capture that CS/Finance/
# Psychology likely have somewhat different real dropout rates.
BACHELOR_COMPLETION_RATE = 0.64

# Sourced 2026-08-20, BLS CPS Table 37b (median weekly earnings of full-time
# wage and salary workers 25+ by educational attainment), 2024 annual
# average: $1,056/week for "some college, no degree".
# https://www.bls.gov/cps/cpsaat37b.htm
SOME_COLLEGE_NO_DEGREE_ANNUAL = 1056 * 52

# No sourced figure for average time-to-departure among non-completers was
# found - this is a stated, labeled assumption (not a sourced fact): a
# non-completer is modeled as leaving partway through the program, at its
# midpoint, taking on a proportional (half) share of the total debt rather
# than the full amount.
NON_COMPLETION_YEAR = SCHOOL_YEARS // 2


def _college_earnings_curve(earn_1yr: float, earn_4yr: float) -> list[float]:
    """Annual earnings for years_since_start 0..HORIZON_YEARS. Years 0-3:
    in school, $0. Year 4 (graduation) is also treated as $0 - Scorecard's
    EARN_MDN_1YR is earnings measured *one year after* leaving, so year 5
    is the first real earnings point. Years 5-8 interpolate linearly
    between the two Scorecard anchor points (1yr and 4yr out); year 8
    onward holds flat at the 4yr figure (see module docstring on why flat,
    not an assumed raise curve)."""
    curve = [0.0] * SCHOOL_YEARS  # years 0-3
    curve.append(0.0)  # year 4: graduation year itself, not yet "1 year out"
    for years_out in range(1, 5):  # years 5-8 -> years_out 1-4
        if years_out <= 4:
            frac = (years_out - 1) / 3  # 0 at 1yr-out, 1 at 4yr-out
            curve.append(earn_1yr + frac * (earn_4yr - earn_1yr))
    while len(curve) <= HORIZON_YEARS:
        curve.append(earn_4yr)
    return curve[: HORIZON_YEARS + 1]


def _dropout_earnings_curve() -> list[float]:
    """Non-completion scenario: $0 through NON_COMPLETION_YEAR (in school,
    then leaves), flat SOME_COLLEGE_NO_DEGREE_ANNUAL from then on - the same
    "flat forever post-training" simplification used everywhere else in this
    model, applied here to the "some college, no degree" wage instead of a
    completed degree's wage."""
    curve = [0.0] * NON_COMPLETION_YEAR
    while len(curve) <= HORIZON_YEARS:
        curve.append(SOME_COLLEGE_NO_DEGREE_ANNUAL)
    return curve[: HORIZON_YEARS + 1]


def _blend(a: list[float], b: list[float], weight_a: float) -> list[float]:
    return [weight_a * x + (1 - weight_a) * y for x, y in zip(a, b)]


def _trade_earnings_curve(apprentice_wage: float, journeyman_wage: float) -> list[float]:
    """Years 0..APPRENTICE_YEARS-1: apprentice wage. From APPRENTICE_YEARS
    on: flat journeyman (BLS median electrician) wage."""
    curve = [apprentice_wage] * APPRENTICE_YEARS
    while len(curve) <= HORIZON_YEARS:
        curve.append(journeyman_wage)
    return curve[: HORIZON_YEARS + 1]


def _cumulative_earnings_net_of_debt(annual_earnings: list[float], starting_debt: float, debt_drawn_at_year: int) -> list[float]:
    """Cumulative earnings minus an interest-accruing debt balance, snapshotted
    each year - NOT a wealth/net-worth calculation (see module docstring: no
    taxes, cost of living, saving, or investment growth). Debt is drawn as
    one lump sum at debt_drawn_at_year (graduation) and accrues
    DEBT_INTEREST_RATE annually thereafter - no repayment modeled."""
    values = []
    cumulative_earnings = 0.0
    debt_balance = 0.0
    for year, earnings in enumerate(annual_earnings):
        if year == debt_drawn_at_year:
            debt_balance = starting_debt
        elif year > debt_drawn_at_year:
            debt_balance *= 1 + DEBT_INTEREST_RATE
        cumulative_earnings += earnings
        values.append(cumulative_earnings - debt_balance)
    return values


def build() -> None:
    scorecard = pd.read_csv(RAW_DIR / "scorecard_national_weighted_averages.csv")
    bls = pd.read_csv(RAW_DIR / "bls_electrician_national.csv")

    journeyman_wage = float(bls.loc[bls["OCC_TITLE"] == "Electricians", "A_MEDIAN"].iloc[0])
    apprentice_wage = float(bls.loc[bls["OCC_TITLE"] == "Helpers--Electricians", "A_MEDIAN"].iloc[0])

    field_name_map = {
        "Computer Science.": "cs",
        "Finance and Financial Management Services.": "finance",
        "Psychology, General.": "psychology",
    }

    programs = []
    program_costs = []
    earnings_rows = []

    for _, row in scorecard.iterrows():
        program_id = field_name_map[row["field"]]
        programs.append(
            {
                "program_id": program_id,
                "path_type": "bachelor_degree",
                "scenario": "completes_only",
                "name": row["field"].rstrip("."),
                "source": "College Scorecard (Most Recent Cohorts, Field of Study), completions-weighted national average",
            }
        )
        program_costs.append(
            {
                "program_id": program_id,
                "total_cost_or_debt": row["DEBT_ALL_STGP_ANY_MDN"],
                "program_length_years": SCHOOL_YEARS,
                "completion_rate": None,  # Scorecard's own figures only cover completers - no dropout rate available
            }
        )
        curve = _college_earnings_curve(row["EARN_MDN_1YR"], row["EARN_MDN_4YR"])
        earnings_net_of_debt = _cumulative_earnings_net_of_debt(curve, row["DEBT_ALL_STGP_ANY_MDN"], debt_drawn_at_year=SCHOOL_YEARS)
        cumulative = 0.0
        for years_since_start, (earnings, net_of_debt) in enumerate(zip(curve, earnings_net_of_debt)):
            cumulative += earnings
            earnings_rows.append(
                {
                    "program_id": program_id,
                    "years_since_start": years_since_start,
                    "annual_earnings": earnings,
                    "cumulative_earnings": cumulative,
                    "cumulative_earnings_net_of_debt": net_of_debt,
                }
            )

        # Completion-rate-weighted expected value: blends the "completes"
        # curve above with a "doesn't complete" curve (see
        # _dropout_earnings_curve and NON_COMPLETION_YEAR/BACHELOR_COMPLETION_RATE).
        expected_program_id = f"{program_id}_expected"
        programs.append(
            {
                "program_id": expected_program_id,
                "path_type": "bachelor_degree_expected_value",
                "scenario": "completion_rate_weighted",
                "name": f"{row['field'].rstrip('.')} (completion-rate-weighted)",
                "source": "College Scorecard completer curve blended with NCES 6-year completion rate + BLS 'some college, no degree' earnings",
            }
        )
        program_costs.append(
            {
                "program_id": expected_program_id,
                "total_cost_or_debt": row["DEBT_ALL_STGP_ANY_MDN"] * NON_COMPLETION_YEAR / SCHOOL_YEARS,
                "program_length_years": NON_COMPLETION_YEAR,
                "completion_rate": BACHELOR_COMPLETION_RATE,
            }
        )
        dropout_curve = _dropout_earnings_curve()
        dropout_earnings_net_of_debt = _cumulative_earnings_net_of_debt(
            dropout_curve,
            row["DEBT_ALL_STGP_ANY_MDN"] * NON_COMPLETION_YEAR / SCHOOL_YEARS,
            debt_drawn_at_year=NON_COMPLETION_YEAR,
        )
        expected_earnings = _blend(curve, dropout_curve, BACHELOR_COMPLETION_RATE)
        expected_earnings_net_of_debt = _blend(earnings_net_of_debt, dropout_earnings_net_of_debt, BACHELOR_COMPLETION_RATE)
        cumulative = 0.0
        for years_since_start, (earnings, net_of_debt) in enumerate(zip(expected_earnings, expected_earnings_net_of_debt)):
            cumulative += earnings
            earnings_rows.append(
                {
                    "program_id": expected_program_id,
                    "years_since_start": years_since_start,
                    "annual_earnings": earnings,
                    "cumulative_earnings": cumulative,
                    "cumulative_earnings_net_of_debt": net_of_debt,
                }
            )

    trade_curve = _trade_earnings_curve(apprentice_wage, journeyman_wage)
    # Electrician appears once per scenario ("electrician" for completes_only,
    # "electrician_expected" for completion_rate_weighted) using the SAME
    # curve both times - not a real completion-risk-weighted trades curve,
    # just a duplicate placeholder so the trades baseline still shows up next
    # to whichever college scenario is selected in a Power BI slicer/filter.
    # DOL's 48.82% completion rate is recorded but not applied here (see
    # module docstring and README - a documented, not silent, gap).
    for trade_program_id, scenario in [("electrician", "completes_only"), ("electrician_expected", "completion_rate_weighted")]:
        programs.append(
            {
                "program_id": trade_program_id,
                "path_type": "trade_apprenticeship",
                "scenario": scenario,
                "name": "Electrician Apprenticeship",
                "source": "BLS OEWS May 2025 national estimates + DOL Registered Apprenticeship (program length)",
            }
        )
        program_costs.append(
            {
                "program_id": trade_program_id,
                "total_cost_or_debt": 0.0,  # earn-while-you-learn - no tuition debt modeled
                "program_length_years": APPRENTICE_YEARS,
                "completion_rate": DOL_COMPLETION_RATE,
            }
        )
        cumulative = 0.0
        for years_since_start, earnings in enumerate(trade_curve):
            cumulative += earnings
            earnings_rows.append(
                {
                    "program_id": trade_program_id,
                    "years_since_start": years_since_start,
                    "annual_earnings": earnings,
                    "cumulative_earnings": cumulative,
                    "cumulative_earnings_net_of_debt": cumulative,  # no debt to net out
                }
            )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(programs).to_csv(OUT_DIR / "programs.csv", index=False)
    pd.DataFrame(program_costs).to_csv(OUT_DIR / "program_costs.csv", index=False)
    pd.DataFrame(earnings_rows).to_csv(OUT_DIR / "earnings_by_year.csv", index=False)

    print(f"Wrote {len(programs)} programs, {len(earnings_rows)} earnings_by_year rows to {OUT_DIR}")


if __name__ == "__main__":
    build()
