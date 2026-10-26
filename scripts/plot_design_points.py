#!/usr/bin/env python3
"""Render the C++ relative-minimax exports as three focused comparisons."""
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/design-points.json').read_text())
DESIGNS = {(d['rows'], d['degree']): d for d in DATA['designs']}
QUADRATIC, CUBIC, REFERENCE = '#1460aa', '#c43c28', '#747d86'
GRAY, INK, RULE, PAPER = '#82949c', '#41484b', '#d8d4ca', '#faf9f6'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':INK,
 'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'svg.fonttype':'none'})


def axes_style(ax, error=False):
    ax.set_facecolor(PAPER)
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['bottom','left']].set_color(RULE)
    ax.grid(axis='y',color=RULE,linewidth=.6)
    ax.set_xlim(0,1)
    ax.set_xticks([0,.5,1])
    if error:
        fmt=ScalarFormatter(useMathText=True);fmt.set_powerlimits((0,0));fmt.set_useOffset(False)
        ax.yaxis.set_major_formatter(fmt)
        ax.axhline(0,color=GRAY,linewidth=.7)


def pieces(ax, n, degree, kind, color, label=None, linestyle='-'):
    design=DESIGNS[n,degree];c=design['coefficients']
    t=np.array([s[0] for s in design['samples']])
    for j in range(n):
        x=(j+t)/n
        if kind=='error': y=np.array([s[1] for s in design['samples']])
        elif kind=='curvature':
            y=2**(j/n)*n*n*sum(k*(k-1)*c[k]*t**(k-2) for k in range(2,degree+1))
        else: y=2**(j/n)*sum(c[k]*t**k for k in range(degree+1))
        ax.plot(x,y,color=color,linewidth=1.7,linestyle=linestyle,label=label if j==0 else None)


def save(fig,name):
    output = ROOT/'assets/figures'/name
    fig.savefig(output,facecolor=PAPER,metadata={'Date':None})
    # Use a browser-available family while keeping labels as searchable text.
    output.write_text(output.read_text().replace("font-family: 'DejaVu Sans'", 'font-family: system-ui, sans-serif'))
    plt.close(fig)


def subdivisions():
    fig, axs=plt.subplots(3,3,figsize=(9,7.3))
    fig.patch.set_facecolor(PAPER)
    x=np.linspace(0,1,600)
    for col,n in enumerate([1,2,4]):
        for row in range(3): axes_style(axs[row,col],row==2)
        # Identical coordinate limits preserve the size of each design's gap.
        # Near f=0 the first fit's discrepancy is large enough to see, while
        # the smaller gaps in the other columns show the improvement directly.
        width=.004
        zoom_x=np.linspace(0,width,300)
        c=DESIGNS[n,2]['coefficients']
        zoom_y=sum(c[k]*(n*zoom_x)**k for k in range(3))
        ax=axs[0,col]
        ax.plot(zoom_x,2**zoom_x,color=REFERENCE,linewidth=2.8)
        ax.plot(zoom_x,zoom_y,color=QUADRATIC,linewidth=2.0,linestyle='--')
        ax.set_xlim(0,width)
        ax.set_xticks([0,width])
        ax.set_xticklabels(['0',f'{width:g}'])
        ax.get_xticklabels()[-1].set_horizontalalignment('right')
        ax.set_ylim(.9996,1.0048)
        ax.set_yticks([1,1.002,1.004])
        fmt=ScalarFormatter(useOffset=False);fmt.set_scientific(False)
        ax.yaxis.set_major_formatter(fmt)
        ax.set_title(f'{n} quadratic'+('' if n==1 else 's'),pad=12)
        ax.set_xlabel('Fractional input f',fontsize=9)
        axs[1,col].plot(x,math.log(2)**2*2**x,color=REFERENCE,linewidth=2)
        pieces(axs[1,col],n,2,'curvature',QUADRATIC)
        axs[1,col].set_ylim(.4,1.02)
        pieces(axs[2,col],n,2,'error',QUADRATIC)
        axs[2,col].set_ylim(-.0019,.0019)
        axs[2,col].set_xlabel('Fractional input f')
        for j in range(1,n):
            for row in [1,2]: axs[row,col].axvline(j/n,color=RULE,linestyle=':',linewidth=.8)
        axs[2,col].set_title(f'Max. relative error {DESIGNS[n,2]["max_relative_error"]:.2e}',fontsize=9,pad=17)
    axs[0,0].set_ylabel('Function value · near f = 0')
    axs[1,0].set_ylabel('Curvature (second derivative)')
    axs[2,0].set_ylabel('Signed relative error')
    fig.legend([axs[0,0].lines[0],axs[0,0].lines[1]],['Exponential','Fitted quadratics'],loc='upper center',ncol=2,frameon=False)
    fig.subplots_adjust(left=.12,right=.98,top=.91,bottom=.08,hspace=.85,wspace=.6)
    save(fig,'quadratic-subdivision.svg')


