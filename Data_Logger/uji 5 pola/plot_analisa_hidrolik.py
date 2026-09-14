import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    files_info = {
        'level5_nonshading': {
            'wode': os.path.join(base_dir, 'wode_pola5_20s.txt'),
            'target_gmpp': 138.49,
            'title': 'Level 5 (Non-Shading - STC 1000 W/m²)',
            'desc': 'level5_nonshading'
        },
        'level2_shading': {
            'wode': os.path.join(base_dir, 'wode_pola2_20s.txt'),
            'target_gmpp': 92.18,
            'title': 'Level 2 (Shading - 660 W/m²)',
            'desc': 'level2_shading'
        }
    }
    
    kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
    
    # Publication plot style
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

    # 1. GENERATE INDIVIDUAL 2-PANEL PLOTS (COLOR & B/W)
    for key, cfg in files_info.items():
        print(f"\nProcessing {cfg['title']}...")
        df_wode = pd.read_csv(cfg['wode'], sep=r'\s+', header=None, names=kolom).dropna()
        target_p = cfg['target_gmpp']
        
        # A. COLOR 2-PANEL
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7.2), sharex=True)
        ax1.axhline(target_p, color='#e00000', linestyle='--', linewidth=1.8, label=f'Target GMPP ({target_p:.1f} W)', zorder=2)
        ax1.plot(df_wode['Waktu'], df_wode['Pin'], color='#0055b3', linestyle='-', linewidth=1.8, label='PV Input Power ($P_{in}$)', zorder=3)
        ax1.plot(df_wode['Waktu'], df_wode['Pout'], color='#1b8a2e', linestyle='-.', linewidth=1.6, label='Hydraulic Motor Power ($P_{out}$)', zorder=3)
        
        ax1.set_ylabel('Power (W)', fontsize=12)
        ax1.set_xlim(0, 20)
        max_p = max(target_p, df_wode['Pin'].max()) * 1.15
        ax1.set_ylim(0, max_p)
        ax1.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
        ax1.legend(loc='lower right', frameon=True, facecolor='white', edgecolor='#333333', fontsize=10)
        ax1.set_title(f"Hydraulic System Response — {cfg['title']}", fontsize=13, fontweight='bold', pad=10)
        
        color_v = '#7c2d12'
        color_i = '#4338ca'
        ax2.plot(df_wode['Waktu'], df_wode['Vout'], color=color_v, linestyle='-', linewidth=1.7, label='Motor Voltage ($V_{out}$)', zorder=3)
        ax2.set_xlabel('Time (s)', fontsize=12)
        ax2.set_ylabel('Motor Voltage $V_{out}$ (V)', color=color_v, fontsize=12)
        ax2.tick_params(axis='y', labelcolor=color_v)
        ax2.set_xlim(0, 20)
        ax2.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
        
        ax2_twin = ax2.twinx()
        ax2_twin.plot(df_wode['Waktu'], df_wode['Iout'], color=color_i, linestyle='--', linewidth=1.7, label='Motor Current ($I_{out}$)', zorder=3)
        ax2_twin.set_ylabel('Motor Current $I_{out}$ (A)', color=color_i, fontsize=12)
        ax2_twin.tick_params(axis='y', labelcolor=color_i)
        
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='lower right', frameon=True, facecolor='white', edgecolor='#333333', fontsize=10)
        
        fig.tight_layout()
        out_png = os.path.join(base_dir, f"hydraulic_{cfg['desc']}_color.png")
        out_pdf = os.path.join(base_dir, f"hydraulic_{cfg['desc']}_color.pdf")
        fig.savefig(out_png, dpi=600, bbox_inches='tight')
        fig.savefig(out_pdf, format='pdf', bbox_inches='tight')
        plt.close(fig)
        print(f"  [SAVED] {os.path.basename(out_png)}")

        # B. BLACK & WHITE 2-PANEL (Journal standard)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7.2), sharex=True)
        ax1.axhline(target_p, color='black', linestyle=':', linewidth=1.8, label=f'Target GMPP ({target_p:.1f} W)', zorder=2)
        ax1.plot(df_wode['Waktu'], df_wode['Pin'], color='black', linestyle='-', linewidth=1.8, label='PV Input Power ($P_{in}$)', zorder=3)
        ax1.plot(df_wode['Waktu'], df_wode['Pout'], color='black', linestyle='--', linewidth=1.6, label='Hydraulic Motor Power ($P_{out}$)', zorder=3)
        
        ax1.set_ylabel('Power (W)', fontsize=12)
        ax1.set_xlim(0, 20)
        ax1.set_ylim(0, max_p)
        ax1.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
        ax1.legend(loc='lower right', frameon=True, facecolor='white', edgecolor='black', fontsize=10)
        ax1.set_title(f"Hydraulic System Response — {cfg['title']}", fontsize=13, fontweight='bold', pad=10)
        
        ax2.plot(df_wode['Waktu'], df_wode['Vout'], color='black', linestyle='-', linewidth=1.7, label='Motor Voltage ($V_{out}$)', zorder=3)
        ax2.set_xlabel('Time (s)', fontsize=12)
        ax2.set_ylabel('Motor Voltage $V_{out}$ (V)', color='black', fontsize=12)
        ax2.set_xlim(0, 20)
        ax2.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7, color='#cccccc', zorder=0)
        
        ax2_twin = ax2.twinx()
        ax2_twin.plot(df_wode['Waktu'], df_wode['Iout'], color='black', linestyle='--', linewidth=1.7, label='Motor Current ($I_{out}$)', zorder=3)
        ax2_twin.set_ylabel('Motor Current $I_{out}$ (A)', color='black', fontsize=12)
        
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='lower right', frameon=True, facecolor='white', edgecolor='black', fontsize=10)
        
        fig.tight_layout()
        out_bw_png = os.path.join(base_dir, f"hydraulic_{cfg['desc']}_bw.png")
        out_bw_pdf = os.path.join(base_dir, f"hydraulic_{cfg['desc']}_bw.pdf")
        fig.savefig(out_bw_png, dpi=600, bbox_inches='tight')
        fig.savefig(out_bw_pdf, format='pdf', bbox_inches='tight')
        plt.close(fig)
        print(f"  [SAVED] {os.path.basename(out_bw_png)}")

    # 2. COMBINED COMPARISON (COLOR & B/W)
    # Color Combined
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.0), sharex=False)
    df5 = pd.read_csv(files_info['level5_nonshading']['wode'], sep=r'\s+', header=None, names=kolom).dropna()
    ax1.axhline(138.49, color='#e00000', linestyle=':', linewidth=1.8, label='Target GMPP (138.5 W)')
    ax1.plot(df5['Waktu'], df5['Pin'], color='#0055b3', linestyle='-', linewidth=1.7, label='Input Power $P_{in}$ (PV)')
    ax1.plot(df5['Waktu'], df5['Pout'], color='#1b8a2e', linestyle='--', linewidth=1.6, label='Output Power $P_{out}$ (Hydraulic)')
    ax1.set_title('(a) Non-Shading Condition — Level 5 (1000 W/m²)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Power (W)', fontsize=11)
    ax1.set_xlabel('Time (s)', fontsize=11)
    ax1.set_xlim(0, 20)
    ax1.set_ylim(0, 165)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='lower right', fontsize=9.5)
    
    df2 = pd.read_csv(files_info['level2_shading']['wode'], sep=r'\s+', header=None, names=kolom).dropna()
    ax2.axhline(92.18, color='#e00000', linestyle=':', linewidth=1.8, label='Target GMPP (92.2 W)')
    ax2.plot(df2['Waktu'], df2['Pin'], color='#0055b3', linestyle='-', linewidth=1.7, label='Input Power $P_{in}$ (PV)')
    ax2.plot(df2['Waktu'], df2['Pout'], color='#1b8a2e', linestyle='--', linewidth=1.6, label='Output Power $P_{out}$ (Hydraulic)')
    ax2.set_title('(b) Shading Condition — Level 2 (660 W/m²)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Power (W)', fontsize=11)
    ax2.set_xlabel('Time (s)', fontsize=11)
    ax2.set_xlim(0, 20)
    ax2.set_ylim(0, 115)
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='lower right', fontsize=9.5)
    
    fig.tight_layout()
    comp_png = os.path.join(base_dir, "hydraulic_comparison_level5_vs_level2_color.png")
    comp_pdf = os.path.join(base_dir, "hydraulic_comparison_level5_vs_level2_color.pdf")
    fig.savefig(comp_png, dpi=600, bbox_inches='tight')
    fig.savefig(comp_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] {os.path.basename(comp_png)}")

    # B/W Combined
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.0), sharex=False)
    ax1.axhline(138.49, color='black', linestyle=':', linewidth=1.8, label='Target GMPP (138.5 W)')
    ax1.plot(df5['Waktu'], df5['Pin'], color='black', linestyle='-', linewidth=1.7, label='Input Power $P_{in}$ (PV)')
    ax1.plot(df5['Waktu'], df5['Pout'], color='black', linestyle='--', linewidth=1.6, label='Output Power $P_{out}$ (Hydraulic)')
    ax1.set_title('(a) Non-Shading Condition — Level 5 (1000 W/m²)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Power (W)', fontsize=11)
    ax1.set_xlabel('Time (s)', fontsize=11)
    ax1.set_xlim(0, 20)
    ax1.set_ylim(0, 165)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='lower right', fontsize=9.5)
    
    ax2.axhline(92.18, color='black', linestyle=':', linewidth=1.8, label='Target GMPP (92.2 W)')
    ax2.plot(df2['Waktu'], df2['Pin'], color='black', linestyle='-', linewidth=1.7, label='Input Power $P_{in}$ (PV)')
    ax2.plot(df2['Waktu'], df2['Pout'], color='black', linestyle='--', linewidth=1.6, label='Output Power $P_{out}$ (Hydraulic)')
    ax2.set_title('(b) Shading Condition — Level 2 (660 W/m²)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Power (W)', fontsize=11)
    ax2.set_xlabel('Time (s)', fontsize=11)
    ax2.set_xlim(0, 20)
    ax2.set_ylim(0, 115)
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='lower right', fontsize=9.5)
    
    fig.tight_layout()
    comp_bw_png = os.path.join(base_dir, "hydraulic_comparison_level5_vs_level2_bw.png")
    comp_bw_pdf = os.path.join(base_dir, "hydraulic_comparison_level5_vs_level2_bw.pdf")
    fig.savefig(comp_bw_png, dpi=600, bbox_inches='tight')
    fig.savefig(comp_bw_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"  [SAVED] {os.path.basename(comp_bw_png)}")

    print("\nALL HYDRAULIC PLOTS GENERATED SUCCESSFULLY!")

if __name__ == '__main__':
    main()
