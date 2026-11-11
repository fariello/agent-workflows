# Walkthrough: overnight session 2026-11-08 to 2026-11-09 (handoff)

- Id: hndoff

What was done while the maintainer was away, what it changed, and what still needs a human. Each item names its commit on `main`.

## Done

| What | Commit | Verification |
|---|---|---|
| Calibrated plan-size guidance from 425 runner execute turns (research `nj8zdp`) | `bbd65499c` | the record holds the method and numbers |
| `aw ipd lint` followability advisory `IPD-Z603` (never blocking; plans dated 2026-11-08+): more than 5 E-items, more than 8 work Scope-Paths, an E-item naming more than 8 units, a V-item demanding only a suite pass. Spec `ipd-structure-and-linting` 8.2; scaffold and templates carry the guidance | `f62d6d044` | `tests/test_ipd_followability.py` 7 passed; tuned on 9,024 V-items (66 hits, about 70% correct) |
| writestd sweeps `sfez3e` (specs), `uog8nc` (backlog), `381ml6` (plans) and orchestrator `8fvkmp` ran under `aw agy run` with Set metastore excluded, per the maintainer's answer | `3d0ddb845` (exclusion), lifecycle commits through `686771fe4` | run `run-20261109T154200Z-1081790`: all four `executed` |
| Plan filename Order may be two or three digits (0 to 999); all 4,473 existing two-digit names parse identically | `f83159217` | `tests/test_artifact_naming_round_trip.py`, `tests/test_plans_order_grammar.py` (boundaries 999/1000) |
| Metastore round-3 split: 212 children; every child within `IPD-Z603` except `cxxmyv` (13 Scope-Paths: the attended cutover must declare what it migrates). Orchestrator `63ib9r` regenerated, coverage pass, dependency graph acyclic (critical path 73), no dangling edges | `7144d9a29` | per-plan lint: 0 errors |
| Correction turns start a fresh host session in the re-adopted lane; `--resume-correction-session` opts back in (backlog `w93his`, done) | `eacd744f9`, `26081cdcf` | `tests/test_turn_fix_it.py` test_09 and test_10, `tests/test_production_fix_it.py`; 399 runner tests passed |
| Three slow askme installer tests listed in `tests/slow_allowlist.txt` (bug `ucuh2h`, filed only in unlanded lane `pkz19w`); lanes `1ajqaa`, `pkz19w` and four landed lanes pruned, so `aw attention` is valid again | `1c3440836` | `aw attention` prints no contract violation |

Core gate on `main` after the last change: `2074 passed`.

## Needs the maintainer

1. Review the metastore Set. All 209 pending metastore plans are `to-review`; nothing runs until they are reviewed and approved. Reviewing them is the next step (`aw oc review metastore`).
2. Design calls the splitting agents flagged for a reviewer to confirm:
   - `cxxmyv` now applies a prepared, inert code patch (`.aw/system/cutover/metastore-code.cutover.patch`, built by Orders 255 to 258) at the cutover, alongside `90iqr1`'s docs patch. The reasoning that this keeps C10a (one on-disk format per commit) is in `2k5t16` OQ-01.
   - The plans propose new public functions `artifact_meta.metadata_region` and a text-based history entry point (`bxupy8`).
   - `786w7r` is one shared baseline for the `e8420v` and `0xsx2n` families.
3. The calibration found that the two 7-hour turns came from slow model replies during certain hours (on 2026-11-06 and 2026-11-07, every turn on that model was slow in the same windows), not from plan size. Cause unknown. Smaller plans limit how much a slow period costs; they do not make the model faster.
