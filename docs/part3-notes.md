# Part 3: sources, datasets and checks

The hardware comparisons recorded here use the common six-cycle implementation.
Part 4 now implements the selected numerical fit in four cycles and remeasures
its generated implementation alternatives. Part 3 keeps its original measured
areas and explicitly identifies their latency; the coefficient words, numerical
model and exhaustive accuracy distributions are unchanged.

The post explains continuous minimax seeding, integer output-interval fitting,
and joint selection of internal rounding and widths. The primary references are
NIST DLMF 3.11(i), Lim/Nagarakatte PLDI 2021, and the MPFR manual; external papers
are linked directly.

- `data/remez-trace.json`: `//sfu:blog_design_points --trace`. A relative-minimax
  quadratic on [0,1], with deliberately uneven initial exchange points. Four
  actual iterations, common plot axes. Production `GenerateSeeds` uses MPFR
  absolute-error Remez on individual short intervals; the diagram uses the
  weighted version consistent with Part 2. Neither is the discrete optimizer.
- `data/search-examples.json`: `//sfu:blog_search_examples`, taking archived
  coefficient tables and seven witnesses from the methodology audit. Includes
  exact allowed integer-C intervals from `FeasibleConstantInterval` and initial
  rounding/width experiments. Sampled errors are not global bounds.
- `data/rounding-refined.json`: `//sfu:rounding_refine`; independent discovery and
  fresh 500,000-draw corpora, accumulated failure neighborhoods. Superseded for
  acceptance by the exhaustive software gate.
- `scripts/draw_search_diagrams.py` only lays out exported values. It performs
  no approximation, search or oracle calculation.

Numerical acceptance requires all 2^32 input encodings through the software model,
not RTL simulation. The reference uses directed interpolation enclosures with
MPFR fallback; the mathematical bound and source are documented in
`code/rtl/audits/rounding/README.md`. Early rejection is allowed. A sampled pass,
partial range, or timed-out run cannot accept.

Hardware candidates use private real fitted ROMs and the same registered-ROM,
five-stage Booth polynomial architecture (six cycles total), one result per
cycle, under a common 1 GHz target. Compare mapped cost in units of one data
flip-flop; defer physical units and implementation details to Part 4. Range
reduction and FP32 reconstruction are part of exhaustive numerical evaluation;
the measured RTL comparison includes the table and polynomial, since those are
the blocks changed in this experiment.

## Completed numerical and hardware comparison

`data/rounding-accepted.json` contains 12 coefficient tables, their internal modes,
widths, and full 2^32-input acceptance reports with configuration/checker hashes.
The coefficient snapshots reconstruct to the recorded SHA-256 exactly.
All have maximum distance two representable steps, zero special-case failures,
zero arithmetic exceptions and zero downward steps across adjacent finite FP32
inputs. Each exhaustive pass required MPFR fallback at 134,683 inputs; the other
reference values were resolved by directed enclosures or exact classifications.

`data/rounding-measurements.json` has normalized mapped costs. Full physical
units, source/library/tool/environment hashes, power and timing are in
`code/rtl/audits/rounding/measurements.json`, with interpretations in its README.
`record_measurements.py` checks that the mapped RTL hashes match the sources,
the canonical integer profile matches the exhaustive report, and both simulation
logs passed before exporting the comparison. Selected profile 11 costs 1228.40
register units and has +292.56 ps setup slack at the common clock target.

The rounding section shows the four compact passing profiles, one for each
rounding pair, plus the 18-bit truncation comparison that explains why a rounding operation
can be worthwhile when it permits narrower arithmetic. Full resource counts and
physical units stay in the implementation notes.

Verification completed: twelve full-domain software passes; all 24 RTL/mapped
scoreboard tests; fixed-point inverse-interval and Remez methodology tests;
certified-reference agreement with MPFR at nodes, adjacent inputs and cell
midpoints (including direct enclosure checks); prior Booth RTL/gate regressions;
article dataset/hash checks; and the seven-page Quarto build with embedded
resources and valid local links. Browser review checked the fixed-axis Remez
comparison and replay, readable interval figure, and final cost table.

`data/part3.provenance.json` binds exported JSON assets to hashes and generator
targets. Retained exporter binary hashes identify the earlier sampled exports;
current accepted tables additionally bind each exact integer profile to its
exhaustive checker binary and complete run report.

## Alternation explanation and exchange walkthrough

The alternation diagram uses the final C++ error curve above a schematic
correction-sign diagram. The dashed lower connectors illustrate required sign
changes; the marked zeros indicate existence within each gap, not numerical
root estimates. The text identifies the correction as the difference of two
quadratics before applying the root-count argument.

