import importlib.util
from pathlib import Path
import pytest


def installer():
    path=Path(__file__).parents[1]/'scripts'/'install_genesis_v2_overlay.py'
    assert path.exists(),'safe overlay installer missing'
    spec=importlib.util.spec_from_file_location('overlay',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_overlay_preserves_existing_historical_and_rejects_conflict(tmp_path):
    m=installer();source=tmp_path/'source';target=tmp_path/'target'
    (source/'genesis_gpu').mkdir(parents=True);target.mkdir()
    (source/'genesis_gpu'/'core.py').write_text('new module')
    (source/'README_GENESIS_V2.md').write_text('guide')
    (target/'AGENTS.md').write_text('existing policy');(target/'README.md').write_text('old evidence')
    m.install(source,target,apply=True,portable_test=True)
    assert (target/'AGENTS.md').read_text()=='existing policy'
    assert (target/'README.md').read_text()=='old evidence'
    assert (target/'genesis_gpu'/'core.py').read_text()=='new module'
    (source/'genesis_gpu'/'core.py').write_text('changed module')
    with pytest.raises(FileExistsError):m.install(source,target,apply=True,portable_test=True)
    assert (target/'genesis_gpu'/'core.py').read_text()=='new module'


def test_overlay_idempotent_and_blocks_symlink_escape(tmp_path):
    m=installer();source=tmp_path/'source';target=tmp_path/'target';outside=tmp_path/'outside'
    (source/'genesis_gpu').mkdir(parents=True);target.mkdir();outside.mkdir()
    (source/'genesis_gpu'/'core.py').write_text('safe')
    try:
        (target/'genesis_gpu').symlink_to(outside,target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f'Creating a directory symlink requires Windows Developer Mode or privilege: {exc}')
    with pytest.raises(ValueError):m.install(source,target,apply=True,portable_test=True)
    assert not (outside/'core.py').exists()
    (target/'genesis_gpu').unlink()
    m.install(source,target,apply=True,portable_test=True)
    r=m.install(source,target,apply=True,portable_test=True)
    assert r['copied']==0 and r['identical']>=1


def test_windows_entrypoints_keep_e_storage_and_never_kill_unrelated():
    root=Path(__file__).parents[1]/'scripts'
    for name in ['genesis_env.ps1','genesis_bootstrap.ps1','genesis_launch.ps1','genesis_status.ps1','genesis_resume.ps1','genesis_stop.ps1']:
        text=(root/name).read_text()
        assert 'genesis_env.ps1' in text or name=='genesis_env.ps1'
        assert 'Stop-Process' not in text and 'taskkill' not in text
    text=(root/'genesis_env.ps1').read_text()
    assert '[EnvironmentVariableTarget]::Process' in text
    assert 'E:' in text


def test_cpu_smoke_launcher_root_flag_is_real(tmp_path):
    import subprocess,sys
    root=Path(__file__).parents[1]
    completed=subprocess.run([sys.executable,str(root/'scripts'/'run_cpu_smoke.py'),'--help'],capture_output=True,text=True,timeout=15)
    assert completed.returncode==0
    assert '--root' in completed.stdout


def test_overlay_includes_only_new_workflow(tmp_path):
    m=installer();source=tmp_path/'s';target=tmp_path/'t'
    (source/'.github'/'workflows').mkdir(parents=True);target.mkdir()
    (source/'.github'/'workflows'/'genesis-v2-cpu.yml').write_text('name: new v2 workflow')
    (source/'.github'/'workflows'/'old.yml').write_text('do not copy')
    m.install(source,target,apply=True,portable_test=True)
    assert (target/'.github'/'workflows'/'genesis-v2-cpu.yml').exists()
    assert not (target/'.github'/'workflows'/'old.yml').exists()


def test_windows_install_and_launcher_guard_reparse_bulk_parents():
    root=Path(__file__).parents[1]/'scripts'
    bootstrap=(root/'genesis_bootstrap.ps1').read_text()
    launcher=(root/'genesis_launch.ps1').read_text()
    assert 'Assert-NoReparseParent $Repo' in bootstrap
    assert 'Assert-NoReparseParent $VenvParent' in bootstrap
    assert 'Assert-NoReparseParent $RunParent' in launcher
