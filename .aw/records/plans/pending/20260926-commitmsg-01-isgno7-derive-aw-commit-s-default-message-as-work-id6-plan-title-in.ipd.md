# IPD: Derive aw commit's default message as work(id6): plan title instead of the full plan path

- Date: 2026-09-26
- Kind: child
- Concern: `aw commit <plan> -- <paths>` WITHOUT `-m` writes the one-line message `work: <full repo-relative plan path>`, from `work_cmd.run_commit`: `message = getattr(args, "message", None) or f"work: {plan_rel}"`. Re-measured at HEAD `61ef21d8`: 41 of 2396 commit subjects since 2026-09-01 start with `work: `, while 702 use the `type(<id6>):` shape. The default spends the whole subject on a roughly 110-character path already recoverable from the diff, carries no id6 in a greppable `type(scope)` position, and is the one shape this repository's history does not otherwise use, at exactly the moment an agent is most likely to accept a default (backlog `qivywd` records an agent having to amend after taking it).
- Scope: IN: (a) a small pure helper in `work_cmd` that derives the default subject from the plan text and filename: `work(<id6>): <H1 title with a leading "IPD: " removed>`, falling back to `work(<id6>): <filename slug>` when the title is missing or empty, and to the current `work: <plan_rel>` when no id6 can be found at all; the id6 is read from the plan's `- Id:` field, falling back to the clustered filename's id6 (`artifact_naming.parse_clustered_prefix`); (b) `run_commit` uses that helper only when `-m` is absent; (c) behavioral tests committing in a scratch git repo and reading `git log -1 --format=%s`. OUT: changing the `--no-plan` rule (it still requires `-m`); changing an explicit `-m`; truncating or reformatting long titles; any lifecycle commit subject (`artifact_core.lifecycle_commit_prefix`), which is a different producer with a security-relevant fixed form.
- Scope-Paths: agent_workflows/work_cmd.py, tests/test_commit_default_message.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: qivywd
- Set: commitmsg
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: isgno7

## Workflow history

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
  - Execution state: pending

### Task group 2: derive the default

- [ ] E-02 ADD `work_cmd._default_commit_message(plan_text: str, plan_rel: str) -> str`, pure (no I/O). Read the id6 from `ipd_lint.parse(plan_text).meta_fields.get("Id")` if it satisfies `artifact_core.is_valid_id6`, else from `artifact_naming.parse_clustered_prefix(Path(plan_rel).name).group("id6")`. Read the title from `ipd_lint.parse(plan_text).title`, strip whitespace and one leading `IPD: ` prefix. Return `f"work({id6}): {title}"` when both exist; `f"work({id6}): {slug}"` when only the id6 exists, where `slug` is the clustered filename's slug group (`artifact_naming.parse_clustered`), or the filename stem when that does not match; and `f"work: {plan_rel}"` when no id6 is found. Never raise: any parse failure falls through to the next rung. Import `ipd_lint` lazily, as `_plan_scope_paths` already does. Docstring cites `qivywd`.
  - Depends on: E-01
  - Expected outcome: for the fixture plan the helper returns `work(wk0001): Demo work plan`.
  - Execution state: pending

- [ ] E-03 USE THE HELPER in `work_cmd.run_commit`: replace the `or f"work: {plan_rel}"` fallback with `or _default_commit_message(text, plan_rel)`, where `text` is the plan text `run_commit` already read for `_plan_scope_paths` (keep it in scope rather than re-reading the file). An explicit `-m` still takes precedence, and the `--no-plan` path is unchanged (it returns 2 before this line when `-m` is absent).
  - Depends on: E-02
  - Expected outcome: E-01's scratch commit now yields subject `work(wk0001): Demo work plan`.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-04 ADD `tests/test_commit_default_message.py`, behavioral only (maintainer's 2026-09-26 ruling: no source-text pins). Build scratch repos as `tests/test_work_gate_severity.WorkGateSeverityTest.setUp` does (including `tests.support.declare_execution_role(self)`), drive `cli.main(["commit", <selector>, "--dir", <repo>, ...])`, and read `git log -1 --format=%s`. Cases: (1) no `-m`, plan with `- Id:` and an `# IPD: <title>` H1 -> `work(wk0001): <title>`; (2) no `-m`, plan whose H1 is empty or absent -> `work(<id6>): <filename slug>`; (3) explicit `-m "custom subject"` -> exactly `custom subject`; (4) `--no-plan` without `-m` -> exit 2, message names `requires -m/--message`, and no new commit is created (HEAD unchanged); (5) unit-level: `_default_commit_message` on text with no `- Id:` and a non-clustered filename returns `work: <plan_rel>` unchanged.
  - Depends on: E-03
  - Expected outcome: all pass; cases (1) and (2) FAIL before E-03; cases (3), (4), (5) pass before and after (controls; (5) is a unit case that exists only after E-02, so it is shown passing after).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The repository's commit history is Conventional-Commits-shaped with an id6 scope (`plan(<id6>): ...`, `lifecycle(<id6>): ...`, `feat(runner): ...`); 702 of 2396 subjects since 2026-09-01 match `^[a-z]*(<6 chars>):`.
