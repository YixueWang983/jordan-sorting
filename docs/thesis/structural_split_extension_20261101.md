# Structural split extension integrated into the thesis

1 November 2026. The author asked to return to the missing split-workload
experiments. All eighteen existing balanced, skew and repeated constructions
were qualified and formally timed under the committed plan. The production
sorting implementation was not changed.

## Findings and evidence

- 18 inputs passed qualification on both backends; their primary traces have
  230 two-sided splits and 212 re-splits per backend.
- All 2,800 formal sample calls and 180 warm-up calls returned correct output.
- Tree/list ratios: median 2.987, range 2.376–3.222; tree slower on every input.
- Direct follow-up updates still affect only retained split outputs. Odd-length
  inputs are mirrored, coupling direction and parity.
- The new session recorded macOS 27.2 and 32% battery, compared with 26.6 and
  100% in the original formal archives. The datasets are reported separately.
- The experiment tools passed 42 relevant test methods before the campaign.
  Qualification, calibration and formal records passed independent archive
  reconstruction. Rebuilding from the copied archives reproduced all analysis
  files byte-for-byte before the results commit.
- All 13,256 original files in the seven checked archive trees are unchanged.

Producer: `bdfcdcf8f13da2a88151ae0524b388181ea7e5a6`. Full protocol, inputs,
raw data, analysis and reproduction commands:
`docs/validation/structural_split_formal_20261101/`.

## Manuscript changes

Section 5.2.1 describes the extension; section 6.6 and table 6.6 give all
eighteen results and their interpretation. The abstract, introduction,
implementation coverage, limitations, conclusions and Appendix B.1 now include
the extension. Combined execution accounting is 69,360 sample calls in 6,800
batches and 1,700 warm-up calls; no cross-campaign ratio is pooled.

The original fifteen-row diagnostic remains table 6.5. Appendix A and the
approved B.2 documentation are unchanged. B.3 only clarifies that the absence
of formal timing for the eighteen structural inputs was true at the time of
the earlier discussion, and points to their subsequent timing extension.
No new independent human proof review or personal contribution is asserted.

## Delivery check

`output/pdf/Wang_Thesis_Draft_2026-11-02.pdf` is the single updated deliverable,
78 pages. Author and cover date remain Yixue Wang and 2 November 2026.

SHA-256: `d662ef5d6e2950dce361c5b092911a343512c92e0b65de3bc725fce48ee7d33f`.

LuaLaTeX/latexmk compilation completed with no warnings, undefined references,
missing characters or overfull/underfull boxes in the final log. All eighteen
table rows match the independently reconstructed archive values. Fifteen
affected PDF pages were rendered and visually reviewed, including the cover,
abstract, methods, results, limitations, conclusion and Appendix B. The complete
new table and discussion fit on PDF page 52 (printed page 40).
