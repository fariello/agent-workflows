# Review findings: plan n9ua3b

- Subject-Id: n9ua3b
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (BLOCKER, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed), PR-011 (LOW, fixed), PR-012 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `d226f5cf`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `clean` after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator row check does not apply.

THE PLAN'S DIAGNOSIS IS CORRECT AND UNUSUALLY WELL EVIDENCED. I re-drove every claim rather than trusting
any, and the analytical core reproduces:

- F-01 reproduces verbatim. `docs/cli-output-contract.md` Section 10 reads "`CommandResult` and
  `aw.agent/v1` **SUBSUMES and REPLACES** the legacy `Drift` TSV wire format" and "Exactly one canonical
  machine format (`aw.agent/v1`) is active"; spec `20260818-1525-01` carries the 2026-08-23 `aw specs note`
  recording "G6 SUPERSEDED". So the plan is right that the backlog item's "needs a maintainer ruling" is
  already answered, and right to decide rather than defer.
- F-02 reproduces exactly and is the finding that makes the plan small. `git tag` lists four tags; at the
  newest, `v1.3.0-rc.1`, `git ls-tree` shows fifteen modules and NONE of `plans_index.py`,
  `prompts_index.py`, `research_index.py` or `artifact_core.py`. No released consumer parses these bytes.
- F-04's deadness claim reproduces. `grep -rn "emit_findings|exit_code_for"` across the whole checkout
  finds `artifact_types.py:155` (its definition), `:147` (`exit_code_for`'s), and `:188` (the single call
  from inside `emit_findings`). Nothing else. The deletion is safe.
- F-05 reproduces including the part that makes it worth taking. `aw sanitize . --agent` emits a conforming
  `aw.agent/v1` record while `engine.py:1451` and the `/assess local-leaks` lens both promise
  `location\trule\tseverity`; and the lens's "use the engine's `severity` field directly" really is
  unsatisfiable, since `to_agent_record` emits `{location, rule}` per diagnostic unless `context.verbose`,
  and `aw sanitize --agent --verbose` exits 2 on an unrecognized argument.
- F-07 reproduces to the exact exception text, and it is the strongest row in the plan:
  `ValueError: Invalid aw.agent/v1 record: Exit code mismatch: exit=0 incompatible with negative outcome
  'findings'`, with the live `info`-exemption case present on this tree.

BUT THE THREE MIGRATION ITEMS WOULD NOT HAVE WORKED AS WRITTEN, and the reasons are mechanical rather than
matters of judgement. This is where the review's value is, and all three were measured rather than reasoned.

FIRST (PR-001, BLOCKER): THERE IS NO `--json` BRANCH TO REPLACE. E-02, E-03 and E-04 each instruct the
executor to replace "the `--json` branch's human prose". Reading all three `run_index` functions, the
`--check` path contains exactly two branches: `if getattr(args, "agent", False)` and the human
fallthrough. `--json` is never tested anywhere in that path, so it reaches the human print loop BY
ACCIDENT. The plan's F-06 describes the symptom correctly (`--json` is byte-identical to the unflagged run)
and mis-describes the cause, and the E-items inherit the error. The fix is not cosmetic: it changes the
items from "repair a broken branch" to "replace a two-branch structure with a three-audience dispatch",
which is a different edit and the reason routing everything through `select_output` is correct.

SECOND (PR-002, BLOCKER): THE PLAN CONTAINS A DIRECT SELF-CONTRADICTION BETWEEN E-01 AND E-02. E-01
requires the human branch byte-unchanged with its `location: rule: detail` lines; E-02 routes all output
through `renderers.get_renderer(ctx).emit(...)`. Driven at review, the human renderer produces:

```
AW index plans
✗ FINDINGS  2 findings

Findings:
  Issue: Manifest index is out of date
  - INDEX.json [WARNING]
    Fix: run 'aw index' to regenerate the manifest index.

Agent output: --agent (automatic when piped)
```

