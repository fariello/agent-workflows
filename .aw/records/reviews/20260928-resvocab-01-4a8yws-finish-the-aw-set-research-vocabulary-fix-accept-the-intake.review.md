# Review findings: plan 4a8yws

- Subject-Id: 4a8yws
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `afb948ce` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and after revision `--phase
review-finalize` conforms with ZERO advisories and zero diagnostics. No pre-review snapshot was owed:
the plan was committed and unmodified. No production or test file was modified by this review; every
measurement ran read-only against this tree or in throwaway `tempfile` git repos, driven from probe
scripts and a pytest plugin under the gitignored `.aw/state/`, with `git status --porcelain` empty
before and after.

THE PLAN'S MEASUREMENT DISCIPLINE ON THE DEFECTS IS EXCELLENT AND ITS RE-SCOPING DECISION IS RIGHT.
Every one of F-1 through F-10 reproduced. F-1: `TYPE_STATUSES['research']` is `['active', 'todo']`,
derived from `HOT_STATUSES`. F-2: `done`/`open`/`parked` each exit 1 with
`Status '<w>' is not valid for research (valid: ['active', 'todo'])`. F-3: the cold target is
redirected with the exact quoted message. F-4: `aw set intake` exits 1. F-5 reproduced end to end:
`aw set active sc0001` on a doc in `reference/202609` exited 0, printed `reference -> active`, and
left `status: active` with the file still in the cold shard. F-6: `has_lifecycle_subdirs("research")`
is `False` and `target_subdir` is `None` for all four statuses. F-7 confirmed and strengthened (see
F-16). F-8/F-9/F-10 re-derived exactly: 123 conformant docs, 64 cold tier / 59 hot tier,
`HOT status sitting in COLD shard: 0`, `COLD status sitting at HOT root: 35`, raw status census
`{'reference': 67, 'archive': 32, 'todo': 13, 'active': 4}` with zero `done`/`open`/`parked`/`intake`,
and 0 shard-month mismatches when computed from `created` (the key `research_archive._shard_subpath`
actually uses). The carrier `zdsf35` exists, is accurate, and correctly scopes itself out. The
spec-sync section is accurate: `5tapom` Section 4's non-goal text and the README's
"`todo` (legacy `intake`)" row and hot-root/monthly-shard rule are all quoted correctly.

WHAT REVIEW FOUND IS THAT TWO OF THE THREE ITEMS COULD NOT BE EXECUTED AS WRITTEN.

**THE PLAN PROMISES SOMETHING IMPOSSIBLE, BECAUSE F-11's FIXTURE CLAIM IS FALSE (PR-801, BLOCKER).**
F-11 says `create_research` "writes into `self.repo_root / '.aw' / 'records' / 'research'` with no
shard component" and "cannot place a doc in a shard at all", and E-03 is built on that, instructing
the executor to extend the fixture. Measured, the signature is
`create_research(filename, id6, set_id, status="active", kind="research-report",
disposition="reference/202609")` building `base / disposition / filename`: sharding is not merely
possible, a COLD SHARD IS THE DEFAULT. The consequence is worse than a wasted step.
`test_set_active_writes_status_for_report` omits `disposition`, so it sets the HOT status `active` on
a doc in `reference/202609` and asserts exit 0 plus `status: active` written, which is EXACTLY the
write E-02 must refuse. So E-03's promise that the four existing tests "must pass unmodified" is
unsatisfiable, and an executor meeting it mid-run would have to either weaken E-02 or delete a test.
Proven by injecting the E-02 guard over the shipped `validate_transition_allowed`:
`test_set_active_writes_status_for_report FAILED` with `AssertionError: 1 != 0` at
`tests/test_status_set.py:2541`, the other three PASSED, and a full-suite run under the same
injection gave `1 failed, 3245 passed, 2 skipped`, confirming it is the ONLY collision in the tree.
FIXED: F-11 corrected, new F-12 records the collision with its evidence, and E-03 now leads with the
repair (`disposition=""`, assertions intact, not weakened) before adding new coverage. V-03 now
requires a per-method disposition statement and forbids a needless fixture extension.

