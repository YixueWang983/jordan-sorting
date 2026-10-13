"""Small production contract for the sibling operations used by Jordan Sorting.

This is separate from the abstract Item/key operation-test model. Implementations
must enforce Jordan geometry and family constraints themselves. The contract
does not certify a backend's complexity or authorize performance experiments.
"""

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class SplitWork:
    """Backend-reported observations, interpreted under its metrics_schema.

    These four legacy fields are not a count of all maintenance work. In
    particular the ordinary backend reports logical partition/copy/transfer
    sizes, excluding repeated validation and ownership-chain traversal.
    """

    sibling_scan_checks: int
    split_items_scanned: int
    split_items_copied: int
    split_items_transferred: int

    def items(self):
        return tuple((field.name, getattr(self, field.name)) for field in fields(self))

    def validate(self):
        for name, value in self.items():
            if type(value) is not int or value < 0:
                raise RuntimeError(f"invalid backend split observation: {name}")
        return self


def require_split_work(work, count_operations):
    if count_operations:
        if not isinstance(work, SplitWork):
            raise RuntimeError("counted split requires backend work observations")
        work.validate()
    elif work is not None:
        raise RuntimeError("split observations must be disabled with counters")
    return work


# No whole-list representation is part of the normal-path interface.
REQUIRED_BACKEND_METHODS = (
    "register_pair", "get_pair", "point_value", "validate_live_pair",
    "validate_dummy_ownership", "boundary_list", "list_owner", "list_size",
    "child_list_ids", "extreme_child", "make_list", "insert_boundary",
    "split_pairs_at_value", "registered_pair_ids", "validate_invariants",
    "logical_snapshot", "audit_snapshot", "validate_iteration_complete",
)


def _immutable_option(value):
    return type(value) in (str, int, bool, type(None)) or (
        type(value) is tuple and all(_immutable_option(item) for item in value)
    )


@dataclass(frozen=True)
class SiblingBackendSpec:
    """Immutable constructor choice; each run, including replay, creates anew.

    Explicit classes support backend development without registering an
    unavailable tree or silently substituting the ordinary implementation.
    Options are immutable keyword arguments, not an already-built backend.
    """

    backend_type: type
    options: tuple = ()

    def __post_init__(self):
        if not isinstance(self.backend_type, type):
            raise TypeError("backend_type must be a class, not a mutable instance")
        if getattr(self.backend_type, "sorting_ready", True) is not True:
            raise TypeError("partial backend is not available for complete sorting")
        for name in REQUIRED_BACKEND_METHODS:
            if not callable(getattr(self.backend_type, name, None)):
                raise TypeError(f"backend lacks required operation: {name}")
        for name in ("backend_name", "audit_schema", "metrics_schema"):
            value = getattr(self.backend_type, name, None)
            if not isinstance(value, str) or not value:
                raise TypeError(f"backend lacks schema/identity: {name}")
        if type(self.options) is not tuple:
            raise TypeError("backend options must be an immutable tuple")
        names = set()
        for item in self.options:
            if type(item) is not tuple or len(item) != 2:
                raise TypeError("backend options must contain (name, value) tuples")
            name, value = item
            if not isinstance(name, str) or not name.isidentifier():
                raise ValueError("backend option name must be an identifier")
            if name in names or name in ("point_value", "execution_policy"):
                raise ValueError(f"duplicate or reserved backend option: {name}")
            if not _immutable_option(value):
                raise TypeError(f"backend option must be immutable: {name}")
            names.add(name)

    @property
    def identity(self):
        cls = self.backend_type
        return (
            cls.__module__, cls.__qualname__, cls.backend_name, self.options,
            cls.audit_schema, cls.metrics_schema,
            "jordan-logical-v1", "jordan-trace-v1",
        )

    def create(self, point_value, execution_policy, *, forbidden_instance=None):
        backend = self.backend_type(
            point_value, execution_policy=execution_policy, **dict(self.options)
        )
        if type(backend) is not self.backend_type:
            raise RuntimeError("backend constructor returned a different backend type")
        if backend is forbidden_instance:
            raise RuntimeError("replay requires a fresh backend instance")
        if backend.execution_policy is not execution_policy:
            raise RuntimeError("backend did not preserve the execution policy")
        if backend.registered_pair_ids():
            raise RuntimeError("backend constructor must return an empty fresh instance")
        return backend

    def validate_instance(self, backend, recorded_identity):
        if type(backend) is not self.backend_type or self.identity != recorded_identity:
            raise RuntimeError("state backend identity/configuration/schema changed")
        for name in ("backend_name", "audit_schema", "metrics_schema"):
            if getattr(backend, name) != getattr(self.backend_type, name):
                raise RuntimeError(f"backend instance schema changed: {name}")


def resolve_sibling_backend(backend="ordinary_list"):
    if isinstance(backend, SiblingBackendSpec):
        return backend
    if not isinstance(backend, str):
        raise TypeError("backend must be a registered name or SiblingBackendSpec")
    if backend == "heterogeneous_finger":
        from heterogeneous_finger_backend import HeterogeneousFingerBackend
        return SiblingBackendSpec(HeterogeneousFingerBackend)
    if backend != "ordinary_list":
        raise ValueError(f"unknown or unavailable sibling backend: {backend}")
    from sibling_list_backend import OrdinarySiblingListBackend

    return SiblingBackendSpec(OrdinarySiblingListBackend)
