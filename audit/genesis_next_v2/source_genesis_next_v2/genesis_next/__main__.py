from __future__ import annotations
# Set before importing NumPy / torch, only in this new process.
import os
os.environ['OMP_NUM_THREADS']='2'
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['MKL_NUM_THREADS']='2'
os.environ['NUMEXPR_NUM_THREADS']='2'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import sys
sys.dont_write_bytecode=True
from .cli import main
raise SystemExit(main())
