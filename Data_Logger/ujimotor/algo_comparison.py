import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def plot_mppt_comparison():
    # ==========================================
    # 1. PARAMETER PENGATURAN PLOT
    # ==========================================
    base_dir = os.path.dirname(__file__)
    
    # List of files to compare (you can add more or change them)
    file_list = [
        os.path.join(base_dir, 'wode3.txt'),
        os.path.join(base_dir, 'pno3.txt'),
        os.path.join(base_dir, 'woa3.txt'),
        os.path.join(base_dir, 'de3.txt')
    ]
    
    max_duration = 20          # Durasi sumbu X yang ingin ditampilkan (detik)
    threshold_power = 1.0      # Batas daya untuk deteksi algoritma "Mulai jalan"
    target_gmpp_power = 64.28  # Daya puncak target dari kurva P-V

    # Define colors for different algorithms
    colors = {
        'WODE': '#0060ad',
        'PNO': '#c03030',
        'WOA': '#228B22',
        'DE': '#D2691E'
    }
    
    linestyles = {
        'WODE': '-',
        'PNO': '--',
        'WOA': '-.',
        'DE': ':'
    }

    markers = {
        'WODE': 'o',
        'PNO': 's',
        'WOA': '^',
        'DE': 'D'
    }
    
    # Fallback colors if more algorithms are added
    default_colors = ['#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    default_linestyles = ['-', '--', '-.', ':']
    color_idx = 0

    # ==========================================
    # 2. PLOTTING SETUP (Publication Quality)
    # ==========================================
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
        'legend.fontsize': 8.5,
        'legend.framealpha': 1.0,
        'legend.edgecolor': '#555555',
        'legend.fancybox': False,
        'legend.handlelength': 2.0,
        'legend.handletextpad': 0.5,
        'legend.borderpad': 0.4,
        'legend.labelspacing': 0.35,
        'figure.facecolor': 'white',
        'figure.dpi': 150,
        'savefig.dpi': 600,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.02,
    })

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.5, 8.0),
                                     gridspec_kw={'hspace': 0.32})
                                     
    # Titles are omitted in academic papers (use captions instead)

    # GMPP reference line for power plot
    ax2.axhline(y=target_gmpp_power, color='black', linestyle='--',
                linewidth=1.5, dashes=(6, 3),
                label=f'Target GMPP = {target_gmpp_power} W', zorder=2)

    # ==========================================
    # 3. DATA PROCESSING & PLOTTING LOOP
    # ==========================================
    max_power_found = target_gmpp_power

    for file_path in file_list:
        if not os.path.exists(file_path):
            print(f"[WARNING] File not found: {os.path.basename(file_path)}. Skipping...")
            continue
            
        base_name = os.path.basename(file_path).lower()
        if 'wode' in base_name:
            algo_name = 'WODE'
        elif 'woa' in base_name:
            algo_name = 'WOA'
        elif 'pno' in base_name:
            algo_name = 'PNO'
        elif 'de' in base_name:
            algo_name = 'DE'
        else:
            algo_name = os.path.splitext(os.path.basename(file_path))[0].upper()
            
        c = colors.get(algo_name)
        if not c:
            c = default_colors[color_idx % len(default_colors)]
            ls = default_linestyles[color_idx % len(default_linestyles)]
            color_idx += 1
        else:
            ls = linestyles.get(algo_name, '-')
            
        m = markers.get(algo_name, 'o')

        print(f"Processing {algo_name} from '{os.path.basename(file_path)}'...")
        kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
        try:
            df = pd.read_csv(file_path, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
            df = df.apply(pd.to_numeric, errors='coerce').dropna()
        except Exception as e:
            print(f"[ERROR] Failed to read {file_path}: {e}")
            continue
            
        if df.empty:
            continue

        # Detect start time
        df_start_mask = df['Pin'] > threshold_power
        if not df_start_mask.any():
            continue
            
        first_high_idx = df_start_mask.idxmax()
        start_idx = max(0, first_high_idx - 1)
        start_time = df.loc[start_idx, 'Waktu']
        
        df_filtered = df.loc[start_idx:].copy()
        df_filtered['Waktu'] = df_filtered['Waktu'] - start_time
        df_final = df_filtered[df_filtered['Waktu'] <= max_duration]
        
        if df_final.empty:
            continue

        if df_final['Pin'].max() > max_power_found:
            max_power_found = df_final['Pin'].max()

        # Plot Duty (a)
        ax1.plot(df_final['Waktu'], df_final['Duty'],
                 color=c, linestyle=ls, linewidth=1.5, zorder=3, label=algo_name)

        # Plot Power (b)
        ax2.plot(df_final['Waktu'], df_final['Pin'],
                 color=c, linestyle=ls, linewidth=1.5, zorder=3, label=algo_name)

    # ==========================================
    # 4. FINALIZING AXES
    # ==========================================
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Duty Cycle (%)')
    ax1.set_xlim(-0.5, max_duration)
    ax1.set_ylim(0, 105)
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax1.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax1.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.6, color='#aaaaaa', zorder=0)

    # Move legend to upper right to avoid covering the steady-state duty cycle lines
    leg1 = ax1.legend(loc='upper right', frameon=True, facecolor='white',
                       edgecolor='#999999', borderaxespad=0.5, ncol=2, fontsize=8)
    if leg1:
        leg1.get_frame().set_linewidth(0.6)
    
    ax1.text(-0.12, 1.02, '(a)', transform=ax1.transAxes, fontsize=12,
             fontweight='bold', va='bottom', ha='left')

    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('PV Power (W)')
    ax2.set_xlim(-0.5, max_duration)
    ax2.set_ylim(0, max_power_found * 1.15)
    ax2.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax2.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax2.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.6, color='#aaaaaa', zorder=0)

    leg2 = ax2.legend(loc='lower right', frameon=True, facecolor='white',
                       edgecolor='#999999', borderaxespad=0.5, ncol=2, fontsize=8)
    if leg2:
        leg2.get_frame().set_linewidth(0.6)
        
    ax2.text(-0.12, 1.02, '(b)', transform=ax2.transAxes, fontsize=12,
             fontweight='bold', va='bottom', ha='left')

    fig.align_ylabels([ax1, ax2])
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()

if __name__ == '__main__':
    plot_mppt_comparison()