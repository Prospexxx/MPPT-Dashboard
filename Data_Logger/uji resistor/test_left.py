import subprocess
import os

with open("c:/Users/PC/Documents/Tugas Akhir/program ta/Dashboard MPPT/Data_Logger/plotmpptandduty.py", "r") as f:
    code = f.read()

# Make it headless
code_mod = "import matplotlib\nmatplotlib.use('Agg')\n" + code

# Change ax1 legend to upper left
code_mod = code_mod.replace("leg1 = ax1.legend(loc='best'", "leg1 = ax1.legend(loc='upper left'")
# Change ax2 legend to lower left
code_mod = code_mod.replace("leg2 = ax2.legend(loc='best'", "leg2 = ax2.legend(loc='lower left'")

# Rewrite ax1 annotation logic
old_ax1_anno = """    # Adaptive placement for ax1 annotation
    duty_ymax = df_final['Duty'].max()
    t_mid1 = max_duration * 0.35
    if t_converge > 0 and t_converge < max_duration * 0.8:
        t_mid1 = t_converge / 2
        
    df_before_mid1 = df_final[df_final['Waktu'] <= t_mid1]
    duty_at_mid = df_before_mid1['Duty'].iloc[-1] if not df_before_mid1.empty else 0
    
    y_text1 = duty_ymax * 0.75 if duty_at_mid < duty_ymax * 0.5 else duty_ymax * 0.25

    ax1.annotate(f'Convergence\\n$t_c$ = {t_converge:.1f} s',
                 xy=(t_converge, y_text1),
                 xytext=(t_mid1, y_text1),
                 fontsize=9.5, color='#333333', fontweight='bold', ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor='#888888', linewidth=0.6, alpha=0.95),
                 arrowprops=dict(arrowstyle='->', color='#666666', lw=0.8,
                                 connectionstyle='arc3,rad=0'),
                 zorder=5)"""

new_ax1_anno = """    # Adaptive placement for ax1 annotation (right side)
    duty_ymax = df_final['Duty'].max()
    
    # Place tag in the steady state region (right side) if there's enough space, else left side
    t_text1 = t_converge + (max_duration - t_converge) / 2
    if max_duration - t_converge < 1.5:
        t_text1 = t_converge / 2
        
    df_at_text1 = df_final[df_final['Waktu'] <= t_text1]
    duty_at_text1 = df_at_text1['Duty'].iloc[-1] if not df_at_text1.empty else 0
    
    y_text1 = duty_ymax * 0.8 if duty_at_text1 < duty_ymax * 0.5 else duty_ymax * 0.2

    ax1.annotate(f'Convergence\\n$t_c$ = {t_converge:.1f} s',
                 xy=(t_converge, y_text1),
                 xytext=(t_text1, y_text1),
                 fontsize=9.5, color='#333333', fontweight='bold', ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor='#888888', linewidth=0.6, alpha=0.95),
                 arrowprops=dict(arrowstyle='->', color='#666666', lw=0.8,
                                 connectionstyle='arc3,rad=0'),
                 zorder=5)"""

code_mod = code_mod.replace(old_ax1_anno, new_ax1_anno)

# Rewrite ax2 annotation logic
old_ax2_anno = """    # Tracking efficiency annotation — adaptive placement
    t_mid2 = max_duration * 0.4
    df_before_mid2 = df_final[df_final['Waktu'] <= t_mid2]
    pin_at_mid = df_before_mid2['Pin'].iloc[-1] if not df_before_mid2.empty else 0
    
    pin_max = max(target_gmpp_power, df_final['Pin'].max())
    y_text2 = pin_max * 0.75 if pin_at_mid < pin_max * 0.5 else pin_max * 0.25
    
    if abs(y_text2 - daya_mppt_avg) < pin_max * 0.15:
        y_text2 = pin_max * 0.2 if daya_mppt_avg > pin_max * 0.5 else pin_max * 0.8

    textstr = r'$\\eta_{\\mathrm{track}}$' + f' = {efisiensi_tracking:.2f}%'
    ax2.annotate(textstr, xy=(t_mid2, daya_mppt_avg),
                 xytext=(t_mid2, y_text2),
                 fontsize=9.5, fontweight='bold', ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffde8',
                           edgecolor='#999999', linewidth=0.6),
                 arrowprops=dict(arrowstyle='->', color='#666666',
                                 lw=0.8, connectionstyle='arc3,rad=0'),
                 zorder=5)"""

new_ax2_anno = """    # Tracking efficiency annotation — adaptive placement (right side)
    t_text2 = max_duration * 0.85
    df_at_text2 = df_final[df_final['Waktu'] <= t_text2]
    pin_at_text2 = df_at_text2['Pin'].iloc[-1] if not df_at_text2.empty else 0
    
    pin_max = max(target_gmpp_power, df_final['Pin'].max())
    y_text2 = pin_max * 0.8 if pin_at_text2 < pin_max * 0.5 else pin_max * 0.2
    
    if abs(y_text2 - daya_mppt_avg) < pin_max * 0.15:
        y_text2 = pin_max * 0.15 if daya_mppt_avg > pin_max * 0.5 else pin_max * 0.85

    textstr = r'$\\eta_{\\mathrm{track}}$' + f' = {efisiensi_tracking:.2f}%'
    ax2.annotate(textstr, xy=(t_text2, daya_mppt_avg),
                 xytext=(t_text2, y_text2),
                 fontsize=9.5, fontweight='bold', ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffde8',
                           edgecolor='#999999', linewidth=0.6),
                 arrowprops=dict(arrowstyle='->', color='#666666',
                                 lw=0.8, connectionstyle='arc3,rad=0'),
                 zorder=5)"""

code_mod = code_mod.replace(old_ax2_anno, new_ax2_anno)

code_mod = code_mod.replace("plt.show()", "plt.savefig('c:/Users/PC/Documents/Tugas Akhir/program ta/Dashboard MPPT/Data_Logger/mppt_test_left.png', dpi=150)")

temp_path = "c:/Users/PC/Documents/Tugas Akhir/program ta/Dashboard MPPT/Data_Logger/plot_temp.py"
with open(temp_path, "w") as f:
    f.write(code_mod)

print("Running test...")
subprocess.run(["C:/Users/PC/AppData/Local/Programs/Python/Python312/python.exe", temp_path])
print("Done")
