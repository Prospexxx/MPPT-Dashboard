import os

files_to_edit = ['algo_comparison_power.py', 'algo_comparison_duty.py']

old_code = '''        # Check if all files exist
        all_exist = True
        for name, fname in files.items():
            if not os.path.exists(fname):
                print(f"[WARNING] File not found: {fname}. Skipping...")
                all_exist = False
                
        if not all_exist:
            print(f"Tidak ada data valid untuk diplot pada Run {i}. Melewati...\\n")
            continue'''

new_code = '''        # Check if all files exist
        valid_files = {}
        for name, fname in files.items():
            if os.path.exists(fname):
                valid_files[name] = fname
            else:
                print(f"[WARNING] File not found: {fname}. Skipping this algorithm...")
                
        if not valid_files:
            print(f"Tidak ada data valid untuk diplot pada Run {i}. Melewati...\\n")
            continue'''

for s in files_to_edit:
    with open(s, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = content.replace(old_code, new_code)
    content = content.replace('for name, fname in files.items():\n            df = pd.read_csv', 'for name, fname in valid_files.items():\n            df = pd.read_csv')
    
    with open(s, 'w', encoding='utf-8') as f:
        f.write(content)

print('Updated plotting scripts to allow missing algorithms.')
