# Review findings: plan 3cs7qg

- Subject-Id: 3cs7qg
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree whose HEAD is `8b64b198`, with the plan's cited `61ef21d8`
confirmed an ancestor (`git merge-base --is-ancestor`). Structural preflight
`aw ipd lint --phase author --agent` returned exit 0 with one advisory (`IPD-Z602` density on E-02,
recorded as F-9 / PR-005 below). No pre-review snapshot was needed: `git status --short` was empty,
so the plan was committed and unmodified.

EVERY AUTHORED CLAIM REPRODUCED, AND I DROVE THE CODE RATHER THAN READING IT. Building a temporary
fixture repo and calling the shipped functions for each of `-`, `none`, `unresolved`, an unknown
`zz9zz9` and a real `bbb222`, I measured exactly the three-way disagreement the plan describes:
`releases.check_from_backlog` produced 1 `check.from-backlog-dangling` for each sentinel,
`runner_shared._read_from_backlog` returned `None` for each, and the `check_engine` readers indexed
the literal, with `_from_backlog_carrier_index` keying `['none']` and `build_graduation_reverse_index`
keying `('backlog', 'none')`. F-4 also holds: the sentinel grep returns nothing (exit 1) and
`python3 -m agent_workflows check release-gates --agent` reports `"findings":0`, exit 0. The plan's
`dc1e791c` provenance is accurate (`git show` confirms the `- From-Backlog: none` bullet was removed
from executed plan `mjx7ne`), and its decision to leave 6os96s alone is correct: that item needs a
cardinality ruling before either regex may change, and its only corpus instance is in `superseded/`.
OQ-01's resolution is also right and not merely convenient. `unresolved` belongs in the absent set
because `From-Backlog` is OPTIONAL, so an undecided value asserts no handoff; I confirmed the
readiness of undecided fields is policed elsewhere (`ipd_schema` refuses an `unresolved` Priority or
Work-Kind at the approval floor) and is not the dangling-link rule's job.

**THE PLAN COUNTED THREE READERS AND THERE ARE FOUR.** This is the finding that justifies the review.
`check_engine.check_from_spec_dangling` reads the sibling `- From-Spec:` field with the identical
defect: driven on a fixture, `-`, `none` and `unresolved` each produce one `check.from-spec-dangling`
finding while a real spec id6 produces none. This is not an adjacent nicety. That function's own
docstring states the design intent explicitly, calling itself "the SPEC-side sibling of
`releases.check_from_backlog`" and saying that "severity parity between the two carriers of one
handoff is the point", and AGENTS.md makes a spec "an equally valid gate carrier". So the two fields
are ONE contract with two carriers, and a sentinel-semantics change applied to one and not the other
ships the very inconsistency this plan exists to remove, in the field with the identical meaning. The
asymmetry would also be invisible for a while, because `check.from-spec-dangling` is reachable from
`aw check all` and NOT from the fail-closed `aw check plans` CI step (measured both ways), so it
would sit unreported until someone ran the full sweep.

**THE FLIP'S REAL OPERATIONAL COST IS NOT THE SENTINELS, AND THE PLAN DID NOT SAY IT.** The plan
treats the CI flip as safe because the family reports zero findings today. It does, and the flip is
still the right call, but `check.blocks-release-dangling` is a family member and
`releases.resolve_release` maps the literal `next` only when EXACTLY ONE release record carries
`Status: planned` (`return planned[0] if len(planned) == 1 else None`). I measured what that means on
a copy of `.aw/records`: baseline 0 findings; mark the single planned release `shipped` and the count
becomes 608 `check.blocks-release-dangling`; add a second planned record and it is 608 again; ship the
old one AND create its successor in the same change and it returns to 0. 608 records carry
`Blocks-Release: next` (331 backlog, 269 plans, 8 specs). So after the flip, a release cycle that
ships without creating the successor record reds `main` on 608 findings. That is arguably the gate
working (the tree genuinely is inconsistent in that state), which is why I did not weaken the flip;
what was wrong was landing it with the cost unstated, in a comment whose whole purpose is to tell a
future reader why the step is fail-closed.

