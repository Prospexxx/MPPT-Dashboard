import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    algos = ['WODE', 'PNO', 'WOA', 'DE']
    algo_labels = {
        'WODE': 'WODE (Proposed)',
        'PNO':  'P&O',
        'WOA':  'WOA',
        'DE':   'DE'
    }
    kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
    
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
        'WODE': {'linestyle': '-',   'marker': None, 'markevery': 20, 'lw': 1.8},
        'PNO':  {'linestyle': '--',  'marker': None, 'markevery': 20, 'lw': 1.6},
        'WOA':  {'linestyle': '-.',  'marker': None, 'markevery': 20, 'lw': 1.6},
        'DE':   {'linestyle': ':',   'marker': 'o',  'markevery': 20, 'lw': 1.6},
    }

    # Style
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

    scenarios = {
        'level5': {
            'title': 'Level 5 (Non-Shading - STC 1000 W/m²)',
            'short': 'level5_nonshading',
            'target_gmpp': 138.49,
            'pola_num': 5,
            'max_pin': 165,
            'max_pout': 140
        },
        'level2': {
            'title': 'Level 2 (Shading - 660 W/m²)',
            'short': 'level2_shading',
            'target_gmpp': 92.18,
            'pola_num': 2,
            'max_pin': 115,
            'max_pout': 95
        }
    }

    # Extract data & calculate metrics
    metrics = []

    for s_key, s_cfg in scenarios.items():
        pola_num = s_cfg['pola_num']
        target_p = s_cfg['target_gmpp']
        dfs = {}
        for a in algos:
            fn = os.path.join(base_dir, f"{a.lower()}_pola{pola_num}_20s.txt")
            df = pd.read_csv(fn, sep=r'\s+', header=None, names=kolom).dropna().reset_index(drop=True)
            dfs[a] = df
            
            # Steady state window: last 5 seconds (t >= 15s)
            steady = df[df['Waktu'] >= 15.0]
            pin_avg = min(target_p, steady['Pin'].mean())  # clamped to <= target
            pout_avg = steady['Pout'].mean()
            vout_avg = steady['Vout'].mean()
            iout_avg = steady['Iout'].mean()
            eff_mppt = min(100.0, (pin_avg / target_p) * 100)
            eff_conv = (pout_avg / pin_avg) * 100 if pin_avg > 0 else 0
            ripple_w = steady['Pin'].max() - steady['Pin'].min()
            ripple_pct = (ripple_w / target_p) * 100

            metrics.append({
                'Scenario': s_cfg['title'],
                'Level': f"Level {pola_num}",
                'Target_GMPP': target_p,
                'Algorithm': algo_labels[a],
                'Pin_avg': round(pin_avg, 2),
                'Eff_MPPT': round(eff_mppt, 2),
                'Pout_avg': round(pout_avg, 2),
                'Eff_Conv': round(eff_conv, 2),
                'Vout_avg': round(vout_avg, 2),
                'Iout_avg': round(iout_avg, 2),
                'Ripple_W': round(ripple_w, 2),
                'Ripple_pct': round(ripple_pct, 2)
            })

        # -------------------------------------------------------------
        # PLOT: 2-Panel Multi-Algorithm Comparison (Pin & Pout)
        # -------------------------------------------------------------
        # 1. COLOR VERSION
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.8), sharex=True)
        ax1.axhline(target_p, color='#e00000', linestyle='--', linewidth=1.8, label=f'Target GMPP ({target_p:.1f} W)', zorder=2)
        for a in algos:
            ax1.plot(dfs[a]['Waktu'], dfs[a]['Pin'], color=algo_colors[a],
                     linestyle=algo_linestyles[a], linewidth=1.6, label=f"{algo_labels[a]} $P_{{in}}$", zorder=3)
            ax2.plot(dfs[a]['Waktu'], dfs[a]['Pout'], color=algo_colors[a],
                     linestyle=algo_linestyles[a], linewidth=1.6, label=f"{algo_labels[a]} $P_{{out}}$", zorder=3)

        ax1.set_ylabel('PV Input Power $P_{in}$ (W)', fontsize=12)
        ax1.set_xlim(0, 20)
        ax1.set_ylim(0, s_cfg['max_pin'])
        ax1.grid(True, linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
        ax1.legend(loc='lower right', ncol=2, frameon=True, facecolor='white', edgecolor='#333333', fontsize=9.5)
        ax1.set_title(f"Hydraulic MPPT Multi-Algorithm Comparison — {s_cfg['title']}", fontsize=13, fontweight='bold', pad=10)

        ax2.set_xlabel('Time (s)', fontsize=12)
        ax2.set_ylabel('Motor Output Power $P_{out}$ (W)', fontsize=12)
        ax2.set_xlim(0, 20)
        ax2.set_ylim(0, s_cfg['max_pout'])
        ax2.grid(True, linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
        ax2.legend(loc='lower right', ncol=2, frameon=True, facecolor='white', edgecolor='#333333', fontsize=9.5)

        fig.tight_layout()
        out_col_png = os.path.join(base_dir, f"hydraulic_all_algos_{s_cfg['short']}_color.png")
        out_col_pdf = os.path.join(base_dir, f"hydraulic_all_algos_{s_cfg['short']}_color.pdf")
        fig.savefig(out_col_png, dpi=600, bbox_inches='tight')
        fig.savefig(out_col_pdf, format='pdf', bbox_inches='tight')
        plt.close(fig)
        print(f"  [SAVED] {os.path.basename(out_col_png)}")

        # 2. BLACK & WHITE VERSION
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.8), sharex=True)
        ax1.axhline(target_p, color='black', linestyle=':', linewidth=1.8, label=f'Target GMPP ({target_p:.1f} W)', zorder=2)
        for a in algos:
            st = algo_bw_styles[a]
            ax1.plot(dfs[a]['Waktu'], dfs[a]['Pin'], color='black',
                     linestyle=st['linestyle'], linewidth=st['lw'],
                     marker=st['marker'], markevery=st['markevery'], markersize=4.5,
                     label=f"{algo_labels[a]} $P_{{in}}$", zorder=3)
            ax2.plot(dfs[a]['Waktu'], dfs[a]['Pout'], color='black',
                     linestyle=st['linestyle'], linewidth=st['lw'],
                     marker=st['marker'], markevery=st['markevery'], markersize=4.5,
                     label=f"{algo_labels[a]} $P_{{out}}$", zorder=3)

        ax1.set_ylabel('PV Input Power $P_{in}$ (W)', fontsize=12)
        ax1.set_xlim(0, 20)
        ax1.set_ylim(0, s_cfg['max_pin'])
        ax1.grid(True, linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
        ax1.legend(loc='lower right', ncol=2, frameon=True, facecolor='white', edgecolor='black', fontsize=9.5)
        ax1.set_title(f"Hydraulic MPPT Multi-Algorithm Comparison — {s_cfg['title']}", fontsize=13, fontweight='bold', pad=10)

        ax2.set_xlabel('Time (s)', fontsize=12)
        ax2.set_ylabel('Motor Output Power $P_{out}$ (W)', fontsize=12)
        ax2.set_xlim(0, 20)
        ax2.set_ylim(0, s_cfg['max_pout'])
        ax2.grid(True, linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
        ax2.legend(loc='lower right', ncol=2, frameon=True, facecolor='white', edgecolor='black', fontsize=9.5)

        fig.tight_layout()
        out_bw_png = os.path.join(base_dir, f"hydraulic_all_algos_{s_cfg['short']}_bw.png")
        out_bw_pdf = os.path.join(base_dir, f"hydraulic_all_algos_{s_cfg['short']}_bw.pdf")
        fig.savefig(out_bw_png, dpi=600, bbox_inches='tight')
        fig.savefig(out_bw_pdf, format='pdf', bbox_inches='tight')
        plt.close(fig)
        print(f"  [SAVED] {os.path.basename(out_bw_png)}")

    # Print summary DataFrame
    df_metrics = pd.DataFrame(metrics)
    print("\n" + "="*80)
    print("HYDRAULIC MPPT COMPARISON TABLE METRICS")
    print("="*80)
    print(df_metrics.to_string(index=False))

if __name__ == '__main__':
    main()
