# Review findings: plan ghna7l

- Subject-Id: ghna7l
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d5a41057` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified, byte-identical to its `.aw/state/lane-inputs/rev-7/` copy. No production
code was modified by this review; every measurement was taken by importing the shipped modules or by
driving the real CLI against a throwaway `git init` repo under `.aw/state/`, since removed, with
`git status --short` empty before and after.

**THE PLAN'S DIAGNOSIS IS CORRECT, ITS DESIGN IS THE RIGHT ONE, AND BOTH WERE RE-MEASURED RATHER
THAN ACCEPTED.** F-01 reproduces exactly: a scratch repo with one planned release and a live `bug`
carrying `- Blocks-Release: -` yields `check_live_bug_gate` -> `[]` and `check_blocks_release` ->
`[('check.blocks-release-dangling', "Blocks-Release '-' does not resolve to a release record")]`,
with `resolve_release(repo, '-')` returning `None`. So the exemption the shipped docs prescribe
genuinely is inexpressible. F-02's two-sided mechanism reads as described. F-03's staleness claim
holds on BOTH setter spellings, driven through the real CLI: the `--status` spelling wrote
`- 2026-09-28 set (aw backlog): RECORDED RATIONALE...` and the positional one wrote
`- 2026-09-29 same-status (aw set): RECORDED RATIONALE...`, each above a preserved `created` line, so
the plan is right to narrow itself and say so. F-04 holds: both predicates return 0 findings
repository-wide, `cnwy8g` is `done`, and the dash marker appears in no file. F-08 reproduces verbatim,
including the `recovery` string's "or file an explicit exemption if this bug genuinely does not gate
the release" and `rg Gate-Exempt` returning nothing tree-wide, which is the sharpest statement of the
defect. F-09 reproduces on all five regexes; F-10 on the enum and all three validator cases; F-11 on
both halves. E-02's four `backlog.gate-*` rule names, E-04's hoisted `set_blocks_release_line(rendered,
br)` shape, E-05's `status_set` neighbour write, OQ-03's two rule constructions, and E-08's cited
registry comment about the I-07 tension were each read and confirmed. The plan's honesty about being a
LATENT-defect repair that clears no existing finding is correct and unusually well stated.

**PR-A01 (HIGH): F-05's PRESERVATION PRECONDITION IS CONDITIONAL, AND THE CONDITION IS ABSENT ON THE
CREATION PATH E-04 MUST SERVE.** This is the one finding that could have cost an execution turn.
`_render_item(item, body, message=None, *, source_text=None)` has TWO branches. With `source_text`
supplied it walks the source bullets and preserves unrecognized keys in order, which is exactly what
F-05 measured and reported. With `source_text` OMITTED it emits a FIXED six-key list plus a hardcoded
`Gate-Kind`/`Gate-Ref` append for `blocked`, and every other bullet is DROPPED. Measured on one
fixture: both exempt bullets survive with `source_text=text` and neither appears without it. Of the
four callers, TWO omit it, and one of those is `backlog.run_new`, the creation path E-04's second
expected outcome depends on. The plan's chosen mechanism SURVIVES this, because E-04 already says to
apply line writers after the render exactly as `--blocks-release` is applied on the very next lines of
`run_new`; the danger is an executor reading E-01's "an unknown bullet already survives a round trip"
as licence to set the model slot and trust a pass-through that does not run there. Recorded as a
correction to a stated precondition plus a both-branches test fence, not a design change.

**PR-A02 (MEDIUM): `validate_item` TAKES `(path, text)`, SO E-02's AND V-02's PRESCRIBED PROBE SHAPE
DOES NOT RUN.** V-02 requires "a driven probe over FIVE fixture items printing the findings for each";
`validate_item(item)` raises `TypeError: validate_item() missing 1 required positional argument:
'text'`. The real signature is `(path: Path, text: str) -> List[core.Drift]`, so it re-parses
internally and each fixture must be written to a file first. Measured additionally: a correctly-shaped
call on an exempt-bullet fixture returns `[('backlog.set-missing', 'missing - Set: bullet')]`, so a
fixture lacking `- Set:` produces an unrelated finding that makes E-02's "clean" case read as a
failure.

**PR-A04 (MEDIUM): E-07 WOULD GRANT AN ESCAPE TO THREE ARTIFACT TYPES WHILE BUILDING THE FIELD FOR
ONE.** The `AGENTS.md` sentence E-07 amends reads "a backlog item, spec, or plan whose `- Work-Kind:`
is in the repository's gating set ... MUST carry `- Blocks-Release:` while it is LIVE". The exemption
is correctly backlog-only, since `check_live_bug_gate` iterates `backlog._iter_items`, and the
Deferred section says so accurately. But an unqualified "or record a typed exemption" appended to that
sentence would promise specs and plans a mechanism they lack. The population is real and the gap is
LATENT: 155 plans carry `- Work-Kind: bug`, 17 are live, and ZERO of those 17 are ungated; no spec
carries the kind. So nothing is wrongly flagged or permitted today, and the wording matters for the
first live plan-bug anyone de-gates.

**PR-A03 (LOW): THE BASELINE DRIFTED 138 TESTS WHILE STATED AS A BAR IN THREE PLACES.** F-06 records
`3069 passed, 2 skipped`; review's clean-tree run reads `3207 passed, 2 skipped, 3 warnings in
101.70s`. E-06's expected outcome ("at or above its F-06 baseline"), the Required tests bullet, and
V-08 all point at the stale figure. The comparison still passes trivially but tells the executor
nothing about their own contribution.

**PR-A05 (LOW): F-07's TWO OFFSETS DRIFTED, THOUGH ITS CONCLUSION HOLDS.** The `<!-- /aw:block -->`
marker is at line 125 (F-07 says 123) and the heading at 160 (says 158). The heading is still 35 lines
below the marker so E-07's authority to edit directly is unaffected, and `engine.py` still owns none
of that text. Worth one line because F-07 is the finding that licenses editing a file an installer
also writes, and because the plan's own Step-0 convention is to cite by anchor rather than offset.

**PR-A06 (MEDIUM): THE GATE CARRIED NO SCOPE FENCE.** It had the execution contract, the lifecycle
move, the what-a-human-approves paragraph, and an unusually good two-things-not-to-re-derive section,
but no declared fence for the runner to reconcile against. This plan has NINE declared paths, a tenth
pre-authorized by OQ-02, and five distinct prohibitions scattered across Deferred, the Scope check and
the gate prose, none collected where an executor looks.

**WHAT REVIEW CHECKED AND FOUND SOUND.** The typed-pair design choice (OQ-01) is well argued and its
reasoning was verified: both candidate shapes exist here for different jobs, and the shipped validator
accepts exactly the two ref shapes a real exemption needs. OQ-02's make-then-justify resolution is the
documented mechanism and both routes genuinely produce the same observable behavior. OQ-03 was
verified from both rules' construction, not their names: `item_gate` is populated only for items that
HAVE a gate (so an exempt item is absent from the map), and `check.orphaned-live-blocker` is
`warning`/heuristic and subject-bounded to blockers. The E-04/E-05 split along the two dispatch paths
is correct and is backed by an in-tree docstring warning about exactly that inconsistency. E-03's
refusal to honor a malformed pair, and its stated reason (not becoming a fourth
`SCOPE_PATHS_GRANDFATHERED`), is the right call and is correctly surfaced to the human as the one
judgement to override. E-06's two-rule assertion is the test that distinguishes this fix from the
broken dash marker and is genuinely load-bearing. E-08 is correctly identified as a declared spec
amendment, the `.spec.md` path is in `- Scope-Paths:`, the spec is `draft` so no approved contract
moves, and the in-code comment it cites says verbatim that widening the catalog wording is a spec edit.

Every finding is FIXED by in-place revision. None was deferred, so no escalation to a
`- Blocking: yes` question is owed and none was written. OQ-01, OQ-02 and OQ-03 all survive review
unchanged and are UPHELD on re-measured evidence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | `_render_item`'s signature and its `if source_text is None:` branch emitting a fixed `Id`/`Status`/`Set`/`Priority`/`Work-Kind`/`Summary` list plus a `blocked`-only `Gate-Kind`/`Gate-Ref` append; two probes on one fixture printing both exempt bullets preserved with `source_text=text` and ABSENT without it; `rg -n "_render_item\(" agent_workflows/*.py` -> 4 callers with `backlog.py:1010` (`run_new`) and `set_records.py:344` omitting the argument | F-05's PRESERVATION PRECONDITION IS CONDITIONAL AND THE CONDITION IS ABSENT ON THE CREATION PATH. E-01 tells the executor an unknown bullet "already survives a `_render_item` round trip today, so this item adds parsing, not preservation". That is true only on the `source_text` branch. `backlog.run_new` omits it, so a pair carried only on the model slot would silently vanish from a newly created item, defeating E-04's second expected outcome with no test failure if the fence covers only the other branch. | C:Low; U:Low; S:Low; F:Low; Overall:Low (the plan's mechanism already works; this corrects a stated precondition and adds one test assertion) | FIXED | Added F-12 with both branches, the four callers, and which two omit the argument. E-01 gained a paragraph stating the condition, naming the two omitting callers, explaining that E-04's post-render line writer is what makes the creation path work, and forbidding the tempting alternative of adding the pair to the template branch's fixed key list. E-01's expected outcome now specifies `source_text=` explicitly. E-06's regression fence must now pin BOTH branches. V-01 requires pasting the omitted-argument render showing the bullets ABSENT. A Step-0 conventions bullet carries the general rule. |
| PR-A02 | MEDIUM | IN-SCOPE | E. Testing / G. Plan executability | `inspect.signature(backlog.validate_item)` -> `(path: 'Path', text: 'str') -> 'List[core.Drift]'`; the `TypeError` raised by an item-shaped call; a correctly-shaped call returning `[('backlog.set-missing', 'missing - Set: bullet')]` on an exempt fixture | E-02's AND V-02's PRESCRIBED PROBE SHAPE DOES NOT RUN. `validate_item` takes a path and the file text, not a parsed item, so every fixture must be written to a file; an item-shaped call raises `TypeError`. Additionally a fixture lacking `- Set:` produces an unrelated `backlog.set-missing` finding, which would make E-02's required "clean" case read as a failure and send an executor debugging their own new rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 with the signature, the `TypeError`, and the `set-missing` interference. E-02 gained a note stating the real signature and requiring the new rule names be registered alongside the existing `backlog.gate-*` ones. E-02's expected outcome now says "NOTHING NEW" and requires a `- Set:` bullet on every fixture. V-02 carries both corrections. A Step-0 conventions bullet records it. |
| PR-A04 | MEDIUM | IN-SCOPE | A. Correctness (documentation honesty) / F. Principles | the quoted `AGENTS.md` MUST clause governing "a backlog item, spec, or plan"; `check_live_bug_gate`'s `for f in _backlog._iter_items(repo_root):`; a census printing `plans: Work-Kind bug=155 live=17 live-and-ungated=0` and `specs: Work-Kind bug=0` | E-07 WOULD ADD AN EXEMPTION ESCAPE TO A MUST CLAUSE GOVERNING THREE ARTIFACT TYPES WHILE THE FIELD SERVES ONE. The exemption is correctly backlog-only, but an unqualified escape clause in that sentence would promise specs and plans a mechanism they do not have. The gap is LATENT rather than active (zero live ungated plan- or spec-bugs today), so this is a wording obligation, not a code one, and it would become a false statement the first time a live plan-bug were de-gated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 with the clause, the checker's iteration domain, and the census. E-07 gained a paragraph requiring the escape be scoped to backlog items explicitly and requiring the plan state that a spec or plan has no exemption field today, with the latency measured rather than implied. V-07 now FAILS if the amended sentence reads as granting all three types an exemption. The Deferred row quantifies the boundary. |
| PR-A06 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | the gate section as authored, carrying the execution contract, lifecycle move, approval summary and a two-things-not-to-re-derive section, but no declared fence; the nine `- Scope-Paths:` entries; five prohibitions spread across Deferred, Scope check and gate prose | THE GATE CARRIED NO SCOPE FENCE. The runner needs a declaration to reconcile the actual diff against, and this plan is unusually fence-hungry: nine declared paths, a tenth (`releases.py`) pre-authorized by OQ-02 via `--scope-reason`, and five distinct prohibitions (do not make the dash resolve, do not honor a malformed pair, do not touch `engine.py`, do not route through `evaluate_blocking_close`, do not change any existing item's gate state) none of which was collected where an executor looks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE naming all nine paths, the pre-authorized tenth with its `--scope-reason` route, and all five negative constraints with their reasons, written as a DECLARATION with no "STOP and report" clause per the 2026-09-01 maintainer ruling. |
| PR-A03 | LOW | IN-SCOPE | G. Plan executability (live-artifact convention) | review's clean-tree `python3 -m pytest` -> `3207 passed, 2 skipped, 3 warnings in 101.70s` at HEAD `d5a41057`, against F-06's `3069 passed, 2 skipped` at `6669140f` | THE SUITE BASELINE DRIFTED BY 138 TESTS AND IS STATED AS A BAR IN THREE PLACES (E-06's expected outcome, the Required tests bullet, and V-08). The comparison passes trivially but cannot separate the executor's contribution from unrelated work, which is what the live-artifact convention exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14 with both measurements. The Required tests bullet now carries both figures labelled context, states the 138-test drift, and requires the executor's own baseline. E-06's expected outcome and V-08 both rewritten to demand a delta against that own baseline. |
| PR-A05 | LOW | IN-SCOPE | A. Correctness (evidence accuracy) | `rg -n 'aw:block\|Every live bug gates' AGENTS.md` -> marker at 125, heading at 160 (F-07 says 123 and 158); both `engine.py` searches still empty; `rg -n 'inherits the item' agent_workflows/engine.py` -> one hit | F-07's TWO LINE OFFSETS HAVE DRIFTED though its conclusion holds. The heading remains 35 lines below the managed marker, so E-07's authority to edit `AGENTS.md` directly is unaffected. Recorded because F-07 is the finding that licenses editing a file an installer also writes, and because the plan's own Step-0 convention is to cite by anchor rather than bare offset. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-17 with the current offsets and the unchanged conclusion. E-07 gained an instruction to locate both edit points by HEADING rather than by number. V-07 now requires the offsets be RE-DERIVED at execution time rather than transcribed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `_render_item`'s unknown-key pass-through does not run on the creation path. Does this invalidate E-01/E-04's approach, or is it a precondition correction? | A PRECONDITION CORRECTION plus a both-branches test fence. The design stands. | (a) Redesign E-04 to set the model slot and add the pair to the template branch's fixed key list - rejected: that re-emits the field FROM the template, which is precisely what keeping both names out of `_TEMPLATE_OWNED_KEYS` is meant to prevent, and it would make the creation path and the update path disagree about who owns the line. (b) Pass `source_text` into `run_new`'s render - rejected: on creation there IS no source text (the file does not exist yet), so the argument has nothing to carry. (c) Say nothing, since E-04's post-render writer already works - rejected: E-01 states the precondition as unconditional, and an executor trusting it would set the slot and ship a silently broken creation path with a green test. | `_render_item`'s two branches read directly; two probes on one fixture showing preservation with and without `source_text`; the four call sites with two omitting it; `backlog.py`'s existing `set_blocks_release_line(rendered, br)` immediately after `run_new`'s render, which is the working precedent E-04 already copies. | yes |
| D-2 | E-07 amends a MUST clause covering backlog items, specs and plans, but the field is backlog-only. Scope the escape clause, or widen the field to all three? | SCOPE THE CLAUSE to backlog items and state that specs and plans have no exemption field. | (a) Widen the field to specs and plans in this plan - rejected: `check_live_bug_gate` iterates `backlog._iter_items` only, so the field would have no reader on those trees, which the plan's Deferred section already identifies correctly as "a field with no reader". (b) Leave the clause unqualified - rejected: it would document a mechanism that does not exist for two of the three types it names, which is the same class of defect as F-08's recovery text advertising a route the tool lacks, i.e. the very thing this plan exists to fix. (c) Narrow the MUST clause itself to backlog items - rejected: that would silently weaken a maintainer's 2026-09-11 ruling about which artifacts must carry the gate, which is far outside this plan's mandate. | The quoted `AGENTS.md` sentence; `check_live_bug_gate`'s iteration domain; the census (155 plan-bugs, 17 live, 0 live-and-ungated; 0 spec-bugs) establishing the gap is latent so no code change is owed today. | yes |
| D-3 | OQ-02 leaves the line writers' home to execution, with `releases.py` undeclared. Accept that, or require the path be declared now? | ACCEPT IT, and name `releases.py` in the new scope fence as a pre-authorized tenth path with its `--scope-reason` route. | (a) Add `releases.py` to `- Scope-Paths:` now - rejected: the plan's own reasoning is sound that it should not assert an edit to a shared file it may not need, and AGENTS.md prescribes make-then-justify for exactly this case. (b) Require the writers go in `backlog.py` to keep the fence closed - rejected: it would fork the `releases.py` line-writer family, which review confirmed is a deliberate six-member group (`set_blocks_release_line`, `set_priority_line`, `set_work_kind_line`, `set_from_backlog_line`, `set_item_dependencies_line`, `set_graduated_to_line`) sharing one insertion-anchor contract. (c) Leave the fence silent about it - rejected: a reviewer adding a fence must name the one path most likely to be touched undeclared, or the fence misleads the runner's reconciliation. | The six `set_*_line` definitions in `releases.py`; OQ-02's own reasoning; AGENTS.md's finalize scope gate requiring a `--scope-reason` per out-of-scope path, which makes either route auditable. | yes |
| D-4 | PR-A01 is HIGH. Does it make this plan NO-GO, or is escalation to a blocking question owed? | NEITHER. It was FIXED by in-place revision, so no unfixed HIGH remains and the readiness is `go-pending-approval`. | (a) NO-GO on the HIGH - rejected: severity is for reporting and the Fix Bar alone decides fixing; this fix is Low Remediation Risk on all four axes, correcting a prose precondition and adding one test assertion, and the plan's actual mechanism was already correct. (b) Escalate as `- Blocking: yes` - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the gate threshold, and this one is FIXED. (c) REPLAN - rejected: the design is right, the defect is measured, and the typed-pair choice is well grounded in two in-tree precedents. | The `plan-review` Fix Bar and readiness vocabulary; `aw ipd lint --phase review-finalize --agent` conforming after revision; `review_findings_gate` absent from `.aw/config/project.json` so the default `HIGH` threshold applies and nothing sits unfixed at it. | yes |
| D-5 | The plan says executing it clears no existing finding (F-04). Does that make it low value, or should review challenge the priority? | UPHOLD IT AS AUTHORED, and do not challenge. | (a) Recommend deferring the plan as low value since no finding moves - rejected: the defect is that `check_live_bug_gate` emits a `recovery` instructing an operator to file an exemption the tool cannot express, which review reproduced verbatim; a checker that prescribes an impossible fix at ERROR severity trains people to ignore it, and that cost is paid on every future de-gate rather than today. (b) Ask the maintainer to re-prioritize - rejected: priority is the maintainer's call and they already set `medium` on the source item, and the repository answers the value question through the recovery text itself. | F-08's recovery string read at its `enrich_drift(...)` call; `rg Gate-Exempt` returning nothing tree-wide; the source item `b0dcyp`'s own "WHY IT MATTERS" paragraph; F-04's zero-finding measurement, which the plan volunteers rather than hides. | yes |
