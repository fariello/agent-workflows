# Review findings: plan wja06w

- Subject-Id: wja06w
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The defect is real and every one of the plan's findings F-1 through F-6 reproduces at lane HEAD
`9f33c5c4`: `aw find specs --status to-review`, `--status bogusvalue` and `--id 4sd62s` all return the
full 38 rows, `aw find backlog --set closescope` returns all 628, and `aw find plans/research --status
<bogus>` both exit 0. The dependency `executed:qfpnrm` is satisfied, the post-`qfpnrm` generic branch
has the shape E-03 assumes (one shared loop that already reads `_read_id`/`_read_status` for display),
all five status enums exist exactly as named including `research_contract.STATUS_NORMALIZATIONS`'
legacy `intake` spelling, and the `CommandResult(status="cannot-run", exit_code=2)` refusal shape E-04
wants has a working precedent in the sibling `search` verb.

Three findings are substantive, and all three are cases where the plan's own stated intent and its
instructions disagree: E-04's `all` rule contradicts OQ-01, E-02's case (10) asserts the opposite of
what the fix can produce, and the chosen reader does not behave the way an equality filter needs.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | high | IN-SCOPE | A. Correctness / F. UX | `at.ARTIFACT_TYPES` = 11 types including walkthroughs/reviews/comms/roadmaps/other (no status enum); union of the five enums = 25 values | E-04's rule ("if at least one type has an enum and the value is in none of them, refuse") CONTRADICTS this plan's own OQ-01. `all` resolves to all eleven types, so it ALWAYS includes enum-less ones; under the authored rule `aw find all --status ran` would exit 2 while `aw find walkthroughs --status ran` exits 0 on the identical value. That makes the BROADER query the stricter one, and it refuses a legitimate lookup for a status only an enum-less type carries. The plan even asserted the refusal as a test expectation (E-02 case 9), so it would have shipped. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | fixed | Rule inverted: ANY resolved type without an enum disables validation entirely, so `all` never validates and a misspelling there returns an honest empty answer. Single-type and all-enum-bearing multi-type queries still validate, which is where F-4 actually bites. E-02 case (9) reversed to assert ACCEPTANCE at exit 0 with the reason stated in the test (the naive expectation is the opposite, so a later reader would otherwise "fix" it back). E-04 and E-05's expected outcomes updated; the gate discloses it. Recorded as the plan's own F-7. |
| PR-002 | high | UNDER-SCOPE | A. Correctness / F. UX | `_read_status` unreadable per generic type: walkthroughs 24/24, reviews 367/367, comms 7/7, roadmaps 1/1, other 4/4, prompts 16/17; specs 0/38, backlog 0/628, releases 0/1 | For SIX of the nine types this plan widens, NO record carries a readable `- Status:` (they have no such field at all), so after E-03 `--status` on any of them returns ZERO rows unconditionally. That is honest and strictly better than today's silent ignore-and-return-everything, but it was unstated, and E-02 case (10) asserted `find walkthroughs --status anything` "is accepted and filters" - which reads as a working filter and would be written as a test that passes for the wrong reason. A reviewer or approver could not tell from the plan how large the visible change is for those types. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | fixed | E-03 now requires treating an unreadable field as a non-match AND recording both measurements in the branch comment; it explicitly forbids "fixing" this with a looser reader (the `_STATUS_RE` parity comment makes the strict reader a matching contract). Case (10) rewritten to assert ZERO rows plus exit 0 with the reason. V-03 additionally demands the live `walkthroughs --status` and `reviews --id` runs showing honest empty answers. OQ-01 now states this as one of its two forced consequences. The gate discloses it. Recorded as F-8, with the `--id` twin as F-9. |
| PR-003 | medium | IN-SCOPE | A. Correctness | `_read_status('- Status: EXECUTED')` -> `'EXECUTED'` verbatim (plan `vfa1tl` declares exactly that); `_read_status('- Status: draft (aw set): status set to draft')` -> `None`, a shape `tests/test_find_single_read.py::test_d_status_disagreement...` pins as legitimate | E-03 says to `continue` past a record whose reader value "differs from" the flag, i.e. exact equality, but the reader neither case-normalizes nor survives a status line carrying trailing prose. So `--status executed` would miss an uppercase declaration that the tool itself displays, and a prose-carrying status is invisible to every `--status` query. Both shapes exist in this repo today. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-03 now requires a case-insensitive compare on both sides (`.strip().lower()`) and records the prose case as a deliberate non-match with its measurement, so the behavior is chosen rather than inherited. V-03 requires the diff to show the compare. Recorded as F-10. |
| PR-004 | medium | UNDER-SCOPE | G. Live-artifact success criteria | re-measured at review: to-review specs 1 (plan says 2), backlog 628 (617), `plans --status approved` 11 rows (24) | Three row counts were written into expected outcomes as bars and all three had already drifted between authoring and review. E-05 in particular said "`specs --status to-review` equals the live number of to-review specs (2 at authoring; re-derive)" - the parenthetical is right but the number invites an executor to reconcile to it, and E-01/F-1/F-3/F-5 carried the others as plain figures. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-05's expected outcome restated so every count is RE-DERIVED at execution with the three drifts named as proof that the authored numbers are not bars; V-05 says explicitly not to compare against any count written in the plan and fixes the direct-count command to scope `--include='*.spec.md'`. Recorded as part of F-11. |
| PR-005 | low | IN-SCOPE | E. Testing | `wc -l tests/test_cli_find.py` -> 110 (plan says 94); `tests/test_find_single_read.py` -> 436 lines, added by `qfpnrm`, unmentioned | F-6's test inventory is stale in both directions. The omission matters more than the line count: the new file calls `cli._find_type_records` DIRECTLY for plans and research, so it is the nearest existing coverage to what E-03 edits, and its status-disagreement case is what surfaced PR-003. Verified no existing test passes `--status`, so E-04's validation cannot break one - which is worth stating positively rather than leaving unknown. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-6 corrected to both files with their real sizes and the positive finding that neither uses `--status`; the conventions bullet updated the same way. Recorded as F-11. |
| PR-006 | low | UNDER-SCOPE | E. Testing | E-02's expected outcome as authored listed (9)'s refusal among the HEAD failures | With PR-001 applied, case (9) now asserts behavior that ALREADY holds at HEAD, so it is a guard against the over-strict validation review rejected, not a proof of new behavior. Leaving it in the "FAIL at HEAD" group would make a correct pre-fix run look like a contradiction - the same guard-versus-proof confusion that costs an executor a debugging cycle. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-02's expected outcome split into the two groups explicitly: FAIL at HEAD = (1)-(6), (8)'s filtering, (10)'s filtering; PASS before and after = (7), (9), (11). The test module docstring must say which group each case is in, and that a guard failing at HEAD means its fixture or expectation is wrong. E-01 also now captures `all --status bogusvalue` at HEAD so the after-comparison is honest. |
| PR-007 | low | IN-SCOPE | E. Testing / F. UX | `aw find specs --status bogusvalue -p` currently prints 38 paths at rc 0 | E-04 requires that "stdout stays empty so a `-p` consumer sees no path" on refusal, which is the right contract for a paths surface, but no validation item demanded evidence of it, so the one property a scripting consumer depends on was untested. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | V-04 now requires `aw find specs --status bogusvalue -p` showing EMPTY stdout with rc 2, alongside the `--json` `exit_code: 2` and the human-surface `echo $?`, plus `aw find all --status bogusvalue` at exit 0 to pin the corrected `all` behavior on the same surface. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | How should `--status` validation behave for `all`, given `all` always spans enum-less types? | Any enum-less type in the resolved set disables validation, so `all` never validates | Validate against the union of the five enums (as authored); validate `all` only against the types that have enums and filter the rest; give the enum-less types invented enums | The union rule was MEASURED to contradict OQ-01: `aw find all --status ran` would be refused while `aw find walkthroughs --status ran` is accepted, making the broad query stricter than the narrow one on the identical value. Inventing enums is what OQ-01 and the Deferred section already rejected because no such enum exists in code. Disabling validation when any resolved type cannot validate is the only rule under which the two queries cannot disagree. | yes |
| D-2 | Is "six types where `--status` now always returns zero" acceptable, or does it need a different filter? | Acceptable; state it and test it | Fall back to a looser status reader for those types; read an alternate field (`Subject-Id:`/`Reviewed-At:`); exclude those types from filtering | Zero rows is the truthful answer when no record carries the field, and it is strictly better than today's behavior (returning everything, which actively misleads). The `_STATUS_RE` parity comment makes the strict reader a MATCHING CONTRACT, so loosening it here would desynchronize the filter from every other matcher; reading an alternate field is a new semantic for `--status` and belongs to whatever plan defines statuses for those types. Excluding them from filtering would restore the silent-ignore defect for six types. | yes |
| D-3 | Should the filter compare statuses case-sensitively (exact equality, as authored) or case-insensitively? | Case-insensitively on both sides | Exact equality; normalize the reader itself | At least one plan in this repo declares `- Status: EXECUTED` and the reader returns it verbatim, so exact equality would hide a record the tool displays. Normalizing inside `selectors._read_status` would change every other consumer of a shared matching contract, which is out of this plan's scope and fence. Comparing case-insensitively at the filter is local and cannot affect another caller. | yes |
| D-4 | Is OQ-02's answer (accept `pending` and `reusable` as plans `--status` values) correct? | Yes; leave it | Refuse them as non-`- Status:` values; make `--status pending` match the directory | Verified the premise: 49 of 836 plan rows DISPLAY `pending` in the status column, and `--status pending`/`--status reusable` each return 0 rows today. Refusing a word the tool prints would send a reader who copied it to an error, which is exactly the confusion this plan exists to remove. Making it match the directory is a behavior change to the plans filter, which the plan correctly scopes out. | yes |
| D-5 | Keep E-02 (11 cases) and E-04 (helper + call site) as single items despite their size? | Keep both | Split E-02 per case group; split E-04 into helper and wiring | No `IPD-Z602` advisory fires, and the rubric diagnostics answer NO on substance: E-02 is one new file against one CLI surface verified by one pytest run, and splitting it would break the tests-first ordering E-03/E-04 depend on; E-04's helper is dead code without its call site, so the two are not independently verifiable. Both items' length is enum tables and rationale, not additional work. | yes |
| D-6 | Should the stale spec `6m4kow` honest-limits bullet be amended in this plan? | No; leave the plan's `aw specs note` approach | Amend the bullet and declare the spec in `Scope-Paths` | The plan's reasoning is sound and matches the repository rule: the bullet is a historical measurement ("was broken"), not a contract this change alters, and a note records the fix without a contract edit. Declaring a spec edit would also oblige the spec-sync reconciliation for no behavioral gain. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `fixed`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> `conforming`, exit 0. After all edits,
  `aw ipd lint --phase review-finalize --agent <plan>` -> `conforming`, exit 0, 0 findings. No
  `IPD-Z602` advisory at any point.
