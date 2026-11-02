"""Single-writer SQLite work ledger; terminal evidence is immutable."""
from __future__ import annotations
from pathlib import Path
import json
import os
import sqlite3
import time
import psutil
from genesis_gpu.contracts import object_sha


TERMINAL={'COMPLETE','NUMERIC_UNRESOLVED','FAILED','BLOCKED'}


class JobStore:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path,timeout=30,isolation_level=None)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, stage TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,
            dependencies TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'PENDING', ordinal INTEGER NOT NULL,
            pid INTEGER, process_started REAL, heartbeat REAL, attempts INTEGER NOT NULL DEFAULT 0,
            result TEXT, updated REAL NOT NULL)''')
        self.db.execute('CREATE INDEX IF NOT EXISTS stage_state ON jobs(stage,state,ordinal)')
        self.pid=os.getpid();self.started=psutil.Process(self.pid).create_time()

    def close(self):self.db.close()

    def enqueue(self,id,stage,kind,payload,dependencies):
        payload=json.dumps(payload,sort_keys=True,allow_nan=False);deps=json.dumps(dependencies)
        old=self.db.execute('SELECT * FROM jobs WHERE id=?',(id,)).fetchone()
        if old:
            if old['stage']!=stage or old['kind']!=kind or old['payload']!=payload or old['dependencies']!=deps:
                raise RuntimeError('Work ID reused with different inputs')
            return False
        ordinal=self.db.execute('SELECT COALESCE(MAX(ordinal),0)+1 FROM jobs').fetchone()[0]
        self.db.execute('INSERT INTO jobs(id,stage,kind,payload,dependencies,ordinal,updated) VALUES(?,?,?,?,?,?,?)',
                        (id,stage,kind,payload,deps,ordinal,time.time()))
        return True

    def claim(self,stage):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            candidates=self.db.execute("SELECT * FROM jobs WHERE stage=? AND state IN ('PENDING','INTERRUPTED') ORDER BY ordinal",(stage,)).fetchall()
            chosen=None
            for row in candidates:
                deps=json.loads(row['dependencies'])
                states=[self.db.execute('SELECT state FROM jobs WHERE id=?',(d,)).fetchone() for d in deps]
                if any(s is None for s in states):continue
                if any(s[0] in {'FAILED','BLOCKED','NUMERIC_UNRESOLVED'} for s in states):
                    self.db.execute("UPDATE jobs SET state='BLOCKED',result=?,updated=? WHERE id=?",
                                    (json.dumps({'reason':'DEPENDENCY_NOT_VALID'}),time.time(),row['id']))
                    continue
                if not all(s[0]=='COMPLETE' for s in states):continue
                chosen=row;break
            if chosen:
                self.db.execute("UPDATE jobs SET state='RUNNING',pid=?,process_started=?,heartbeat=?,updated=?,attempts=attempts+1 WHERE id=?",
                                (self.pid,self.started,time.time(),time.time(),chosen['id']))
            self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
        if not chosen:return None
        row=dict(self.db.execute('SELECT * FROM jobs WHERE id=?',(chosen['id'],)).fetchone())
        row['payload']=json.loads(row['payload']);row['dependencies']=json.loads(row['dependencies'])
        return row

    def heartbeat(self,id):
        self.db.execute("UPDATE jobs SET heartbeat=?,updated=? WHERE id=? AND pid=? AND state='RUNNING'",(time.time(),time.time(),id,self.pid))

    def finish(self,id,state,result):
        if state not in TERMINAL|{'INTERRUPTED'}:raise ValueError('Invalid terminal state')
        row=self.db.execute('SELECT * FROM jobs WHERE id=?',(id,)).fetchone()
        if row is None or row['state']!='RUNNING' or row['pid']!=self.pid:
            raise RuntimeError('Cannot overwrite completed or unowned work')
        self.db.execute('UPDATE jobs SET state=?,result=?,updated=? WHERE id=?',
                        (state,json.dumps(result,sort_keys=True,allow_nan=False),time.time(),id))

    def interrupt_owned(self):
        self.db.execute("UPDATE jobs SET state='INTERRUPTED',updated=? WHERE state='RUNNING' AND pid=? AND process_started=?",
                        (time.time(),self.pid,self.started))

    def recover_interrupted(self,force_dead_only=True):
        changed=0
        for row in self.db.execute("SELECT * FROM jobs WHERE state='RUNNING'").fetchall():
            alive=False
            try:
                p=psutil.Process(row['pid']);alive=abs(p.create_time()-row['process_started'])<.1 and p.status()!=psutil.STATUS_ZOMBIE
            except (psutil.NoSuchProcess,psutil.AccessDenied):
                # AccessDenied is conservatively treated as alive.
                alive=psutil.pid_exists(row['pid'])
            if not alive:
                self.db.execute("UPDATE jobs SET state='INTERRUPTED',updated=? WHERE id=?",(time.time(),row['id']));changed+=1
        return changed

    def rows(self,stage=None):
        query='SELECT * FROM jobs'+(' WHERE stage=?' if stage else '')+' ORDER BY ordinal'
        rows=self.db.execute(query,(stage,) if stage else ()).fetchall()
        result=[]
        for row in rows:
            r=dict(row)
            for key in ('payload','dependencies','result'):
                if r[key] is not None:r[key]=json.loads(r[key])
            result.append(r)
        return result

    def counts(self,stage=None):
        counts={}
        for row in self.rows(stage):counts[row['state']]=counts.get(row['state'],0)+1
        return counts

    def stage_complete(self,stage):
        rows=self.rows(stage)
        return bool(rows) and all(r['state'] in TERMINAL for r in rows)

    def evidence_digest(self,stage):
        return object_sha([{'id':r['id'],'state':r['state'],'result':r['result']} for r in self.rows(stage)])
