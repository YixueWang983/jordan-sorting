"""Synthetic-clock mechanical fixtures; never formal performance observations."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments')]
import copy,gc,gzip,json,shutil,subprocess,tempfile,unittest
from contextlib import ExitStack
from unittest.mock import patch
from common_input_protocol import source_identity,digest,BACKENDS,measurement_protocol
from committed_records import atomic_json,atomic_bytes,canonical,read_records,run_bounded
import matched_measurement as runner
import validate_matched_measurement as checker
from development_backend_pilot import trial_batch


class MatchedToolTests(unittest.TestCase):
    def directory(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);return Path(t.name)
    def request(self,stage='calibration'):
        values=list(range(1,9));rules=measurement_protocol()
        return dict(stage=stage,index=0,case=dict(case='mechanical-eight',values=values,input_sha256=digest(values)),
                    rules=rules,batch_size=2 if stage=='formal' else None,gc_thresholds=list(gc.get_threshold()))
    def ticks(self,values,name,expected,batch,clock=None):
        # Real minimal calls; deterministic synthetic durations unrelated to speed.
        ns=(5_000_000 if name==BACKENDS[0] else 8_000_000)*batch
        it=iter((100,100+ns));return trial_batch(values,name,expected,batch,clock=lambda:next(it))
    def run_case(self,out,request,trial=None):
        with patch.object(runner,'trial_batch',side_effect=trial or self.ticks):
            return runner.execute_case(request,out)

    def test_first_common_batch_and_all_output_checks(self):
        out=self.directory()/'case';request=self.request()
        self.assertEqual(self.run_case(out,request),0)
        report=checker.check_job(out,request,passing=True)
        self.assertEqual(report['rows'],12);self.assertEqual(report['result']['chosen_batch'],2)
        self.assertEqual([r['batch_size'] for r in read_records(out)], [1]*6+[2]*6)

    def test_paired_schedule_and_statistics(self):
        out=self.directory()/'case';request=self.request('formal')
        self.assertEqual(self.run_case(out,request),0)
        report=checker.check_job(out,request,passing=True)
        rows=read_records(out);samples=[r for r in rows if r['kind']=='sample']
        self.assertEqual(len(rows),50);self.assertEqual(len(samples),40)
        self.assertEqual(sum(samples[i]['backend']==BACKENDS[0] for i in range(0,40,2)),10)
        self.assertEqual(report['result']['tree_over_list_median'],1.6)
        self.assertEqual(report['result']['groups'][BACKENDS[0]]['iqr_ns_per_call'],0)
        self.assertEqual(checker.percentile([1,2,8,10],.25),1.75)
        self.assertEqual(checker.percentile([1,2,8,10],.75),8.5)

    def test_r7_nonconstant_samples_and_no_trimming(self):
        request=self.request('formal');out=self.directory()/'case';counter={n:0 for n in BACKENDS}
        def varying(values,name,expected,batch,clock=None):
            row=self.ticks(values,name,expected,batch);counter[name]+=1
            row['elapsed_ns']=(counter[name]**2)*batch;return row
        self.assertEqual(self.run_case(out,request,varying),0)
        result=checker.check_job(out,request,passing=True)['result']['groups'][BACKENDS[0]]
        self.assertEqual(result['batches'],20);self.assertEqual(result['median_ns_per_call'],240.5)
        self.assertEqual(result['q25_ns_per_call'],115.75);self.assertEqual(result['q75_ns_per_call'],410.25)

    def test_failed_output_and_serialization_are_committed(self):
        for kind in ('bad-output','serialization'):
            out=self.directory()/'case';calls=[0]
            def bad(values,name,expected,batch,clock=None):
                calls[0]+=1;row=self.ticks(values,name,expected,batch)
                if calls[0]==2:
                    if kind=='serialization':row['outputs']=object()
                    else:row.update(status='ERROR',error={'type':'ValueError','message':'bad output'},outputs=[{'output':[99],'output_diagnostic':None}])
                return row
            self.assertEqual(self.run_case(out,self.request(),bad),2)
            rows=read_records(out);self.assertEqual(len(rows),2);self.assertEqual(rows[-1]['status'],'ERROR')
            self.assertFalse(checker.check_job(out,self.request(),passing=False)['full'])
            if kind=='serialization':self.assertEqual(rows[-1]['error']['type'],'SerializationError')

    def test_no_batch_reaches_threshold_is_failure(self):
        out=self.directory()/'case';request=self.request();request['rules']['calibration']['batch_candidates']=[1]
        self.assertEqual(self.run_case(out,request),2)
        self.assertFalse(checker.check_job(out,request,passing=False)['full'])
        with self.assertRaises(ValueError):checker.check_job(out,request,passing=True)

    def test_row_and_summary_tampering_rejected(self):
        original=self.directory()/'case';request=self.request('formal');self.run_case(original,request)
        for kind in ('order','batch','count-bool','clock','output','drop','stats'):
            out=self.directory()/'case';shutil.copytree(original,out)
            if kind=='drop':(out/'records/000049.json.gz').unlink()
            elif kind=='stats':
                value=runner.read(out/'summary.json');value['result']['tree_over_list_median']=1;atomic_json(out/'summary.json',value)
            else:
                path=out/'records/000010.json.gz';row=json.loads(gzip.decompress(path.read_bytes()))
                if kind=='order':row['round']=1
                elif kind=='batch':row['batch_size']=4
                elif kind=='count-bool':row['completed_calls']=True
                elif kind=='clock':row['elapsed_ns']=0
                elif kind=='output':row['outputs'][0]['output']=[99]
                atomic_bytes(path,gzip.compress(canonical(row),mtime=0))
            with self.subTest(kind=kind),self.assertRaises(ValueError):checker.check_job(out,request,passing=True)

    def test_actual_termination_preserves_earlier_batch(self):
        root=self.directory();out=root/'case';request=self.request();atomic_json(root/'request.json',request)
        script=root/'worker.py';script.write_text('''import sys,time,json
from pathlib import Path
sys.path[:0]=[str(Path(sys.argv[1])/'src'),str(Path(sys.argv[1])/'experiments')]
import matched_measurement as r
real=r.trial_batch
calls=0
def trial(*a,**k):
 global calls
 calls+=1
 if calls==2:time.sleep(30)
 return real(*a,**k)
r.trial_batch=trial
raise SystemExit(r.execute_case(json.loads(Path(sys.argv[2]).read_text()),Path(sys.argv[3])))
''')
        self.assertEqual(run_bounded([sys.executable,str(script),str(ROOT),str(root/'request.json'),str(out)],out,2),2)
        self.assertEqual(len(read_records(out)),1);failure=runner.read(out/'failure.json')
        self.assertEqual(failure['status'],'RESOURCE_TIMEOUT');self.assertEqual(failure['current']['record_index'],1)
        self.assertFalse(checker.check_job(out,request,passing=False)['full'])

    def fixture_scope(self,root):
        stack=ExitStack();selection=dict(cases=[dict(spec={'case':'mechanical-eight'},values=list(range(1,9)),input_sha256=digest(list(range(1,9))))],selection_sha256='fixture-selection')
        env=runner.capture_environment();env['execution']['dirty']=False
        qualification=root/'q';qualification.mkdir();atomic_json(qualification/'environment.json',env['execution']);atomic_json(qualification/'manifest.json',{})
        binding=dict(producing_head=env['execution']['head'],selection_sha256=selection['selection_sha256'],archive_manifest_sha256=digest({}),
                     production_sources_identical=True,current_production_sha256={p:h for p,h in source_identity().items() if p.startswith('src/')})
        stack.enter_context(patch.object(runner,'frozen_selection',return_value=selection));stack.enter_context(patch.object(checker,'frozen_selection',return_value=selection))
        stack.enter_context(patch.object(runner,'qualify_binding',return_value=binding));stack.enter_context(patch.object(runner,'capture_environment',return_value=env))
        stack.enter_context(patch.object(checker,'validate_qualification',return_value={'all_selected_qualified':True,'selection_sha256':selection['selection_sha256']}))
        stack.enter_context(patch('validate_common_qualification_v2.validate_revision'))
        def worker(command,output,seconds):
            req=runner.read(Path(command[command.index('--worker')+1]));code=self.run_case(output,req)
            if code:atomic_json(output/'failure.json',dict(status='WORKER_ERROR',accepted=False,performance_eligible=False,committed_records=len(read_records(output))))
            return code
        stack.enter_context(patch.object(runner,'run_bounded',side_effect=worker))
        return stack,qualification,env

    def test_full_controller_and_independent_archive_rebuild_fixture(self):
        root=self.directory();scope,q,env=self.fixture_scope(root)
        review=dict(schema='representation_locality_cost_review_v1',approved=True,
                    production_sha256={p:h for p,h in source_identity().items() if p.startswith('src/')},review_references=['TEST STUB ONLY; no proof reviewed'])
        with scope:
            self.assertTrue(runner.run(root/'cal','calibration','common',q))
            self.assertEqual(checker.validate(root/'cal',qualification=q)['batch_sizes'],{'mechanical-eight':2})
            with self.assertRaises(ValueError):runner.run(root/'forbidden','formal','common',q,calibration=root/'cal')
            self.assertFalse((root/'forbidden').exists())
            self.assertTrue(runner.run(root/'paired','formal','common',q,calibration=root/'cal',review=review))
            report=checker.validate(root/'paired',qualification=q,calibration=root/'cal')
            self.assertTrue(report['complete']);self.assertFalse(report['performance_eligible'])
            (root/'paired'/'extra').mkdir();runner.seal(root/'paired')
            with self.assertRaises(ValueError):checker.validate(root/'paired',qualification=q,calibration=root/'cal')

    def test_full_controller_rejects_zero_exit_without_evidence(self):
        root=self.directory();scope,q,env=self.fixture_scope(root)
        def empty(command,out,seconds):
            out.mkdir();atomic_json(out/'progress.json',dict(status='COMPLETE',committed_records=0));return 0
        with scope,patch.object(runner,'run_bounded',side_effect=empty):
            self.assertFalse(runner.run(root/'cal','calibration','common',q))
            report=checker.validate(root/'cal',qualification=q)
            self.assertFalse(report['complete']);self.assertEqual(report['batch_sizes'],{})

    def test_full_controller_failure_record_reconstruction(self):
        root=self.directory();scope,q,env=self.fixture_scope(root)
        def broken(command,out,seconds):
            request=runner.read(Path(command[command.index('--worker')+1]));calls=[0]
            def bad(*args,**kw):
                calls[0]+=1
                if calls[0]==2:raise RuntimeError('injected later batch failure')
                return self.ticks(*args,**kw)
            code=self.run_case(out,request,bad)
            atomic_json(out/'failure.json',dict(status='WORKER_ERROR',accepted=False,performance_eligible=False,
                        committed_records=len(read_records(out)),current=runner.read(out/'progress.json')))
            return code
        with scope,patch.object(runner,'run_bounded',side_effect=broken):
            self.assertFalse(runner.run(root/'cal','calibration','common',q))
            report=checker.validate(root/'cal',qualification=q);self.assertFalse(report['complete'])
            rows=read_records(root/'cal/jobs/mechanical-eight');self.assertEqual([r['status'] for r in rows],['PASS','ERROR'])

    def test_resealed_environment_and_calibration_corruption_rejected(self):
        root=self.directory();scope,q,env=self.fixture_scope(root)
        with scope:
            self.assertTrue(runner.run(root/'cal','calibration','common',q))
            for kind in ('environment','source','decision','configuration'):
                out=root/kind;shutil.copytree(root/'cal',out)
                if kind in ('environment','source'):
                    value=runner.read(out/'environment.json')
                    if kind=='environment':value['clock']['monotonic']=False
                    else:value['execution']['source_sha256']['src/paper_jordan.py']='0'*64
                    atomic_json(out/'environment.json',value)
                elif kind=='decision':
                    value=runner.read(out/'jobs/mechanical-eight/summary.json');value['result']['chosen_batch']=4
                    atomic_json(out/'jobs/mechanical-eight/summary.json',value)
                else:
                    value=runner.read(out/'config.json');value['rules']['calibration']['target_batch_ns']=1
                    atomic_json(out/'config.json',value)
                runner.seal(out)
                with self.subTest(kind=kind),self.assertRaises(ValueError):checker.validate(out,qualification=q)

    def test_manual_receipt_does_not_accept_wrong_source_or_missing_review(self):
        for value in (None,{},dict(schema='representation_locality_cost_review_v1',approved=True,production_sha256={},review_references=['stub'])):
            with self.assertRaises(ValueError):checker.check_review(value,source_identity())

    def test_optimization_guards(self):
        for script in ('matched_measurement.py','validate_matched_measurement.py'):
            result=subprocess.run([sys.executable,'-O',str(ROOT/'experiments'/script),'--help'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('optimization level 0',result.stderr)


if __name__=='__main__':unittest.main()
