# IPD: Derive aw commit's default message as work(id6): plan title instead of the full plan path

- Date: 2026-09-26
- Kind: child
- Concern: `aw commit <plan> -- <paths>` WITHOUT `-m` writes the one-line message `work: <full repo-relative plan path>`, from `work_cmd.run_commit`: `message = getattr(args, "message", None) or f"work: {plan_rel}"`. Re-measured at HEAD `61ef21d8`: 41 of 2396 commit subjects since 2026-09-01 start with `work: `, while 702 use the `type(<id6>):` shape. The default spends the whole subject on a roughly 110-character path already recoverable from the diff, carries no id6 in a greppable `type(scope)` position, and is the one shape this repository's history does not otherwise use, at exactly the moment an agent is most likely to accept a default (backlog `qivywd` records an agent having to amend after taking it).
- Scope: IN: (a) a small pure helper in `work_cmd` that derives the default subject from the plan text and filename: `work(<id6>): <H1 title with a leading "IPD: " removed>`, falling back to `work(<id6>): <filename slug>` when the title is missing or empty, and to the current `work: <plan_rel>` when no id6 can be found at all; the id6 is read from the plan's `- Id:` field, falling back to the clustered filename's id6 (`artifact_naming.parse_clustered_prefix`); (b) `run_commit` uses that helper only when `-m` is absent; (c) behavioral tests committing in a scratch git repo and reading `git log -1 --format=%s`. OUT: changing the `--no-plan` rule (it still requires `-m`); changing an explicit `-m`; truncating or reformatting long titles; any lifecycle commit subject (`artifact_core.lifecycle_commit_prefix`), which is a different producer with a security-relevant fixed form.
- Scope-Paths: agent_workflows/work_cmd.py, tests/test_commit_default_message.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: qivywd
- Set: commitmsg
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: isgno7

## Workflow history

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED, none deferred, none open; 5 decisions D-1..D-5 recorded. Reviewed at HEAD ba22551f. `aw ipd lint --phase author --agent` reported `clean`/`findings: 0` before revision; the lane-input copy was byte-identical to the tracked file and the tree was clean, so no pre-review snapshot. THIS IS A WELL-BUILT SMALL PLAN and I reproduced its defect end to end: driving `cli.main(["commit","wk0001","--dir",<repo>,"--","src/f.py"])` on the `test_work_gate_severity` fixture shape yielded subject `work: .aw/records/plans/pending/20260828-wk-01-wk0001-demo.ipd.md`. F-3 and F-4 also hold, and I independently confirmed the collision-safety claim the plan rests on rather than trusting it (`artifact_audit._FINALIZE_SUBJECT_RE` does NOT match `work(isgno7): ...`, and `worktree_lease.commit_subject_is_interrupted_snapshot` does not either). SIX CORRECTIONS, two of which are real defects in the design. (1) THE MIDDLE FALLBACK RUNG IS UNREACHABLE BY ITS OWN MECHANISM: `ipd_lint.parse` collects metadata ONLY AFTER it sees the H1 (`if not seen_h1: ... continue`), so a plan with an absent or empty H1 yields `meta_fields == {}` and `Id == None` as well as an empty title. Driven: `parse("- Id: wk0001\\n\\n## Goal\\nx\\n")` -> `title=''`, `Id=None`. So E-02's "only the id6 exists" rung is dead via that reader and E-04 case (2) would silently exercise the LAST rung instead, passing while proving the opposite of its intent. (2) `work_cmd` ALREADY HAS THE RIGHT READER and the plan proposes a new mechanism beside it: `_plan_id6(text)` is a full-line `- Id:` regex with two existing callers in this same module, and being regex-based it is immune to the H1 problem. E-02 now reads the id6 through `_plan_id6` (with the filename prefix as the second rung) and uses `ipd_lint.parse` for the TITLE only, which is the one thing it is needed for. ALSO: (3) an explicit `-m ""` falls through to the derived default because `or` treats the empty string as falsy, unchanged behavior but now stated and pinned as a case rather than left as a surprise; (4) the history figures drifted between authoring and review (50 of 2556 `work: `, 733 `type(id6)`, versus the authored 41 of 2396), so they are re-stated as context to be re-derived, per the live-artifact convention; (5) a title can legitimately contain backticks, quotes and `$(...)`, which is safe because the message is passed as an argument and never through a shell, now recorded with a case so nobody "sanitizes" it later; (6) the new test file was the only declared test path while E-04 drives `cli.main` through `work_cmd`, so the validation now also re-runs the two existing suites the plan already named. Full record: `.aw/records/reviews/20260926-commitmsg-01-isgno7-derive-aw-commit-s-default-message-as-work-id6-plan-title-in.review.md`.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog qivywd. Authored review-ready; the default-message source and the 41-of-2396 history count were re-measured at HEAD 61ef21d8.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `aw commit`'s default message greppable by id6 and shaped like the rest of this repository's history (`type(<id6>): <summary>`), while an explicit `-m` still wins and `--no-plan` still requires one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD. Paste the `message = ... or f"work: {plan_rel}"` line from `work_cmd.run_commit`, and `git log --since=2026-09-01 --format=%s | grep -c '^work: '` beside the total count. Then, in a scratch git repo with a conformant approved plan under `.aw/records/plans/pending/` (the fixture shape `tests/test_work_gate_severity.py` uses, `_PLAN` with `- Id: wk0001`), run `cli.main(["commit", "wk0001", "--dir", <repo>, "--", "src/f.py"])` and paste `git log -1 --format=%s`.
  - Depends on: none
  - Expected outcome: the subject is `work: .aw/records/plans/pending/<plan filename>`.
  - ALREADY DRIVEN AT REVIEW, so treat this as confirmation: the scratch commit produced subject `work: .aw/records/plans/pending/20260828-wk-01-wk0001-demo.ipd.md` (rc 0). The fixture needs `support.declare_execution_role` and a MODIFIED tracked file to have something to commit; `setUp` commits `src/f.py` first, so change it before invoking `commit`.
  - THE HISTORY COUNTS ARE A LIVE POPULATION AND MOVE; RE-DERIVE THEM AND DO NOT TREAT ANY NUMBER AS THE BAR. Measured at review: 50 of 2556 subjects since 2026-09-01 start with `work: ` and 733 match `^[a-z]+([0-9a-z]{6}): `, against the authored 41 of 2396 and 702. The proportion is the point (the `work: ` shape is rare and the scoped shape dominant), not the figure.
  - Execution state: pending

