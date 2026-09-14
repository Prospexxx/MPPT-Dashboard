import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

def plot_all_gmpp_iv():
    base_dir = os.path.dirname(__file__)
    gmpp_files = glob.glob(os.path.join(base_dir, 'gmpp_*.txt'))
    
    for nama_file in gmpp_files:
        try:
            print(f"Membaca data dari {nama_file}...")
            
            # Kolom diperbarui untuk membaca Run_Num yang ditambahkan di Phase 2
            kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty', 'Run_Num']
            
            df = pd.read_csv(nama_file, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
            df = df.apply(pd.to_numeric, errors='coerce')
            df = df.dropna()
            
            if df.empty:
                print(f"Data kosong setelah dibersihkan untuk {nama_file}")
                continue
                
            df_gmpp = df[df['Mode'] == 5]
            if df_gmpp.empty:
                df_gmpp = df
                
            df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)

            # --- Filter Anti-Glitch Final ---
            # 1. Hapus spike ekstrem (ke atas maupun ke bawah) menggunakan rolling median
            df_gmpp['Pin_median'] = df_gmpp['Pin'].rolling(window=15, center=True, min_periods=1).median()
            df_gmpp = df_gmpp[abs(df_gmpp['Pin'] - df_gmpp['Pin_median']) <= 6.0]
            
            # 2. Ambil nilai maksimum Pin untuk setiap bin tegangan (0.1V) agar kurva atas mulus (envelope)
            df_gmpp['Vin_bin'] = df_gmpp['Vin'].round(1)
            idx_max = df_gmpp.groupby('Vin_bin')['Pin'].idxmax().dropna()
            df_gmpp = df_gmpp.loc[idx_max].sort_values(by='Vin').reset_index(drop=True)
            plt.rcdefaults()
            plt.rcParams.update({
                'font.family': 'serif',
                'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
                'mathtext.fontset': 'stix',
                'font.size': 11,
                'axes.labelsize': 13,
                'axes.labelweight': 'bold',
                'axes.linewidth': 0.8,
                'axes.edgecolor': '#333333',
                'xtick.direction': 'in',
                'ytick.direction': 'in',
                'xtick.top': True,
                'ytick.right': True,
                'xtick.labelsize': 11,
                'ytick.labelsize': 11,
                'legend.fontsize': 11,
                'legend.framealpha': 1.0,
                'legend.edgecolor': '#555555',
            })
            
            fig = plt.figure(figsize=(8, 5))

            plt.plot(df_gmpp['Vin'], df_gmpp['Iin'], color='#0060ad', linewidth=2.0, label='Experimental I-V Curve')

            idx_mpp = df_gmpp['Pin'].idxmax()
            v_mpp = df_gmpp.loc[idx_mpp, 'Vin']
            p_mpp = df_gmpp.loc[idx_mpp, 'Pin']
            i_mpp = df_gmpp.loc[idx_mpp, 'Iin']

            plt.scatter(v_mpp, i_mpp, color='#c03030', s=60, zorder=5, label='Global Maximum Power Point (GMPP)')

            mpp_text = f'GMPP:\n$I_{{GMPP}}$ = {i_mpp:.2f} A at $V_{{GMPP}}$ = {v_mpp:.2f} V\n($P_{{GMPP}}$ = {p_mpp:.2f} W)'
            plt.annotate(mpp_text,
                         xy=(v_mpp, i_mpp),
                         xycoords='data',
                         xytext=(0.95, 0.95), 
                         textcoords='axes fraction',
                         ha='right', va='top',
                         arrowprops=dict(color='#444444', arrowstyle='->', lw=1.0, connectionstyle='arc3,rad=-0.1'),
                         fontsize=12, fontweight='bold',
                         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999999", alpha=0.9))

            plt.xlabel(r'PV Voltage, $V_{\mathrm{in}}$ (V)')
            plt.ylabel(r'PV Current, $I_{\mathrm{in}}$ (A)')
            
            plt.grid(True, which='both', linestyle='--', alpha=0.6)
            plt.xlim(0, df_gmpp['Vin'].max() + 2)
            plt.ylim(0, df_gmpp['Iin'].max() + (df_gmpp['Iin'].max() * 0.25))
            
            plt.legend(loc='lower left', fontsize=11)
            plt.tight_layout()

            run_num = os.path.basename(nama_file).replace('.txt', '').split('_')[-1]
            out_plot = os.path.join(base_dir, f'karakteristik_iv_run{run_num}.png')
            plt.savefig(out_plot, dpi=600, bbox_inches='tight')
            plt.close(fig)
            print(f"Berhasil menyimpan {os.path.basename(out_plot)}")

        except Exception as e:
            print(f"[ERROR] Terjadi kesalahan pada {nama_file}: {e}")

if __name__ == '__main__':
    plot_all_gmpp_iv()