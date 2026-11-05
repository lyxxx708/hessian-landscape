import json,tempfile,unittest
from pathlib import Path
from unittest import mock

class V2ExecutionTests(unittest.TestCase):
    def test_cpu_assay_is_not_blocked_by_live_v2_worker(self):
        # v1 refused CPU assays while a v2 worker existed, although CPU work cannot contend for its GPU.
        from genesis_next import safety
        busy=[{'ProcessId':5,'CommandLine':'python -m genesis_gpu --root x pipeline'}]
        with mock.patch.object(safety,'process_inventory',return_value=busy):
            self.assertEqual(safety.require_exclusive('cpu')['gpu_check'],'CPU_ONLY')
            with self.assertRaises(RuntimeError):safety.require_exclusive('cuda:0')

    def test_gamma_qualification_is_per_condition(self):
        # v1 required all three gammas to pass before any state of the family could run.
        from genesis_next.cli import qualified_conditions
        lock={'freeze_sha':'x','execution_device':'cpu','config':{'gammas':[.001,.01,.1],'memory_target_gib':9.5},
              'plan':{'states':[{'state_id':'a','checkpoint_index':3,'run':{'model':{'family':'dln'},'seed_index':1}}]}}
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'results').mkdir()
            r={'freeze_sha':'x','state_id':'a','status':'EXECUTED','device':'cpu','conditions':[
               {'gamma':.001,'status':'QUALIFIED'},{'gamma':.01,'status':'NUMERIC_UNRESOLVED'},{'gamma':.1,'status':'QUALIFIED'}]}
            (p/'results/a.json').write_text(json.dumps(r))
            self.assertEqual(qualified_conditions(lock,p),{('dln',.001),('dln',.1)})

    def test_condition_ledger_covers_every_planned_condition(self):
        from genesis_next.ledger import condition_ledger
        lock={'freeze_sha':'x','config':{'gammas':[.001,.01]},'plan':{'states':[
            {'state_id':'a','checkpoint_index':1,'run':{'model':{'family':'dln'},'setting_id':'s','seed_index':0,'run_id':'r'}}]}}
        rows=condition_ledger(lock,results={},source_ready={'a':False})
        self.assertEqual([r['status'] for r in rows],['SOURCE_NOT_READY']*2)
        rows=condition_ledger(lock,results={'a':{'conditions':[{'gamma':.001,'status':'QUALIFIED'}],'status':'EXECUTED'}},source_ready={'a':True})
        self.assertEqual([r['status'] for r in rows],['NUMERIC_VALID','READY'])

class ChildOwnershipTests(unittest.TestCase):
    def test_grandchild_passes_ancestor_check(self):
        import os,subprocess,sys
        from genesis_next.cli import is_ancestor
        self.assertTrue(is_ancestor(os.getppid()))
        self.assertFalse(is_ancestor(2**22+12345))

if __name__=='__main__':unittest.main()
