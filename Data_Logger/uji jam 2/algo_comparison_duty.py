import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def plot_mppt_comparison_duty():
    # ==========================================
    # 1. PARAMETER PENGATURAN PLOT
    # ==========================================
    base_dir = os.path.dirname(__file__)
    
    max_duration = 40          # Durasi sumbu X yang ingin ditampilkan (detik)
    threshold_power = 1.0      # Batas daya untuk deteksi algoritma "Mulai jalan"

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
    })

    # Loop through run 0 to 4
    for run_idx, suffix in enumerate(['', '1', '2', '3', '4', '5']):
        wode_file = f'wode{suffix}.txt'
            
        file_list = [
            os.path.join(base_dir, wode_file),
            os.path.join(base_dir, f'pno{suffix}.txt'),
            os.path.join(base_dir, f'woa{suffix}.txt'),
            os.path.join(base_dir, f'de{suffix}.txt')
        ]
        
        print(f"\nMembuat plot perbandingan duty untuk Run {run_idx}...")
        fig, ax = plt.subplots(1, 1, figsize=(6.5, 4.5))

        # Buat inset axes untuk efek zoom-in ("paper style") di top middle slightly left
        axins = ax.inset_axes([0.3, 0.6, 0.4, 0.35])

        valid_plots = 0
        max_duty_found = 0
        duty_min_zoom = 100
        duty_max_zoom = 0

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
                
            c = colors.get(algo_name, '#000000')
            ls = linestyles.get(algo_name, '-')
            
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

            valid_plots += 1
            if df_final['Duty'].max() > max_duty_found:
                max_duty_found = df_final['Duty'].max()

            # Plot Duty
            ax.plot(df_final['Waktu'], df_final['Duty'],
                     color=c, linestyle=ls, linewidth=1.5, zorder=3, label=algo_name)
                     
            # Plot ke inset
            axins.plot(df_final['Waktu'], df_final['Duty'],
                     color=c, linestyle=ls, linewidth=1.5, zorder=3)
                     
            # Hitung min/max untuk zoom window
            mask_zoom = (df_final['Waktu'] >= 34) & (df_final['Waktu'] <= 38)
            if not df_final[mask_zoom].empty:
                duty_min_zoom = min(duty_min_zoom, df_final.loc[mask_zoom, 'Duty'].min())
                duty_max_zoom = max(duty_max_zoom, df_final.loc[mask_zoom, 'Duty'].max())

        if valid_plots == 0:
            print(f"Tidak ada data valid untuk diplot pada Run {run_idx}. Melewati...")
            plt.close(fig)
            continue

        # Konfigurasi inset axes (zoom-in window)
        x1, x2 = 34, 38
        if duty_min_zoom < duty_max_zoom:
            y1, y2 = duty_min_zoom - 2, duty_max_zoom + 2
        else:
            y1, y2 = 40, 60
            
        axins.set_xlim(x1, x2)
        axins.set_ylim(y1, y2)
        axins.tick_params(axis='both', which='both', labelsize=8)
        axins.grid(True, linestyle=':', linewidth=0.5)
        ax.indicate_inset_zoom(axins, edgecolor="black")

        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Duty Cycle (%)')
        ax.set_xlim(-0.5, max_duration)
        ax.set_ylim(0, min(105, max_duty_found * 1.15))
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.6, color='#aaaaaa', zorder=0)

        leg = ax.legend(loc='upper right', frameon=True, facecolor='white',
                           edgecolor='#999999', borderaxespad=0.5, ncol=2, fontsize=8)
        if leg:
            leg.get_frame().set_linewidth(0.6)
            
        plt.tight_layout(rect=[0, 0, 1, 0.98])
        
        out_plot = os.path.join(base_dir, f'algo_comparison_duty_run{run_idx}.png')
        plt.savefig(out_plot, dpi=600, bbox_inches='tight')
        plt.close(fig)
        print(f"Berhasil menyimpan {os.path.basename(out_plot)}")

if __name__ == '__main__':
    plot_mppt_comparison_duty()
