# find_hardcoded_ru.py
import re
import os

ui_files = [
    'ui/deploy_tab.py',
    'ui/branches_tab.py',
    'ui/settings_tab.py',
    'ui/about_tab.py',
    'ui/gitignore_tab.py',
    'ui/toolbar.py',
    'ui/menu.py',
    'ui/main_window.py'
]

ru_pattern = re.compile(r'["\']([А-Яа-яЁё\s\W]+)["\']')

for file_path in ui_files:
    if not os.path.exists(file_path):
        continue
    
    print(f"\n📄 {file_path}:")
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            # Пропускаем комментарии и строки с lang_mgr
            if line.strip().startswith('#') or 'lang_mgr' in line:
                continue
            
            matches = ru_pattern.findall(line)
            if matches:
                # Фильтруем короткие строки и технические
                for match in matches:
                    if len(match) > 3 and match not in ['Ctrl+O', 'Ctrl+Q', 'F5']:
                        print(f"  {i}: {line.strip()[:80]}")