"""
generate_all_6metode.py
=======================
Master script: copies all 6-method raw data (WODE, PNO, WOA, DE, INC, INC-Fuzzy)
into the 'Data 6 metode' folder and generates publication-quality power & duty plots
with smaller zoom-in boxes positioned to not obstruct the graph.
"""
import os, shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ============================================================
# PATHS
# ============================================================
BASE   = r"c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger"
MOTOR  = os.path.join(BASE, "ujimotor")
SIM    = os.path.join(BASE, "simulasi")
OUT    = os.path.join(BASE, "Data 6 metode")
os.makedirs(OUT, exist_ok=True)

# ============================================================
# 1. COPY RAW TXT DATA (Run 0 only)
# ============================================================
raw_files = {
    "wode.txt": os.path.join(MOTOR, "wode.txt"),
    "pno.txt":  os.path.join(MOTOR, "pno.txt"),
    "woa.txt":  os.path.join(MOTOR, "woa.txt"),
    "de.txt":   os.path.join(MOTOR, "de.txt"),
    "inc.txt":  os.path.join(MOTOR, "inc.txt"),
    "fuzzy.txt": os.path.join(MOTOR, "fuzzy.txt"),
    "gmpp.txt": os.path.join(MOTOR, "gmpp.txt"),
}
for dst_name, src_path in raw_files.items():
    dst_path = os.path.join(OUT, dst_name)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
        print(f"Copied {dst_name}")
    else:
        print(f"[SKIP] {src_path} not found")

# ============================================================
# 2. COMMON STYLE
# ============================================================
ALGO_STYLES = {
    'WODE':      {'color': '#0b3d91', 'ls': '-',  'lw': 1.8, 'marker': None, 'ms': 0},
    'PNO':       {'color': '#d62728', 'ls': '-',  'lw': 1.7, 'marker': None, 'ms': 0},
    'WOA':       {'color': '#2ca02c', 'ls': '-',  'lw': 1.7, 'marker': None, 'ms': 0},
    'DE':        {'color': '#ff7f0e', 'ls': '-',  'lw': 1.8, 'marker': 'o', 'ms': 3},
    'INC':       {'color': '#8c564b', 'ls': '-',  'lw': 1.7, 'marker': 's', 'ms': 3},
    'INC-Fuzzy': {'color': '#7f7f7f', 'ls': '-',  'lw': 1.7, 'marker': '^', 'ms': 3},
}
ALGO_ORDER = ['WODE', 'PNO', 'WOA', 'DE', 'INC', 'INC-Fuzzy']

def compute_stats_table(data, target_gmpp):
    stats_data = []
    for algo in ALGO_ORDER:
        if algo not in data:
            continue
        df = data[algo]
        t_track_thr = 0.95 * target_gmpp
        reached = df[df['Pin'] >= t_track_thr]
        t_track = reached['Waktu'].iloc[0] if not reached.empty else np.nan

        # Requested metric window: 20 s to 25 s
        steady_mask = (df['Waktu'] >= 20) & (df['Waktu'] <= 25)
        dfs = df[steady_mask]

        if not dfs.empty:
            p_avg = dfs['Pin'].mean()
            eff = (p_avg / target_gmpp) * 100
            ripple = dfs['Pin'].max() - dfs['Pin'].min()
        else:
            p_avg, eff, ripple = np.nan, np.nan, np.nan

        stats_data.append([algo, f"{t_track:.2f}", f"{p_avg:.2f}", f"{eff:.2f}", f"{ripple:.2f}"])
    return stats_data

def write_performance_summary(stats_data, output_path):
    if not stats_data:
        return
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Algo\tt_track(s)\tPavg_20-25s(W)\tEff(%)\tRipple_20-25s(W)\n")
        for row in stats_data:
            f.write(f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\t{row[4]}\n")

def setup_rcparams():
    plt.rcdefaults()
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 11,
        'axes.labelsize': 16,
        'axes.titlesize': 14,
        'axes.labelweight': 'bold',
        'axes.linewidth': 1.1,
        'axes.edgecolor': 'black',
        'axes.facecolor': 'white',
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
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
        'legend.fontsize': 11,
        'legend.framealpha': 1.0,
        'legend.edgecolor': '#555555',
        'legend.fancybox': False,
        'legend.handlelength': 2.0,
        'legend.handletextpad': 0.5,
        'legend.borderpad': 0.4,
        'legend.labelspacing': 0.35,
    })

