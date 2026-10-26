# Exponential hardware: four-post plan

Status: editorial plan. Post titles are descriptive. Detailed research and
measurements live in the independent code/ and eda/ repositories; the article
repository consumes exported artifacts. Each post will publish as one HTML page.

## Writing and presentation

Keep the softmax motivation to a short paragraph. Explain algorithms, bit widths,
design choices and measurements directly. Avoid catchy narrative headings,
artificial transitions and repetitive production-readiness qualifications.

Keep the blog theme static and understated. Content interactions should answer a
specific question. Provide useful diagrams or static views when a widget adds
nothing. Reuse a table row, error plot and datapath across posts so comparisons
remain easy to follow.

Each post starts with a short recap (except Part 1), its current question,
and a numbered series outline with titles, topic descriptions, links to existing
posts and a current-post marker. Part 1 opens with the series goal and outline
before motivation.

## 1. Computing exp2

Question: what makes exponential hardware expensive, and what does base two
simplify?

- Open with the series goal, numerical/throughput targets and four-part scope.
- Define S = QK^T/sqrt(d), P = softmax(S), O = PV and their matrix shapes
  before using attention shorthand.
- Brief motivation: attention produces MN scores with approximately MNK matrix
  work, then performs scalar operations over MN scores. The arithmetic-work
  ratio scales with K; increasing matrix throughput makes surrounding operations
  more visible. This is a work comparison, not a direct latency prediction.
- Define FP32 input/output, 2 ULP, one result per cycle per lane, and attention to
  negative inputs and zero.
- Compare direct lookup, arithmetic, and range-reduced approximation.
- Explain 2^x = 2^n 2^f and e^x = 2^n e^r with x = n ln(2) + r.
- Explain why direct exp is a viable design. Compare range reduction and constant
  precision rather than treating the mathematical base as inherently costly.
- Explain why Taylor is locally accurate but not the best fixed-degree fit over
  an interval. Introduce minimax error and Remez before the detailed later search.
- Show the error introduced by FP32 rounding of x log2(e). Higher-precision
  conversion or combination with an existing input scale must account for it.

Visual: one guided zoom shows the same quadratic on [−2, 2], [−1, 1],
[−½, ½] and [−¼, ¼]. One play/pause button; no parameter controls. Explain
the scaled-copy identity with a numerical example in the prose.
Explain base-conversion error with two worked examples, including FP32 spacing
and the resulting output error. Do not add an error-inspection widget or an
architecture inventory before the reader understands the mathematical reason.

## 2. Range reduction, tables and polynomial degree

Question: why do more polynomial pieces or a higher degree help, and what
hardware does each choice require?

- Begin with why one quadratic is insufficient even on [0,1]: its curvature is
  constant while exponential curvature increases. Show one, two and four fitted
  quadratics, with their curvature and errors on the same physical interval.
- Explain what a coefficient table provides only after showing why different
  coefficients in different regions help. Each input evaluates one polynomial.
- Compare independently fitted quadratic and cubic curves at one, two and four
  intervals, with identical coordinate limits across the design columns. A cubic's
  curvature can vary within an interval. No Taylor construction in this part.
- Define j=floor(Nf), t=Nf-j after motivating multiple pieces. Use f=11/16,
  N=8 to show row 5 and t=1/2. Explain that row coefficients already include
  the interval's position.
- Compare eight quadratics and two cubics at one 5e-6 real-fit target. Count
  coefficient values and multiply-add stages; briefly note address/residual
  widths and coefficient-range effects. Treat quadratics as the architecture
  developed next, not a scalar-cost winner.
- Leave fixed-point arithmetic, rounding and coefficient fitting to Part 3,
  and detailed circuit implementation to Part 4.

Presentation: two static fit comparisons with prose between them. Preserve
common-scale close-ups, curvature and errors. No widget controls, weighted
costs, Booth diagrams or numerical fixed-point detour in Part 2.

## 3. Remez, coefficient search, accuracy testing and hardware cost

Question: how do we fit coefficients for fixed arithmetic and choose useful hardware experiments?

- Start with the hardware point and the structural reasons for trying width,
  rounding and table-size neighbors. Show the search workflow once.
- Briefly explain the accuracy contract, fixed-point representation and one
  numerical multiply-add. Define a concrete recorded hardware model in pseudocode,
  keeping table words mutable and circuit formats/operations fixed.
- Explain the Remez coefficient/error solve, four alternating extrema, stationary
  points, exchange, precision and convergence.
- Convert acceptable rounded outputs to accumulator intervals, invert rounding,
  and solve the integer c interval for fixed a,b.