The Remez walkthrough exposes six phases from four actual solves: initial solve,
locate extrema without changing the curve, first exchange/solve, locate new
extrema, second exchange/solve, and third exchange/convergence. A fixed-axis
close-up at the negative minimum distinguishes the chosen point from the true
extremum in the second iteration. Its axes stay unchanged through convergence.
No fitting or root finding runs in JavaScript; controls reveal exported traces.

## Resolution and precision search, October 22

The revised narrative starts with RNE hardware candidates, explains fitting and
counterexample feedback, prices the candidates, and then compares narrowing
circuits. `data/hardware-search.json` contains the actual additional resolution
experiments, not a schematic or interpolated design-space frontier.

RNE/RNE accepted profiles:

| Rows | a/b/c | residual | first/result | Proxy | Mapped FF units |
| ---: | --- | ---: | --- | ---: | ---: |
| 32 | 12/16/26 | 22 | 22/28 | 1705.05 | 1529.45 |
| 64 | 11/14/24 | 20 | 19/26 | 1611.90 | 1355.20 |
| 128 | 10/13/23 | 20 | 17/25 | 1769.35 | 1309.85 |
| 256 | 10/13/23 | 20 | 17/25 | 2233.60 | 1492.75 |

All four are accepted by exhaustive FP32 C++ checks. The three new RTL fixtures
pass lint, RTL and gate scoreboards, and setup timing under the same six-cycle,
one-input-per-cycle architecture and constraints as the earlier 12 profiles.
The reduced ROM decision-network estimator comes from `area.cc`; the C++
`//sfu:search_cost` exporter combines its mux/AND/OR/inverter counts with the
calibrated Booth/completion rates and the actual six-stage nominal register
inventory. Primitive AND/OR and inverter rates are 0.3 and 0.15 FF units.
Arithmetic completion includes RNE; do not use this proxy as an isolated RNE vs
truncation estimator. Rounding-mode comparisons use measured whole designs.

The proxy and mapping disagree between 64 and 128 rows. Do not claim a global
optimum or exact ROM-only cause for that reversal. ROM Boolean factoring,
arithmetic constant folding and uniform Booth-row pricing distinguish the
proxy from mapping. Preserve several candidates and map them. Part 2's earlier
regular-tree cost example remains unchanged; this study uses the coefficient
contents and the six-cycle RTL inventory explicitly.

The 32-row medium profile (11/14/24,20,19/26) and the 64-row compact profile
(10/13/23,20,17/25) still fail after four fits. Their snapshots and full reports
are exported as rejected fits, not impossibility results for those formats.
A wider 64-row profile (11/15/25,20,20/27) also passes and is retained in the code
audit; it is not one of the plotted mapped comparisons.

The counterexample illustration uses the actual 128-row compact RNE sequence:
16,813, 7,417 and zero failures after successive fits. Every count comes from a
complete exhaustive run. The format does not change between those passes.

New generators: `draw_hardware_search.py` lays out exported data;
`rtl/rounding/export_resolution.py` serializes frozen C++ profiles into RTL and
C++ fixtures; `record_resolution.py` binds those fixtures to accepted reports,
source hashes, passing simulation logs and completed mapping/STA reports.

## Cost methodology and constant propagation

Cost has separate roles before and after fitting. `search_cost PROFILE
--architecture` reads only the format header and prices a regular selection
tree, arithmetic and pipeline widths. It works on a seed header without any
coefficient rows. The default invocation reads the fitted words and refines
ROM selection logic. It still uses generic arithmetic/nominal storage counts;
mapped RTL performs additional constant propagation. These scores guide
multiple nearby formats, outside the coefficient solver's numerical inner
loop. The gray bars in the resolution figure are explicitly after-fit
estimates, not architectural estimates available before search. Architecture
scores are also retained in hardware-search.json for reproduction.

The audit in code/rtl/audits/rounding/constant-bits/README.md confirms that
profile 11's a[9]=0 and c[22]=1 are literals through carried registers and into
Booth/compressor logic. The mapped snapshot's cell histogram matches the
published baseline. Explicitly narrowing a to nine physical bits at the same
fractional scale gives cost 1229.30 versus 1228.40 and improves slack by 43.94 ps;
keep the existing area baseline. Do not change the published rounding costs or
claim a missing constant-propagation optimization from this experiment.

## Article structure and workflow verification

The search procedure now precedes its mathematical components: architectural
proposal and neighborhood exploration; fixed-format coefficient fitting;
counterexample refinement and exhaustive acceptance; content-aware repricing;
synthesis and feedback into further proposals. Hardware prices are outside
ScoreCandidate, whose objective remains failure count, maximum ULP distance and
summed numerical error. The article does not claim that table size is fixed
permanently after an RNE-only comparison.