**E-01's CHANGE SITE DOES NOT SATISFY E-01's OWN REQUIREMENT (PR-802, HIGH).** E-01 names
`validate_transition_allowed` and separately requires that "the normalized value must be what is
written to the file, so a doc set from `intake` lands on `todo` and never on the legacy spelling".
Those two clauses contradict each other: `apply_status_change`, which writes the file, calls
`normalize_target_status(target_status, rec.record_type)` INDEPENDENTLY on the RAW target. Measured by
patching each candidate site over the shipped code: validator-only gave `aw set intake sc0002 ->
exit 0` with the file reading `status: intake`, the precise outcome the item forbids; patching the
shared `normalize_target_status` gave `status: todo`. The helper has 13 call sites, all inside
`status_set.py` and none elsewhere, including the two `--dry-run`/agent preview
`detail=f"status: ... -> {normalize_target_status(...)}"` sites that V-01's "TARGET is `todo`"
assertion depends on, so it is the only site where validation, the write, and the preview agree by
construction. FIXED: E-01 moved to the shared helper with the measurement recorded, new F-14, new
OQ-02 recording the widened blast radius, and V-01 now demands both the written-bytes check and
evidence that plans' `done`/`pending` aliasing is unaffected. Full suite green under exactly this
patch (`3246 passed, 2 skipped`).

**E-02 MIS-CITES THE SYMBOL IT DEFERS TO (PR-803, LOW).** E-02 says not to "re-implement the shard
math (`research_archive._shard_subpath` already owns it)". That symbol is
`_shard_subpath(status: str, created: str)`: it computes a DESTINATION from a status plus a date and
returns `None` for any hot status, so it cannot classify a file's current tier from a path, and an
executor following the instruction would look for a fit that does not exist. The tier test E-02
actually needs is a first-path-segment comparison against `REFERENCE_DIR`/`ARCHIVE_DIR` with no
shard-month arithmetic at all. FIXED in E-02, new F-15.

**E-02's REFUSAL POINTS AT AN UNVERIFIED PROMOTE DIRECTION (PR-804, LOW).** The message says
"exactly as the existing cold-target refusal does", but the shipped refusal sends the user to
`promote --to reference` (which F-3 measured) while E-02's sends them to `promote --to <hot status>`
(which nothing measured). Had that path not existed, the refusal would have stranded the doc
unreachable by any verb. Verified at review that it works: `promote --to active` and `--to todo` both
preview exit 0, and `--to active --apply` printed `active: sc0001 -> ...` with
`still in cold shard: False` and the file present at the hot root. FIXED: E-02 records the
verification, new F-13, and V-02 now requires the escape hatch to be re-demonstrated against the
changed tree plus an `archive/` tier case beside the `reference/` one.

