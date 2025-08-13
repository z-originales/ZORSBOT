import re
import os

pyrefly = os.environ.get('PYREFLY_RESULT', '')
ruff = os.environ.get('RUFF_RESULT', '')

pyrefly_errors = len(re.findall(r'ERROR', pyrefly))
ruff_errors = len(re.findall(r': ::error', ruff))

with open('report.md', 'w') as f:
    f.write("# Résumé du code check\n\n")
    f.write(f"- Erreurs pyrefly : {pyrefly_errors}\n")
    f.write(f"- Erreurs ruff : {ruff_errors}\n")