An executor following E-02 literally would ship that, silently replacing a user-visible surface the plan
promises not to touch, and would discover it only when E-01's own assertions failed, with no instruction
for what to do next. I RESOLVED THIS BY DEMONSTRATION rather than description, as the workflow requires for
a mechanism choice: `renderers.HumanRenderer.render` returns `str(result.data["human_rendered"])` verbatim
before building any banner, and setting that key reproduced the legacy line byte-exactly:

```
OUT: "INDEX.json: check.stale-index-stale: INDEX.json is out of date; run 'aw index plans'"
```

E-02 now mandates the hatch, E-01 expects the naive path to fail loudly, and V-02 requires the executor to
confirm by quotation which mechanism they used.

THIRD (PR-003, HIGH): E-02's `repo_root` INSTRUCTION CRASHES `--json` AND ONLY `--json`. The item says to
put `repo_root` into `CommandResult.data` "as `cli._run_check` does". `cli._run_check` puts a `str` there
(verified: `aw check plans --json` emits `data.repo_root` as a string). A `Path`, which is what the plan's
own `repo_root = Path(...)` idiom produces, makes `JSONRenderer.render` raise
`TypeError: Object of type PosixPath is not JSON serializable` out of `json.dumps(result.to_dict())`,
because `to_dict` passes `data` through unchanged. Driven both ways at review: `str` -> `OK rc=1`,
`PosixPath` -> `RAISED TypeError`. This is the worst shape of defect for a plan whose test module leads
with `--agent`, because the compact record never serializes `data` and so every `--agent` assertion passes.

FOURTH (PR-004, HIGH): THE DELETION ORPHANS A LIVE, TESTED HELPER THE PLAN NEVER MENTIONS.
`attention_contract.escape_detail` exists for exactly one declared purpose: its docstring says it escapes a
drift `detail` "for the single-line `location<TAB>rule<TAB>detail` agent record", and the comment above it
names `artifact_core.render_agent_drift` as the owner of that emission. It has 20 live call sites across
`attention.py`, `specs.py` and `cli.py`, plus `tests/test_attention_contract.py::test_detail_escaping_keeps_one_line`.
After E-05 it escapes tabs for a form no code emits, with a comment citing a deleted symbol. I did NOT fix
this by unwinding it (in `aw.agent/v1` the `detail` field is JSON-encoded, so the escaping is redundant
rather than wrong, and 20 call sites across three modules is a materially larger change than this plan's
subject). E-05 now corrects the comment and FILES the redundancy, so the debt is recorded rather than
hidden; this also closes the plan's own claim that nothing would still reference the removed form.

I ALSO FOUND A CROSS-PLAN COLLISION THE PLAN'S SURVEY MISSED (PR-005). Sibling `qgpanb` is `- Status:
reviewed`, declares `agent_workflows/research_index.py` and `agent_workflows/plans_index.py` in its own
`- Scope-Paths:`, and its E-03 text states plainly that "`aw index research --check` goes from exit 1 to
exit 0 once E-04 lands, and that is the intended effect rather than a side effect". This plan requires
exit-code PARITY on that exact command. The two are compatible as CODE (that plan edits the `Drift`
construction inside `check_drift`; this one edits emission inside `run_index`) and the runner isolates each
item and revalidates on merge, so I did not raise a sequencing hazard. It is an EVIDENCE-INTERPRETATION
hazard: an executor comparing against this plan's authored exit codes could read `qgpanb` having landed as
a regression of their own work, and E-04 and V-04 now say so explicitly.

ONE CAUSATION CLAIM IS WRONG IN A WAY THAT WOULD HAVE PRODUCED A FALSE HISTORY LINE (PR-006). The plan says
deleting the symbol "makes that spec text stale", of spec `20260808-1945-01`'s G3/N3/Section 11 required-reuse
constraint. Measured: `aw attention --check --agent` ALREADY emits a conforming `aw.agent/v1` record and
`grep` finds no `render_agent_drift` reference in `attention.py` at all, so attention stopped honoring that
constraint when it was migrated. E-08 would therefore have written an `aw specs note` announcing a
supersession that already happened. The note's wording now records an EXISTING supersession.

EVERY LIVE FIGURE HAS DRIFTED, ONE OF THEM IN A WAY THAT MOVES WHICH VERB DEMONSTRATES THE PLAN'S OWN TRAP
(PR-007). The research `--agent` output went from 115 lines to 123, its absolute-path count from 61 to 69,
and most consequentially the plans manifest went from ABSENT to STALE: `check.stale-index-missing` is `info`
(exempt, exit 0) while `check.stale-index-stale` is `warning` (exit 1), so the `findings`-with-`exit=0` pair
that F-07's trap turns on now appears on `index prompts --check` (two findings, `RC=0`) rather than on
`index plans --check` (which now reports `stale` and exits 1). Every such number is restated as context with
a re-derivation instruction, and E-03 now points at prompts as the verb that currently exhibits the trap.

THE SUITE IS NOT GREEN AND THE BAR WAS UNACHIEVABLE (PR-008). Bare `python3 -m pytest` at review HEAD:
`1 failed, 3487 passed, 2 skipped, 3 warnings in 118.63s`. The failure is
`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a
date-boundary bug pinning a history line against a hardcoded `2026-09-30`. E-05's "the full suite is green"
is therefore unsatisfiable, and an executor meeting it would either misattribute a pre-existing red or
paper over it. New F-15 records it; the bar is now no NEW failure, and fixing it is forbidden as out of
scope and another party's work.

