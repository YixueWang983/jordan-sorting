# Jordan Sorting

Implementation and experimental evaluation of the 1990 Simplified Jordan
Sorting algorithm. The project uses one Python sorting core with ordinary-list
and heterogeneous finger-tree backends.

## Current thesis and results

The current review draft is the **80-page unified-results thesis**, built on
2 November 2026:

- [Read the current PDF](output/pdf/Wang_Thesis_Refined_Results_2026-11-02.pdf)
- [LaTeX sources and build instructions](thesis/README.md)
- [Revision record and numerical sources](docs/thesis/unified_refinement_20261102.md)
- [Build and visual-review record](docs/thesis/unified_refinement_20261102/build_report.json)

The complete formal attempt measures 302 inputs from five predetermined sources.
The uninstrumented tree is faster on 44 inputs. The input-level tree/list ratio
has median 1.257 and range 0.590–1.518. These are descriptive results for the
selected inputs and one host, not a general performance guarantee.

The first attempt stopped after a power-check failure. An explicitly authorized
restart departed from the no-retry rule; the main results use only the complete
second attempt. Both attempts, the diagnosis and the restart decision remain
in the formal archive. The constructor benchmark and the 170-input stability
check are separate follow-ups.

Appendix A remains unchanged by the results revision. The requested Appendix B
content update is still deferred; the current experiment paths are listed in
the method chapter and the indexes below. This PDF is not ready for supervisor circulation until Appendix B is updated.

## Evidence

| Record | Location |
| --- | --- |
| Predetermined inputs and exclusions | [Input registry](docs/validation/input_suite_registry_20261101/README.md) |
| Measurement rules | [Protocol](docs/plan/uninstrumented_rerun_protocol_20261101.md) and [five-source addendum](docs/plan/uninstrumented_rerun_addendum_20261101.md) |
| Equivalence, qualification and calibration | [Preparation archive](docs/validation/unified_preflight_20261101/README.md) |
| Both formal attempts, restart, validation and analysis | [Formal archive](docs/validation/unified_formal_20261101/README.md) |
| Constructor benchmark and post hoc stability check | [Follow-up archive](docs/validation/unified_followup_20261101/README.md) |
| Older experiments and proof-to-source map | [Dated evidence index](docs/thesis/evidence_source_index_20261022.md) |

Archive paths and source identities are part of the evidence. Follow each
archive's reproduction notes; older records describe their producing version,
not the current project status.

## Repository layout

| Directory | Purpose |
| --- | --- |
| `src/` | Sorting core, backends, oracle and generators |
| `tests/` | Correctness and experiment-tool tests |
| `experiments/` | Qualification, measurement, validation and analysis tools |
| `thesis/` | Current LaTeX manuscript and figures |
| `output/` | [Current deliverable and older-file recovery](output/README.md) |
| `docs/validation/` | Preserved experimental and review evidence |
| `docs/` | [Documentation index](docs/README.md), plans and development records |
| `results/` | Earlier experiment records, with their original scope |
| `data/` | Saved examples and input data |
| `presentations/` | Historical progress presentation sources |

## Development

Run the unit tests from the repository root:

```sh
python3 -m unittest discover -s tests
```

Test reports are version-specific. The repository cleanup did not run new
experiments or claim a fresh full-suite result. To build the thesis, use the
[thesis instructions](thesis/README.md).

## Historical material

Old plans, progress notes and evidence remain under their original paths.
The November 2 cleanup removed superseded PDFs and delivery packages from the
current checkout and replaced outdated navigation. The
[cleanup record](docs/maintenance/repository_cleanup_20261102.md) lists every
removed file and its recovery location in Git history. No history was rewritten.
