"""
generate_wode_only_plot.py
=========================
Create a separate WODE-only power and duty plot from the existing dataset.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

BASE = r"c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger"
OUT = os.path.join(BASE, "Data 6 metode")
os.makedirs(OUT, exist_ok=True)

KOLOM = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
MAX_DURATION = 25
THRESHOLD = 1.0


def setup_rcparams():
    plt.rcdefaults()
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'axes.labelweight': 'bold',
        'axes.linewidth': 0.8,
        'axes.edgecolor': '#333333',
        'axes.facecolor': 'white',
        'xtick.labelsize': 9.5,
        'ytick.labelsize': 9.5,
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.top': True,
        'ytick.right': True,
        'xtick.major.size': 4,
        'ytick.major.size': 4,
        'xtick.minor.size': 2,
        'ytick.minor.size': 2,
        'xtick.major.width': 0.8,
        'ytick.major.width': 0.8,
        'xtick.minor.width': 0.5,
        'ytick.minor.width': 0.5,
        'xtick.minor.visible': True,
        'ytick.minor.visible': True,
        'legend.fontsize': 8.0,
        'legend.framealpha': 1.0,
        'legend.edgecolor': '#555555',
        'legend.fancybox': False,
        'legend.handlelength': 2.0,
        'legend.handletextpad': 0.5,
        'legend.borderpad': 0.4,
        'legend.labelspacing': 0.35,
    })


def load_wode_data():
    wode_path = os.path.join(OUT, 'wode.txt')
    if not os.path.exists(wode_path):
        raise FileNotFoundError(f"WODE data not found: {wode_path}")

    df = pd.read_csv(wode_path, sep=r'\s+', header=None, names=KOLOM, on_bad_lines='skip')
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    if df.empty:
        raise ValueError('WODE data is empty after parsing.')

    mask = df['Pin'] > THRESHOLD
    if not mask.any():
        raise ValueError('WODE data has no valid power above threshold.')

    first = mask.idxmax()
    start_idx = max(0, first - 1)
    t0 = df.loc[start_idx, 'Waktu']
    df = df.loc[start_idx:].copy()
    df['Waktu'] = df['Waktu'] - t0
    df = df[df['Waktu'] <= MAX_DURATION]
    return df


def load_target_gmpp():
    gmpp_path = os.path.join(OUT, 'gmpp.txt')
    if not os.path.exists(gmpp_path):
        return 138.49

    try:
        dfg = pd.read_csv(gmpp_path, sep=r'\s+', header=None, names=KOLOM, on_bad_lines='skip')
        dfg = dfg.apply(pd.to_numeric, errors='coerce').dropna()
        dfg5 = dfg[dfg['Mode'] == 5]
        if dfg5.empty:
            dfg5 = dfg
        return float(dfg5['Pin'].max())
    except Exception:
        return 138.49


def plot_single_power(df, target_gmpp):
    fig, ax = plt.subplots(figsize=(7.5, 5.0), dpi=300)
    ax.axhline(y=target_gmpp, color='black', linewidth=1.5, dashes=(6, 3),
               label=f'Measured GMPP = {target_gmpp:.2f} W', zorder=2)

    ax.plot(df['Waktu'], df['Pin'], color='black', linewidth=1.6, zorder=3, label='WODE Power')

    axins = ax.inset_axes([0.68, 0.25, 0.28, 0.26])
    axins.axhline(y=target_gmpp, color='black', linewidth=1.0, dashes=(6, 3), zorder=2)
    mz = (df['Waktu'] >= 20) & (df['Waktu'] <= 25)
    x1, x2 = 20, 25
    if not df[mz].empty:
        y1 = df.loc[mz, 'Pin'].min() - 2
        y2 = df.loc[mz, 'Pin'].max() + 2
    else:
        y1, y2 = target_gmpp - 5, target_gmpp + 2
    axins.plot(df['Waktu'], df['Pin'], color='black', linewidth=1.3, zorder=3)
    axins.set_xlim(x1, x2)
    axins.set_ylim(y1, y2)
    axins.tick_params(axis='both', which='both', labelsize=7.5)
    axins.grid(True, linestyle=':', linewidth=0.5, alpha=0.7)
    ax.indicate_inset_zoom(axins, edgecolor='black')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('PV Power (W)')
    ax.set_xlim(-0.5, MAX_DURATION)
    ax.set_ylim(0, 155)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.6, color='#aaaaaa', zorder=0)

    legend = ax.legend(loc='lower right', frameon=True, facecolor='white',
                      edgecolor='#999999', borderaxespad=0.5, ncol=1, fontsize=8)
    if legend:
        legend.get_frame().set_linewidth(0.6)

    plt.tight_layout()
    out_file = os.path.join(OUT, 'wode_power_only.png')
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved WODE power plot: {out_file}')


def plot_single_duty(df):
    fig, ax = plt.subplots(figsize=(7.5, 5.0), dpi=300)
    ax.plot(df['Waktu'], df['Duty'], color='black', linewidth=1.6, zorder=3, label='WODE Duty')

    axins = ax.inset_axes([0.68, 0.25, 0.28, 0.26])
    mz = (df['Waktu'] >= 20) & (df['Waktu'] <= 25)
    x1, x2 = 20, 25
    if not df[mz].empty:
        y1 = df.loc[mz, 'Duty'].min() - 2
        y2 = df.loc[mz, 'Duty'].max() + 2
    else:
        y1, y2 = 20, 60
    axins.plot(df['Waktu'], df['Duty'], color='black', linewidth=1.3, zorder=3)
    axins.set_xlim(x1, x2)
    axins.set_ylim(y1, y2)
    axins.tick_params(axis='both', which='both', labelsize=7.5)
    axins.grid(True, linestyle=':', linewidth=0.5, alpha=0.7)
    ax.indicate_inset_zoom(axins, edgecolor='black')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Duty Cycle (%)')
    ax.set_xlim(-0.5, MAX_DURATION)
    max_duty = df['Duty'].max() if not df.empty else 100
    ax.set_ylim(0, min(105, max_duty * 1.15))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.6, color='#aaaaaa', zorder=0)

    legend = ax.legend(loc='upper right', frameon=True, facecolor='white',
                      edgecolor='#999999', borderaxespad=0.5, ncol=1, fontsize=8)
    if legend:
        legend.get_frame().set_linewidth(0.6)

    plt.tight_layout()
    out_file = os.path.join(OUT, 'wode_duty_only.png')
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved WODE duty plot: {out_file}')


def main():
    setup_rcparams()
    df = load_wode_data()
    target_gmpp = load_target_gmpp()
    plot_single_power(df, target_gmpp)
    plot_single_duty(df)
    print('\n=== DONE ===')
    print(f'Output dir: {OUT}')


if __name__ == '__main__':
    main()
