import json,csv,hashlib,sys
from pathlib import Path
P=Path(sys.argv[1])
meta={'package':'GENESIS_NEXT_v2_AUDIT','timestamp':'20261106_002250 (Asia/Shanghai)','branch':'audit/genesis-next-v2-20261106_002250','base_branch':'audit/genesis-v2-interim-20261104','base_commit':'629032110fa51affc7f4e96cdb75f0c40070a9fe',
 'related':{'pr15':'https://github.com/lyxxx708/hessian-landscape/pull/15 (unmodified)','original_genesis_v2_root':'E:\GENESIS\runs\genesis_full_v2 (not included, still running)'},
 'freeze_sha':'0c881869d1eb17bb034a7fde8f0868ed7780b324a07b9b90ebe65d0a5c6305bf','executed_source_dir':'source_genesis_next_v2/','source_is_git_repo':False,
 'measurement_records':{'states':38,'conditions':114,'independent_seeds':19,'planned_states':80,'planned_conditions':240},
 'status':'READY_FOR_INDEPENDENT_SCIENTIFIC_AUDIT (pending remote verification, see PR)','evidence_class':'POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION'}
(P/'SNAPSHOT_METADATA.json').write_text(json.dumps(meta,indent=2))
rows=[]
for p in sorted(P.rglob('*')):
    if p.is_file() and p.name!='FILE_MANIFEST_SHA256.csv':rows.append((p.relative_to(P).as_posix(),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()))
with (P/'FILE_MANIFEST_SHA256.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['path','bytes','sha256']);w.writerows(rows)
print(len(rows)+1,sum(r[1] for r in rows))
