# AGENTS.md: CYC report

LaTeX source of the senior project report **CYC: AI-Driven Platform for UX/UI Development Life Cycle**
(Computer Engineering, KMUTT). The text is in Thai, built with XeLaTeX + Biber on the `cpe-thesis-th` class.
One codebase produces four reports:

| Entry file          | Report                                | Layout reference                     | Status |
|---------------------|---------------------------------------|--------------------------------------|--------|
| `proposal.tex`      | First report (proposal), submitted    | class default, 16pt                  | **frozen**: text in `reports/proposal/`, never edit |
| `progress-sem1.tex` | รายงานความก้าวหน้า ภาคการศึกษาที่ 1   | `Progress_Sem1_THAI_Example1.pdf`    | current report |
| `progress-sem2.tex` | รายงานความก้าวหน้า ภาคการศึกษาที่ 2   | none yet, so it copies sem 1         | provisional |
| `final.tex`         | ปริญญานิพนธ์ฉบับสมบูรณ์               | none yet, so it copies sem 1         | provisional |

The project being reported on is the **cyc-monorepo** (`github.com/cyc-senior/cyc-monorepo`, often checked out
next to this repo, e.g. `../cyc-monorepo`). It is a Turborepo with `apps/frontend` (Next.js) and `apps/backend`
(NestJS, Prisma, BullMQ, CPE AI Gateway). Facts written in the report (features, counts, models, routes, limits)
must come from that code or its git history, not from guesses. Write down the commit/branch you used whenever you state a count.

## Layout

```
<report>.tex            spine: style + front matter + ordered \input list of content files. No prose here.
config/preamble.tex     packages, fonts, size macros (shared). Body size comes from \reportbodysize.
config/report-info.tex  title, members, advisors, committee, keywords (shared by the living reports)
config/styles/*.tex     layout per report kind: progress.tex (measured from the sem 1 example), final.tex
config/bibliography.tex reference list (bib/cyc.bib)
frontmatter/*.tex       page layouts: cover, signature, abstract, lists; progress.tex/final.tex give the page order
content/                ALL prose: 1 file = 1 \section (or a chapter intro paragraph)
  abstract/{en,th}.tex, glossary.tex, acknowledgement.tex, appendix.tex
  ch1/ ch2/ ch3/        shared by sem1, sem2 and final
  ch3/development-sem1.tex, development-sem2.tex   work per semester (final includes both)
  ch4/sem1/ ch4/sem2/ ch4/final/   chapter 4 differs per report
  ch5/                  final only
reports/proposal/       frozen proposal text and report-info
figures/<chapter>/      images; reference them from the repo root: figures/ch3-methodology/x.png
tools/                  pdf_outline.py (measure an example PDF), gantt_to_latex.py, er_diagram.py
```

`\chapter{...}` lines live in the spine, not in content files, so a report can rename or reorder chapters.
Content files start at `\section` (chapter intros are `intro.tex`, plain paragraphs).

## Rules

- **Never commit PDFs at the repo root.** That covers example reports and build output (`/*.pdf` is in `.gitignore`).
  Only `figures/**.pdf` (diagrams) are tracked.
- Never edit `reports/proposal/` or `proposal.tex` content. It is the submitted version.
- Text that differs by report belongs in its own content file (e.g. `ch4/sem2/...`), and the spine picks it.
  Use `\termphrase` (defined in each spine, e.g. "ในภาคการศึกษาที่ 1") only for short phrases in shared intros.
  Avoid `\if` switches in content.
- Layout changes go in `config/styles/<kind>.tex`. Do not touch `cpe-thesis-th.cls` or `config/preamble.tex` for one report.
- Every content file starts with `% !TeX root = <relative path to the spine>` (shared files point at the
  current report, `progress-sem1.tex`) and a one-line `%` comment naming the section.
- Wrap Thai paragraphs in `\thaijustify{...}`. Missing content is `\todo{what is missing}` (red in the PDF).
  CI counts them. Before submission, `grep -rn '\\todo' content frontmatter` must be empty for that report's files.
