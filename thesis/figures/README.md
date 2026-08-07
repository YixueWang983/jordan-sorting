# Thesis Figures

This directory is reserved for thesis-facing copies of validated figures.

Source analysis files remain under `docs/analysis/`, and immutable experiment
evidence remains under `results/runs/`. Do not modify either source in order to
fit the LaTeX document. Record the source path and SHA-256 whenever a figure is
copied or converted for the thesis.

## Week 12 Results Figures

### Median runtime by size

- Thesis figure: `thesis/figures/week12_runtime_by_size.pdf`
- Source: `docs/analysis/week12_runtime_by_size.svg`
- Source SHA-256:
  `871ddaec0cf1f13189e2c249874bd68d8d30a29989bbd9905b24dc86df7f5dd7`
- Conversion: the source SVG was printed to vector PDF with headless Google
  Chrome, then cropped with `pdfcrop --margins 2`; the source was not modified.
- Generated PDF SHA-256:
  `4b29bd6c391c4591564cd761b8a0a836609a93e6d9c87746432eeee78f5ce432`

### Runtime ratios by size

- Thesis figure: `thesis/figures/week12_runtime_ratio_by_size.pdf`
- Source: `docs/analysis/week12_runtime_ratio_by_size.svg`
- Source SHA-256:
  `ab5db0b407c6feb86f59f022ff59cd52f0c45ae6c65ac157ea965f9eb81d66b2`
- Conversion: the source SVG was printed to vector PDF with headless Google
  Chrome, then cropped with `pdfcrop --margins 2`; the source was not modified.
- Generated PDF SHA-256:
  `31c0e63010b8c8b83cafbe8b1fde6ad9744954d7eb26580bba4f8b3b312beacd`
