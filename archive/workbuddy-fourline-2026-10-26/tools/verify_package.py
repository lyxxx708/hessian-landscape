#!/usr/bin/env python3
"""Standalone verifier for the WorkBuddy four-line archive package.

Standard library only. Streams the package; never loads the archive into memory.

    python verify_package.py --zip WorkBuddy_AllStages_20261026.zip
    python verify_package.py --zip ... --manifest FILE_MANIFEST.csv
    python verify_package.py --zip ... --json report.json

Exit codes: 0 = verified, 1 = mismatch, 2 = unusable input.
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import zipfile

EXPECTED_OUTER_BYTES = 2089046079
EXPECTED_OUTER_SHA256 = "290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f"
EXPECTED_MANIFEST_SHA256 = "f24b79119d5fb96c59ab4afc76420cdc9734fa84a8e2a21b89455edf41401836"
EXPECTED_MEMBERS = 2026
EXPECTED_CONTENT_MEMBERS = 2024
EXPECTED_CONTENT_BYTES = 2141079119

CHUNK = 8 * 1024 * 1024


def sha256_stream(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


def load_manifest(path):
    """Return {normalised_package_path: (bytes, sha256)}.

    Accepts the original MANIFEST.csv (columns: archive_path,bytes,sha256,phase_root)
    and this repository's FILE_MANIFEST.csv (same plus relative_path).
    """
    out = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames or "archive_path" not in rdr.fieldnames:
            raise ValueError("manifest missing 'archive_path' column")
        for row in rdr:
            key = row["archive_path"].replace("\\", "/")
            out[key] = (int(row["bytes"]), row["sha256"].strip().lower())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, help="path to WorkBuddy_AllStages_20261026.zip")
    ap.add_argument("--manifest", help="thing to verify against; defaults to the "
                                      "package's own embedded MANIFEST.csv")
    ap.add_argument("--json", help="write a JSON report here")
    args = ap.parse_args()

    if not os.path.isfile(args.zip):
        print("FAIL  no such file: %s" % args.zip)
        return 2

    rep = {}
    failures = []

    # ---- outer identity ----
    digest, size = sha256_stream(args.zip)
    rep["outer_bytes"] = size
    rep["outer_sha256"] = digest
    ok_size = size == EXPECTED_OUTER_BYTES
    ok_hash = digest == EXPECTED_OUTER_SHA256
    print("outer bytes     %-12d %s" % (size, "OK" if ok_size else "MISMATCH (expected %d)" % EXPECTED_OUTER_BYTES))
    print("outer sha256    %-12s %s" % (digest[:12] + "...", "OK" if ok_hash else "MISMATCH"))
    if not ok_hash:
        failures.append("outer sha256")

    try:
        zf = zipfile.ZipFile(args.zip)
    except zipfile.BadZipFile as e:
        print("FAIL  not a valid zip: %s" % e)
        return 2

    # ---- structural safety ----
    infos = zf.infolist()
    rep["members"] = len(infos)
    unsafe = [i.filename for i in infos
              if i.filename.startswith(("/", "\\"))
              or ".." in i.filename.replace("\\", "/").split("/")]
    names = [i.filename.replace("\\", "/") for i in infos]
    dups = len(names) - len(set(names))
    rep["unsafe_paths"] = unsafe
    rep["duplicate_paths"] = dups
    print("members         %-12d %s" % (len(infos), "OK" if len(infos) == EXPECTED_MEMBERS else "expected %d" % EXPECTED_MEMBERS))
    print("unsafe paths    %-12d %s" % (len(unsafe), "OK" if not unsafe else "FAIL"))
    print("duplicate paths %-12d %s" % (dups, "OK" if dups == 0 else "FAIL"))
    if unsafe:
        failures.append("unsafe paths")
    if dups:
        failures.append("duplicate paths")

    # ---- manifest ----
    if args.manifest:
        with open(args.manifest, "rb") as f:
            man_digest = hashlib.sha256(f.read()).hexdigest()
        man = load_manifest(args.manifest)
        rep["manifest_source"] = os.path.basename(args.manifest)
        rep["manifest_sha256"] = man_digest
        print("manifest        %-12s %s" % (man_digest[:12] + "...", "(external)"))
    else:
        try:
            raw = zf.read("MANIFEST.csv")
        except KeyError:
            print("FAIL  package has no MANIFEST.csv and none was supplied")
            return 2
        man_digest = hashlib.sha256(raw).hexdigest()
        rep["manifest_source"] = "MANIFEST.csv (embedded)"
        rep["manifest_sha256"] = man_digest
        ok_man = man_digest == EXPECTED_MANIFEST_SHA256
        print("manifest        %-12s %s" % (man_digest[:12] + "...", "OK" if ok_man else "MISMATCH"))
        if not ok_man:
            failures.append("manifest sha256")
        import io
        man = {}
        rdr = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        for row in rdr:
            man[row["archive_path"].replace("\\", "/")] = (
                int(row["bytes"]), row["sha256"].strip().lower())

    # ---- per-entry ----
    content_members = 0
    content_bytes = 0
    size_bad = []
    hash_bad = []
    extra = []
    read_err = []
    for i in infos:
        if i.is_dir():
            continue
        name = i.filename.replace("\\", "/")
        if name in ("MANIFEST.csv", "MANIFEST.sha256"):
            continue
        content_members += 1
        h = hashlib.sha256()
        got = 0
        try:
            with zf.open(i, "r") as fp:
                while True:
                    b = fp.read(CHUNK)
                    if not b:
                        break
                    h.update(b)
                    got += len(b)
        except Exception as e:                      # noqa: BLE001 - report and continue
            read_err.append({"path": name, "error": repr(e)})
            continue
        content_bytes += got
        exp = man.get(name)
        if exp is None:
            extra.append(name)
            continue
        if got != exp[0] or i.file_size != exp[0]:
            size_bad.append({"path": name, "read": got, "cd": i.file_size, "manifest": exp[0]})
        if h.hexdigest() != exp[1]:
            hash_bad.append({"path": name, "got": h.hexdigest(), "manifest": exp[1]})

    missing = [p for p in man if p not in set(names)]

    rep.update({
        "content_members": content_members,
        "content_bytes": content_bytes,
        "size_mismatch": size_bad,
        "hash_mismatch": hash_bad,
        "missing_from_package": missing,
        "not_in_manifest": extra,
        "read_errors": read_err,
    })

    print("content members %-12d %s" % (content_members, "OK" if content_members == EXPECTED_CONTENT_MEMBERS else "expected %d" % EXPECTED_CONTENT_MEMBERS))
    print("content bytes   %-12d %s" % (content_bytes, "OK" if content_bytes == EXPECTED_CONTENT_BYTES else "expected %d" % EXPECTED_CONTENT_BYTES))
    for label, items in (("size mismatch", size_bad), ("hash mismatch", hash_bad),
                         ("missing", missing), ("extra", extra), ("read error", read_err)):
        print("%-15s %-12d %s" % (label, len(items), "OK" if not items else "FAIL"))
        if items:
            failures.append("%s (%d)" % (label, len(items)))

    rep["failures"] = failures
    rep["result"] = "PACKAGE_VERIFIED" if not failures else "PACKAGE_FAILED"
    print("RESULT          %s" % rep["result"])

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2)
        print("report written  %s" % args.json)

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())