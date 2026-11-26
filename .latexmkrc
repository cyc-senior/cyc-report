# Build with XeLaTeX + Biber (works from terminal: `latexmk report.tex`, and from VS Code)
$pdf_mode = 5;          # 5 = xelatex
$bibtex_use = 2;        # run biber/bibtex when needed, clean .bbl too
@default_files = ('report.tex');
