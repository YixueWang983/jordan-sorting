import ast
from contextlib import ExitStack
from types import FunctionType
import unittest
from unittest.mock import patch

import heterogeneous_finger_backend as tree
import heterogeneous_finger_split as split
from matched_backend_fixture import backend_spec, identity
from paper_jordan_sort import paper_jordan_diagnostics_valid, paper_jordan_sort_valid
from paper_execution_policy import MINIMAL_POLICY
from sibling_backend_contract import SiblingBackendSpec
from uninstrumented_finger import prepare_uninstrumented, _RemoveObservers
from validate_finger_work_modes import sequence


class UninstrumentedTreeTests(unittest.TestCase):
    def test_old_identity_and_default_behavior(self):
        self.assertEqual(identity('heterogeneous_finger'), [
            'heterogeneous_finger_backend', 'HeterogeneousFingerBackend',
            'heterogeneous_finger', [['detailed_work', False]],
            'heterogeneous-split-adopt-v2', 'heterogeneous-record-access-v2',
            'jordan-logical-v1', 'jordan-trace-v1'])
        b = tree.HeterogeneousFingerBackend(lambda p:p)
        self.assertTrue(b.instrumented)
        self.assertTrue(b.detailed_work)
        self.assertIs(type(b.work), tree.WorkLedger)
        self.assertNotIn('split_value', vars(b))

    def test_invalid_configuration_and_mutation(self):
        for value in (1, None, 'false'):
            with self.assertRaises(TypeError):
                tree.HeterogeneousFingerBackend(int, instrumented=value)
        with self.assertRaises(ValueError):
            tree.HeterogeneousFingerBackend(int, instrumented=False)
        spec = backend_spec('heterogeneous_finger_uninstrumented')
        b = spec.create(int, MINIMAL_POLICY)
        self.assertIs(type(b), tree.HeterogeneousFingerBackend)
        self.assertIsNone(b.work)
        self.assertFalse(b.instrumented)
        b._instrumented = True
        with self.assertRaisesRegex(RuntimeError, 'instrumentation configuration'):
            spec.validate_instance(b, spec.identity)

    def test_all_record_types_and_methods_are_unobserved(self):
        family = prepare_uninstrumented()
        for name, cls in family.types.items():
            with self.subTest(record=name):
                self.assertIs(cls.__getattribute__, object.__getattribute__)
                self.assertIs(cls.__setattr__, object.__setattr__)
                self.assertFalse(issubclass(cls, tree._Tracked))
        b = backend_spec('heterogeneous_finger_uninstrumented').create(int, MINIMAL_POLICY)
        observed = [n for n,v in vars(tree.HeterogeneousFingerBackend).items() if isinstance(v,FunctionType) and hasattr(v,'__wrapped__')]
        self.assertEqual(len(observed), 21)
        for name in observed:
            self.assertFalse(hasattr(getattr(b,name).__func__, '__wrapped__'))
            self.assertIs(getattr(b,name).__func__, family.methods[name])
        for name,v in vars(split.TreeOperations).items():
            if hasattr(v, '__wrapped__'):
                self.assertFalse(hasattr(getattr(family.operations,name), '__wrapped__'))

    def test_sorts_with_ledger_and_tracking_methods_forbidden(self):
        spec = backend_spec('heterogeneous_finger_uninstrumented')
        def forbidden(*a, **k):
            raise AssertionError('uninstrumented path accessed an observer')
        with ExitStack() as stack:
            for name in ('__init__','add','allocate','read','write','phase','observe','snapshot'):
                stack.enter_context(patch.object(tree.WorkLedger,name,forbidden))
            stack.enter_context(patch.object(tree._Tracked,'__getattribute__',forbidden))
            stack.enter_context(patch.object(tree._Tracked,'__setattr__',forbidden))
            for shape in ('balanced','skew','repeated'):
                for n in (32,33):
                    values=sequence(n,shape,bool(n%2))
                    result=paper_jordan_diagnostics_valid(values,backend=spec)
                    self.assertTrue(result['invariants_valid'])
                    self.assertEqual(result['output'],sorted(values))
                    self.assertEqual(paper_jordan_sort_valid(values,'minimal',backend=spec),sorted(values))

    def test_checked_traces_and_counted_trace_match(self):
        for shape in ('balanced','skew','repeated'):
            values=sequence(33,shape,True)
            reports=[paper_jordan_diagnostics_valid(values,backend=spec) for spec in (
                backend_spec('heterogeneous_finger'),
                backend_spec('heterogeneous_finger_uninstrumented'),
                SiblingBackendSpec(tree.HeterogeneousFingerBackend))]
            for field in ('output','trace','metrics'):
                self.assertEqual(reports[0][field],reports[1][field])
                self.assertEqual(reports[0][field],reports[2][field])

    def test_projection_preserves_algorithm_calls(self):
        original=ast.parse('def f(self):\n self.work.add("rotations")\n self.rotate()\n with self.work.phase("join"):\n  return self.join()\n')
        projected=_RemoveObservers().visit(original)
        text=ast.unparse(projected)
        self.assertIn('self.rotate()',text)
        self.assertIn('return self.join()',text)
        self.assertNotIn('self.work',text)
        self.assertIs(prepare_uninstrumented(),prepare_uninstrumented())
        with self.assertRaisesRegex(RuntimeError,'algorithm call'):
            _RemoveObservers().visit(ast.parse('self.work.add("x", self.rotate())'))


if __name__ == '__main__':
    unittest.main()
