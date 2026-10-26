#!/usr/bin/env python3
"""Plot how FP32 argument rounding becomes relative exponential error.

Uses the MPFR-exported rounded arguments in data/base-conversion.json. Decimal
arithmetic evaluates the exact identity exp(delta * ln(2)) - 1 without subtracting
nearly equal binary64 exponentials. The reference is the real-valued exponential;
final FP32 output rounding is deliberately a separate step in the article.
"""
import argparse
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, ScalarFormatter

ROOT = Path(__file__).resolve().parents[1]
BLUE, ORANGE, INK, RULE, PAPER = '#3e6a89', '#b86632', '#41484b', '#d8d4ca', '#faf9f6'


def samples():
    rows = json.loads((ROOT / 'data/base-conversion.json').read_text())['rows']
    result = []
    with localcontext() as context:
        context.prec = 80
        ln2 = Decimal(2).ln()
        for row in reversed(rows):
            x = Decimal.from_float(row[0])
            z = x / ln2
            delta = Decimal.from_float(row[2]) - z
            relative_output = (delta * ln2).exp() - 1
            relative_input = abs(delta / z) if z else Decimal('NaN')
            # RNE has at most half an input spacing of absolute error.
            half_spacing = 2**(math.floor(math.log2(abs(float(z)))) - 24) if z else 0
            result.append((float(x), float(abs(delta)), float(abs(relative_output)),
                           float(relative_input), half_spacing))
    return result


def plot(output):
    data = samples()
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 10,
        'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': INK,
        'ytick.color': INK, 'svg.fonttype': 'none',
    })
    fig, ax = plt.subplots(figsize=(8.4, 5.5))
    fig.patch.set_facecolor(PAPER)
    fig.subplots_adjust(left=.12, right=.96, top=.79, bottom=.16)
    fig.text(.12, .95, 'How much output error does an input error cause?', fontsize=14)
    fig.text(.12, .895, 'Relative input error → relative output error', fontsize=10, va='top')
    fig.text(.12, .85, r'FP32 at $x=-76.25$: $3.37\times10^{-8}\;\rightarrow\;2.57\times10^{-6}$',
             fontsize=10)
    ax.set_facecolor(PAPER)
    ax.set_axisbelow(True)
    ax.grid(color=RULE, linewidth=.6)
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color(RULE)
    ax.set_xlim(0, 6.5e-8)
    ax.set_ylim(0, 5e-6)
    ax.xaxis.set_major_locator(MultipleLocator(1e-8))
    ax.yaxis.set_major_locator(MultipleLocator(1e-6))
    for axis in (ax.xaxis, ax.yaxis):
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((0, 0))
        axis.set_major_formatter(formatter)
    ax.tick_params(length=0, pad=7)
    ax.set_xlabel(r'Relative input error $|\delta|/|z|$ ', labelpad=12)
    ax.set_ylabel(r'Relative output error $|2^{z+\delta}/2^z-1|$ ', labelpad=10)
    for original, color in [(-1, BLUE), (-16, '#7c919c'), (-76.25, ORANGE)]:
        # Holding x fixed isolates sensitivity from the FP32 spacing pattern.
        # The slope is |x|, so a common horizontal error has different effects.
        ax.plot([0, 6e-8], [0, abs(original)*6e-8], color=color, linewidth=1.8)
        ax.text(6.07e-8, abs(original)*6e-8, f'x = {original:g}'.replace('-', '−'),
                fontsize=9, color=color, va='center')
        row = next(row for row in data if row[0] == original)
        ax.scatter(row[3], row[2], s=44, color=color,
                   edgecolors=PAPER, linewidths=1, zorder=5)
    selected = next(row for row in data if row[0] == -76.25)
    input_error, output_error = selected[3], selected[2]
    ax.plot([input_error, input_error, 0], [0, output_error, output_error],
            color=ORANGE, linestyle=(0, (4, 4)), linewidth=1)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, facecolor=PAPER, metadata={'Date': None})
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'assets/figures/base-conversion-error.svg')
    plot(parser.parse_args().output)
