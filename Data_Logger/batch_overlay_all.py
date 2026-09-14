"""
Karakteristik PV Overlay - Batch Processing untuk SEMUA folder Data_Logger
Menghasilkan P-V dan I-V overlay plot per folder.
Style: Black & White, gaya jurnal akademik, figsize 7x5.5, grid
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==============================================================================
# Konfigurasi folder dan file GMPP
# ==============================================================================
BASE = os.path.dirname(os.path.abspath(__file__))

# Daftar folder beserta file gmpp dan jumlah kolomnya
FOLDERS = {
    'uji 2': {
        'files': ['gmpp.txt', 'gmpp1.txt', 'gmpp2.txt', 'gmpp3.txt'],
        'ncols': 10,
        'filter': 'duty_spike',
    },
    'uji jam 2': {
        'files': ['gmpp.txt', 'gmpp1.txt', 'gmpp2.txt', 'gmpp3.txt'],
        'ncols': 10,
        'filter': 'duty_spike',
    },
    'uji motor 2 part 2': {
        'files': ['gmpp.txt', 'gmpp1.txt', 'gmpp2.txt', 'gmpp3.txt', 'gmpp4.txt', 'gmpp5.txt'],
        'ncols': 10,
        'filter': 'duty_spike',
    },
    'uji resistor': {
        'files': ['gmpp.txt', 'gmpp1.txt', 'gmpp2.txt', 'gmpp3.txt', 'gmpp4.txt'],
        'ncols': 10,
        'filter': 'median_envelope',
    },
    'ujimotor': {
        'files': ['gmpp.txt', 'gmpp1.txt', 'gmpp2.txt', 'gmpp3.txt'],
        'ncols': 10,
        'filter': 'median_envelope',
    },
}

KOLOM_10 = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']

# Style per run (hingga 6 run)
RUN_STYLES = [
    {'linestyle': '-',   'marker': None,  'markevery': 8},
    {'linestyle': '--',  'marker': None,  'markevery': 8},
    {'linestyle': '-.',  'marker': None,  'markevery': 8},
    {'linestyle': ':',   'marker': 'o',   'markevery': 8},
    {'linestyle': '-',   'marker': 's',   'markevery': 8},
    {'linestyle': '--',  'marker': '^',   'markevery': 8},
]


def load_and_clean(filepath, ncols, filter_type):
    """Baca file gmpp, filter Mode==5, anti-glitch, return DataFrame bersih."""
    if not os.path.isfile(filepath):
        return None

    kolom = KOLOM_10 if ncols == 10 else KOLOM_10 + ['Run_Num']
    df = pd.read_csv(filepath, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
    df = df.apply(pd.to_numeric, errors='coerce').dropna()

    if df.empty:
        return None

    df_gmpp = df[df['Mode'] == 5]
    if df_gmpp.empty:
        df_gmpp = df

    df_gmpp = df_gmpp.reset_index(drop=True)

    if filter_type == 'duty_spike':
        # 1. Truncate at Duty reset
        duty_diff = df_gmpp['Duty'].diff()
        reset_idx = duty_diff[duty_diff < -10].index
        if len(reset_idx) > 0:
            df_gmpp = df_gmpp.iloc[:reset_idx[0]]

        # 2. Patch glitch spikes
        for col in ['Vin', 'Iin', 'Pin']:
            rolling = df_gmpp[col].rolling(window=21, center=True, min_periods=1).median()
            threshold = 5.0 if col != 'Iin' else 0.5
            spike_mask = np.abs(df_gmpp[col] - rolling) > threshold
            df_gmpp.loc[spike_mask, col] = rolling[spike_mask]

    elif filter_type == 'median_envelope':
        # 1. Rolling median spike removal
        df_gmpp = df_gmpp.copy()
        df_gmpp['Pin_median'] = df_gmpp['Pin'].rolling(window=15, center=True, min_periods=1).median()
        df_gmpp = df_gmpp[abs(df_gmpp['Pin'] - df_gmpp['Pin_median']) <= 6.0]

        # 2. Envelope: ambil Pin max per Vin bin (0.1 V)
        df_gmpp['Vin_bin'] = df_gmpp['Vin'].round(1)
        idx_max = df_gmpp.groupby('Vin_bin')['Pin'].idxmax().dropna()
        df_gmpp = df_gmpp.loc[idx_max]

    df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)
    return df_gmpp


def setup_rc():
    """Atur rcParams gaya jurnal hitam-putih."""
    plt.rcdefaults()
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.labelweight': 'normal',
        'axes.linewidth': 1.0,
        'axes.edgecolor': 'black',
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.top': True,
        'ytick.right': True,
        'xtick.major.size': 5,
        'ytick.major.size': 5,
        'xtick.minor.size': 3,
        'ytick.minor.size': 3,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 11,
        'legend.framealpha': 1.0,
        'legend.edgecolor': 'black',
        'legend.fancybox': False,
    })


def process_folder(folder_name, config):
    """Proses satu folder: buat P-V dan I-V overlay."""
    folder_path = os.path.join(BASE, folder_name)
    print(f"\n{'='*60}")
    print(f"  Folder: {folder_name}")
    print(f"{'='*60}")

    # Load semua data
    all_data = {}
    for i, fname in enumerate(config['files']):
        fpath = os.path.join(folder_path, fname)
        d = load_and_clean(fpath, config['ncols'], config['filter'])
        if d is not None:
            run_label = i + 1
            all_data[run_label] = d
            print(f"  Run {run_label} ({fname}): {len(d)} titik data dimuat.")
        else:
            print(f"  [SKIP] {fname} tidak ada / kosong.")

    if not all_data:
        print(f"  [ERROR] Tidak ada data di folder {folder_name}!")
        return

    setup_rc()

    # ------------------------------------------------------------------
    # Plot P-V Overlay
    # ------------------------------------------------------------------
    fig_pv, ax_pv = plt.subplots(figsize=(7, 5.5))
    max_vin_all = 0
    max_pin_all = 0

    for run_num, df in sorted(all_data.items()):
        style = RUN_STYLES[(run_num - 1) % len(RUN_STYLES)]

        idx_mpp = df['Pin'].idxmax()
        p_mpp = df.loc[idx_mpp, 'Pin']

        ax_pv.plot(df['Vin'], df['Pin'],
                   color='black',
                   linestyle=style['linestyle'],
                   linewidth=1.5,
                   marker=style['marker'],
                   markersize=5,
                   markevery=style['markevery'],
                   markerfacecolor='black',
                   markeredgecolor='black',
                   label=f"Run {run_num} ($P_{{GMPP}}$ = {p_mpp:.2f} W)")

        max_vin_all = max(max_vin_all, df['Vin'].max())
        max_pin_all = max(max_pin_all, df['Pin'].max())

    ax_pv.set_xlabel('Voltage (V)')
    ax_pv.set_ylabel('Power (W)')
    ax_pv.set_xlim(0, max_vin_all + 2)
    ax_pv.set_ylim(0, max_pin_all * 1.15)
    ax_pv.set_aspect('auto')
    ax_pv.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    ax_pv.legend(loc='upper left', fontsize=11)
    fig_pv.tight_layout()

    out_pv_png = os.path.join(folder_path, 'karakteristik_pv_overlay.png')
    out_pv_pdf = os.path.join(folder_path, 'karakteristik_pv_overlay.pdf')
    fig_pv.savefig(out_pv_png, dpi=600, bbox_inches='tight')
    fig_pv.savefig(out_pv_pdf, bbox_inches='tight')
    plt.close(fig_pv)
    print(f"  [OK] P-V: {os.path.basename(out_pv_png)}, {os.path.basename(out_pv_pdf)}")

    # ------------------------------------------------------------------
    # Plot I-V Overlay
    # ------------------------------------------------------------------
    fig_iv, ax_iv = plt.subplots(figsize=(7, 5.5))
    max_iin_all = 0

    for run_num, df in sorted(all_data.items()):
        style = RUN_STYLES[(run_num - 1) % len(RUN_STYLES)]

        idx_mpp = df['Pin'].idxmax()
        i_mpp = df.loc[idx_mpp, 'Iin']

        ax_iv.plot(df['Vin'], df['Iin'],
                   color='black',
                   linestyle=style['linestyle'],
                   linewidth=1.5,
                   marker=style['marker'],
                   markersize=5,
                   markevery=style['markevery'],
                   markerfacecolor='black',
                   markeredgecolor='black',
                   label=f"Run {run_num} ($I_{{GMPP}}$ = {i_mpp:.2f} A)")

        max_iin_all = max(max_iin_all, df['Iin'].max())

    ax_iv.set_xlabel('Voltage (V)')
    ax_iv.set_ylabel('Current (A)')
    ax_iv.set_xlim(0, max_vin_all + 2)
    ax_iv.set_ylim(0, max_iin_all * 1.15)
    ax_iv.set_aspect('auto')
    ax_iv.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    ax_iv.legend(loc='lower left', fontsize=11)
    fig_iv.tight_layout()

    out_iv_png = os.path.join(folder_path, 'karakteristik_iv_overlay.png')
    out_iv_pdf = os.path.join(folder_path, 'karakteristik_iv_overlay.pdf')
    fig_iv.savefig(out_iv_png, dpi=600, bbox_inches='tight')
    fig_iv.savefig(out_iv_pdf, bbox_inches='tight')
    plt.close(fig_iv)
    print(f"  [OK] I-V: {os.path.basename(out_iv_png)}, {os.path.basename(out_iv_pdf)}")


# ==============================================================================
# Main: proses semua folder
# ==============================================================================
if __name__ == '__main__':
    for folder_name, config in FOLDERS.items():
        process_folder(folder_name, config)

    print(f"\n{'='*60}")
    print("  SELESAI! Semua overlay telah dibuat.")
    print(f"{'='*60}")
