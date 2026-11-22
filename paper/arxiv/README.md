# Kymora Preprint (arXiv / Tech Report Draft)

This directory contains the LaTeX preprint source for the Kymora technical paper.

## Files
- `main.tex`: Primary LaTeX manuscript
- `references.bib`: BibTeX bibliography

## Compilation Instructions

To compile the PDF locally with `pdflatex` and `bibtex`:

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Or using `latexmk`:

```bash
latexmk -pdf main.tex
```

## Release & Submission Policy

> [!CAUTION]
> In accordance with release protocols, **NO automated submission to arXiv, JOSS, or any preprint server** will be performed. Submissions are strictly gated behind explicit human instruction.