### Task group 2: derive the default

- [ ] E-02 ADD `work_cmd._default_commit_message(plan_text: str, plan_rel: str) -> str`, pure (no I/O). Read the id6 with THIS MODULE'S EXISTING `_plan_id6(plan_text)` (see the next bullet), falling back to `artifact_naming.parse_clustered_prefix(Path(plan_rel).name).group("id6")`; validate either with `artifact_core.is_valid_id6`. Read the title from `ipd_lint.parse(plan_text).title`, strip whitespace and one leading `IPD: ` prefix. Return `f"work({id6}): {title}"` when both exist; `f"work({id6}): {slug}"` when only the id6 exists, where `slug` is the clustered filename's slug group (`artifact_naming.parse_clustered`), or the filename stem when that does not match; and `f"work: {plan_rel}"` when no id6 is found. Never raise: any parse failure falls through to the next rung. Import `ipd_lint` lazily, as `_plan_scope_paths` already does. Docstring cites `qivywd`.
  - Depends on: E-01
  - Expected outcome: for the fixture plan the helper returns `work(wk0001): Demo work plan`.
  - USE `work_cmd._plan_id6`, NOT `ipd_lint.parse(...).meta_fields`, AND THIS IS A CORRECTNESS FIX RATHER THAN A STYLE PREFERENCE. `ipd_lint.parse` collects the metadata slice ONLY AFTER it has seen the H1 (`if not seen_h1: ... continue`), so a plan with NO H1 or an EMPTY H1 yields `meta_fields == {}` AND an empty title together. Driven at review: `parse("- Id: wk0001\n\n## Goal\nx\n")` -> `title=''`, `Id=None`; `parse("# \n\n- Id: wk0001...")` -> the same. The consequence is that the middle rung ("only the id6 exists") is UNREACHABLE through that reader and E-04 case (2) would silently exercise the LAST rung while claiming to prove the middle one. `_plan_id6` is a full-line `(?m)^- Id:\s*([0-9a-z]{6})\s*$` regex, already defined in this module and already used twice (`run_finish`'s two `plan_id = _plan_id6(text) or plan_path.stem` call sites), so it is both immune to the H1 gate and the established local reader. Reusing it also avoids adding a second id6 mechanism to one module, which is the drift GUIDING_PRINCIPLES P8 forbids.
  - USE `ipd_lint.parse` FOR THE TITLE ONLY, which is the one thing it uniquely provides (fence-aware H1 extraction). An empty `title` is the correct signal to fall to the slug rung; do not also infer the id6 from it.
  - THE TITLE IS NOT SANITIZED AND MUST NOT BE. Measured at review, an H1 may legitimately contain backticks, double quotes and `$(...)`; that is SAFE because the message travels as an argument to `git commit` through `git_commit_helper`, never through a shell, and `compose_message_with_trailers` returns it byte-for-byte when there are no trailers. Do NOT add escaping or quoting: it would corrupt legitimate titles to defend against an injection path that does not exist here. E-04 case (6) pins this.
  - Execution state: pending

- [ ] E-03 USE THE HELPER in `work_cmd.run_commit`: replace the `or f"work: {plan_rel}"` fallback with `or _default_commit_message(text, plan_rel)`, where `text` is the plan text `run_commit` already read for `_plan_scope_paths` (keep it in scope rather than re-reading the file). An explicit `-m` still takes precedence, and the `--no-plan` path is unchanged (it returns 2 before this line when `-m` is absent).
  - Depends on: E-02
  - Expected outcome: E-01's scratch commit now yields subject `work(wk0001): Demo work plan`.
  - `text` IS SAFELY IN SCOPE, AND THE REASON IS THE `--no-plan` GUARD, SO DO NOT REMOVE THAT GUARD. Verified at review: `text` is assigned inside `if plan_path is not None:`, which would leave it unbound on the `--no-plan` path; but `--no-plan` without `-m` already `return 2` earlier, and `--no-plan` WITH `-m` never evaluates the right-hand side of the `or`. So the reference is safe only while both facts hold. Keep the `--no-plan` refusal exactly as it is, and do not hoist the default's computation above the `or`, which would evaluate it eagerly and raise `UnboundLocalError` on the `--no-plan` path. E-04 case (4) is the regression test for that, so it must assert the exit code AND that no commit was created.
  - `-m ""` FALLS THROUGH TO THE DERIVED DEFAULT, because `or` treats the empty string as falsy. That is TODAY's behavior too (an empty `-m` currently yields `work: <plan_rel>`), so this item does not change it and must not "fix" it silently; E-04 case (5) pins it so the behavior is recorded rather than accidental. If the maintainer wants an explicit empty message honored, that is a separate change to the argument handling.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-04 ADD `tests/test_commit_default_message.py`, behavioral only (maintainer's 2026-09-26 ruling: no source-text pins). Build scratch repos as `tests/test_work_gate_severity.WorkGateSeverityTest.setUp` does (including `tests.support.declare_execution_role(self)`), drive `cli.main(["commit", <selector>, "--dir", <repo>, ...])`, and read `git log -1 --format=%s`. Cases: (1) no `-m`, plan with `- Id:` and an `# IPD: <title>` H1 -> `work(wk0001): <title>`; (2) no `-m`, plan whose H1 is absent or empty -> `work(<id6>): <filename slug>`, which is the rung the H1 gate makes unreachable via `meta_fields` and is therefore the case that PROVES E-02 used `_plan_id6`; (3) explicit `-m "custom subject"` -> exactly `custom subject`; (4) `--no-plan` without `-m` -> exit 2, message names `requires -m/--message`, and no new commit is created (HEAD unchanged); (5) `-m ""` -> falls through to the derived default, pinning today's `or` semantics rather than changing them; (6) a title containing backticks, double quotes and `$(...)` survives VERBATIM in the subject, pinning that nothing sanitizes it; (7) unit-level: `_default_commit_message` on text with no `- Id:` and a non-clustered filename returns `work: <plan_rel>` unchanged.
  - Depends on: E-03
  - Expected outcome: all pass; cases (1) and (2) FAIL before E-03; cases (3), (4), (5) pass before and after (controls); (6) and (7) exist only after the change and are shown passing after.
  - CASE (2) IS THE LOAD-BEARING TEST AND MUST BE BUILT TO ACTUALLY REACH ITS RUNG. Give the fixture plan a real `- Id: wk0001` line and NO H1 (or an empty `# `), keep its clustered filename so the slug resolves, and assert the subject is `work(wk0001): demo`. Measured at review, that plan text yields `meta_fields == {}` from `ipd_lint.parse`, so an implementation that read the id6 from `meta_fields` would produce `work: <plan_rel>` and this assertion would FAIL: that is exactly the discrimination the case exists for. Do not weaken it to accept either output.
  - Execution state: pending