The format grid replaces the three cost-summary cards. It shows four physical
profiles across four row counts using the recorded acceptance/rejection reports;
blank cells mean not in that comparison. A failed fit is not a proof of an
infeasible format. The cost figure now shows candidate order at three stages,
with exact costs and explicit rank positions: before fitting, 32/64/128/256;
after fitted-ROM repricing, 64/32/128/256; after mapping, 128/64/256/32. These are
the same four completed fits viewed with different information available, not
a claim that discovery happened in exactly that order. The original exploratory
runs predated the new logging of architecture-only estimates.

`data/methodology-check.json` records two checks:

- `methodology-verified-rne` replays the pipeline with a previously accepted
  128-row wide RNE table as its initial fit. A nine-word seed header suffices
  for the initial estimate; fitting is then followed by a complete 2^32-input
  check and an after-fit score bound to the exact coefficient profile hash.
  This is a workflow replay, not a new independent candidate discovery.
- `methodology-neighbor64-tt` starts from a new minimax seed and fits the
  64-row medium profile (11/14/24, residual 20, first/result 19/26) with two
  truncations. Complete passes have 51,314, 912 and zero accuracy failures;
  monotonicity violations are 12, zero and zero. The accepted profile maps to
  1282.00 FF units with +292.60 ps setup slack. It meets the same six-cycle,
  one-input-per-cycle 1 GHz contract and passes RTL and mapped scoreboards.
  Thus it does not displace the 128-row truncation candidate at 1228.40.

The runner now rejects mismatched initial-profile headers and nonempty output
directories, preserving both configuration identity and earlier experiment
records. `record_methodology_check.py` binds costs, numerical acceptance, fixture
and mapped source hashes; the article checker independently reconstructs the
canonical profile hashes. Physical implementation remains a later measurement
stage; no placement/routing result is claimed here.

## Methodology revision: numerical quality across all choices

The article and sfu/README.md now distinguish acceptance, numerical quality and
hardware cost. The bound remains at most two representable steps, exact required
special/bypass behavior and monotonicity. Every accepted architecture/coefficient
fit also needs complete error counts at distances exactly 0/1/2, cumulative
within-one-ULP counts, and direction diagnostics on fixed common input domains.
Zero means matching the correctly rounded FP32 reference, not exact real exp2.

Exactly-one counts are not minimized on their own: moving errors from two to one
increases that bin while improving accuracy. For these bounded distributions,
correctly-rounded and cumulative-within-one counts describe the relevant CDF
comparisons. Keep tradeoffs when one improves and the other worsens. Directional
bias is diagnostic; a small signed mean can conceal cancellation.

Area and accuracy are presented separately to the decision maker. Do not invent
a combined weight or automatically select the smallest feasible profile. A pure
win requires no worse area and no worse declared numerical measures, with a
strict improvement somewhere. Cost-stage frontiers are provisional exploration
guides because mapping can reverse cost ordering. This applies to all degrees,
table sizes, coefficient/intermediate widths, narrowing rules and coefficient
words, not only the RNE/truncate comparison.

## Completed quality measurement and first-stage truncation audit

The full quality census now covers all 18 frozen fits, including both failed
RNE grid cells and all 16 mapped accepted fits. Raw counts and common-domain
denominators are in data/numerical-quality.json; the canonical profile hashes
bind every new report to its original coefficient words and mapping. The report
collector preserves all fits and identifies the area/accuracy frontier using
correctly-rounded and cumulative-within-one counts across the full, negative
and near-zero approximation domains. All input encodings have equal weight;
these are not workload-weighted softmax statistics.

The final article comparison combines table resolution, coefficient widths,
retained widths and rounding rules in one table. Its main view emphasizes the
negative approximation domain. Expanded results show the other domains,
directional errors and frontier membership. The area-rank diagram still teaches
the progression of cost information; it is not the final design ranking.

At compact 17-bit widths, RR versus TT changes negative-domain zero-ULP answers
from 38.48% to 50.86% and two-ULP answers from 5.05% to 2.43%. Across the full
approximation domain RR still has more correctly rounded answers. The 64-row
TT medium fit costs 1282.00 and gives 62.76% zero ULP and 0.30% two ULP on the
negative domain. This is an actual accuracy/area tradeoff against compact
128-row TT, rather than a reason to declare the area minimum the winner.

