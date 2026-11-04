import os, glob, re

files = glob.glob('docs/project-docs/*.md')
files = [f for f in files if not os.path.basename(f).startswith('_')]

total_replaced = 0
for fp in files:
    with open(fp, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if line.startswith('#'):
            # Replace & in headings with 'and'
            new_line = re.sub(r'\s+&\s+', ' and ', line)
            new_line = re.sub(r'&amp;', 'and', new_line)
            if new_line != line:
                total_replaced += 1
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    with open(fp, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

print(f"Replaced {total_replaced} ampersands in headings across {len(files)} files!")
