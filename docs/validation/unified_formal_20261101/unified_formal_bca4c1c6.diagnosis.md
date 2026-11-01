# Formal session stopped at the power gate

The author explicitly confirmed personal review of all checklist items and authorized receipt creation and formal execution in the chat. The author subsequently confirmed other applications were closed and synchronization handled. The formal command was launched exactly once by Codex on the author’s Mac using caffeinate -i. It exited with code 2. No retry, resumption, replacement run, or source stitching was performed.

## Verified completion scope

| Source | Status | PASS | ERROR | NOT_RUN |
|---|---|---:|---:|---:|
| common | COMPLETE | 140 | 0 | 0 |
| targeted_split | COMPLETE | 12 | 0 | 0 |
| structural | COMPLETE | 18 | 0 | 0 |
| geometric | ERROR | 23 | 1 | 76 |
| seeded | NOT_RUN | 0 | 0 | 32 |

Only the three fully completed sources (170 inputs) are eligible for the preregistered complete-source performance summaries. The 23 PASS inputs in geometric and the failed input’s observations remain failure evidence; they are not added to the main performance denominator. The full 302-input session is incomplete. No performance analysis or thesis numeric update has been performed following this failure.

## Recorded cause

Input geometric--geometric-n256-08 (n=256, B=2) failed its post-job power checkpoint. The saved before observation says AC Power; the saved after observation says Battery Power. Low Power Mode was 0 in both. The 50 committed batch records (10 warmups and 40 formal samples) have PASS status, but this does not override the failed environmental gate. The job is marked WORKER_ERROR, accepted=false, performance_eligible=false. The observations establish a power-state change; they do not establish its physical cause or exact time within the job.

Failure was recorded at 2026-11-01 21:41:19 Europe/Berlin (20:41:19 UTC). Source execution lasted approximately 205.3 seconds after the formal session’s source loop began; this excludes prerequisite validation at startup.

## Read-only verification

The independent validator exited 0 and reported archive_valid=true, complete=false, hard_error=true, all_sources_complete=false. This confirms integrity and faithful failure recording, not a successful full campaign. The manifest and all raw records are retained. The working tree remained clean on main.

## Evidence

- ./unified_formal_bca4c1c6/
- ./unified_formal_bca4c1c6.console.log
- ./unified_formal_bca4c1c6.validation.json
- ./unified_formal_bca4c1c6/sources/geometric/jobs/geometric--geometric-n256-08/failure.json
- ./unified_formal_bca4c1c6/sources/geometric/jobs/geometric--geometric-n256-08/power.json
- ./author_unified_review_bca4c1c6.json

Do not rerun the formal command or delete the output. Further treatment of the incomplete session must respect the preregistered failure and reporting rules.
