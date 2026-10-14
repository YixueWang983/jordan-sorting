"""Recompute archived counts/inequalities, not rerun algorithms or prove them."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT/'experiments'), str(ROOT/'src')]
from validate_matched_backend_fixture import validate


def read(path):
    with gzip.open(path, 'rt') if path.suffix == '.gz' else path.open() as stream:
        return json.load(stream)


def sources(mapping):
    assert mapping
    for path, expected in mapping.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path


def main():
    probe = read(HERE/'cost_probe/records.json.gz')
    plan = read(HERE/'cost_probe/plan.json')
    assert probe['source_sha256'] == plan['source_sha256']
    sources(plan['source_sha256'])
    counts = Counter(); cases = defaultdict(set); split_events = []
    for event in probe['events']:
        counts[event['kind']] += 1
        if event['kind'] == 'join':
            a, b = event['normalized_ranks']
            assert max(a,b) <= event['result_rank'] <= max(a,b)+1
            assert event['recursive_calls'] <= 2*abs(a-b)+3
            if 'accumulator' in event:
                assert event['accumulator'] <= event['sibling']+1
        elif event['kind'] == 'split_down':
            assert all(r <= event['source_rank']+1 for r in event['result_normalized_ranks'])
            assert event['recursive_calls'] <= 2*sum(event['result_normalized_ranks'])+5*event['joins']
            if type(event['case']) is dict:
                case = event['case']; key = (case['leaves'], case['shape_index'])
                assert case['cut'] not in cases[key]
                cases[key].add(case['cut'])
            else:
                split_events.append(event)
        else:
            assert event['kind'] == 'repair_short'
            assert event['rib_calls'] <= 2
            assert event['rib_steps'] <= 4*(event['start_rank']+event['propagations']+2)
            assert event['propagations']+event['potential_change'] <= 8
    for (n, index), cuts in cases.items():
        assert 1 <= n <= 10 and index >= 0 and cuts == set(range(n+1))
    exhaustive = sum(len(cuts) for cuts in cases.values())
    assert exhaustive == probe['exhaustive_split_cases'] == 2634
    assert len(probe['histories']) == 12 and len(split_events) == 36
    assert len({h['case'] for h in probe['histories']}) == 12
    for history in probe['histories']:
        rows = history['explicit_operation_steps']
        assert history['model_and_structure_passed'] is True
        assert [r['sequence'] for r in rows] == list(range(history['operations']))
        matching = [e for e in probe['events'] if e['case'] == history['case']]
        assert sum(r['steps']['rooted_join_steps'] for r in rows) == sum(
            e['recursive_calls'] for e in matching if e['kind'] == 'join')
    assert all(e['cascades']+e['potential_change'] <= 8 for e in probe['inserts'])
    assert probe['raw_red_root_join'] == {'before':[0,0],'normalized':[1,1],'result':2}

    plan = read(HERE/'middle_splits/plan.json'); sources(plan['source_sha256'])
    files = sorted((HERE/'middle_splits').glob('case-*.json.gz'))
    assert len(files) == len(plan['plan']) == 12
    hashes = set(); prefixes = 0; smaller = []; total_splits = 0
    expected_runs = {f'{b}/{m}' for b in ('ordinary','tree_on','tree_off') for m in ('checked','minimal')}
    for path, spec in zip(files, plan['plan']):
        row = read(path); values = row['values']; assert row['spec'] == spec
        digest = hashlib.sha256(repr(values).encode()).hexdigest()
        assert digest == row['input_sha256'] and digest not in hashes
        hashes.add(digest); assert set(row['runs']) == expected_runs
        for name, run in row['runs'].items():
            assert run['output'] == sorted(values) and run['final_replay_passed'] is True
            if name.endswith('/minimal'):
                assert run['prefixes'] == []
                continue
            assert run['prefixes'] == list(range(3,len(values)+1))
            parents = {}; outputs = set(); finite = Counter(); count = Counter(); sizes = []
            for e in run['trace']:
                if e['step'] == 'step3a_insert_pair':
                    parents[e['iteration']] = e['parent_pair_id']
                    if e['insertion_mode'] == 'boundary_insertion' and e['sibling_list_id'] in outputs:
                        count['insert_into_previous_split_output'] += 1
                if e['step'] != 'step3b_split_sibling_list' or not e['performed']:
                    continue
                count['splits'] += 1
                count['resplit_previous_output'] += int(e['input_list_id'] in outputs)
                if parents[e['iteration']] > 0:
                    count['finite_owner_splits'] += 1; finite[parents[e['iteration']]] += 1
                a,b = e['left_size'], e['right_size']; assert a+b == e['input_size']
                if a and b:
                    count['both_nonempty'] += 1; sizes.append([a,b])
                outputs.update(x for x in (e['left_list_id'],e['right_list_id']) if x is not None)
            count = Counter({k:v for k,v in count.items() if v})
            count['finite_owners_with_multiple_transfers'] = sum(n>1 for n in finite.values())
            assert run['coverage'] == {'counts':dict(count),'nonempty_split_sizes':sizes}
            assert any(min(a,b)==spec['k'] for a,b in sizes)
            if name == 'tree_on/checked':
                prefixes += len(run['prefixes']); smaller.extend(min(a,b) for a,b in sizes)
                total_splits += count['splits']
    assert read(HERE/'middle_splits/summary.json') == {
        'accepted':True,'inputs':12,'original_runs':72,'performance_eligible':False,
        'per_checked_configuration':{'prefixes':prefixes,'nonempty_smaller_sides':smaller}}
    success = validate(HERE/'matched_fixture'); failure = validate(HERE/'failed_fixture')
    assert success['completed_successfully'] and not failure['completed_successfully']
    print(json.dumps({'archive_counts_and_sources_checked':True,
        'cost_events':dict(counts),'exhaustive_split_cases':exhaustive,
        'mixed_histories':12,'mixed_recorded_operations':sum(h['operations'] for h in probe['histories']),
        'mixed_split_calls':len(split_events),'insertion_observations_including_construction':len(probe['inserts']),
        'middle_inputs':12,'middle_original_runs':72,'per_checked_configuration':{
            'prefixes':prefixes,'splits':total_splits,'nonempty_smaller_sides':smaller},
        'synthetic_fixture':success,'retained_failure_fixture':failure},indent=2))


if __name__ == '__main__': main()