- `lifecycle(<id6>)` subjects are produced ONLY by `artifact_core.lifecycle_commit_prefix` / `finalize_commit_subject`, and readers match `lifecycle(<id6>): finalize` narrowly ("a looser match would let an ordinary work commit that merely names the plan pass as finalize evidence"). A `work(<id6>):` subject cannot collide with that keyword.
- No code in `agent_workflows/` parses `work: ` subjects (grep for `"work: "` and `work(` found only the producer line), so changing the default breaks no reader.
- `work_cmd._plan_scope_paths` already parses the plan with `ipd_lint.parse`, imported lazily; `ipd_lint.parse(text).title` holds the H1 (`IPD: <title>`) and `.meta_fields["Id"]` the id6 (measured on a real plan).
- The pre-commit hooks are pinned to `default_stages: [pre-commit]` (`.pre-commit-config.yaml`), so no commit-msg hook constrains the subject.
- Tests run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `work_cmd.run_commit` | The default subject is `work: <plan_rel>`. | `message = getattr(args, "message", None) or f"work: {plan_rel}"` |
| F-2 | INFO | git history | 41 commits since 2026-09-01 carry that shape; 702 use `type(<id6>):`. | `git log --since=2026-09-01 --format=%s \| grep -c '^work: '` -> 41 of 2396 |
| F-3 | INFO | readers | Nothing parses `work: ` subjects. | grep of `agent_workflows/` |
| F-4 | INFO | `--no-plan` | Already refuses without `-m` before the message line. | `"error: aw commit --no-plan requires -m/--message (there is no plan to derive the ..."` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures.
2. E-02 adds the pure derivation helper with its three-rung fallback.
3. E-03 wires it into `run_commit`.
4. E-04 adds scratch-repo behavioral tests.

## Deferred / out of scope (with reason)

- Requiring `-m` whenever a plan governs the commit (the backlog item's alternative).
  - Carrier-Declined: it costs a round trip on every call and discards information the tool already has; the derived default is greppable and honest about being a generic work commit, which is the item's preferred fix.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/git_commit_helper.py` is deliberately NOT changed; it receives the message string as before.
- Scope-Paths justification: `work_cmd.py` holds the producer; the new test file holds E-04.

## Required tests / validation

- `tests/test_commit_default_message.py` (new): five behavioral cases on scratch repos, two failing before the fix.
- `python3 -m pytest -o addopts="" -q tests/test_work_gate_severity.py tests/test_scope_match.py` stays green.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: no spec defines `aw commit`'s default message (grep of `.aw/records/specs/` for `work: ` finds nothing). No `.spec.md` is in `- Scope-Paths:`.
- No user-facing docs quote the old default.

## Open questions

### OQ-01: Should a long title be truncated to keep the subject short?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No, from repository evidence: the history's subject length is median 65 and p90 97 characters with a maximum of 473, so there is no enforced cap, and a truncated title is less greppable than a full one. Plan titles are the author's chosen summary and are the natural subject.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the producer line, the two counts, and the scratch commit's `git log -1 --format=%s` with the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the helper's diff and a `python3 -c` call printing its result for the fixture plan text (`work(wk0001): Demo work plan`), for a title-less variant, and for an id-less non-clustered variant.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `run_commit` diff and the re-run of E-01's scratch commit showing `work(wk0001): Demo work plan`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_commit_default_message.py` passing with its count; the same run with E-03 temporarily reverted showing cases (1) and (2) FAILING and (3), (4) passing; `python3 -m pytest -o addopts="" -q tests/test_work_gate_severity.py tests/test_scope_match.py` passing; and the bare `python3 -m pytest` summary line before and after with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. When `aw commit <plan>` is run without `-m`, the commit subject becomes `work(<id6>): <plan title>` instead of `work: <full plan path>`, falling back to the filename slug and then to today's form. An explicit `-m` still wins, and `--no-plan` still requires `-m`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/work_cmd.py` (`run_commit`'s default and the new helper) and the new `tests/test_commit_default_message.py`. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-04 must show cases (1) and (2) FAILING before the change.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push); pass `-m` explicitly for this plan's own commits, since the change under test is the default. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `qivywd` `done` with `--evidence` citing the executed plan.
