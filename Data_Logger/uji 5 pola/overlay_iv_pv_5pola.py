"""
Overlay I-V and P-V Characteristic Curves for 5 Irradiance Patterns
====================================================================
Sources (same as the 100s tracking experiment):
  - Pola 1: uji motor 2 part 2 / gmpp1.txt  (estimasi 880 W/m², GMPP = 122.30 W)
  - Pola 2: uji motor 20m / gmpp_2.txt       (PSC, estimasi 660 W/m², GMPP = 92.18 W)
  - Pola 3: uji motor 2 part 2 / gmpp4.txt  (estimasi 910 W/m², GMPP = 126.13 W)
  - Pola 4: ujimotor / gmpp3.txt             (PSC, estimasi 460 W/m², GMPP = 64.28 W)
  - Pola 5: ujimotor / gmpp.txt              (estimasi 1000 W/m² STC, GMPP = 138.49 W)

Outputs (saved to uji 5 pola/):
  - overlay_pv_5pola.png/pdf   — P-V overlay
  - overlay_iv_5pola.png/pdf   — I-V overlay
  - overlay_iv_pv_5pola.png/pdf — Combined 2-panel (I-V top, P-V bottom)
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# === CONFIGURATION ===
out_dir = r"c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji 5 pola"

sources = [
    {
        'pola': 1,
        'label': 'Pola 1 — GMPP = 122.30 W',
        'file': r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji motor 2 part 2\gmpp1.txt',
        'ncols': 10,
        'irradiance': '880 W/m² (estimasi)',
        'target_gmpp': 122.30,
        'color': '#1565C0',   # Blue
        'linestyle': '-',
    },
    {
        'pola': 2,
        'label': 'Pola 2 — GMPP = 92.18 W',
        'file': r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji motor 20m\gmpp_2.txt',
        'ncols': 11,
        'irradiance': '660 W/m² (estimasi, PSC)',
        'target_gmpp': 92.18,
        'color': '#E65100',   # Deep Orange
        'linestyle': '--',
    },
    {
        'pola': 3,
        'label': 'Pola 3 — GMPP = 126.13 W',
        'file': r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji motor 2 part 2\gmpp4.txt',
        'ncols': 10,
        'irradiance': '910 W/m² (estimasi)',
        'target_gmpp': 126.13,
        'color': '#2E7D32',   # Green
        'linestyle': '-.',
    },
    {
        'pola': 4,
        'label': 'Pola 4 — GMPP = 64.28 W',
        'file': r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\ujimotor\gmpp3.txt',
        'ncols': 10,
        'irradiance': '460 W/m² (estimasi, PSC)',
        'target_gmpp': 64.28,
        'color': '#AD1457',   # Magenta/Pink
        'linestyle': ':',
    },
    {
        'pola': 5,
        'label': 'Pola 5 — GMPP = 138.49 W',
        'file': r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\ujimotor\gmpp.txt',
        'ncols': 10,
        'irradiance': '1000 W/m² (estimasi, STC)',
        'target_gmpp': 138.49,
        'color': '#6A1B9A',   # Purple
        'linestyle': (0, (3, 1, 1, 1)),  # densely dashdotted
    },
]

kolom10 = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']

# === LOAD & CLEAN DATA ===
data = []
for src in sources:
    fp = src['file']
    df = pd.read_csv(fp, sep=r'\s+', header=None, usecols=range(10), names=kolom10, on_bad_lines='skip')
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    
    df5 = df[df['Mode'] == 5]
    if df5.empty:
        df5 = df
    df5 = df5.reset_index(drop=True)
    
    # Truncate at duty reset (end of sweep)
    duty_diff = df5['Duty'].diff()
    reset_idx = duty_diff[duty_diff < -10].index
    if len(reset_idx) > 0:
        df5 = df5.iloc[:reset_idx[0]]
    
    # Gunakan data mentah dari file TXT tanpa mengubah bentuk kurva.
    df5 = df5.sort_values(by='Vin').reset_index(drop=True)

    # Deteksi GMPP dari nilai Pin asli database.
    idx_mpp = df5['Pin'].idxmax()
    v_mpp = df5.loc[idx_mpp, 'Vin']
    p_mpp = df5.loc[idx_mpp, 'Pin']
    i_mpp = df5.loc[idx_mpp, 'Iin']

    src['df'] = df5
    src['v_mpp'] = v_mpp
    src['p_mpp'] = p_mpp
    src['i_mpp'] = i_mpp

    print(f"Pola {src['pola']}: {len(df5)} pts, GMPP = {p_mpp:.2f} W at {v_mpp:.2f} V, {i_mpp:.2f} A")


# === MATPLOTLIB STYLE ===
plt.rcdefaults()
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 11,
    'axes.labelsize': 13,
    'axes.labelweight': 'bold',
    'axes.linewidth': 1.0,
    'axes.edgecolor': 'black',
    'axes.facecolor': 'white',
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.top': True,
    'ytick.right': True,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'xtick.major.size': 5,
    'ytick.major.size': 5,
    'xtick.minor.size': 3,
    'ytick.minor.size': 3,
    'xtick.minor.visible': True,
    'ytick.minor.visible': True,
    'legend.fontsize': 10,
    'legend.framealpha': 1.0,
    'legend.edgecolor': '#444444',
})

# ================================================================
# PLOT 1: P-V OVERLAY
# ================================================================
fig1, ax1 = plt.subplots(figsize=(9, 6))

for src in sources:
    df5 = src['df']
    ax1.plot(df5['Vin'], df5['Pin'],
             color=src['color'], linestyle=src['linestyle'], linewidth=2.0,
             label=src['label'], zorder=3)
    # Mark GMPP point
    ax1.scatter(src['v_mpp'], src['p_mpp'], color=src['color'],
                s=70, zorder=5, edgecolors='black', linewidths=0.6)
    ax1.annotate(f"  {src['p_mpp']:.1f} W",
                 xy=(src['v_mpp'], src['p_mpp']),
                 fontsize=9, fontweight='bold', color=src['color'],
                 ha='left', va='bottom')

ax1.set_xlabel(r'PV Voltage, $V_{\mathrm{PV}}$ (V)')
ax1.set_ylabel(r'PV Power, $P_{\mathrm{PV}}$ (W)')
ax1.set_xlim(0, 42)
ax1.set_ylim(0, 160)
ax1.xaxis.set_major_locator(ticker.MultipleLocator(5))
ax1.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax1.yaxis.set_major_locator(ticker.MultipleLocator(20))
ax1.yaxis.set_minor_locator(ticker.MultipleLocator(5))
ax1.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
ax1.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#444444',
           handlelength=2.5, borderpad=0.5)

fig1.tight_layout()
fig1.savefig(os.path.join(out_dir, 'overlay_pv_5pola.png'), dpi=600, bbox_inches='tight')
fig1.savefig(os.path.join(out_dir, 'overlay_pv_5pola.pdf'), format='pdf', bbox_inches='tight')
plt.close(fig1)
print("[SAVED] overlay_pv_5pola.png & PDF")

# ================================================================
# PLOT 2: I-V OVERLAY
# ================================================================
fig2, ax2 = plt.subplots(figsize=(9, 6))

for src in sources:
    df5 = src['df']
    ax2.plot(df5['Vin'], df5['Iin'],
             color=src['color'], linestyle=src['linestyle'], linewidth=2.0,
             label=src['label'], zorder=3)
    # Mark MPP point on I-V
    ax2.scatter(src['v_mpp'], src['i_mpp'], color=src['color'],
                s=70, zorder=5, edgecolors='black', linewidths=0.6)
    ax2.annotate(f"  {src['i_mpp']:.2f} A",
                 xy=(src['v_mpp'], src['i_mpp']),
                 fontsize=9, fontweight='bold', color=src['color'],
                 ha='left', va='bottom')

ax2.set_xlabel(r'PV Voltage, $V_{\mathrm{PV}}$ (V)')
ax2.set_ylabel(r'PV Current, $I_{\mathrm{PV}}$ (A)')
ax2.set_xlim(0, 42)
ax2.set_ylim(0, 6)
ax2.xaxis.set_major_locator(ticker.MultipleLocator(5))
ax2.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax2.yaxis.set_major_locator(ticker.MultipleLocator(1))
ax2.yaxis.set_minor_locator(ticker.MultipleLocator(0.2))
ax2.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
ax2.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='#444444',
           handlelength=2.5, borderpad=0.5)

fig2.tight_layout()
fig2.savefig(os.path.join(out_dir, 'overlay_iv_5pola.png'), dpi=600, bbox_inches='tight')
fig2.savefig(os.path.join(out_dir, 'overlay_iv_5pola.pdf'), format='pdf', bbox_inches='tight')
plt.close(fig2)
print("[SAVED] overlay_iv_5pola.png & PDF")

# ================================================================
# PLOT 3: COMBINED 2-PANEL (I-V top, P-V bottom)
# ================================================================
fig3, (ax_iv, ax_pv) = plt.subplots(2, 1, figsize=(10, 9), sharex=True)

for src in sources:
    df5 = src['df']
    # I-V (top)
    ax_iv.plot(df5['Vin'], df5['Iin'],
               color=src['color'], linestyle=src['linestyle'], linewidth=1.8,
               label=src['label'], zorder=3)
    ax_iv.scatter(src['v_mpp'], src['i_mpp'], color=src['color'],
                  s=55, zorder=5, edgecolors='black', linewidths=0.5)

    # P-V (bottom)
    ax_pv.plot(df5['Vin'], df5['Pin'],
               color=src['color'], linestyle=src['linestyle'], linewidth=1.8,
               label=src['label'], zorder=3)
    ax_pv.scatter(src['v_mpp'], src['p_mpp'], color=src['color'],
                  s=55, zorder=5, edgecolors='black', linewidths=0.5)
    ax_pv.annotate(f"  {src['p_mpp']:.1f} W",
                   xy=(src['v_mpp'], src['p_mpp']),
                   fontsize=8.5, fontweight='bold', color=src['color'],
                   ha='left', va='bottom')

# I-V panel
ax_iv.set_ylabel(r'PV Current, $I_{\mathrm{PV}}$ (A)', fontsize=12)
ax_iv.set_ylim(0, 6)
ax_iv.yaxis.set_major_locator(ticker.MultipleLocator(1))
ax_iv.yaxis.set_minor_locator(ticker.MultipleLocator(0.2))
ax_iv.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
ax_iv.legend(loc='upper right', ncol=2, frameon=True, facecolor='white',
             edgecolor='#444444', fontsize=9.5, handlelength=2.2, borderpad=0.4)
ax_iv.text(0.02, 0.95, '(a) I-V Characteristics', transform=ax_iv.transAxes,
           fontsize=12, fontweight='bold', va='top')

# P-V panel
ax_pv.set_xlabel(r'PV Voltage, $V_{\mathrm{PV}}$ (V)', fontsize=12)
ax_pv.set_ylabel(r'PV Power, $P_{\mathrm{PV}}$ (W)', fontsize=12)
ax_pv.set_xlim(0, 42)
ax_pv.set_ylim(0, 160)
ax_pv.xaxis.set_major_locator(ticker.MultipleLocator(5))
ax_pv.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax_pv.yaxis.set_major_locator(ticker.MultipleLocator(20))
ax_pv.yaxis.set_minor_locator(ticker.MultipleLocator(5))
ax_pv.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
ax_pv.legend(loc='upper left', ncol=2, frameon=True, facecolor='white',
             edgecolor='#444444', fontsize=9.5, handlelength=2.2, borderpad=0.4)
ax_pv.text(0.02, 0.95, '(b) P-V Characteristics', transform=ax_pv.transAxes,
           fontsize=12, fontweight='bold', va='top')

fig3.tight_layout()
fig3.savefig(os.path.join(out_dir, 'overlay_iv_pv_5pola.png'), dpi=600, bbox_inches='tight')
fig3.savefig(os.path.join(out_dir, 'overlay_iv_pv_5pola.pdf'), format='pdf', bbox_inches='tight')
plt.close(fig3)
print("[SAVED] overlay_iv_pv_5pola.png & PDF")

print("\n[DONE] All I-V and P-V overlay plots generated!")
