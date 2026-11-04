from pathlib import Path
import os
import sys
import platform
import importlib.metadata
import subprocess
import torch
import numpy as np
import psutil
from genesis_gpu.runtime.atomic_io import source_manifest,atomic_json


def configure_determinism():
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True
    torch.backends.cudnn.allow_tf32=False
    torch.backends.cuda.matmul.allow_tf32=False


def code_root():return Path(__file__).resolve().parents[2]


def runtime_abi():
    """Stable software ABI: no free memory, timestamps or changing process state.

    Avoid importing optional torchvision operators merely to read its version.
    A post-freeze library/runtime change requires a new G0 and protocol.
    """
    packages = {}
    for name in ('numpy','scipy','torchvision','safetensors','scikit-learn','PyYAML','pandas'):
        try: packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: packages[name] = None
    result = {'python': platform.python_version(), 'implementation': platform.python_implementation(),
              'torch': str(torch.__version__), 'cuda_runtime': torch.version.cuda,
              'cudnn': torch.backends.cudnn.version(), 'packages': packages,
              'platform': platform.system(), 'machine': platform.machine()}
    if torch.cuda.is_available():
        result['devices'] = [{'name': torch.cuda.get_device_name(i),
                              'capability': list(torch.cuda.get_device_capability(i)),
                              'total_memory': torch.cuda.get_device_properties(i).total_memory}
                             for i in range(torch.cuda.device_count())]
        try:
            proc = subprocess.run(['nvidia-smi','--query-gpu=driver_version','--format=csv,noheader'],
                                  capture_output=True, text=True, timeout=10, check=True)
            result['nvidia_driver'] = sorted(set(proc.stdout.strip().splitlines()))
        except (OSError, subprocess.SubprocessError): result['nvidia_driver'] = 'UNAVAILABLE'
    return result


def environment_receipt(device):
    try:
        git=subprocess.run(['git','rev-parse','HEAD'],cwd=code_root(),capture_output=True,text=True,timeout=5,check=True).stdout.strip()
    except (OSError,subprocess.SubprocessError):git=None
    cuda=torch.cuda.is_available()
    receipt={'python':sys.version,'platform':platform.platform(),'torch':str(torch.__version__),'numpy':np.__version__,
             'cuda_available':cuda,'torch_cuda':torch.version.cuda,'requested_device':str(device),'git_commit':git,
             'runtime_abi':runtime_abi(),'ram_bytes':psutil.virtual_memory().total,'source':source_manifest(code_root()),
             'deterministic_algorithms':torch.are_deterministic_algorithms_enabled()}
    if str(device).startswith('cuda') and cuda:
        p=torch.cuda.get_device_properties(torch.device(device));receipt['gpu']={'name':p.name,'total_memory':p.total_memory,'capability':[p.major,p.minor]}
    return receipt
