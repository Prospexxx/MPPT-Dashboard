import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

def plot_mppt_comparison_power():
    # ==========================================
    # 1. PARAMETER PENGATURAN PLOT
    # ==========================================
    base_dir = os.path.dirname(__file__)
    
    max_duration = 40          # Durasi sumbu X yang ingin ditampilkan (detik)
    threshold_power = 1.0      # Batas daya untuk deteksi algoritma "Mulai jalan"
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
    for run_idx, suffix in enumerate(['', '1', '2', '3', '4']):
        wode_file = f'wode{suffix}.txt'
            
        file_list = [
            os.path.join(base_dir, wode_file),
            os.path.join(base_dir, f'pno{suffix}.txt'),
            os.path.join(base_dir, f'woa{suffix}.txt'),
            os.path.join(base_dir, f'de{suffix}.txt')
        ]
        
        # --- Ambil Target GMPP aktual dari karakteristik_p-v ---
        gmpp_file = os.path.join(base_dir, f'gmpp{suffix}.txt')
        target_gmpp_power = 64.28 # fallback default
        if os.path.exists(gmpp_file):
            try:
                kolom_gmpp = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
                df_gmpp = pd.read_csv(gmpp_file, sep=r'\s+', header=None, names=kolom_gmpp, on_bad_lines='skip')
                df_gmpp = df_gmpp.apply(pd.to_numeric, errors='coerce').dropna()
                
                df_gmpp_mode5 = df_gmpp[df_gmpp['Mode'] == 5]
                if df_gmpp_mode5.empty:
                    df_gmpp_mode5 = df_gmpp
                    
                df_gmpp_mode5 = df_gmpp_mode5.sort_values(by='Vin').reset_index(drop=True)
                
                if not df_gmpp_mode5.empty:
                    target_gmpp_power = df_gmpp_mode5['Pin'].max()
            except Exception as e:
                print(f"[WARNING] Gagal membaca target GMPP dari {gmpp_file}: {e}")
                
        
        print(f"\nMembuat plot perbandingan daya untuk Run {run_idx}...")
        fig, ax = plt.subplots(1, 1, figsize=(6.5, 4.5))

        # GMPP reference line for power plot
        ax.axhline(y=target_gmpp_power, color='black', linewidth=1.5, dashes=(6, 3),
                    label=f'Measured GMPP = {target_gmpp_power:.2f} W', zorder=2)

        # Buat inset axes untuk efek zoom-in ("paper style")
        # Pindahkan lebih ke kanan (sejajar dengan legend)
        axins = ax.inset_axes([0.55, 0.25, 0.4, 0.4])
        axins.axhline(y=target_gmpp_power, color='black', linewidth=1.5, dashes=(6, 3), zorder=2)

        max_power_found = target_gmpp_power
        valid_plots = 0
        power_min_zoom = 1000
        power_max_zoom = 0
        stats_data = []

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
            if df_final['Pin'].max() > max_power_found:
                max_power_found = df_final['Pin'].max()

            # Plot Power
            ax.plot(df_final['Waktu'], df_final['Pin'],
                     color=c, linestyle=ls, linewidth=1.5, zorder=3, label=algo_name)
            
            # Plot ke inset
            axins.plot(df_final['Waktu'], df_final['Pin'],
                     color=c, linestyle=ls, linewidth=1.5, zorder=3)
                     
            # Hitung min/max untuk zoom window
            mask_zoom = (df_final['Waktu'] >= 34) & (df_final['Waktu'] <= 38)
            if not df_final[mask_zoom].empty:
                power_min_zoom = min(power_min_zoom, df_final.loc[mask_zoom, 'Pin'].min())
                power_max_zoom = max(power_max_zoom, df_final.loc[mask_zoom, 'Pin'].max())

            # --- Hitung Statistik MPPT ---
            # 1. Tracking Time (Waktu pertama kali mencapai 95% GMPP)
            track_threshold = 0.95 * target_gmpp_power
            reached_idx = df_final[df_final['Pin'] >= track_threshold]
            t_track = reached_idx['Waktu'].iloc[0] if not reached_idx.empty else np.nan

            # 2. Steady-state metrics (30s - 40s)
            steady_mask = (df_final['Waktu'] >= 30) & (df_final['Waktu'] <= 40)
            df_steady = df_final[steady_mask]

            if not df_steady.empty:
                p_avg = df_steady['Pin'].mean()
                eff = (p_avg / target_gmpp_power) * 100 if target_gmpp_power > 0 else 0
                ripple = df_steady['Pin'].max() - df_steady['Pin'].min()
            else:
                eff, ripple = np.nan, np.nan

            stats_data.append([algo_name, f"{t_track:.2f}", f"{eff:.2f}", f"{ripple:.2f}"])

        if valid_plots == 0:
            print(f"Tidak ada data valid untuk diplot pada Run {run_idx}. Melewati...")
            plt.close(fig)
            continue

        # Konfigurasi inset axes (zoom-in window)
        x1, x2 = 34, 38
        if power_min_zoom < power_max_zoom:
            y1, y2 = power_min_zoom - 1.0, power_max_zoom + 1.0
        else:
            y1, y2 = target_gmpp_power - 5, target_gmpp_power + 2
            
        axins.set_xlim(x1, x2)
        axins.set_ylim(y1, y2)
        axins.tick_params(axis='both', which='both', labelsize=8)
        axins.grid(True, linestyle=':', linewidth=0.5)
        ax.indicate_inset_zoom(axins, edgecolor="black")

        ax.set_xlabel('Time (s)')
        ax.set_ylabel('PV Power (W)')
        ax.set_xlim(-0.5, max_duration)
        ax.set_ylim(0, max_power_found * 1.15)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.6, color='#aaaaaa', zorder=0)

        leg = ax.legend(loc='lower right', frameon=True, facecolor='white',
                           edgecolor='#999999', borderaxespad=0.5, ncol=2, fontsize=8)
        if leg:
            leg.get_frame().set_linewidth(0.6)
            
        # Tambahkan Tabel Statistik di kiri bawah
        if stats_data:
            columns = ["Algo", "t_track(s)", "Eff(%)", "Ripple(W)"]
            table = ax.table(cellText=stats_data, colLabels=columns, loc='lower left', 
                             bbox=[0.02, 0.05, 0.35, 0.22], cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(7.5)
            # Format header tabel
            for (row, col), cell in table.get_celld().items():
                cell.set_edgecolor('#aaaaaa')
                if row == 0:
                    cell.set_text_props(weight='bold')
                    cell.set_facecolor('#e0e0e0')
                elif col == 0:
                    cell.set_text_props(weight='bold')

        plt.tight_layout(rect=[0, 0, 1, 0.98])
        
        out_plot_png = os.path.join(base_dir, f'algo_comparison_power_run{run_idx}.png')
        out_plot_pdf = os.path.join(base_dir, f'algo_comparison_power_run{run_idx}.pdf')
        
        plt.savefig(out_plot_png, dpi=600, bbox_inches='tight')
        plt.savefig(out_plot_pdf, format='pdf', bbox_inches='tight')
        plt.close(fig)
        print(f"Berhasil menyimpan {os.path.basename(out_plot_png)} & PDF")

if __name__ == '__main__':
    plot_mppt_comparison_power()
