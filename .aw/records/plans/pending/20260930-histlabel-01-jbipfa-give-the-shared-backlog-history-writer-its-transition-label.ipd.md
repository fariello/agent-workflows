# IPD: Give the shared backlog history writer its transition label so both spellings of aw backlog set record the same thing

- Date: 2026-09-30
- Kind: child
- Concern: `aw backlog set` has two spellings of one transition and they write DIFFERENT history labels. `aw backlog set <status> <id6>` (positional, via `status_set.apply_status_change`) writes `- <date> <status> (aw set): <msg>`, naming the transition. `aw backlog set <path> --status <status>` (via `backlog.run_set` -> `backlog._reattach_history`) writes `- <date> set (aw backlog): <msg>`, because `_reattach_history` HARDCODES the token `set` and uses its `new_status` parameter only as a message fallback. So 476 records in this repository's own backlog corpus carry the uninformative `set` label where the writer knew the target status, and a reader cannot tell the transition from the record without reading its free-text message. Backlog `awqzuh` filed this at `eikajx`'s review (finding F-13, decision D-3), where `eikajx` deliberately ACCEPTED the label rather than widen the shared writer.
- Scope: IN: give `backlog._reattach_history` an explicit `label` parameter defaulting to today's `"set"` so no existing caller changes behavior silently; pass the TARGET STATUS from `backlog.run_set`, tagging a genuine transition with the status and a same-status write with `same-status` so the two spellings agree on BOTH cases; pass `"done"` from `set_records.close_on_answer`; update the two tests that pin the old label (`tests/test_backlog.py::BacklogPreservationTests::test_close_on_answer_preserves_prior_history_records` and `::test_release_exempt_setter_roundtrip_and_parity`), both of which this change measurably breaks; add parity tests over BOTH spellings covering a genuine transition, a same-status write, and the preservation property; one CHANGELOG entry. OUT, each with a reason recorded under "Deferred": the ACTOR asymmetry (`(aw backlog)` versus `(aw set)`), which is a truthful attribution of which code path ran and is not a defect; the 476 EXISTING records, which are committed history and must not be rewritten; `status_set.apply_status_change`, which already writes the correct label and is not touched; the dedup asymmetry between the two spellings, which is a real separate defect this plan MEASURED and FILED as backlog `r74211` rather than fixing.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/set_records.py, tests/test_backlog.py, tests/test_history_label_parity.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: awqzuh
- Set: histlabel
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: jbipfa

## Workflow history

- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `awqzuh`. The asymmetry was re-measured live at HEAD `4b7f2582` by driving both spellings over identical fixtures, and the whole suite was run against a THROWAWAY probe of the fix to find its exact blast radius (2 failures, both label pins, both in `tests/test_backlog.py`); the probe was reverted and the tree is clean.
- 2026-09-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make one transition record the same thing whichever spelling of `aw backlog set` an agent or human typed, so a reader scanning a backlog item's `## Workflow history` can see WHAT the transition was from the record's label rather than having to infer it from free text.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: give the shared writer a label, without changing any caller silently

- [ ] E-01 `agent_workflows/backlog.py` (`_reattach_history`): add a keyword parameter `label: str = "set"` and build the record as `f"- {today} {label} (aw backlog): {msg}"` instead of hardcoding `set`. CHANGE NOTHING ELSE IN THIS FUNCTION. Specifically: `msg = message.strip() or f"status -> {new_status}"` stays exactly as it is (the `new_status` parameter keeps its message-fallback job and does NOT become the label, so a caller that passes a status but wants the old token is unaffected); the `old_text`-not-`rendered` source of prior records stays (the docstring explains, with a measurement, why reading priors from `rendered` preserved a re-dated forgery); and the newest-first assembly `hist_block = "\n".join([new_record] + prior)` stays.

    THE DEFAULT IS THE WHOLE SAFETY ARGUMENT AND IT IS NOT DECORATION. `_reattach_history` has exactly TWO callers in the tree, `backlog.run_set` and `set_records.close_on_answer` (verified by searching the whole repository for the symbol), and E-02 and E-03 update both. Defaulting to `"set"` nonetheless means a THIRD caller arriving on a long-lived branch keeps today's behavior rather than raising a `TypeError` at merge time, which is the failure mode a required parameter would introduce for no gain. Add a docstring paragraph recording WHY the parameter exists (the two spellings disagreed; backlog `awqzuh`), naming `status_set.apply_status_change` as the writer whose label shape this now matches, and stating that the default preserves the legacy token for an unaware caller.

    DO NOT "SIMPLIFY" THIS BY DERIVING THE LABEL FROM `new_status` INSIDE THE FUNCTION. That looks tidier and is wrong in a measured way: `close_on_answer` passes `new_status="done"` and a same-status `run_set` call passes the item's CURRENT status, so an internal derivation would have to re-implement the same-status discrimination E-02 performs, in a function that cannot see the item's prior status (it receives `old_text`, not a parsed item, and parsing it here would duplicate `parse_item` work the caller has already done). The label is the CALLER's knowledge; the parameter is how the caller states it.
  - Depends on: none
  - Expected outcome: `_reattach_history(old, rendered, "done", "msg")` (no `label`) still emits `- <today> set (aw backlog): msg`, byte-identical to today; `_reattach_history(old, rendered, "done", "msg", label="done")` emits `- <today> done (aw backlog): msg`; prior records are preserved verbatim and newest-first in both calls; the function's other three behaviors (message fallback, prior-record source, body re-emission) are unchanged in the diff.
  - Execution state: pending