- Captions: `\caption{...}` + `\label{fig:...}` / `\label{tab:...}`; sections that are referenced get `\label{sec:...}`.
  Labels must be unique across all files a spine includes.
- Long tables: `xltabular` inside `\begingroup\small ... \endgroup` (see `content/ch4/sem1/status-vs-plan.tex`).
- Thai style: formal report register; technical terms stay in English (user story, variant, prompt).
  Match the voice of the existing chapters.
- Citations: add to `bib/cyc.bib`, cite with `~\cite{key}`.

## Build

```
latexmk                    # current report (see @default_files in .latexmkrc)
latexmk final.tex          # one report
```
Requires TeX Live (xelatex, biber, latexmk); fonts are loaded from `fonts/`. There may be no TeX on the
machine. In that case use CI: **GitHub Actions → "Build report PDF" → Run workflow → pick a report** (or `all`).
Push/PR builds the current report plus any report whose spine changed. PDFs come out as run artifacts.

When the semester changes, update the "current report" in **both** `.latexmkrc` (`@default_files`) and
`.github/workflows/build.yml` (`CURRENT_REPORT`), and the `% !TeX root` lines of shared files
(`content/ch1..3`, `config/`, `frontmatter/`).

## Playbook: new report type from an example PDF

Use this when the user hands over an example PDF (e.g. a sem 2 or final report from another group) and says
"make our report match this". Example PDFs are layout/outline references only: never copy their text.

1. Put the PDF at the repo root (git ignores it) and measure it:
   `python tools/pdf_outline.py <example.pdf>` (needs `pip install pymupdf`).
   It prints the bookmark outline, front-matter page order, font sizes (body/chapter/section/caption),
   margins, page-number position and caption format. Thai text may come out garbled. The outline is reliable.
2. **Layout:** compare the numbers with `config/styles/progress.tex`, which holds the sem 1 measurements:
   body 14.3pt, chapter 19.1pt bold, section 16.7pt bold, margins L4/R2/T3cm, page number bottom centre,
   captions "รูปที่ 3.1: ..." regular weight. Put only the differences into the report's style file
   (`config/styles/final.tex`, or create `config/styles/progress-sem2.tex` that `\input`s progress.tex then overrides).
   Body size goes in the spine's `\reportbodysize`.
3. **Front matter:** list the pages before chapter 1 in order (cover, signature, abstract EN/TH,
   acknowledgement, ToC, lists, glossary...). Edit `frontmatter/<kind>.tex` to match. Make a new layout file in
   `frontmatter/` only when a page looks different from the existing ones.
4. **Outline:** map every chapter/section of the example to our files. Write the table into your reply:
   example heading → existing content file / new file / not applicable to our project.
   Reuse shared files when the heading already exists. Create new content files for the rest, with
   `\todo{...}` saying what goes there, and fill whatever can be filled from the monorepo now.
   Domain-specific sections of the example (e.g. "การพัฒนา NAS") map to our own equivalents
   (e.g. "การพัฒนา AI pipeline"), not to literal copies.
5. Update the spine (`progress-sem2.tex` / `final.tex`): style, `\termphrase`, front matter, `\chapter` titles
   exactly as in the example, `\input` order. Remove the "PROVISIONAL" notes once the report matches.
6. Update the table in this file (layout reference + status) and the README tree if files were added.
7. Build (locally or via the workflow) and compare page by page with the example: ToC look, chapter heading,
   caption style, page numbers.

## Playbook: start the next semester

1. Switch the current report (see Build).
2. Add the semester's work as new content files (e.g. `ch3/development-sem2.tex`, `ch4/sem2/*`). Do not
   rewrite last semester's files to say something else. The final report includes both.
3. Refresh shared sections that went stale (ch1 deliverables, ch3 design diagrams, Gantt via
   `tools/gantt_to_latex.py`), using the monorepo as the source of truth.