# ============================================================
# 3. LOAD DATA
# ============================================================
KOLOM = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
MAX_DURATION = 25   # seconds to display
THRESHOLD = 1.0

def load_algo(filename):
    fpath = os.path.join(OUT, filename)
    if not os.path.exists(fpath):
        return None
    df = pd.read_csv(fpath, sep=r'\s+', header=None, names=KOLOM, on_bad_lines='skip')
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    if df.empty:
        return None
    mask = df['Pin'] > THRESHOLD
    if not mask.any():
        return None
    first = mask.idxmax()
    start_idx = max(0, first - 1)
    t0 = df.loc[start_idx, 'Waktu']
    df = df.loc[start_idx:].copy()
    df['Waktu'] = df['Waktu'] - t0
    df = df[df['Waktu'] <= MAX_DURATION]
    return df

# Map algo name -> filename
FILE_MAP = {
    'WODE': 'wode.txt',
    'PNO':  'pno.txt',
    'WOA':  'woa.txt',
    'DE':   'de.txt',
    'INC':  'inc.txt',
    'INC-Fuzzy': 'fuzzy.txt',
}

# Load GMPP
gmpp_path = os.path.join(OUT, "gmpp.txt")
target_gmpp = 138.49  # default
if os.path.exists(gmpp_path):
    try:
        dfg = pd.read_csv(gmpp_path, sep=r'\s+', header=None, names=KOLOM, on_bad_lines='skip')
        dfg = dfg.apply(pd.to_numeric, errors='coerce').dropna()
        dfg5 = dfg[dfg['Mode'] == 5]
        if dfg5.empty:
            dfg5 = dfg
        target_gmpp = dfg5['Pin'].max()
    except:
        pass
print(f"Target GMPP = {target_gmpp:.2f} W")

# Load all algorithms
data = {}
for algo in ALGO_ORDER:
    df = load_algo(FILE_MAP[algo])
    if df is not None:
        data[algo] = df
        print(f"Loaded {algo}: {len(df)} points, max Pin={df['Pin'].max():.2f} W")
    else:
        print(f"[SKIP] {algo} data not available")

# ============================================================
# 4. POWER COMPARISON PLOT (6 methods, B&W, small zoom box)
# ============================================================
setup_rcparams()
fig, ax = plt.subplots(figsize=(13, 6.2), dpi=300)

# GMPP line
ax.axhline(y=target_gmpp, color='black', linewidth=1.8, dashes=(6, 3),
           label=f'Measured GMPP = {target_gmpp:.2f} W', zorder=2)

# inset style matching the five-level figure
axins = ax.inset_axes([0.62, 0.20, 0.32, 0.28])
axins.axhline(y=target_gmpp, color='black', linewidth=1.0, dashes=(6, 3), zorder=2)

stats_data = compute_stats_table(data, target_gmpp)
power_min_zoom, power_max_zoom = 1000, 0

for algo in ALGO_ORDER:
    if algo not in data:
        continue
    df = data[algo]
    s = ALGO_STYLES[algo]

    # Main plot
    ax.plot(df['Waktu'], df['Pin'], color=s['color'], linestyle=s['ls'],
            linewidth=s['lw'], marker=s['marker'], markevery=15,
            markersize=s['ms'], zorder=3, label=algo)
    # Inset
    axins.plot(df['Waktu'], df['Pin'], color=s['color'], linestyle=s['ls'],
               linewidth=s['lw'], marker=s['marker'], markevery=5,
               markersize=max(0, s['ms']-1), zorder=3)

    # Zoom bounds
    mz = (df['Waktu'] >= 20) & (df['Waktu'] <= 24)
    if df[mz].any().any():
        power_min_zoom = min(power_min_zoom, df.loc[mz, 'Pin'].min())
        power_max_zoom = max(power_max_zoom, df.loc[mz, 'Pin'].max())

# Configure inset
x1, x2 = 20, 24
if power_min_zoom < power_max_zoom:
    y1, y2 = power_min_zoom - 2, power_max_zoom + 2
else:
    y1, y2 = target_gmpp - 5, target_gmpp + 2
axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)
axins.tick_params(axis='both', which='both', labelsize=10)
axins.grid(True, linestyle='--', linewidth=0.6, alpha=0.7, color='#b5b5b5')
ax.indicate_inset_zoom(axins, edgecolor="black")

ax.set_xlabel('Time (s)', fontsize=18, fontweight='bold')
ax.set_ylabel('PV Power (W)', fontsize=18, fontweight='bold')
ax.set_xlim(0, 24)
ax.set_ylim(0, 155)
ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#b5b5b5', zorder=0)

leg = ax.legend(loc='lower right', frameon=True, facecolor='white',
                edgecolor='black', borderaxespad=0.5, ncol=2, fontsize=11)
if leg:
    leg.get_frame().set_linewidth(0.8)

plt.tight_layout()
pwr_png = os.path.join(OUT, "algo_comparison_power_run0.png")
pwr_pdf = os.path.join(OUT, "algo_comparison_power_run0.pdf")
plt.savefig(pwr_png, dpi=300, bbox_inches='tight')
plt.savefig(pwr_pdf, format='pdf', bbox_inches='tight')
plt.close()
print(f"\nSaved POWER plot: {pwr_png}")

# ============================================================
# 5. DUTY CYCLE COMPARISON PLOT (6 methods, B&W, small zoom box)
# ============================================================
setup_rcparams()
fig, ax = plt.subplots(figsize=(13, 6.2), dpi=300)

# inset style matching the five-level figure
axins = ax.inset_axes([0.62, 0.20, 0.32, 0.28])

duty_min_zoom, duty_max_zoom = 100, 0

for algo in ALGO_ORDER:
    if algo not in data:
        continue
    df = data[algo]
    s = ALGO_STYLES[algo]

    ax.plot(df['Waktu'], df['Duty'], color=s['color'], linestyle=s['ls'],
            linewidth=s['lw'], marker=s['marker'], markevery=15,
            markersize=s['ms'], zorder=3, label=algo)
    axins.plot(df['Waktu'], df['Duty'], color=s['color'], linestyle=s['ls'],
               linewidth=s['lw'], marker=s['marker'], markevery=5,
               markersize=max(0, s['ms']-1), zorder=3)

    mz = (df['Waktu'] >= 20) & (df['Waktu'] <= 24)
    if df[mz].any().any():
        duty_min_zoom = min(duty_min_zoom, df.loc[mz, 'Duty'].min())
        duty_max_zoom = max(duty_max_zoom, df.loc[mz, 'Duty'].max())

# Configure duty inset
x1, x2 = 20, 24
if duty_min_zoom < duty_max_zoom:
    y1, y2 = duty_min_zoom - 2, duty_max_zoom + 2
else:
    y1, y2 = 40, 60
axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)
axins.tick_params(axis='both', which='both', labelsize=10)
axins.grid(True, linestyle='--', linewidth=0.6, alpha=0.7, color='#b5b5b5')
ax.indicate_inset_zoom(axins, edgecolor="black")

ax.set_xlabel('Time (s)', fontsize=18, fontweight='bold')
ax.set_ylabel('Duty Cycle (%)', fontsize=18, fontweight='bold')
ax.set_xlim(0, 24)
max_duty = max((data[a]['Duty'].max() for a in data), default=80)
ax.set_ylim(0, min(105, max_duty * 1.15))
ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#b5b5b5', zorder=0)

leg = ax.legend(loc='upper right', frameon=True, facecolor='white',
                edgecolor='black', borderaxespad=0.5, ncol=2, fontsize=11)
if leg:
    leg.get_frame().set_linewidth(0.8)

plt.tight_layout()
duty_png = os.path.join(OUT, "algo_comparison_duty_run0.png")
duty_pdf = os.path.join(OUT, "algo_comparison_duty_run0.pdf")
plt.savefig(duty_png, dpi=300, bbox_inches='tight')
plt.savefig(duty_pdf, format='pdf', bbox_inches='tight')
plt.close()
print(f"Saved DUTY plot: {duty_png}")

summary_path = os.path.join(OUT, "performance_summary.txt")
write_performance_summary(compute_stats_table(data, target_gmpp), summary_path)
print(f"Saved performance summary: {summary_path}")
print("\n=== ALL DONE ===")
print(f"Output directory: {OUT}")