- Explain coupled moves across unequal coefficient quantization scales.
  Show the fit/model/exhaustive-feedback loop in short pseudocode.
- Classify failures by row, residual position, intermediate rounding and joins;
  use witnesses and neighboring FP32 inputs to guide further fitting.
- Recheck every learned point and keep fresh held-out audits separate from
  fitting. Show the actual failed and revised tables from methodology_audit.json.
- Explain the directed hardware experiments: start with generous widths and
  RNE, reduce coefficient/internal widths, try truncation, change table size
  and refit. Circuit reasoning and observed failures suggest the next experiment.
- Show the fixed-point coefficient-fit loop and our selection of new hardware
  points separately in a flowchart. Present measured area ratios and accuracy,
  without a scalar proxy ranking claimed to drive an automated outer search.

Presentation: one guided Remez sequence, a real before/after integer-C
intersection diagram, a narrowing circuit, a search flowchart and recorded
hardware experiments. Keep ULP background brief with a reference. Show measured
area and error distributions rather than weighted resource inventories.
Search RNE and truncation independently at both Horner narrowing points, refit
each configuration, and compare synthesized feasible designs at common timing,
latency and throughput. Do not assume truncation wins: extra precision can cost
more than rounding logic. Sampled tests reject and refine; accept only after
exhaustive software evaluation of all FP32 encodings, including special cases,
subnormal reconstruction and monotonicity. Keep run scopes and provenance in
supporting notes.

## 4. Generating RTL and searching implementation choices

Question: with a numerical design fixed, which circuit structures give the best
area, timing and power, and how can we explore them systematically?

The lesson is to identify the design's independently changeable parts, encode
those choices in a custom RTL producer, and use measured experiments to improve
the implementation. Booth recoding is one of those parts. The post should follow
the search rather than become an arithmetic-circuit tutorial.

- Begin with the fitted design from Part 3: coefficient words, binary points,
  narrowing rules, interface, throughput and latency. These define the numerical
  behavior that each implementation must preserve.
- Identify the implementation choices with one annotated diagram: which operand
  to recode, whether to carry or regenerate decoding, compressor organization,
  carry completion, register cuts, and constant propagation from coefficient words.
  Explain why each can change area, timing or switching.
- Open with the reason for a problem-specific generator: a fitted computation
  leaves many implementation choices, and writing each combination by hand slows
  exploration. Numerical configuration plus selected hardware knobs produce RTL.
  Another problem would need its own generator and relevant knobs.
- Explain each atom with a worked example, diagram and competing costs before
  showing the exploration loop. Keep backend languages and serialization out.
- Start from the handwritten implementation and the comparable generated seed.
  Change individual choices, record their outcomes and retain useful area/timing/
  power tradeoffs. Then combine promising changes and test those combinations.
- Tell the actual experimental sequence: column compression reduced both logic
  and stored bits; shared residual decoding traded repeated logic for 27 extra
  registers; combining shared decoding with the better compressor still lost.
  Show the measured comparisons and explain the structural reasons.
- Use the experiment record to choose the next mutations. Distinguish the directed
  experiments we actually ran from an automated evolutionary controller. The
  producer and retained records make either possible without rewriting RTL.
- Explain how implementation results feed back into Part 3: the best circuit for
  one numerical design can change which neighboring width/table designs are worth
  fitting. Keep the numerical-design and circuit-implementation searches distinct.

Presentation: worked atom diagrams, followed by the generation/check/measurement
loop. A prebuilt interactive viewer selects recorded circuits and shows a block-level
SVG, a block-specific logic excerpt and expandable exact source, and measured
area/timing/power/register counts. Keep diagrams above bit level in that viewer.
Keep ROM rows collapsed in their own tab. Clicking each relevant circuit block
selects its explanation and code; alternative colors match circuit and code
highlights. Trace local aliases to saved assignments. Use the same saved
measurements in the result plot. Introduce Yosys/ABC/OpenSTA,
Verilator and ASAP7 with links. No code downloads.

## Assets and publication

- Keep browser code and CSS scoped to each content interaction.
- Inline supported assets and data into each HTML post. Avoid runtime network
  fetches for reproducible examples; native MathML handles equations.
- Copy exported datasets into data/ with code commit, environment identity,
  target names and source hashes in provenance records.
- Present recorded RTL inline in the implementation viewer; do not publish code downloads.
- Keep this plan and theme-validation fixtures out of the public render list.
- Add GitHub repository/profile links when the author provides their URLs.
