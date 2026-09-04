# Tsxtract LaTeX Research Paper

This directory contains the complete, publication-quality LaTeX research paper for **Tsxtract**, formatted for submission to IEEE conferences or journals (using the `IEEEtran` document class).

---

## Directory Layout

```
paper/
├── main.tex                 # Main compilable LaTeX research paper (IEEEtran)
├── references.bib           # Complete BibTeX bibliography with real citations
├── generate_figures.py      # Python script to regenerate all publication-quality vector figures
├── figures/                 # Pre-generated vector PDF figures
│   ├── architecture.pdf     # System pipeline & FFI architecture diagram
│   ├── throughput.pdf       # Batch throughput comparison (series/sec, log scale)
│   ├── scaling.pdf          # Scaling across series count (N = 10 to 100,000)
│   ├── memory.pdf           # Memory footprint: zero-copy vs defensive copies
│   └── speedup.pdf          # Multi-core Rayon parallel speedup & efficiency
├── paper.md                 # JOSS / arXiv Markdown version of the paper
├── paper.bib                # JOSS BibTeX reference file
└── README.md                # Compilation instructions and guide
```

---

## Compilation Instructions

### Using `latexmk` (Recommended)
```bash
latexmk -pdf main.tex
```

### Using `pdflatex` and `bibtex` manually
```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### Regenerating Vector Figures
```bash
python generate_figures.py
```
This will regenerate all vector PDF figures in `paper/figures/` using publication-standard serif typography and matplotlib vector rendering.