The local fitter still uses violations, maximum sample ULP and summed sample
ULP to guide coefficient moves. The exhaustive archive and frontier do not
claim that each fit optimizes the whole accuracy distribution within its
format. Later coefficient proposals can enter the same collection.

The first-stage truncation area reversal is now traced in
code/rtl/audits/rounding/first-rounding-delta/. Replayed mapped cell histograms
match profiles 8 and 10. Profile 8 has A[9]=0 throughout; profile 10 has A=512
in row 127 and a mapped register carrying the revived bit. The generic top
Booth digit changes from zero to a variable multiple of the residual. Its
mapped FF is traced by cell identity because ABC can leave obsolete variable
netname IDs disconnected after optimization. Common C[22]=1 remains unchanged.

With the original table unchanged, removing first RNE saves 40.70 FF units.
With the refitted table and narrowing unchanged, forcing just A[9] to zero
saves 40.15. These are structural probes, not numerical candidates; each is
a complete remapping. Restored coefficient-bit support is therefore large
enough to offset the rounding saving. Changes to the other refitted bits and
mapping explain why the two probes are not an additive decomposition of the
accepted circuits' +3.45 difference. Supporting source/snapshot hashes and
public normalized results are bound in data/rounding-area-delta.json.


## Narrower 256-row neighbor search

The original resolution comparison did not shrink physical widths at 256 rows.
The follow-up adds 11 frozen profiles: eight exhaustively accepted and mapped,
three unsuccessful fits. They are bound in data/narrow256-study.json and merged
into numerical-quality.json, whose archive now has 29 profiles and 24 accepted
mapped alternatives. The final comparison adds the residual width explicitly;
expanded result identifiers include every width to distinguish nearby profiles.
The RNE grid adds combined 16-, 15- and 14-bit-first-result profiles with
8/13/23-bit coefficients and an 18-bit residual.

The new 256-row 15-bit-first-result truncate/truncate fit maps to 1209.35 units
and dominates the earlier 128-row 1228.40-unit fit in area and both cumulative
quality counts across all three approximation domains. Its negative-domain
zero-ULP fraction is 53.73%, one-ULP 45.78%, remainder two ULP. Other narrower
256-row alternatives remain on the frontier. The article explains why smaller
intervals invite smaller coefficient/intermediate widths and why independent
passing reductions cannot simply be combined. It does not call an unsuccessful
fit an impossibility result. See code/rtl/audits/rounding/narrow256-search.md
for individual hypotheses, attempts, failures, costs and future experiments.


## Center the comparison on the current candidates

The staged-cost diagram now compares 32-row wide, 64-row medium, 128-row
compact-17 and 256-row narrower-15 RNE fits. Its mapped-area leader is the
256-row fit at 1275.85, replacing the earlier equal-width 256-row point. The
width-cost explanation uses 256-row first results of 16 versus 15 bits
(1335.25 versus 1275.85; nine versus eight Booth rows). Rounding comparisons
lead with the 256-row 15-bit profile. The 128-row constant-bit example remains
as a short subsection explaining why whole-circuit costs can reverse a local
rounding saving; it precedes the final results rather than closing the post.


## Remove the 128-row reference-design framing

The published counterexample example now uses narrow256-s15-rne's exhaustive
history (75,704 -> 7,973 -> 0) at fixed widths and RNE modes. The cost discussion
no longer repeats the older 128-row constant-mask example; the short coefficient
bit case explains the 510-to-512 transition without promoting that fit to a
reference design. The final comparison presents current area/quality options
and omits the historical paragraph about superseding the 128-row area minimum.
That dominance result remains in the raw frontier and this log. Neutral 128-row
grid points and measured comparison-table entries remain visible.


## Reorganize coefficient fitting and hardware exploration

The opening now states the two search levels briefly, followed by a compact
accuracy definition and Goldberg reference. Numerical-quality domains and the
frontier explanation sit beside the final comparison. Rounding circuits now
follow Q1/Q2, before the acceptable-output intervals they affect.

The coefficient-fit explanation now includes a real before/after row from
narrow256-s15-rne, exported by //sfu:blog_coupled_move. Row 5 changes A/B from
78/2877 to 58/2878 while C stays 4251473. Two retained inputs have disjoint
allowed-C intervals before the refit and overlapping intervals afterward.
Their errors change from 1/3 to 0/1 steps. This is a before/after refit, not a
claim that those words were one recorded local proposal. The exporter checks
interval endpoints and adjacent rejected words through the forward model.
The export binds the source profiles, witnesses and exporter sources by hash.

