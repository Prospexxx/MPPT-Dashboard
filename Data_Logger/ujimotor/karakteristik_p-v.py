import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

def plot_all_gmpp():
    base_dir = os.path.dirname(__file__)
    gmpp_files = [os.path.join(base_dir, f'gmpp{suffix}.txt') for suffix in ['', '1', '2', '3', '4']]
    
    for run_idx, nama_file in enumerate(gmpp_files):
        try:
            print(f"Membaca data dari {nama_file}...")
            
            # Kolom tanpa Run_Num untuk uji resistor
            kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
            
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

            plt.plot(df_gmpp['Vin'], df_gmpp['Pin'], color='#c03030', linewidth=2.0, label='Experimental P-V Curve')

            idx_mpp = df_gmpp['Pin'].idxmax()
            v_mpp = df_gmpp.loc[idx_mpp, 'Vin']
            p_mpp = df_gmpp.loc[idx_mpp, 'Pin']

            plt.scatter(v_mpp, p_mpp, color='#0060ad', s=60, zorder=5, label='Global Maximum Power Point (GMPP)')

            plt.annotate(f'GMPP:\n$P_{{GMPP}}$ = {p_mpp:.2f} W at $V_{{GMPP}}$ = {v_mpp:.2f} V',
                         xy=(v_mpp, p_mpp),
                         xycoords='data',
                         xytext=(0.95, 0.95),
                         textcoords='axes fraction',
                         ha='right', va='top',
                         arrowprops=dict(color='#444444', arrowstyle='->', lw=1.0, connectionstyle='arc3,rad=-0.1'),
                         fontsize=12, fontweight='bold',
                         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999999", alpha=0.9))

            plt.xlabel(r'PV Voltage, $V_{\mathrm{in}}$ (V)')
            plt.ylabel(r'PV Power, $P_{\mathrm{in}}$ (W)')
            
            plt.grid(True, which='both', linestyle='--', alpha=0.6)
            plt.xlim(0, df_gmpp['Vin'].max() + 2)
            plt.ylim(0, df_gmpp['Pin'].max() + (df_gmpp['Pin'].max() * 0.2))
            
            plt.legend(loc='lower left', fontsize=11)
            plt.tight_layout()

            out_name = os.path.join(base_dir, f'karakteristik_p-v_run{run_idx}.png')
            out_name_pdf = os.path.join(base_dir, f'karakteristik_p-v_run{run_idx}.pdf')
            plt.savefig(out_name, dpi=600, bbox_inches='tight')
            plt.savefig(out_name_pdf, format='pdf', bbox_inches='tight')
            plt.close()
            print(f"Berhasil menyimpan {os.path.basename(out_name)} & PDF")

        except Exception as e:
            print(f"[ERROR] Terjadi kesalahan pada {nama_file}: {e}")

if __name__ == '__main__':
    plot_all_gmpp()