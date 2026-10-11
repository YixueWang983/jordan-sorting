# First Revision Audit — 2026-10-11

Status: **PASS for the first version-alignment revision**. Expanded experiments, backend implementation and the complete 2026-10-25 supervisor-review package remain pending.

## Scope and Claim Review

Nine LaTeX files were revised: Abstract, Introduction, Algorithm, Implementation, Experimental Method, Results, Limitations, Conclusion and the traceability appendix. The current implementation is bound to `6f7468324672e6f5abe9d95862cd5f296b792614`; the formal timing archive remains bound to `98868b1b705f6d5f22404ee8ad7b88ad7a834f52`.

The [claim amendments](revision_claims_20261011.md) distinguish the current failure contract from the measured historical implementation. In particular:

- Internal update failures propagate; already performed mutations are not restored. The failed state must be discarded. Public calls do not retry, recover a partial output, or substitute oracle output.
- Split planning, stale-plan rejection, conservation, output-list construction, ownership updates and local checks remain part of the current implementation.
- Execution-policy switches remain distinct from rollback support. The historical minimal call included recovery preparation, although successful measured calls need not execute rollback.
- All existing numerical results remain historical. This revision makes no performance claim for the current implementation or causal speedup claim for rollback removal.
- The heterogeneous finger-tree backend remains a specification. No implementation or linear-time bound is claimed for it.

The historical 46-claim inventory and its audit remain unchanged. This audit covers the amendments above; it does not retroactively extend the old content freeze to new work.

## Verification

| Check | Result and boundary |
| --- | --- |
| Current implementation regression | **133 tests passed** across `test_paper_jordan`, `test_paper_jordan_sort`, `test_sibling_list_backend`, and `test_paper_execution_policy` |
| Existing source, tests and evidence | SHA-256 comparison confirmed **520 protected tracked files unchanged**, including implementation, tests, experiments, results, analysis, historical thesis records, figures and bibliography |
| Archived evidence manifests | All **12 file entries** across the pilot and formal manifests matched their recorded hashes |
| Numerical and mathematical content | All **12 table, 7 figure and 19 equation environments** remained unchanged against the pre-revision source copy |
| Source cross-references | **127 unique labels**, no unresolved source cross-references |
| Final build | **74 A4 pages**, 16 bibliography entries; final LaTeX and Biber logs contain no warnings, errors, undefined references or overfull/underfull boxes |
| Visual review | All 74 pages inspected through contact sheets; detailed checks of physical pages 3, 14, 15, 29, 35, 39, 40, 41, 45, 53, 61, 65 and 70 found no clipping, overlap or defective pagination |
| Source/output correspondence | Build-input hashes verified against the repository source; the exported PDF and `thesis/build/main.pdf` match the reviewed clean-build PDF |

This was a targeted regression run, not a full repository test run, a new exhaustive validation campaign, or a timing experiment. Manifest hashes were checked directly; the full historical evidence validator was not rerun and is not claimed to have been rerun.

The test command, from the repository root, was:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:experiments:tests python3 -m unittest \
  test_paper_jordan test_paper_jordan_sort \
  test_sibling_list_backend test_paper_execution_policy -v
```

## Build and Reproduction

The host initially lacked a usable TeX toolchain. A portable [TinyTeX](https://github.com/rstudio/tinytex-releases) installation was placed inside the task's `work/thesis_revision_20261011/toolchain` directory. No system installation or shell-profile change was needed. The successful build used TeX Live 2026, LuaHBTeX 1.24.0, Latexmk 4.88 and Biber 2.22.

The bundled universal Biber wrapper required an unavailable `lipo` command. Its existing ARM64 executable slice was extracted unchanged into a local wrapper directory; the extraction offsets and SHA-256 values are recorded in `work/thesis_revision_20261011/toolchain/biber-arm/extraction.json`. This is consistent with the upstream [Biber launcher issue](https://github.com/plk/biber/issues/433).

The PDF was built from a fresh copy of the tracked thesis sources, without the previous machine's auxiliary files. With the local Biber and TinyTeX binaries on `PATH`, the command was:

```bash
mkdir -p build/texmf-var build/texmf-cache
TEXMFVAR=build/texmf-var TEXMFCACHE=build/texmf-cache latexmk -lualatex main.tex
```

The local helper is `/Users/schnee/Documents/Codex/2026-10-11/mu-q/work/thesis_revision_20261011/build_thesis.sh`; it accepts a thesis source directory as its first argument. The verified clean build, console log, test log, rendered pages and pre-edit copies remain under that same work directory.

The [source bindings](revision_source_bindings_20261011.json) identify the implementation, tests and archived manifests. The [build record](revision_build_record_20261011.json) records exact thesis input hashes and the reviewed output:

```text
PDF: Jordan_Sorting_论文修订稿_2026-10-11.pdf
Pages: 74
Bytes: 507114
SHA-256: 90c26ad0c471818fd98d2edccd7b69f57533a51fdbc1d34c17461ae42bfe9c64
```

## Remaining Work

The next task is to fix expanded-input generation rules and resource budgets, then validate the generator and candidate pool. Current-core timing and any backend comparison require new, independently validated archives before their results enter the thesis. The complete review draft remains scheduled for 2026-10-22, with checking on October 23–24 and supervisor review on October 25. Personal and examination metadata remain placeholders for later completion.
