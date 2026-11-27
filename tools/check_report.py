"""Static check of a report spine, without TeX: follows \\input recursively and reports
missing files, unbalanced braces, duplicate \\label and \\ref/\\cref to unknown labels,
missing figures, and how many \\todo placeholders are left.

Usage: python tools/check_report.py progress-sem1.tex [final.tex ...]
Exit code 1 when an error (not a \\todo) is found.
"""
import os
import re
import sys

BS = "\\"
INPUT = re.compile(r"\\(?:input|include)\{([^}]+)\}")
LABEL = re.compile(r"\\label\{([^}]+)\}")
REF = re.compile(r"\\(?:ref|cref|Cref|autoref|pageref)\{([^}]+)\}")
GRAPHIC = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}#]+)\}")
TODO = re.compile(r"\\todo\{")


def strip_comments(text):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.split("\n"))


def check(spine):
    errors, todos, labels, refs, seen = [], [], {}, [], []

    def visit(path, depth=0):
        if not path.endswith(".tex"):
            path += ".tex"
        if not os.path.exists(path):
            errors.append(f"missing file: {path}")
            return
        seen.append(path)
        text = strip_comments(open(path, encoding="utf-8").read())
        flat = text.replace(BS + BS, "").replace(BS + "{", "").replace(BS + "}", "")
        if flat.count("{") != flat.count("}"):
            errors.append(f"unbalanced braces in {path}: {flat.count('{')} '{{' vs {flat.count('}')} '}}'")
        for m in LABEL.finditer(text):
            if m.group(1) in labels:
                errors.append(f"duplicate label {m.group(1)}: {labels[m.group(1)]} and {path}")
            labels[m.group(1)] = path
        refs.extend((r.strip(), path) for m in REF.finditer(text) for r in m.group(1).split(","))
        for m in GRAPHIC.finditer(text):
            g = m.group(1)
            if not any(os.path.exists(g + ext) for ext in ("", ".pdf", ".png", ".jpg")):
                errors.append(f"missing figure {g} in {path}")
        todos.extend(path for _ in TODO.finditer(text))
        for m in INPUT.finditer(text):
            visit(m.group(1), depth + 1)

    visit(spine)
    for r, path in refs:
        if r not in labels:
            errors.append(f"reference to unknown label {r} in {path}")
    print(f"{spine}: {len(seen)} files, {len(labels)} labels, {len(todos)} \\todo left")
    for e in errors:
        print("  ERROR", e)
    return not errors


if __name__ == "__main__":
    ok = all([check(s) for s in sys.argv[1:] or ["progress-sem1.tex"]])
    sys.exit(0 if ok else 1)
