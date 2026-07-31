# Week 11 v2 M4 Machine Preflight

Last updated: 2026-07-31

Status: replacement machine identity frozen; formal timing readiness must be
rechecked on Day 5 and immediately before Day 6.

## Version Boundary

This preflight belongs only to:

```text
gate version:
    v2

run ID:
    week11_paper_sorting_pilot_v2_m4

machine baseline:
    docs/analysis/week11_machine_baseline_v2_m4.json
```

The v1 M1 gate and its evidence paths remain historical, immutable records.
They must not be reused on this replacement computer.

## Source Baseline

Captured during W11D2.5 development on 2026-07-31.

```text
development HEAD:
    e68600a4aa628d299f11bada5cd5b7725a787b2d

origin/main:
    e68600a4aa628d299f11bada5cd5b7725a787b2d

starting worktree:
    clean
```

The formal evidence must record the later clean and pushed commit that owns
the completed runner and validator. This is a migration baseline, not the
formal timing commit.

## Machine Identity

```text
machine name:
    MacBook Air

model identifier:
    Mac16,13

chip:
    Apple M4

CPU cores:
    10 total
    4 performance
    6 efficiency

memory:
    16 GB

architecture:
    arm64
```

Serial number, hardware UUID, provisioning identifiers, and other unique
device identifiers are intentionally excluded.

## Operating System

```text
operating system:
    macOS 26.5.2

build:
    25F84
```

## Python Environment

```text
version:
    Python 3.12.4

implementation:
    CPython

distribution:
    Anaconda

executable:
    /opt/anaconda3/bin/python
```

## Power, Load, and Disk Snapshot

Development snapshot on 2026-07-31:

```text
power source:
    AC Power

battery:
    42 percent
    discharging

load averages:
    1.47, 1.89, 1.93

available disk:
    approximately 55 GiB
```

This snapshot is not timing-ready because the battery reports active
discharge. No timing experiment was run.

Day 6 must not start until stable AC power, a non-discharging battery state,
low system load, sufficient disk space, and an otherwise idle machine are all
confirmed by the Day 5 fail-closed gate.

## Migration Verification

```text
v1 formal output directory:
    absent

v2 formal output directory:
    absent

formal timing:
    not executed
```
