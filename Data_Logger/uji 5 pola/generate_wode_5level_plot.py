"""
generate_wode_5level_plot.py
===========================
Generate a separate WODE-only plot for the five-level irradiance experiment.
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)

folder_part2 = os.path.join(parent_dir, "uji motor 2 part 2")
folder_ujimotor = os.path.join(parent_dir, "ujimotor")
folder_20m = os.path.join(parent_dir, "uji motor 20m")

sources = [
    {
        'pola': 1,
        'folder': folder_part2,
        'file': 'wode1.txt',
        'target_gmpp': 122.30,
        'irradiance': '880 W/m²',
    },
    {
        'pola': 2,
        'folder': folder_20m,
        'file': 'wode_2.txt',
        'target_gmpp': 92.18,
        'irradiance': '660 W/m²',
    },
    {
        'pola': 3,
        'folder': folder_part2,
        'file': 'wode4.txt',
        'target_gmpp': 126.13,
        'irradiance': '910 W/m²',
    },
    {
        'pola': 4,
        'folder': folder_ujimotor,
        'file': 'wode3.txt',
        'target_gmpp': 64.28,
        'irradiance': '460 W/m² (PSC)',
    },
    {
        'pola': 5,
        'folder': folder_ujimotor,
        'file': 'wode.txt',
        'target_gmpp': 138.49,
        'irradiance': '1000 W/m² (STC)',
    },
]

kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
threshold_power = 1.0


def load_wode_segment(file_path):
    df = pd.read_csv(file_path, sep=r'\s+', header=None, usecols=range(10), names=kolom, on_bad_lines='skip')
    df = df.apply(pd.to_numeric, errors='coerce').dropna().reset_index(drop=True)
    if df.empty:
        return None

    mask = df['Pin'] > threshold_power
    if not mask.any():
        return None

    first_idx = mask.idxmax()
    start_idx = max(0, first_idx - 1)
    t0 = df.loc[start_idx, 'Waktu']
    df_sub = df.loc[start_idx:].copy().reset_index(drop=True)
    df_sub['t_rel'] = df_sub['Waktu'] - t0
    df_20s = df_sub[df_sub['t_rel'] <= 20.0].copy().reset_index(drop=True)
    return df_20s


def save_formatted_txt(df, out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            mode_val = int(row['Mode']) if not pd.isna(row['Mode']) else 1
            f.write(
                f"{row['Waktu']:.3f}\t"
                f"{row['Vin']:.2f}\t"
                f"{row['Iin']:.2f}\t"
                f"{row['Pin']:.2f}\t"
                f"{row['Vout']:.2f}\t"
                f"{row['Iout']:.2f}\t"
                f"{row['Pout']:.2f}\t"
                f"{row['Eff']:.2f}\t"
                f"{mode_val}\t"
                f"{row['Duty']:.2f}\n"
            )


def build_100s_data():
    combined = []
    gmpp_target = []
    for i, src in enumerate(sources):
        t_offset = i * 20.0
        file_path = os.path.join(src['folder'], src['file'])
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing data file: {file_path}")

        seg = load_wode_segment(file_path)
        if seg is None:
            raise ValueError(f"No valid WODE data in {file_path}")

        seg = seg.copy()
        seg['Waktu'] = t_offset + seg['t_rel'].values
        seg['Pola'] = src['pola']
        combined.append(seg[kolom + ['Pola']])

        step = np.linspace(0.0, 19.9, 195)
        gmpp_target.append(pd.DataFrame({
            'Waktu': t_offset + step,
            'Vin': np.nan,
            'Iin': np.nan,
            'Pin': np.full_like(step, src['target_gmpp']),
            'Vout': np.nan,
            'Iout': np.nan,
            'Pout': np.nan,
            'Eff': 100.0,
            'Mode': 5,
            'Duty': np.nan,
            'Pola': src['pola'],
        }))

    df_100s = pd.concat(combined, ignore_index=True)
    df_target = pd.concat(gmpp_target, ignore_index=True)
    return df_100s, df_target


def setup_rcparams():
    plt.rcdefaults()
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'axes.labelweight': 'bold',
        'axes.linewidth': 1.1,
        'axes.edgecolor': 'black',
        'axes.facecolor': 'white',
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.top': True,
        'ytick.right': True,
        'xtick.major.size': 5,
        'ytick.major.size': 5,
        'xtick.minor.size': 3,
        'ytick.minor.size': 3,
        'xtick.major.width': 1.0,
        'ytick.major.width': 1.0,
        'xtick.minor.width': 0.6,
        'ytick.minor.width': 0.6,
        'xtick.minor.visible': True,
        'ytick.minor.visible': True,
    })


def plot_wode_power(df_100s, df_target):
    fig, ax = plt.subplots(figsize=(13, 6.2))

    target_t = df_target['Waktu'].to_numpy()
    target_p = df_target['Pin'].to_numpy()
    ax.plot(target_t, target_p, color='red', linewidth=2.0, dashes=(6, 3), label='Target GMPP', zorder=2)
    ax.plot(df_100s['Waktu'], df_100s['Pin'], color='#0b3d91', linewidth=1.8, label='WODE Power', zorder=3)

    for i, src in enumerate(sources):
        x_center = i * 20.0 + 10.0
        ax.text(x_center, 150, f"{src['irradiance']}\nTarget = {src['target_gmpp']:.1f} W",
                ha='center', va='top', fontsize=9.0, fontweight='bold',
                bbox=dict(boxstyle='square,pad=0.25', facecolor='white', edgecolor='#666666', linewidth=0.7))

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('PV Power (W)', fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 168)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(2))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
    leg = ax.legend(loc='upper right', ncol=2, frameon=True, facecolor='white', edgecolor='black', fontsize=10)
    leg.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    out_png = os.path.join(base_dir, 'wode_5level_power.png')
    out_pdf = os.path.join(base_dir, 'wode_5level_power.pdf')
    fig.savefig(out_png, dpi=600, bbox_inches='tight')
    fig.savefig(out_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f'Saved WODE 5-level power plot: {out_png}')


def plot_wode_duty(df_100s):
    fig, ax = plt.subplots(figsize=(13, 6.2))
    ax.plot(df_100s['Waktu'], df_100s['Duty'], color='#0b3d91', linewidth=1.8, label='WODE Duty', zorder=3)

    for i, src in enumerate(sources):
        x_center = i * 20.0 + 10.0
        ax.text(x_center, 95, src['irradiance'],
                ha='center', va='top', fontsize=9.0, fontweight='bold',
                bbox=dict(boxstyle='square,pad=0.25', facecolor='white', edgecolor='#666666', linewidth=0.7))

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Duty Cycle (%)', fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(2))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
    leg = ax.legend(loc='upper right', ncol=1, frameon=True, facecolor='white', edgecolor='black', fontsize=10)
    leg.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    out_png = os.path.join(base_dir, 'wode_5level_duty.png')
    out_pdf = os.path.join(base_dir, 'wode_5level_duty.pdf')
    fig.savefig(out_png, dpi=600, bbox_inches='tight')
    fig.savefig(out_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f'Saved WODE 5-level duty plot: {out_png}')


def main():
    setup_rcparams()
    df_100s, df_target = build_100s_data()
    save_formatted_txt(df_100s[kolom], os.path.join(base_dir, 'wode_5level_100s.txt'))
    print(f'Saved WODE 5-level merged data: {os.path.join(base_dir, "wode_5level_100s.txt")}')
    plot_wode_power(df_100s, df_target)
    plot_wode_duty(df_100s)
    print('\n=== DONE ===')
    print(f'Output dir: {base_dir}')


if __name__ == '__main__':
    main()
