import unittest,tempfile,json,sys
from pathlib import Path
from unittest.mock import patch

class PlanTests(unittest.TestCase):
    def test_plan_is_s1_only_and_does_not_replace_missing(self):
        from genesis_next.planning import make_plan
        cfg={'source_stage':'s1','settings':['A'],'seed_indices':[0,1],'checkpoints':[1,3],'gammas':[.01]}
        lock={'runs':[{'run_id':'s1-a','stage':'s1','setting_id':'A','seed':123,'seed_index':0,'model':{'family':'dln'}},
                      {'run_id':'s1-b','stage':'s1','setting_id':'A','seed':124,'seed_index':1,'model':{'family':'dln'}},
                      {'run_id':'s2-a','stage':'s2','setting_id':'A','seed':125,'seed_index':0,'model':{'family':'dln'}}]}
        p=make_plan(lock,cfg)
        self.assertEqual(len(p['states']),4)
        self.assertTrue(all(x['run']['stage']=='s1' for x in p['states']))
        self.assertEqual(p['condition_count'],4)

    def test_missing_setting_is_not_silently_dropped(self):
        from genesis_next.planning import make_plan
        with self.assertRaises(ValueError):make_plan({'runs':[]},{'source_stage':'s1','settings':['A'],'seed_indices':[0],'checkpoints':[1],'gammas':[.01]})

    def test_s2_config_forbidden(self):
        from genesis_next.planning import make_plan
        with self.assertRaises(ValueError):make_plan({'runs':[]},{'source_stage':'s2','settings':[]})

    def test_source_hash_mismatch_blocks_import(self):
        from genesis_next.planning import verify_source
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'x.py').write_text('changed')
            with self.assertRaises(ValueError):verify_source(p,{'source':{'files':[{'path':'x.py','sha256':'0'*64,'bytes':7}]}})

    def test_native_commandline_gates_v2(self):
        from genesis_next.safety import source_processes
        ps=[{'ProcessId':5,'CommandLine':'python -m genesis_gpu pipeline --root E:/GENESIS/runs/genesis_full_v2'},
            {'ProcessId':6,'CommandLine':'python -m genesis_next run'}]
        self.assertEqual(source_processes(ps)[0]['ProcessId'],5)
        self.assertEqual(len(source_processes(ps)),1)

    def test_lock_never_overwrites(self):
        from genesis_next.safety import execution_lock
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            with execution_lock(p):
                with self.assertRaises(RuntimeError):
                    with execution_lock(p):pass
            self.assertFalse((p/'ACTIVE.lock').exists())

    def test_immutable_result_id_collision_is_rejected(self):
        from genesis_next.planning import validate_result_identity
        with self.assertRaises(ValueError):validate_result_identity({'freeze_sha':'x','state_id':'one'},'y','one')

class SummaryTests(unittest.TestCase):
    def test_final_result_not_independent_seed_inflation(self):
        from genesis_next.reporting import summarize_rows
        rows=[]
        for seed in [1,2]:
            for ckpt in [1,3]:
                for gamma in [.01,.1]:
                    rows.append({'setting_id':'A','seed':str(seed),'family':'dln','checkpoint':ckpt,
                                 'gamma':gamma,'status':'QUALIFIED','delta':.1,'matched_gain_ratio':1.,'cg8_gain_ratio':.98})
        out=summarize_rows(rows,bootstrap=100,seed=7)
        self.assertEqual(len(out),2)
        self.assertEqual(out[0]['independent_seed_n'],2)
        self.assertEqual(out[0]['measurement_n'],4)

if __name__=='__main__':unittest.main()

class QualificationIsolationTests(unittest.TestCase):
    def test_cpu_receipt_cannot_qualify_cuda(self):
        from genesis_next.cli import qualified_families
        lock={'freeze_sha':'x','execution_device':'cuda:0','config':{'gammas':[.01],'memory_target_gib':9.5},
              'plan':{'states':[{'state_id':'a','checkpoint_index':3,'run':{'model':{'family':'dln'},'seed_index':1}}]}}
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'results').mkdir()
            (p/'results/a.json').write_text(json.dumps({'freeze_sha':'x','state_id':'a','status':'EXECUTED',
                 'device':'cpu','conditions':[{'status':'QUALIFIED'}]}))
            self.assertEqual(qualified_families(lock,p),[])

    def test_cuda_receipt_requires_memory_measurement(self):
        from genesis_next.cli import qualified_families
        lock={'freeze_sha':'x','execution_device':'cuda:0','config':{'gammas':[.01],'memory_target_gib':9.5},
              'plan':{'states':[{'state_id':'a','checkpoint_index':3,'run':{'model':{'family':'dln'},'seed_index':1}}]}}
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'results').mkdir()
            r={'freeze_sha':'x','state_id':'a','status':'EXECUTED','device':'cuda:0','conditions':[{'status':'QUALIFIED'}]}
            (p/'results/a.json').write_text(json.dumps(r));self.assertEqual(qualified_families(lock,p),[])
            r.update(memory_within_target=True,peak_allocated_gib=1.,peak_reserved_gib=2.)
            (p/'results/a.json').write_text(json.dumps(r));self.assertEqual(qualified_families(lock,p),['dln'])
