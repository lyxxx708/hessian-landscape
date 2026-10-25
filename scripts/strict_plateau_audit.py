"""Strict historical plateau audit: NO unsafe pickle loading.

Input: verified raw inverse matrix NPZ (with explicit array key) OR NxN CSV of
block Frobenius norms. Default metric matches GENESIS's ordered layer-pair
block-RMS and squared-energy mass. The historical source identity must be
confirmed separately; this tool does NOT certify provenance.

Examples:
 python -m scripts.strict_plateau_audit --claims-only
 python -m scripts.strict_plateau_audit --npz original_raw.npz --key R --block-sizes 100,100,100,100,100,100,100,100,100,100,100,100
 python -m scripts.strict_plateau_audit --block-norms-csv original_R_block_norms.csv
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def block_norms(matrix, sizes):
    a = np.asarray(matrix)
    sizes = [int(x) for x in sizes]
    if a.ndim != 2 or a.shape[0] != a.shape[1] or a.shape[0] != sum(sizes):
        raise ValueError("matrix dimension must equal sum(block sizes)")
    if not np.isfinite(a).all():
        raise ValueError("matrix has nonfinite entries")
    limits = np.cumsum([0, *sizes])
    return np.array([[np.linalg.norm(a[limits[i]:limits[i+1],limits[j]:limits[j+1]], "fro")
                      for j in range(len(sizes))] for i in range(len(sizes))])


def audit_norms(norms):
    a = np.asarray(norms, dtype=np.float64)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or not len(a):
        raise ValueError("block norms must be a nonempty square array")
    if not np.isfinite(a).all() or (a < 0).any():
        raise ValueError("block norms must be finite and nonnegative")
    L = len(a)
    energy = np.square(a)
    bin_energy = np.array([sum(energy[i, j] for i in range(L)
                               for j in range(L) if abs(i-j) == k)
                           for k in range(L)])
    counts = np.array([L if k == 0 else 2*(L-k) for k in range(L)])
    total = float(bin_energy.sum())
    if total == 0 or bin_energy[0] == 0:
        raise ValueError("zero energy or zero diagonal-block energy")
    rms = np.sqrt(bin_energy / counts)
    rel = rms / rms[0]
    mass = bin_energy / total
    offdiag = float(1-mass[0])
    max_ratio = float(max(rel[1:], default=0))
    maxbound = (L-1)*max_ratio**2/(1+(L-1)*max_ratio**2)
    if offdiag > maxbound + 1e-10:
        raise AssertionError("block-mass consistency bound violated")
    return {
        "layers": L, "pair_counts_by_distance": counts.tolist(),
        "block_rms_by_distance": rms.tolist(),
        "normalized_rms_by_distance": rel.tolist(),
        "energy_mass_by_distance": mass.tolist(),
        "offdiag_energy_mass": offdiag,
        "tail_energy_mass_k_ge_4": float(sum(mass[4:])),
        "sum_mass_error": float(abs(sum(mass)-1)),
        "block_norm_transpose_relative": float(np.linalg.norm(a-a.T) /
                                                max(np.linalg.norm(a), 1e-300)),
        "offdiag_upper_bound_from_observed_max_ratio": maxbound
    }


def claim_bounds(layers=12, min_ratio=.09, max_ratio=.12, reported_mass=.39):
    """All nonzero distance-bin normalized block RMS in [min_ratio,max_ratio]."""
    L = layers
    if L <= 1 or min_ratio < 0 or max_ratio < min_ratio or not (0 < reported_mass < 1):
        raise ValueError("invalid parameters")
    n_off = L*(L-1)
    def mass(c):
        z=(L-1)*c*c
        return z/(1+z)
    required_max = np.sqrt(reported_mass/((1-reported_mass)*(L-1)))
    n1 = 2*(L-1)
    nfar = n_off-n1
    required_near = np.sqrt(max(0.,(L*reported_mass/(1-reported_mass)-nfar*max_ratio**2)/n1))
    ntail=sum(2*(L-k) for k in range(4,L))
    tail_upper=(ntail*max_ratio**2)/(L+ntail*max_ratio**2)
    return {
        "L": L, "assumed_all_k_ge_1_between": [min_ratio, max_ratio],
        "reported_offdiag": reported_mass,
        "compatible_offdiag_min": mass(min_ratio),
        "compatible_offdiag_max": mass(max_ratio),
        "reported_mass_compatible": bool(mass(min_ratio)-1e-12 <= reported_mass <= mass(max_ratio)+1e-12),
        "necessary_max_ratio_for_reported_mass": float(required_max),
        "necessary_adjacent_ratio_if_k_ge_2_at_most_max_ratio": float(required_near),
        "max_tail_k_ge_4_mass_if_every_ratio_at_most_max_ratio": float(tail_upper),
    }


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group()
    group.add_argument("--npz")
    group.add_argument("--block-norms-csv")
    group.add_argument("--claims-only", action="store_true")
    p.add_argument("--key",default="R",help="explicit NPZ array key (e.g. inverse_damped_H)")
    p.add_argument("--block-sizes",default=",".join(["100"]*12))
    p.add_argument("--json-out",default=None)
    args=p.parse_args()
    report={"status":"CLAIMS_ONLY_NO_ORIGINAL_MATRIX",
            "claim_consistency":claim_bounds()}
    if args.npz or args.block_norms_csv:
        path=Path(args.npz or args.block_norms_csv)
        if path.suffix.lower() in {".pkl",".pickle",".pt",".pth"}:
            raise ValueError("Unsafe deserialization refused; convert source in a trusted isolated environment.")
        if args.npz:
            with np.load(path,allow_pickle=False) as z:
                if args.key not in z.files:
                    raise KeyError("available keys: "+", ".join(z.files))
                m=z[args.key]
            sizes=[int(x) for x in args.block_sizes.split(",")]
            norms=block_norms(m,sizes)
            mat_err=float(np.linalg.norm(m-m.T.conj())/max(np.linalg.norm(m),1e-300))
        else:
            norms=np.loadtxt(path,delimiter=",")
            mat_err=None
        report.update({"status":"RAW_MATRIX_OR_BLOCK_NORM_AUDITED_PROVENANCE_NOT_AUTOMATICALLY_VERIFIED",
                       "input_path":str(path), "input_sha256":sha256(path),
                       "matrix_symmetry_error":mat_err,
                       "observed":audit_norms(norms)})
    raw=json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)
    print(raw)
    if args.json_out:
        Path(args.json_out).write_text(raw+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
