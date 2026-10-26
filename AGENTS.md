# Article conventions

Use descriptive titles and direct technical prose. Avoid catchy narrative
headings, artificial story framing, and repetitive production-readiness caveats.
Explain the mathematics, design choices and evidence.

Published prose explains our choices and their reasons; it should not read as
instructions to the reader (“report this,” “keep that,” “use these”). Describe
what an algorithm does and why, and distinguish completed experiments from
planned measurements. Do not turn a proposed methodology into a claim of work
already performed merely to replace an imperative with “we did.”

Do not invent author biography, social profiles, publication dates, or completed
results.

Keep the site shell plain: system fonts, restrained colors, readable line length,
ordinary links, and no animated theme effects. Rich interaction belongs inside
article content, with keyboard-accessible controls and a useful static view.

Quarto builds this independent repository. Rendering does not execute research
code or depend on sibling code/ or eda/ checkouts. Export data explicitly and
record its provenance. Keep supported resources embedded in each post's HTML.
Use scripts/site.py for setup, preview, build, and validation.

## Educational writing

Write for a college student who knows calculus and floating point. Start with
the mathematical question and concrete examples. Explain why a method helps
before describing its operations or hardware blocks. Do not open with a plan
of the implementation. Avoid vague compression metaphors and closing block
inventories that repeat the mechanics without explaining the mathematics.

Use literal section titles such as “Error from base conversion.” Do not turn
headings into slogans or stories about budgets, journeys, machines, or tradeoffs.
Avoid compressed summaries such as “n supplies the binary scale” or “the
number format handles the rest.” State the identity and the operation it permits:
2^x = 2^n 2^f; approximate 2^f, then multiply by 2^n by adjusting the exponent
for normal outputs. Apply this direct explanatory style within paragraphs as
well as headings. Avoid metaphors such as buying accuracy or paying for hardware.
No author bylines on posts or templates; the site already identifies the author.

Less is more: add a widget only when manipulating it establishes an idea that
static prose or two worked examples cannot explain as clearly. Introduce the
question before the visual and interpret its result afterward. Error plots
need an explanation of where the error comes from and what the scale means.
A collection of error readouts is not a substitute for teaching the cause.
Prefer static diagrams separated by explanatory prose when each comparison
needs its own explanation. Do not add navigation controls just to reveal the
next comparison. For a visual claim that benefits from motion, prefer a short
guided sequence over controls for every parameter. Change one design choice per step and keep the function interval
fixed. Show the old and new curves and explain their changed shape; a sequence
of summary error numbers alone does not teach the cause.

After its series introduction, Part 1 gives a brief, explicit softmax motivation: its formula, why the
maximum is subtracted, and the MNK versus MN work comparison. Then introduce
exp2. Keep this opening short; do not expand it into an attention tutorial.

Support the softmax throughput thesis with sourced model head shapes and GPU
rates. Distinguish head width from hidden size, MACs from FLOPs, and QK-only
work from both attention matmuls. Label peak-rate balance calculations as such;
use dense matrix rates and name the exponential precision. Do not present a
peak-rate calculation as a measured end-to-end kernel bottleneck.

Open the first post with the series goal and scope before the motivation.
Define attention matrices and the weighted-sum product before using QK or PV
shorthand. When introducing Taylor approximations, explain their local objective
and why a fixed-degree minimax fit can improve the worst error over an interval.
Introduce Remez and rounded-coefficient search as the next steps, without
requiring the reader to know approximation theory already.

Keep attention background succinct but self-contained: give the computation,
matrix roles/shapes, row-wise softmax and operation count once. Refer readers
to FlashAttention papers for the broader algorithm and implementation; avoid
repeating shape explanations or expanding into an attention tutorial.

## Series navigation

Every series post opens with a short recap of what earlier parts established,
then states what this part covers and lists the series titles and topics in
order. Link existing posts and mark the current one. Part 1 has no recap: open
with the series goal, then the titled outline and motivation. Keep titles
consistent with index.qmd and update the outlines when the series changes.

When presenting an approximation polynomial, derive or motivate its coefficients
before using it in a visual. Name the approximation when it first appears;
explain how its conditions determine the coefficients rather than simply
asserting that it matches the curve.

For mathematical methods, use authoritative mathematical references and
relevant papers, with specific sections that support the explanation. Author-
and university-hosted papers are welcome. Link external references directly;
do not copy or host them in this repository.
Library documentation can supplement implementation details, but should not be
the main reference for minimax theory or Remez.

When discussing exponential throughput pressure, include dense FP8 attention
matmuls alongside BF16/FP16 and keep softmax precision explicit. State whether
a published rate is per GPU, per system, or per SM per cycle; use the named
SKU rather than substituting a higher-clocked family configuration.