- [ ] E-05 CONFIRM NO SUBJECT READER REGRESSES, which the plan asserted from one grep and which is the only way this change could break something outside its own surface. Re-run the search at the executing HEAD over `agent_workflows/` for consumers of commit SUBJECTS, not just for the literal `work: `: `rg -n 'format=%s' agent_workflows/` plus the readers it finds. Then drive the two that matter, both of which key on a prefix and so could in principle be confused by a new `work(<id6>):` shape: `artifact_audit._FINALIZE_SUBJECT_RE` must NOT match `work(<id6>): <title>`, and `worktree_lease.commit_subject_is_interrupted_snapshot` must return False for it. Paste both results.
  - Depends on: E-03
  - Expected outcome: no reader matches the new shape; the finalize-evidence and interrupted-snapshot classifications are unchanged.
  - MEASURED AT REVIEW, so this is confirmation rather than discovery: `_FINALIZE_SUBJECT_RE.match("work(isgno7): ...")` -> None while `"lifecycle(isgno7): finalize ..."` -> match, and the snapshot predicate is prefix-anchored on `WIP INTERRUPTED SNAPSHOT (not finished work):`. ALSO NOTE, and report it rather than editing it: `runner_shared._commit_subject`'s docstring asserts as verified that a subject in this repository "names a plan path under `.aw/records/`", quoting two measured peers whose subjects are `work: .aw/records/plans/pending/...`. That claim becomes stale for future commits. It is a REFUSAL-RENDERING helper that only truncates to 120 chars, so nothing breaks, and `runner_shared.py` is deliberately NOT in `- Scope-Paths:`; name it in the finalize report as a known-stale comment for a follow-up rather than widening this plan.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The repository's commit history is Conventional-Commits-shaped with an id6 scope (`plan(<id6>): ...`, `lifecycle(<id6>): ...`, `feat(runner): ...`); 702 of 2396 subjects since 2026-09-01 match `^[a-z]*(<6 chars>):`.