THREE SMALLER CORRECTIONS. The plan's own `render_agent_drift` census missed the fifth reference, the
comment in `attention_contract.py` (PR-009), which matters because it is text that becomes false and is now
E-05's to correct. The clean-tree wording DIFFERS PER VERB and the plan asserted only the plans form:
measured, research prints `index --check: clean`, not `research index --check: clean`, so a test written to
the plan's text would fail on a correct implementation (PR-010). And E-01 cites
`tests/test_plans_index.py`'s `_run` harness as fixture material for a SUBPROCESS test, but that harness is
IN-PROCESS (`redirect_stdout` around a direct `run_index` call), so it is a fixture-construction reference
and not a subprocess one (PR-011).

ONE THING I CHECKED AND DID NOT FLAG. The plan deletes `render_agent_drift` while
`docs/cli-output-contract.md` Section 10 names it, and Section 10 also carries a stale code citation
(`artifact_core.py:247-266`; the definition is at line 672). I did not add a finding: Section 10 names the
symbol HISTORICALLY, as the thing being superseded, so the text stays true after deletion, and the plan is
right that amending Section 10 would be the alternative fix it rejects. The stale offset is pre-existing,
outside this plan's declared paths, and the plan's own convention note already records that offsets expire.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | Rubric G (executability), Rubric A | Plan E-02/E-03/E-04 ("the `--json` branch's human prose") and F-06; read of `plans_index.run_index`, `prompts_index.run_index`, `research_index.run_index` at review HEAD `d226f5cf` | All three E-items instruct replacing a `--json` branch that DOES NOT EXIST. Each `run_index` `--check` path holds exactly two branches (`if getattr(args, "agent", False)` and the human fallthrough); `--json` is never tested and reaches the human print loop by accident. F-06 reports the symptom correctly and the cause wrongly, and the E-items inherit it. The correct edit is a three-audience dispatch replacing a two-branch structure, which is a different change from the one authored. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-06 rewritten to state the real cause with the read that establishes it; E-02, E-03 and E-04 retitled from "MACHINE BRANCHES" to "OUTPUT" and each now states there is no `--json` branch and that `--json` becomes a real audience for the first time; E-01's `--json` assertion records the cause; the gate's new traps paragraph leads with it. |
| PR-002 | BLOCKER | IN-SCOPE | Rubric D (anti-regression), internal consistency | Plan E-01 ("ASSERT THE HUMAN BRANCH IS UNCHANGED") versus E-02 (route all output through `get_renderer`); `renderers.HumanRenderer.render` driven at review both ways | The plan's two requirements are incompatible as written. In human mode the shared renderer emits a title banner, an outcome line, a structured `Findings:` block and an `Agent output:` footer, not the `location: rule: detail` lines E-01 and V-02 require byte-unchanged. An executor would edit all three verbs and discover the contradiction only from a failing test, with no instruction for resolving it, and the tempting resolution (relax the assertion) ships a silent user-visible regression. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | Mechanism DEMONSTRATED at review, not described: new F-10 records the renderer's actual human output and that `data["human_rendered"]` reproduces the legacy line byte-exactly. E-02 now mandates the hatch and forbids a mode-guarded print path (which would re-fork the color decision this module's comment records as a measured defect); E-01 expects the naive path to fail loudly and forbids relaxing the assertion; V-02 requires confirmation by quotation. |
| PR-003 | HIGH | IN-SCOPE | Rubric A (correctness), Rubric E | Plan E-02 ("Put `repo_root` into `CommandResult.data` as `cli._run_check` does"); two review runs, `str` -> OK, `PosixPath` -> `TypeError`; `aw check plans --json` emitting a `str` | Following E-02 with a `Path` (which the plan's own `repo_root = Path(...)` idiom produces) makes `JSONRenderer.render` raise `TypeError: Object of type PosixPath is not JSON serializable`, because `to_dict` passes `data` through unchanged. `cli._run_check`, the cited pattern, passes a `str`. The `--agent` path never serializes `data`, so a `Path` passes every `--agent` assertion and fails under `--json` alone. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-11 records both runs; E-02 now states the `str` requirement with the measured failure and the `cli._run_check` precedent; E-01's `--json` assertion is identified as the one that catches it; V-02 requires the `--json` stdout plus a quotation of the line where `repo_root` is set. |
| PR-004 | HIGH | UNDER-SCOPE | Rubric C (architecture), Rubric D | `attention_contract.escape_detail` docstring and the comment at `attention_contract.py:787`; `grep -rn escape_detail --include=*.py .` returning 20 call sites plus `tests/test_attention_contract.py::test_detail_escaping_keeps_one_line` | Deleting `render_agent_drift` orphans a live, tested helper whose only declared purpose is that wire form: `escape_detail` escapes tabs and newlines so "the single-line `location<TAB>rule<TAB>detail` agent record" stays one line, and its comment names the deleted function as the emission owner. The plan never mentions it, so it would ship a comment citing a deleted symbol and leave the plan's own "no document promises a TSV form any more" claim false in code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-12 records the census and the docstring. E-05 now explicitly does NOT delete it or touch its callers (unwinding 20 sites across three modules is a larger change than this plan's subject, and the escaping is redundant rather than wrong under JSON encoding), MUST correct the comment, and MUST file the redundancy with `aw backlog new`, recording the id6. A new "Deferred / out of scope" entry carries it; V-05 requires the filed id and the untouched call-site count. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric E (testing), cross-plan consistency | `.aw/records/plans/pending/20260930-sevreg-01-qgpanb-...ipd.md` `- Status: reviewed`, its `- Scope-Paths:` naming both index modules, its E-03 text | A `reviewed` sibling declares two of this plan's modules and its STATED INTENT is to move `aw index research --check` from exit 1 to exit 0, which is one of this plan's exit-parity bars. The plan's cross-plan survey does not mention it. The two are compatible as code (different functions in the same modules) and the runner isolates each item, so this is not a sequencing hazard, but an executor comparing against this plan's authored exit codes could read the sibling having landed as a regression of their own work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-14 records the collision and why it is evidence-interpretation rather than sequencing; E-04 carries a coordination paragraph; V-04 requires the executor to state whether `qgpanb` has landed and forbids reporting its intended move as a regression; the `Required tests` section requires exit parity against the executor's own baseline. |
| PR-006 | MEDIUM | IN-SCOPE | Rubric D, honest records | Plan E-05 ("Deleting the symbol makes that spec text stale") and E-08; `aw attention --check --agent` emitting a conforming record; no `render_agent_drift` reference in `attention.py` | The plan asserts this change makes spec `20260808-1945-01`'s reuse constraint stale. It is ALREADY stale: attention emits a conforming `aw.agent/v1` record today and reaches `render_agent_drift` nowhere, so the constraint was superseded when attention was migrated. E-08 would have written an `aw specs note` announcing a supersession that already happened, which is a false history line on an implemented spec. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-13 records the measurement; E-05 restates the staleness as pre-existing and instructs the note to record an existing supersession; V-08 requires the note's causation wording be confirmed and the `attention --check --agent` record pasted as its evidence. |
| PR-007 | MEDIUM | IN-SCOPE | Rubric G (live-artifact re-derivation convention) | Plan F-07 ("`index plans --check` returns rc 0"), F-08 (61 of 115), Concern (115 lines); re-measured at review: 123 lines, 69 absolute, `index plans --check` rc 1 with `stale`, `index prompts --check` rc 0 with `missing` | Every live figure has drifted in one day, and one drift moves WHICH verb demonstrates the plan's own central trap: the plans manifest went from absent (`info`, exit 0) to stale (`warning`, exit 1), so the `findings`-with-`exit=0` pair F-07 turns on is now on prompts, not plans. An executor re-deriving F-07 on plans would not reproduce it and could conclude the trap was not real. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07, F-08 and the Concern restated with both measurements and explicit re-derivation instructions; E-02's trap paragraph and E-03 now name prompts as the current exhibitor while stating the verb itself must be re-derived; E-04's count paragraph and V-04 require re-derived before-counts with zero as the only fixed bar; a new `Required tests` bullet lists every drifted figure. |
| PR-008 | MEDIUM | IN-SCOPE | Rubric E (honest baselines) | Plan E-05 ("the full suite is green"); `python3 -m pytest` at review reporting `1 failed, 3487 passed, 2 skipped` | The suite is not green, so E-05's expected outcome is unsatisfiable. The failure is an unrelated date-boundary bug in `tests/test_backlog.py` pinning a hardcoded `2026-09-30`. An executor held to a green run would either misattribute the pre-existing red or paper over it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-15 records the run and names the failure and its cause; E-05's expected outcome changed to "no NEW failure"; the `Required tests` section states the bar and forbids fixing the test as out of scope and another party's. |
| PR-009 | LOW | IN-SCOPE | Rubric G, evidence completeness | Plan F-03's census (four sites); `grep -rn render_agent_drift --include=*.py .` returning five, the fifth being `attention_contract.py:787` | The plan corrects the backlog item's caller census and its own census misses a reference: a comment naming `render_agent_drift` as the owner of the emission `escape_detail` escapes for. Not a caller, so the deletion stays safe, but it is text that becomes false and an executor doing the E-05 deadness search would meet an unexplained match. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 restated with all five references at review HEAD; E-05 owns correcting the comment (shared with PR-004); V-05 tells the executor to EXPECT one non-caller match and to account for it. |
| PR-010 | LOW | IN-SCOPE | Rubric E (testing precision) | Plan E-01 and V-02 (the `plans index --check: clean` wording); `research_index.run_index` printing `index --check: clean` | The clean-tree wording differs per verb and the plan asserts only the plans form. Research prints `index --check: clean`, not `research index --check: clean`, so a test written literally to the plan's text would fail against a correct implementation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now enumerates all three wordings and requires per-verb assertion; E-03 and E-04 each name their own string; V-03 and V-04 require it in their evidence. |
| PR-011 | LOW | IN-SCOPE | Rubric G (executability) | Plan E-01 (cites `tests/test_plans_index.py`'s `_run` harness for a subprocess test); that harness using `redirect_stdout` around a direct `run_index` call | E-01 asks for a SUBPROCESS test and points at an IN-PROCESS harness as the shape to copy, which would send the executor to code that cannot serve the stated purpose (an in-process call cannot measure a process exit code, which E-01 separately requires the record's `exit` to equal). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01's reference clarified: `test_plans_index.py` is cited for FIXTURE construction only (`_plan`), with `conformance_matrix.run_cli`/`_pinned_env` or a direct `subprocess.run` for the process side, and the existing `_run` harness identified as in-process so it is not mistaken for a subprocess rig. |
| PR-012 | LOW | UNDER-SCOPE | Rubric G (gate completeness) | Plan's `## Approval and execution gate`; `- Blocks-Release: next` in front matter | The gate carries the commit, never-push, re-measure and lifecycle clauses but says nothing about the inherited release gate, so an executor could close backlog `qczq5r` `done` and drop the `Blocks-Release: next` the plan inherits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The POST-GATE LIFECYCLE paragraph now states that `qczq5r` is `graduated` on handoff and may close `done` only once this plan is `executed`, which is what preserves the gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The human branch must be byte-unchanged yet all output must route through the shared renderer, and those conflict. Which mechanism preserves the legacy lines? | `data["human_rendered"]`, demonstrated byte-exact at review. | Keeping a separate mode-guarded print path beside the renderer, rejected because it re-forks the color decision `plans_index.run_index`'s own comment records as a measured defect (`Term(color=not no_color)` forcing color on under `--agent`, `--json`, `NO_COLOR=1`, `TERM=dumb` and a pipe). Relaxing E-01's byte-identical assertion, rejected because it ships a silent user-visible change the plan promises not to make. | `renderers.HumanRenderer.render` returns `str(result.data["human_rendered"])` before building any banner; driven at review, a `CommandResult` carrying the key emitted exactly `INDEX.json: check.stale-index-stale: ...` and nothing else. | yes |
| D-2 | `escape_detail` is orphaned by the deletion. Unwind its 20 call sites, or keep it and record the redundancy? | Keep it untouched; correct its comment; file the redundancy as a backlog item. | Unwinding all 20 call sites in `attention.py`, `specs.py` and `cli.py`, rejected as a materially larger change than migrating three verbs and one with no behavioral gain. Deleting the helper, rejected because 20 live callers and a shipped test would break. Saying nothing, rejected because it leaves a comment citing a deleted symbol. | In `aw.agent/v1` the `detail` field is JSON-encoded, so the escaping is redundant rather than wrong; `grep -rn escape_detail` shows 20 call sites plus `tests/test_attention_contract.py::test_detail_escaping_keeps_one_line`. | yes |
| D-3 | Sibling `qgpanb` is `reviewed`, declares two of the same modules, and deliberately moves one of this plan's exit-parity bars. Sequence the two, or treat it as evidence guidance? | Evidence guidance: no dependency declared, exit parity measured against the executor's own baseline. | Adding `- Item-Dependencies:` on `qgpanb`, rejected because the two edit different functions (`check_drift` construction versus `run_index` emission) so neither needs the other, and an unnecessary edge delays both. | Read of `qgpanb`'s E-03/E-04 (they wrap `Drift` constructions in `check_drift`) against this plan's E-02/E-04 (they replace emission in `run_index`); AGENTS.md records that the runner isolates each item in its own worktree and revalidates on merge, so file overlap is not a hazard. | yes |
| D-4 | Is `docs/cli-output-contract.md` Section 10 made false by deleting `render_agent_drift`? | No; no finding raised, no edit made. | Adding a finding requiring Section 10 be amended, rejected. | Section 10 names the symbol HISTORICALLY, as the thing `aw.agent/v1` "SUBSUMES and REPLACES", so the text stays true after deletion; the plan is right that amending it would be the alternative fix it rejects. Its stale code offset (`artifact_core.py:247-266` versus the actual 672) is pre-existing and outside the declared paths. | yes |
| D-5 | E-08's note would announce a spec supersession. Has it already happened? | Already happened; the note records an existing supersession rather than causing one. | Letting the note claim this change supersedes a live constraint, rejected as a false history line on an implemented spec. | `aw attention --check --agent` already emits a conforming `aw.agent/v1` record and `grep` finds no `render_agent_drift` reference in `attention.py`, so attention stopped honoring spec `20260808-1945-01`'s reuse constraint when it was migrated. | yes |
| D-6 | The suite has a pre-existing failure. Fix it, or carry it? | Carry it; the plan forbids fixing it. | Fixing it inside this plan, rejected as an undeclared out-of-scope edit to another party's test in a shared checkout. | The failure is a hardcoded `2026-09-30` versus the current date in `tests/test_backlog.py`, touching no path this plan declares; AGENTS.md's shared-checkout rule against modifying work that is not yours. | yes |
