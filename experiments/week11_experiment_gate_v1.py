"""Explicit compatibility entry point for the frozen Week 11 v1 M1 gate."""

from week11_experiment_gate import (
    PAPER_ALGORITHM_NAME,
    WEEK11_EXPERIMENT_GATE,
    WEEK11_OUTPUT_DIR,
    WEEK11_RUN_ID,
    Week11ExperimentGate,
    gate_to_dict,
    validate_week11_experiment_gate,
)


WEEK11_EXPERIMENT_GATE_V1 = WEEK11_EXPERIMENT_GATE
WEEK11_GATE_VERSION_V1 = "v1"
WEEK11_MACHINE_BASELINE_PATH_V1 = (
    "docs/analysis/week11_machine_baseline_v1_m1.json"
)
WEEK11_MACHINE_BASELINE_SHA256_V1 = (
    "0a18befd93257c2ce4f625cdc17ceafd537d1c7349ed2a5601d684ebba41e617"
)
WEEK11_MACHINE_IDENTITY_ID_V1 = "week11_v1_m1_macbookair10_1"
WEEK11_MACHINE_PREFLIGHT_PATH_V1 = (
    "docs/analysis/week11_machine_preflight_v1_m1.md"
)
WEEK11_OUTPUT_DIR_V1 = WEEK11_OUTPUT_DIR
WEEK11_RUN_ID_V1 = WEEK11_RUN_ID


__all__ = (
    "PAPER_ALGORITHM_NAME",
    "WEEK11_EXPERIMENT_GATE_V1",
    "WEEK11_GATE_VERSION_V1",
    "WEEK11_MACHINE_BASELINE_PATH_V1",
    "WEEK11_MACHINE_BASELINE_SHA256_V1",
    "WEEK11_MACHINE_IDENTITY_ID_V1",
    "WEEK11_MACHINE_PREFLIGHT_PATH_V1",
    "WEEK11_OUTPUT_DIR_V1",
    "WEEK11_RUN_ID_V1",
    "Week11ExperimentGate",
    "gate_to_dict",
    "validate_week11_experiment_gate",
)