- `lifecycle(<id6>)` subjects are produced ONLY by `artifact_core.lifecycle_commit_prefix` / `finalize_commit_subject`, and readers match `lifecycle(<id6>): finalize` narrowly ("a looser match would let an ordinary work commit that merely names the plan pass as finalize evidence"). A `work(<id6>):` subject cannot collide with that keyword.
- No code in `agent_workflows/` parses `work: ` subjects (grep for `"work: "` and `work(` found only the producer line), so changing the default breaks no reader.
- `work_cmd._plan_scope_paths` already parses the plan with `ipd_lint.parse`, imported lazily; `ipd_lint.parse(text).title` holds the H1 (`IPD: <title>`) and `.meta_fields["Id"]` the id6 (measured on a real plan).
- BUT `ipd_lint.parse` GATES METADATA ON THE H1: it skips every line until it sees one, so a plan with no H1 (or an empty one) returns BOTH an empty `title` AND an empty `meta_fields`. The two cannot be obtained independently from that reader (F-5).
- `work_cmd` ALREADY HAS `_plan_id6(text)`, a full-line `- Id:` regex with two callers in this module, which is immune to that gate and is the established local id6 reader (F-6). Prefer it over adding a second mechanism.
- The commit message reaches git as an ARGUMENT, never through a shell, and `git_commit_helper.compose_message_with_trailers` returns it byte-for-byte when there are no trailers, so a title's punctuation needs no escaping (F-8).
- `text` in `run_commit` is bound only inside `if plan_path is not None:`; the `--no-plan` path is safe ONLY because it returns 2 earlier when `-m` is absent and short-circuits the `or` when `-m` is present. Do not hoist the default's computation out of the `or`.
- The pre-commit hooks are pinned to `default_stages: [pre-commit]` (`.pre-commit-config.yaml`), so no commit-msg hook constrains the subject.
- Tests run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-4 were measured by the author at HEAD `61ef21d8`. F-5 through F-9 were measured at
`/plan-review` (2026-09-26, HEAD `ba22551f`), each by DRIVING the parser, the CLI, or the reader
concerned rather than by reading the code.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `work_cmd.run_commit` | The default subject is `work: <plan_rel>`. | `message = getattr(args, "message", None) or f"work: {plan_rel}"`; CONFIRMED end to end at review: the scratch commit's subject was `work: .aw/records/plans/pending/20260828-wk-01-wk0001-demo.ipd.md` |
| F-2 | INFO | git history | The `work: ` shape is rare and the scoped shape dominant. RE-MEASURED at review: 50 of 2556 subjects since 2026-09-01 versus 733 scoped (authored: 41 of 2396 versus 702). A live population; re-derive rather than citing either figure. | `git log --since=2026-09-01 --format=%s \| grep -c '^work: '` -> 50; `grep -cE '^[a-z]+\([0-9a-z]{6}\): '` -> 733; total 2556 |
| F-3 | INFO | readers | Nothing parses `work: ` subjects. CONFIRMED and WIDENED at review: the search was redone for subject CONSUMERS rather than for the literal, and the two prefix-keyed readers were driven. | `rg -n 'format=%s' agent_workflows/` -> 5 sites; `artifact_audit._FINALIZE_SUBJECT_RE.match("work(isgno7): ...")` -> None; `worktree_lease.commit_subject_is_interrupted_snapshot("work(isgno7): ...")` -> False |
| F-4 | INFO | `--no-plan` | Already refuses without `-m` before the message line. | `"error: aw commit --no-plan requires -m/--message (there is no plan to derive the ..."`, returning 2 |
| F-5 | MEDIUM | E-02's proposed id6 reader, and `ipd_lint.parse` | **THE MIDDLE FALLBACK RUNG IS UNREACHABLE THROUGH THE PROPOSED MECHANISM, AND THE TEST FOR IT WOULD HAVE PASSED WHILE PROVING THE OPPOSITE.** `parse` collects the metadata slice only after the H1 (`if not seen_h1: ... continue`), so a plan with an absent or empty H1 loses BOTH the title and every metadata field together. Reading the id6 from `meta_fields` therefore cannot produce the "id6 but no title" state E-02's second rung is for, and E-04 case (2) would land on the third rung (`work: <plan_rel>`) unnoticed. | driven: `parse("- Id: wk0001\n\n## Goal\nx\n")` -> `title=''`, `meta_fields.get("Id") is None`; `parse("# \n\n- Id: wk0001...")` -> same; `parse("# Just A Title\n\n- Id: wk0001...")` -> `Id='wk0001'`; the `seen_h1` gate read in `ipd_lint.parse` |
| F-6 | MEDIUM | `work_cmd._plan_id6` | **THE MODULE ALREADY HAS THE CORRECT READER AND THE PLAN PROPOSED A SECOND MECHANISM BESIDE IT.** `_plan_id6(text)` is a full-line `- Id:` regex with two existing callers in this same module, and being regex-based it is immune to F-5's H1 gate. Reusing it fixes F-5 and avoids a second id6 mechanism in one module. | `_plan_id6`'s body read; callers at `run_finish`'s two `plan_id = _plan_id6(text) or plan_path.stem` sites |
| F-7 | INFO | `run_commit`'s `or` expression | `-m ""` falls through to the DERIVED default, because the empty string is falsy. This is today's behavior (an empty `-m` currently yields `work: <plan_rel>`), so the change preserves it; recorded because it is easy to alter accidentally and worth pinning. | `("" or "work: x")` -> `"work: x"`; the `getattr(args, "message", None) or ...` expression |
| F-8 | INFO | title content, and the commit path | A title may contain backticks, double quotes and `$(...)`, and that is SAFE: the message is passed as an argument to git through `git_commit_helper`, never through a shell, and `compose_message_with_trailers` returns it byte-for-byte when there are no trailers. So no sanitizing is needed, and adding any would corrupt legitimate titles. | driven: `parse` preserves `` `backticks` ``, `"quotes"` and `$(cmd)` in `.title`; `compose_message_with_trailers`'s "byte-for-byte identical: the existing-caller guarantee" |
| F-9 | LOW | `runner_shared._commit_subject` docstring | A COMMENT (not code) asserts as verified that a subject here "names a plan path under `.aw/records/`", citing two measured peers whose subjects are `work: .aw/records/plans/pending/...`. This change makes that claim stale for future commits. Nothing breaks (the helper only truncates a subject to 120 chars for a refusal message) and `runner_shared.py` is deliberately out of scope, so it is REPORTED for a follow-up rather than edited here. | the docstring read in `runner_shared._commit_subject`; its only use is inside `format_conflict_resolver_facts`' refusal text |