Put units directly in table headers. Compare demand and capacity on the same
time and hardware basis; for architecture comparisons prefer FLOPs/SM/cycle
and exponential results/SM/cycle, with a dimensionless demand/capacity ratio.
Use scientific notation for relative FP error. Keep labels and explanatory
text outside plotting areas when they would obstruct curves or guides.

Part 2 focuses on range reduction, subdivision and polynomial degree. Show one,
two and four independently optimized quadratics and cubics with their curvature
and common-scale close-ups/errors. Use relative-minimax fits, not Taylor seeds.
Explain j=floor(Nf), t=Nf-j with a short numerical example and state that the
selected row already includes its interval's location.

Close Part 2 with eight quadratics versus two cubics at one illustrative
real-fit error target: coefficient values, table rows and multiply-add stages.
Briefly explain that fewer address bits leave a wider residual and that wider
intervals can require larger coefficients. Choose quadratics as the architecture
to investigate, without claiming a scalar-cost winner. Tease finite precision,
coefficient fitting and measured area in Part 3. Keep weighted costs, Booth
circuits, pipeline inventories and synthesis out of Part 2.

Introduce fixed point in Part 3 where the rounded model is defined. Explain why
known ranges permit fixed scales, how constant alignment uses wiring, and why
FP32 interfaces do not require FP32 internal arithmetic. Keep one numerical
multiply-add diagram and a concise guard/sticky/tie explanation. Narrowing
introduces rounding error; register placement alone does not. Avoid duplicating
this detour in Part 2.

When fitted and reference curves overlap at full scale, include a coordinate
zoom. Columns comparing designs must use identical horizontal and vertical
limits so visible gaps reflect the improvement. Distinguish line styles and
retain common-scale error comparisons. Keep figure commentary interpretive;
do not repeat captions and axes in the prose.

Part 3 treats intermediate RNE versus truncation as a co-design search choice,
along with coefficient and retained widths. Explain both possible outcomes:
refitting may compensate for truncation, or RNE may avoid enough extra width
to produce smaller hardware. Use synthesis to compare feasible alternatives;
do not preselect the cheaper-looking rounding operation as the winner.

Call a candidate a 2-ULP design only after exhaustive software-model validation.
Sampled tests identify promising candidates and counterexamples. Keep their
scope explicit in supporting results; do not present a sampled maximum as a
global error bound or an acceptance result.

Part 3 must show how table resolution and precision profiles were chosen before
comparing internal rounding modes. Use recorded candidates and counterexample
feedback, not unexplained final widths or a widget full of controls. Describe
the directed hardware experiments and show synthesized area alongside accuracy;
Part 4 supplies the RTL details. Illustrate truncation and RNE with a circuit. Distinguish the local rounding-circuit saving from the
cost of a complete refitted table and pipeline. A failed fit rejects its words;
it does not prove that no coefficients can work in that format.

Explain the algorithm independently of its implementation language or research
code organization. Say “model” when discussing numerical evaluation; keep C++,
executable names and tooling mechanics in supporting implementation notes unless
they are necessary to explain the algorithm.

Part 3 describes directed hardware experiments with automated coefficient
fitting inside each fixed design point. We choose table sizes, coefficient and
internal formats, and narrowing rules using circuit reasoning and observed
failures/accuracy. Changing those choices requires a new coefficient fit and
acceptance check. Do not imply an automated outer hardware search, scalar proxy
objective, or demonstrated proxy-ranking strategy. Explain each experiment's
hypothesis and measured outcome. Present mapped-area ratios without register-bit
resource scores. Keep archived proxy experiments in supporting records.

Present a short procedure overview before the mathematics and a flowchart before
the hardware experiments. Show the failed-input feedback within a fixed point
separately from our choice of a new hardware point. Revisit widths and rounding
after changing table size. Constant coefficient bits affect registers and
consuming arithmetic as well as ROM lookup; state only propagation confirmed
in RTL. Part 2 motivates the structural tradeoffs that suggest the Part 3 experiments.

Passing two ULP is eligibility, not a numerical-quality ranking. Explain and
report distributions at zero/one/two ULP plus cumulative within-one-ULP results
for all table sizes, degrees, widths, rounding rules and coefficient fits.
Compare common fixed input domains and separate exact bypass populations.
Present accuracy/area tradeoffs for the decision maker without an invented
combined score. Identify pure wins in the declared objectives. Label existing
area-only comparisons as such; do not claim a preferred design before its
numerical-quality distribution is available.

When the methodology introduces comparison metrics, carry them into the actual
experiments and result tables. A paragraph describing distributions or a
frontier is not a substitute for measuring them. Combine nearby architecture,
precision and rounding alternatives in a consistent comparison rather than
scattering isolated area results through the prose. Explain area reversals
with traced circuit changes and controlled comparisons, distinguishing
structural probes from numerically accepted designs.

Integrate new experiments into the existing explanation of the design space;
do not append a section merely because that experiment was performed last.
Use a compact circuit example to explain what changed and why it matters for
the search methodology. Keep controlled-probe mechanics and extra cost deltas
in the experiment log when the main text can explain the finding directly.

