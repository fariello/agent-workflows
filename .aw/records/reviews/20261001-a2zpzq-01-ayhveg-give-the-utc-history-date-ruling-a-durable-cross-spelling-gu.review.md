# Review findings: plan ayhveg

- Subject-Id: ayhveg
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fe2ee961c` in an isolated review lane. Plan committed (`b90eec6d4`) and byte-identical to the
sealed lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` clean before semantic review;
`--phase review-finalize` clean after revision.

Re-verified:
- Dependency `5ivkdh` is EXECUTED (`.aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-...ipd.md`, commit
  `3c55295a3`). That commit removed the date masks from `tests/test_backlog.py` and
  `tests/test_history_label_parity.py` (docstring included) and added `tests/test_history_date_clock.py`, a
  hand-listed guard under `Pacific/Kiritimati` and `Pacific/Honolulu`.
  `python3 -m pytest -o addopts="" -q tests/test_history_date_clock.py tests/test_history_label_parity.py tests/test_backlog.py`
  -> `57 passed in 10.88s`.
- `command_surface.COMMAND_INVENTORY`: tuple of 163 `CommandDeclaration`; set/note verbs: `set`, `ipd set`,
  `backlog set`, `backlog note`, `specs set`, `specs note`, `prompts set`, `config set`, `ipd dependencies set`,
  aliases `spec set`/`spec note`.
- Live skew window during review (UTC 2026-10-07, Honolulu 2026-10-06). Under TZ=Pacific/Honolulu:
  `backlog note` -> `- 2026-10-07 note (aw backlog): notez`; `specs note` -> `- 2026-10-07 note (aw specs): notez`;
  `aw set to-review sp0001` -> `- 2026-10-07 to-review (aw set): posz`.
- Third mask `tests/test_backlog_history_dedup_parity.py` `_DATE_RE`: with it disabled under Honolulu, `ran 6 fail 0 err 0`.
- Red-at-base feasibility: `git worktree add --detach <scratch> 3c55295a3^` plus the shipped guard copied in fails
  `'2026-10-06' not found in {'2026-10-07'} : Under Pacific/Honolulu, backlog created line wrote 2026-10-06`.
- Carriers resolve: `7qvs1c` done, `fcnz1r` open, `fnb8pl` graduated.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-100 | HIGH | IN-SCOPE | G. Executability (stale premise) | `tests/test_history_label_parity.py` `_normalize_history_record` (mask gone, commit `3c55295a3`); `tests/test_backlog_history_dedup_parity.py` `_DATE_RE` | E-04 targeted two masks the executed dependency had already removed, missed a third live mask, and V-04 demanded diffs that would be empty. An executor would either no-op or invent work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 rewritten to the third mask plus the one stale `hiding actor and date skew` comment, with an `rg` re-derivation; Scope-Paths swaps `tests/test_backlog.py` for `tests/test_backlog_history_dedup_parity.py`; V-04, Proposed changes, Scope check, Required tests updated; F-10/F-11 added. |
| PR-101 | MEDIUM | IN-SCOPE | C. Avoid duplicate paths | `tests/test_history_date_clock.py` `test_backlog_set_both_spellings_record_utc_date`, `test_specs_new_records_utc_date_and_local_filename` | E-03 would re-assert, in a second file, the per-family UTC and local-filename cases the shipped guard already pins. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now states that it EXTENDS the shipped guard (derived spellings, agreement assertion), leaves that file untouched, and may cite its composition cases. F-12 records the uncovered spellings already measured UTC. |
| PR-102 | LOW | IN-SCOPE | E. Test isolation | `tests/test_history_date_clock.py` `env = {**os.environ, "TZ": zone, ...}`; `tests/test_history_date_clock_readers.py` docstring "no in-worker time.tzset()" | E-01 mandated in-process `time.tzset()` under xdist, while both shipped TZ suites use subprocess `env=`, which is safer and simpler. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and V-01 prefer the subprocess form, still allowing an in-process context manager with guaranteed restore; precondition computed at the same instant, tolerating midnight crossing. |
| PR-103 | MEDIUM | IN-SCOPE | A./Shared checkout safety; E. Evidence feasibility | Required tests "with `5ivkdh`'s production edits reverted or stashed"; AGENTS.md shared-checkout rule | Red-at-base required reverting or stashing production code in a shared checkout, which the repo contract forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-specified as a detached scratch worktree at `3c55295a3^` with the new test copied in, demonstrated feasible at review. V-03 updated. |
| PR-104 | LOW | IN-SCOPE | G. Traceability | `aw check` `check.ipd-carrier-finished-unverified` on this plan: "carrier 7qvs1c finished (done)" | The Deferred row naming carrier `7qvs1c` lacked evidence that the finished carrier discharged it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Carrier-Evidence:` citing the executed `5ivkdh` plan; advisory cleared. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | With half the plan absorbed by `5ivkdh`, re-scope or retire? | Re-scope: keep the derived guard, agreement assertion, third mask | Retire as superseded (rejected: the derived surface and `backlog/specs note`, `ipd set`, `prompts set` coverage are not in the shipped hand-listed guard) | `tests/test_history_date_clock.py` test names; `command_surface.COMMAND_INVENTORY` | yes |
| D-2 | How to obtain red-at-base without touching the shared checkout? | Detached scratch worktree at `3c55295a3^` | `git stash`/revert (rejected: AGENTS.md shared-checkout rule) | review run of the shipped guard in such a worktree | yes |
