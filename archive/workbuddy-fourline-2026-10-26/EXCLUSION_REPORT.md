# Exclusion and publication-safety report

Repository `lyxxx708/hessian-landscape` is **public**. This file records what was
checked before the raw payload was published, what was excluded, and what remains a
residual risk.

No secret value is reproduced anywhere in this report. Findings are recorded as
category, path and count only.

## 1. What the package contains

2,026 members / 2,141,079,119 uncompressed bytes, from 50 declared roots:

source code (`bridge/`, `runner/`, `science_v*/`, `scripts/`, `tools/`, `contracts/`),
experiment protocols and plans (`PLAN.json`, `PROTOCOL.md`, `METHODS_ADDENDUM.md`,
`research_design_v1..v3`), execution records and terminal receipts (`records/**`),
raw numerical arrays (`*.npz`, 14 files), logs, test harnesses, documentation, and the
27 report/table/figure artifacts.

Extension census of the package confirms there is no binary blob of unknown provenance:
`.json` 864, `.md` 335, `.py` 257, `.log` 219, `.txt` 117, `.mjs` 82, `.sha256` 52,
`.csv` 30, `.ps1` 26, `.npz` 14, `.cmd` 6, `.jsonl` 6, `.pdf` 5, `.svg` 4, `.bin` 3,
`.before` 2, `.reconstructed` 1, `.patch` 1.

## 2. Content scan for credentials

Every text-decodable member was scanned: **1,861 entries / 58,919,171 bytes**. The
remaining 165 binary members (2,082,485,376 bytes) were scanned with a reduced
binary-safe pattern set.

Patterns applied:

| Category | Target |
| --- | --- |
| `PRIVATE_KEY_BLOCK` | PEM `BEGIN … PRIVATE KEY` |
| `OPENAI_STYLE_KEY` | `sk-…` |
| `ANTHROPIC_KEY` | `sk-ant-…` |
| `GITHUB_TOKEN` | `ghp_/gho_/ghu_/ghs_/ghr_…`, `github_pat_…` |
| `GITLAB_TOKEN` | `glpat-…` |
| `AWS_AKID` / `AWS_SECRET` | access key id and assigned secret |
| `GOOGLE_API_KEY` | `AIza…` |
| `DASHSCOPE_QWEN_KEY` | `sk-<32 hex>` |
| `GLM_ZHIPU_KEY` | `<32 hex>.<14-20 alnum>` |
| `HUGGINGFACE_TOKEN` | `hf_…` |
| `SLACK_TOKEN` | `xox[baprs]-…` |
| `BEARER_TOKEN` | literal `Bearer <24+>` |
| `JWT` | three-segment base64url `eyJ…` |
| `GENERIC_ASSIGNED_SECRET` | `api_key` / `secret` / `password` / `client_secret` … assigned a 16+ char quoted literal |

**Result: 0 matches in text members. 0 matches in binary members.**

## 3. Content scan for private state and personal data

| Category | Result |
| --- | --- |
| Email addresses | 0 |
| Chinese mobile numbers | 0 |
| Chinese ID-card-shaped strings | 0 |
| `Cookie` / `Set-Cookie` headers | 0 |
| `session_id` assignments | 3 files — *code identifiers only* (`bridge/adapters/workbuddy/index.mjs`, `bridge/core/bridge.mjs`, `bridge/mcp/server.mjs`); these are parameter names in the Bridge source, not captured session values |
| `sqlite` / `.db` references | 2 files — *source code only* (`bridge/core/bridge.mjs`, `bridge/persistence/store.mjs`); the persistence layer's own schema references, no database file present |
| Local user paths | 1 file, 2 occurrences |

### The one disclosure that exists

`conversation_reports/workbuddy_retrospective_evidence_20261026.json` contains two
absolute paths embedding the local Windows account name:

```
C:\Users\<account>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
C:\Users\<account>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python312.dll
```

These are **runtime-anchor records** — the retrospective captured which interpreter
binaries it measured, with expected and actual byte counts and SHA-256, so the
measurement can be re-checked. The account name is already public as the repository
owner (`lyxxx708`) and the owner of every commit in this repository.

**Decision: retained.** Redacting them would break the reproducibility of the runtime
anchor audit, and the disclosure adds no information beyond what the GitHub account
already exposes. If that account name ever becomes sensitive, the correct fix is to
re-issue a redacted copy as a *new* package version — never to mutate this one.

## 4. Protected subtrees

The research protocol forbids publishing frozen `D008`/`D009`, confirmatory, holdout,
sealed or frozen material. A path predicate over all 2,026 members
(`d008`, `d009`, `confirmatory`, `holdout`, `sealed`, `frozen`, case-insensitive)
returned **0 hits**.

Independently corroborated by the package's own authorization record,
`project/science_v4/AUTHORIZATION.json`, which grants only pilot scope:

```json
"pilot_authorized": true,
"confirmatory_authorized": false,
"historical_data_authorized": false,
"no_claim_promotion": true
```

The package was built under that grant, so protected material was never in scope to
begin with. Both the path scan and the grant agree.

## 5. Filename-level audit

Searched all 2,026 members for `.env*`, `id_rsa`/`id_ed25519`/`id_ecdsa`/`id_dsa`,
`.netrc`, `.pgpass`, `.git-credentials`, `credentials*`, `secret*`, `cookie*`,
`*.key`, `*.pem`, `*.p12`, `*.pfx`, `*.kdbx`, `*.sqlite*`, `*.db`, `auth.json`,
`token.json` — **0 hits**.

## 6. Excluded from publication

| Excluded | Bytes (local) | Reason |
| --- | --- | --- |
| `E:\WorkBuddyProject\.venvs\**` | part of 10.07 GB tree | Virtual environments; reproducible from lockfiles, not evidence |
| `E:\WorkBuddyProject\node_modules\**` | idem | Dependency cache |
| `E:\WorkBuddyProject\.git\**` | idem | Git object database |
| `E:\WorkBuddyProject\` other Codex session trees | idem | Unrelated working directories outside the four-line scope |
| `E:\WorkBuddyProject\data\` root | idem | Declared out of scope by `COLLECTION_SCOPE.json` |
| Any `D008`/`D009`/confirmatory/holdout subtree | — | Protocol-forbidden; none present |
| Credentials / tokens / keys | — | None detected; would have been blocked |

The 10.07 GB local tree is therefore **not** the archive's denominator. The archive's
denominator is the 50 declared roots (1,984 files / 2,139,736,566 bytes), all of which
are present.

## 7. Residual risk — stated plainly

1. The credential scan is **shape-based and heuristic**. A secret in an unrecognised
   encoding, split across files, or encrypted would not match. This risk cannot be
   driven to zero by scanning.
2. `*.npz` and `*.bin` content was pattern-scanned but not semantically parsed. They are
   numerical arrays produced by the study's own code.
3. Publication is irreversible in practice: once public, forks and caches persist.
   If a leak is later found, the remedy is revocation of the credential plus a new
   package version — deleting the release does not un-publish it.
4. The commit history on this branch already contains the documentary material from the
   previous session; nothing in it was rewritten.

## 8. Verdict

`PUBLICATION_SAFE_WITH_DISCLOSURE` — the package carries source code, protocols,
records, raw numerical arrays and the report, one minor local-account path disclosure
that is already public via the repository owner, and no credential, no protected
subtree, and no third-party material of unclear licence.