def cubic():
    fig,axs=plt.subplots(3,3,figsize=(9,7.5));fig.patch.set_facecolor(PAPER)
    x=np.linspace(0,1,600)
    zoom_x=np.linspace(0,.004,300)
    for col,n in enumerate([1,2,4]):
        for row in range(3): axes_style(axs[row,col],row==2)
        ax=axs[0,col]
        ax.plot(zoom_x,2**zoom_x,color=REFERENCE,linewidth=2.5,label='Exponential')
        for degree,color,name in [(2,QUADRATIC,'Quadratic'),(3,CUBIC,'Cubic')]:
            c=DESIGNS[n,degree]['coefficients']
            values=sum(c[k]*(n*zoom_x)**k for k in range(degree+1))
            ax.plot(zoom_x,values,color=color,linewidth=2.0,
                    linestyle='--' if degree==3 else '-',label=name)
            pieces(axs[1,col],n,degree,'curvature',color,linestyle='--' if degree==3 else '-')
            pieces(axs[2,col],n,degree,'error',color,linestyle='--' if degree==3 else '-')
        ax.set_title(f'{n} interval'+('' if n==1 else 's'),pad=12)
        ax.set_xlim(0,.004);ax.set_ylim(.9996,1.0048)
        ax.set_xticks([0,.004]);ax.set_yticks([1,1.002,1.004])
        ax.get_xticklabels()[-1].set_horizontalalignment('right')
        ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
        ax.set_xlabel('Fractional input f',fontsize=9)
        axs[1,col].plot(x,math.log(2)**2*2**x,color=REFERENCE,linewidth=2.5,zorder=1)
        axs[1,col].set_ylim(.4,1.02)
        axs[2,col].set_ylim(-.0019,.0019)
        axs[2,col].set_xlabel('Fractional input f')
        for j in range(1,n):
            for row in [1,2]: axs[row,col].axvline(j/n,color=RULE,linestyle=':',linewidth=.8)
        quad=DESIGNS[n,2]['max_relative_error'];cub=DESIGNS[n,3]['max_relative_error']
        axs[2,col].set_title(f'Max. error: quadratic {quad:.2e}\ncubic {cub:.2e}',fontsize=9,pad=17)
    axs[0,0].set_ylabel('Function value · near f = 0')
    axs[1,0].set_ylabel('Curvature (second derivative)')
    axs[2,0].set_ylabel('Signed relative error')
    fig.legend(axs[0,0].lines,['Exponential','Quadratic','Cubic'],loc='upper center',ncol=3,frameon=False)
    fig.subplots_adjust(left=.12,right=.98,top=.91,bottom=.08,hspace=.9,wspace=.6)
    save(fig,'cubic-curvature.svg')


def exchange():
    fig=plt.figure(figsize=(8.4,5.8));fig.patch.set_facecolor(PAPER)
    ax=fig.add_axes([.13,.12,.83,.48]);axes_style(ax,True)
    for n,d,color,label in [(4,2,QUADRATIC,'4 quadratic rows'),(2,3,CUBIC,'2 cubic rows')]:
        pieces(ax,n,d,'error',color,label)
    ax.set_xlabel('Fractional input f');ax.set_ylabel('Signed relative error')
    ax.legend(loc='upper left',bbox_to_anchor=(0,1.21),ncol=2,frameon=False)
    for y,n,d,color in [(.91,4,2,QUADRATIC),(.78,2,3,CUBIC)]:
        fig.text(.13,y,f'{n} rows × {d+1} coefficients: {n*(d+1)}W table bits; {d} multiply-add stages',color=color,fontsize=11)
        strip=fig.add_axes([.13,y-.055,.83,.025]);strip.set_xlim(0,1);strip.set_ylim(0,1);strip.axis('off')
        for j in range(n):
            strip.add_patch(plt.Rectangle((j/n,0),1/n-.004,1,facecolor=color,alpha=.3))
    save(fig,'table-arithmetic-choice.svg')

if __name__=='__main__':
    subdivisions();cubic();exchange()
