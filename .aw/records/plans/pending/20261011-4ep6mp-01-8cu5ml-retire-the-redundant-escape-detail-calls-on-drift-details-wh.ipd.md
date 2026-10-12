# IPD: Retire the redundant escape_detail calls on drift details while keeping it where it still guards a line

- Date: 2026-10-11
- Kind: child
- Concern: `attention_contract.escape_detail` was written to keep a drift `detail` on one line of the retired `location<TAB>rule<TAB>detail` TSV agent record (`artifact_core.render_agent_drift`, deleted by executed plan `n9ua3b`). That wire form is gone: `--agent` now emits `aw.agent/v1`, where `detail` is JSON-encoded. Yet 26 call sites still route values through it, and measurement shows the escaping is not merely redundant on most of them: 8 sites wrap a `{value!r}` that `repr` has ALREADY escaped, so `escape_detail` doubles every backslash a second time and a reader sees `'we\\\\ird'` for a status that was authored `we\ird` (measured, F-03). Another 9 sites pass a constant or a tool-built string that can contain no tab, newline, carriage return or backslash, so the call is a provable identity (F-04). The remaining 9 sites still do real work on a HUMAN single-line surface (F-05) and must stay.
- Scope: IN: remove `A.escape_detail` from the 17 drift-detail call sites F-03 and F-04 classify (8 repr-wrapped, 9 provable identity) in `attention.py`, `specs.py`, `research_index.py` and `releases.py`; rewrite the `_AGENT_ESCAPES` comment and the `escape_detail` docstring in `attention_contract.py` so they state the helper's REMAINING purpose (keep an untrusted value on one line of a human-rendered surface) instead of a deleted wire form; add a behavioral test module; amend spec Section 8.8's stale `--agent` TSV escaping clause; add a CHANGELOG line. OUT: the 9 call sites F-05 keeps (`attention.scan` duplicate-id, `attention.stranded_lane_drift`, the four board gate-ref renders, the `cli.py` gate-ref render, and the two `specs.run_migrate` history-message writes); deleting or renaming `escape_detail` or `_AGENT_ESCAPES`; `tests/test_attention_contract.py::test_detail_escaping_keeps_one_line`; any change to `_CONTROL_CHAR_RE`, `is_safe_descriptive`, `neutralize_control_characters` or `escape_markdown_inline`.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/specs.py, agent_workflows/research_index.py, agent_workflows/releases.py, agent_workflows/attention_contract.py, tests/test_drift_detail_escaping.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 4ep6mp
- Set: 4ep6mp
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: 8cu5ml

## Workflow history

- 2026-10-12 to-review (opencode): Authored from backlog `4ep6mp`. Classified all 26 live call sites by measurement into remove-repr-wrapped (8), remove-provable-identity (9) and keep-human-single-line (9); measured that the repr-wrapped sites double-escape backslashes today.
- 2026-10-12 draft (opencode): created.

## Goal

Stop escaping drift details for a wire form that no longer exists. Remove `escape_detail` from every call site where it is either a provable identity or actively double-escapes a `repr`, keep it at the sites where it still keeps an untrusted value on one human-rendered line, and make the helper's documentation say which of those it is for.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and behavioral tests

- [ ] E-01 Record the baseline on the unmodified tree: the full call-site census (`rg -n "escape_detail\(" agent_workflows`), and the failing node-id set of a bare `python3 -m pytest` run, so later failures can be compared by node id rather than by count.
  - Depends on: none
  - Expected outcome: a census of 26 call sites across `attention.py` (12), `specs.py` (8), `research_index.py` (3), `releases.py` (2) and `cli.py` (1), matching F-02, plus a saved list of baseline failing node ids (possibly empty).
  - Execution state: pending

