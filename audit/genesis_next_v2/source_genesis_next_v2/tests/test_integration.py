"""Integration fixtures emulate file/API schemas, not real GENESIS checkpoints."""
import csv,json,tempfile,subprocess,sys,os,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
from types import ModuleType,SimpleNamespace
import numpy as np
import torch
from torch import nn

PACKAGE=Path(__file__).resolve().parents[1]

def put(p,value):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value),encoding='utf-8');return p

def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def fixture(base):
    bundle=base/'bundle';source=bundle/'07_SOURCE/executed_source';source.mkdir(parents=True)
    (source/'x.py').write_text('# synthetic integration fixture\n')
    config=json.loads((PACKAGE/'configs/protocol.json').read_text());runs=[]
    for sid in config['settings']:
        fam='dln' if sid.startswith('dln') else 'mlp' if sid.startswith('mlp') else 'resnet' if sid.startswith('resnet') else 'transformer'
        for si in config['seed_indices']:
            runs.append({'run_id':f's1-{sid}-{si}','setting_id':sid,'stage':'s1','seed_index':si,
                         'seed':9007199254740993+len(runs),'model':{'family':fam}})
    lock={'protocol_sha':'fixture','runs':runs,'source':{'files':[{'path':'x.py','sha256':h(source/'x.py'),'bytes':(source/'x.py').stat().st_size}]}}
    lp=put(bundle/'01_PROTOCOL/protocol_lock/protocol-lock.json',lock)
    live=base/'live';live.mkdir();(live/'protocol-lock.json').write_bytes(lp.read_bytes())
    rows=[];audits=[]
    for si in range(2):
        for ck in [1,2,3]:
            for gamma in [.01,.1]:
                job=f'{si}-{ck}-{gamma}';d=.12 if gamma==.01 else .03
                rows.append({'job_id':job,'stage':'s1','setting_id':'A','seed':str(9007199254740993+si),'seed_index':si,
                  'checkpoint_index':ck,'gamma':gamma,'schema':'coarse','state':'COMPLETE','target_delta':d,
                  'log10_grad':0,'short_gain_over_g2':.99,'matched_gain_over_g2':1})
                audits.append({'job_id':job,'setting':'A','seed_index':si,'checkpoint':ck,'gamma':gamma,'schema':'coarse',
                  'class':'AGREE','v2_F_star':1,'v2_delta':d,'ref_delta':d,'v2_E_task':.1,'ref_E_task':.1,'v2_E_val':.2,'ref_E_val':.2})
    f=bundle/'03_SCIENTIFIC_DATA/prediction/DERIVED_predictor_feature_table.csv';f.parent.mkdir(parents=True)
    with f.open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    a=bundle/'04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_rows.jsonl';a.parent.mkdir(parents=True)
    a.write_text('\n'.join(json.dumps(r) for r in audits)+'\n')
    files=[p for p in bundle.rglob('*') if p.is_file()];m=bundle/'09_MANIFEST/FILE_MANIFEST_SHA256.csv';m.parent.mkdir(parents=True)
    with m.open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=['path','bytes','sha256','on_github']);w.writeheader()
        w.writerows({'path':str(p.relative_to(bundle)),'bytes':p.stat().st_size,'sha256':h(p),'on_github':'yes'} for p in files)
    return bundle,live

