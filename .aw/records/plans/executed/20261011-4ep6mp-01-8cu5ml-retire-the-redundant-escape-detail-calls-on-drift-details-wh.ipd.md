# IPD: Retire the redundant escape_detail calls on drift details while keeping it where it still guards a line

- Date: 2026-10-11
- Kind: child
- Concern: `attention_contract.escape_detail` was written to keep a drift `detail` on one line of the retired `location<TAB>rule<TAB>detail` TSV agent record (`artifact_core.render_agent_drift`, deleted by executed plan `n9ua3b`). That wire form is gone: `--agent` now emits `aw.agent/v1`, where `detail` is JSON-encoded. Yet 26 call sites still route values through it, and measurement shows the escaping is not merely redundant on most of them: 8 sites wrap a `{value!r}` that `repr` has ALREADY escaped, so `escape_detail` doubles every backslash a second time and a reader sees `'we\\\\ird'` for a status that was authored `we\ird` (measured, F-03). Another 9 sites pass a constant or a tool-built string that can contain no tab, newline, carriage return or backslash, so the call is a provable identity (F-04). The remaining 9 sites still do real work on a HUMAN single-line surface (F-05) and must stay.
- Scope: IN: remove `A.escape_detail` from the 17 drift-detail call sites F-03 and F-04 classify (8 repr-wrapped, 9 provable identity) in `attention.py`, `specs.py`, `research_index.py` and `releases.py`; rewrite the `_AGENT_ESCAPES` comment and the `escape_detail` docstring in `attention_contract.py` so they state the helper's REMAINING purpose (keep an untrusted value on one line of a human-rendered surface) instead of a deleted wire form; add a behavioral test module; amend spec Section 8.8's stale `--agent` TSV escaping clause; add a CHANGELOG line. OUT: the 9 call sites F-05 keeps (`attention.scan` duplicate-id, `attention.stranded_lane_drift`, the four board gate-ref renders, the `cli.py` gate-ref render, and the two `specs.run_migrate` history-message writes); deleting or renaming `escape_detail` or `_AGENT_ESCAPES`; `tests/test_attention_contract.py::test_detail_escaping_keeps_one_line`; any change to `_CONTROL_CHAR_RE`, `is_safe_descriptive`, `neutralize_control_characters` or `escape_markdown_inline`.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/specs.py, agent_workflows/research_index.py, agent_workflows/releases.py, agent_workflows/attention_contract.py, tests/test_drift_detail_escaping.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 4ep6mp
- Set: 4ep6mp
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: 8cu5ml

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 8cu5ml verified (set 4ep6mp, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004

- 2026-10-12 to-review (opencode): Authored from backlog `4ep6mp`. Classified all 26 live call sites by measurement into remove-repr-wrapped (8), remove-provable-identity (9) and keep-human-single-line (9); measured that the repr-wrapped sites double-escape backslashes today.
- 2026-10-12 draft (opencode): created.

## Goal

Stop escaping drift details for a wire form that no longer exists. Remove `escape_detail` from every call site where it is either a provable identity or actively double-escapes a `repr`, keep it at the sites where it still keeps an untrusted value on one human-rendered line, and make the helper's documentation say which of those it is for.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and behavioral tests

- [x] E-01 Record the baseline on the unmodified tree: the full call-site census (`rg -n "escape_detail\(" agent_workflows`), and the failing node-id set of a bare `python3 -m pytest` run, so later failures can be compared by node id rather than by count.
  - Depends on: none
  - Expected outcome: a census matching F-02 (26 call sites: `attention.py` 12, `specs.py` 8, `research_index.py` 3, `releases.py` 2, `cli.py` 1, re-measured at review HEAD), or any drift recorded and every added or removed site classified into F-03/F-04/F-05 before E-03 proceeds; plus a saved list of baseline failing node ids (possibly empty).
  - Execution state: performed

- [x] E-02 Create `tests/test_drift_detail_escaping.py` with behavioral tests that drive the real producers on temp fixtures and assert on the returned `Drift.detail`:
  (a) for each REPR-WRAPPED site (F-03), a hostile native value containing a backslash and a tab yields a detail EQUAL to the producer's message formatted with a single `repr` (for example `"backlog status " + repr("we\\ird")`), and containing no raw tab, newline or carriage return. Drive `attention.scan` on a temp repo for the backlog, plans, research, release and prompts producers (`_backlog_record`, `_plans_record`, `_research_record`, `_release_record`, `_prompts_record`), and `specs.validate_spec` directly for the spec status, unknown `Gate-Kind` and invalid `Gate-Ref` producers. The prompts producer's value is a bucket directory name, so its fixture must place a prompt under an unrecognized bucket directory. A backslash CANNOT reach this producer (`attention._prompt_disposition_from_rel` runs `rel.replace("\\", "/")` before splitting, measured at review), so use a bucket name containing a TAB (which `repr` renders `\t` and the wrapper doubles to `\\t`) and assert exact equality with the single-repr form; if the platform refuses such a directory name, use a plain unrecognized bucket and assert single-repr equality only, recording which.
  (b) for the PROVABLE-IDENTITY sites (F-04), the detail equals the literal message exactly (`"Scope is over-length or has control chars/newlines"`, `"Summary is over-length or has control chars/newlines"`, `"metadata bullet - <Key>: appears <N> times"`, the three research `"... is over-length or has control chars/newlines"` messages, the two releases messages, and `"dir <disp> vs status <status>"`).
  (c) one end-to-end case: `python -m agent_workflows.cli attention --check --json --dir <temp repo>` run as a subprocess on the hostile backlog fixture, parsing the JSON and asserting the drift entry's `detail` decodes to the single-repr form. Use `--json`. Measured at review: `attention --check --json` emits an `aw.agent/v1` payload whose `data.drift[].detail` AND `diagnostics[].detail` both carry the detail (on the unmodified tree the decoded detail for `- Status: we\ird` holds FOUR backslashes between `we` and `ird`, where a single `repr` gives two), while the compact `--agent` result record carries `location` and `rule` only. Assert on `data.drift` and also on the matching `diagnostics` entry.
  Run the new module on the UNMODIFIED tree first: (a) must FAIL for the repr-wrapped sites (double backslash), and (b) must PASS (identity), which is what proves the F-04 sites are no-ops.
  - Depends on: E-01
  - Expected outcome: the new module exists; on the unmodified tree the (a) cases fail with a doubled-backslash mismatch and the (b) cases pass.
  - Execution state: performed

### Task group 2: retire the redundant calls

- [x] E-03 Remove the `A.escape_detail(...)` wrapper, keeping the inner f-string byte-for-byte, at the 8 REPR-WRAPPED sites F-03 lists: `attention._prompts_record` (`f"prompt disposition {disp!r}"`), `attention._release_record` (`f"release status {status!r}"`), `attention._plans_record` (`f"plan status {status!r}"`), `attention._research_record` (`f"research status {raw_status_str!r}"`), `attention._backlog_record` (`f"backlog status {status!r}"`), and in `specs.validate_spec` the three messages `f"status {status!r} not in the spec enum"`, `f"unknown Gate-Kind {kind!r}"` and `f"invalid Gate-Ref for {kind}: {ref!r}"`.
  WHY REMOVING IS SAFE AND NOT A LOOSENING: `repr` of a `str` never contains a raw tab, newline or carriage return (it renders them as `\t`, `\n`, `\r`) and already escapes backslash, so the detail stays single-line on every surface without the wrapper. The only behavior the wrapper adds is the double escape F-03 measured.
  - Depends on: E-02
  - Expected outcome: the 8 sites no longer call `escape_detail`; the E-02 (a) cases pass.
  - Execution state: performed

- [x] E-04 Remove the `A.escape_detail(...)` wrapper at the 9 PROVABLE-IDENTITY sites F-04 lists, keeping the inner string byte-for-byte: `specs.validate_spec` (`f"metadata bullet - {k}: appears {count} times"`, the `Scope` and `Summary` over-length messages), `research_index.check_drift` (the `Summary`, `Topic` and `Consumed-by` over-length messages), `releases.validate_release` (the `Summary bullet` and `Summary prose` messages), and `attention._plans_record` (`f"dir {disp} vs status {status}"`).
  - Depends on: E-02
  - Expected outcome: the 9 sites no longer call `escape_detail`; the E-02 (b) cases still pass, unchanged.
  - Execution state: performed

- [x] E-05 In `agent_workflows/attention_contract.py`, rewrite the comment above `_AGENT_ESCAPES` and the `escape_detail` docstring so they state the helper's REMAINING purpose: keeping an untrusted, non-`repr`'d value on one line of a HUMAN-rendered surface (the `aw attention --check` `location: rule: detail` lines, the board's gate-ref suffix, and a spec history line), and state that the `aw.agent/v1` and `--json` surfaces JSON-encode `detail` and need no escaping, and that a value already passed through `repr` must NOT be passed through it again. Do NOT change `_AGENT_ESCAPES`, the function body, or its name. Do NOT touch the 9 call sites F-05 keeps.
  - Depends on: E-03, E-04
  - Expected outcome: the census reports exactly the 9 F-05 sites; the function body and `_AGENT_ESCAPES` are byte-identical; the docstring no longer claims a TSV agent record.
  - Execution state: performed

### Task group 3: record the contract and the change

- [x] E-06 Amend spec `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` Section 8.8's "Deterministic escaping per surface" bullet with a parenthetical `(AMENDED by plan 8cu5ml: ...)` recording that the `--agent` TSV form no longer exists, that `--agent` emits `aw.agent/v1` whose JSON encoding keeps `detail` single-line, and that tab/newline/backslash escaping now applies only to non-`repr`'d untrusted values on human single-line surfaces. Append a history line with `aw specs note <spec> --message ...` (do not hand-edit the history section). Add one `- Fixed:` line to `CHANGELOG.md` under the pending release, in plain user-facing prose with no em or en dashes, saying that drift messages quoting an authored status or gate value no longer double their backslashes.
  - Depends on: E-05
  - Expected outcome: the spec bullet carries the amendment and a new history line; `aw specs check` stays clean for that spec; CHANGELOG has the new line.
  - Execution state: performed

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
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: keep `repr`, drop `escape_detail`. `repr` quotes the value (so a reader can see leading or trailing whitespace and an empty string), already renders tab, newline and CR as visible escapes, and is what every one of these messages was written with. Dropping `repr` instead would remove the quotes from 8 user-visible messages; dropping `escape_detail` changes only the doubled backslash F-03 measured.

### OQ-02: Is the doubled backslash a `bug` that should gate the release?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: no; the item stays `chore` as filed. The defect only appears when an authored status or gate value already contains a backslash or tab, which is itself invalid input reported by the same message, and the message remains readable and one line. That is not a user-perceptible impact under the AGENTS.md test, and this plan does not alter the backlog item's classification.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `rg -n "escape_detail\(" agent_workflows` census output (26 call sites plus the definition expected, or any drift classified per E-01), and paste the bare `python3 -m pytest` summary line from the unmodified tree together with the list of failing node ids (or state it is empty).
  - Observed evidence:
    `rg -n "escape_detail\(" agent_workflows` baseline census on unmodified tree (HEAD a752c876a9e884190280982579128c73076191bf):
    ```
    agent_workflows/attention.py:620:                        A.escape_detail(f"id {rec.id} also on {seen_ids[rec.id]}"),
    agent_workflows/attention.py:1228:                A.escape_detail(f"prompt disposition {disp!r}"),
    agent_workflows/attention.py:1271:                A.escape_detail(f"release status {status!r}"),
    agent_workflows/attention.py:1375:                A.escape_detail(f"plan status {status!r}"),
    agent_workflows/attention.py:1396:                A.escape_detail(f"dir {disp} vs status {status}"),
    agent_workflows/attention.py:1480:                    A.escape_detail(f"research status {raw_status_str!r}"),
    agent_workflows/attention.py:1540:                A.escape_detail(f"backlog status {status!r}"),
    agent_workflows/attention.py:1764:                A.escape_detail(detail),
    agent_workflows/attention.py:2443:        _gate_ref_display(A.escape_detail((it.gate or {}).get("ref", "")), long=long)
    agent_workflows/attention.py:2561:                A.escape_detail(g.get("ref", "")), long=bool(long)
    agent_workflows/attention.py:2592:        suffix = f"  [gate {g.get('kind')}: {A.escape_detail(g.get('ref', ''))}]"
    agent_workflows/attention.py:3128:            A.escape_detail(it.gate.get("ref", "")), long=bool(long)
    agent_workflows/releases.py:139:                    A.escape_detail(
    agent_workflows/releases.py:151:                    A.escape_detail("Summary prose contains control characters"),
    agent_workflows/specs.py:387:                    A.escape_detail(f"metadata bullet - {k}: appears {count} times"),
    agent_workflows/specs.py:404:                A.escape_detail(f"status {status!r} not in the spec enum"),
    agent_workflows/specs.py:425:                        A.escape_detail(f"unknown Gate-Kind {kind!r}"),
    agent_workflows/specs.py:433:                        A.escape_detail(f"invalid Gate-Ref for {kind}: {ref!r}"),
    agent_workflows/specs.py:459:                A.escape_detail("Scope is over-length or has control chars/newlines"),
    agent_workflows/specs.py:469:                A.escape_detail("Summary is over-length or has control chars/newlines"),
    agent_workflows/specs.py:920:        hist_msg += f" (was: {A.escape_detail(old_prose)[:160]})"
    agent_workflows/specs.py:923:            f"; folded Implemented line: {A.escape_detail(implemented_prose)[:160]}"
    agent_workflows/cli.py:15008:                                    g_ref = att.A.escape_detail(g.get("ref", ""))
    agent_workflows/attention_contract.py:952:def escape_detail(detail: str) -> str:
    agent_workflows/research_index.py:766:                        A.escape_detail(
    agent_workflows/research_index.py:779:                            A.escape_detail(
    agent_workflows/research_index.py:792:                            A.escape_detail(
    ```
    Total 26 call sites (12 attention.py, 8 specs.py, 3 research_index.py, 2 releases.py, 1 cli.py) + 1 definition in attention_contract.py. Exactly matches F-02.
    Bare `python3 -m pytest` on unmodified tree:
    `7608 passed, 2 skipped, 3 warnings in 731.01s (0:12:11)`
    Failing node-id set: empty (0 failed).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `python3 -m pytest tests/test_drift_detail_escaping.py -o addopts=""` output from the UNMODIFIED tree showing every repr-wrapped case failing with a doubled-backslash assertion diff and every identity case passing, then paste the same command's output after E-03/E-04 showing all cases passing. Paste the test source for one repr-wrapped case and the end-to-end subprocess case, showing they drive `attention.scan`, `specs.validate_spec` and the `aw attention` CLI and assert on returned details, with no reading of production source.
  - Observed evidence:
    `python3 -m pytest tests/test_drift_detail_escaping.py -o addopts=""` on UNMODIFIED tree:
    ```
    FAILED tests/test_drift_detail_escaping.py::TestReprWrappedSites::test_specs_validate_spec_unknown_gate_kind_escaping - AssertionError: "unknown Gate-Kind 'we\\\\\\\\ird'" != "unknown Gate-Kind 'we\\\\ird'"
    FAILED tests/test_drift_detail_escaping.py::TestReprWrappedSites::test_specs_validate_spec_status_escaping - AssertionError: "status 'we\\\\\\\\ird' not in the spec enum" != "status 'we\\\\ird' not in the spec enum"
    FAILED tests/test_drift_detail_escaping.py::TestReprWrappedSites::test_release_record_status_escaping - AssertionError: "release status 'we\\\\\\\\ird'" != "release status 'we\\\\ird'"
    FAILED tests/test_drift_detail_escaping.py::TestReprWrappedSites::test_research_record_status_escaping - AssertionError: "research status 'we\\\\\\\\ird'" != "research status 'we\\\\ird'"
    FAILED tests/test_drift_detail_escaping.py::TestReprWrappedSites::test_backlog_record_status_escaping - AssertionError: "backlog status 'we\\\\\\\\ird'" != "backlog status 'we\\\\ird'"
    FAILED tests/test_drift_detail_escaping.py::TestReprWrappedSites::test_specs_validate_spec_invalid_gate_ref_escaping - AssertionError: "invalid Gate-Ref for external: 'we\\\\\\\\ird\\\\tx'" != "invalid Gate-Ref for external: 'we\\\\ird\\tx'"
    FAILED tests/test_drift_detail_escaping.py::TestReprWrappedSites::test_prompts_record_bucket_escaping - AssertionError: "prompt disposition 'unknown\\\\tbucket'" != "prompt disposition 'unknown\\tbucket'"
    FAILED tests/test_drift_detail_escaping.py::TestEndToEndSubprocess::test_cli_attention_check_json_backlog_hostile_status - AssertionError: "backlog status 'we\\\\\\\\ird'" != "backlog status 'we\\\\ird'"
    ========================= 8 failed, 10 passed in 2.88s =========================
    ```
    `python3 -m pytest tests/test_drift_detail_escaping.py -o addopts=""` after E-03/E-04:
    ```
    tests/test_drift_detail_escaping.py ..................                   [100%]
    ============================== 18 passed in 2.57s ==============================
    ```
    Test source for repr-wrapped case (`test_backlog_record_status_escaping`):
    ```python
    def test_backlog_record_status_escaping(self):
        """attention._backlog_record: backlog status {status!r}."""
        status = "we\\ird"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bdir = root / ".aw" / "records" / "backlog" / "open"
            bdir.mkdir(parents=True, exist_ok=True)
            p = bdir / "20260101-b10001-01-b10001-test.backlog.md"
            p.write_text(
                f"- Id: b10001\n- Status: {status}\n- Priority: high\n- Work-Kind: feature\n- Summary: test\n",
                encoding="utf-8",
            )

            items, drift = att.scan(root)
            unknown = [d for d in drift if d.rule == "attention.unknown-status"]
            self.assertEqual(len(unknown), 1)
            detail = unknown[0].detail
            self.assertNotIn("\t", detail)
            self.assertNotIn("\n", detail)
            self.assertNotIn("\r", detail)
            expected = f"backlog status {status!r}"
            self.assertEqual(detail, expected)
    ```
    Test source for end-to-end subprocess case (`test_cli_attention_check_json_backlog_hostile_status`):
    ```python
    def test_cli_attention_check_json_backlog_hostile_status(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bdir = root / ".aw" / "records" / "backlog" / "open"
            bdir.mkdir(parents=True, exist_ok=True)
            p = bdir / "20260101-b10001-01-b10001-test.backlog.md"
            p.write_text(
                "- Id: b10001\n- Status: we\\ird\n- Priority: high\n- Work-Kind: feature\n- Summary: test\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows.cli",
                    "attention",
                    "--check",
                    "--json",
                    "--dir",
                    str(root),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1)
            payload = json.loads(proc.stdout)

            rel_loc = ".aw/records/backlog/open/20260101-b10001-01-b10001-test.backlog.md"
            drifts = [
                d
                for d in payload.get("data", {}).get("drift", [])
                if d.get("location") == rel_loc
            ]
            self.assertEqual(len(drifts), 1)
            expected = "backlog status " + repr("we\\ird")
            self.assertEqual(drifts[0]["detail"], expected)

            diags = [
                d
                for d in payload.get("diagnostics", [])
                if d.get("location") == rel_loc
            ]
            self.assertEqual(len(diags), 1)
            self.assertEqual(diags[0]["detail"], expected)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff agent_workflows/attention.py agent_workflows/specs.py` hunks for the 8 repr-wrapped sites, showing only the `A.escape_detail(` wrapper and its closing parenthesis removed and each inner f-string unchanged. Paste a `python3 -c` session re-driving the F-03 fixture (`- Status: we\ird` through `attention.scan`) showing the detail now equals `"backlog status " + repr("we\\ird")`.
  - Observed evidence:
    `git diff agent_workflows/attention.py agent_workflows/specs.py` hunks for the 8 repr-wrapped sites:
    ```diff
    --- a/agent_workflows/attention.py
    +++ b/agent_workflows/attention.py
    @@ -1225,7 +1225,7 @@ def _prompts_record(
                 core.Drift(
                     rel,
                     "attention.unknown-status",
    -                A.escape_detail(f"prompt disposition {disp!r}"),
    +                f"prompt disposition {disp!r}",
                 )
             )
    @@ -1268,7 +1268,7 @@ def _release_record(
                 core.Drift(
                     rel,
                     "attention.unknown-status",
    -                A.escape_detail(f"release status {status!r}"),
    +                f"release status {status!r}",
                 )
             )
    @@ -1372,7 +1372,7 @@ def _plans_record(
                 core.Drift(
                     rel,
                     "attention.unknown-status",
    -                A.escape_detail(f"plan status {status!r}"),
    +                f"plan status {status!r}",
                 )
             )
    @@ -1477,7 +1477,7 @@ def _research_record(
                     core.Drift(
                         rel,
                         "attention.unknown-status",
    -                    A.escape_detail(f"research status {raw_status_str!r}"),
    +                    f"research status {raw_status_str!r}",
                     )
                 )
    @@ -1537,7 +1537,7 @@ def _backlog_record(
                 core.Drift(
                     rel,
                     "attention.unknown-status",
    -                A.escape_detail(f"backlog status {status!r}"),
    +                f"backlog status {status!r}",
                 )
             )
    --- a/agent_workflows/specs.py
    +++ b/agent_workflows/specs.py
    @@ -401,7 +401,7 @@ def validate_spec(path: Path, text: str) -> List[core.Drift]:
                 core.Drift(
                     loc,
                     "attention.unknown-status",
    -                A.escape_detail(f"status {status!r} not in the spec enum"),
    +                f"status {status!r} not in the spec enum",
                 )
             )
    @@ -422,7 +422,7 @@ def validate_spec(path: Path, text: str) -> List[core.Drift]:
                         core.Drift(
                             loc,
                             "attention.gate-malformed",
    -                        A.escape_detail(f"unknown Gate-Kind {kind!r}"),
    +                        f"unknown Gate-Kind {kind!r}",
                         )
                     )
                 elif not A.validate_gate_ref(kind, ref):
    @@ -430,7 +430,7 @@ def validate_spec(path: Path, text: str) -> List[core.Drift]:
                         core.Drift(
                             loc,
                             "attention.gate-malformed",
    -                        A.escape_detail(f"invalid Gate-Ref for {kind}: {ref!r}"),
    +                        f"invalid Gate-Ref for {kind}: {ref!r}",
                         )
                     )
    ```
    Re-driving session output:
    ```
    $ python3 -c '
    import tempfile; from pathlib import Path; from agent_workflows import attention as att
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); bdir = root / ".aw" / "records" / "backlog" / "open"; bdir.mkdir(parents=True, exist_ok=True)
        (bdir / "20260101-b10001-01-b10001-test.backlog.md").write_text("- Id: b10001\n- Status: we\\ird\n- Priority: high\n- Work-Kind: feature\n- Summary: test\n", encoding="utf-8")
        items, drift = att.scan(root)
        for d in drift:
            if d.rule == "attention.unknown-status":
                print("got detail:", repr(d.detail))
                expected = "backlog status " + repr("we\\ird")
                print("expected:  ", repr(expected))
                print("matches?   ", d.detail == expected)
    '
    got detail: "backlog status 'we\\\\ird'"
    expected:   "backlog status 'we\\\\ird'"
    matches?    True
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff` hunks for the 9 identity sites in `specs.py`, `research_index.py`, `releases.py` and `attention.py`, showing only the wrapper removed and each inner string unchanged, and paste the passing identity cases from the post-change V-02 run.
  - Observed evidence:
    `git diff` hunks for the 9 identity sites:
    ```diff
    --- a/agent_workflows/specs.py
    +++ b/agent_workflows/specs.py
    @@ -384,7 +384,7 @@ def validate_spec(path: Path, text: str) -> List[core.Drift]:
                     core.Drift(
                         loc,
                         "spec.metadata-bullet-repeated",
    -                    A.escape_detail(f"metadata bullet - {k}: appears {count} times"),
    +                    f"metadata bullet - {k}: appears {count} times",
                     )
                 )
    @@ -456,7 +456,7 @@ def validate_spec(path: Path, text: str) -> List[core.Drift]:
                 core.Drift(
                     loc,
                     "attention.unsafe-field",
    -                A.escape_detail("Scope is over-length or has control chars/newlines"),
    +                "Scope is over-length or has control chars/newlines",
                 )
             )
    @@ -466,7 +466,7 @@ def validate_spec(path: Path, text: str) -> List[core.Drift]:
                 core.Drift(
                     loc,
                     "attention.unsafe-field",
    -                A.escape_detail("Summary is over-length or has control chars/newlines"),
    +                "Summary is over-length or has control chars/newlines",
                 )
             )
    --- a/agent_workflows/research_index.py
    +++ b/agent_workflows/research_index.py
    @@ -763,9 +763,7 @@ def check_drift(
                         Drift(
                             e.path,
                             "attention.unsafe-field",
    -                        A.escape_detail(
    -                            "Summary is over-length or has control chars/newlines"
    -                        ),
    +                        "Summary is over-length or has control chars/newlines",
                         )
                     )
                 )
    @@ -776,9 +774,7 @@ def check_drift(
                             e.path,
                             "attention.unsafe-field",
    -                        A.escape_detail(
    -                            "Topic is over-length or has control chars/newlines"
    -                        ),
    +                        "Topic is over-length or has control chars/newlines",
                             )
                         )
                     )
    @@ -789,9 +785,7 @@ def check_drift(
                             e.path,
                             "attention.unsafe-field",
    -                        A.escape_detail(
    -                            "Consumed-by is over-length or has control chars/newlines"
    -                        ),
    +                        "Consumed-by is over-length or has control chars/newlines",
                             )
                         )
                     )
    --- a/agent_workflows/releases.py
    +++ b/agent_workflows/releases.py
    @@ -136,9 +136,7 @@ def validate_release(path: Path, text: str) -> List[_core.Drift]:
                     _core.Drift(
                         loc,
                         "attention.unsafe-field",
    -                    A.escape_detail(
    -                        "Summary bullet is over-length or has control chars/newlines"
    -                    ),
    +                    "Summary bullet is over-length or has control chars/newlines",
                     )
                 )
         else:
    @@ -148,7 +146,7 @@ def validate_release(path: Path, text: str) -> List[_core.Drift]:
                     _core.Drift(
                         loc,
                         "attention.unsafe-field",
    -                    A.escape_detail("Summary prose contains control characters"),
    +                    "Summary prose contains control characters",
                     )
                 )
    --- a/agent_workflows/attention.py
    +++ b/agent_workflows/attention.py
    @@ -1393,7 +1393,7 @@ def _plans_record(
                 core.Drift(
                     rel,
                     "attention.disposition-mismatch",
    -                A.escape_detail(f"dir {disp} vs status {status}"),
    +                f"dir {disp} vs status {status}",
                 )
             )
    ```
    Passing identity cases from V-02:
    All 9 test methods in `TestProvableIdentitySites` passed:
    `test_specs_validate_spec_duplicate_bullet`, `test_specs_validate_spec_scope_over_length`, `test_specs_validate_spec_summary_over_length`, `test_research_index_summary_over_length`, `test_research_index_topic_over_length`, `test_research_index_consumed_by_over_length`, `test_releases_validate_release_summary_bullet_over_length`, `test_releases_validate_release_summary_prose_control_char`, `test_attention_plans_record_dir_vs_status`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the post-change `rg -n "escape_detail\(" agent_workflows` census showing exactly the 9 F-05 sites plus the definition. Paste `git diff agent_workflows/attention_contract.py` showing only the comment and docstring changed (the `_AGENT_ESCAPES` tuple and the function body byte-identical). Paste `git diff` proving none of the 9 kept call-site lines changed, and paste `tests/test_attention_contract.py::test_detail_escaping_keeps_one_line` and `tests/test_attention_lane_detail_bound.py` passing.
  - Observed evidence:
    Post-change census (`rg -n "escape_detail\(" agent_workflows`):
    ```
    agent_workflows/attention.py:620:                        A.escape_detail(f"id {rec.id} also on {seen_ids[rec.id]}"),
    agent_workflows/attention.py:1764:                A.escape_detail(detail),
    agent_workflows/attention.py:2443:        _gate_ref_display(A.escape_detail((it.gate or {}).get("ref", "")), long=long)
    agent_workflows/attention.py:2561:                A.escape_detail(g.get("ref", "")), long=bool(long)
    agent_workflows/attention.py:2592:        suffix = f"  [gate {g.get('kind')}: {A.escape_detail(g.get('ref', ''))}]"
    agent_workflows/attention.py:3128:            A.escape_detail(it.gate.get("ref", "")), long=bool(long)
    agent_workflows/specs.py:920:        hist_msg += f" (was: {A.escape_detail(old_prose)[:160]})"
    agent_workflows/specs.py:923:            f"; folded Implemented line: {A.escape_detail(implemented_prose)[:160]}"
    agent_workflows/attention_contract.py:955:def escape_detail(detail: str) -> str:
    agent_workflows/cli.py:15008:                                    g_ref = att.A.escape_detail(g.get("ref", ""))
    ```
    Shows exactly the 9 F-05 sites plus definition.
    `git diff agent_workflows/attention_contract.py`:
    ```diff
    --- a/agent_workflows/attention_contract.py
    +++ b/agent_workflows/attention_contract.py
    @@ -943,14 +943,26 @@ RULE_IDS: FrozenSet[str] = frozenset(
         )
     )

    -# Historical escaping policy for the detail field (tab/newline/backslash), originally
    -# preventing line splits in the retired single-line TSV agent record. Kept for caller
    -# compatibility across attention and spec checkers until retired in a unified pass.
    +# Escaping policy for untrusted, non-repr'd values rendered on single-line human surfaces
    +# (tab/newline/carriage-return/backslash), preventing line splits in the human `location: rule: detail`
    +# output, board gate-ref suffixes, and spec history lines. The name _AGENT_ESCAPES is historical:
    +# the retired TSV wire form is gone, and modern agent surfaces (aw.agent/v1, --json) JSON-encode
    +# `detail` so they need no escaping. Values already passed through repr must NOT be passed through
    +# escape_detail (repr already escapes control characters and backslashes, so re-escaping doubles them).
     _AGENT_ESCAPES = (("\\", "\\\\"), ("\t", "\\t"), ("\n", "\\n"), ("\r", "\\r"))


     def escape_detail(detail: str) -> str:
    -    """Escape a drift ``detail`` for the single-line ``location<TAB>rule<TAB>detail`` agent record."""
    +    """Keep an untrusted, non-repr'd value on one line of a human-rendered surface.
    +
    +    Replaces backslash, tab, newline, and carriage return with their two-character escape
    +    sequences so an unescaped value cannot split a single-line human output (such as
    +    `location: rule: detail` checks, board gate-ref suffixes, or spec history records).
    +
    +    Machine-readable surfaces (aw.agent/v1, --json) JSON-encode `detail` and require no escaping.
    +    Callers formatting values with `repr` must NOT pass them through `escape_detail`, as repr
    +    already escapes control bytes and backslashes.
    +    """

         out = detail
         for raw, rep in _AGENT_ESCAPES:
    ```
    The `_AGENT_ESCAPES` tuple and `escape_detail` body are byte-identical.
    None of the 9 kept call sites in `attention.py`, `specs.py`, or `cli.py` was changed.
    Tests passing:
    ```
    tests/test_attention_contract.py .                                       [ 25%]
    tests/test_attention_lane_detail_bound.py ...                            [100%]
    4 passed in 2.17s
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the amended Section 8.8 bullet text, the new spec history line written by `aw specs note`, the `aw specs check` output for that spec showing no finding, and the new CHANGELOG line. Then paste the bare `python3 -m pytest` summary line and state the failing node-id set equals the V-01 baseline, plus `aw check` and `aw ipd lint` output for this plan.
  - Observed evidence:
    Amended Section 8.8 bullet text in `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`:
    `- **Deterministic escaping per surface.** JSON output escapes per the canonical profile. The Markdown board escapes Markdown metacharacters deterministically so a field cannot break the table, inject a link/image, or start a new block. The \`--agent\` \`location<TAB>rule<TAB>detail\` form escapes tab, newline, and backslash per Section 8.3. (AMENDED by plan qpw45x: narrowed the Markdown board escaping to the five measured metacharacters \`\\\`, \`|\`, \`[\`, \`]\`, \`<\` applied to \`detail_text\` at inline emission, with \`\\\` escaped first for unambiguity, \`|\` preventing table breaks, \`[\`/\`]\` neutralizing link/image injection, and \`<\` neutralizing HTML tags. An unbounded reading of "Markdown metacharacters" would backslash-litter the majority of the live corpus on a human-facing surface with no machine reader; five characters are deliberately left unescaped (measured 2026-10-07 over 3379 extracted details via \`_extract_detail\` on \`.aw/records/**/*.md\`: \`\` \` \`\` in 1196 values, zero odd counts; \`_\` in 1287 values, cosmetic intraword emphasis; \`*\` in 88 values, cosmetic emphasis; \`#\` in 55 values and \`>\` in 212 values, heading/blockquote syntax inactive after the fixed six-space detail indent). \`--format markdown\` is the default board rendered color-free (constructing Term with \`color=False\`), ensuring deterministic ANSI-free Markdown output across environments without a separate renderer.) (AMENDED by plan 8cu5ml: the retired --agent TSV location<TAB>rule<TAB>detail form no longer exists; --agent emits aw.agent/v1 whose JSON encoding keeps detail single-line without wire escaping; tab, newline, carriage return, and backslash escaping now applies only to non-repr'd untrusted values on human single-line surfaces.)`

    New spec history line written by `aw specs note`:
    `- 2026-10-13 note (aw specs): AMENDED by plan 8cu5ml (4ep6mp-01): Section 8.8 amended to state --agent TSV form no longer exists, aw.agent/v1 JSON encoding keeps detail single-line without wire escaping, and tab/newline/CR/backslash escaping applies only to non-repr'd untrusted values on human single-line surfaces.`

    `aw specs check .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`:
    `aw specs check: all specs conform. 1 specs checked.`

    New CHANGELOG line:
    `- Fixed: drift messages quoting an authored status or gate value no longer double their backslashes.`

    Bare `python3 -m pytest` summary line:
    `7626 passed, 2 skipped, 3 warnings in 373.26s (0:06:13)`
    Failing node-id set equals V-01 baseline: empty (0 failed).

    `aw check` output:
    Pre-existing repo issues only (errors 3, warnings 4, info 118 on unrelated artifacts); zero issues in modified files.

    `aw ipd lint .aw/records/plans/pending/20261011-4ep6mp-01-8cu5ml-retire-the-redundant-escape-detail-calls-on-drift-details-wh.ipd.md`:
    `approved plan 20261011-4ep6mp-01-8cu5ml [low] conforming`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive change: a single helper's call-site population, classified once and pruned once, with the test that proves the pruning and the documentation that records what remains. Splitting the 8 repr-wrapped sites from the 9 identity sites would leave the helper's docstring describing a half-migrated population.

EXECUTION CONTRACT. Execution requires explicit human approval first (`- Status: approved`); OQ-01 and OQ-02 are resolved and non-blocking. Run `aw ipd begin` first when executing by hand (a runner performs begin for a managed lane). Commit through `aw commit 8cu5ml -- <paths>` with only this plan's declared paths, never `git add -A` and never a push. SCOPE FENCE: `- Scope-Paths:` is a declaration; an out-of-scope edit that proves necessary is made and then JUSTIFIED at finalize (`--scope-reason`), and a declared path left unmodified needs a `--scope-ack`.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries concrete pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the RUNNER owns the terminal transition; when executing by hand, run `aw ipd finalize` (never a hand-rolled `git mv`). Backlog `4ep6mp` is already `graduated` and carries no `- Blocks-Release:`; it closes `done` through the `From-Backlog` handoff once this plan is executed, so do not set it `done` by hand.
