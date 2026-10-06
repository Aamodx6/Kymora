# Kymora papers

The canonical paper is the JOSS draft **`paper.md`** (with `paper.bib`):
every performance figure in it traces to a committed artifact via
`../CLAIMS.md`.

## Directory Layout

```
paper/
├── paper.md                 # Canonical JOSS paper (Kymora, sourced numbers)
├── paper.bib                # JOSS BibTeX reference file
├── figures/                 # PNG figures (mirrored in landing/public/figures/)
└── legacy/                  # Superseded IEEE draft — stale, provenance only
    ├── README.md            # Why legacy/ exists (read this first)
    ├── main.tex             # Old IEEEtran draft (Tsxtract name, v0.3.0 numbers)
    ├── references.bib       # Legacy BibTeX bibliography
    ├── generate_figures.py  # Legacy figure generator (hardcodes old numbers)
    ├── architecture.pdf
    ├── throughput.pdf
    ├── scaling.pdf
    ├── memory.pdf
    └── speedup.pdf
```

See `legacy/README.md` for rebuild instructions of the legacy draft.