- [ ] E-02 `agent_workflows/backlog.py` (`run_set`): pass the label at the `_reattach_history` call site, discriminating a genuine transition from a same-status write, so the `--status` spelling agrees with the positional one on BOTH cases. Compute the label from the item's PRIOR status (read from the file text as it was, via `parse_item(text).status`, NOT from `item.status`, which `run_set` has ALREADY overwritten with `new_status` several lines earlier at `item.status = new_status`): when the prior status differs from `new_status` the label is `new_status`; when they are equal the label is `same-status`.

    THE SAME-STATUS HALF IS NOT OPTIONAL AND IT IS NOT GOLD-PLATING. `status_set.apply_status_change` tags a true same-status write `same-status` DELIBERATELY, and its docstring states the reason: "so verdict readers do not mistake it for a review record". Labelling a same-status `--status open` write `open` would therefore make the `--status` spelling assert a transition that did not happen, which is a WORSE record than today's uninformative `set`. Measured on the probe: with the status-only label, a same-status call through `run_set` wrote `- <today> open (aw backlog): exempted reason` while the positional spelling wrote `- <today> same-status (aw set): exempted reason`, so the two spellings still disagreed and `test_release_exempt_setter_roundtrip_and_parity` still failed (that test normalizes `set (aw backlog)` on one side against `same-status (aw set)` on the other, which is itself evidence that same-status is the case it exercises). With the `same-status` discrimination added, both spellings emitted `same-status`.

    MEASURED PARITY AFTER THIS ITEM, all six combinations driven over identical fixtures at HEAD `4b7f2582` with the probe applied:

    | Target | `--status` spelling | positional spelling |
    |---|---|---|
    | `graduated` (from `open`) | `graduated (aw backlog)` | `graduated (aw set)` |
    | `open` (from `open`) | `same-status (aw backlog)` | `same-status (aw set)` |
    | `done` (from `open`) | `done (aw backlog)` | `done (aw set)` |

    THE ACTOR STILL DIFFERS AND THAT IS CORRECT, NOT A REMAINING HALF OF THIS BUG. `(aw backlog)` versus `(aw set)` truthfully names which code path wrote the record, the parenthesis is where every writer in the tree records its own identity (`created (aw backlog)`, `note (aw backlog)`, `note (aw specs)`), and `same_status_message_is_duplicate` documents that it deliberately does NOT compare the actor. Do not unify it; see "Deferred".

    NOTE WHAT THIS ITEM DOES NOT FIX, and do not be tempted into it here: the two spellings also differ on DEDUPLICATION. Measured at HEAD `4b7f2582` with no probe applied, two identical same-status `--status` calls produced TWO identical records, while two identical positional calls produced ONE (`apply_status_change` consults `same_status_message_is_duplicate`; `run_set` consults nothing). That is a separate, real defect with its own blast radius (it decides whether a write happens at all, not what a record says), and it is ALREADY FILED as backlog `r74211`. Do not wire the dedup predicate into `run_set` here, even though it would be a two-line change: that widens this plan past the scope its review approved, and `r74211` records two implementation hazards a casual port would trip on.
  - Depends on: E-01
  - Expected outcome: `aw backlog set <path> --status graduated` on an `open` item writes `- <today> graduated (aw backlog): <msg>`; the same call with `--status open` on an `open` item writes `- <today> same-status (aw backlog): <msg>`; every prior record survives verbatim in both; the label is computed from the file's PRIOR status, so re-reading `item.status` (already mutated) cannot make a genuine transition look like a same-status write.
  - Execution state: pending

