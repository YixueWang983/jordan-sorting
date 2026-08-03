# Week 11 Pilot Run 002 Failure Record

Last updated: 2026-08-03

## Status

```text
protocol_version: week11_pilot_v1
execution_id: week11_pilot_v1__run002
source_commit: f008d77ab78dbadcca66a51aae3dadab7408516b
result: read-only preflight failed before evidence initialization
execution_id_reusable: false
```

This execution ID is retired and must not be used again.

## Commands

The required macOS memory probe succeeded outside the Codex sandbox:

```bash
sysctl -n hw.memsize
```

```text
17179869184
```

The following read-only preflight was then run once:

```bash
python experiments/run_week11_pilot.py \
  --preflight-only \
  --execution-id week11_pilot_v1__run002
```

The formal pilot command was not run.

## Failure

The preflight rejected the captured power state:

```text
RuntimeError: Week 11 timing preflight failed: power must be battery-free,
charging/full on AC, or high-charge discharging on AC, with low-power mode
disabled
```

The immediately captured macOS state was:

```text
Now drawing from 'AC Power'
InternalBattery: 100%; finishing charge
active AC profile: lowpowermode 0
```

The power parser accepts the exact states `charging`, `charged`, `full`, and
`discharging`. It treats the real macOS phrase `finishing charge` as unknown,
so the readiness gate failed closed even though AC was connected, the battery
was full, and low-power mode was disabled.

This is a power-state parser coverage gap. It is not an algorithm, generator,
validator, timing, or insufficient-power failure.

## Execution Boundary

The failed command used `--preflight-only`. It did not:

- create `results/runs/week11_pilot_v1__run002`;
- write `config.json` or `environment.json`;
- generate cases or run oracle certification;
- run checked diagnostics;
- perform warm-up or measured timing;
- write CSV, manifest, or validation-report evidence.

The expected run directory was confirmed absent immediately afterward.

## Required Follow-up

Before another attempt:

1. review this failure checkpoint;
2. keep `week11_pilot_v1__run002` retired;
3. decide whether `finishing charge` should be normalized to a safe accepted
   battery state;
4. if so, add focused parser and readiness regression tests before changing
   the runner;
5. commit, push, and review any parser correction;
6. use a new execution ID, expected to be `week11_pilot_v1__run003`;
7. do not start W11D7 until a new run produces validated evidence.
