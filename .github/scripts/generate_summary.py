import argparse as arg
import pathlib
import json
from collections import Counter

def setup_parser():
    inparser = arg.ArgumentParser(description='Generate a summary from the code improver workflow json files.')
    subparser = inparser.add_subparsers(dest='command', required=True, help='Subcommand to choose the type of summary to generate.')
    pyrefly_cmd = subparser.add_parser('pyrefly', help='Generate a summary from the pyrefly json files.')
    ruff_cmd = subparser.add_parser('ruff', help='Generate a summary from the ruff json files.')

    for cmd in [pyrefly_cmd, ruff_cmd]:
        cmd.add_argument('INPUT' , type=pathlib.Path, nargs=1, help='Input file')
        cmd.add_argument('--output' , type=pathlib.Path, nargs=1, help='Output file')

    return inparser

def generate_pyrefly_summary(input_pyrefly_file: pathlib.Path, output_pyrefly_file: pathlib.Path | None = None) -> int:
    with open(input_pyrefly_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    errors = data.get('errors', [])
    total_errors = len(errors)
    files = {e['path'] for e in errors}

    if total_errors == 0:
        summary = [
            "# Rapport Pyrefly ✅",
            f"📄 Aucun problème détecté dans {len(files)} fichier(s)."
        ]
    else:
        error_types = dict(Counter(e['name'] for e in errors))
        summary = [
            "# Rapport Pyrefly ❌",
            f"\n📄 Fichiers concernés: {len(files)}",
            f"\n❌ Nombre total d’erreurs: {total_errors}",
            "## Types d’erreurs:",
        ]
        for name, count in error_types.items():
            summary.append(f"* 🧩 {name}: {count}")

    markdown = "\n".join(summary)
    if output_pyrefly_file:
        with open(output_pyrefly_file, 'w', encoding='utf-8') as out:
            out.write(markdown)
    else:
        print(markdown)

    return total_errors


def generate_ruff_summary(input_ruff_file: pathlib.Path, output_ruff_file: pathlib.Path | None = None) -> int:
    with open(input_ruff_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_errors = len(data)
    files = {e['filename'] for e in data}
    non_fixable = [e for e in data if e.get('fix') is None]
    unsafe_fixable = [e for e in data if e.get('fix') and e.get('unsafe')]
    fixable = [e for e in data if e.get('fix') is not None]
    error_types = dict(Counter(e['code'] for e in data if e.get('code')))

    if total_errors == 0:
        summary = [
            "# Rapport Ruff ✅",
            f"📄 Aucun problème détecté dans {len(files)} fichier(s)."
        ]
    else:
        summary = ["# Rapport Ruff ❌", f"\n📄 Fichiers concernés: {len(files)}",
                   f"\n❌ Nombre total d’erreurs: {total_errors}",
                   f"🔧 Erreurs réparables automatiquement: {len(fixable)}",
                   f"🚫 Erreurs non réparables: {len(non_fixable)}", "## Types d’erreurs:",
                   f"* 🔧 réparables automatiquement: {len(fixable)}", f"* ⚠️ unsafe fixable: {len(unsafe_fixable)}",
                   f"* 🚫 non fixable: {len(non_fixable)}",
                   "\n### Détails des erreurs:"]

        for code, count in error_types.items():
            summary.append(f"* 🧩 {code}: {count}")

    markdown = "\n".join(summary)
    if output_ruff_file:
        with open(output_ruff_file, 'w', encoding='utf-8') as out:
            out.write(markdown)
    else:
        print(markdown)

    return total_errors



if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()

    input_file = args.INPUT[0]
    output_file = args.output[0] if args.output else None

    # Vérification explicite du fichier d'entrée
    if not input_file.exists():
        print(f"Erreur: Le fichier d'entrée '{input_file}' n'a pas été trouvé.")
        exit(1)

    # Vérification explicite du dossier de sortie si output_file est fourni
    if output_file:
        output_dir = output_file.parent
        if not output_dir.exists():
            print(f"Erreur: Le dossier de sortie '{output_dir}' n'existe pas.")
            exit(-1)

    if args.command == 'pyrefly':
        exit(generate_pyrefly_summary(input_file, output_file))
    elif args.command == 'ruff':
        exit(generate_ruff_summary(input_file,  output_file))