- Dependency: `executed:qfpnrm` resolves to
  `.aw/records/plans/executed/20260925-findonce-01-qfpnrm-...ipd.md` with `- Status: executed`.
- Fail-open modes reproduced (`-p`, row counts): `find specs` 38; `--status to-review` 38;
  `--status bogusvalue` 38 rc 0; `--id 4sd62s` 38; `find backlog` 628; `--set closescope` 628;
  `find plans --status bogusvalue` 0 rc 0; `find research --status bogus` 0 rc 0;
  `find plans --status approved` 11 (control, filters).
- Generic branch read post-`qfpnrm`: one shared loop over `sorted(matched_paths)` that reads
  `sel_mod._read_id(text)` and `sel_mod._read_status(text)` for DISPLAY only, with no `--set` read at
  all, serving both the selector and no-selector arms - the shape E-03 assumes.
- Enums confirmed present and typed: `attention_contract.SPEC_STATUSES` (frozenset, 9),
  `backlog.STATUSES` (frozenset, 5), `releases.RELEASE_STATUSES` (tuple, 3), `plans.RECOGNIZED`
  (frozenset, 9), `research_contract.STATUSES` (4) + `STATUS_NORMALIZATIONS` (`{'intake': 'todo'}`).
- `intake` acceptance verified end to end: `find research --status intake` and `--status todo` both
  return 13 rows; `research_contract.normalize_status('intake')` -> ok with value `todo`,
  `('bogus')` -> not ok.
- Strict reader over specs yields ONLY values in `SPEC_STATUSES` (38 records, 0 outside), confirming
  the reader is region-bounded and does not pick up the `- Status:` lines inside embedded
  open-question blocks - which is why E-03's choice of reader is correct.
- OQ-02 premise verified: `find plans` displays `pending` for 49 rows, and `--status pending` /
  `--status reusable` each return 0 rows.
- Refusal precedent verified: `cli._run_find`'s sibling `search` path already uses
  `CommandResult(command=..., status="cannot-run", exit_code=2, summary=...)` on agent/json and
  `term.status("fail", ...)` + `return 2` otherwise.
- No existing test passes `--status` to `aw find` (checked `tests/test_cli_find.py` and
  `tests/test_find_single_read.py`), so E-04 cannot break one.
- Bare `python3 -m pytest` -> `2525 passed, 2 skipped` (baseline; review edits touch records only).
