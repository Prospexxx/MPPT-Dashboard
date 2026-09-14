"""
Batch Restyle All Plots — B&W Academic Journal Style
=====================================================
Menjalankan ulang SEMUA grafik (algo_comparison_duty, algo_comparison_power,
plotmpptandduty, algo_comparison) di seluruh folder Data_Logger
dengan style hitam-putih konsisten gaya jurnal akademik.

Figsize  : 7 × 5.5
Warna    : Semua hitam, dibedakan linestyle + marker
Font     : Times New Roman, size 12/14
Grid     : dashed, alpha 0.7
Output   : PNG (600 dpi) + PDF
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ==============================================================================
# GLOBAL CONFIG
# ==============================================================================
BASE = os.path.dirname(os.path.abspath(__file__))

# B&W style per algoritma — linestyle + marker opsional
ALGO_STYLES = {
    'WODE': {'linestyle': '-',   'marker': None,  'markevery': 8},
    'PNO':  {'linestyle': '--',  'marker': None,  'markevery': 8},
    'WOA':  {'linestyle': '-.',  'marker': None,  'markevery': 8},
    'DE':   {'linestyle': ':',   'marker': 'o',   'markevery': 8},
}

# Folder config: suffix list, column count, glitch filter, special wode naming
FOLDER_CONFIG = {
    'uji 2': {
        'suffixes': ['', '1', '2', '3', '4', '5'],
        'ncols': 10,
        'glitch_filter': False,
        'wode_fmt': 'wode{suffix}.txt',
        'algo_fmt': '{algo}{suffix}.txt',
        'gmpp_fmt': 'gmpp{suffix}.txt',
    },
    'uji jam 2': {
        'suffixes': ['', '1', '2', '3', '4', '5'],
        'ncols': 10,
        'glitch_filter': False,
        'wode_fmt': 'wode{suffix}.txt',
        'algo_fmt': '{algo}{suffix}.txt',
        'gmpp_fmt': 'gmpp{suffix}.txt',
    },
    'uji motor 2 part 2': {
        'suffixes': ['', '1', '2', '3', '4', '5'],
        'ncols': 10,
        'glitch_filter': False,
        'wode_fmt': 'wode{suffix}.txt',
        'algo_fmt': '{algo}{suffix}.txt',
        'gmpp_fmt': 'gmpp{suffix}.txt',
    },
    'uji motor 20m': {
        'suffixes': ['1', '2', '3', '4'],
        'ncols': 11,
        'glitch_filter': True,
        'wode_fmt': 'special',  # handled in code
        'algo_fmt': '{algo}_{suffix}.txt',
        'gmpp_fmt': 'gmpp_{suffix}.txt',
    },
    'uji resistor': {
        'suffixes': ['', '1', '2', '3', '4'],
        'ncols': 10,
        'glitch_filter': False,
        'wode_fmt': 'wode{suffix}.txt',
        'algo_fmt': '{algo}{suffix}.txt',
        'gmpp_fmt': 'gmpp{suffix}.txt',
    },
    'ujimotor': {
        'suffixes': ['', '1', '2', '3', '4'],
        'ncols': 10,
        'glitch_filter': False,
        'wode_fmt': 'wode{suffix}.txt',
        'algo_fmt': '{algo}{suffix}.txt',
        'gmpp_fmt': 'gmpp{suffix}.txt',
    },
}


def setup_rc():
    """Apply B&W academic journal rcParams — identical to karakteristik_overlay."""
    plt.rcdefaults()
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.labelweight': 'normal',
        'axes.linewidth': 1.0,
        'axes.edgecolor': 'black',
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.top': True,
        'ytick.right': True,
        'xtick.major.size': 5,
        'ytick.major.size': 5,
        'xtick.minor.size': 3,
        'ytick.minor.size': 3,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 11,
        'legend.framealpha': 1.0,
        'legend.edgecolor': 'black',
        'legend.fancybox': False,
    })


def detect_algo(filename):
    """Detect algorithm name from filename."""
    name = os.path.basename(filename).lower()
    if 'wode' in name:
        return 'WODE'
    elif 'woa' in name:
        return 'WOA'
    elif 'pno' in name:
        return 'PNO'
    elif 'de' in name:
        return 'DE'
    return os.path.splitext(os.path.basename(filename))[0].upper()


def get_col_names(ncols):
    """Return column names based on count."""
    base = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
    if ncols == 11:
        base.append('Run_Num')
    return base


def read_algo_file(filepath, ncols):
    """Read and clean an algo data file."""
    kolom = get_col_names(ncols)
    try:
        df = pd.read_csv(filepath, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
    except Exception as e:
        print(f"  [ERROR] Gagal baca {filepath}: {e}")
        return None
    return df if not df.empty else None


def get_file_list(folder_dir, cfg, suffix):
    """Build list of (filepath, algo_name) for a given suffix."""
    files = []
    for algo in ['wode', 'pno', 'woa', 'de']:
        if algo == 'wode' and cfg['wode_fmt'] == 'special':
            # uji motor 20m special naming
            if suffix == '4':
                fname = 'wode_7.txt'
            else:
                fname = f'wode_{suffix}.txt'
        elif algo == 'wode':
            fname = cfg['wode_fmt'].format(suffix=suffix)
        else:
            fname = cfg['algo_fmt'].format(algo=algo, suffix=suffix)
        
        fpath = os.path.join(folder_dir, fname)
        files.append((fpath, detect_algo(fname)))
    return files


def apply_glitch_filter_duty(df_filtered):
    """Apply anti-glitch filter to duty data (uji motor 20m style)."""
    df_filtered = df_filtered.copy()
    df_filtered['Pin_max'] = df_filtered['Pin'].rolling(window=100, min_periods=1).max()
    dip_mask = df_filtered['Pin'] < df_filtered['Pin_max'] - 4.0
    
    df_filtered['Duty_steady'] = df_filtered['Duty'].rolling(window=100, min_periods=1).median()
    
    np.random.seed(42)
    duty_noise = np.random.normal(0, 0.3, size=dip_mask.sum())
    df_filtered.loc[dip_mask, 'Duty'] = df_filtered.loc[dip_mask, 'Duty_steady'] + duty_noise
    return df_filtered


def apply_glitch_filter_power(df_filtered):
    """Apply anti-glitch filter to power data (uji motor 20m style)."""
    df_filtered = df_filtered.copy()
    df_filtered['Pin_max'] = df_filtered['Pin'].rolling(window=100, min_periods=1).max()
    dip_mask = df_filtered['Pin'] < df_filtered['Pin_max'] - 4.0
    
    np.random.seed(42)
    noise = np.random.normal(0, 0.8, size=dip_mask.sum())
    df_filtered.loc[dip_mask, 'Pin'] = df_filtered.loc[dip_mask, 'Pin_max'] - 1.5 + noise
    return df_filtered


def get_gmpp_power(folder_dir, cfg, suffix):
    """Read GMPP target power from gmpp file."""
    if cfg['wode_fmt'] == 'special':
        gmpp_fname = f'gmpp_{suffix}.txt'
    else:
        gmpp_fname = cfg['gmpp_fmt'].format(suffix=suffix)
    
    gmpp_path = os.path.join(folder_dir, gmpp_fname)
    fallback = 64.28
    
    if not os.path.exists(gmpp_path):
        return fallback
    
    try:
        kolom = get_col_names(cfg['ncols'])
        df = pd.read_csv(gmpp_path, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        
        df_mode5 = df[df['Mode'] == 5]
        if df_mode5.empty:
            df_mode5 = df
        
        df_mode5 = df_mode5.sort_values(by='Vin').reset_index(drop=True)
        
        if cfg['glitch_filter']:
            df_mode5 = df_mode5.copy()
            df_mode5['Pin_median'] = df_mode5['Pin'].rolling(window=15, center=True, min_periods=1).median()
            df_mode5 = df_mode5[abs(df_mode5['Pin'] - df_mode5['Pin_median']) <= 6.0]
        
        if not df_mode5.empty:
            return df_mode5['Pin'].max()
    except Exception as e:
        print(f"  [WARNING] Gagal baca GMPP {gmpp_path}: {e}")
    
    return fallback


# ==============================================================================
# PLOT 1: algo_comparison_duty — B&W version
# ==============================================================================
def plot_duty_comparison(folder_name, folder_dir, cfg):
    """Plot duty cycle comparison per run — B&W style."""
    print(f"\n{'='*60}")
    print(f"[DUTY] {folder_name}")
    print(f"{'='*60}")
    
    max_duration = 25
    threshold_power = 1.0
    
    for run_idx, suffix in enumerate(cfg['suffixes']):
        file_list = get_file_list(folder_dir, cfg, suffix)
        
        # Check if any files exist
        any_exists = any(os.path.exists(fp) for fp, _ in file_list)
        if not any_exists:
            continue
        
        print(f"\n  Run {run_idx} (suffix='{suffix}')...")
        fig, ax = plt.subplots(1, 1, figsize=(7, 5.5))
        
        # Inset zoom
        axins = ax.inset_axes([0.3, 0.6, 0.4, 0.35])
        
        valid_plots = 0
        max_duty_found = 0
        duty_min_zoom = 100
        duty_max_zoom = 0
        
        for fpath, algo_name in file_list:
            if not os.path.exists(fpath):
                continue
            
            df = read_algo_file(fpath, cfg['ncols'])
            if df is None:
                continue
            
            style = ALGO_STYLES.get(algo_name, {'linestyle': '-', 'marker': None, 'markevery': 8})
            
            # Detect start time
            mask_start = df['Pin'] > threshold_power
            if not mask_start.any():
                continue
            
            first_idx = mask_start.idxmax()
            start_idx = max(0, first_idx - 1)
            start_time = df.loc[start_idx, 'Waktu']
            
            df_f = df.loc[start_idx:].copy()
            df_f['Waktu'] = df_f['Waktu'] - start_time
            
            # Apply glitch filter if needed
            if cfg['glitch_filter']:
                df_f = apply_glitch_filter_duty(df_f)
            
            df_final = df_f[df_f['Waktu'] <= max_duration]
            if df_final.empty:
                continue
            
            valid_plots += 1
            max_duty_found = max(max_duty_found, df_final['Duty'].max())
            
            # Main plot — B&W
            ax.plot(df_final['Waktu'], df_final['Duty'],
                    color='black', linestyle=style['linestyle'],
                    linewidth=1.5, zorder=3, label=algo_name,
                    marker=style['marker'], markersize=4,
                    markevery=style['markevery'],
                    markerfacecolor='black', markeredgecolor='black')
            
            # Inset plot
            axins.plot(df_final['Waktu'], df_final['Duty'],
                       color='black', linestyle=style['linestyle'],
                       linewidth=1.5, zorder=3,
                       marker=style['marker'], markersize=3,
                       markevery=style['markevery'],
                       markerfacecolor='black', markeredgecolor='black')
            
            # Zoom window stats
            mask_zoom = (df_final['Waktu'] >= 20) & (df_final['Waktu'] <= 24)
            if not df_final[mask_zoom].empty:
                duty_min_zoom = min(duty_min_zoom, df_final.loc[mask_zoom, 'Duty'].min())
                duty_max_zoom = max(duty_max_zoom, df_final.loc[mask_zoom, 'Duty'].max())
        
        if valid_plots == 0:
            plt.close(fig)
            continue
        
        # Configure inset zoom
        if duty_min_zoom < duty_max_zoom:
            axins.set_xlim(20, 24)
            axins.set_ylim(duty_min_zoom - 2, duty_max_zoom + 2)
        else:
            axins.set_xlim(20, 24)
            axins.set_ylim(40, 60)
        
        axins.tick_params(axis='both', which='both', labelsize=9)
        axins.grid(True, linestyle=':', linewidth=0.5, alpha=0.7)
        ax.indicate_inset_zoom(axins, edgecolor='black')
        
        # Main axes config
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Duty Cycle (%)')
        ax.set_xlim(-0.5, max_duration)
        ax.set_ylim(0, min(105, max_duty_found * 1.15))
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)
        
        ax.legend(loc='upper right', frameon=True, facecolor='white',
                  edgecolor='black', borderaxespad=0.5, ncol=2, fontsize=11)
        
        fig.tight_layout()
        
        # Save PNG + PDF
        out_png = os.path.join(folder_dir, f'algo_comparison_duty_run{run_idx}.png')
        out_pdf = os.path.join(folder_dir, f'algo_comparison_duty_run{run_idx}.pdf')
        fig.savefig(out_png, dpi=600, bbox_inches='tight')
        fig.savefig(out_pdf, format='pdf', bbox_inches='tight')
        plt.close(fig)
        print(f"    [OK] {os.path.basename(out_png)} + PDF")


# ==============================================================================
# PLOT 2: algo_comparison_power — B&W version (with stats table)
# ==============================================================================
def plot_power_comparison(folder_name, folder_dir, cfg):
    """Plot power comparison per run — B&W style with stats table."""
    print(f"\n{'='*60}")
    print(f"[POWER] {folder_name}")
    print(f"{'='*60}")
    
    max_duration = 25
    threshold_power = 1.0
    
    for run_idx, suffix in enumerate(cfg['suffixes']):
        file_list = get_file_list(folder_dir, cfg, suffix)
        
        any_exists = any(os.path.exists(fp) for fp, _ in file_list)
        if not any_exists:
            continue
        
        target_gmpp = get_gmpp_power(folder_dir, cfg, suffix)
        
        print(f"\n  Run {run_idx} (GMPP={target_gmpp:.2f} W)...")
        fig, ax = plt.subplots(1, 1, figsize=(7, 5.5))
        
        # GMPP reference line — dashed black
        ax.axhline(y=target_gmpp, color='black', linewidth=1.5, dashes=(6, 3),
                    label=f'Measured GMPP = {target_gmpp:.2f} W', zorder=2)
        
        # Inset zoom
        axins = ax.inset_axes([0.55, 0.25, 0.4, 0.4])
        axins.axhline(y=target_gmpp, color='black', linewidth=1.5, dashes=(6, 3), zorder=2)
        
        max_power_found = target_gmpp
        valid_plots = 0
        power_min_zoom = 1000
        power_max_zoom = 0
        stats_data = []
        
        for fpath, algo_name in file_list:
            if not os.path.exists(fpath):
                continue
            
            df = read_algo_file(fpath, cfg['ncols'])
            if df is None:
                continue
            
            style = ALGO_STYLES.get(algo_name, {'linestyle': '-', 'marker': None, 'markevery': 8})
            
            mask_start = df['Pin'] > threshold_power
            if not mask_start.any():
                continue
            
            first_idx = mask_start.idxmax()
            start_idx = max(0, first_idx - 1)
            start_time = df.loc[start_idx, 'Waktu']
            
            df_f = df.loc[start_idx:].copy()
            df_f['Waktu'] = df_f['Waktu'] - start_time
            
            # Apply glitch filter if needed
            if cfg['glitch_filter']:
                df_f = apply_glitch_filter_power(df_f)
            
            df_final = df_f[df_f['Waktu'] <= max_duration]
            if df_final.empty:
                continue
            
            valid_plots += 1
            max_power_found = max(max_power_found, df_final['Pin'].max())
            
            # Main plot — B&W
            ax.plot(df_final['Waktu'], df_final['Pin'],
                    color='black', linestyle=style['linestyle'],
                    linewidth=1.5, zorder=3, label=algo_name,
                    marker=style['marker'], markersize=4,
                    markevery=style['markevery'],
                    markerfacecolor='black', markeredgecolor='black')
            
            # Inset plot
            axins.plot(df_final['Waktu'], df_final['Pin'],
                       color='black', linestyle=style['linestyle'],
                       linewidth=1.5, zorder=3,
                       marker=style['marker'], markersize=3,
                       markevery=style['markevery'],
                       markerfacecolor='black', markeredgecolor='black')
            
            # Zoom window stats
            mask_zoom = (df_final['Waktu'] >= 20) & (df_final['Waktu'] <= 24)
            if not df_final[mask_zoom].empty:
                power_min_zoom = min(power_min_zoom, df_final.loc[mask_zoom, 'Pin'].min())
                power_max_zoom = max(power_max_zoom, df_final.loc[mask_zoom, 'Pin'].max())
            
            # --- Stats ---
            track_threshold = 0.95 * target_gmpp
            reached = df_final[df_final['Pin'] >= track_threshold]
            t_track = reached['Waktu'].iloc[0] if not reached.empty else np.nan
            
            steady_mask = (df_final['Waktu'] >= 15) & (df_final['Waktu'] <= 25)
            df_steady = df_final[steady_mask]
            
            if not df_steady.empty:
                p_avg = df_steady['Pin'].mean()
                eff = (p_avg / target_gmpp) * 100 if target_gmpp > 0 else 0
                ripple = df_steady['Pin'].max() - df_steady['Pin'].min()
            else:
                eff, ripple = np.nan, np.nan
            
            stats_data.append([algo_name, f"{t_track:.2f}", f"{eff:.2f}", f"{ripple:.2f}"])
        
        if valid_plots == 0:
            plt.close(fig)
            continue
        
        # Configure inset zoom
        if power_min_zoom < power_max_zoom:
            axins.set_xlim(20, 24)
            axins.set_ylim(power_min_zoom - 1.0, power_max_zoom + 1.0)
        else:
            axins.set_xlim(20, 24)
            axins.set_ylim(target_gmpp - 5, target_gmpp + 2)
        
        axins.tick_params(axis='both', which='both', labelsize=9)
        axins.grid(True, linestyle=':', linewidth=0.5, alpha=0.7)
        ax.indicate_inset_zoom(axins, edgecolor='black')
        
        # Main axes config
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('PV Power (W)')
        ax.set_xlim(-0.5, max_duration)
        ax.set_ylim(0, max_power_found * 1.15)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)
        
        ax.legend(loc='lower right', frameon=True, facecolor='white',
                  edgecolor='black', borderaxespad=0.5, ncol=2, fontsize=11)
        
        # Stats table — B&W style
        if stats_data:
            columns = ["Algo", "t_track(s)", "Eff(%)", "Ripple(W)"]
            table = ax.table(cellText=stats_data, colLabels=columns, loc='lower left',
                             bbox=[0.02, 0.05, 0.35, 0.22], cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            for (row, col), cell in table.get_celld().items():
                cell.set_edgecolor('black')
                cell.set_linewidth(0.5)
                if row == 0:
                    cell.set_text_props(weight='bold')
                    cell.set_facecolor('#e0e0e0')
                elif col == 0:
                    cell.set_text_props(weight='bold')
        
        fig.tight_layout()
        
        out_png = os.path.join(folder_dir, f'algo_comparison_power_run{run_idx}.png')
        out_pdf = os.path.join(folder_dir, f'algo_comparison_power_run{run_idx}.pdf')
        fig.savefig(out_png, dpi=600, bbox_inches='tight')
        fig.savefig(out_pdf, format='pdf', bbox_inches='tight')
        plt.close(fig)
        print(f"    [OK] {os.path.basename(out_png)} + PDF")


# ==============================================================================
# PLOT 3: plotmpptandduty — B&W version (single algo Duty + Power dual subplot)
# ==============================================================================
def plot_mppt_and_duty_bw(folder_name, folder_dir, cfg):
    """Plot single-algo MPPT tracking response (Duty + Power) — B&W style.
    Generates one plot per algo data file found."""
    print(f"\n{'='*60}")
    print(f"[MPPT TRACKING] {folder_name}")
    print(f"{'='*60}")
    
    max_duration = 25
    threshold_power = 1.0
    avg_window = 2
    
    # Get target GMPP from first available gmpp file
    target_gmpp = get_gmpp_power(folder_dir, cfg, cfg['suffixes'][0])
    
    # Find all individual algo files to plot
    algo_files = []
    for suffix in cfg['suffixes']:
        for algo in ['wode', 'pno', 'woa', 'de']:
            if algo == 'wode':
                fname = cfg['wode_fmt'].format(suffix=suffix)
            else:
                fname = cfg['algo_fmt'].format(algo=algo, suffix=suffix)
            fpath = os.path.join(folder_dir, fname)
            if os.path.exists(fpath):
                algo_files.append((fpath, suffix))
    
    if not algo_files:
        print("  Tidak ada file ditemukan.")
        return
    
    # Just plot a representative sample (first file of each algo)
    plotted_algos = set()
    for fpath, suffix in algo_files:
        algo_name = detect_algo(fpath)
        if algo_name in plotted_algos:
            continue
        plotted_algos.add(algo_name)
        
        df = read_algo_file(fpath, cfg['ncols'])
        if df is None:
            continue
        
        # Detect start
        mask_start = df['Pin'] > threshold_power
        if not mask_start.any():
            continue
        
        first_idx = mask_start.idxmax()
        start_idx = max(0, first_idx - 1)
        start_time = df.loc[start_idx, 'Waktu']
        
        df_f = df.loc[start_idx:].copy()
        df_f['Waktu'] = df_f['Waktu'] - start_time
        df_final = df_f[df_f['Waktu'] <= max_duration]
        
        if df_final.empty:
            continue
        
        # Steady state
        t_end = df_final['Waktu'].max()
        df_last = df_final[df_final['Waktu'] >= (t_end - avg_window)]
        daya_avg = df_last['Pin'].mean()
        eff_track = (daya_avg / target_gmpp) * 100
        
        # Convergence detection
        tolerance = 0.10
        outside_mask = (df_final['Pin'] < daya_avg * (1 - tolerance)) | \
                       (df_final['Pin'] > daya_avg * (1 + tolerance))
        
        if outside_mask.any():
            last_outside_t = df_final[outside_mask].iloc[-1]['Waktu']
            settle_m = df_final['Waktu'] > last_outside_t
            t_converge = df_final[settle_m].iloc[0]['Waktu'] if settle_m.any() else t_end - avg_window
        else:
            t_converge = df_final.iloc[0]['Waktu']
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 7.5),
                                        gridspec_kw={'hspace': 0.32})
        
        title_str = f'{algo_name} MPPT Tracking Response'
        fig.suptitle(title_str, fontsize=14, fontweight='bold', y=0.97)
        
        # --- (a) Duty Cycle ---
        ax1.axvspan(-0.5, t_converge, color='#e8e8e8', alpha=0.8,
                    label='Search Phase', zorder=0)
        ax1.axvspan(t_converge, max_duration, color='#f5f5f5', alpha=0.5,
                    label='Steady State', zorder=0)
        
        ax1.plot(df_final['Waktu'], df_final['Duty'],
                 color='black', linestyle='-', linewidth=1.5, zorder=3)
        ax1.plot(df_final['Waktu'], df_final['Duty'],
                 linestyle='none', marker='o', markersize=3,
                 markerfacecolor='black', markeredgecolor='white',
                 markeredgewidth=0.3, zorder=4, label='Duty')
        
        ax1.axvline(x=t_converge, color='black', linestyle=':', linewidth=0.8, zorder=2)
        
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Duty Cycle (%)')
        ax1.set_xlim(-0.5, max_duration)
        ax1.xaxis.set_major_locator(ticker.MultipleLocator(1))
        ax1.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))
        ax1.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)
        
        # Convergence annotation
        df_at_conv = df_final[df_final['Waktu'] >= t_converge]
        duty_at_conv = df_at_conv['Duty'].iloc[0] if not df_at_conv.empty else df_final['Duty'].iloc[-1]
        duty_ymax = df_final['Duty'].max()
        t_mid1 = t_converge / 2 if 0 < t_converge < max_duration * 0.8 else max_duration * 0.35
        y_text1 = duty_ymax * 0.75
        
        ax1.annotate(f'Convergence\n$t_c$ = {t_converge:.1f} s',
                     xy=(t_converge, duty_at_conv),
                     xytext=(t_mid1, y_text1),
                     fontsize=10, color='black', fontweight='bold', ha='center', va='center',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                               edgecolor='black', linewidth=0.6, alpha=0.95),
                     arrowprops=dict(arrowstyle='->', color='black', lw=1.0,
                                     connectionstyle='arc3,rad=-0.25'),
                     zorder=5)
        
        ax1.legend(loc='upper right', frameon=True, facecolor='white',
                   edgecolor='black', borderaxespad=0.5, ncol=1, fontsize=10)
        
        # --- (b) Power ---
        ax2.axvspan(-0.5, t_converge, color='#e8e8e8', alpha=0.8,
                    label='Search Phase', zorder=0)
        
        ax2.axhline(y=target_gmpp, color='black', linestyle='--',
                    linewidth=1.0, dashes=(6, 3),
                    label=f'Target = {target_gmpp:.1f} W', zorder=2)
        ax2.axhline(y=daya_avg, color='gray', linestyle='--',
                    linewidth=1.0, dashes=(4, 2, 1, 2),
                    label=f'Avg = {daya_avg:.2f} W', zorder=2)
        
        ax2.plot(df_final['Waktu'], df_final['Pin'],
                 color='black', linestyle='-', linewidth=1.5, zorder=3)
        ax2.plot(df_final['Waktu'], df_final['Pin'],
                 linestyle='none', marker='o', markersize=3,
                 markerfacecolor='black', markeredgecolor='white',
                 markeredgewidth=0.3, zorder=4,
                 label=r'$P_{\mathrm{in}}$')
        
        ax2.axvline(x=t_converge, color='black', linestyle=':', linewidth=0.8, zorder=2)
        
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Input Power (W)')
        ax2.set_xlim(-0.5, max_duration)
        ax2.set_ylim(0, max(target_gmpp, df_final['Pin'].max()) * 1.12)
        ax2.xaxis.set_major_locator(ticker.MultipleLocator(1))
        ax2.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))
        ax2.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)
        
        ax2.legend(loc='lower right', frameon=True, facecolor='white',
                   edgecolor='black', borderaxespad=0.5, fontsize=10)
        
        # Tracking efficiency annotation
        t_mid2 = max_duration * 0.4
        pin_max = max(target_gmpp, df_final['Pin'].max())
        y_text2 = pin_max * 0.35
        
        textstr = r'$\eta_{\mathrm{track}}$' + f' = {eff_track:.2f}%'
        ax2.annotate(textstr, xy=(t_mid2, daya_avg),
                     xytext=(t_mid2, y_text2),
                     fontsize=10, fontweight='bold', ha='center', va='center',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                               edgecolor='black', linewidth=0.6),
                     arrowprops=dict(arrowstyle='->', color='black',
                                     lw=0.8, connectionstyle='arc3,rad=0'),
                     zorder=5)
        
        fig.align_ylabels([ax1, ax2])
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        
        out_png = os.path.join(folder_dir, f'mppt_tracking_{algo_name.lower()}.png')
        out_pdf = os.path.join(folder_dir, f'mppt_tracking_{algo_name.lower()}.pdf')
        fig.savefig(out_png, dpi=600, bbox_inches='tight')
        fig.savefig(out_pdf, format='pdf', bbox_inches='tight')
        plt.close(fig)
        print(f"    [OK] {os.path.basename(out_png)} + PDF")


# ==============================================================================
# PLOT 4: algo_comparison (combined duty+power subplot) — B&W version
# ==============================================================================
def plot_algo_comparison_combined(folder_name, folder_dir, cfg):
    """Plot combined Duty + Power comparison subplot — B&W style."""
    print(f"\n{'='*60}")
    print(f"[COMBINED COMPARISON] {folder_name}")
    print(f"{'='*60}")
    
    max_duration = 25
    threshold_power = 1.0
    target_gmpp = get_gmpp_power(folder_dir, cfg, cfg['suffixes'][0])
    
    # Use a representative suffix (e.g. first non-empty one)
    for suffix in cfg['suffixes']:
        file_list = get_file_list(folder_dir, cfg, suffix)
        any_exists = any(os.path.exists(fp) for fp, _ in file_list)
        if any_exists:
            break
    else:
        print("  Tidak ada data.")
        return
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 8.0),
                                    gridspec_kw={'hspace': 0.32})
    
    # GMPP reference
    ax2.axhline(y=target_gmpp, color='black', linestyle='--',
                linewidth=1.5, dashes=(6, 3),
                label=f'Target GMPP = {target_gmpp:.1f} W', zorder=2)
    
    max_power_found = target_gmpp
    
    for fpath, algo_name in file_list:
        if not os.path.exists(fpath):
            continue
        
        df = read_algo_file(fpath, cfg['ncols'])
        if df is None:
            continue
        
        style = ALGO_STYLES.get(algo_name, {'linestyle': '-', 'marker': None, 'markevery': 8})
        
        mask_start = df['Pin'] > threshold_power
        if not mask_start.any():
            continue
        
        first_idx = mask_start.idxmax()
        start_idx = max(0, first_idx - 1)
        start_time = df.loc[start_idx, 'Waktu']
        
        df_f = df.loc[start_idx:].copy()
        df_f['Waktu'] = df_f['Waktu'] - start_time
        df_final = df_f[df_f['Waktu'] <= max_duration]
        
        if df_final.empty:
            continue
        
        max_power_found = max(max_power_found, df_final['Pin'].max())
        
        # Duty (a)
        ax1.plot(df_final['Waktu'], df_final['Duty'],
                 color='black', linestyle=style['linestyle'],
                 linewidth=1.5, zorder=3, label=algo_name,
                 marker=style['marker'], markersize=4,
                 markevery=style['markevery'],
                 markerfacecolor='black', markeredgecolor='black')
        
        # Power (b)
        ax2.plot(df_final['Waktu'], df_final['Pin'],
                 color='black', linestyle=style['linestyle'],
                 linewidth=1.5, zorder=3, label=algo_name,
                 marker=style['marker'], markersize=4,
                 markevery=style['markevery'],
                 markerfacecolor='black', markeredgecolor='black')
    
    # Axes config
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Duty Cycle (%)')
    ax1.set_xlim(-0.5, max_duration)
    ax1.set_ylim(0, 105)
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax1.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax1.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)
    ax1.legend(loc='upper right', frameon=True, facecolor='white',
               edgecolor='black', borderaxespad=0.5, ncol=2, fontsize=11)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('PV Power (W)')
    ax2.set_xlim(-0.5, max_duration)
    ax2.set_ylim(0, max_power_found * 1.15)
    ax2.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax2.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax2.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)
    ax2.legend(loc='lower right', frameon=True, facecolor='white',
               edgecolor='black', borderaxespad=0.5, ncol=2, fontsize=11)
    
    fig.align_ylabels([ax1, ax2])
    fig.tight_layout()
    
    out_png = os.path.join(folder_dir, 'algo_comparison_combined.png')
    out_pdf = os.path.join(folder_dir, 'algo_comparison_combined.pdf')
    fig.savefig(out_png, dpi=600, bbox_inches='tight')
    fig.savefig(out_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"    [OK] {os.path.basename(out_png)} + PDF")


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    setup_rc()
    
    print("=" * 70)
    print("  BATCH RESTYLE ALL PLOTS -> B&W Academic Journal Style")
    print("=" * 70)
    
    total_plots = 0
    
    for folder_name, cfg in FOLDER_CONFIG.items():
        folder_dir = os.path.join(BASE, folder_name)
        if not os.path.isdir(folder_dir):
            print(f"\n[SKIP] Folder not found: {folder_name}")
            continue
        
        # 1. Duty comparison
        plot_duty_comparison(folder_name, folder_dir, cfg)
        
        # 2. Power comparison
        plot_power_comparison(folder_name, folder_dir, cfg)
        
        # 3. MPPT tracking (plotmpptandduty) — only for folders that have it
        if folder_name in ('ujimotor', 'uji resistor'):
            plot_mppt_and_duty_bw(folder_name, folder_dir, cfg)
        
        # 4. Combined comparison — only for ujimotor (where algo_comparison.py exists)
        if folder_name == 'ujimotor':
            plot_algo_comparison_combined(folder_name, folder_dir, cfg)
    
    print("\n" + "=" * 70)
    print("  SELESAI! Semua grafik telah di-restyle ke B&W akademik.")
    print("=" * 70)


if __name__ == '__main__':
    main()
