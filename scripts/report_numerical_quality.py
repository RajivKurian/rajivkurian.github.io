"""Present frozen exhaustive distributions next to their mapped design costs."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
study=json.loads((root/'data/numerical-quality.json').read_text())
records=[r for r in study['records'] if r['exhaustive']['accepted']]
# Group by architecture, then rounding. This keeps the RNE/truncation quartet
# adjacent without hiding the wider or different-resolution alternatives.
records.sort(key=lambda r: (r['table_bits'], -r['shape'][4], *[-v for v in r['shape']], not r['first_rne'], not r['final_rne']))
area_reference=min(records,key=lambda r:r['mapped_cost'])
def percent(count,stats):return f"{100*count/stats['count']:.2f}"
def name(r):
    return f"{1<<r['table_bits']} · "+'/'.join(map(str,r['shape']))+' · '+''.join('R' if r[k] else 'T' for k in ['first_rne','final_rne'])
def row(r,domain):
    s=r['exhaustive']['quality'][domain]
    return [percent(v,s) for v in s['ulp'][:2]]
lines=['<!-- Generated from numerical-quality.json by report_numerical_quality.py. -->', '', '::: {.quality-results}', '',
       '| Rows | Coefficient bits a/b/c | Residual bits | Result bits s/y | Q₁/Q₂ | Mapped area¹ | 0 ULP % | 1 ULP % |',
       '| ---: | :--- | ---: | :--- | :---: | ---: | ---: | ---: |']
for r in records:
    values=row(r,'negative_approximation')
    lines.append('| '+' | '.join([str(1<<r['table_bits']), '/'.join(map(str,r['shape'][:3])), str(r['shape'][3]), '/'.join(map(str,r['shape'][4:])), '/'.join('R' if r[k] else 'T' for k in ['first_rne','final_rne']), f"{r['mapped_cost']/area_reference['mapped_cost']:.3f}×",*values])+' |')
lines+=['', '¹ Mapped area is relative to the smallest measured circuit: 256 rows, 8/13/23-bit coefficients, 18-bit residual, 15/25-bit results and two truncations (**1.000×**). The ratios use synthesized cell area; Part 4 examines the implementation. **R = RNE; T = truncation.** **The remaining percentage is at two ULP.** All fits meet the two-ULP bound and monotonicity requirement. Area and timing cover coefficient lookup and the polynomial pipeline, with one input per cycle, six cycles of latency and the same 1 GHz clock target.', '',
        '<details>', '<summary>Other input ranges, error direction and the accuracy/area frontier</summary>', '',
        'The main table counts each of the **278,265,855** FP32 inputs in $-150<x<-2^{-26}$ once. Each FP32 encoding in this range has equal weight. The table below compares the full approximation range and the near-zero subset too. Here a design is identified by **rows · a/b/c/residual/first/result widths · rounding pair**.', '',
        '| Design | All approximation: 0 ULP % | All approximation: 1 ULP % | Near zero: 0 ULP % | Near zero: 1 ULP % | Negative: below % | Negative: above % | Frontier² |',
        '| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |']
for r in records:
    a=r['exhaustive']['quality']['approximation'];z=r['exhaustive']['quality']['near_zero'];n=r['exhaustive']['quality']['negative_approximation']
    lines.append('| '+' | '.join([name(r),percent(a['ulp'][0],a),percent(a['ulp'][1],a),percent(z['ulp'][0],z),percent(z['ulp'][1],z),percent(n['below'],n),percent(n['above'],n),'Yes' if r['frontier'] else 'No'])+' |')
lines+=['', 'The full approximation domain contains **555,089,918** inputs in $-150<x<128$, excluding $|x|\le2^{-26}$. The near-zero subset contains **218,103,808** inputs in $[-1,-2^{-26})$. The remaining **3,723,100,162** finite encodings use common exact-result bypasses; all have zero error for every accepted fit. Nonfinite behavior is checked separately.', '',
        '² The frontier uses area, correctly rounded counts and within-one-ULP counts in **all three approximation domains**. A “No” means another measured design is no worse in every one of those measures and better in at least one. The rounded percentages shown here are for readability; comparisons use the integer counts.', '',
        '</details>', '', ':::', '']
(root/'includes/design-quality-results.qmd').write_text('\n'.join(lines))
