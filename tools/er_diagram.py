#!/usr/bin/env python3
"""Draw ER diagrams of the CYC database from the backend's Prisma schema, one per
group of tables, as PDF figures for chapter 3.

Usage:
    python3 tools/er_diagram.py <path/to/schema.prisma> figures/ch3-methodology/

Needs Graphviz (`dot`). Each table lists its primary key (PK), foreign keys (FK)
and its other columns (cut to MAX_FIELDS, the rest summarised as "+n more").
Edges point from the referencing table to the one it refers to and are marked
1 / N (or 1 / 0..1 when the foreign key is unique).
"""
import re, subprocess, sys, pathlib

MAX_FIELDS = 4
GROUPS = {
    "er-workspace-project": [
        "User", "Account", "RefreshToken", "UserAvatar", "Workspace", "WorkspaceAvatar",
        "WorkspaceInvitation", "WorkspaceMember", "Project", "ProjectMember", "DesignIntent",
        "UserPersona", "AuditLog"],
    "er-design-generation": [
        "Project", "UserPersona", "UserStory", "StoryGeneration", "DesignRound",
        "GenerationJob", "UIVariant"],
    "er-testing": [
        "DesignRound", "UIVariant", "TestSession", "SessionVariant", "SessionParticipant",
        "ConsentRecord", "TestTask", "TaskRun", "InteractionEvent", "Feedback"],
    "er-analysis-report": [
        "Project", "DesignRound", "TestSession", "Feedback", "FeedbackAnalysis", "FeedbackTheme",
        "ThemeFeedback", "DesignDecision", "RoundFeedbackLink", "RoundComment",
        "RoundAcknowledgement", "Report"],
}
#: Tables drawn only for context in a group (defined in another figure): shown grey, no columns.
CONTEXT = {"er-design-generation": {"Project", "UserPersona"},
           "er-testing": {"DesignRound", "UIVariant"},
           "er-analysis-report": {"Project", "DesignRound", "TestSession", "Feedback"}}
#: Layout direction per figure, chosen so the drawing fits the page it goes on.
RANKDIR = {"er-workspace-project": "LR", "er-design-generation": "TB",
           "er-testing": "TB", "er-analysis-report": "LR"}


def parse(path):
    text = open(path, encoding="utf-8").read()
    enums = set(re.findall(r"^enum (\w+)", text, re.M))
    models = {}
    for name, body in re.findall(r"^model (\w+) \{(.*?)^\}", text, re.S | re.M):
        cols, rels, uniques = [], [], set()
        composite = set()
        for u in re.findall(r"@@id\(\[([^\]]*)\]", body):
            composite |= {x.strip() for x in u.split(",")}
        for u in re.findall(r"@@unique\(\[([^\]]*)\]", body):
            fields = [x.strip() for x in u.split(",")]
            if len(fields) == 1:
                uniques.add(fields[0])
        for line in body.splitlines():
            line = line.split("//")[0].strip()
            if not line or line.startswith("@@"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            field, typ = parts[0], parts[1]
            base = typ.rstrip("?[]")
            if "@relation" in line and "fields:" in line:
                fks = re.search(r"fields:\s*\[([^\]]*)\]", line).group(1).split(",")
                rels.append((base, [f.strip() for f in fks], typ.endswith("?")))
                continue
            if typ.endswith("[]") or (base[0].isupper() and base not in enums and base not in
                                     {"String", "Int", "Float", "Boolean", "DateTime", "Json", "Decimal", "BigInt", "Bytes"}):
                continue  # back-relation fields
            if "@unique" in line:
                uniques.add(field)
            cols.append((field, base + ("?" if typ.endswith("?") else ""), "@id" in line or field in composite))
        models[name] = dict(cols=cols, rels=rels, uniques=uniques)
    return models


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def node(name, m, context):
    if context:
        return (f'"{name}" [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5" COLOR="#888888" BGCOLOR="#EEEEEE">'
                f'<TR><TD><FONT COLOR="#555555"><B>{name}</B></FONT></TD></TR></TABLE>>];')
    fk = {f for _, fs, _ in m["rels"] for f in fs}
    pk = [c for c in m["cols"] if c[2]]
    fks = [c for c in m["cols"] if c[0] in fk and not c[2]]
    rest = [c for c in m["cols"] if c[0] not in fk and not c[2]]
    shown = rest[:MAX_FIELDS]
    rows = [f'<TR><TD COLSPAN="3" BGCOLOR="#D9D9D9"><B>{name}</B></TD></TR>']
    for f, t, _ in pk:
        rows.append(f'<TR><TD ALIGN="LEFT"><B>{"PK, FK" if f in fk else "PK"}</B></TD><TD ALIGN="LEFT"><B>{f}</B></TD><TD ALIGN="LEFT">{esc(t)}</TD></TR>')
    for f, t, _ in fks:
        rows.append(f'<TR><TD ALIGN="LEFT">FK</TD><TD ALIGN="LEFT">{f}</TD><TD ALIGN="LEFT">{esc(t)}</TD></TR>')
    for f, t, _ in shown:
        rows.append(f'<TR><TD></TD><TD ALIGN="LEFT">{f}</TD><TD ALIGN="LEFT">{esc(t)}</TD></TR>')
    if len(rest) > len(shown):
        rows.append(f'<TR><TD></TD><TD ALIGN="LEFT" COLSPAN="2"><I>+{len(rest) - len(shown)} more</I></TD></TR>')
    return (f'"{name}" [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
            + "".join(rows) + "</TABLE>>];")


def draw(models, group, tables, outdir):
    ctx = CONTEXT.get(group, set())
    lines = ['digraph ER {', f'graph [rankdir={RANKDIR.get(group, "LR")}, nodesep=0.22, ranksep=0.45, fontname="TH Sarabun New", splines=true, overlap=false];',
             'node [shape=plain, fontname="TH Sarabun New", fontsize=18];',
             'edge [fontname="TH Sarabun New", fontsize=14, arrowhead=none, color="#444444"];']
    for t in tables:
        lines.append(node(t, models[t], t in ctx))
    seen = set()
    for t in tables:
        for target, fks, _ in models[t]["rels"]:
            if t in ctx and target in ctx:
                continue
            if target not in tables or (t, target, tuple(fks)) in seen:
                continue
            seen.add((t, target, tuple(fks)))
            one = len(fks) == 1 and fks[0] in models[t]["uniques"]
            lines.append(f'"{target}" -> "{t}" [taillabel="1", headlabel="{"0..1" if one else "N"}", labeldistance=1.6];')
    lines.append("}")
    dot = "\n".join(lines)
    out = pathlib.Path(outdir) / f"{group}.pdf"
    subprocess.run(["dot", "-Tpdf", "-o", str(out)], input=dot.encode(), check=True)
    print(out)


def main():
    schema, outdir = sys.argv[1], sys.argv[2]
    models = parse(schema)
    for group, tables in GROUPS.items():
        draw(models, group, tables, outdir)


if __name__ == "__main__":
    main()
