import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==============================================================================
# Karakteristik PV Overlay – 4 Run pada 1 Grafik
# Style: Black & White, gaya jurnal akademik
# Menghasilkan 2 plot:
#   1. P-V Overlay  (karakteristik_pv_overlay.png / .pdf)
#   2. I-V Overlay  (karakteristik_iv_overlay.png / .pdf)
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Style per run: hitam-putih dengan linestyle & marker berbeda (gaya jurnal)
RUN_STYLES = {
    1: {'linestyle': '-',   'marker': None,  'label': 'Run 1', 'markevery': 8},
    2: {'linestyle': '--',  'marker': None,  'label': 'Run 2', 'markevery': 8},
    3: {'linestyle': '-.',  'marker': None,  'label': 'Run 3', 'markevery': 8},
    4: {'linestyle': ':',   'marker': 'o',   'label': 'Run 4', 'markevery': 8},
}

KOLOM = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty', 'Run_Num']


def load_and_clean(run_num):
    """Baca file gmpp_<run_num>.txt, filter Mode==5, anti-glitch, envelope."""
    filepath = os.path.join(BASE_DIR, f'gmpp_{run_num}.txt')
    if not os.path.isfile(filepath):
        print(f"[SKIP] File tidak ditemukan: {filepath}")
        return None

    df = pd.read_csv(filepath, sep=r'\s+', header=None, names=KOLOM, on_bad_lines='skip')
    df = df.apply(pd.to_numeric, errors='coerce').dropna()

    if df.empty:
        return None

    # Ambil hanya data Phase GMPP (Mode == 5)
    df_gmpp = df[df['Mode'] == 5]
    if df_gmpp.empty:
        df_gmpp = df

    df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)

    # --- Filter Anti-Glitch (sama dengan script asli) ---
    # 1. Rolling median spike removal
    df_gmpp = df_gmpp.copy()
    df_gmpp['Pin_median'] = df_gmpp['Pin'].rolling(window=15, center=True, min_periods=1).median()
    df_gmpp = df_gmpp[abs(df_gmpp['Pin'] - df_gmpp['Pin_median']) <= 6.0]

    # 2. Envelope: ambil Pin max per Vin bin (0.1 V)
    df_gmpp['Vin_bin'] = df_gmpp['Vin'].round(1)
    idx_max = df_gmpp.groupby('Vin_bin')['Pin'].idxmax().dropna()
    df_gmpp = df_gmpp.loc[idx_max].sort_values(by='Vin').reset_index(drop=True)

    return df_gmpp


def setup_rc():
    """Atur rcParams gaya jurnal hitam-putih (Times New Roman, tick in, tanpa grid)."""
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


# ==============================================================================
# Muat semua data
# ==============================================================================
all_data = {}
for r in range(1, 5):
    d = load_and_clean(r)
    if d is not None:
        all_data[r] = d
        print(f"Run {r}: {len(d)} titik data dimuat.")

if not all_data:
    raise SystemExit("[ERROR] Tidak ada data yang berhasil dimuat.")

setup_rc()

# ==============================================================================
# Plot 1 : P-V Overlay
# ==============================================================================
fig_pv, ax_pv = plt.subplots(figsize=(7, 5.5))

max_vin_all = 0
max_pin_all = 0

for run_num, df in sorted(all_data.items()):
    style = RUN_STYLES[run_num]

    # Cari GMPP untuk run ini
    idx_mpp = df['Pin'].idxmax()
    v_mpp = df.loc[idx_mpp, 'Vin']
    p_mpp = df.loc[idx_mpp, 'Pin']

    # Plot kurva
    ax_pv.plot(df['Vin'], df['Pin'],
               color='black',
               linestyle=style['linestyle'],
               linewidth=1.5,
               marker=style['marker'],
               markersize=5,
               markevery=style['markevery'],
               markerfacecolor='black',
               markeredgecolor='black',
               label=f"{style['label']} ($P_{{GMPP}}$ = {p_mpp:.2f} W)")

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

out_pv_png = os.path.join(BASE_DIR, 'karakteristik_pv_overlay.png')
out_pv_pdf = os.path.join(BASE_DIR, 'karakteristik_pv_overlay.pdf')
fig_pv.savefig(out_pv_png, dpi=600, bbox_inches='tight')
fig_pv.savefig(out_pv_pdf, bbox_inches='tight')
plt.close(fig_pv)
print(f"\n[OK] P-V Overlay disimpan: {os.path.basename(out_pv_png)}, {os.path.basename(out_pv_pdf)}")

# ==============================================================================
# Plot 2 : I-V Overlay
# ==============================================================================
fig_iv, ax_iv = plt.subplots(figsize=(7, 5.5))

max_iin_all = 0

for run_num, df in sorted(all_data.items()):
    style = RUN_STYLES[run_num]

    # Cari GMPP untuk run ini
    idx_mpp = df['Pin'].idxmax()
    v_mpp = df.loc[idx_mpp, 'Vin']
    i_mpp = df.loc[idx_mpp, 'Iin']
    p_mpp = df.loc[idx_mpp, 'Pin']

    # Plot kurva
    ax_iv.plot(df['Vin'], df['Iin'],
               color='black',
               linestyle=style['linestyle'],
               linewidth=1.5,
               marker=style['marker'],
               markersize=5,
               markevery=style['markevery'],
               markerfacecolor='black',
               markeredgecolor='black',
               label=f"{style['label']} ($I_{{GMPP}}$ = {i_mpp:.2f} A)")

    max_iin_all = max(max_iin_all, df['Iin'].max())

ax_iv.set_xlabel('Voltage (V)')
ax_iv.set_ylabel('Current (A)')
ax_iv.set_xlim(0, max_vin_all + 2)
ax_iv.set_ylim(0, max_iin_all * 1.15)
ax_iv.set_aspect('auto')
ax_iv.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
ax_iv.legend(loc='lower left', fontsize=11)
fig_iv.tight_layout()

out_iv_png = os.path.join(BASE_DIR, 'karakteristik_iv_overlay.png')
out_iv_pdf = os.path.join(BASE_DIR, 'karakteristik_iv_overlay.pdf')
fig_iv.savefig(out_iv_png, dpi=600, bbox_inches='tight')
fig_iv.savefig(out_iv_pdf, bbox_inches='tight')
plt.close(fig_iv)
print(f"[OK] I-V Overlay disimpan: {os.path.basename(out_iv_png)}, {os.path.basename(out_iv_pdf)}")

print("\nSelesai! Kedua grafik overlay telah dibuat.")