- [ ] E-03 `agent_workflows/set_records.py` (`close_on_answer`): pass `label="done"` to the `_reattach_history` call, so the question-answered close records the transition it actually performs. The call becomes `_backlog._reattach_history(text, rendered, "done", "question answered; close-on-answer", label="done")`.

    THIS IS THE ITEM THAT DISCHARGES `eikajx`'s ACCEPTED DEBT. `eikajx` E-01 routed `close_on_answer` through `_reattach_history` (correctly, to stop it destroying prior records) and its review then measured that the emitted label could not be the `done (aw set)` its own Expected outcome demanded, accepted `set (aw backlog)`, and filed the asymmetry as `awqzuh` with an explicit instruction not to widen the shared writer inside that plan's scope. This plan is the widening, deliberately scoped, so the instruction is honored rather than contradicted.

    CHANGE NOTHING ELSE IN `close_on_answer`. The `evaluate_blocking_close` refusal stays exactly where `rendrop` E-08 put it, AFTER rendering and BEFORE `core.atomic_write`, and still receives the reattached text; the function's signature, its `ValueError` refusal shape, and its single-`repo_root` coupling are untouched (`gatedir` `9vglxd` OQ-01 resolved that split against).
  - Depends on: E-01
  - Expected outcome: `close_on_answer` on a `blocked` item writes `- <today> done (aw backlog): question answered; close-on-answer` as the FIRST record, with every prior record intact and no re-dated `created` line; the release-gate refusal still raises `ValueError` on an un-handed-off gate and still writes nothing.
  - Execution state: pending

### Task group 2: correct the two tests this change breaks, and fence the parity

- [ ] E-04 Correct the two EXISTING tests in `tests/test_backlog.py` that pin the old label. Both were measured to FAIL against the probe of E-01 through E-03, and neither failure indicates a regression: each test asserts the very string this plan deliberately changes.

    (a) `BacklogPreservationTests::test_close_on_answer_preserves_prior_history_records` asserts `self.assertIn("set (aw backlog)", history_lines[0])`. Measured failure: `AssertionError: 'set (aw backlog)' not found in '- 2026-09-30 done (aw backlog): question answered; close-on-answer'`. Change that assertion to `done (aw backlog)`. DO NOT WEAKEN IT to a substring that would pass either way (for example asserting only `(aw backlog)`): the label is now the contract and the test is its pin. Leave the other four assertions in that test exactly as they are; they pin the preservation property `eikajx` restored and this plan must not disturb (4 records, close record first, the three originals byte-identical, no re-dated `created` line).

    (b) `BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` normalizes the two spellings' output before comparing, with `.replace("set (aw backlog)", "HIST_ACTOR")` on the `--status` side and `.replace("same-status (aw set)", "HIST_ACTOR")` on the positional side. That normalization is what makes the test pass DESPITE the asymmetry, so it must be updated to the new labels: the `--status` side becomes `.replace("same-status (aw backlog)", "HIST_ACTOR")`. Measured failure against the probe: `'- 2026-09-30 same-status (aw backlog): exempted reason' != '- 2026-09-30 HIST_ACTOR: exempted reason'`. Note WHY only the actor now needs normalizing at all: after E-02 the two records differ ONLY in the parenthesis, which is the asymmetry this plan deliberately keeps, so the test's normalization shrinks from hiding a label difference to hiding an actor difference. Record that in a comment beside the replace, so a later reader does not restore the old string believing it to be a fixture detail.

    Add no new assertions to either test here; E-05 owns the new coverage.
  - Depends on: E-02, E-03
  - Expected outcome: both named tests pass; test (a) now asserts `done (aw backlog)` and still asserts all four preservation properties; test (b)'s `--status`-side normalization reads `same-status (aw backlog)` and carries a comment stating that only the ACTOR asymmetry is being normalized away and why that asymmetry is intended.
  - Execution state: pending

