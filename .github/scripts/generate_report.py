import re

with open('pyrefly_output.txt') as f:
    pyrefly = f.read()
with open('ruff_output.txt') as f:
    ruff = f.read()

pyrefly_errors = len(re.findall(r'FAILED', pyrefly))
ruff_errors = len(re.findall(r': error', ruff))

with open('report.md', 'w') as f:
    f.write("# Résumé du code check\n\n")
    f.write(f"- Erreurs pyrefly : {pyrefly_errors}\n")
    f.write(f"- Erreurs ruff : {ruff_errors}\n")