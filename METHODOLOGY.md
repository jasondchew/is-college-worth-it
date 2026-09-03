# Methodology, Data Sources, and Build Log

Full data sourcing, cleaning, scoping decisions, financial trajectory methodology, and SQL exploration work for [Is a Four-Year Degree Still Worth It? College vs. Skilled Trades](README.md). This is the detailed record behind the headline findings on the main README: every judgment call, every data quality issue found and fixed, and the exact SQL queries used to explore the source data. Read this if you want to see the rigor, not just the conclusions.

---

## Data Sources

| Source | What it provides | Status |
|---|---|---|
| [College Scorecard](https://collegescorecard.ed.gov/data/) (U.S. Dept. of Education) | Field-of-study-level debt, 1yr/4yr earnings, completion rates | Sourced: 3,073 institution-level rows (801 CS, 1,482 Psychology, 790 Finance), bachelor's level only |
| [BLS OEWS](https://www.bls.gov/oes/) (May 2025 national estimates) | Electrician wage distribution (10th–90th percentile, national) | Sourced: 757,220 electricians nationally, median $63,190/yr |
| DOL Registered Apprenticeship (RAPIDS / apprenticeship.gov) | Apprenticeship program length, completion rates | Sourced. Program length: 4yr/8,000 OJT hrs (non-union, IEC/ABC) or 5yr/10,000 hrs (IBEW union). Completion rate: **48.82%** nationwide (FY2024, Construction industry, electrician-related occupations, 7,822 apprentices in cohort), pulled by Jason directly via the [Apprentice Completion Rate Analysis dashboard](https://www.apprenticeship.gov/data-and-statistics/completion-rate-analysis) after the dashboard didn't respond to browser automation |
| General Social Survey (GSS), NORC/University of Chicago, 1972-2024 cumulative file | Self-reported job satisfaction (`SATJOB`) by occupation (`OCC10`) | Sourced for Electricians, CS-related, and Finance-related occupations. **Psychology excluded from this comparison**, see Scoping Decisions below. |

## Sourced Figures So Far (raw, not yet cleaned/validated)

**GSS job satisfaction by occupation (1972-2024 cumulative, `SATJOB` question), with 95% confidence intervals** (`src/satisfaction_trend.py`):

| Occupation group | n | % "very satisfied" | 95% CI |
|---|---|---|---|
| Electricians | 258 | 50.8% | 44.7-56.8% |
| CS-related (developers/programmers/analysts) | 600 | 48.8% | 44.9-52.8% |
| Finance-related (managers/advisors/agents/analysts) | 533 | 55.3% | 51.1-59.5% |

**GSS job satisfaction by decade**, same script, output in `data/processed/satisfaction_by_decade.csv`; the pooled table above answers "how satisfied is each group overall," but the original business question asked whether satisfaction has *changed* over time, which a whole-period number can't speak to by construction. Point estimate with 95% CI in parentheses:

| Decade | CS-related | Electrician | Finance-related |
|---|---|---|---|
| 1970s | 57.6% (41-73%) | 56.8% (42-70%) | 74.5% (61-85%) |
| 1980s | 53.4% (42-64%) | 46.7% (35-59%) | 65.1% (54-74%) |
| 1990s | 57.5% (48-66%) | 49.2% (37-62%) | 53.4% (43-64%) |
| 2000s | 54.3% (46-63%) | 42.4% (27-59%) | 47.2% (38-57%) |
| 2010s | 41.7% (33-51%) | 59.4% (42-75%) | 61.5% (52-70%) |
| 2020s* | 38.4% (31-46%) | 53.3% (36-70%) | 42.7% (34-52%) |

**Confidence intervals use the Wilson score method** (not the more common normal-approximation/Wald interval), chosen because Wald behaves badly at exactly the sample sizes and proportions here (as low as n≈30 per cell, with proportions well away from 50%), where it can produce a lower bound below 0% or upper bound above 100%. Wilson stays valid at both ends.

**Reading the decade trend correctly (this section originally got the headline finding wrong, corrected 2026-08-25/26 after checking confidence intervals directly rather than just eyeballing point estimates):** all three groups' point estimates trend downward from the 1970s to the 2020s (CS: 57.6%→38.4%; Finance: 74.5%→42.7%; Electrician: 56.8%→53.3%). But "the number went down" and "the drop is statistically real" are two different claims, and only one field's decline survives a check against sampling noise. Comparing each group's 1970s and 2020s confidence intervals: **Finance's don't overlap at all (60.5-84.7% vs. 33.6-52.4%), the only statistically confirmed decline of the three.** CS's do overlap (40.8-72.8% vs. 30.9-46.4%), so its apparent drop can't be distinguished from sampling noise, despite looking similar in size to Finance's on paper. Electrician's overlap too, and this was checked exhaustively, not just at the two endpoint decades: all 15 possible pairwise combinations of Electrician's six decade intervals overlap with each other, the strongest version of "no confirmed change" this data can support.

*2020s covers only 3 of GSS's usual ~5 survey waves per decade (2021, 2022, 2024), fieldwork for the rest of the decade hasn't happened yet, so this bin isn't comparable to a full decade the way 1970-2010 are. Notably, Finance, the field with the only statistically confirmed satisfaction decline, is also the slowest-paying-off of the two degree fields that eventually overtake the electrician path financially (crosses at year 23, vs. CS's year 11; see Financial Trajectory below).

Annual bins (rather than decade) were considered and rejected: GSS doesn't survey every year, and per-group annual counts run ~5-15 respondents, too sparse for even a wide confidence interval to be meaningful.

**BLS electrician annual wages (May 2025, national):** 10th pct $42,640 / 25th $49,430 / median $63,190 / 75th $83,940 / 90th $108,510. Separate "Helpers—Electricians" line (median $42,670) usable as an apprentice-wage proxy.

## Scoping Decisions (the "why," not just the "what")

**Computer Science (CIP 1107), not "Computer and Information Sciences, General" (CIP 1101):** Scorecard splits computing degrees into ~15 CIP codes spanning genuinely different programs (Computer Science, Computer Engineering, IT Administration, Networking, etc.). 1107 was chosen to avoid blending sub-disciplines with different labor-market outcomes into one number. This is a within-Scorecard taxonomy choice, not a claim that "CS" means the same thing across every data source used here; see the open question below.

**Psychology, General (CIP 4201):** No general-vs-specific ambiguity the way there was for CS: the other Psychology CIP codes are narrower specializations, so General is the standard bachelor's category with the largest sample size.

**Electrician as the trade anchor:** Chosen because it's the specific trade Jason has personally observed former students entering: the actual origin of this project, not a generic pick.

**Finance (CIP 5208 "Finance and Financial Management Services"), added as a third degree field:** Motivated by wanting to directly test a specific claim (heard via a Charlie Kirk campus debate clip) that a finance/business career path requires a college degree. Unlike "Business" broadly, which splits across dozens of GSS occupation titles (managers, sales, retail, etc.) with no clean single mapping, Finance has exactly one Scorecard CIP code at the bachelor's level, and a defensible GSS occupation bucket: Financial managers, Personal financial advisors, Securities/commodities/financial services sales agents, and Financial analysts (deliberately excluding lower-level "financial clerks" and "financial examiners," which don't specifically require a finance degree). This is a real judgment call about which titles count; worth being ready to defend if asked.

**Psychology excluded from the GSS happiness comparison:** GSS's "Psychologist" occupation title typically requires a doctorate and license, making it a far more credentialed, self-selected population than "someone with a psychology bachelor's degree." Most psych bachelor's grads scatter into HR, case work, sales, teaching, and other roles rather than becoming "Psychologists." Using that occupation's satisfaction number (72.2% very satisfied, n=72) as a stand-in for "psych degree happiness" would overstate it and compare an apples-to-oranges population. Psychology's Scorecard debt/earnings data has no such problem and stays in the financial-trajectory comparison; only the happiness dimension is affected. The diffuse, hard-to-pin-down career path this reveals is itself a real, citable point about the degree, not just a data limitation to hide.

## Cleaning & Validation

**Column definition correction (2026-08-18):** `IPEDSCOUNT1` was initially described in this doc as "enrollment"/"program size," verified against the College Scorecard's own data dictionary, and that's wrong. Its real definition: **"Number of awards to all students in year 1 of the pooled debt cohort,"** a count of degrees *completed/conferred* in that program, not students currently enrolled. The weighting logic below still holds (a bigger completions cohort is still a reasonable proxy for a bigger program), but every reference to "enrollment" or "program size" from this column has been corrected to "completions"/"award count" throughout this doc.

**College Scorecard suppression:** the debt/earnings columns use `PS` (not the string "PrivacySuppressed" seen in some other Scorecard files) to mark institution-CIP-year cells where the reporting cohort was too small to disclose. Row-level suppression is substantial: 51.2% (CS), 40.3% (Finance), 25.2% (Psychology) on median debt; similar rates on 1yr/4yr earnings. This looked alarming at first, so it was checked properly rather than assumed acceptable: suppressed rows have a median completions count (`IPEDSCOUNT1`) of **10** vs. **50** for valid rows (mean 15.7 vs. 107.6); suppression correlates strongly with tiny completion cohorts. Weighted by actual completions rather than row count, valid (non-suppressed) rows still capture **86.2% (CS) / 92.9% (Finance) / 93.4% (Psychology)** of total completions. This is the direct justification for using a completions-weighted average rather than a naive average of institution rows: the latter would be far more distorted by the missing small programs than the former, since a weighted approach never gave those small programs much influence to begin with.

**What the debt figure actually measures (2026-08-20):** `DEBT_ALL_STGP_ANY_MDN` is defined in Scorecard's own data dictionary as **"Median Stafford and Grad PLUS loan debt disbursed at all institutions,"** median debt *among people who borrowed through these specific federal loan programs*, not the cost of the degree for everyone who earned it. Someone whose family paid cash shows as $0 in this figure despite paying the same tuition, so this column understates true cost for anyone who didn't finance their education this way, and, more importantly for this project's framing, it means the model is structurally blind to the role family wealth plays in who gets to "afford" the debt-free version of the college outcome.

Tried to quantify *how much* this matters, by computing a borrowing rate (`DEBT_ALL_STGP_ANY_N` loan-recipient count ÷ `IPEDSCOUNT1` completions count) per field. Result: CS 75.9%, Finance **102.1%**, Psychology **146.3%**. Rates over 100% are impossible, so this was checked rather than reported: the two columns turn out to draw from different populations (`DEBT_ALL_STGP_ANY_N` counts anyone who borrowed while enrolled, including people who never completed; `IPEDSCOUNT1` counts completers only), so dividing one by the other compares different groups, not a real rate. Rejected rather than published. A real "cost regardless of financing" figure (net price) exists in Scorecard's separate institution-level file, not the field-of-study file used here, and would need its own sourcing/join/suppression-check pass, flagged as real future work, not done in this pass.

**Duplicate check (initially reported wrong, then corrected):** a first pass flagged 90 duplicate `(UNITID, CIPCODE)` pairs. That turned out to be a false signal: 93 rows have a **null `UNITID`**, and pandas' `.duplicated()` groups multiple `NaN` values together as if they were equal, which is why unrelated rows got flagged as "duplicates" of each other. Re-checked correctly (excluding null-`UNITID` rows from that specific check): **zero real duplicate rows.** The null-`UNITID` rows themselves are a separate, genuine finding: mostly identifiable colleges that have since closed (Mount Ida College, Marygrove College, Mills College, MacMurray College, College of New Rochelle), whose institution ID appears to get nulled out in IPEDS once marked inactive, even though the historical field-of-study outcomes data is retained. These rows are kept (they still have valid completions/debt/earnings data and represent real past students) but are worth knowing about if a number looks off later. **Lesson worth keeping:** check for nulls in your join/dedup key columns before running a duplicate check, not after: a naive `.duplicated()` call will silently misreport results if the key itself has missing values.

**Why cleaning looked shorter here than on Olist:** Olist's duplication came from SQL join fan-out (multi-item/multi-payment orders creating repeated `order_id` rows), a real structural duplication risk from joining tables. This project's Scorecard extract was pulled directly from one source file with no joins performed yet, so there was no join-fan-out risk to begin with; the real cleaning work here was investigating *why* values were missing (suppression, driven by small cohort size) rather than mechanically dropping rows. That's still cleaning/validating; just shaped by what this specific data actually needed, not a fixed checklist applied the same way every time.

**Methodology finding on Psychology's low 4-year earnings:** `EARN_MDN_4YR` only counts people who are "working and not enrolled in school" during the measurement year (Scorecard's own definition), so anyone still pursuing a doctorate at the 4-year mark (typical for a psych PhD) is excluded from the calculation entirely, not counted as a low earner. This means the $51,921 figure isn't being dragged down by still-in-training future psychologists; it's the real ceiling for people whose *only* credential is a bachelor's in psychology, since the higher-paying "Psychologist" title requires a doctorate they don't have (and, by construction of this metric, aren't currently pursuing). This independently confirms the same structural fact the GSS occupation-mapping issue already surfaced from a completely different dataset: two unrelated sources landing on the same conclusion.

**Completions-weighted national figures per degree field** (weighted mean of each institution's own median value, weighted by `IPEDSCOUNT1` (number of degrees awarded in year 1 of the pooled cohort, not current enrollment), using only non-suppressed rows):

| Field | Median debt | Earnings, 1yr out | Earnings, 4yr out |
|---|---|---|---|
| Computer Science | $20,351 | $87,316 | $127,020 |
| Finance | $21,726 | $60,520 | $90,416 |
| Psychology | $22,936 | $32,012 | $51,921 |

Sanity-checked: debt is similar across fields (tracks school cost more than major), earnings spread in the expected direction. Saved to `data/raw/scorecard_national_weighted_averages.csv`.

## Financial Trajectory (v1)

Built in `src/trajectory.py`, reading directly from the cleaned source files above. Outputs three tidy tables to `data/processed/`: `programs.csv`, `program_costs.csv`, `earnings_by_year.csv` (long format: one row per program per year, with both `annual_earnings` and `cumulative_earnings_net_of_debt` columns, ready for Power BI). `programs.csv` includes a `scenario` column (`completes_only` vs. `completion_rate_weighted`) so the two versions of the comparison can be filtered independently instead of showing all 8 program lines at once. Electrician appears once per scenario using the identical curve both times, a documented placeholder, not a real completion-risk-weighted trades curve (that's still the known remaining asymmetry noted above), just enough so the trades baseline shows up next to whichever college scenario is selected.

**On the column name:** `cumulative_earnings_net_of_debt`, not "net worth" or "wealth." This is deliberate: it's gross cumulative earnings minus the outstanding (interest-accruing) debt balance, and nothing else. It does not model taxes, cost of living, spending, saving, or investment growth. "Which path has earned more money in total by year N, net of student debt" is the precise claim; "wealth accumulation" would be overclaiming what's actually computed here.

**Methodology decisions (resolved):**

- **Nominal dollars, not inflation-adjusted.** Real dollars are more rigorous for a multi-year comparison, but require a CPI projection assumption on top of everything else already being assumed. Flagged as a known v1 simplification, not an oversight.
- **Student debt accrues interest as a standing liability**, using Scorecard's `DEBT_ALL_STGP_ANY_MDN` as the starting balance, which is median debt *among people who borrowed*, not the cost of the degree for everyone (see Cleaning & Validation above). Someone whose family paid cash shows as $0 debt in this model despite paying the same tuition; the model is structurally blind to the role family wealth plays here. Interest accrues at 6.39% (Direct Unsubsidized rate for loans first disbursed July 2025-June 2026, [FSA Partners](https://fsapartners.ed.gov/knowledge-center/library/electronic-announcements/2025-05-30/interest-rates-direct-loans-first-disbursed-between-july-1-2025-and-june-30-2026)), not an active repayment schedule; no assumption is made about what fraction of income goes toward loan payments. `cumulative_earnings_net_of_debt` nets the (interest-accruing) debt balance against cumulative earnings each year: a snapshot, not a cash-flow model.
- **Apprentice wages are netted in during the training years** (BLS's "Helpers—Electricians" median, $42,670/yr, as the apprentice-wage proxy), the whole point of the trades comparison is earning while training, so omitting this would silently bias the comparison toward college.
- **No forced join between Scorecard (degree-grain) and BLS/GSS (occupation-grain).** Each path's earnings curve is built from its own native source instead: the three degree paths use Scorecard's own post-grad earnings (already tied directly to that specific degree, no occupation-code bridging needed), the trades path uses BLS's own electrician wage data.
- **Post-training annual earnings are modeled flat forever for both sides** (not growing at different assumed rates): an arbitrary asymmetric growth-rate assumption between the two paths would bias whichever one got the more generous curve. Flat-and-symmetric is the more defensible simplification, but it has a real consequence documented below.
- **Completion risk:** the plain `cs`/`finance`/`psychology` rows still model a completed degree only (Scorecard's own figures only cover people who finished). A completion-rate-weighted `_expected` variant per field was added afterward; see "Sensitivity: accounting for college non-completion risk" below. DOL's 48.82% trades completion rate remains stored in `program_costs.csv` for context but unapplied to the electrician curve, a known remaining asymmetry.

**Headline result (30-year horizon):**

| Path | Annual earnings post-training (flat) | Crosses electrician's cumulative earnings net of debt at |
|---|---|---|
| Computer Science | $127,020 | Year 9-10 |
| Finance | $90,416 | Year 16-18 |
| Psychology | $51,921 | **Never** |
| Electrician | $63,190 | n/a |

**Known limitation worth stating plainly:** Psychology's gap to the electrician path doesn't just persist, it *widens every year* (-$374K at year 10, -$681K by year 30), a direct, mechanical consequence of the flat-forever assumption above, not an empirical finding about real career trajectories. Since Psychology's modeled flat wage ($51,921) never rises above the electrician's modeled flat wage ($63,190), a cumulative gap between two flat, unequal annual incomes can only grow, never close. Real careers see wage growth with tenure on both sides of this comparison; modeling that growth would change this result and is the natural v2 extension, not a quick fix, since it means picking real growth curves per field/occupation rather than one shared flat assumption.

### Sensitivity: accounting for college non-completion risk

**The sharpest criticism of the v1 model above:** Scorecard's own earnings/debt figures only cover people who *finished* their degree, so the `cs`/`finance`/`psychology` curves silently assumed 100% completion, even though the trades side's own 48.82% DOL completion rate was sitting right there in `program_costs.csv`, unapplied. "Debt without a finished degree" is one of the most commonly cited real arguments against college, and the plain model couldn't represent that outcome at all.

Added a second, explicitly-labeled variant per degree field (`cs_expected`, `finance_expected`, `psychology_expected`), blending the original "completes" curve with a "doesn't complete" curve, weighted by a national completion rate:

- **Completion rate: 64%**, NCES Fast Facts #40, 6-year completion rate for first-time, full-time students who began seeking a bachelor's degree at a 4-year institution in fall 2014. ([nces.ed.gov](https://nces.ed.gov/fastfacts/display.asp?id=40)) One national rate applied across all three fields, since Scorecard doesn't provide a field-specific completion rate; CS, Finance, and Psychology almost certainly have somewhat different real dropout rates this doesn't capture.
- **Non-completion earnings: $54,912/yr** ($1,056/week), BLS CPS Table 37b, 2024 annual average, median earnings for full-time workers 25+ with "some college, no degree." ([bls.gov](https://www.bls.gov/cps/cpsaat37b.htm))
- **Non-completion timing and debt: a stated assumption, not a sourced figure.** No reliable national figure for "how far through a bachelor's program the average non-completer gets" was found, so a non-completer is modeled as leaving at the program's midpoint (year 2 of 4), taking on half the total debt rather than the full amount. This is a labeled simplification, worth revisiting if a better-sourced figure turns up.

**Result: every crossover point moves later once non-completion risk is priced in.**

| Path | Crosses electrician (completes only) | Crosses electrician (completion-rate-weighted) |
|---|---|---|
| Computer Science | Year 9-10 | **Year 11** |
| Finance | Year 16-18 | **Year 23** |
| Psychology | Never | Never (gap widens further) |

Trades-side completion risk (the DOL 48.82% figure) is still not applied to the electrician curve; that's the same asymmetry in reverse, and a fair next step, just out of scope for this pass since it was specifically the college-side gap that got flagged.

## Reconciling Money and Satisfaction

The two dimensions of this project don't point at one clean "winner": worth saying plainly rather than picking a favorite:

- **Computer Science has the best long-run cumulative earnings net of debt**, even after pricing in non-completion risk (crosses the electrician path at year 11). Its satisfaction point estimate also drops over time (57.6% → 38.4%), but that drop's confidence intervals overlap across decades, so it isn't statistically distinguishable from sampling noise, despite looking like a real decline on paper.
- **Electrician has a substantial, real financial lead in the near term**, ahead of every degree path for at least a decade (11 years vs. CS, 23 vs. Finance under the completion-rate-weighted curves) before eventually being overtaken by CS. For anyone actually choosing at 18, "which path is ahead 10 years from now" is a very different, and arguably more decision-relevant, question than "which path wins eventually." Electrician's satisfaction shows no statistically confirmed change across any of the five decades measured, checked exhaustively across all 15 possible pairwise decade combinations, not just the two endpoints, and every pair overlaps.
- **Finance has a solid financial outcome** (crosses electrician by year 23, the slowest of the two fields that eventually do) **and is the only field in this data with a statistically confirmed satisfaction decline** (74.5% in the 1970s to 42.7% in the 2020s, non-overlapping confidence intervals). Ironically, the field that takes the longest to pay off financially is also the one field where the data can confidently say something got worse.
- **Psychology has no satisfaction comparison at all** (excluded, see Scoping Decisions above) and is the clear financial loser, never catching up to the electrician path under this model's assumptions.

**One important caveat that tempers all of the satisfaction findings above:** at any single point in time, the 2020s cross-section alone for example, all three groups' confidence intervals overlap each other too, so no field can be confidently called "highest" or "lowest" in satisfaction right now. The only confident satisfaction claim this data supports is about *change over time* for Finance specifically, not a current-day ranking between fields.

## Deliberately Out of Scope (v2 ideas)

The presentation's closing "Sources & Scope" page (page 6) states this list directly, as three bullets under "Deliberately out of scope (not gaps we missed)"; this section is the text record of that list, with the reasoning behind each item spelled out further than slide space allows:

- **A second trade beyond electrician** (plumbing, HVAC), to test whether these findings generalize past one trade or are specific to electrician's particular wage/apprenticeship profile.
- **Occupational physical toll** (injury/disability rates). A real, commonly-raised argument against the trades that this data doesn't capture. Satisfaction and physical toll are different constructs, and GSS's satisfaction figures may even understate toll: workers forced out by injury exit the surveyed population entirely.
- **Job security / layoff risk, compared across all four paths** (added 2026-09-02, after the presentation initially shipped). The financial model compares earnings trajectories assuming continuous employment on every path; it says nothing about how likely someone is to *stay* employed. That risk is genuinely uneven across the four: CS has been through real, well-documented tech layoff waves (2022-2024) the model doesn't touch; Finance carries cyclical/recessionary layoff exposure; Psychology bachelor's holders scatter into varied roles (see Scoping Decisions above) with correspondingly varied, hard-to-pin-down security; and electrician work, while less prone to mass layoffs, is tied to construction-cycle demand instead. A real version of this would need a job-security or displacement metric by occupation/field, e.g. BLS unemployment rate by occupation or educational attainment, or BLS JOLTS layoffs-and-discharges rate by industry, a distinct sourcing task from anything pulled for this project so far, and worth scoping as its own v2 addition rather than retrofitted into the existing financial-trajectory or satisfaction analysis.

**So which path is "worth it"?** Depends entirely on what's being optimized and over what time horizon: money short-term favors trades, money long-term favors CS (with real completion risk attached, and a satisfaction trade-off that looks real but isn't statistically confirmed), Finance takes the longest of any path that eventually pays off and carries the one confirmed satisfaction downside, Electrician holds flat satisfaction at zero debt for fifty years, and Psychology is a financial laggard with no satisfaction data to weigh against it. That's a more honest answer than picking one, and the actual point of building both dimensions into this project from the start.

## Open Methodology Questions (not yet resolved)

- **How to bridge Scorecard's degree-field grain to BLS/GSS's occupation grain**, beyond the "each path uses its own native source" workaround above: Scorecard classifies people by what they studied (CIP code), BLS and GSS classify people by what job they hold (SOC code / occupation category). There's no direct one-to-one mapping between "graduated with a CS degree" and "works in a computing occupation." Still unresolved for any analysis that would need to combine the two directly.

## Data Acquisition Tooling

Sourcing and per-source quality profiling for this project uses **[The Registrar](../The%20Registrar/)**, a custom-built data acquisition/QA agent, its first completed real-world run (a prior planned run against CAASPP data was superseded when that project was dropped). Registrar's provenance docs for each source will be included in this repo once generated. Its automatic cross-source join feature is deliberately **not** used here: College Scorecard, BLS, DOL, and GSS are four different grains with no shared join key, so the actual trajectory calculation is custom analysis code instead.

## SQL Exploration Tooling

SQL exploration for this project uses **[SQL & Business Thinking AI Tutor](../SQL%20&%20Business%20Thinking%20AI%20Tutor/)**, Jason's own custom-built practice tool, the first real (non-generic-practice-dataset) use of it, against this project's own data. It's a multi-step LLM-orchestrated workflow (agentic *characteristics*: it adapts its next step based on real feedback, like re-generating a question if its own reference SQL fails to run, but not a fully autonomous agent, since the pipeline order itself is fixed application logic, not something the LLM plans on its own), not a single prompt-in/answer-out tool. Per the app's design, Jason writes every SQL query himself; the app never writes or reveals SQL for him.

The actual workflow, per uploaded file: the app profiles the schema and flags data-quality issues, then proposes one realistic high-level business question the dataset can help answer, decomposed into a sequence of SQL sub-questions that build in difficulty: one generated at a time, informed by how the previous ones went, rather than a fixed batch decided upfront. For each sub-question, Jason writes and submits SQL; a wrong answer gets a progressively stronger hint (never the solution itself), and the app separately tracks which SQL concepts he's weaker on across the session, so later questions lean into those rather than repeating what's already solid. Once every sub-question in the set is answered correctly, the app synthesizes a business recommendation grounded in Jason's own query results, not a canned answer, since it only has what his queries actually returned to work from.

Uploading both `scorecard_institutions_combined.csv` and `gss_satisfaction_extract.csv` together surfaced a real gap in the Tutor itself: its multi-upload flow always requires confirming *some* join before exercises unlock, with no path for "these tables genuinely aren't related." Since the two files share zero column names (different grains: institution-level degree outcomes vs. individual survey respondents), any manual join pick would have been arbitrary and meaningless. **Workaround:** uploaded and explored the files one at a time instead (single-upload mode skips the join step entirely), the correct fit for two genuinely unrelated tables. The gap itself is now documented in the Tutor's own README/CLAUDE.md as a planned feature (a "these tables aren't related" option), found and written down *because* it came up on real project data rather than a synthetic practice fixture.

Exploration finished on both files as of 2026-08-20. Solved queries below, pulled directly from the Tutor's own exercise logs, deduped where the same easy question got regenerated verbatim across separate sessions (the Tutor generates one business question at a time per upload, so re-opening a file for a second session sometimes lands on the same opening question).

### Solved: `scorecard_institutions_combined.csv`

Three standalone warm-up queries (explored before locking in a business question), then a full set under one business question.

**Warm-up: institutions offering a CS bachelor's, ordered alphabetically** (`SELECT_WHERE`, `ORDER_LIMIT`):
```sql
SELECT INSTNM, CONTROL, CIPDESC
FROM scorecard_institutions_combined
WHERE CIPDESC = 'Computer Science.' AND CREDDESC = 'Bachelor''s Degree' AND CONTROL = 'Public'
ORDER BY INSTNM;
```

**Warm-up: Psychology bachelor's programs with 100+ students, top 10** (`SELECT_WHERE`, `ORDER_LIMIT`):
```sql
SELECT INSTNM, IPEDSCOUNT2
FROM scorecard_institutions_combined
WHERE CREDDESC = 'Bachelor''s Degree' AND CIPDESC = 'Psychology, General.' AND IPEDSCOUNT2 >= 100
ORDER BY IPEDSCOUNT2 DESC
LIMIT 10;
```

**Warm-up: excluding `PS`-suppressed earnings values** (`SELECT_WHERE`, `ORDER_LIMIT`), the same suppression issue later formalized in Cleaning & Validation above:
```sql
SELECT INSTNM, CIPDESC, EARN_MDN_4YR
FROM scorecard_institutions_combined
WHERE CONTROL = 'Private, nonprofit' AND EARN_MDN_4YR != 'PS'
ORDER BY INSTNM
LIMIT 15;
```

**Business question: Which combination of institution type and field of study gives students the best return on investment: strong post-graduation earnings relative to typical debt loads?**

```sql
-- easy: CS programs at public institutions
SELECT INSTNM, OPEID6
FROM scorecard_institutions_combined
WHERE CONTROL = 'Public' AND CIPDESC = 'Computer Science.'
ORDER BY INSTNM;
```
```sql
-- medium: avg 4yr earnings by institution type, CS only, casting past 'PS'
SELECT CONTROL, AVG(EARN_MDN_4YR::NUMERIC) AS avg_md_4yr_earnings
FROM scorecard_institutions_combined
WHERE CIPDESC = 'Computer Science.' AND CREDDESC = 'Bachelor''s Degree' AND EARN_MDN_4YR != 'PS'
GROUP BY CONTROL
ORDER BY avg_md_4yr_earnings DESC;
```
```sql
-- medium: avg 4yr earnings by field, only fields averaging above $40,000
SELECT CIPDESC, AVG(EARN_MDN_4YR::NUMERIC) AS avg_md_earnings_yr
FROM scorecard_institutions_combined
WHERE EARN_MDN_4YR != 'PS'
GROUP BY CIPDESC
HAVING AVG(EARN_MDN_4YR::NUMERIC) > 40000
ORDER BY avg_md_earnings_yr DESC;
```
```sql
-- medium: same pattern, grouped by field + institution type, min 5 rows and >$35,000 avg
SELECT CIPDESC, CONTROL, COUNT(*) AS count_rows, AVG(EARN_MDN_4YR::NUMERIC) AS avg_md_earnings_4yr
FROM scorecard_institutions_combined
WHERE EARN_MDN_4YR != 'PS'
GROUP BY CIPDESC, CONTROL
HAVING COUNT(*) >= 5 AND AVG(EARN_MDN_4YR::NUMERIC) > 35000
ORDER BY avg_md_earnings_4yr DESC;
```
```sql
-- hard: top 3 institutions by 4yr earnings per field, via CTE + RANK() window function
WITH cte1 AS (
    SELECT CIPDESC, INSTNM, CONTROL, EARN_MDN_4YR::NUMERIC,
        RANK() OVER (PARTITION BY CIPDESC ORDER BY EARN_MDN_4YR::NUMERIC DESC) AS ranking
    FROM scorecard_institutions_combined
    WHERE EARN_MDN_4YR != 'PS'
)
SELECT * FROM cte1 WHERE ranking >= 1 AND ranking <= 3;
```

### Solved: `gss_satisfaction_extract.csv`

Two sessions, both centered on the same underlying question (occupation satisfaction, and whether it's shifted over time) with slightly different generated wording.

**Business question: Which occupations report the highest job satisfaction, and has that changed over time? This could help a career counseling service point people toward more satisfying career paths.**

```sql
-- easy: 2020 responses by occupation_group
SELECT year, occupation_group, satjob
FROM gss_satisfaction_extract
WHERE year = 2020
ORDER BY occupation_group;
```
```sql
-- medium: response count + 'very satisfied' count per group
SELECT occupation_group, COUNT(*) AS count_responses,
    SUM(CASE WHEN satjob = 'very satisfied' THEN 1 ELSE 0 END) AS count_very_satisfied
FROM gss_satisfaction_extract
GROUP BY occupation_group
ORDER BY occupation_group;
```
```sql
-- medium: % 'very satisfied' per group, via CTE
WITH cte1 AS (
    SELECT occupation_group, COUNT(*) AS count_responses,
        SUM(CASE WHEN satjob = 'very satisfied' THEN 1 ELSE 0 END) AS count_very_satisfied
    FROM gss_satisfaction_extract
    GROUP BY occupation_group
)
SELECT occupation_group, ROUND((count_very_satisfied * 1.0 / count_responses) * 100.0, 1) AS perc_vs_to_responses
FROM cte1
ORDER BY perc_vs_to_responses DESC;
```
```sql
-- medium: occ10_title response counts above 50
SELECT occ10_title, COUNT(*) AS count_responses
FROM gss_satisfaction_extract
GROUP BY occ10_title
HAVING COUNT(*) > 50
ORDER BY count_responses DESC;
```

**Business question: Which occupation groups report the highest job satisfaction, and has that changed over time? This could help guide career-advice content or workforce planning.**

```sql
-- easy: 2022 'very satisfied' responses
SELECT year, occupation_group, occ10_title, satjob
FROM gss_satisfaction_extract
WHERE year = 2022 AND satjob = 'very satisfied';
```
```sql
-- medium: groups with 100+ 'very satisfied' responses
SELECT occupation_group, COUNT(*) AS count_responses,
    SUM(CASE WHEN satjob = 'very satisfied' THEN 1 ELSE 0 END) AS count_very_satisfied
FROM gss_satisfaction_extract
GROUP BY occupation_group
HAVING SUM(CASE WHEN satjob = 'very satisfied' THEN 1 ELSE 0 END) > 100
ORDER BY count_very_satisfied DESC;
```
```sql
-- hard: each group's top-ranked year by % 'very satisfied', via CTE + RANK() window function
WITH percentages AS (
    SELECT occupation_group, year,
        ROUND((SUM(CASE WHEN satjob = 'very satisfied' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) * 100.0, 1) AS perc_vs_to_responses
    FROM gss_satisfaction_extract
    GROUP BY occupation_group, year
),
group_ranking AS (
    SELECT occupation_group, year, perc_vs_to_responses,
        RANK() OVER (PARTITION BY occupation_group ORDER BY perc_vs_to_responses DESC) AS ranking
    FROM percentages
)
SELECT occupation_group, year, perc_vs_to_responses, ranking
FROM group_ranking
WHERE ranking = 1;
```
```sql
-- medium: each group/year's % 'very satisfied', plus each group's across-year average via AVG() OVER (PARTITION BY ...)
WITH percentages AS (
    SELECT occupation_group, year,
        (SUM(CASE WHEN satjob = 'very satisfied' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) * 100.0 AS perc_vs_to_responses
    FROM gss_satisfaction_extract
    GROUP BY occupation_group, year
)
SELECT occupation_group, year, perc_vs_to_responses,
    ROUND(AVG(perc_vs_to_responses) OVER (PARTITION BY occupation_group), 1) AS avg_perc
FROM percentages
ORDER BY occupation_group, year;
```
```sql
-- medium: window function in isolation, no CTE - each row's occupation_group response count via COUNT() OVER (PARTITION BY ...)
SELECT occupation_group, year, satjob,
    COUNT(*) OVER (PARTITION BY occupation_group) AS count_over_the_group
FROM gss_satisfaction_extract
ORDER BY occupation_group, year;
```
