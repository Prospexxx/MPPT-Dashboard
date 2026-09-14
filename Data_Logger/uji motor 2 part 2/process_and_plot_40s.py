"""
Process and Plot 40-Second Multi-Pattern (4 Pola) MPPT Comparison
==================================================================
Dataset Sources:
  - Pola 1 (00 - 10 s): Run 1 (wode1, pno1, woa1, de1, gmpp1)
  - Pola 2 (10 - 20 s): Run 3 (wode3, pno3, woa3, de3, gmpp3)
  - Pola 3 (20 - 30 s): Run 4 (wode4, pno4, woa4, de4, gmpp4)
  - Pola 4 (30 - 40 s): Run 5 (wode5, pno5, woa5, de5, gmpp5)

Outputs:
  1. Processed TXT data files (40s continuous + 10s per Pola)
  2. Publication-quality B&W academic journal style plots (PNG 600 DPI + PDF):
     - algo_comparison_power_40s.png / .pdf
     - algo_comparison_duty_40s.png / .pdf
     - algo_comparison_power_duty_40s.png / .pdf
  3. Performance statistics summary table (CSV)
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ---------------------------------------------------------
    # 1. PARAMETERS & CONFIGURATION
    # ---------------------------------------------------------
    runs = ['1', '3', '4', '5']
    algos = ['WODE', 'PNO', 'WOA', 'DE']
    kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
    threshold_power = 1.0

    # Line styles matching journal standard (B&W)
    algo_styles = {
        'WODE': {'linestyle': '-',   'marker': None,  'markevery': 12, 'lw': 1.6},
        'PNO':  {'linestyle': '--',  'marker': None,  'markevery': 12, 'lw': 1.6},
        'WOA':  {'linestyle': '-.',  'marker': None,  'markevery': 12, 'lw': 1.6},
        'DE':   {'linestyle': ':',   'marker': 'o',   'markevery': 12, 'lw': 1.6},
    }

    # ---------------------------------------------------------
    # 2. READ GMPP TARGETS PER RUN
    # ---------------------------------------------------------
    gmpp_targets = []
    gmpp_raw_dfs = {}
    for r in runs:
        gfile = os.path.join(base_dir, f'gmpp{r}.txt')
        if not os.path.exists(gfile):
            print(f"[WARNING] GMPP file not found: {gfile}")
            gmpp_targets.append(64.28)
            continue
        
        df_g = pd.read_csv(gfile, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
        df_g = df_g.apply(pd.to_numeric, errors='coerce').dropna()
        df_mode5 = df_g[df_g['Mode'] == 5]
        if df_mode5.empty:
            df_mode5 = df_g
        target_p = df_mode5['Pin'].max()
        gmpp_targets.append(target_p)
        gmpp_raw_dfs[r] = df_g
        print(f"-> Target GMPP Run {r}: {target_p:.2f} W")

    # ---------------------------------------------------------
    # 3. EXTRACT 10-SECOND SEGMENTS & BUILD CONTINUOUS 40S DATA
    # ---------------------------------------------------------
    pola_data_10s = {a: {} for a in algos}  # [algo][pola_idx] = df (t in 0..10s)
    pola_gmpp_10s = {}
    combined_data_40s = {a: [] for a in algos}
    
    for i, r in enumerate(runs):
        pola_num = i + 1
        t_offset = i * 10.0
        
        # GMPP segment for this 10s
        target_p = gmpp_targets[i]
        t_step = np.linspace(0.0, 9.9, 98)
        df_gmpp_seg = pd.DataFrame({
            'Waktu': t_step,
            'Vin': np.nan,
            'Iin': np.nan,
            'Pin': np.full_like(t_step, target_p),
            'Vout': np.nan,
            'Iout': np.nan,
            'Pout': np.nan,
            'Eff': np.full_like(t_step, 100.0),
            'Mode': 5,
            'Duty': np.nan
        })
        pola_gmpp_10s[pola_num] = df_gmpp_seg
        
        for a in algos:
            fname = f"{a.lower()}{r}.txt"
            fpath = os.path.join(base_dir, fname)
            if not os.path.exists(fpath):
                print(f"[ERROR] File not found: {fname}")
                continue
            
            df = pd.read_csv(fpath, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
            df = df.apply(pd.to_numeric, errors='coerce').dropna().reset_index(drop=True)
            
            # Detect start time
            mask = df['Pin'] > threshold_power
            if not mask.any():
                print(f"[WARNING] No power > {threshold_power} W in {fname}")
                continue
            
            first_idx = mask.idxmax()
            start_idx = max(0, first_idx - 1)
            t0 = df.loc[start_idx, 'Waktu']
            
            df_sub = df.loc[start_idx:].copy().reset_index(drop=True)
            df_sub['t_rel'] = df_sub['Waktu'] - t0
            
            # Slice first 10 seconds
            df_10s = df_sub[df_sub['t_rel'] <= 10.0].copy().reset_index(drop=True)
            
            # Save 10s individual slice (Waktu from 0 to 10s)
            df_pola_save = df_10s.copy()
            df_pola_save['Waktu'] = df_pola_save['t_rel']
            pola_data_10s[a][pola_num] = df_pola_save[kolom]
            
            # Build 40s continuous slice (Waktu from t_offset to t_offset + 10s)
            df_40s_slice = df_10s.copy()
            df_40s_slice['Waktu'] = t_offset + df_40s_slice['t_rel']
            df_40s_slice['Pola'] = pola_num
            df_40s_slice['Run'] = r
            combined_data_40s[a].append(df_40s_slice)

    # Concatenate 40s dataframes
    dfs_40s = {a: pd.concat(combined_data_40s[a], ignore_index=True) for a in algos}

    # ---------------------------------------------------------
    # 4. SAVE TXT DATA FILES (Requirement 1)
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("SAVING PROCESSED TXT DATA FILES")
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

    # A. 40-Second Continuous Files
    for a in algos:
        out_fn = os.path.join(base_dir, f"{a.lower()}_40s.txt")
        save_formatted_txt(dfs_40s[a][kolom], out_fn)
        print(f"  [SAVED] {os.path.basename(out_fn)} ({len(dfs_40s[a])} rows)")
        
    # GMPP continuous 40s file
    gmpp_40s_rows = []
    for i, r in enumerate(runs):
        t_offset = i * 10.0
        t_points = np.linspace(0.0, 9.9, 98)
        for tp in t_points:
            gmpp_40s_rows.append({
                'Waktu': t_offset + tp,
                'Vin': 0.0, 'Iin': 0.0,
                'Pin': gmpp_targets[i],
                'Vout': 0.0, 'Iout': 0.0, 'Pout': 0.0,
                'Eff': 100.0, 'Mode': 5, 'Duty': 0.0
            })
    df_gmpp_40s = pd.DataFrame(gmpp_40s_rows)
    out_gmpp_40s = os.path.join(base_dir, "gmpp_40s.txt")
    save_formatted_txt(df_gmpp_40s, out_gmpp_40s)
    print(f"  [SAVED] {os.path.basename(out_gmpp_40s)} ({len(df_gmpp_40s)} rows)")

    # B. 10-Second Individual Files per Pola
    for pola_num in [1, 2, 3, 4]:
        for a in algos:
            out_pola_fn = os.path.join(base_dir, f"{a.lower()}_pola{pola_num}_10s.txt")
            save_formatted_txt(pola_data_10s[a][pola_num], out_pola_fn)
            print(f"  [SAVED] {os.path.basename(out_pola_fn)}")
        
        # Save individual GMPP pola 10s
        out_gmpp_pola_fn = os.path.join(base_dir, f"gmpp_pola{pola_num}_10s.txt")
        save_formatted_txt(pola_gmpp_10s[pola_num], out_gmpp_pola_fn)
        print(f"  [SAVED] {os.path.basename(out_gmpp_pola_fn)}")

    # ---------------------------------------------------------
    # 5. CALCULATE STATISTICAL METRICS PER POLA
    # ---------------------------------------------------------
    stats_list = []
    for i, r in enumerate(runs):
        pola_num = i + 1
        t_target = gmpp_targets[i]
        for a in algos:
            df_a = dfs_40s[a]
            sub = df_a[df_a['Pola'] == pola_num]
            
            # Tracking time (first time reach >= 95% target GMPP)
            track_thresh = 0.95 * t_target
            reached = sub[sub['Pin'] >= track_thresh]
            t_track = reached['t_rel'].iloc[0] if not reached.empty else np.nan
            
            # Steady state window: last 3 seconds (t_rel in [7.0, 10.0])
            steady = sub[(sub['t_rel'] >= 7.0) & (sub['t_rel'] <= 10.0)]
            if not steady.empty:
                p_avg = steady['Pin'].mean()
                eff = (p_avg / t_target) * 100
                ripple = steady['Pin'].max() - steady['Pin'].min()
            else:
                p_avg, eff, ripple = np.nan, np.nan, np.nan
                
            stats_list.append({
                'Pola': f"Pola {pola_num}",
                'Run_Source': f"Run {r}",
                'GMPP_Target_W': t_target,
                'Algorithm': a,
                't_track_s': t_track,
                'p_avg_W': p_avg,
                'Eff_pct': eff,
                'Ripple_W': ripple
            })
            
    df_stats = pd.DataFrame(stats_list)
    stats_out_path = os.path.join(base_dir, "mppt_performance_summary_40s.csv")
    df_stats.to_csv(stats_out_path, index=False)
    print(f"  [SAVED] {os.path.basename(stats_out_path)}")

    # ---------------------------------------------------------
    # 6. PLOTTING SETUP (Academic Journal Standard)
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
        'axes.linewidth': 1.0,
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
        'xtick.major.width': 0.9,
        'ytick.major.width': 0.9,
        'xtick.minor.width': 0.6,
        'ytick.minor.width': 0.6,
        'xtick.minor.visible': True,
        'ytick.minor.visible': True,
    })

    # Stepped GMPP data coordinates for 40s
    gmpp_t = [0, 10, 10, 20, 20, 30, 30, 40]
    gmpp_p = [gmpp_targets[0], gmpp_targets[0],
              gmpp_targets[1], gmpp_targets[1],
              gmpp_targets[2], gmpp_targets[2],
              gmpp_targets[3], gmpp_targets[3]]

    pola_headers = [
        f"Pattern 1 (Run 1)\nGMPP = {gmpp_targets[0]:.2f} W",
        f"Pattern 2 (Run 3)\nGMPP = {gmpp_targets[1]:.2f} W",
        f"Pattern 3 (Run 4)\nGMPP = {gmpp_targets[2]:.2f} W",
        f"Pattern 4 (Run 5)\nGMPP = {gmpp_targets[3]:.2f} W"
    ]

    # =========================================================
    # PLOT 1: PV POWER COMPARISON (40s)
    # =========================================================
    print("\n" + "="*60)
    print("GENERATING PLOT 1: algo_comparison_power_40s")
    print("="*60)
    
    fig, ax = plt.subplots(figsize=(11, 6.2))

    # Subtle pattern shading
    ax.axvspan(0, 10, facecolor='#ffffff', alpha=1.0)
    ax.axvspan(10, 20, facecolor='#f8f8f8', alpha=1.0)
    ax.axvspan(20, 30, facecolor='#ffffff', alpha=1.0)
    ax.axvspan(30, 40, facecolor='#f8f8f8', alpha=1.0)

    # Measured GMPP step line
    ax.plot(gmpp_t, gmpp_p, color='black', linewidth=1.8, dashes=(6, 3),
            label='Measured GMPP', zorder=2)

    # Algorithms
    for a in algos:
        st = algo_styles[a]
        df = dfs_40s[a]
        ax.plot(df['Waktu'], df['Pin'], color='black',
                linestyle=st['linestyle'], linewidth=st['lw'],
                marker=st['marker'], markersize=4.5, markevery=st['markevery'],
                markerfacecolor='black', markeredgecolor='black',
                label=a, zorder=3)

    # Vertical divider lines
    for i in range(1, 4):
        ax.axvline(x=i*10, color='#555555', linestyle='--', linewidth=0.9, zorder=1)

    # Pattern headers
    for i, h in enumerate(pola_headers):
        ax.text(i*10 + 5, 147, h, ha='center', va='top', fontsize=9.5, fontweight='bold',
                bbox=dict(boxstyle='square,pad=0.35', facecolor='white', edgecolor='#666666', linewidth=0.8))

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('PV Power (W)', fontsize=12)
    ax.set_xlim(-0.5, 40.5)
    ax.set_ylim(0, 160)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    # Proportional Legend placed in lower right (x: 34-40s where power is steady at ~98W)
    leg = ax.legend(loc='lower right', ncol=2, frameon=True, facecolor='white',
                    edgecolor='black', fontsize=10.5, handlelength=2.5,
                    borderpad=0.6, labelspacing=0.4, borderaxespad=0.8)
    leg.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    power_png = os.path.join(base_dir, "algo_comparison_power_40s.png")
    power_pdf = os.path.join(base_dir, "algo_comparison_power_40s.pdf")
    fig.savefig(power_png, dpi=600, bbox_inches='tight')
    fig.savefig(power_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] {os.path.basename(power_png)} & PDF (600 DPI)")

    # =========================================================
    # PLOT 2: DUTY CYCLE COMPARISON (40s)
    # =========================================================
    print("\n" + "="*60)
    print("GENERATING PLOT 2: algo_comparison_duty_40s")
    print("="*60)
    
    fig, ax = plt.subplots(figsize=(11, 6.2))

    ax.axvspan(0, 10, facecolor='#ffffff', alpha=1.0)
    ax.axvspan(10, 20, facecolor='#f8f8f8', alpha=1.0)
    ax.axvspan(20, 30, facecolor='#ffffff', alpha=1.0)
    ax.axvspan(30, 40, facecolor='#f8f8f8', alpha=1.0)

    for a in algos:
        st = algo_styles[a]
        df = dfs_40s[a]
        ax.plot(df['Waktu'], df['Duty'], color='black',
                linestyle=st['linestyle'], linewidth=st['lw'],
                marker=st['marker'], markersize=4.5, markevery=st['markevery'],
                markerfacecolor='black', markeredgecolor='black',
                label=a, zorder=3)

    for i in range(1, 4):
        ax.axvline(x=i*10, color='#555555', linestyle='--', linewidth=0.9, zorder=1)

    for i, h in enumerate(pola_headers):
        ax.text(i*10 + 5, 93, h, ha='center', va='top', fontsize=9.5, fontweight='bold',
                bbox=dict(boxstyle='square,pad=0.35', facecolor='white', edgecolor='#666666', linewidth=0.8))

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Duty Cycle (%)', fontsize=12)
    ax.set_xlim(-0.5, 40.5)
    ax.set_ylim(0, 100)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg = ax.legend(loc='lower right', ncol=2, frameon=True, facecolor='white',
                    edgecolor='black', fontsize=10.5, handlelength=2.5,
                    borderpad=0.6, labelspacing=0.4, borderaxespad=0.8)
    leg.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    duty_png = os.path.join(base_dir, "algo_comparison_duty_40s.png")
    duty_pdf = os.path.join(base_dir, "algo_comparison_duty_40s.pdf")
    fig.savefig(duty_png, dpi=600, bbox_inches='tight')
    fig.savefig(duty_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] {os.path.basename(duty_png)} & PDF (600 DPI)")

    # =========================================================
    # PLOT 3: STACKED 2-PANEL (POWER & DUTY CYCLE 40s)
    # =========================================================
    print("\n" + "="*60)
    print("GENERATING PLOT 3: algo_comparison_power_duty_40s (Stacked 2-Panel)")
    print("="*60)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5), sharex=True)

    for ax_curr in [ax1, ax2]:
        ax_curr.axvspan(0, 10, facecolor='#ffffff', alpha=1.0)
        ax_curr.axvspan(10, 20, facecolor='#f8f8f8', alpha=1.0)
        ax_curr.axvspan(20, 30, facecolor='#ffffff', alpha=1.0)
        ax_curr.axvspan(30, 40, facecolor='#f8f8f8', alpha=1.0)
        for i in range(1, 4):
            ax_curr.axvline(x=i*10, color='#555555', linestyle='--', linewidth=0.9, zorder=1)

    # Top Plot: Power
    ax1.plot(gmpp_t, gmpp_p, color='black', linewidth=1.8, dashes=(6, 3),
             label='Measured GMPP', zorder=2)

    for a in algos:
        st = algo_styles[a]
        df = dfs_40s[a]
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

    for i, h in enumerate(pola_headers):
        ax1.text(i*10 + 5, 147, h, ha='center', va='top', fontsize=9.5, fontweight='bold',
                 bbox=dict(boxstyle='square,pad=0.3', facecolor='white', edgecolor='#666666', linewidth=0.8))

    ax1.set_ylabel('PV Power (W)', fontsize=12)
    ax1.set_ylim(0, 160)
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax1.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax1.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg1 = ax1.legend(loc='lower right', ncol=2, frameon=True, facecolor='white',
                      edgecolor='black', fontsize=9.5, handlelength=2.2, borderpad=0.5)
    leg1.get_frame().set_linewidth(0.8)

    # Bottom Plot: Duty
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Duty Cycle (%)', fontsize=12)
    ax2.set_xlim(-0.5, 40.5)
    ax2.set_ylim(0, 100)
    ax2.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax2.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax2.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax2.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)

    leg2 = ax2.legend(loc='lower right', ncol=4, frameon=True, facecolor='white',
                      edgecolor='black', fontsize=9.5, handlelength=2.2, borderpad=0.5)
    leg2.get_frame().set_linewidth(0.8)

    fig.tight_layout()
    stacked_png = os.path.join(base_dir, "algo_comparison_power_duty_40s.png")
    stacked_pdf = os.path.join(base_dir, "algo_comparison_power_duty_40s.pdf")
    fig.savefig(stacked_png, dpi=600, bbox_inches='tight')
    fig.savefig(stacked_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] {os.path.basename(stacked_png)} & PDF (600 DPI)")
    
    print("\n" + "="*60)
    print("ALL PROCESSING AND PLOTTING COMPLETED SUCCESSFULLY!")
    print("="*60)

if __name__ == '__main__':
    main()