## Proposed changes (ordered, validatable)

1. E-01 re-measures, re-deriving the history counts rather than inheriting them.
2. E-02 adds the pure derivation helper with its three-rung fallback, reading the id6 through the module's existing `_plan_id6` so the middle rung is actually reachable (F-5, F-6).
3. E-03 wires it into `run_commit`, preserving the `--no-plan` guard the `text` reference depends on.
4. E-04 adds scratch-repo behavioral tests, with case (2) built to discriminate the reader and cases (5) and (6) pinning the empty-`-m` and unsanitized-title behaviors.
5. E-05 confirms no subject reader regresses, driving the two prefix-keyed ones (F-3), and reports the now-stale `runner_shared` comment (F-9) rather than editing it.

## Deferred / out of scope (with reason)

- Requiring `-m` whenever a plan governs the commit (the backlog item's alternative).
  - Carrier-Declined: it costs a round trip on every call and discards information the tool already has; the derived default is greppable and honest about being a generic work commit, which is the item's preferred fix.

## Scope check

- Over-scope: none.
- Under-scope: two gaps closed at review. E-02's id6 reader could not reach its own middle fallback rung, and the test for that rung would have passed while proving the opposite (F-5, F-6), so the mechanism changed to the module's existing `_plan_id6` and E-04 case (2) is now built to discriminate. And no item verified that a subject CONSUMER could not be confused by the new shape beyond one grep for the literal string, now E-05, which drives the two prefix-keyed readers.
- `agent_workflows/git_commit_helper.py` is deliberately NOT changed; it receives the message string as before, and its no-trailer path is byte-for-byte, which is what makes an unsanitized title safe.
- `agent_workflows/runner_shared.py` is deliberately NOT declared even though `_commit_subject`'s docstring becomes stale (F-9): it is a comment in a refusal-rendering helper that only truncates, nothing reads the asserted shape, and editing a 30k-line shared module for a comment would widen a `low`-priority chore. E-05 reports it for a follow-up instead.
- Scope-Paths justification: `work_cmd.py` holds the producer, the existing `_plan_id6` reader, and the new helper; the new test file holds E-04.

## Required tests / validation

- `tests/test_commit_default_message.py` (new): seven behavioral cases on scratch repos, two failing before the fix. Case (2) must be built so that an implementation reading the id6 from `ipd_lint.parse(...).meta_fields` FAILS it (F-5); that discrimination is the point of the case.
- `python3 -m pytest -o addopts="" -q tests/test_work_gate_severity.py tests/test_scope_match.py` stays green. REQUIRED rather than incidental: E-04 drives `cli.main(["commit", ...])` through the same `work_cmd.run_commit` those suites exercise, so they are the regression surface for this edit even though neither file is modified.
- E-05's two reader drives (`artifact_audit._FINALIZE_SUBJECT_RE`, `worktree_lease.commit_subject_is_interrupted_snapshot`) against the new subject shape.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: no spec defines `aw commit`'s default message (grep of `.aw/records/specs/` for `work: ` finds nothing). No `.spec.md` is in `- Scope-Paths:`.
- No user-facing docs quote the old default.

## Open questions

### OQ-01: Should a long title be truncated to keep the subject short?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No, from repository evidence: the history's subject length is median 65 and p90 97 characters with a maximum of 473, so there is no enforced cap, and a truncated title is less greppable than a full one. Plan titles are the author's chosen summary and are the natural subject. CONFIRMED at review that nothing enforces a cap mechanically either: the pre-commit hooks are pinned to `default_stages: [pre-commit]`, so no `commit-msg` hook inspects the subject, and the only length handling anywhere is `runner_shared._commit_subject`'s display truncation to 120 chars, which affects a refusal message and not the commit.

### OQ-02: Should the derived title be escaped or sanitized before it becomes a commit subject?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO, and this is resolved from measured evidence rather than left implicit, because "sanitize untrusted-looking text" is exactly the well-meant change a later reader might add and it would corrupt legitimate titles. An H1 may contain backticks, double quotes and `$(...)` (driven at review), and all of it is safe: the message travels as an ARGUMENT to `git commit` via `git_commit_helper`, never through a shell, and `compose_message_with_trailers` returns it byte-for-byte when no trailers are supplied ("byte-for-byte identical: the existing-caller guarantee"). Plan titles are also authored in-repo by the same people who author the code, so they are not a trust boundary. E-04 case (6) pins the verbatim behavior so a future escaping attempt fails a test.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the producer line, the two counts, and the scratch commit's `git log -1 --format=%s` with the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the helper's diff and a `python3 -c` call printing its result for the fixture plan text (`work(wk0001): Demo work plan`), for a title-less variant (must be `work(wk0001): demo`, i.e. the MIDDLE rung, not `work: <plan_rel>`), and for an id-less non-clustered variant. ALSO paste `ipd_lint.parse(<the title-less text>).meta_fields.get("Id")` showing it is `None`, which is what proves the helper read the id6 through `_plan_id6` and not through `meta_fields` (F-5). Paste the diff showing `_plan_id6` is the reader used.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `run_commit` diff and the re-run of E-01's scratch commit showing `work(wk0001): Demo work plan`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_commit_default_message.py` passing PER NODE ID (use `-v`, so each of the seven cases is individually visible rather than a bare count); the same run with E-03 temporarily reverted showing cases (1) and (2) FAILING and (3), (4), (5) passing; `git diff --stat agent_workflows/work_cmd.py` after restoring, showing an EMPTY diff against the intended change; `python3 -m pytest -o addopts="" -q tests/test_work_gate_severity.py tests/test_scope_match.py` passing; and the bare `python3 -m pytest` summary line before and after with the after-minus-before failing node-ID set (must be empty). Paste case (6)'s asserted subject verbatim so the unsanitized-title behavior is visible in the record.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `rg -n 'format=%s' agent_workflows/` result, and the two driven reader checks against a `work(<id6>): <title>` subject: `artifact_audit._FINALIZE_SUBJECT_RE.match(...)` -> None (with the `lifecycle(...)` positive control matching) and `worktree_lease.commit_subject_is_interrupted_snapshot(...)` -> False. Then state whether `runner_shared._commit_subject`'s docstring claim is still accurate and, if not, name it as a reported follow-up rather than editing it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. When `aw commit <plan>` is run without `-m`, the commit subject becomes `work(<id6>): <plan title>` instead of `work: <full plan path>`, falling back to the filename slug and then to today's form. An explicit `-m` still wins, and `--no-plan` still requires `-m`.

TWO THINGS WORTH KNOWING, both added at review and neither a reason to withhold approval. FIRST, THE PLAN TITLE GOES INTO THE SUBJECT VERBATIM, including any backticks, quotes or `$(...)` it contains. That is safe (the message is a git ARGUMENT, never shell input, and the trailer composer is byte-for-byte with no trailers) and it is now pinned by a test so nobody later "sanitizes" it and mangles legitimate titles (OQ-02, F-8). It does mean a long or oddly punctuated title becomes a long or oddly punctuated subject; OQ-01 resolves deliberately not to truncate, and nothing in this repository enforces a subject cap. SECOND, ONE COMMENT ELSEWHERE GOES STALE: `runner_shared._commit_subject`'s docstring asserts that a subject here names a plan path. Nothing reads that shape and the helper only truncates for a refusal message, so E-05 REPORTS it for a follow-up instead of widening this `low`-priority chore into a 30k-line shared module (F-9).

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/work_cmd.py` (`run_commit`'s default and the new helper) and the new `tests/test_commit_default_message.py`. `agent_workflows/git_commit_helper.py` and `agent_workflows/runner_shared.py` are explicitly NOT in scope. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-04 must show cases (1) and (2) FAILING before the change, PER NODE ID (use `-v`). One claim is specifically easy to fake and must be DRIVEN: V-02's proof that the title-less plan yields the MIDDLE rung (`work(wk0001): demo`) while `ipd_lint.parse(...).meta_fields.get("Id")` on that same text is `None`. Asserting only the final subject would pass for an implementation that reached the wrong rung.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if the derived default cannot be computed without re-reading the plan file (i.e. `text` is not in scope where the message is built), stop rather than hoisting the computation out of the `or`, which raises `UnboundLocalError` on the `--no-plan` path. And if any subject READER turns out to match the new `work(<id6>):` shape (E-05), stop and report rather than adjusting that reader: a shape that can be mistaken for finalize evidence or for an interrupted snapshot is a correctness problem, not a formatting one.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push); pass `-m` explicitly for this plan's own commits, since the change under test is the default. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `qivywd` `done` with `--evidence` citing the executed plan.