**F-7 IS CORRECT, AND THE ONE REPORTED FINDING IS A RED HERRING WORTH RECORDING (PR-805, LOW).**
`aw check research` reports `errors 1` in a scratch repo, which could be misread as detection of the
stranding. It is not: the single diagnostic is `{"location":"<collisions>","rule":
"check.collisions-not-checked"}`, byte-identical before and after the stranding, and
`aw research index --check --agent` emits nothing (clean) afterwards. FIXED by recording it as new
F-16 so an executor re-running F-7 does not mistake the unrelated finding for a detector. Also
recorded: F-14's suite baseline has moved to `3246 passed, 2 skipped` (new F-17), so the validation
items now demand re-derivation rather than comparison against a plan-written digit.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. OQ-01 survives review and is upheld: the corpus census was re-derived independently and matches
its figures exactly, so the migration question really is answered by evidence. New OQ-02 records the
shared-helper decision as non-blocking and reversible. The three Carrier-Declined rows and the
`zdsf35` carrier were each checked and are honest.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | blocker | IN-SCOPE | D. Anti-regression / E. Testing | `tests/test_status_set.py` `create_research` signature with `disposition="reference/202609"` default; `test_set_active_writes_status_for_report` omitting it; E-02 guard injected -> `AssertionError: 1 != 0` at `tests/test_status_set.py:2541`; full suite under injection `1 failed, 3245 passed` | F-11's claim that the fixture cannot shard is false (a cold shard is its DEFAULT), so one pre-existing test asserts precisely the write E-02 must refuse, making E-03's promise that all four pass "unmodified" unsatisfiable. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | F-11 corrected; new F-12 with the measurement; E-03 rewritten to repair `test_set_active_writes_status_for_report` via `disposition=""` with assertions intact, and to stop extending the fixture; V-03 requires a per-method disposition statement; the gate now names this as read-before-coding. |
| PR-802 | high | IN-SCOPE | A. Correctness and data integrity | `apply_status_change` calling `normalize_target_status(target_status, rec.record_type)` independently of the validator; validator-only patch -> `exit 0` with `status: intake` on disk; shared-helper patch -> `status: todo`; 13 call sites all within `status_set.py` | E-01's named change site cannot satisfy E-01's own requirement: it passes validation and then writes the legacy `intake` spelling the item exists to eliminate. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-01 moved to the shared `normalize_target_status` with the measurement recorded; new F-14; new OQ-02 records the blast radius; V-01 demands the written-bytes check plus proof plans' aliasing is unaffected; full suite green under the patch. |
| PR-803 | low | IN-SCOPE | G. Plan executability | `research_archive._shard_subpath(status: str, created: str)`; `_shard_subpath('active','20260905') -> None` | E-02 defers the tier computation to a symbol that takes a status and a date, not a path, and returns `None` for every hot status, so it cannot classify a file's tier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-02 now specifies a first-path-segment comparison against `REFERENCE_DIR`/`ARCHIVE_DIR` and explicitly overrides the `_shard_subpath` instruction; new F-15; V-02 asserts the symbol was not used. |
| PR-804 | low | IN-SCOPE | F. KISS / UX (prevent silent failure and dead ends) | F-3 measured only `promote --to reference`; review measured `promote --to active`/`--to todo` preview exit 0 and `--to active --apply` giving `still in cold shard: False` with the file at the hot root | E-02's refusal directs the user to a promote direction the plan never verified; an unverified remedy in a refusal message risks stranding the doc unreachable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-02 records the end-to-end verification; new F-13; V-02 requires the escape hatch re-demonstrated against the changed tree plus an `archive/` tier case. |
| PR-805 | low | IN-SCOPE | Evidence accuracy | `aw check research --agent` reporting `findings: 1` with `check.collisions-not-checked`, byte-identical before and after the stranding; `aw research index --check --agent` empty after it; bare suite `3246 passed, 2 skipped` vs the plan's 3217-era comparison | F-7's conclusion is right but `aw check research`'s unrelated single finding could be misread as detection; and the suite baseline the plan compares against has moved. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | New F-16 records the red herring explicitly; new F-17 records the re-measured baseline; V-03 and Required tests now demand a baseline re-run rather than a plan-written digit. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | One pre-existing test asserts exactly what E-02 must refuse. Repair the test, narrow E-02, or drop E-02? | Repair the test with the minimal `disposition=""` change, keeping its assertions, and leave E-02 at full strength. | (a) Narrow E-02 to the `archive/` tier only so `reference/` keeps working: rejected as arbitrary, since both directories are cold tiers and the stranding is identical in each. (b) Drop E-02: rejected because F-5/F-7 measure a real silent-corruption defect that is half the plan's purpose. (c) Delete the test: rejected because it pins genuine behavior (a hot status IS writable on a hot-root report) that must keep working; moving it to the hot root preserves exactly that. | The fixture's `disposition` parameter already supports the hot root and `test_set_hot_status_on_prompt_refuses` already uses `disposition=""`, so the repair is idiomatic and one argument wide; the injected-guard run showing this is the only collision in the tree. | yes |
| D-2 | E-01 must change a helper shared by every record type to meet its own requirement. Accept that, or fork a research-only path? | Change the shared `normalize_target_status`, guarded to `record_type == "research"`. | (a) Patch `validate_transition_allowed` only (as authored): rejected on measurement, it writes `status: intake`. (b) Patch both functions separately: rejected as a forked predicate putting one aliasing rule in two places, the desync shape `TYPE_STATUSES`' own "DERIVED, never re-listed" comments exist to prevent, and it would still miss the two preview `detail=` call sites. | `apply_status_change` re-deriving the written value from the raw target; the measured `status: intake` vs `status: todo` outcomes; 13 call sites all inside `status_set.py`; full suite green under the shared-helper patch. | yes |
| D-3 | E-02's message names a promote direction the plan never measured. Verify it, or soften the message? | Verify it end to end and record the verification in the plan. | (a) Soften the message to name no verb: rejected because the repository convention (and the shipped cold-target refusal) is that a refusal names the verb that CAN do the job. (b) Assume it works by symmetry with `--to reference`: rejected because a refusal pointing at a dead end would strand the doc, which is a worse failure than the one E-02 prevents. | `promote --to active`/`--to todo` previewing exit 0 and `--to active --apply` moving the file out of `reference/202609` to the hot root. | yes |