Organize the article around the measured design space, not a sequence of old
reference designs being replaced. When results change, audit examples, figure
data, labels, transitions and conclusions together. Avoid calling an earlier
candidate the baseline or discussing its supersession unless that history is
itself needed to teach the algorithm. Keep such history in experiment notes.


Published prose should explain the current method directly. Remove arguments
against earlier drafts, such as “not weighted resource scores,” when the contrast
only makes sense to someone who saw the revision history. Define the quantity
and its basis positively. Preserve contrasts that teach a real mathematical or
hardware distinction; do not mechanically delete every “not” or “rather than.”


Part 3's exposition follows hardware point -> arithmetic model -> starting
coefficients -> fitting the rounded model -> measured experiments. Introduce
hardware choices and the reasons to try neighbors before Remez. Show short
pseudocode for a concrete recorded point, with typed coefficient rows, residual
and result formats, and both narrowing operations. Distinguish changing table
words inside the automated fitter from changing hardware parameters between
experiments. Use the same model when explaining Remez initialization, interval
constraints and exhaustive counterexample feedback. Introduce fixed-point
representation before the model so it does not interrupt that progression.


Keep Part 1's broad mathematical motivation; Part 3 refines it with algorithms
and measurements. Avoid repeating procedural setup around every representation:
the flowchart explains hardware exploration, typed pseudocode defines the model,
and inner-loop pseudocode shows coefficient proposals, C constraints and scoring.
Improve explanatory coverage by replacing redundant text rather than continually
lengthening Part 3.

State measurement scope where results are introduced: current area, clock and
latency comparisons cover coefficient lookup plus the polynomial pipeline.
Full-model FP32 accuracy includes range reduction and reconstruction. Do not
call these measured blocks the complete FP32 exp2 unit. Explain the fitter's
stopping condition separately from the accuracy metrics reported for its fits.

Part 4 opens with the reason for a problem-specific RTL generator: a fitted
numerical design still leaves implementation choices, and generating that family
makes it practical to explore them. Explain the selected atoms with worked
examples and diagrams before the exploration procedure and measured results.
Keep implementation languages and serialization formats out of this explanation.
Use prebuilt recorded circuits for the interactive RTL/results viewer, with
block-level diagrams and scrollable highlighted source. Do not publish code
archives or download links for these examples.

The RTL viewer is a custom circuit inspector. Selecting a diagram block shows
that block's explanation, logic excerpt and expandable exact source. Keep ROM
contents in a separate tab with coefficient rows collapsed. Use consistent
colors for implementation alternatives in the circuit and code highlights.
Trace readable aliases and changed-code examples to recorded circuit graphs;
do not substitute a generic structural outline for the implementation.

Design-choice sections explicitly enumerate the implemented alternatives before
comparing them. Give each alternative a matching circuit view with consistent
positions and colors. For Booth recoding, distinguish local a/s recoding, local
t recoding at both multipliers, and shared t decoding with carried controls.

Keep measured area, slack, power and mapped flip-flop totals out of design-choice
diagrams. Explain structural widths and storage requirements there; present
measured outcomes in the results section and circuit inspector.

Organize Part 4's implementation experiments by clock target. Explain the
limiting stage and why each generated change might help before presenting its
measurement. Compare carry logic against additional storage/stages, and retain
latency/power tradeoffs. Show prepared experiments for the selected target in
the inspector rather than an unstructured inventory of design combinations.
New pipeline structures belong in the generator and its model checks.

Explain compression through its circuit purpose: defer carry propagation while
reducing multiple addends to two rows. Introduce one 3:2/full-adder cell, then a
small symbolic multiply-add whose complete alternative networks and final
addition fit in the diagrams. Show named signal bits, not a series of evaluated
decimal totals. Explain zero-input simplification to half adders and carry
dependencies between layers. Compare whole circuits; fewer compression cells
can move work into the final adder instead of removing it.

Part 4 explains the generator inputs and their concrete generated circuit before
the exploration loop. Measured optimizations get focused before/after diagrams:
show the changed row support, carry boundaries or work across a cut. Trace bit
patterns to recorded circuits, and use identical weights when comparing row
storage. Generic labeled boxes alone do not explain a storage reduction.

Conclude each clock-study experiment, including timing failures, with a complete
pipeline snapshot using recorded per-stage slack. Highlight failing stages and
the least-margin passing stage. Explain how that timing picture suggests the
next experiment; a global worst-slack number does not locate the problem.

Part 4 uses high bits on the left consistently for product rows, compression
and carry completion; carries travel toward higher weights on the left. Teach
compressor-output arrival differences before comparing carry networks. Define
unified completion before the experiments, separating the numerical truncation
boundary from an implementation split. Distinguish overlap that motivates a
hybrid from the measured cell-level reason one specific mapped circuit wins.