A SECOND CONSEQUENCE OF THE FLIP BELONGS IN FRONT OF THE HUMAN, measured the same way: filing a live
bug with the documented `--blocks-release -` escape hatch produces exactly 1 `check.live-bug-ungated`
finding, which after the flip fails the merge. `backlog._default_blocks_release`'s own comment
defends that hatch ("A default is not a prohibition; an author may legitimately file an ungated
bug"), so the flip narrows a documented path. It is consistent with the "we do not ship known bugs"
policy and I did not flag it as a defect, but it is a policy consequence the approver should see
rather than discover, so it is now stated in the gate.

THE PLAN HAD NO REGRESSION GUARD, which is the quiet one. E-01..E-03 as authored made the readers
agree on the day of execution and obliged nothing thereafter: a fifth reader, or a fourth sentinel
added to the constant, would diverge silently and the next hand-written sentinel would red CI on live
data rather than a test. The `IPD-Z602` advisory on the authored E-02 was the same signal in
structural form (three readers, three call-site groups, one item). The added E-06 iterates the
frozenset itself rather than a literal list, so adding a member to the constant automatically obliges
every reader, and V-06 demands a mutation proving the guard bites instead of passing vacuously.

ONE V-ITEM'S EVIDENCE COMMAND COULD NOT HAVE DISTINGUISHED SUCCESS FROM FAILURE. The authored V-02
demanded `grep -n '"none"' ...releases.py ...runner_shared.py ...check_engine.py` show "no remaining
inline sentinel set". I ran it: it returns 8 hits, all but one legitimate and unrelated
(`PEER_NONE`, `AUDIT_BASIS_NONE`, an `outcome="none"`, a `grandfathered`/`none` check, prompt text).
An executor pasting that output would be pasting noise, and a reviewer reading it could not tell the
change had landed. The precise command, `grep -n '{"-", "none", "unresolved"}' agent_workflows/*.py`,
returns exactly one hit before the change and must return none after.

ON THE ONE NEW IMPORT, checked because it is the only structural risk in the change. `releases`
imports `ipd_schema` nowhere today, so E-02 adds an edge. I walked module-scope imports by AST: the
closure of `ipd_schema` is `{artifact_core, attention_contract, backlog, config, lifecycle_dirs,
plans, record_placement}` and does NOT contain `releases`, so there is no cycle (`backlog` reaches
`releases` only through function-local imports). Cost measured rather than assumed: a bare
`import agent_workflows.releases` is about 94ms best-of-9 against about 110ms with `ipd_schema`
alongside, so roughly 16ms, and on every CLI path that actually reaches `check_from_backlog`
(`check release-gates`, `releases list`) `ipd_schema` is ALREADY in `sys.modules`, so the real added
cost there is zero. A module-scope import is therefore fine and I did not require the local-import
dance.

THE HANDOFF CLOSE IS ALREADY LEGITIMATE, verified so the gate's final instruction is not a guess:
`check_engine.evaluate_blocking_close(repo, <7dcw6z path>, "done")` returns
`legitimate=True, path='HANDOFF'` with this plan as the sole carrier, so setting `7dcw6z` done after
execution preserves the gate as the plan says.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | A. correctness; C. architecture (one contract, two carriers) | `check_engine.check_from_spec_dangling` with `_ITEM_FROM_SPEC_RE`; driven on a fixture: `From-Spec: -`/`none`/`unresolved` -> 1 `check.from-spec-dangling` each, `sss111` -> 0 | **THERE IS A FOURTH READER AND THE PLAN MISSED IT.** `- From-Spec:` has the identical defect and, per its own docstring ("severity parity between the two carriers of one handoff is the point") and AGENTS.md ("an equally valid gate carrier"), the identical contract. Fixing only `From-Backlog` ships the same inconsistency in the twin field, and it would stay quiet: the rule is reachable from `aw check all` but NOT from the fail-closed `aw check plans` CI step. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-7 with its own item E-04 and V-04 (whose fixture must carry a spec `- Id:`, or the empty-known-set guard returns 0 for every case and proves nothing). The constant was renamed `SOURCE_LINK_ABSENT_SENTINELS` / `source_link_is_absent` so the shared name covers both fields; Concern, Scope, Goal and the ordered-changes list updated; a Project-conventions bullet records the one-contract-two-carriers rule. |
| PR-002 | MEDIUM | UNDER-SCOPE | C. operability; G. executability (an unstated consequence of the deliverable) | `releases.resolve_release`: `return planned[0] if len(planned) == 1 else None`; measured on a copy of `.aw/records`: 0 findings baseline, 608 `check.blocks-release-dangling` with the single planned release marked `shipped`, 608 with two planned records, 0 with ship-plus-successor; 608 records carry `Blocks-Release: next` (331 backlog / 269 plans / 8 specs) | **THE FLIP'S REAL COST IS THE RELEASE TRANSITION, NOT THE SENTINELS.** `check.blocks-release-dangling` is a family member and `next` resolves only when exactly one release record is `planned`, so after the flip a release cycle that ships without creating the successor record reds `main` on 608 findings. The plan justified the flip solely on "0 findings today" and named none of this. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | Not weakened (the state IS broken, so fail-closed is correct). Added as F-8; E-07 must name the state and the measured numbers in the CI comment and file a new gated backlog item for the fix; a Deferred row explains why the fix itself needs a maintainer decision (a release-cycle obligation versus a `next`-resolution change touching every gate reader) and must not be pre-empted here. The gate's "what a human is approving" now states it as a consequence being accepted. |
| PR-003 | MEDIUM | UNDER-SCOPE | D. anti-regression; E. testing | authored E-01..E-03 made the readers agree with nothing obliging a future reader; `aw ipd lint --phase author --detail` -> `advisory: IPD-Z602 (line 40): E-02: action text may bundle multiple concerns` | **NO REGRESSION GUARD: THE DIVERGENCE REGROWS SILENTLY.** The shared constant is only shared while every reader remembers to consult it, and the next reader or the next sentinel diverges with no test failing. The failure then surfaces as a red CI run on live records, which is exactly the class of surprise this plan exists to remove. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-9 and given its own item E-06: one test parameterized over the six public readers asserting each treats EVERY member of `ipd_schema.SOURCE_LINK_ABSENT_SENTINELS` as absent, ITERATING the frozenset rather than a literal list, so a new member automatically obliges every reader. V-06 demands a mutation (add a fourth member, touch no reader, watch it fail) because a guard that passes under that mutation has proved nothing. |
| PR-004 | MEDIUM | IN-SCOPE | E. testing (an evidence command that cannot fail) | ran the authored V-02 command: `grep -n '"none"' agent_workflows/releases.py agent_workflows/runner_shared.py agent_workflows/check_engine.py` -> 8 hits (`PEER_NONE`, `AUDIT_BASIS_NONE`, `outcome="none"`, a `grandfathered`/`none` check, prompt text, and the one real sentinel set) | **V-02's DEMANDED EVIDENCE COULD NOT DISTINGUISH SUCCESS FROM FAILURE.** The command returns 8 hits before the change and 7 after, nearly all unrelated. An executor would paste noise and a reviewer could not tell whether the inline set was gone, which makes the validation item decorative on precisely the item that proves the duplicate set was removed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now demands `grep -n '{"-", "none", "unresolved"}' agent_workflows/*.py` (exactly 1 hit before, 0 after, measured), states why the loose grep is forbidden, and additionally requires the fresh-interpreter import proof for the new `releases` -> `ipd_schema` edge. |
| PR-005 | LOW | IN-SCOPE | G. right-sizing and conceptual density | `aw ipd lint --phase author --detail` -> `IPD-Z602` on E-02; the item named three readers across three modules with five distinct `check_engine` call sites | **ONE E-ITEM CARRIED THREE MODULES AND FIVE CALL SITES.** The linter flagged it and the diagnostics agree with the rubric: the `check_engine` half introduces its own helper and rewrites five call sites, which is a different pass from two one-line edits elsewhere, and it needs its own V-item evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split: E-02 keeps the two simple readers (`releases`, `runner_shared`), E-03 takes the `check_engine` group. With E-04/E-06 added the checklist is E-01..E-08, `Highest E allocated` raised 05 -> 08, V-01..V-08 rewritten 1:1, and dependency edges and the ordered-changes list renumbered. Re-linted: `conforming`, advisory cleared. |
| PR-006 | LOW | UNDER-SCOPE | F. honest documentation (a doc line the change falsifies) | `AGENTS.md`: "In CI, `aw check release-gates` runs as a named advisory step in `tests.yml` until pre-existing baseline findings are resolved, and flips to fail-closed once clean."; the `<!-- /aw:block -->` marker precedes that section | **THE PLAN'S OWN E-07 MAKES A TRACKED AGENTS.md SENTENCE FALSE AND DECLARED NO DOC SYNC.** The spec-sync section read a bare "N/A". The sentence is in the repo-local `## Release gates` section below the managed-block marker, so correcting it touches no installer-managed text and is cheap. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section rewritten: it still amends no `.spec.md` (correctly, none defines these sentinels) and now names the one stale sentence, proves it sits outside the managed block, and requires the edit plus a `--scope-reason AGENTS.md=...` at finalize. Deliberately left out of `- Scope-Paths:` so the reconciliation records it explicitly. |
| PR-007 | LOW | IN-SCOPE | E. testing (a change that makes checkers report LESS) | authored E-03 had one negative case (`zz9zz9`) covering only `From-Backlog` | **A SUITE THAT MOSTLY ASSERTS SILENCE PASSES IF A READER IS BROKEN INTO TOTAL SILENCE.** Every sentinel assertion is an assertion that nothing is reported, so without a per-field negative control a reader accidentally neutered (an over-broad absent test, a swallowed exception) still passes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires TWO negative cases, one per field (`zz9zz9` -> exactly 1 `check.from-backlog-dangling`, and on the spec field exactly 1 `check.from-spec-dangling`), asserts the carrier and graduation indexes explicitly rather than only the dangling rule, and a Required-tests bullet records why the negatives are load-bearing. V-05 requires reverting EACH reader hunk separately and watching only its own cases go red. |
| PR-008 | LOW | IN-SCOPE | A. correctness (a live-artifact count cited as the bar) | plan cited `"findings":0` at HEAD `61ef21d8`; the lane HEAD is `8b64b198` with `61ef21d8` an ancestor; `.aw/records` is a shared tree any concurrent agent may add a gated item to | **THE GATING ZERO WAS MEASURED AT AUTHORING AND QUOTED AS A FACT.** A release-gate finding count is a live-artifact count over records other parties are editing, and the plan's stop condition depends on it. The authored E-04 did say to re-run, but the plan also presented the old HEAD's number as the state, and the repository's own convention puts an authoring measurement in prose as context and never as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now says to RE-DERIVE at the branch head and not to trust either number; the Findings preamble marks which rows were re-measured in review and which are the author's; a "RE-DERIVE, DO NOT TRUST, THE ZERO" clause was added to the gate. |
| PR-009 | LOW | IN-SCOPE | F. honest documentation (a convention stated more broadly than it holds) | `ipd_authoring.build_skeleton`: `if from_backlog: lines.append(f"- From-Backlog: {from_backlog}")` | **THE PLAN CITED THE SCAFFOLD'S `unresolved` SENTINEL AS IF THE SCAFFOLD WROTE IT ON THIS FIELD.** It writes `Item-Dependencies: unresolved` and `Work-Kind`/`Priority: unresolved`, but it emits `- From-Backlog:` only when a value is given, so it never writes `From-Backlog: unresolved`. The convention still justifies including `unresolved` in the set, but the mechanism matters: every sentinel this plan handles arrives by hand edit or an external writer, which is exactly why a code-level fix beats a data cleanup. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Project-conventions bullet now states the `if from_backlog` guard and draws the conclusion explicitly. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan fixes sentinel handling on `From-Backlog`. Is the sibling `From-Spec` reader in scope, or is adding it scope creep on an approved-shape plan? | IN SCOPE. E-04 fixes `check_from_spec_dangling` in the same change, and the shared constant is named for both fields. | (a) Fix `From-Backlog` only and file `From-Spec` as a new backlog item: rejected, because it ships a KNOWN inconsistency between two readers the codebase itself calls one contract, and the fix is a one-line guard in a function the plan is already reasoning about; a follow-up item would sit behind the same decision with nothing new to decide. (b) Fix `From-Spec` silently without recording it: rejected, it hides a scope widening the maintainer may disagree with. (c) Widen further to `Graduated-To`: rejected, that field is deliberately MULTI-valued with a whole-value regex and `parse_graduated_to`, so it has a different contract and is not affected. | `check_from_spec_dangling`'s docstring calls itself "the SPEC-side sibling of `releases.check_from_backlog`" and says "severity parity between the two carriers of one handoff is the point"; AGENTS.md calls a spec "an equally valid gate carrier"; driven measurement shows the identical three-sentinel defect; `check_types` includes the rule so `aw check all` reports it. | yes |
| D-2 | The CI flip makes 608 records dangle if the single planned release is shipped without a successor. Weaken the flip, block the plan, or land it with the cost stated? | LAND IT WITH THE COST STATED, plus a new gated backlog item for the underlying fragility. | (a) Make the step conditional (fail-closed only when clean), the shape plan `2vw35i` used: rejected, that shape existed because findings then existed and could not be fixed; the family is clean now, and a gate that disables itself when it would fire is not a gate. (b) Treat it as a BLOCKER and hold the plan: rejected, the 608-finding state is a genuinely broken tree, so the gate is behaving correctly; refusing the flip would keep a working gate off for a hazard that is a separate defect. (c) Fix `next` resolution here: rejected as out of scope and unsafe, it would change every `Blocks-Release` reader and needs a maintainer ruling. | Measured on a copy of `.aw/records`: 0 baseline, 608 on ship-only, 608 on two-planned, 0 on ship-plus-successor; `releases.resolve_release` returns None unless exactly one record is `planned`; no shipped code path marks a release `shipped` (`grep` finds no writer), so the transition is a human act that can be given an obligation. | yes |
| D-3 | Should the shared constant be named `FROM_BACKLOG_ABSENT_SENTINELS` as authored, or renamed now that `From-Spec` consults it? | RENAME to `SOURCE_LINK_ABSENT_SENTINELS` / `source_link_is_absent`. | (a) Keep the authored name: rejected, a `FROM_BACKLOG`-named constant read by the spec-side checker is the kind of misnaming a later maintainer "corrects" by forking a second set, which is precisely the divergence being removed. (b) Two constants, one per field: rejected outright, that IS the divergence. | The plan's own goal is one definition for one contract; `ipd_schema` already groups `META_FROM_BACKLOG` and `META_FROM_SPEC` as siblings in adjacent comments. The plan is unexecuted, so renaming costs nothing. | yes |
| D-4 | `AGENTS.md` carries a sentence the flip falsifies. Edit it here, or leave it to a docs pass? | EDIT IT HERE, as a justified out-of-fence change rather than a declared scope path. | (a) Leave it: rejected, it would leave the contributor-facing contract stating the step is advisory the moment it is not, and AGENTS.md is the file agents read to learn CI policy. (b) Add `AGENTS.md` to `- Scope-Paths:`: rejected deliberately, so the finalize reconciliation FORCES a recorded `--scope-reason` for a one-sentence edit to the repository's instruction file, which is the outcome I want over a silent in-fence edit. (c) A separate docs plan: rejected, one stale sentence created by this change belongs in this change. | The sentence sits in the repo-local `## Release gates (Blocks-Release)` section, below `<!-- /aw:block -->` (verified: the managed block ends before it), so no installer-managed text is touched and no target repo inherits it. `aw ipd finalize` refuses without a `--scope-reason` per out-of-scope path. | yes |
| D-5 | My own split of E-02 and the two added items changed the plan's shape from 5 items to 8. Is that a right-sizing improvement or reviewer inflation? | AN IMPROVEMENT, and recorded so it is checkable. | (a) Keep 5 items and fold `From-Spec` and the guard into existing ones: rejected, it would re-trip `IPD-Z602` (already firing on the authored E-02) and bundle a second module's five call sites with a one-line edit. (b) Add the items without recording the count change: rejected, a reviewer who restructures an author's checklist and does not say so has shipped an unreviewed judgement. | `aw ipd lint --phase author --detail` reported `IPD-Z602` on the authored E-02 and `conforming` with no advisory after the split; each new item names one deliverable in one module with one V-item, which is the rubric's right-sizing test. | yes |
| D-6 | The flip turns the documented `aw backlog new --blocks-release -` ungated-bug path into a CI failure. Is that a finding to fix, or a consequence to disclose? | A CONSEQUENCE TO DISCLOSE in the gate, not a finding. | (a) File it as a finding requiring the plan to preserve the hatch: rejected, that would mean weakening `check.live-bug-ungated`, which AGENTS.md mandates and a sibling plan built deliberately. (b) Say nothing: rejected, the approver would discover it from a red build on the next ungated bug, and it is a real narrowing of a path the code's own comment defends. | Measured: one deliberately ungated live bug yields exactly 1 `check.live-bug-ungated`, exit 1. `backlog._default_blocks_release`'s comment states "A default is not a prohibition; an author may legitimately file an ungated bug". AGENTS.md's "Every live bug gates the next release" makes the gating policy explicit, so the flip enforces stated policy. | yes |

### Deferred and open

- (none). All nine findings were FIXED in place. None reached Medium-High or High Remediation Risk, so
  the Fix Bar permitted no deferral. PR-002 is the closest call at Medium overall (security and
  functionality axes, because a red `main` at release time blocks shipping): it is FIXED as a
  disclosure-plus-carrier rather than by weakening the gate, and the underlying `next`-resolution
  fragility is carried to a new backlog item by E-07 rather than deferred inside this plan, because it
  needs a maintainer decision this plan must not pre-empt.
- No question required the human. The plan's one open question (OQ-01) was already resolved and I
  verified its reasoning against the shipped approval floor rather than accepting it. Every decision
  above rests on a measurement recorded with the command that produced it.
- No `Reversible: no` decision was made, so no escalation to a `- Blocking: yes` question was owed.
  D-1 through D-6 are all plan-text choices on an unexecuted plan, each undoable by editing the plan.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I verified the four readers'
CURRENT behavior by driving them, and I did not verify that the proposed `check_engine` refactor
(`_from_backlog_value` behind five call sites) preserves every caller's semantics; E-03 and V-03 are
written to make the executor prove that, but the proof is theirs. SECOND, my 608-finding measurement
used a COPY of `.aw/records` with the project config, not a full repo clone, so it exercised the check
functions rather than the CLI end to end; the direction and magnitude are sound but a real release
would want the number re-derived. THIRD, the sentinel census (0 records) is a live-artifact count on a
shared tree and was true when I ran it, which is exactly why E-07 re-derives rather than cites it.
FOURTH, I did not run the full suite: this is a plan review that changed no code, and E-08 owns that
obligation. FIFTH, I checked `Graduated-To` only far enough to establish it has a DIFFERENT contract
(multi-valued, whole-value regex, `parse_graduated_to`) and is therefore unaffected; I did not audit
its own sentinel handling, so if it has an analogous gap this review did not look for it.
