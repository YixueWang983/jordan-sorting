"""Generate the uninstrumented implementation from the canonical tree source.

No algorithm method is maintained here. A deliberately small AST projection
removes observer statements/decorators and chooses a plain record class family.
Both modules execute in one private namespace, so constructors and isinstance
checks consistently resolve to that family, including split fragments.

Preparation is cached per process and explicitly performed before timing.
The public backend retains its exact type: immutable SiblingBackendSpec identity
continues to distinguish configurations by constructor options.
"""
from __future__ import annotations

import ast
from functools import lru_cache
import hashlib
from pathlib import Path
from types import FunctionType, MethodType, SimpleNamespace


RECORDS = ('PairHandle', '_Node', 'ExternalLeaf', 'InternalNode', 'ListHeader',
           'RootedPiece', 'FingerPiece')
BACKEND_SPECIAL = {'__init__', 'detailed_work', 'instrumented', 'validate_configuration'}


def _path(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _path(node.value) + '.' + node.attr
    return ''


class _RemoveObservers(ast.NodeTransformer):
    """Only remove known, statement-only ledger operations, never algorithm calls."""
    def __init__(self):
        self.removed = {'counter_statements': 0, 'phase_blocks': 0,
                        'decorators': 0, 'ledger_arguments': 0}

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and _path(node.value.func) in {
                'self.work.add', 'self.work.allocate', 'self.b.work.add',
                'self.b.work.allocate', 'ledger.allocate'}:
            for argument in (*node.value.args, *(k.value for k in node.value.keywords)):
                for part in ast.walk(argument):
                    if isinstance(part, (ast.NamedExpr, ast.Await, ast.Yield, ast.YieldFrom)):
                        raise RuntimeError('counter argument may change algorithm state')
                    if isinstance(part, ast.Call) and not (
                            _path(part.func) == 'type' and len(part.args) == 1
                            and _path(part.args[0]) == 'self' and not part.keywords):
                        raise RuntimeError('counter argument contains an algorithm call')
            self.removed['counter_statements'] += 1
            return None
        return self.generic_visit(node)

    def visit_With(self, node):
        if (len(node.items) == 1 and node.items[0].optional_vars is None
                and isinstance(node.items[0].context_expr, ast.Call)
                and _path(node.items[0].context_expr.func) in
                    {'self.work.phase', 'self.b.work.phase'}):
            self.removed['phase_blocks'] += 1
            return self.generic_visit(node).body
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and _path(decorator.func) in {'observed', 'phase'}:
                self.removed['decorators'] += 1
            else:
                decorators.append(decorator)
        node.decorator_list = decorators
        node = self.generic_visit(node)
        if not node.body:
            node.body = [ast.Pass()]
        return node

    def visit_Call(self, node):
        if (isinstance(node.func, ast.Name) and node.func.id in RECORDS
                and node.args and _path(node.args[0]) in {'self.work', 'self.b.work'}):
            self.removed['ledger_arguments'] += 1
            node.args[0] = ast.Constant(None)
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if (node.module == 'heterogeneous_finger_split' and
                [(n.name, n.asname) for n in node.names] == [('TreeOperations', None)]):
            # The generated namespace already binds its own TreeOperations.
            return None
        return node


class _PlainFields:
    __slots__ = ('_ledger',)
    _fields = frozenset()
    _pointers = frozenset()


@lru_cache(maxsize=1)
def prepare_uninstrumented():
    """Compile once, outside the timing interval; return the selected class family."""
    import heterogeneous_finger_backend as backend
    import heterogeneous_finger_split as split
    namespace = dict(vars(backend))
    namespace.update({k: v for k, v in vars(split).items() if k not in RECORDS})
    namespace['_Tracked'] = _PlainFields
    transformer = _RemoveObservers()
    source_hashes = {}
    for module, names in (
            (backend, set(RECORDS) | {'HeterogeneousFingerBackend'}),
            (split, {'RootedPiece', 'FingerPiece', 'TreeOperations'})):
        path = Path(module.__file__)
        source = path.read_bytes()
        source_hashes[path.name] = hashlib.sha256(source).hexdigest()
        parsed = ast.parse(source, filename=str(path))
        classes = [n for n in parsed.body if isinstance(n, ast.ClassDef) and n.name in names]
        for cls in classes:
            if cls.name == 'HeterogeneousFingerBackend':
                cls.body = [n for n in cls.body if not
                            (isinstance(n, ast.FunctionDef) and n.name in BACKEND_SPECIAL)]
        projected = transformer.visit(ast.Module(body=classes, type_ignores=[]))
        ast.fix_missing_locations(projected)
        for node in ast.walk(projected):
            if _path(node) in {'self.work', 'self.b.work', 'WorkLedger', '_UNOBSERVED'}:
                raise RuntimeError('unhandled instrumentation in canonical tree source')
        # All constructors and type checks use this one selected namespace.
        exec(compile(projected, str(path), 'exec'), namespace)
    implementation = namespace['HeterogeneousFingerBackend']
    methods = {}
    for name, value in vars(implementation).items():
        if isinstance(value, FunctionType):
            methods[name] = value
        elif isinstance(value, staticmethod):
            methods[name] = value
    types = {name: namespace[name] for name in RECORDS}
    for cls in types.values():
        if (cls.__getattribute__ is not object.__getattribute__ or
                cls.__setattr__ is not object.__setattr__):
            raise RuntimeError('generated record still intercepts fields')
    return SimpleNamespace(methods=methods, types=types,
                           operations=namespace['TreeOperations'],
                           source_sha256=source_hashes, projection=dict(transformer.removed))


def bind_uninstrumented(instance):
    family = prepare_uninstrumented()
    for name, method in family.methods.items():
        setattr(instance, name, method.__func__ if isinstance(method, staticmethod)
                else MethodType(method, instance))
    instance._uninstrumented_family = family
