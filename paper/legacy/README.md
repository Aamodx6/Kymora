# Legacy IEEE draft (stale, superseded)

This directory holds the superseded IEEE-conference draft of the paper
(`main.tex`, written under the old `Tsxtract` name with v0.3.0-era numbers,
`benches/` paths, and a 98-test suite count) plus its build inputs
(`references.bib`, `generate_figures.py`) and prebuilt figure PDFs.

**Do not update these files.** The canonical paper is now the JOSS draft at
`../paper.md`, whose performance figures trace to committed artifacts via
`../../CLAIMS.md`. This draft is kept for provenance only.

To rebuild the legacy PDFs (requires a LaTeX toolchain; numbers will still
be stale):

```bash
cd paper/legacy
python generate_figures.py   # regenerates the figure PDFs below
latexmk -pdf main.tex
```