The hardware exploration is explicitly guided experimentation around an
automated fixed-format fitter. The 510-to-512 constant-bit example belongs in
the content-aware cost explanation, not a separate rounding-results detour.
The conclusion names the compact 256-row 15-bit TT and more accurate 16-bit RR
implementations to follow in Part 4, without declaring an application winner.


## Make the hardware-search loop explicit

The opening now fixes table size, coefficient formats, internal formats and
narrowing rules before describing the ordered workflow: estimate, fit, evaluate
and refit, synthesize passing fits, then select neighboring hardware points.
The coefficient-fitting section holds all those choices fixed. The rounding
circuit comparison now appears with the hardware experiments, alongside width
and table-size changes, rather than leading the fitting explanation as though
rounding were the primary search problem.


## Consolidate hardware costs and show the search loops

The hardware-cost section now groups table/coefficient widths, multiplier widths,
aligned sums, storage and narrowing rules with normalized costs and reasons.
The RNE/truncation circuit sits inside its cost bullet. The 40.70-unit local
saving is the controlled unchanged-coefficient first-stage comparison from
rounding-area-delta.json; the 4.5 completion rate already includes RNE, so it is
not added again. It is a representative measured delta, not a new width-scaled
rounding law or a change to exported proxy rankings.

hardware-search-flow.svg shows fixed hardware -> dimensional estimate -> fit ->
exhaustive test -> quality/content-aware estimate/synthesis -> neighboring
hardware. Failed tests return to fitting; stalled fits can change hardware.
The opening retains only a short overview to avoid duplicating the full loop.


## Describe the actual directed exploration

The outer hardware choices are made by us, not an automated scalar-cost search.
The published explanation now starts at generous widths with RNE for a chosen
table size, then explains coefficient-width, residual/intermediate-width,
rounding and table-resolution experiments. Every hardware change requires a
new coefficient fit and acceptance check. The inner fitter and counterexample
feedback remain automated. No new numerical experiments were run for this edit.

Removed scalar proxy rates, register-bit area units and the staged-ranking
figure from Part 3. Archived exports and their validation remain intact.
The comparison displays mapped area divided by the smallest mapped area in the
measured accepted set (narrow256-s15-tt). The shared register-area normalization
in the source cancels in these ratios; these are measured cell-area ratios,
not sums of proxy weights. Accuracy data, acceptance and frontier are unchanged.
The flowchart marks our hardware choices separately from automated fitting.


## Move the number-format introduction from Part 2

Part 2 now focuses on subdivision and degree. Its worked integer multiply-add
and fixed-scale rationale move to the introduction of the rounded model here.
The prose keeps the 3*3 + aligned 5 example and a short guard/sticky/tie
explanation, without the earlier decision table and repeated rounding details.
The existing diagram/data are unchanged. The recap and series overview agree
with the new division of topics.


## Connect the hardware point, model and coefficient search

The revised order is hardware choices and experiment heuristics -> workflow ->
accuracy/number formats -> one concrete model -> Remez seed -> integer fitting
and counterexamples -> measured circuits and results. The fixed-point example
now precedes Remez rather than interrupting the transition to interval fitting.
The workflow is explained once near the start.

The model pseudocode uses narrow256-s15-rne: 256 rows; A/B/C formats (8,24),
(13,20),(23,22); residual (18,18); first (15,22); final (25,23); RNE/RNE.
The format pairs are word bits/fractional bits and match the frozen profile
and arithmetic scales. The table is mutable during fitting while the arithmetic
and formats remain fixed. Search pseudocode seeds from Remez and shows the
fit/evaluate/add-witness loop. These are explanatory pseudocode, not another
implementation. No numerical or synthesis results changed.


## Reduce repetition after the series-wide review

Part 1's overview is unchanged. Part 3 now combines the two opening hardware
lists, gives the flowchart the outer-workflow role, keeps the typed model for
fixed arithmetic, and replaces the opaque whole-fit pseudocode with the inner
A/B -> C-range -> model-score loop. Empty intersections still produce trial
words near conflicting bounds, matching the fitter's failure-reduction logic.
The alternation proof and Remez exchange sequence remain; duplicated setup
and transitions are shortened. The main source falls from 3291 to about 2850
words, including pseudocode, captions and navigation.

The accuracy introduction bridges Part 2's illustrative relative error to
FP32 spacing below one. The comparison states the fitter's passing-table
stopping condition and that accuracy distributions are measured afterward.
Area/timing/latency are explicitly scoped to coefficient lookup plus polynomial
pipeline, while numerical validation covers the full FP32 model. The generated
results-table footnote states the same scope. Results interpretation connects
rounding, table resolution and wider arithmetic to their observed tradeoffs.
No numerical fits, area measurements or distributions were changed.
