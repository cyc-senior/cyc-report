# Build with XeLaTeX + Biber.
#   latexmk                      -> builds the report we are working on now (first entry below)
#   latexmk final.tex            -> one report
#   latexmk proposal.tex progress-sem1.tex progress-sem2.tex final.tex   -> all of them
# Each report writes <name>.pdf at the repo root (ignored by git).
$pdf_mode = 5;          # 5 = xelatex
$bibtex_use = 2;        # run biber/bibtex when needed, clean .bbl too
@default_files = ('progress-sem1.tex');   # CURRENT report: change when the semester changes
