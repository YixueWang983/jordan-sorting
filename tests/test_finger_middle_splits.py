import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import validate_finger_middle_splits as campaign
from oracle import oracle


class MiddleSplitCampaignTests(unittest.TestCase):
    def test_fixed_inputs_cover_both_parities_and_mirrors_without_duplicates(self):
        seen = set()
        for n in (128, 129):
            for k in (3, 7, 19):
                forward = campaign.values_for(n, k, False)
                backward = campaign.values_for(n, k, True)
                self.assertEqual(backward, [n+1-x for x in forward])
                for values in (forward, backward):
                    self.assertEqual(sorted(values), list(range(1, n+1)))
                    self.assertTrue(oracle(values)['valid'])
                    self.assertNotIn(tuple(values), seen)
                    seen.add(tuple(values))
        self.assertEqual(len(seen), 12)

    def test_timeout_and_worker_error_are_failures_with_retained_artifacts(self):
        for outcome in ('timeout', 'worker_error'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)/'campaign'
                def worker(*args, **kwargs):
                    self.assertEqual(kwargs['timeout'], 180)
                    output.mkdir()
                    (output/'completed-case.txt').write_text('keep this evidence')
                    if outcome == 'timeout':
                        raise subprocess.TimeoutExpired(args[0], 180)
                    return subprocess.CompletedProcess(args[0], 7)
                with patch.object(campaign.sys, 'argv', ['campaign', '--output', str(output)]), \
                     patch.object(campaign.subprocess, 'run', worker):
                    self.assertEqual(campaign.main(), 2)
                failure = json.loads((output/'failure.json').read_text())
                self.assertIs(failure['accepted'], False)
                self.assertIs(failure['retry_or_replacement'], False)
                self.assertEqual((output/'completed-case.txt').read_text(), 'keep this evidence')


if __name__ == '__main__': unittest.main()
