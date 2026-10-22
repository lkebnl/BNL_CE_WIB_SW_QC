"""
Plotting helpers for Item 05 (Noise Evaluation) of the FEMB QC report.

Color convention (fixed for the whole chapter, Okabe-Ito color-blind-safe):
    each FE gain always uses the same color, from cool (low gain) to warm (high gain).
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

GAINS = ['4_7', '7_8', '14_0', '25_0']
GAIN_LABEL = {'4_7': '4.7 mV/fC', '7_8': '7.8 mV/fC', '14_0': '14 mV/fC', '25_0': '25 mV/fC'}
GAIN_COLOR = {'4_7': '#0072B2',    # blue
              '7_8': '#009E73',    # bluish green
              '14_0': '#E69F00',   # orange
              '25_0': '#D55E00'}   # vermillion

PEAK_TIMES = ['0_5', '1_0', '2_0', '3_0']
PEAK_LABEL = {'0_5': '0.5 us', '1_0': '1 us', '2_0': '2 us', '3_0': '3 us'}

# SELC runs at 14 mV/fC, so its leakage-current steps are shades of the 14 mV/fC orange
LEAKAGES = ['100pA', '500pA', '1nA', '5nA']
LEAKAGE_LABEL = {'100pA': '100 pA', '500pA': '500 pA', '1nA': '1 nA', '5nA': '5 nA'}
LEAKAGE_COLOR = {'100pA': '#F2BF5E', '500pA': '#E69F00', '1nA': '#AD7400', '5nA': '#6B4700'}

# Interface modes for the SEON/DIFF summary plot; 200 mV BL solid, 900 mV BL dashed (same as SE plot)
MODE_COLOR = {'SEON': '#4D4D4D', 'DIFF': '#CC79A7'}

FAIL_STYLE = dict(marker='x', color='#C00000', s=90, linewidths=2.5, zorder=5)
WARN_STYLE = dict(marker='^', facecolors='none', edgecolors='#8B6508', s=80, linewidths=2, zorder=5)

INK = '#222222'
INK_MUTED = '#666666'
GRID = '#E3E3E3'

NCH = 128
CHIP_CH = 16

# Font sizes (pt); the figure is shown about half size in the report, so keep them large
FS_SUPTITLE = 17
FS_TITLE = 14
FS_LABEL = 13
FS_TICK = 12
FS_LEGEND = 13
FS_TABLE = 11
FS_ASIC = 10


def _style_axis(ax):
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color('#999999')
    ax.tick_params(colors=INK, labelsize=FS_TICK)
    ax.grid(axis='y', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _channel_axis(ax, ymax):
    ax.set_xlim(-1, NCH)
    ax.set_xticks(range(0, NCH + 1, 32))
    for b in range(CHIP_CH, NCH, CHIP_CH):
        ax.axvline(b - 0.5, color='#BBBBBB', linewidth=0.8, linestyle=':', zorder=1)
    for chip in range(NCH // CHIP_CH):
        ax.text(chip * CHIP_CH + CHIP_CH / 2 - 0.5, ymax * 0.985, 'A{}'.format(chip),
                ha='center', va='top', fontsize=FS_ASIC, color=INK_MUTED)


def _panel(ax, title, series, ymax, row_first):
    """series: list of (rms list, color, marks)."""
    _style_axis(ax)
    plotted = False
    for rms, color, marks in series:
        if rms is None:
            continue
        rms = np.asarray(rms, dtype=float)
        ax.plot(range(NCH), rms, color=color, linewidth=1.6, alpha=0.95)
        for key, style in (('fail', FAIL_STYLE), ('warn', WARN_STYLE)):
            chs = [c for c in (marks or {}).get(key, []) if 0 <= c < NCH]
            if chs:
                ax.scatter(chs, rms[chs], **style)
        plotted = True
    ax.set_ylim(0, ymax)
    _channel_axis(ax, ymax)
    ax.set_title(title, fontsize=FS_TITLE, color=INK, loc='left', fontweight='bold')
    ax.set_xlabel('Channel', fontsize=FS_LABEL, color=INK)
    if row_first:
        ax.set_ylabel('RMS noise [ADC]', fontsize=FS_LABEL, color=INK)
    if not plotted:
        ax.text(0.5, 0.5, 'no data', transform=ax.transAxes, ha='center', va='center',
                fontsize=FS_LABEL, color=INK_MUTED)


def _stat(rms, compact=False):
    if rms is None:
        return '-'
    rms = np.asarray(rms, dtype=float)
    if compact:
        return '{:.1f}'.format(np.mean(rms))
    return '{:.1f} ± {:.1f}'.format(np.mean(rms), np.std(rms))


def _stats_table(ax, rms_dict, bl, has_selc):
    """Mean ± std of every configuration: rows = configuration, columns = gain."""
    ax.axis('off')
    # with SELC the table has a single panel slot, so show the mean only
    compact = has_selc
    rows, cells = [], []
    for pt in PEAK_TIMES:
        rows.append('SE OFF {}'.format(PEAK_LABEL[pt]))
        cells.append([_stat(rms_dict.get('SE_{}mVBL_{}mVfC_{}us'.format(bl, g, pt)), compact) for g in GAINS])
    for mode, name in (('SEON', 'SE ON 2 us'), ('DIFF', 'DIFF 2 us')):
        rows.append(name)
        cells.append([_stat(rms_dict.get('{}_{}mVBL_{}mVfC_2_0us'.format(mode, bl, g)), compact) for g in GAINS])
    if has_selc:
        for l in LEAKAGES:
            rows.append('SELC {}'.format(LEAKAGE_LABEL[l]))
            cells.append(['' if g != '14_0' else
                          _stat(rms_dict.get('SELC_{}mVBL_14_0mVfC_2_0us_{}'.format(bl, l)), compact) for g in GAINS])
    cols = [GAIN_LABEL[g].replace(' mV/fC', '') for g in GAINS]
    tb = ax.table(cellText=cells, rowLabels=rows, colLabels=cols, loc='upper center',
                  cellLoc='center', rowLoc='left',
                  bbox=(0.30, 0.0, 0.70, 0.93) if compact else (0.24, 0.0, 0.76, 0.93))
    tb.auto_set_font_size(False)
    tb.set_fontsize(FS_TABLE)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor('#DDDDDD')
        if r == 0 and c >= 0:
            # column header: gain color as a swatch bar, text stays in ink
            cell.set_facecolor(GAIN_COLOR[GAINS[c]])
            cell.get_text().set_color('white' if GAINS[c] != '14_0' else INK)
            cell.get_text().set_fontweight('bold')
        elif c == -1:
            cell.set_facecolor('#F7F7F7')
    ax.set_title('Mean RMS [ADC]' if compact else 'Mean RMS ± std [ADC], gain in mV/fC',
                 fontsize=FS_TITLE, color=INK, loc='left', fontweight='bold')


def _legend_line(fig, has_selc):
    """One-line color key under the figure title."""
    handles = [Line2D([0], [0], color=GAIN_COLOR[g], lw=4, label=GAIN_LABEL[g]) for g in GAINS]
    if has_selc:
        handles += [Line2D([0], [0], color=LEAKAGE_COLOR[l], lw=4, label='SELC ' + LEAKAGE_LABEL[l])
                    for l in LEAKAGES]
    handles += [Line2D([0], [0], linestyle='none', marker='x', color=FAIL_STYLE['color'], markersize=10,
                       markeredgewidth=2.5, label='Fail'),
                Line2D([0], [0], linestyle='none', marker='^', markerfacecolor='none',
                       markeredgecolor=WARN_STYLE['edgecolors'], markersize=10, markeredgewidth=2,
                       label='Warning')]
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.005, 0.945), ncol=len(handles),
               fontsize=FS_LEGEND, frameon=False, handlelength=1.5, columnspacing=1.3, handletextpad=0.5)


def plot_all_configuration(rms_dict, bl, fp_png, title, marks=None):
    """
    One summary figure of channel RMS for every configuration at one baseline.

    rms_dict : {fname: [128 rms]} (log.report_log053_rms[ifemb])
    bl       : '200' or '900'
    marks    : {fname: {'fail': [ch], 'warn': [ch]}}  (optional)
    Layout   : row 1 = SE OFF at 0.5 / 1 / 2 / 3 us (one line per gain)
               row 2 = SE ON 2 us, DIFF 2 us, [SELC 14 mV/fC 2 us], mean ± std table
    """
    marks = marks or {}
    has_selc = any(k.startswith('SELC_{}mVBL'.format(bl)) for k in rms_dict)

    all_vals = np.concatenate([np.asarray(v, dtype=float) for k, v in rms_dict.items()
                               if '_{}mVBL_'.format(bl) in k] or [np.array([1.0])])
    ymax = float(np.nanmax(all_vals)) * 1.15

    fig = plt.figure(figsize=(17, 8.6))
    fig.patch.set_facecolor('white')
    gs = fig.add_gridspec(2, 4)
    ax0 = fig.add_subplot(gs[0, 0])
    axes_top = [ax0] + [fig.add_subplot(gs[0, i], sharey=ax0) for i in range(1, 4)]
    axes_bot = [fig.add_subplot(gs[1, i], sharey=ax0) for i in range(3 if has_selc else 2)]
    for ax in axes_top[1:] + axes_bot[1:]:
        plt.setp(ax.get_yticklabels(), visible=False)

    for i, pt in enumerate(PEAK_TIMES):
        series = [(rms_dict.get('SE_{}mVBL_{}mVfC_{}us'.format(bl, g, pt)), GAIN_COLOR[g],
                   marks.get('SE_{}mVBL_{}mVfC_{}us'.format(bl, g, pt))) for g in GAINS]
        _panel(axes_top[i], 'SE OFF  |  {}'.format(PEAK_LABEL[pt]), series, ymax, i == 0)

    for i, (mode, ttl) in enumerate((('SEON', 'SE ON  |  2 us'), ('DIFF', 'DIFF  |  2 us'))):
        series = [(rms_dict.get('{}_{}mVBL_{}mVfC_2_0us'.format(mode, bl, g)), GAIN_COLOR[g],
                   marks.get('{}_{}mVBL_{}mVfC_2_0us'.format(mode, bl, g))) for g in GAINS]
        _panel(axes_bot[i], ttl, series, ymax, i == 0)

    if has_selc:
        series = [(rms_dict.get('SELC_{}mVBL_14_0mVfC_2_0us_{}'.format(bl, l)), LEAKAGE_COLOR[l],
                   marks.get('SELC_{}mVBL_14_0mVfC_2_0us_{}'.format(bl, l))) for l in LEAKAGES]
        _panel(axes_bot[2], 'SE leakage  |  14 mV/fC, 2 us', series, ymax, False)
        table_ax = fig.add_subplot(gs[1, 3])
    else:
        table_ax = fig.add_subplot(gs[1, 2:4])
    _stats_table(table_ax, rms_dict, bl, has_selc)

    fig.suptitle(title, fontsize=FS_SUPTITLE, color=INK, fontweight='bold', x=0.008, y=0.995, ha='left')
    _legend_line(fig, has_selc)
    fig.tight_layout(rect=(0, 0, 1, 0.925), h_pad=2.0, w_pad=1.0)
    fig.savefig(fp_png, dpi=150, facecolor='white')
    plt.close(fig)