class CLIIntegration(unittest.TestCase):
    def test_inspect_plan_freeze_reproduce_and_immutability(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);bundle,live=fixture(root);out=root/'out'
            before={str(p):h(p) for p in root.rglob('*') if p.is_file()}
            for cmd in ['inspect','plan','freeze','reproduce','freeze']:
                r=subprocess.run([sys.executable,'-B','-m','genesis_next',cmd,'--bundle',str(bundle),'--run-root',str(live),'--out',str(out)],cwd=PACKAGE,capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stderr)
            lock=json.loads((out/'FOLLOWUP_LOCK.json').read_text());self.assertEqual(lock['plan']['state_count'],80)
            report=next((out/'e0').glob('*/summary.json'));summary=json.loads(report.read_text())
            self.assertEqual(summary['paired_seed_n'],2);self.assertEqual(summary['pairs_positive'],2)
            for p,sha in before.items():self.assertEqual(h(Path(p)),sha)

    def test_tampered_manifest_rejected(self):
        from genesis_next.io_utils import verify_bundle
        with tempfile.TemporaryDirectory() as d:
            b,_=fixture(Path(d));(b/'07_SOURCE/executed_source/x.py').write_text('not the same')
            self.assertEqual(verify_bundle(b)['status'],'FAIL')

    def test_internal_child_cannot_start_standalone(self):
        r=subprocess.run([sys.executable,'-B','-m','genesis_next','_child','--out','/not-present',
                          '--state-id','x','--device','cpu','--approve-compute'],cwd=PACKAGE,capture_output=True,text=True)
        self.assertEqual(r.returncode,2);self.assertIn('exclusive parent',r.stderr)

class Toy(nn.Module):
    def __init__(self):
        super().__init__();self.layers=nn.ModuleList([nn.Linear(2,2,bias=False),nn.Linear(2,1,bias=False)])
        with torch.no_grad():
            self.layers[0].weight.copy_(torch.tensor([[.8,.2],[-.1,.6]]));self.layers[1].weight.copy_(torch.tensor([[.3,-.7]]))
    def forward(self,x):return self.layers[1](self.layers[0](x))

class ToyOp:
    def __init__(self,model,inputs,targets,loss,*,microbatch=None,dtype=None):
        import copy
        self.model=copy.deepcopy(model).to(dtype=dtype or next(model.parameters()).dtype)
        self.theta=torch.cat([p.detach().flatten() for p in self.model.parameters()])
        self.inputs=inputs.to(dtype=self.theta.dtype);self.targets=targets.to(dtype=self.theta.dtype)
        self.loss=loss;self.microbatch=microbatch or len(inputs);self.buffers={};self.matvec_count=0
        entries=[];start=0
        for name,p in self.model.named_parameters():
            entries.append(SimpleNamespace(name=name,start=start,stop=start+p.numel(),shape=p.shape));start+=p.numel()
        self.layout=SimpleNamespace(entries=entries,group_indices=lambda schema='coarse',device=None:[torch.arange(e.start,e.stop,device=device) for e in entries])
        self.prediction=self.forward(self.theta).detach();self.identity={'dtype':str(self.theta.dtype),'fixture':True}
    def forward(self,t):
        from torch.func import functional_call
        params={e.name:t[e.start:e.stop].reshape(e.shape) for e in self.layout.entries}
        return functional_call(self.model,params,(self.inputs,))
    def objective(self,t):return ((self.forward(t)-self.targets)**2).mean()/2
    def gradient(self):
        t=self.theta.clone().requires_grad_();return torch.autograd.grad(self.objective(t),t)[0].detach()
    def raw_ggn(self,v):
        J=torch.autograd.functional.jacobian(lambda t:self.forward(t).reshape(-1),self.theta)
        self.matvec_count+=1;return (J.T@(J@v)/self.prediction.numel()).detach()
    def matvec(self,v,damping=0):return self.raw_ggn(v)+damping*v
    def block_matvec(self,i,u,damping=0,schema='coarse'):
        idx=self.layout.group_indices()[i];v=torch.zeros_like(self.theta);v[idx]=u
        return self.raw_ggn(v)[idx]+damping*u

def toy_dense(op,with_hessian=True,**kwargs):
    J=torch.autograd.functional.jacobian(lambda t:op.forward(t).reshape(-1),op.theta)
    return {'G':J.T@J/op.prediction.numel(),'H':torch.autograd.functional.hessian(op.objective,op.theta),
            'gradient':op.gradient(),'J':J}

