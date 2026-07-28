# Week 11 Machine Preflight

Last updated: 2026-07-28

Status: machine identity frozen; formal timing readiness must be rechecked on
Day 5 and immediately before Day 6.

## Source Baseline

Captured on 2026-07-28 at approximately 19:43 CEST.

```text
HEAD:
    d6f9f2ffb2a4af49097a80b2b8cec7e6accbd5d0

origin/main:
    d6f9f2ffb2a4af49097a80b2b8cec7e6accbd5d0

commit:
    Align final experiment evidence rules

starting worktree:
    clean
```

The formal Day 6 evidence must record the later pushed source commit that owns
the completed runner and validator. This Day 1 commit is the development
baseline, not the final evidence commit.

## Machine Identity

```text
model:
    MacBook Air

model identifier:
    MacBookAir10,1

model number:
    MGN63D/A

chip:
    Apple M1

CPU cores:
    8 total
    4 performance
    4 efficiency

memory:
    8 GB

architecture:
    arm64
```

Serial number, hardware UUID, and device identifiers are intentionally not
stored in the repository because they are not needed for reproducibility.

## Operating System

```text
operating system:
    macOS 26.5

build:
    25F71

platform string:
    macOS-26.5-arm64-arm-64bit
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

logical CPU count reported by Python:
    8

perf_counter resolution:
    4.166666666666667e-08 seconds
```

The same Python executable and environment must be used for Day 6.

## Power and Load Snapshot

Day 1 snapshot:

```text
power source:
    AC Power

battery:
    63 percent
    discharging

load averages:
    8.81, 3.53, 2.39
```

This snapshot is not timing-ready. Although macOS reported AC power, the
battery was still discharging and the one-minute load average was high. No
timing experiment was run.

Day 6 must not start until:

- AC power is connected and stable;
- the battery is not reporting active discharge caused by an unstable power
  connection;
- load averages have returned to a low, stable baseline;
- no large download, compilation, virtual machine, backup, indexing task, or
  other sustained workload is active;
- no thermal warning or obvious throttling condition is present.

## Formal Run Controls

For the complete pilot:

1. use this physical machine;
2. use `/opt/anaconda3/bin/python`;
3. connect stable AC power before preflight;
4. close large downloads, compilers, virtual machines, containers, and
   high-load applications;
5. avoid system updates, package installation, and source changes;
6. do not change power mode during the run;
7. do not combine local results with WSL, Docker, remote CI, or another
   machine;
8. record a fresh power/load snapshot in `environment.json` before timing;
9. keep the terminal session and machine awake for the entire run;
10. preserve the complete output directory immediately after validation.

If the machine, Python environment, or frozen configuration changes, the run
must use a new gate version and run ID.

## Planned Pilot Date

Earliest planned execution:

```text
2026-08-02
```

This date is conditional on formal approval of the Day 5 preflight gate. It is
not a deadline and does not authorize early execution.

## Baseline Verification

```text
unit tests:
    383 passed

compileall:
    passed

exhaustive valid permutations through n=8:
    2,074 passed

fixed generated cases:
    48 passed

Week 11 gate:
    frozen_not_executed

formal output directory:
    absent
```

## Day 5 and Day 6 Recheck

Immediately before formal execution, record again:

```text
git HEAD and origin/main
clean worktree status
machine model and architecture
OS version
Python version and executable
power source and battery state
load averages
available disk space
formal output-directory absence
```

If any hard gate fails, do not run the pilot.