- [ ] E-02 Create `tests/test_drift_detail_escaping.py` with behavioral tests that drive the real producers on temp fixtures and assert on the returned `Drift.detail`:
  (a) for each REPR-WRAPPED site (F-03), a hostile native value containing a backslash and a tab yields a detail EQUAL to the producer's message formatted with a single `repr` (for example `"backlog status " + repr("we\\ird")`), and containing no raw tab, newline or carriage return. Drive `attention.scan` on a temp repo for the backlog, plans, research, release and prompts producers (`_backlog_record`, `_plans_record`, `_research_record`, `_release_record`, `_prompts_record`), and `specs.validate_spec` directly for the spec status, unknown `Gate-Kind` and invalid `Gate-Ref` producers. The prompts producer's value is a bucket directory name, so its fixture must place a prompt under an unrecognized bucket directory; if a bucket name containing a backslash cannot reach the drift branch, use a plain unrecognized bucket and assert exact equality with the single-repr form only.
  (b) for the PROVABLE-IDENTITY sites (F-04), the detail equals the literal message exactly (`"Scope is over-length or has control chars/newlines"`, `"Summary is over-length or has control chars/newlines"`, `"metadata bullet - <Key>: appears <N> times"`, the three research `"... is over-length or has control chars/newlines"` messages, the two releases messages, and `"dir <disp> vs status <status>"`).
  (c) one end-to-end case: `python -m agent_workflows.cli attention --check --json --dir <temp repo>` run as a subprocess on the hostile backlog fixture, parsing the JSON and asserting the drift entry's `detail` decodes to the single-repr form. Use `--json`, not `--agent`: measured at authoring, the `aw.agent/v1` record's diagnostics carry `location` and `rule` only, with no `detail` key, so `--agent` cannot observe this change. If the `--json` payload nests the drift list under a different key than `data.drift`, locate it from the payload and say where.
  Run the new module on the UNMODIFIED tree first: (a) must FAIL for the repr-wrapped sites (double backslash), and (b) must PASS (identity), which is what proves the F-04 sites are no-ops.
  - Depends on: E-01
  - Expected outcome: the new module exists; on the unmodified tree the (a) cases fail with a doubled-backslash mismatch and the (b) cases pass.
  - Execution state: pending

### Task group 2: retire the redundant calls

- [ ] E-03 Remove the `A.escape_detail(...)` wrapper, keeping the inner f-string byte-for-byte, at the 8 REPR-WRAPPED sites F-03 lists: `attention._prompts_record` (`f"prompt disposition {disp!r}"`), `attention._release_record` (`f"release status {status!r}"`), `attention._plans_record` (`f"plan status {status!r}"`), `attention._research_record` (`f"research status {raw_status_str!r}"`), `attention._backlog_record` (`f"backlog status {status!r}"`), and in `specs.validate_spec` the three messages `f"status {status!r} not in the spec enum"`, `f"unknown Gate-Kind {kind!r}"` and `f"invalid Gate-Ref for {kind}: {ref!r}"`.
  WHY REMOVING IS SAFE AND NOT A LOOSENING: `repr` of a `str` never contains a raw tab, newline or carriage return (it renders them as `\t`, `\n`, `\r`) and already escapes backslash, so the detail stays single-line on every surface without the wrapper. The only behavior the wrapper adds is the double escape F-03 measured.
  - Depends on: E-02
  - Expected outcome: the 8 sites no longer call `escape_detail`; the E-02 (a) cases pass.
  - Execution state: pending

- [ ] E-04 Remove the `A.escape_detail(...)` wrapper at the 9 PROVABLE-IDENTITY sites F-04 lists, keeping the inner string byte-for-byte: `specs.validate_spec` (`f"metadata bullet - {k}: appears {count} times"`, the `Scope` and `Summary` over-length messages), `research_index.check_drift` (the `Summary`, `Topic` and `Consumed-by` over-length messages), `releases.validate_release` (the `Summary bullet` and `Summary prose` messages), and `attention._plans_record` (`f"dir {disp} vs status {status}"`).
  - Depends on: E-02
  - Expected outcome: the 9 sites no longer call `escape_detail`; the E-02 (b) cases still pass, unchanged.
  - Execution state: pending