class AssayContractIntegration(unittest.TestCase):
    def test_complete_assay_against_small_torch_oracle(self):
        from genesis_next.io_utils import object_digest
        from genesis_next.assay import assay_state
        cfg=json.loads((PACKAGE/'configs/protocol.json').read_text());cfg.update(cg_steps=[1,2,4,8],max_iterations=100)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);live=root/'live';out=root/'out';src=root/'source';src.mkdir()
            run={'run_id':'s1-toy','stage':'s1','seed_index':1,'seed':123,'setting_id':'dln_toy','model':{'family':'dln'}}
            state={'state_id':'fixture-state','run':run,'checkpoint_index':3}
            orig={'protocol_sha':'test','config':{'damping_floor':1e-8,'line_search':[0.,.1,1.]}}
            put(live/'protocol-lock.json',orig);put(live/'checkpoints/s1-toy/training_receipt.json',{'status':'COMPLETE'})
            for gamma in cfg['gammas']:
                jid=object_digest(['test','s1-toy',3,gamma,'coarse','measure'])
                put(live/'measurements'/jid/'result.json',{'job_id':jid,'gamma':gamma,'schema':'coarse',
                  'provenance':{'stage':'s1','run_id':'s1-toy','checkpoint_index':3,'checkpoint_integrity_sha':'checkpoint'},
                  'spectral_scale':{'value':1.},'utility':{'status':'NUMERIC_VALID','delta':.1}})
            def rebuild(payload,c,root):
                dtype=getattr(torch,c['analysis_dtype']);x=torch.tensor([[.10000000007,.5],[.4,.20000000003],[-.3,.8]],dtype=torch.float64)
                y=torch.tensor([[.1],[-.2],[.3]],dtype=torch.float64)
                op=ToyOp(Toy(),x.to(dtype),y.to(dtype),'mse',dtype=dtype)
                pv={'model_spec':{'family':'dln'},'run_id':'s1-toy','setting_id':'dln_toy','seed':123,'stage':'s1',
                    'seed_index':1,'checkpoint_index':3,'checkpoint_integrity_sha':'checkpoint'}
                return op,ToyOp(Toy(),x.to(dtype),y.to(dtype),'mse',dtype=dtype),pv
            mods={}
            for n in ['genesis_gpu','genesis_gpu.runtime','genesis_gpu.runtime.measurement','genesis_gpu.curvature',
                      'genesis_gpu.curvature.operators','genesis_gpu.audit','genesis_gpu.audit.independent_reference','genesis_gpu.contracts']:
                mods[n]=ModuleType(n)
            mods['genesis_gpu.runtime.measurement'].rebuild_snapshot=rebuild
            mods['genesis_gpu.curvature.operators'].FrozenOperator=ToyOp
            mods['genesis_gpu.audit.independent_reference'].dense_reference=toy_dense
            mods['genesis_gpu.audit.independent_reference'].independent_ggn_vector=lambda op,v:op.raw_ggn(v)
            mods['genesis_gpu.contracts'].object_sha=object_digest
            lock={'config':cfg,'freeze_sha':'synthetic-freeze','inputs':{'source':str(src),'run_root':str(live)}}
            before={str(p):h(p) for p in live.rglob('*') if p.is_file()}
            with patch.dict(sys.modules,mods):r=assay_state(lock,state,'cpu',out)
            self.assertEqual(r['qualified_condition_n'],3)
            self.assertEqual(len(r['conditions'][0]['gauge']),3)
            self.assertTrue(all(x['status']=='PASS' for c in r['conditions'] for x in c['gauge']))
            self.assertTrue(r['precision']['same_device'])
            self.assertIn('input_quantization_control',r)
            json.dumps(r,allow_nan=False)
            for p,sha in before.items():self.assertEqual(h(Path(p)),sha)

if __name__=='__main__':unittest.main()
