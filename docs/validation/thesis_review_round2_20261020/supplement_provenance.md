# Supplement provenance retained outside the thesis

This note replaces the process discussion formerly in Appendix B.4 at `2da8b662`. It does not change any archived records or their status.

Four external reviewer files are preserved verbatim under `../thesis_revision_20261020/external_review/`. They report 1,900 stress inputs and fifteen-input wrapper medians, but lack bound commands, source/environment identities and individual records. Their original scripts lack optimization guards; the timing script checks only the final output per batch. Those aggregates remain excluded from verified coverage and formal estimates.

The separately executed `../thesis_revision_20261020/local_supplement/` froze its protocol, input values and source hashes before running. It saves 900 diagnostic batches and traces for forty correctness cases, with every output checked. It is neither a reproduction of all external runs nor a formal campaign. Production Python matches `19a553fb`; process-local diagnostic changes are recorded. Seeded inputs are not uniform samples.
