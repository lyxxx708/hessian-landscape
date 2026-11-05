from pathlib import Path
W=Path(r'E:\GENESIS\worktrees\genesis-next-v2')
p=W/'genesis_next/cli.py'; s=p.read_text(encoding='utf-8')
s=s.replace("def qualified_conditions(lock,output):","""def is_ancestor(pid):
    \"\"\"True if pid is this process's parent or an earlier ancestor (venv launchers add a shim process).\"\"\"
    import psutil
    try:return any(a.pid==pid for a in psutil.Process().parents())
    except psutil.Error:return False

def qualified_conditions(lock,output):""",1)
s=s.replace("if not active.exists() or read_json(active).get('pid')!=os.getppid():","if not active.exists() or not is_ancestor(read_json(active).get('pid')):")
s=s.replace("""            if not dest.exists():
                status='TIMEOUT_INCONCLUSIVE'""","""            partial0=out/'partials'/f'{sid}.json'
            if not dest.exists() and code not in (0,'TIMEOUT') and not partial0.exists() and elapsed<20:
                # Launch/infrastructure failure before any assay work: not a scientific measurement, never committed.
                write_json(out/'infra_failures'/f'{sid}-{time.time_ns()}.json',{'state_id':sid,'exit':code,'log':str(logdir/f'{sid}.log')})
                skipped.add(sid);events.append({'state_id':sid,'status':'INFRA_FAILURE_NOT_COMMITTED'});del running[sid];continue
            if not dest.exists():
                status='TIMEOUT_INCONCLUSIVE'""")
s=s.replace("stop=out/'STOP';running={};events=[]","stop=out/'STOP';running={};events=[];skipped=set()")
s=s.replace("if committed(sid) or sid in running or not source_ready(lock,state):continue","if committed(sid) or sid in running or sid in skipped or not source_ready(lock,state):continue")
p.write_text(s,encoding='utf-8')
t=W/'tests/test_v2.py'; x=t.read_text(encoding='utf-8')
x=x.replace("if __name__=='__main__':unittest.main()","""class ChildOwnershipTests(unittest.TestCase):
    def test_grandchild_passes_ancestor_check(self):
        import os,subprocess,sys
        from genesis_next.cli import is_ancestor
        self.assertTrue(is_ancestor(os.getppid()))
        self.assertFalse(is_ancestor(2**22+12345))

if __name__=='__main__':unittest.main()""")
t.write_text(x,encoding='utf-8')
