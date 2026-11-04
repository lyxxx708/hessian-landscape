"""Explicit portable engineering validation; never a substitute for local CUDA G0."""
from pathlib import Path
import argparse
import os
import subprocess
import sys


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,help='New portable smoke run directory (no scientific evidence)')
    args=parser.parse_args(argv)
    os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
    repo=Path(__file__).resolve().parents[1]
    root=args.root.resolve() if args.root is not None else repo/'local_artifacts'/'cpu_smoke_v2'
    return subprocess.call([sys.executable,'-m','genesis_gpu','--config',str(repo/'configs'/'smoke_v2.yaml'),'--root',str(root),'pipeline'],cwd=repo)


if __name__=='__main__':raise SystemExit(main())
