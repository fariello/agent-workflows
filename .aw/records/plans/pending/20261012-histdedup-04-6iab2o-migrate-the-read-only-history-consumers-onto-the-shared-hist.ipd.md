# IPD: Migrate the read-only history consumers onto the shared history-record reader

- Date: 2026-10-12
- Kind: child
- Concern: After sibling `kgv213` the dedup predicate and the backlog writer read history through `attention_contract.history_block`, but every other reader still bounds the block with `attention._history_section_lines` (heading-to-heading) and matches records against `line.strip()`, which counts INDENTED history-shaped lines that the canonical rule says are not records. The backlog item asks to "migrate the consumers to it" rather than leave two partitioning rules, and warns that `_history_section_lines` has many consumers, including `plan_readiness` verdict reading, so this migration is its own reviewable change. Measured in this lane at HEAD `5ebf5364d`: substituting the canonical rule for every consumer below and recomputing over all 2489 tracked artifacts with a history heading changed ZERO answers.
- Scope: IN: migrate the record-reading consumers to `attention_contract.history_block(text).records`: `attention` (`_prompts_record`, `_release_record`, `_spec_record`, `_plans_record`, `_research_record`, `_backlog_record`, each `A.last_history_at(_history_section_lines(text))`), `check_engine` (`_item_close_date`, `_item_graduated_date`, `_spec_implementing_date`), and `plan_readiness` (`extract_newest_history_entry`, `history_has_review_record`, `newest_verdict`); keep `attention._history_section_lines` as a function (tests and `tests/support.py` reference it) but document that record readers must use `history_block`; a corpus-equivalence test and fixtures fencing each consumer's indented-quotation behavior; one CHANGELOG entry. OUT: `status_set.same_status_message_is_duplicate` and `backlog` (done by `kgv213`); test modules that call `_history_section_lines` to inspect fixtures (they read their own outputs and are not consumers of the rule); any change to positional newest-first semantics; plan history writers.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/check_engine.py, agent_workflows/plan_readiness.py, tests/test_history_consumers_shared_reader.py, CHANGELOG.md
- Item-Dependencies: executed:kgv213
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: wkpcop
- Set: histdedup
- Order: 4
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6iab2o

## Workflow history

- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `wkpcop` to carry the consumer migration the item suggests, split from `kgv213` because these readers gate approval and attention surfaces. Zero-answer-change measured over 2489 artifacts at `5ebf5364d`. Blocking status: none.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every reader of history RECORDS use the one canonical bounding rule, so no surface (attention dates, close and graduation dates, review-verdict and approval gates) can count a quoted, indented history line as a record, while proving no current answer changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [ ] E-01 Before editing, record the base sha (`git rev-parse HEAD`) and capture a BASELINE answers file outside the tree's tracked paths (e.g. under `.aw/state/`, gitignored): for every tracked `.aw/records/**/*.md` containing `## Workflow history`, the values of `attention_contract.last_history_at([l.strip() for l in attention._history_section_lines(t)])`, `check_engine._item_close_date`, `check_engine._item_graduated_date`, `check_engine._spec_implementing_date`, `plan_readiness.extract_newest_history_entry`, `plan_readiness.newest_verdict`, `plan_readiness.history_has_review_record`. If `kgv213` has not executed (no `attention_contract.history_block`), mark this and every later item `blocked` and edit nothing.
  - Depends on: none
  - Expected outcome: a JSON baseline keyed by path, with its artifact count.
  - Execution state: pending

### Task group 2: migrate

- [ ] E-02 `agent_workflows/attention.py`: in the six `_*_record` builders replace `A.last_history_at(_history_section_lines(text))` with `A.last_history_at(A.history_block(text).records)`. Add to `_history_section_lines`'s docstring that it returns the RAW heading-bounded section and that record readers must use `attention_contract.history_block`.
  - Depends on: E-01
  - Expected outcome: no `_history_section_lines` call remains on a record-reading path in `attention.py`.
  - Execution state: pending

- [ ] E-03 `agent_workflows/check_engine.py`: in `_item_close_date`, `_item_graduated_date`, `_spec_implementing_date` read `_ac.history_block(text).records` (records are already rstripped, column-zero, so the `^- ` regexes match unchanged) and update each docstring's "Reuses `attention._history_section_lines`" sentence.
  - Depends on: E-01
  - Expected outcome: the three readers call the shared reader.
  - Execution state: pending

- [ ] E-04 `agent_workflows/plan_readiness.py`: in `extract_newest_history_entry`, `history_has_review_record`, `newest_verdict` iterate `history_block(text or "").records` instead of stripped `_history_section_lines` lines; drop the now-unused import only if nothing else in the module uses it; update the module docstring sentence that says the bounding is reused from `attention._history_section_lines`.
  - Depends on: E-01
  - Expected outcome: approval/verdict readers use the shared reader; their answers on the live corpus are unchanged (V-04 proves it).
  - Execution state: pending

### Task group 3: tests and changelog

