"""
Process and Plot 100-Second 5-Pattern (5 Pola) MPPT Comparison
==============================================================
This script processes and generates seamless continuous 100s data (5 patterns @ 20s each):
  - Pola 1 (00 - 20 s): 'uji motor 2 part 2' Run 1 (GMPP = 122.30 W, Irradiance ~880 W/m²)
  - Pola 2 (20 - 40 s): 'uji motor 20m' Run 2 (GMPP = 92.18 W, Irradiance ~660 W/m²) -> wode_2, pno_2, woa_2, de_2, gmpp_2
  - Pola 3 (40 - 60 s): 'uji motor 2 part 2' Run 4 (GMPP = 126.13 W, Irradiance ~910 W/m²)
  - Pola 4 (60 - 80 s): 'ujimotor' Run 3 (GMPP = 64.28 W, PSC Irradiance ~460 W/m²)
  - Pola 5 (80 - 100 s): 'ujimotor' Run 0 (GMPP = 138.49 W, STC Irradiance ~1000 W/m²)

Outputs:
  1. Seamless continuous 100-second TXT data (wode_100s, pno_100s, woa_100s, de_100s, gmpp_100s)
  2. Individual 20-second TXT data per pattern (wode_polaX_20s, etc.)
  3. Archived 40s data and scripts from previous experiment in subfolder 'data_40s_arsip/'
  4. Both Color (reference image style) & B&W (journal style) plots in 600 DPI PNG & PDF
  5. Statistical performance summary CSV
"""

