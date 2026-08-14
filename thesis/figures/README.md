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

## Generated Explanatory Figures

The explanatory figures below are original repository artifacts. They are
drawn as standalone TikZ documents with the shared style file
`thesis/figures/source/figure_style.tex`, compiled with LuaLaTeX, and retained
as vector PDFs. The shared style SHA-256 is:

```text
933b2af4110bc1898726b8b9016adc24dc635b77077853dcab016ff91fdee823
```

### Jordan sorting problem

- Thesis figure: `thesis/figures/jordan_sorting_problem.pdf`
- TikZ source: `thesis/figures/source/jordan_sorting_problem.tex`
- Source SHA-256:
  `eb782ed3bec6ebf5388ab07c838088b10d3226771fbbef1ba0d4244858997153`
- Generated PDF SHA-256:
  `3cc1d95222f09940ef9516268a45f37276ed8c5e8e986c733c3ad8a1eba09f09`

### Running reconstruction example

- Thesis figure: `thesis/figures/running_example_reconstruction.pdf`
- TikZ source: `thesis/figures/source/running_example_reconstruction.tex`
- Source SHA-256:
  `2e045ab4fc74fae77d444c656f93da5876b71dfd655d6ed7c3dc9f4759fef5e1`
- Generated PDF SHA-256:
  `91827eafc183ac6b7e750103613e8ba6308f83d5702cb183a4c93de827a79e72`
- Example provenance: the sequence $(2,3,1,7,6,4,5)$ is oracle-valid. Its
  checked diagnostic records an increasing iteration at $i=4$, a performed
  left-side split, transfer of $P_2$ to $P_4$, and insertion after output
  anchor $z_2$.

### Formal experiment pipeline

- Thesis figure: `thesis/figures/formal_experiment_pipeline.pdf`
- TikZ source: `thesis/figures/source/formal_experiment_pipeline.tex`
- Source SHA-256:
  `3316dd1ca055a439a5fa9991f042b5ed0663c1d3e61ce8cd091afcd8de4280db`
- Generated PDF SHA-256:
  `7083ace32989942aa633f97f9f4c002ed1eb3139811de9b627203432c0510e06`

### Pair families and sibling-list ownership

- Thesis figure: `thesis/figures/family_sibling_structure.pdf`
- TikZ source: `thesis/figures/source/family_sibling_structure.tex`
- Source SHA-256:
  `3acf769706606c13c4842819ac2cebcc85a5c971eee38e7cfcffb46240786d93`
- Generated PDF SHA-256:
  `6160c56c3f51eb6ff2348427b06024e661543400b1be60a0529fc3ac79d1f752`
- Example provenance: the displayed final family/list layout and the $i=4$
  transfer are derived from the same checked sequence used by the running
  reconstruction example.

### Step 3(c) anchor and odd-index z1 anomaly

- Thesis figure: `thesis/figures/step3c_anchor_z1_anomaly.pdf`
- TikZ source: `thesis/figures/source/step3c_anchor_z1_anomaly.tex`
- Source SHA-256:
  `b00432a7f457046b1ad6b856004a120cfef012f1e100295dfea28e1a26d4873e`
- Generated PDF SHA-256:
  `f5d8522b2d7a5e440eccde5adb31cf7d3009a499de59fe1452100f852bb6c268`
- Example provenance: for the oracle-valid prefix $(1,2,3,4,6,7,0)$, the
  checked implementation records base anchor $z_2$, output anchor $z_1$, and
  `adjusted_for_z1=true` at decreasing iteration $i=7$.
