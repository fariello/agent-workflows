- Id: 21ct62
- Status: open
- Blocks-Release: next
- Set: wfartgrowth
- Priority: medium
- Work-Kind: bug
- Summary: ARCHITECTURE.md still documents the retired repo-root workflow-artifacts/ run-scratch path in two places

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): ARCHITECTURE.md still documents the retired repo-root workflow-artifacts/ run-scratch path in two places

Measured 2026-09-18 while executing wfartifacts Order 03 (plan 9x1rps), which swept the 86 stale references out of the shipped workflow bodies under .aw/system/workflows/.

WHAT IS WRONG. ARCHITECTURE.md, which is user-facing documentation, still names the RETIRED repo-root path that Order 07 (spec 20260817-2124-01, u7xtni) replaced with .aw/workflow-artifacts/:

  ARCHITECTURE.md:147  Every run creates `workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped; ...
  ARCHITECTURE.md:201  ... never touches `workflow-artifacts/` run records, user code, or `.aw/records/`.

Measured with the PATH-reference form used by the Order 03 guard:

  $ grep -rnoP '(?<![/\\w-])workflow-artifacts/' ARCHITECTURE.md
  ARCHITECTURE.md:147:workflow-artifacts/
  ARCHITECTURE.md:201:workflow-artifacts/

WHY IT MATTERS RATHER THAN BEING COSMETIC. Line 147 calls that directory 'the authoritative record', so a reader following ARCHITECTURE.md creates run scratch at a repo-root path that the framework-owned .aw/.gitignore does NOT ignore (it ignores the anchored /workflow-artifacts/, i.e. .aw/workflow-artifacts/). Run records carry local context, absolute home paths and session detail, so that path being unignored is the D92 leak the relocation exists to prevent. This is the same defect class as the two false claims in assess/assess.md that Order 03 repaired, just on a different surface.

WHY IT WAS NOT FIXED IN PLACE. ARCHITECTURE.md is outside Order 03's Scope-Paths (.aw/system/workflows/, tests/test_docs.py), and no sibling in Set wfartifacts covers it either: Order 04 (l1c1iz) scopes the run-scratch README template, .aw/records/README.md, engine.py and tests/test_dir_readmes.py. Broadening scope opportunistically is forbidden by the execution contract, so the finding is carried here instead.

SUGGESTED FIX. Re-point both lines to .aw/workflow-artifacts/, and consider extending the Order 03 guard (tests/test_docs.py, ShippedRunScratchPathTests) to cover root user-facing docs as well as the shipped workflow tree; the guard's _bare_run_scratch_refs helper already encodes which spellings are legitimately bare (the anchored gitignore pattern, the workflow-artifacts-README.md template filename, and scan_secrets.py's path-segment name).

NOT THE SAME AS zzsaq2, which is about run-scratch never being pruned or archived. This one is purely a stale documented path.