- [ ] E-05 Author `tests/test_history_label_parity.py` fencing the new contract across BOTH spellings, so the asymmetry cannot silently return. Every test must DRIVE a surface and assert on the written file; none may read production source with `inspect`/`ast`/regex, count callers, or assert docstring text (`AGENTS.md`, GUIDING_PRINCIPLES P16). Reach the `--status` spelling through `cli.main(["backlog", "set", <path>, "--status", ..., "--no-commit", "--dir", ...])` and the positional spelling through `cli.main(["backlog", "set", <status>, <id6>, "--yes", "--no-commit", "--dir", ...])`, following the pattern `tests/test_history_provenance.py` already uses; pass `--no-commit` on every invocation (`rendrop` F-12). Read the written records through `attention._history_section_lines` + `attention_contract.HISTORY_RECORD_RE`, the shared readers, rather than re-deriving the block boundary.

    Cover, each as a named test:
    (a) a GENUINE transition (`open -> graduated`) through the `--status` spelling records the label `graduated`;
    (b) the same transition through the POSITIONAL spelling records the label `graduated`, and the two records differ ONLY in the actor parenthesis (assert this by normalizing the actor and comparing the whole record, so a future divergence in date, label, or message fails);
    (c) a SAME-STATUS write (`open -> open` with an explicit `--message`) records `same-status` through BOTH spellings;
    (d) the transition label does NOT come at the cost of the preservation property: a 3-record item taken through the `--status` spelling ends with 4 records, the new one first and the three originals byte-identical (this is the `eikajx` E-08 property, re-pinned here because E-01 edits the function that provides it);
    (e) a caller passing NO `label` still gets `set` (the legacy default), driven through `backlog._reattach_history` directly since no CLI surface exercises the default after E-02 and E-03; assert the emitted record string and the preserved priors.

    Case (e) is the one case that calls a private function directly, and that is deliberate: the default's whole purpose is to protect a caller that does not yet exist, so no CLI path can reach it. It still asserts an OUTCOME (the returned text) and not a source property, so P16 holds.

    PRE-CHANGE FAIL/PASS SPLIT, to be stated honestly in the report: (a), (b), (c) and (e) are NEW pins of NEW behavior, so (a), (b) and (c) MUST fail on the base commit (the `--status` side writes `set` there) and (e) MUST pass (the default is today's behavior). (d) MUST pass on the base commit; it pins a property `eikajx` already shipped, and demanding it fail first would be demanding a test lie. Do not manufacture a failure for (d) or (e).
  - Depends on: E-02, E-03
  - Expected outcome: a new test module whose five named cases all pass after E-01 through E-03; (a), (b) and (c) demonstrably FAIL on the base commit with the `set` label in the failure message; (d) and (e) pass on the base commit and pin thereafter; no test in the module reads production source text.
  - Execution state: pending

### Task group 3: record the user-visible change and reconcile the tree

- [ ] E-06 Add ONE `CHANGELOG.md` entry under the `## 2.0.0 (pending)` heading recording what a USER sees: a backlog item's history record now names the transition (`graduated`, `done`, `same-status`) whichever spelling of `aw backlog set` was used, instead of the uninformative `set` on one of them. Describe only the user-visible effect, name no private helper, and write no em or en dashes (user-facing prose, `AGENTS.md`). Place it beside the existing history-provenance entry that `eikajx` E-07 wrote ("a backlog item closed through the question-answered path now keeps its full workflow history..."), since the two describe the same surface and a reader benefits from finding them together.

    DO NOT FILE THE DEDUP ASYMMETRY HERE: IT IS ALREADY FILED. Backlog `r74211` was created at AUTHORING time (not deferred to execution), carrying both measured outputs, the name of the predicate `backlog.run_set` fails to call, the reason it was fenced out of this plan, and two implementation hazards a later executor would otherwise rediscover (the unconditional sidecar write, and `apply_status_change`'s `_write_history_anyway` branch). It is cited as the carrier of this plan's fourth Deferred row. Verify it still resolves rather than filing a second copy.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: one CHANGELOG entry in the file's established voice, naming only the user-visible effect, containing no em or en dash, and sitting beside the existing history-provenance entry; backlog `r74211` still resolves via `aw find r74211` and is unchanged by this item.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16). No test in this plan may read production source with `inspect`/`ast`/regex, count callers, or assert a docstring's text. A label change is verified by DRIVING the setter and reading the written file.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; `-n0` is forbidden (several times slower here) and a second `-q` suppresses the `N passed` line this plan requires pasted.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- The inline history block's boundary is a measured subtlety documented in `backlog._prior_history_records`: the block ends at the first line that is neither blank nor a column-zero `- ` bullet, and a record MUST start at column zero, because on legacy item `tk1gqo` an unbounded scan promoted five indented prose-quoted example lines into the item's provenance and turned 11 records into 17. Any code or test this plan touches that reads history reuses that helper or `attention._history_section_lines`; neither re-derives the boundary.
- INLINE HISTORY IS THE DURABLE HOME and the sidecar is a machine-local activity log (maintainer ruling 2026-09-10, `vhbvwz` OQ-01; `record_history.append_advisory` states it in its own docstring). That is why a cosmetic label defect in the inline record is worth fixing at all: the inline block is what survives a clone.
- The record grammar is `- <date> <label> (<actor>): <message>`, and the LABEL and ACTOR are distinct fields with distinct jobs: the label names the event, the parenthesis names the writer. `plan_readiness._HISTORY_RECORD_PARTS_RE` parses them separately as `mid` and `actor`. This plan changes the label on one path and deliberately leaves the actor alone.

## Findings

Every finding below was measured in this lane worktree at HEAD `4b7f2582` (the lane's base commit), by driving the real surfaces over identical fixtures in temporary repositories.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | LOW (CONFIRMED) | Drove both spellings on identical `open` items and took the whole file. `--status`: `- 2026-09-30 set (aw backlog): carrier handed off`. Positional: `- 2026-09-30 graduated (aw set): carrier handed off`. | **THE ASYMMETRY IS REAL AND REPRODUCES EXACTLY AS `awqzuh` DESCRIBES.** `backlog._reattach_history` hardcodes `new_record = f"- {today} set (aw backlog): {msg}"`, so the `--status` spelling cannot name the transition even though `run_set` knows it. `status_set.apply_status_change` builds `hist_entry = f"- {today} {status_tag} ({actor}): {message}"` with `status_tag = norm_status`, so the positional spelling does. BOTH preserved the prior `created` record correctly, so no provenance is at risk; this is queryability, which is why the item is `chore`. |
| F-02 | N/A (SCALE) | Parsed every `.backlog.md` under `.aw/records/backlog/` with the same bounding `_prior_history_records` uses and counted leading label tokens: `created` 697, `set` 476, `graduated` 263, `done` 187, `open` 90, `note` 29, `same-status` 8, `blocked` 7, and 10 one-off hand-written tokens. Total 1768 records. | **476 RECORDS CARRY THE UNINFORMATIVE LABEL, AND THE STATUS-NAMING CONVENTION IS ALREADY DOMINANT.** `graduated` + `done` + `open` + `blocked` + `same-status` = 555 records already name their transition, so this plan aligns the minority path with the established majority rather than inventing a convention. NOTE the count differs from `awqzuh`'s (`set` 318, total not stated): the item measured on 2026-09-28 and the corpus has grown since, so the item's numbers are not wrong, merely older. Re-measure rather than quoting either number at execution time. |
| F-03 | MEDIUM | Searched the whole repository for `_reattach_history`. Two call sites: `backlog.run_set` and `set_records.close_on_answer`. Both are updated by this plan (E-02, E-03). | **THE BLAST RADIUS IS TWO CALLERS, WHICH IS WHY A DEFAULTED PARAMETER IS SUFFICIENT AND A REQUIRED ONE IS GRATUITOUS.** `awqzuh` warns that `_reattach_history` is "the shared preserving writer that plan vhbvwz E-08 built" and that "every `--status` transition goes through it", which is true and is exactly why the default matters: a required parameter would `TypeError` for any caller arriving on a long-lived branch, while a defaulted one leaves that caller emitting today's record. |
| F-04 | HIGH (BLAST RADIUS) | Applied a THROWAWAY probe implementing E-01 through E-03, ran the suite bare, then reverted with `git checkout --` and re-ran `tests/test_backlog.py` green (44 passed). Probe run: `2 failed, 3385 passed, 2 skipped, 3 warnings in 61.42s`. | **EXACTLY TWO TESTS BREAK, BOTH ARE LABEL PINS, AND BOTH ARE IN ONE FILE.** `test_close_on_answer_preserves_prior_history_records` (`'set (aw backlog)' not found in '- 2026-09-30 done (aw backlog): question answered; close-on-answer'`) and `test_release_exempt_setter_roundtrip_and_parity` (normalization mismatch on the same-status record). No other test in 3385 depends on the old label. E-04 owns both. THE EXECUTOR MUST RE-DERIVE THIS BASELINE on the tree as it finds it rather than trusting this row: the corpus and the suite both move. |
| F-05 | MEDIUM (DESIGN) | Probed the status-only label first and re-ran the parity test: it still failed, with `- 2026-09-30 open (aw backlog): exempted reason` against `- 2026-09-30 same-status (aw set): exempted reason`. Adding the `same-status` discrimination made both sides emit `same-status`. | **A STATUS-ONLY LABEL IS INSUFFICIENT AND WOULD BE A NEW FALSEHOOD.** `apply_status_change` tags a true same-status write `same-status` deliberately ("so verdict readers do not mistake it for a review record"). Labelling such a write `open` would assert a transition that did not happen, which is worse than today's vague `set`. Hence E-02 carries both halves, and the existing parity test is the surface that caught it. |
| F-06 | MEDIUM (SEPARATE DEFECT, NOT FIXED HERE) | At base, two identical same-status `--status` calls produced TWO identical records (`- 2026-09-30 set (aw backlog): metadata only` twice); two identical positional calls produced ONE. | **THE TWO SPELLINGS ALSO DISAGREE ON DEDUPLICATION, AND THAT IS A DIFFERENT BUG.** `apply_status_change` consults `same_status_message_is_duplicate`, whose docstring records the measured three-identical-records run that motivated it; `backlog.run_set` consults nothing. This decides whether a write HAPPENS rather than what a record SAYS, so its blast radius and its review are different. FILED at authoring time as backlog `r74211`, which carries both measured outputs, the uncalled predicate's name, and two implementation hazards (the unconditional sidecar write, and `apply_status_change`'s `_write_history_anyway` branch). Do not fix it in this plan. |
| F-07 | LOW (CONSUMER SAFETY) | Drove `production_checks.backlog_graduate_legitimacy` over four crafted items. With today's `set` label and a message lacking the word `graduated`: FINDING. With the new `graduated` label and the same message: CLEAN. With the runner's real message (`graduated by run run-X: abc123`): CLEAN both before and after. | **THE ONE CONSUMER THAT READS A BACKLOG RECORD'S TEXT IS MADE STRICTLY MORE CORRECT, NOT LESS.** That check's clause 4 tests `if "graduated" not in newest`, matching the WHOLE record line rather than the label, so after this change the label itself satisfies it. The runner's own message already contains the word, so its live path is unaffected either way; the improvement is confined to a hand-written message. `attention_contract.HISTORY_RECORD_RE` is `^- (?P<date>\d{4}-\d{2}-\d{2}) .+$`, so only the DATE is grammatical there, and `ipd_lifecycle._plan_status_events` gates on `_PLAN_STATUS_VOCAB` and applies to PLANS. No consumer is broken by the change. |
| F-08 | N/A (PROVENANCE) | `eikajx`'s `## Workflow history` and its E-01 prose both record the acceptance and the filing of `awqzuh`. | **THIS PLAN IS THE DEBT `eikajx` DELIBERATELY DEFERRED, NOT A CONTRADICTION OF IT.** `eikajx` E-01 says "ACCEPT THE `set (aw backlog)` LABEL AND DO NOT WIDEN `_reattach_history` TO TAKE ONE", with the first reason being that its OWN scope fence forbade it. That fence bound `eikajx`, not the repository. Executing this plan discharges the item that fence created. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/backlog.py` (`_reattach_history`): add `label: str = "set"`; build the record with it; document why (E-01).
2. `agent_workflows/backlog.py` (`run_set`): compute the label from the PRIOR status, `same-status` when the status does not move, and pass it (E-02).
3. `agent_workflows/set_records.py` (`close_on_answer`): pass `label="done"` (E-03).
4. `tests/test_backlog.py`: correct the two label pins the change breaks, preserving every other assertion (E-04).
5. `tests/test_history_label_parity.py`: new module fencing both spellings over transition, same-status, preservation, and the legacy default (E-05).
6. `CHANGELOG.md`: one user-facing entry (E-06). The dedup asymmetry this plan fences out is ALREADY filed as backlog `r74211`, created at authoring time rather than deferred to execution.

## Deferred / out of scope (with reason)

- THE ACTOR ASYMMETRY (`(aw backlog)` versus `(aw set)`) IS NOT A DEFECT AND IS DELIBERATELY KEPT. The parenthesis is where every writer in this tree records its own identity (`created (aw backlog)`, `note (aw backlog)`, `note (aw specs)`, `migrated (aw specs)`), so two different code paths naming themselves differently is truthful attribution. `same_status_message_is_duplicate` documents that it deliberately does NOT compare the actor ("the same note re-asserted under a different actor string is still the same note"), so no consumer is confused by it. Unifying it would also require choosing which lie to tell, since neither path is the other.
  - Carrier-Declined: not a defect; the actor field's job is to name the writer, and the two writers genuinely differ, so there is no outstanding work to carry
- THE 476 EXISTING `set` RECORDS ARE NOT REWRITTEN. They are committed history; rewriting them would assert that a past transition recorded something it did not, which is precisely the forgery `_reattach_history`'s own docstring exists to prevent. The fix is forward-only.
  - Carrier-Declined: rewriting committed history is prohibited rather than postponed, so there is nothing for a carrier to pick up later
- `status_set.apply_status_change` IS NOT TOUCHED. It already writes the correct label, it is the shape this plan matches, and it serves plans, specs, prompts and releases as well as backlog items, so editing it would widen the blast radius from one function with two callers to the whole setter surface.
  - Carrier-Declined: the function is already correct on this axis; no defect exists there to carry
- THE DEDUPLICATION ASYMMETRY (F-06) IS FILED, NOT FIXED. At base, two identical same-status `--status` calls appended TWO identical records while two identical positional calls appended ONE, because `status_set.apply_status_change` consults `same_status_message_is_duplicate` and `backlog.run_set` consults nothing. It changes whether a write HAPPENS rather than what a record SAYS, so it carries a different blast radius and deserves its own review and its own tests.
  - Carrier: r74211
- THE 77 LEGACY OLDEST-FIRST ARTIFACTS, the per-artifact metadata store, and re-tracking `.aw/records/history.jsonl` are all untouched; each is owned elsewhere and none is reachable from a label change.
  - Carrier: jhrao5

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `agent_workflows/backlog.py` (E-01, E-02), `agent_workflows/set_records.py` (E-03), `tests/test_backlog.py` (E-04), `tests/test_history_label_parity.py` (E-05), `CHANGELOG.md` (E-06).
- Under-scope: the backlog item E-06(b) files is written under `.aw/records/backlog/open/` by `aw backlog new` and is NOT declared in `Scope-Paths`, because its path is not knowable at authoring time (the id6 is minted at execution). Declare it during execution if the finalize scope reconciliation requires it, and record the widening in the transition message; this note is the authorization to do so. The plan's own file under `.aw/records/plans/**` needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. Baseline RE-DERIVED on the tree as found before any edit, so the delta is honest rather than compared against F-04's number.
- The two corrected tests named in E-04, run individually and named in the evidence.
- The new `tests/test_history_label_parity.py`, with its pre-change fail/pass split demonstrated on the base commit (via `git stash` or a scratch checkout) and reported as measured, not as authored.
- `AW_NO_REEXEC=1 aw backlog check`, `AW_NO_REEXEC=1 aw specs check` and `AW_NO_REEXEC=1 aw sanitize --agent`, each expected to exit 0 (all three measured exit-0 at authoring time).
- `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw attention --check`: BOTH exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET, not an exit code. Measured at authoring time: `aw check` exit 1 with 58 findings (35 `check.plan-spec-link-missing`, 11 `check.ipd-uncarried-obligation`, 4 `check.ipd-lint-diagnostic`, 2 `check.ipd-carrier-finished-unverified`, 2 `check.lifecycle-transition-invalid`, 2 `check.name-nonconformant`, 1 `check.scope-path-target-stale`, 1 `check.system-layout-missing`); `aw attention --check` exit 1. Capture the named finding set before and after and require them IDENTICAL. Do NOT attempt to make either exit 0, and specifically do not "fix" another plan's conformance finding or another lane's state: that is a co-worker's work in a shared checkout.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing.

## Spec / documentation sync

No spec amendment is required, and that is a measured conclusion rather than an omission. The history RECORD GRAMMAR is not specified in any `.spec.md`: searching the spec tree for `HISTORY_RECORD_RE` and for the `- <date> <label> (<actor>)` shape returns nothing, and spec `20260813-1833-01-attention-visible-backlog-tier.spec.md` G3 says only that `set` should "append history" without constraining the label. Spec `20260818-1525-02-sidecar-metadata-and-history.spec.md` governs WHERE history lives (inline, durable) and not what a record's label says; `eikajx` E-06 already amended its stale passages and this plan does not disturb that.

Two DOCUMENTATION surfaces describe this behavior and both remain accurate after the change, so neither is edited: `.aw/records/backlog/README.md` says history is recorded inline, newest first, with priors kept (all still true), and `docs/artifact-lifecycles.md` item 4 says "Every status change adds a history line" (still true, and it names no label). If a reviewer wants the label convention written down, the right home is `.aw/records/backlog/README.md`'s record-shape block, which already shows `- YYYY-MM-DD <event> (<actor>): <one line>`: that placeholder `<event>` is now honest for BOTH spellings where before it was honest for only one, which is an argument that the documentation was already describing the intended behavior and the code was the thing out of step.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a transcript of a python session that calls `backlog._reattach_history` TWICE on the same 3-record fixture, once WITHOUT `label` and once with `label="done"`, printing the full returned text both times. The no-`label` call must show `set (aw backlog)` and the `label="done"` call must show `done (aw backlog)`; both must show all three prior records verbatim with their original dates, newest-first, and no re-dated `created` line. ALSO paste `git diff -- agent_workflows/backlog.py` restricted to `_reattach_history` and confirm by inspection that the message fallback (`msg = message.strip() or ...`), the `prior = _prior_history_records(old_text)` source, and the body re-emission are unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the three rows of the parity table measured on the POST-change tree, each produced by driving `cli.main(["backlog", "set", <path>, "--status", <target>, ...])` and printing the written file's first record: `open -> graduated` must read `graduated (aw backlog)`, `open -> open` must read `same-status (aw backlog)`, and `open -> done` must read `done (aw backlog)`. Then paste the matching positional-spelling record for each and confirm the only difference is the actor parenthesis. FALSIFIER REQUIRED: also paste a run proving the label is read from the PRIOR status and not from the already-mutated `item.status` - drive a genuine `open -> graduated` transition and show the label is `graduated` and NOT `same-status` (a naive `item.status` read would produce `same-status` for every call, since `run_set` sets `item.status = new_status` before the render).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the full written file from driving `set_records.close_on_answer` on a `blocked` item carrying three real records. It must show FOUR records, the first reading `- <today> done (aw backlog): question answered; close-on-answer`, the three originals byte-identical with their original dates, and no `created` line dated today. Separately paste the refusal path still working: a `close_on_answer` call on an item carrying an un-handed-off `- Blocks-Release:` must raise `ValueError` and leave no file written under `done/` (show the exception text and the empty directory listing).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the actual output of `python3 -m pytest tests/test_backlog.py -o addopts=""` showing both named tests passing by name (`test_close_on_answer_preserves_prior_history_records`, `test_release_exempt_setter_roundtrip_and_parity`), plus the per-test counts that clearing `addopts` provides. ALSO paste `git diff -- tests/test_backlog.py` and confirm by inspection that test (a) retains its four preservation assertions (4 records, close record first, originals equal, no re-dated `created`) and that test (b)'s comment states which asymmetry is being normalized and why.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_history_label_parity.py -o addopts=""` green with all five cases named. THEN paste the PRE-CHANGE run of the same module against the base commit (stash the production changes, or run in a scratch checkout at the base commit) showing cases (a), (b) and (c) FAILING with the `set` label visible in the failure output, and (d) and (e) PASSING. Report the split as MEASURED; if it differs from E-05's authored expectation, say so and explain which case moved rather than adjusting a test to match the prediction.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new `CHANGELOG.md` entry verbatim and confirm it contains no em or en dash (show the check you ran, for example a grep for the two characters returning nothing on that entry). Paste `AW_NO_REEXEC=1 aw find r74211` resolving to the filed dedup item, and `git diff -- .aw/records/backlog/` showing NO change to it (this item must not edit the carrier it cites). FINALLY paste the whole-tree gate pass: the BARE `python3 -m pytest` with its `N passed` line and a baseline re-derived on the pre-change tree; `aw backlog check`, `aw specs check` and `aw sanitize --agent` each exiting 0; `aw check` and `aw attention --check` reporting an IDENTICAL named finding set before and after (both exit 1 on pre-existing conditions, which is not this plan's failure); `aw ipd lint --phase pre-transition` conforming; and `git diff --cached --name-only` matching this plan's declared scope with nothing belonging to a co-worker.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is NOT approved by its own authorship. It carries `- Status: to-review` and no `- Readiness:` field, because readiness is an OUTPUT of `/plan-review` and writing one here would forge a verdict no review produced (`AGENTS.md`). Execution requires a human `approved` transition recorded through `aw ipd set approved <id6> --by-human`.

At execution: run `aw ipd begin` first, perform the items in dependency order, and do not mark a `V-*` complete from the matching `E-*` checkmark. The terminal transition is `aw ipd finalize`; do not `git mv` this plan by hand, and do not move it to `executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence. Commit through `aw commit <plan> -- <paths>`, path-scoped to this plan's `Scope-Paths` plus the one backlog item E-06(b) creates; never `git add -A`, never `--no-verify`, and never push.
