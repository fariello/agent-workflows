# Assessment - bugs (product code; framework is the subject)

Verdict: adequate for bugs/correctness (no Blocker/High; a small cluster of Medium install-path
correctness gaps + Low annotation/portability items).
IPD written: `.agents/plans/pending/20260715-2053-01-assess-bugs.md`
Run: 20260715-205322 | Method: two parallel read-only bug-hunting lanes (D84 dogfood: engine+cli;
comms/plans/versioning/config/tools) + coordinator synthesis; the three Medium findings re-verified
against source before filing.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| F4 | MEDIUM | Low | QA/engineer | `engine.run()` computes `returncode` then `return 0` - the `install-workflows.py` multi-repo path reports success even when a repo failed/aborted. |
| F5 | MEDIUM | Low | data-integrity | `.created-files.json` omits `create_setup_artifacts` files (gitleaksignore, secret-scan CI, `.agents/comms/` skeleton), so `--undo` leaves them behind. |
| F8 | MEDIUM | Low | QA/engineer | `_install_all`/`setup` catch `except Exception`; `install_into_repo` can raise `SystemExit` (BaseException) -> escapes and aborts the batch, breaking R-4 isolation. |
| F1 | LOW | Low | engineer | `prompt_and_run_commit(..., artifacts: list[str] = None)` annotation vs default mismatch (the deferred LSP diagnostic; only instance in engine/cli). |
| F6 | LOW | Low | engineer | Preserved customized shim mis-tagged `[already current]` -> reported as `[no change]`. |
| F14 | LOW | Low | data-integrity | `save_created_files_record` swallows write failure silently (degrades `--undo`). |
| F-tools | LOW | Low | engineer | CSV outputs miss `newline=""` (Windows); dead PHONY-skip clause in run_checks; short-secret redaction reveals up to 8 chars. |

## Proposed plan (summary)

1. F4 `run()` -> `return returncode`. 2. F5 record `create_setup_artifacts` files for rollback. 3. F8
catch `SystemExit` in `_install_all`/setup. 4. F1 annotation Optional. 5. F6 distinct preserved tag. 6.
F14 warn on record-write failure. 7. F-tools (CSV newline, dead PHONY clause, short-secret redaction).
Each with a regression test. All Low Remediation Risk.

## Deferred (with reason)

- F7 (latent UnboundLocalError in merge_pointer_block native branch) and F12 (dead if/elif in
  ensure_backups_gitignored): not reachable today; cosmetic/defensive - optional tidy-up only.
- F4-versioning (bare-tag parse_describe): not reachable (sole caller uses `git describe --long`);
  documented boundary, no fix.
- All "confirmed SAFE" surfaces (is_filename_safe, payload-blind parser, ACK_WRITER, validate_ack,
  Set/Order, versioning ordering, config/discovery/pypi_links/term, run_checks honesty): not touched.

## No Blocker/High

The install path is no-clobber, backs up before overwrite, and stages-not-commits, so writes are safe.
The gaps are exit-code honesty (F4), rollback completeness (F5/F14), and batch isolation (F8), not
destructive data overwrites and not any security-control bypass (is_filename_safe verified bypass-free).

Next step: review the IPD (optionally run plan-review) and approve before execution. This workflow does
not execute the plan.
