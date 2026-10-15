"""Versioned synchronous qualification; not the public fresh-prefix checker.

Both instances use the same resumable production loop and CHECKED policy.
Every prefix gets full current-state/history checks and comparison. A third
fresh CHECKED instance is replayed once at the end. This intentionally differs
from constructing a fresh instance for EVERY prefix; the reference stays in
paper_jordan.validate_paper_jordan_state_reference for bounded comparison.
"""
from paper_execution_policy import CHECKED_POLICY
from sibling_backend_contract import resolve_sibling_backend
import paper_jordan as core

QUALIFICATION_SCHEMA = "synchronous_checked_prefixes_v2"


def require_independent(first, second):
    """Audit-only identity check for states and the concrete backend registries."""
    if first.backend_identity != second.backend_identity or first.execution_policy is not second.execution_policy:
        raise RuntimeError("qualification instances differ in backend/config/policy")
    for name in ("sibling_backend", "partial_order", "pairs", "pair_by_end_index",
                 "stage_results", "backend_work", "trace", "metrics"):
        if getattr(first, name) is getattr(second, name):
            raise RuntimeError("qualification instances share mutable " + name)
    if any(first.pairs.get(pid) is pair for pid, pair in second.pairs.items()):
        raise RuntimeError("qualification instances share pair objects")
    if any(a is b for a,b in zip(first.points, second.points)):
        raise RuntimeError("qualification instances share point objects")
    for name in ("_pairs", "_lists", "_nodes", "_dummies", "_dummy_pair_ids"):
        left = getattr(first.sibling_backend, name, None)
        right = getattr(second.sibling_backend, name, None)
        if left is None and right is None:
            continue
        if type(left) is not dict or type(right) is not dict or left is right:
            raise RuntimeError("qualification backend registry alias/type: " + name)
        # Ordinary dummy registries store immutable IDs; tree registries store
        # mutable headers, handles and nodes, whose identities must be disjoint.
        mutable = lambda values: {id(v) for v in values if type(v) not in (int, str, bool, type(None))}
        if mutable(left.values()) & mutable(right.values()):
            raise RuntimeError("qualification backend objects shared: " + name)


def run_synchronous_qualification(values, *, backend="ordinary_list", prefix_callback=None):
    """Return the primary state and coverage counts; no timing qualification.

    Callback is an external observer after both prefix states pass. Failure
    aborts the run; no state or audit result survives for a later invocation.
    Small n<3 remains the public API's separate base-case contract.
    """
    values = list(values)
    spec = resolve_sibling_backend(backend)
    primary = core._iterate_paper_jordan_states(values, execution_policy=CHECKED_POLICY, backend=spec)
    peer = core._iterate_paper_jordan_states(values, execution_policy=CHECKED_POLICY, backend=spec)
    report = dict(schema=QUALIFICATION_SCHEMA, prefix_comparisons=0,
                  fresh_final_replays=0, initialized_instances=2, history_work={},
                  same_backend_same_config=True, performance_eligible=False)
    try:
        for state, other in zip(primary, peer, strict=True):
            if state.processed_count != other.processed_count:
                raise RuntimeError("qualification prefixes differ")
            require_independent(state, other)
            left = core._validate_state_local(state, history_work=report['history_work'])
            right = core._validate_state_local(other, history_work=report['history_work'])
            core._compare_replay_states(state, other, snapshots=left, replay_views=right)
            core._count_state_validation(state); core._count_state_validation(other)
            report['prefix_comparisons'] += 1
            if prefix_callback is not None:
                prefix_callback(state, left)
        if report['prefix_comparisons'] != len(values)-2:
            raise RuntimeError("qualification missed a completed prefix")
        fresh = core._run_paper_jordan_state_values(
            values, execution_policy=CHECKED_POLICY, backend=spec,
            forbidden_backend=state.sibling_backend)
        require_independent(state, fresh); require_independent(other, fresh)
        # Re-audit the primary at the final comparison too, since even an
        # observer could have altered it. No prior successful view is trusted.
        left = core._validate_state_local(state, history_work=report['history_work'])
        final = core._validate_state_local(fresh, history_work=report['history_work'])
        core._compare_replay_states(state, fresh, snapshots=left, replay_views=final)
        report.update(fresh_final_replays=1, initialized_instances=3)
        return state, report
    finally:
        primary.close(); peer.close()
