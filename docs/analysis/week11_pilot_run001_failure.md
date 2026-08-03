# Week 11 Pilot Run 001 Failure Record

Last updated: 2026-08-03

## Status

```text
protocol_version: week11_pilot_v1
execution_id: week11_pilot_v1__run001
source_commit: 0ceefc8d85302774681ce29263e9a0f6f5ed7b67
result: failed before evidence initialization
execution_id_reusable: false
```

This execution ID is retired and must not be used again.

## Command

```bash
python experiments/run_week11_pilot.py \
  --execution-id week11_pilot_v1__run001
```

The command was launched once from the Codex desktop execution environment.

## Failure

The runner failed while capturing anonymous benchmark-environment metadata:

```text
capture_benchmark_environment()
-> _physical_memory_gb()
-> sysctl -n hw.memsize
-> Operation not permitted
-> RuntimeError: could not capture physical memory
```

The same read-only `sysctl` command was run separately in that environment and
returned `Operation not permitted`. This is consistent with a Codex sandbox
restriction, not an algorithm, generator, validator, or timing failure.

## Execution Boundary

The failure occurred before:

- creation of `results/runs/week11_pilot_v1__run001`;
- writing `config.json` or `environment.json`;
- case generation or oracle certification;
- checked diagnostics;
- warm-up or measured timing;
- CSV, manifest, or validation-report creation.

The expected run directory was confirmed absent immediately after the failure.
No timing result was produced and no partial timing evidence exists.

## Required Follow-up

Before another attempt:

1. review this failure checkpoint;
2. keep `week11_pilot_v1__run001` retired;
3. select a new execution ID, expected to be `week11_pilot_v1__run002`;
4. execute from a normal terminal environment where `sysctl -n hw.memsize`
   succeeds;
5. retain the unchanged `week11_pilot_v1` protocol and source-controlled
   execution path;
6. do not start W11D7 until a new run produces validated evidence.