- [ ] E-05 `tests/test_history_consumers_shared_reader.py` (new, behavioral, P16) plus `CHANGELOG.md`: tests calling the real consumers on fixtures: (a) a plan whose body below its history block (after a column-zero prose line) quotes an indented `- <date> /plan-review (...): APPROVE` record under a block whose real newest review is `REJECT`: `newest_verdict` returns the REJECT polarity and `history_has_review_record` reflects only real records; (b) a backlog item whose only history-shaped line is indented: `attention` reports `last_history_at` None for it via `attention.scan` on a temp repo holding that item, and `_item_close_date` returns None; (c) a wrapped multi-line plan record keeps every following record visible to `extract_newest_history_entry`. Add one CHANGELOG line (no em or en dashes) stating attention, check and readiness readers now share the history bounding rule.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: new module passes; CHANGELOG has one new entry.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `attention_contract.newest_history_record` is POSITIONAL by design (date-max was measured to flip `history_verdict_approves` for 20 plans); `history_block` keeps file order, so positional semantics are untouched.
- `plan_readiness` gates unattended approval (`is_plan_review_approved`, `approval_refusals`), so any reader change there must be proven answer-preserving on the live corpus, not argued.
- `tests/support.py` documents `attention._history_section_lines` by name; it stays.
- Suite runs bare as `python3 -m pytest`.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | Consumers on the loose rule: six `attention` record builders, three `check_engine` date readers, three `plan_readiness` readers (plus `status_set.same_status_message_is_duplicate`, which `kgv213` owns). | `rg -n "_history_section_lines" agent_workflows` at `5ebf5364d`. |
| F-02 | Migration changes no answer today. | Probe patching the canonical rule into `attention._history_section_lines` and `plan_readiness._history_section_lines`, recomputing the seven answers in E-01 over 2489 artifacts: `diffs {}`. |
| F-03 | The loose rule CAN mis-answer: a quoted indented review line in a body under the history heading region (no intervening `## `) is read as a record. Six tracked artifacts carry indented history-shaped lines in that region (`tk1gqo`, `r74211`, `4znh53`, reviews `7jqev2`, `1i300e`, plan `y6gsqw`); none happens to change an answer, which is luck, not a property. | Corpus probe at `5ebf5364d`. |

## Proposed changes (ordered, validatable)

1. E-01 baseline. 2. E-02..E-04 migrate. 3. E-05 fence and record.

## Deferred / out of scope (with reason)

- Deleting `_history_section_lines`: test code references it; deletion buys nothing once no production record reader uses it.
  - Carrier-Declined: test code references it and no production record reader will use it after this plan
- Test modules that read history from fixtures: they are inspecting outputs, not implementing the rule.
  - Carrier-Declined: they inspect their own fixture outputs and do not implement the rule

## Scope check

- Over-scope: none.
- Under-scope: none; every production consumer listed in F-01 that `kgv213` does not own is migrated.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_history_consumers_shared_reader.py tests/test_history_provenance.py tests/test_backlog_history_dedup_parity.py tests/test_history_block_bounding.py`, actual output pasted.
- Every existing test module covering `plan_readiness` and `attention` (find them with `rg -l "plan_readiness|attention" tests`), actual output pasted.
- The WHOLE BARE SUITE, `python3 -m pytest`, summary pasted, no new failure against the base.
- `aw attention --format json` before (base sha) and after, diffed: identical apart from timestamps.

## Spec / documentation sync

N/A. No spec states the bounding rule; the attention spec (`.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`) Section 8.5 requires `last_history_at` be "parsed from validated history, never mtime", which is preserved (still the newest record, now from the canonical reader).

## Open questions

### OQ-01: Is the blast radius acceptable?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The item flagged this risk without measuring it. F-02 measures it as zero answer changes across the whole tracked corpus, and V-04 re-proves that at execution time against a fresh baseline, so the change is gated on evidence rather than argument.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the base sha and the baseline's artifact count and path.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE `git diff agent_workflows/attention.py` and `rg -n "_history_section_lines" agent_workflows/attention.py` showing only the definition remains. PASTE the before/after `aw attention --format json` diff summary.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE `git diff agent_workflows/check_engine.py` and `aw check` output on the live repository with no new finding versus the base.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE `git diff agent_workflows/plan_readiness.py`. PASTE the output of recomputing the E-01 answers after E-02..E-04 and diffing against the baseline: the required result is zero differing answers; any difference is a FAIL unless it is one of F-03's artifacts and the new answer is shown to be the correct one.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the new module's pytest output passing and `git diff CHANGELOG.md`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution and depends on `kgv213` being executed. The executor is bound by the AGENTS.md execution contract: commit only the declared Scope-Paths through `aw commit <plan> -- <paths>`, never push, paste actual runner output. Before the terminal transition `aw ipd lint --phase pre-transition` must conform. Under `aw oc run` / `aw agy run` the runner finalizes; manually, run `aw ipd finalize 6iab2o ... --apply`. Do not set backlog `wkpcop` to `done`.
