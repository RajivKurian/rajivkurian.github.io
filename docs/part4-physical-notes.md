# Physical-design follow-up — on hold

The physical-design work is paused at the user's request. Part 4 deliberately
uses synthesis-only measurements to keep the implementation exploration simpler.
Its opening explains that physical timing/power and the work required for clock
trees, buffering, sizing and setup/hold repair should ideally guide exploration.
Do not fold these physical experiments into the article without revisiting its
scope and comparison tables together.

## Findings to retain

OpenROAD is built and published independently under `eda/dist/`; the binary and
archive checksums are in `eda/dist/openroad.lock.json`. Source/dependency locks,
build scripts and platform setup are in `eda/openroad/`. Research-code changes
do not rebuild it.

The complete experiment log is
[code/rtl/physical/RESULTS.md](../../code/rtl/physical/RESULTS.md).
[comparison.json](../../code/rtl/physical/comparison.json) contains the final
common-flow measurements. Raw runs retain routed ODB/DEF/Verilog, extracted
SPEF, per-stage timing, DRC reports, checked activity, power and input hashes.

- Four-cycle 1 ns circuit: +42.09 ps setup, +15.80 ps hold, 306.282 µm² cells.
- Four-cycle 800 ps hybrid: −6.44 ps setup, +19.22 ps hold, 310.889 µm² cells.
- Six-cycle 700 ps circuit: −31.68 ps setup, +18.52 ps hold, 353.084 µm² cells.
- All three have zero router-reported DRC violations, all signal nets routed,
  and passing 16,392-cycle fixed-point-model checks with reset and bubbles.
- Both tighter targets fail in lookup/input capture. Their arithmetic register
  stages pass. Additional arithmetic pipelining does not address those paths.
- At 1 ns, estimated power changes from 0.846 mW after synthesis to 1.235 mW
  with extracted wires and clock-tree cells. The clock tree contributes 0.203 mW.
  Activity uses ideal-delay transitions, so delay-generated glitches are omitted.

## Flow fixes already investigated

Short, double-width IO pins caused 273 persistent M5 violations, all at the
north IO edge. Normal-width, 0.2 µm-long pins with 0.4 µm minimum spacing
resolved that plateau. A 10 ps pre-route hold margin removed small extracted
hold failures. Repairing timing again with global-route parasitics substantially
improved the 700 ps lookup, but did not close it. Better global-route timing did
not always translate to better extracted timing: retain both measurements.

These are block-level ASAP7 RVT TT experiments at 0.7 V and 25 °C. Router DRC
checking has been performed; separate GDS signoff DRC/LVS has not. Keep these
physical results separate from the article's synthesis-only data.

## When this work resumes

Start with the recorded lookup critical paths: inspect address fanout, decode
placement, buffering and cell drive strengths. Compare changes under the same
floorplan, corner, IO constraints, clock uncertainty and repair margins. Examine
placement sensitivity before attributing small differences to a generator knob.
Only then consider changing lookup structure or pipeline boundaries. Preserve
all existing failed and passing runs rather than rebuilding unchanged probes.