- [ ] E-05 In `agent_workflows/attention_contract.py`, rewrite the comment above `_AGENT_ESCAPES` and the `escape_detail` docstring so they state the helper's REMAINING purpose: keeping an untrusted, non-`repr`'d value on one line of a HUMAN-rendered surface (the `aw attention --check` `location: rule: detail` lines, the board's gate-ref suffix, and a spec history line), and state that the `aw.agent/v1` and `--json` surfaces JSON-encode `detail` and need no escaping, and that a value already passed through `repr` must NOT be passed through it again. Do NOT change `_AGENT_ESCAPES`, the function body, or its name. Do NOT touch the 9 call sites F-05 keeps.
  - Depends on: E-03, E-04
  - Expected outcome: the census reports exactly the 9 F-05 sites; the function body and `_AGENT_ESCAPES` are byte-identical; the docstring no longer claims a TSV agent record.
  - Execution state: pending

### Task group 3: record the contract and the change

- [ ] E-06 Amend spec `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` Section 8.8's "Deterministic escaping per surface" bullet with a parenthetical `(AMENDED by plan 8cu5ml: ...)` recording that the `--agent` TSV form no longer exists, that `--agent` emits `aw.agent/v1` whose JSON encoding keeps `detail` single-line, and that tab/newline/backslash escaping now applies only to non-`repr`'d untrusted values on human single-line surfaces. Append a history line with `aw specs note <spec> --message ...` (do not hand-edit the history section). Add one `- Fixed:` line to `CHANGELOG.md` under the pending release, in plain user-facing prose with no em or en dashes, saying that drift messages quoting an authored status or gate value no longer double their backslashes.
  - Depends on: E-05
  - Expected outcome: the spec bullet carries the amendment and a new history line; `aw specs check` stays clean for that spec; CHANGELOG has the new line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `attention_contract.escape_detail` replaces, in order, `\` -> `\\`, tab -> `\t`, newline -> `\n`, carriage return -> `\r` (`_AGENT_ESCAPES`). It does NOT touch C0/C1 or bidi controls; `neutralize_control_characters` and `escape_markdown_inline` own those on the board (executed plan `qpw45x`).
- `artifact_core.render_agent_drift` (the TSV emitter) was deleted by executed plan `n9ua3b`, whose E-05 explicitly left `escape_detail` and its callers untouched and filed this backlog item (`4ep6mp`) for the redundancy. `n9ua3b`'s review counted 20 sites; at this HEAD the census is 26 because `releases.py` and `research_index.py` gained calls since (executed plans `ynhst5` and `xnogdl`).
- Human surfaces print `detail` raw on one line: `attention.run` (`--check` human branch, `f"{d.location}: {d.rule}: {d.detail}\n"`), `attention` board drift footer (`f"  ! {d.location}: {d.rule}: {d.detail}"`), `research_index.run_index`, `plans_index`, `prompts_index`. So a value that CAN carry a raw newline still needs a one-line guard there; that is why F-05's sites stay.
- Drift details must never echo an untrusted value where avoidable (`ynhst5`, `xnogdl` conventions); this plan only removes a wrapper and changes no message text, so it neither adds nor removes an echo.
- Tests must exercise real producers and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): the new module must not grep source for `escape_detail`. The census in E-01/E-05 is execution evidence, not a test.
- Run the suite bare as `python3 -m pytest` (repo-local development contract).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The wire form `escape_detail` was written for is gone. `n9ua3b` deleted `render_agent_drift`; the helper's docstring still says it escapes "for the single-line `location<TAB>rule<TAB>detail` agent record", and the comment above `_AGENT_ESCAPES` already calls the rationale historical. | `attention_contract.escape_detail` docstring and the `_AGENT_ESCAPES` comment read at HEAD `2965add5f`; `n9ua3b` E-05 and its review PR-004/F-12. |
| F-02 | Census: 26 live call sites. `attention.py` 12, `specs.py` 8, `research_index.py` 3, `releases.py` 2, `cli.py` 1, plus the definition and `tests/test_attention_contract.py::test_detail_escaping_keeps_one_line`. | `rg -c "escape_detail\(" agent_workflows/*.py` at HEAD `2965add5f` reports per-file counts of releases 2, attention_contract 1 (the definition), attention 12, cli 1, research_index 3, specs 8. |
| F-03 | **8 sites DOUBLE-ESCAPE a `repr`.** Each passes `f"... {value!r}"`; `repr` already escapes backslash and renders tab/newline as `\t`/`\n`, so `escape_detail` turns every one of those backslashes into two. Sites: `attention._prompts_record`, `_release_record`, `_plans_record` (`plan status`), `_research_record`, `_backlog_record`; `specs.validate_spec` status, unknown `Gate-Kind`, invalid `Gate-Ref`. | Measured: a backlog item with `- Status: we\ird` driven through `attention.scan` yields detail `"backlog status 'we\\\\\\\\ird'"` (Python repr of the detail), where a single `repr` gives `'we\\\\ird'`. `specs.validate_spec` on `- Status: C:\x` yields `"status 'C:\\\\\\\\x' not in the spec enum"`, and on `- Gate-Ref: a\b<TAB>c` yields `"invalid Gate-Ref for external: 'a\\\\\\\\b\\\\tc'"`. |
| F-04 | **9 sites are a provable identity.** Their argument is a constant, or is built only from values that cannot contain `\`, tab, newline or CR: `specs.validate_spec` duplicate-bullet (`k` matches `_TOP_KEY_RE`'s `[A-Za-z0-9_-]+`, `count` is an int) and the `Scope`/`Summary` constants; `research_index.check_drift`'s three constants; `releases.validate_release`'s two constants; `attention._plans_record` `dir {disp} vs status {status}`, which fires only when `disp in plans_mod.DIR_TERMINAL` and `status in plans_mod.TERMINAL`, both closed sets of plain words. | Read: `specs._TOP_KEY_RE = re.compile(r"^- ([A-Za-z0-9_-]+):(?:\s*(.*))?$")`; `plans.TERMINAL = ("executed", "superseded", "not-executed")`; `plans.DIR_TERMINAL` keys the same three words. E-02 (b) proves the identity on the unmodified tree by passing before any edit. |
| F-05 | **9 sites still do real work and stay.** `attention.scan` duplicate-id (`id {rec.id} also on {seen_ids[rec.id]}`, not `repr`'d; `rec.id` comes from a fallback `- Id:` parse that keeps an internal tab, measured `att._plans_id('- Id: ab\tcd\n') == 'ab\tcd'`, and the location is a repo path); `attention.stranded_lane_drift` (composes free-text `why` from a run record, and `tests/test_attention_lane_detail_bound.py` asserts that detail has no newline); the four board gate-ref renders in `_shared_gate_ref`, `_render_item_row` (both branches) and `_render_table_row`, plus the `cli.py` gate-ref render (`g_ref = att.A.escape_detail(g.get("ref", ""))`), which print an authored `Gate-Ref` on a human board line and are not drift details at all; and `specs.run_migrate`'s two history-message writes, which put authored prose into a durable Markdown history line. | Each site read at HEAD. The gate-ref sites print into the human board, not `aw.agent/v1`, so `n9ua3b`'s "JSON-encoded, therefore redundant" argument does not apply to them. `run_migrate` is a WRITE path whose output is persisted; changing it would change what future history lines contain. |
| F-06 | No existing test pins the double-escaped form, so removing the wrapper at F-03's sites changes no expected value in the suite. | `rg` over `tests/` for the F-03 message prefixes (`backlog status`, `plan status`, `not in the spec enum`, `invalid Gate-Ref for`, `research status`, `release status`, `prompt disposition`) returns no assertion on a detail value. The only escaping test is `test_detail_escaping_keeps_one_line`, which calls the helper directly and stays. |
| F-07 | The governing spec still describes the deleted surface: Section 8.8 says "The `--agent` `location<TAB>rule<TAB>detail` form escapes tab, newline, and backslash per Section 8.3." A 2026-10-01 spec note records the TSV removal but the bullet itself was never amended. | `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`, Section 8.8 bullet "Deterministic escaping per surface" and the `## Workflow history` line "TSV render_agent_drift removed". |

## Proposed changes (ordered, validatable)

1. Baseline census and failing-node set (E-01).
2. Behavioral tests that fail on the double escape and pass on the identity sites before any edit (E-02).
3. Drop the wrapper at the 8 repr-wrapped sites (E-03) and the 9 identity sites (E-04).
4. Re-document `escape_detail` for its remaining purpose, leaving its body and the 9 kept sites alone (E-05).
5. Amend spec Section 8.8 and add a CHANGELOG line (E-06).

## Deferred / out of scope (with reason)

- **The 9 sites F-05 keeps.** They guard a raw newline or tab on a human single-line surface or a persisted history line, which is a live purpose, not a redundancy. Removing them would let an authored tab or newline split a `--check` line or a board row.
  - Carrier-Declined: nothing is owed; this is a DECISION this plan makes on measured evidence (F-05), not postponed work. The helper stays, with documentation that names exactly these surfaces.
- **Replacing the kept guard with `repr` or with `neutralize_control_characters`.** Either would change rendered text for every gate ref and lane row, a visible behavior change with no measured defect behind it.
  - Carrier-Declined: nothing is owed; no defect is measured on those surfaces, so a carrier would schedule a change whose validation could not distinguish a fix from churn.
- **Renaming `escape_detail` or `_AGENT_ESCAPES`.** The `_AGENT_` prefix is now a misnomer, but renaming touches the 9 kept sites and the shipped test for a cosmetic gain; E-05's comment states the name is historical.
  - Carrier-Declined: nothing is owed; a cosmetic rename is not work a later reader needs, and the corrected comment removes the only harm (a misleading rationale).

## Scope check

- Over-scope: none. Every declared path is written: `attention.py` and `specs.py` by E-03/E-04, `research_index.py` and `releases.py` by E-04, `attention_contract.py` by E-05, the new test module by E-02, the spec and `CHANGELOG.md` by E-06.
- Under-scope: all 26 call sites are classified (8 + 9 removed, 9 kept with reason). Not covered, by decision recorded above: the kept sites, a different guard for them, and a rename.

## Required tests / validation

- `tests/test_drift_detail_escaping.py` (E-02): the repr-wrapped cases FAIL on the unmodified tree and PASS after E-03; the identity cases PASS both before and after.
- `tests/test_attention_contract.py`, `tests/test_attention.py`, `tests/test_attention_lane_detail_bound.py`, `tests/test_specs_verbs.py`, `tests/test_specs_metadata_duplicate_bullet.py` and `tests/test_attention_degraded_item.py` stay green (they drive the touched producers and the kept helper).
- The full suite run bare as `python3 -m pytest`, compared by failing node-id set against the E-01 baseline.
- `aw specs check` on the amended spec, `aw check`, and `aw ipd lint` on this plan.

## Spec / documentation sync

E-06 amends `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` Section 8.8 and adds a `CHANGELOG.md` line. The spec path is declared in `- Scope-Paths:` so both runners announce the edit before the run and reconcile it at run end. WHY the amendment is required: the bullet still mandates escaping for a `--agent` TSV form that no longer exists (F-07), so after this plan narrows where escaping applies, an unamended spec would describe a contract the code deliberately does not implement and every later reviewer would read it as a defect.

## Open questions

### OQ-01: Should the repr-wrapped sites keep `escape_detail` and drop `repr` instead?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: keep `repr`, drop `escape_detail`. `repr` quotes the value (so a reader can see leading or trailing whitespace and an empty string), already renders tab, newline and CR as visible escapes, and is what every one of these messages was written with. Dropping `repr` instead would remove the quotes from 8 user-visible messages; dropping `escape_detail` changes only the doubled backslash F-03 measured.

### OQ-02: Is the doubled backslash a `bug` that should gate the release?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: no; the item stays `chore` as filed. The defect only appears when an authored status or gate value already contains a backslash or tab, which is itself invalid input reported by the same message, and the message remains readable and one line. That is not a user-perceptible impact under the AGENTS.md test, and this plan does not alter the backlog item's classification.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `rg -n "escape_detail\(" agent_workflows` census output showing 26 call sites plus the definition, and paste the bare `python3 -m pytest` summary line from the unmodified tree together with the list of failing node ids (or state it is empty).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `python3 -m pytest tests/test_drift_detail_escaping.py -o addopts=""` output from the UNMODIFIED tree showing every repr-wrapped case failing with a doubled-backslash assertion diff and every identity case passing, then paste the same command's output after E-03/E-04 showing all cases passing. Paste the test source for one repr-wrapped case and the end-to-end subprocess case, showing they drive `attention.scan`, `specs.validate_spec` and the `aw attention` CLI and assert on returned details, with no reading of production source.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff agent_workflows/attention.py agent_workflows/specs.py` hunks for the 8 repr-wrapped sites, showing only the `A.escape_detail(` wrapper and its closing parenthesis removed and each inner f-string unchanged. Paste a `python3 -c` session re-driving the F-03 fixture (`- Status: we\ird` through `attention.scan`) showing the detail now equals `"backlog status " + repr("we\\ird")`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff` hunks for the 9 identity sites in `specs.py`, `research_index.py`, `releases.py` and `attention.py`, showing only the wrapper removed and each inner string unchanged, and paste the passing identity cases from the post-change V-02 run.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the post-change `rg -n "escape_detail\(" agent_workflows` census showing exactly the 9 F-05 sites plus the definition. Paste `git diff agent_workflows/attention_contract.py` showing only the comment and docstring changed (the `_AGENT_ESCAPES` tuple and the function body byte-identical). Paste `git diff` proving none of the 9 kept call-site lines changed, and paste `tests/test_attention_contract.py::test_detail_escaping_keeps_one_line` and `tests/test_attention_lane_detail_bound.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the amended Section 8.8 bullet text, the new spec history line written by `aw specs note`, the `aw specs check` output for that spec showing no finding, and the new CHANGELOG line. Then paste the bare `python3 -m pytest` summary line and state the failing node-id set equals the V-01 baseline, plus `aw check` and `aw ipd lint` output for this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive change: a single helper's call-site population, classified once and pruned once, with the test that proves the pruning and the documentation that records what remains. Splitting the 8 repr-wrapped sites from the 9 identity sites would leave the helper's docstring describing a half-migrated population.

EXECUTION CONTRACT. Execution requires explicit human approval first (`- Status: approved`); OQ-01 and OQ-02 are resolved and non-blocking. Run `aw ipd begin` first when executing by hand (a runner performs begin for a managed lane). Commit through `aw commit 8cu5ml -- <paths>` with only this plan's declared paths, never `git add -A` and never a push. SCOPE FENCE: `- Scope-Paths:` is a declaration; an out-of-scope edit that proves necessary is made and then JUSTIFIED at finalize (`--scope-reason`), and a declared path left unmodified needs a `--scope-ack`.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries concrete pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the RUNNER owns the terminal transition; when executing by hand, run `aw ipd finalize` (never a hand-rolled `git mv`). The runner sets backlog `4ep6mp` to `graduated`; do not set it `done` by hand.
