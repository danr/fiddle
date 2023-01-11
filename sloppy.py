
def goto_file_sloppy(fragment: str):
    import re
    m = re.search(r'([^\s:]+):?(\d*)', fragment)
    filename, line_str = m.groups()
    if line_str.isdigit():
        line = int(line_str)
    else:
        line = 1
    return f'edit {filename} {line}'

print(
    goto_file_sloppy(' viable/prov.py:412: babab'),
    goto_file_sloppy(' viable/prov.py:: babab'),
    goto_file_sloppy(' viable/prov.py babab'),
    sep='\n',
)