import os
import shutil
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    
    # ---------------------------------------------------------
    # 1. DEFINE SOURCES AND METADATA FOR 5 PATTERNS
    # ---------------------------------------------------------
    folder_part2 = os.path.join(parent_dir, "uji motor 2 part 2")
    folder_ujimotor = os.path.join(parent_dir, "ujimotor")
    folder_20m = os.path.join(parent_dir, "uji motor 20m")
    
    sources = [
        {
            'pola': 1,
            'folder': folder_part2,
            'run': '1',
            'desc': 'Pola 1 (Run 1 part 2)',
            'wode': 'wode1.txt', 'pno': 'pno1.txt', 'woa': 'woa1.txt', 'de': 'de1.txt', 'gmpp': 'gmpp1.txt',
            'target_gmpp': 122.30,
            'irradiance': '880 W/m²',
            'condition': 'Uniform High'
        },
        {
            'pola': 2,
            'folder': folder_20m,
            'run': '2',
            'desc': 'Pola 2 (Run 2 20m - 92.18 W)',
            'wode': 'wode_2.txt', 'pno': 'pno_2.txt', 'woa': 'woa_2.txt', 'de': 'de_2.txt', 'gmpp': 'gmpp_2.txt',
            'target_gmpp': 92.18,
            'irradiance': '660 W/m²',
            'condition': 'Medium Irradiance'
        },
        {
            'pola': 3,
            'folder': folder_part2,
            'run': '4',
            'desc': 'Pola 3 (Run 4 part 2)',
            'wode': 'wode4.txt', 'pno': 'pno4.txt', 'woa': 'woa4.txt', 'de': 'de4.txt', 'gmpp': 'gmpp4.txt',
            'target_gmpp': 126.13,
            'irradiance': '910 W/m²',
            'condition': 'Uniform Peak'
        },
        {
            'pola': 4,
            'folder': folder_ujimotor,
            'run': '3',
            'desc': 'Pola 4 (Run 3 ujimotor)',
            'wode': 'wode3.txt', 'pno': 'pno3.txt', 'woa': 'woa3.txt', 'de': 'de3.txt', 'gmpp': 'gmpp3.txt',
            'target_gmpp': 64.28,
            'irradiance': '460 W/m² (PSC)',
            'condition': 'Partial Shading'
        },
        {
            'pola': 5,
            'folder': folder_ujimotor,
            'run': '0',
            'desc': 'Pola 5 (Run 0 ujimotor)',
            'wode': 'wode.txt', 'pno': 'pno.txt', 'woa': 'woa.txt', 'de': 'de.txt', 'gmpp': 'gmpp.txt',
            'target_gmpp': 138.49,
            'irradiance': '1000 W/m² (STC)',
            'condition': 'Full Irradiance (STC)'
        }
    ]

    algos = ['WODE', 'PNO', 'WOA', 'DE']
    kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
    threshold_power = 1.0

    # Styling Palettes
    algo_colors = {
        'WODE': '#0055b3',  # Solid Blue
        'PNO':  '#cc2222',  # Red
        'WOA':  '#1b8a2e',  # Green
        'DE':   '#d97706'   # Amber
    }
    algo_linestyles = {
        'WODE': '-',
        'PNO':  '--',
        'WOA':  '-.',
        'DE':   ':'
    }
    algo_bw_styles = {
        'WODE': {'linestyle': '-',   'marker': None,  'markevery': 25, 'lw': 1.6},
        'PNO':  {'linestyle': '--',  'marker': None,  'markevery': 25, 'lw': 1.6},
        'WOA':  {'linestyle': '-.',  'marker': None,  'markevery': 25, 'lw': 1.6},
        'DE':   {'linestyle': ':',   'marker': 'o',   'markevery': 25, 'lw': 1.6},
    }

    # ---------------------------------------------------------
    # 2. EXTRACT 20-SECOND SLICES & BUILD CONTINUOUS 100S DATA
    # ---------------------------------------------------------
    pola_data_20s = {a: {} for a in algos}
    pola_gmpp_20s = {}
    combined_100s = {a: [] for a in algos}

    for i, src in enumerate(sources):
        pola_num = i + 1
        t_offset = i * 20.0
        target_p = src['target_gmpp']
        
        # GMPP 20s slice
        t_step = np.linspace(0.0, 19.9, 195)
        df_gmpp_seg = pd.DataFrame({
            'Waktu': t_step,
            'Vin': np.nan, 'Iin': np.nan,
            'Pin': np.full_like(t_step, target_p),
            'Vout': np.nan, 'Iout': np.nan, 'Pout': np.nan,
            'Eff': np.full_like(t_step, 100.0),
            'Mode': 5,
            'Duty': np.nan
        })
        pola_gmpp_20s[pola_num] = df_gmpp_seg
        
        for a in algos:
            fn = src[a.lower()]
            fp = os.path.join(src['folder'], fn)
            if not os.path.exists(fp):
                print(f"[ERROR] File not found: {fp}")
                continue
            
            # Read first 10 columns
            df = pd.read_csv(fp, sep=r'\s+', header=None, usecols=range(10), names=kolom, on_bad_lines='skip')
            df = df.apply(pd.to_numeric, errors='coerce').dropna().reset_index(drop=True)
            
            mask = df['Pin'] > threshold_power
            if not mask.any():
                print(f"[WARNING] No power > {threshold_power} W in {fn}")
                continue
            
            first_idx = mask.idxmax()
            start_idx = max(0, first_idx - 1)
            t0 = df.loc[start_idx, 'Waktu']
            
            df_sub = df.loc[start_idx:].copy().reset_index(drop=True)
            df_sub['t_rel'] = df_sub['Waktu'] - t0
            df_20s = df_sub[df_sub['t_rel'] <= 20.0].copy().reset_index(drop=True)
            
            # Save 20s individual slice (Waktu from 0 to 20s)
            df_pola_save = df_20s.copy()
            df_pola_save['Waktu'] = df_pola_save['t_rel']
            pola_data_20s[a][pola_num] = df_pola_save[kolom]
            
            # Build seamless 100s continuous slice
            t_orig = df_20s['t_rel'].values
            t_scaled = t_offset + (t_orig / t_orig[-1]) * 20.0 if t_orig[-1] > 0 else t_offset + t_orig
            df_100s_slice = df_20s.copy()
            df_100s_slice['Waktu'] = t_scaled
            df_100s_slice['Pola'] = pola_num
            combined_100s[a].append(df_100s_slice)

    dfs_100s = {a: pd.concat(combined_100s[a], ignore_index=True) for a in algos}

    # ---------------------------------------------------------
    # 3. SAVE FORMATTED TXT DATA FILES
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("SAVING 100-SECOND & 20-SECOND PROCESSED TXT DATA FILES")
    print("="*60)

    def save_formatted_txt(df_to_save, out_path):
        """Save dataframe with exact 10-column tab-delimited formatting without headers."""
        with open(out_path, 'w', encoding='utf-8') as f:
            for _, row in df_to_save.iterrows():
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

    # A. 100-Second Continuous Files
    for a in algos:
        out_fn = os.path.join(base_dir, f"{a.lower()}_100s.txt")
        save_formatted_txt(dfs_100s[a][kolom], out_fn)
        print(f"  [SAVED] {os.path.basename(out_fn)} ({len(dfs_100s[a])} rows)")

    # GMPP continuous 100s file
    gmpp_100s_rows = []
    for i, src in enumerate(sources):
        t_offset = i * 20.0
        t_points = np.linspace(0.0, 19.9, 195)
        for tp in t_points:
            gmpp_100s_rows.append({
                'Waktu': t_offset + tp,
                'Vin': 0.0, 'Iin': 0.0,
                'Pin': src['target_gmpp'],
                'Vout': 0.0, 'Iout': 0.0, 'Pout': 0.0,
                'Eff': 100.0, 'Mode': 5, 'Duty': 0.0
            })
    df_gmpp_100s = pd.DataFrame(gmpp_100s_rows)
    out_gmpp_100s = os.path.join(base_dir, "gmpp_100s.txt")
    save_formatted_txt(df_gmpp_100s, out_gmpp_100s)
    print(f"  [SAVED] {os.path.basename(out_gmpp_100s)} ({len(df_gmpp_100s)} rows)")

    # B. Individual 20-Second Files per Pola
    for pola_num in range(1, 6):
        for a in algos:
            out_pola_fn = os.path.join(base_dir, f"{a.lower()}_pola{pola_num}_20s.txt")
            save_formatted_txt(pola_data_20s[a][pola_num], out_pola_fn)
            print(f"  [SAVED] {os.path.basename(out_pola_fn)}")
        
        out_gmpp_pola_fn = os.path.join(base_dir, f"gmpp_pola{pola_num}_20s.txt")
        save_formatted_txt(pola_gmpp_20s[pola_num], out_gmpp_pola_fn)
        print(f"  [SAVED] {os.path.basename(out_gmpp_pola_fn)}")

    # C. Archive 40s files from previous experiment into subfolder
    archive_dir = os.path.join(base_dir, "data_40s_arsip")
    os.makedirs(archive_dir, exist_ok=True)
    if os.path.exists(folder_part2):
        for f in os.listdir(folder_part2):
            if '40s' in f or 'pola' in f:
                src_f = os.path.join(folder_part2, f)
                dst_f = os.path.join(archive_dir, f)
                if os.path.isfile(src_f):
                    shutil.copy2(src_f, dst_f)
        print(f"  [ARCHIVED] Copied previous 40s experiment data to {os.path.basename(archive_dir)}/")

    # ---------------------------------------------------------
    # 4. CALCULATE STATISTICAL METRICS PER POLA
    # ---------------------------------------------------------
    stats_list = []
    for i, src in enumerate(sources):
        pola_num = i + 1
        t_target = src['target_gmpp']
        for a in algos:
            df_a = dfs_100s[a]
            sub = df_a[df_a['Pola'] == pola_num]
            
            # Tracking time (first time reach >= 95% target GMPP)
            track_thresh = 0.95 * t_target
            reached = sub[sub['Pin'] >= track_thresh]
            t_track = reached['t_rel'].iloc[0] if not reached.empty else np.nan
            
            # Steady state window: last 5 seconds (t_rel in [15.0, 20.0])
            steady = sub[(sub['t_rel'] >= 15.0) & (sub['t_rel'] <= 20.0)]
            if not steady.empty:
                p_avg = steady['Pin'].mean()
                eff = (p_avg / t_target) * 100
                ripple = steady['Pin'].max() - steady['Pin'].min()
            else:
                p_avg, eff, ripple = np.nan, np.nan, np.nan
                
            stats_list.append({
                'Pola': f"Pola {pola_num}",
                'Source': src['desc'],
                'Condition': src['condition'],
                'Irradiance': src['irradiance'],
                'GMPP_Target_W': t_target,
                'Algorithm': a,
                't_track_s': round(t_track, 3) if not pd.isna(t_track) else None,
                'p_avg_W': round(p_avg, 2) if not pd.isna(p_avg) else None,
                'Eff_pct': round(eff, 2) if not pd.isna(eff) else None,
                'Ripple_W': round(ripple, 2) if not pd.isna(ripple) else None
            })

    df_stats = pd.DataFrame(stats_list)
    stats_csv = os.path.join(base_dir, "mppt_performance_summary_100s.csv")
    df_stats.to_csv(stats_csv, index=False)
    print(f"  [SAVED] {os.path.basename(stats_csv)}")

    # ---------------------------------------------------------
    # 5. MATPLOTLIB STYLE SETUP (Publication Quality)
    # ---------------------------------------------------------
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

    # Stepped coordinates for Target GMPP
    gmpp_t = [0, 20, 20, 40, 40, 60, 60, 80, 80, 100]
    gmpp_p = [
        sources[0]['target_gmpp'], sources[0]['target_gmpp'],
        sources[1]['target_gmpp'], sources[1]['target_gmpp'],
        sources[2]['target_gmpp'], sources[2]['target_gmpp'],
        sources[3]['target_gmpp'], sources[3]['target_gmpp'],
        sources[4]['target_gmpp'], sources[4]['target_gmpp'],
    ]

    # =========================================================
    # PLOT 1A: COLOR POWER (Matching Example Image)
    # =========================================================
    print("\n" + "="*60)
    print("GENERATING PLOTS: COLOR & BLACK/WHITE")
    print("="*60)
    
    fig, ax = plt.subplots(figsize=(13, 6.2))

    # Red Target GMPP step line
    ax.plot(gmpp_t, gmpp_p, color='#e00000', linewidth=2.2, label='Target GMPP', zorder=2)

    for a in algos:
        df = dfs_100s[a]
        ax.plot(df['Waktu'], df['Pin'], color=algo_colors[a],
                linestyle=algo_linestyles[a], linewidth=1.5,
                label=f"{a} Power", zorder=3)

    # Top Irradiance and GMPP Annotation Boxes
    for i, src in enumerate(sources):
        x_center = i * 20.0 + 10.0
        ax.text(x_center, 150, f"{src['irradiance']}\nTarget = {src['target_gmpp']:.1f} W",
                ha='center', va='top', fontsize=9.0, fontweight='bold', color='#222222',
                bbox=dict(boxstyle='square,pad=0.3', facecolor='#ffffff', edgecolor='#888888', linewidth=0.7, alpha=0.95))

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Power (W)', fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 168)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(2))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg = ax.legend(loc='upper right', ncol=5, frameon=True, facecolor='white',
                    edgecolor='#333333', fontsize=10, handlelength=2.2, borderpad=0.45)
    leg.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    p_col_png = os.path.join(base_dir, "algo_comparison_power_100s_color.png")
    p_col_pdf = os.path.join(base_dir, "algo_comparison_power_100s_color.pdf")
    fig.savefig(p_col_png, dpi=600, bbox_inches='tight')
    fig.savefig(p_col_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] algo_comparison_power_100s_color.png & PDF (600 DPI)")

    # =========================================================
    # PLOT 1B: BLACK & WHITE POWER (Academic Journal Paper)
    # =========================================================
    fig, ax = plt.subplots(figsize=(13, 6.2))

    ax.plot(gmpp_t, gmpp_p, color='black', linewidth=1.8, dashes=(6, 3), label='Target GMPP', zorder=2)

    for a in algos:
        st = algo_bw_styles[a]
        df = dfs_100s[a]
        ax.plot(df['Waktu'], df['Pin'], color='black',
                linestyle=st['linestyle'], linewidth=st['lw'],
                marker=st['marker'], markersize=4.5, markevery=st['markevery'],
                markerfacecolor='black', markeredgecolor='black',
                label=a, zorder=3)

    for i, src in enumerate(sources):
        x_center = i * 20.0 + 10.0
        ax.text(x_center, 150, f"{src['irradiance']}\nGMPP = {src['target_gmpp']:.1f} W",
                ha='center', va='top', fontsize=9.0, fontweight='bold',
                bbox=dict(boxstyle='square,pad=0.3', facecolor='white', edgecolor='#666666', linewidth=0.7))

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('PV Power (W)', fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 168)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(2))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg = ax.legend(loc='upper right', ncol=5, frameon=True, facecolor='white',
                    edgecolor='black', fontsize=10, handlelength=2.5, borderpad=0.45)
    leg.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    p_bw_png = os.path.join(base_dir, "algo_comparison_power_100s_bw.png")
    p_bw_pdf = os.path.join(base_dir, "algo_comparison_power_100s_bw.pdf")
    fig.savefig(p_bw_png, dpi=600, bbox_inches='tight')
    fig.savefig(p_bw_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] algo_comparison_power_100s_bw.png & PDF (600 DPI)")

    # =========================================================
    # PLOT 2: DUTY CYCLE (COLOR & B/W)
    # =========================================================
    fig, ax = plt.subplots(figsize=(13, 6.2))
    for a in algos:
        df = dfs_100s[a]
        ax.plot(df['Waktu'], df['Duty'], color=algo_colors[a],
                linestyle=algo_linestyles[a], linewidth=1.5,
                label=f"{a} Duty", zorder=3)

    for i, src in enumerate(sources):
        x_center = i * 20.0 + 10.0
        ax.text(x_center, 94, f"{src['irradiance']}",
                ha='center', va='top', fontsize=9.0, fontweight='bold', color='#222222',
                bbox=dict(boxstyle='square,pad=0.25', facecolor='#ffffff', edgecolor='#888888', linewidth=0.7, alpha=0.95))

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Duty Cycle (%)', fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(2))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg = ax.legend(loc='upper right', ncol=4, frameon=True, facecolor='white',
                    edgecolor='#333333', fontsize=10, handlelength=2.2, borderpad=0.45)
    leg.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    d_col_png = os.path.join(base_dir, "algo_comparison_duty_100s_color.png")
    d_col_pdf = os.path.join(base_dir, "algo_comparison_duty_100s_color.pdf")
    fig.savefig(d_col_png, dpi=600, bbox_inches='tight')
    fig.savefig(d_col_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] algo_comparison_duty_100s_color.png & PDF (600 DPI)")

    # =========================================================
    # PLOT 3A: STACKED 2-PANEL COLOR (POWER + DUTY 100s)
    # =========================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8.8), sharex=True)

    # Top: Power
    ax1.plot(gmpp_t, gmpp_p, color='#e00000', linewidth=2.2, label='Target GMPP', zorder=2)
    for a in algos:
        df = dfs_100s[a]
        ax1.plot(df['Waktu'], df['Pin'], color=algo_colors[a],
                 linestyle=algo_linestyles[a], linewidth=1.4,
                 label=f"{a} Power", zorder=3)
        ax2.plot(df['Waktu'], df['Duty'], color=algo_colors[a],
                 linestyle=algo_linestyles[a], linewidth=1.4,
                 label=f"{a} Duty", zorder=3)

    for i, src in enumerate(sources):
        x_center = i * 20.0 + 10.0
        ax1.text(x_center, 150, f"{src['irradiance']}\nTarget = {src['target_gmpp']:.1f} W",
                 ha='center', va='top', fontsize=8.8, fontweight='bold', color='#222222',
                 bbox=dict(boxstyle='square,pad=0.25', facecolor='#ffffff', edgecolor='#888888', linewidth=0.7, alpha=0.95))

    ax1.set_ylabel('PV Power (W)', fontsize=12)
    ax1.set_ylim(0, 168)
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax1.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax1.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg1 = ax1.legend(loc='upper right', ncol=5, frameon=True, facecolor='white',
                      edgecolor='#333333', fontsize=9.5, handlelength=2.0, borderpad=0.4)
    leg1.get_frame().set_linewidth(0.8)

    # Bottom: Duty
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Duty Cycle (%)', fontsize=12)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax2.xaxis.set_minor_locator(ticker.MultipleLocator(2))
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax2.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax2.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg2 = ax2.legend(loc='upper right', ncol=4, frameon=True, facecolor='white',
                      edgecolor='#333333', fontsize=9.5, handlelength=2.0, borderpad=0.4)
    leg2.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    stacked_col_png = os.path.join(base_dir, "algo_comparison_power_duty_100s_color.png")
    stacked_col_pdf = os.path.join(base_dir, "algo_comparison_power_duty_100s_color.pdf")
    fig.savefig(stacked_col_png, dpi=600, bbox_inches='tight')
    fig.savefig(stacked_col_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] algo_comparison_power_duty_100s_color.png & PDF (600 DPI)")

    # =========================================================
    # PLOT 3B: STACKED 2-PANEL BLACK & WHITE
    # =========================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8.8), sharex=True)

    ax1.plot(gmpp_t, gmpp_p, color='black', linewidth=1.8, dashes=(6, 3), label='Target GMPP', zorder=2)
    for a in algos:
        st = algo_bw_styles[a]
        df = dfs_100s[a]
        ax1.plot(df['Waktu'], df['Pin'], color='black',
                 linestyle=st['linestyle'], linewidth=st['lw'],
                 marker=st['marker'], markersize=4.5, markevery=st['markevery'],
                 markerfacecolor='black', markeredgecolor='black',
                 label=a, zorder=3)
        ax2.plot(df['Waktu'], df['Duty'], color='black',
                 linestyle=st['linestyle'], linewidth=st['lw'],
                 marker=st['marker'], markersize=4.5, markevery=st['markevery'],
                 markerfacecolor='black', markeredgecolor='black',
                 label=a, zorder=3)

    for i, src in enumerate(sources):
        x_center = i * 20.0 + 10.0
        ax1.text(x_center, 150, f"{src['irradiance']}\nGMPP = {src['target_gmpp']:.1f} W",
                 ha='center', va='top', fontsize=8.8, fontweight='bold',
                 bbox=dict(boxstyle='square,pad=0.25', facecolor='white', edgecolor='#666666', linewidth=0.7))

    ax1.set_ylabel('PV Power (W)', fontsize=12)
    ax1.set_ylim(0, 168)
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax1.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax1.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg1 = ax1.legend(loc='upper right', ncol=5, frameon=True, facecolor='white',
                      edgecolor='black', fontsize=9.5, handlelength=2.2, borderpad=0.4)
    leg1.get_frame().set_linewidth(0.8)

    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Duty Cycle (%)', fontsize=12)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax2.xaxis.set_minor_locator(ticker.MultipleLocator(2))
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax2.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax2.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg2 = ax2.legend(loc='upper right', ncol=4, frameon=True, facecolor='white',
                      edgecolor='black', fontsize=9.5, handlelength=2.2, borderpad=0.4)
    leg2.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    stacked_bw_png = os.path.join(base_dir, "algo_comparison_power_duty_100s_bw.png")
    stacked_bw_pdf = os.path.join(base_dir, "algo_comparison_power_duty_100s_bw.pdf")
    fig.savefig(stacked_bw_png, dpi=600, bbox_inches='tight')
    fig.savefig(stacked_bw_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] algo_comparison_power_duty_100s_bw.png & PDF (600 DPI)")

    print("\n" + "="*60)
    print("ALL 5-PATTERN PROCESSING & PLOTTING COMPLETED SUCCESSFULLY!")
    print("="*60)

if __name__ == '__main__':
    main()
