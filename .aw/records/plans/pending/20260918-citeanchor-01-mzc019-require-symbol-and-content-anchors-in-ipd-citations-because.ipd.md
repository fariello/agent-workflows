# IPD: Require symbol and content anchors in IPD citations, because a file:line reference expires silently and misdirects an executor to unrelated valid code

- Date: 2026-09-18
- Kind: child
- Concern: An IPD citation of the form `somefile.py:897-905` is true only at the instant it is written, and the plan pipeline is deliberately longer than that instant. A plan is authored, reviewed (often twice), approved, and then executed days later, while other agents commit to the same files concurrently in a shared checkout. By execution time the line numbers name different code.
  THE FAILURE IS SILENT MISDIRECTION, NOT A DANGLING POINTER, AND THAT IS THE WHOLE POINT. A drifted line number almost never points at nothing; it points at OTHER, VALID, PLAUSIBLE-LOOKING code. A dangling reference announces itself and costs an executor one grep. A drifted one does not announce itself, so the executor reads the wrong construct, believes the plan described it, and reasons from there. MEASURED on plan `216rgg` at HEAD `d445e6e6` while preparing to execute it: it cites the cross-type emission at `check_engine.py:897-905`, and what is actually at those lines today is the `seen_ids` dictionary initialization plus a comment about identity slots. The real emission (the branch whose message contains `different type`) is roughly 44 lines further down. Its other three anchors have drifted the same way, and its `doctor.py:530` citation now lands on a BLANK LINE.
  THE CORPUS IS SATURATED WITH THESE. MEASURED at the same HEAD: **96 of 101** pending plans (95%) carry file:line citations, **2816** of them in total, the densest single plan carrying 102. So this is a property of the authoring convention, not a lapse by one author.
  EVERY COUNT IN THIS PLAN IS A DATED SNAPSHOT OF A MOVING CORPUS, NOT A LIVE INVARIANT. RE-MEASURED at HEAD `8087387e` (after `216rgg` and `di08i9` executed and merged): **94 of 99** pending plans (94%), **2771** citations. The SHAPE is what must survive re-measurement, and it did: saturation stayed at roughly 95% while the absolute numbers moved within hours. An implementer must RE-DERIVE these and report the denominator rather than quoting this plan, which is the same discipline `2lcqno` Section 4 cost 4 imposes for the same reason.
  THE OBVIOUS METRIC UNDERSTATES THE PROBLEM AND MUST NOT BE USED AS THE MEASURE OF IT. Scanning the same 2816 citations for ones that are PROVABLY dead (the file no longer exists, or the line number exceeds the file's length) finds only **8**, which is 0%. That near-zero is not reassurance, it is the symptom restated: a line number stays syntactically valid while becoming semantically wrong, which is exactly why the corpus looks healthy and reads wrong. Any validation built for this defect must therefore key on the ANCHOR'S FORM, never on whether the target resolves.
  REVIEW CANNOT FIX THIS, WHICH IS WHY THE CONTRACT MUST CHANGE. `216rgg` was reviewed twice and its own history records that "every line number and count in this plan was MEASURED at HEAD rather than carried from the spec". That claim was TRUE when written. Verification cannot preserve a reference type that expires by construction, so more diligence is not the remedy and asking for it would be the wrong conclusion to draw.
- Scope: The IPD authoring contract's treatment of code citations, the scaffold guidance an author starts from, and a lint diagnostic that nudges new plans toward durable anchors. IN: stating the anchor rule in the IPD spec; emitting it in `aw ipd scaffold`'s `## Project conventions discovered (Step 0)` guidance so an author meets it before writing findings; adding ONE advisory `aw ipd lint` diagnostic at `info` that reports a bare file:line anchor in a plan being authored, with a `--legacy`-style exemption for plans predating the rule. OUT: retrofitting the 2816 existing citations (see Deferred, and note this is the single largest thing this plan deliberately does not do); any change to `check_engine`'s rules; any change to how REVIEWS cite code; forbidding line numbers outright.
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, tests/test_ipd_lint.py, .aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md
- Item-Dependencies: none
- Status: to-review
- Set: citeanchor
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: mzc019

## Workflow history

- 2026-09-18 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored at the maintainer's instruction ("we need to stop putting line numbers in plans"), after the drift was measured on `216rgg` while preparing to execute it. Every claim in this plan is anchored by SYMBOL or by CONTENT STRING rather than by line number, which is both the rule it proposes and the only honest way to state it. THE COUNTS TO RE-DERIVE, not to trust: 96/101 plans, 2816 citations, 8 provably dead, and `216rgg`'s four drifted anchors. The maintainer chose a plan over a backlog item.
- 2026-09-18 rebased onto `8087387e` (opencode/its_direct/pt3-claude-opus-5-1m-us): NO content revision, and the plan's own thesis gained a NATURAL EXPERIMENT worth recording. `216rgg` executed and merged in the interim, rewriting the exact region of `check_engine.py` this plan cites as its headline evidence. RESULT: all four symbol anchors used here (`ipd_lint._structural_lines`, `ipd_schema.H_PROJECT_CONVENTIONS`, `check_engine.CARRIER_CUTOVER_DATE`, `check_engine.carrier_severity_for_plan`) still resolve, and the `C_*` constant count is unchanged at 30, so nothing in this plan needed repair. Had those been line numbers they would now be as stale as the ones this plan was written to describe. Counts re-derived and annotated as snapshots (94/99, 2771); `aw ipd lint` still CONFORMING.
- 2026-09-18 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a code citation in a NEW IPD point at something that survives the gap between authoring and execution, by naming a symbol or a quoted content string instead of a line number, so an executor who follows a citation arrives at the construct the author meant rather than at whatever code now occupies that offset.

READ THE GOAL PRECISELY: this plan changes what a FUTURE plan is asked to write, and repairs NOTHING that already exists. It is a contract-and-nudge change, not a migration. The 2816 existing citations stay exactly as they are, and Deferred says why.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: state the rule

- [ ] E-01 STATE THE ANCHOR RULE IN THE IPD SPEC, in `.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md`, as a normative item covering how an IPD cites code. Require, in order of preference: (a) a SYMBOL path (`module.function`, `Class.method`, a `RuleSpec` row keyed by its rule id, a dict key); (b) a QUOTED CONTENT STRING unique enough to grep (for a branch with no symbol of its own, cite the message literal it emits, e.g. the branch whose message contains `different type`); (c) a line number ONLY as a trailing convenience appended to (a) or (b), never as the sole anchor. State the REASON in the spec and not merely the rule, because a rule whose reason is absent gets re-litigated: a symbol survives insertion, deletion, and file moves, while an offset survives none of them, and a drifted offset misdirects rather than failing.
  ALSO STATE THE ONE LEGITIMATE EXCEPTION so the rule is not read as absolute: a citation whose SUBJECT IS THE LINE ITSELF (a lint diagnostic's reported position, a traceback, a diff hunk quoted as evidence) is correctly a line number, because there the offset is the fact being reported rather than a pointer to a construct.
  - Depends on: none
  - Expected outcome: the spec carries the anchor rule, its rationale, its preference order, and the line-as-subject exception; the amendment is declared in this plan's `- Scope-Paths:` and announced by the runner per the spec-amendment contract.
  - Execution state: pending

### Task group 2: put it where an author will meet it

- [ ] E-02 EMIT THE RULE IN THE SCAFFOLD SO AN AUTHOR READS IT BEFORE WRITING FINDINGS, not after review. `aw ipd scaffold` writes the `## Project conventions discovered (Step 0)` section from `ipd_schema` (the heading constant is `H_PROJECT_CONVENTIONS`; the skeleton body is emitted by the scaffold writer in that module). Add a one-line convention to the emitted skeleton stating the anchor rule and pointing at the spec. KEEP IT TO ONE LINE: the scaffold's value is that it is read, and every line added to a skeleton lowers the odds the next one is.
  WHY THE SCAFFOLD AND NOT ONLY THE SPEC: an author who is writing a Findings table is not reading the IPD spec at that moment, and the measured 95% saturation shows the current default behavior is to reach for a line number. The scaffold is the surface that changes the default.
  - Depends on: E-01
  - Expected outcome: a freshly scaffolded IPD contains the anchor convention in its Step 0 section; `aw ipd lint` still reports the scaffold output conforming.
  - Execution state: pending

- [ ] E-03 ADD ONE ADVISORY LINT DIAGNOSTIC AT `info`, NOT AN ERROR, reporting a bare file:line anchor in a plan's prose. Allocate a fresh stable code in the existing namespace (the codes are declared as `C_*` module constants in `ipd_lint`, grouped by area with the id-family group using the `IPD-I3xx` block); do not reuse a retired code. The detector must key on a citation that carries a line number and NO accompanying symbol or quoted content string on the same bullet or table cell, because the defect is a MISSING durable anchor and not the presence of a number.
  IT MUST BE `info` AND MUST NOT GATE, for a reason this repository has already paid for twice: `check.setid-collision` shipped at `error` for behavior that was later ruled CORRECT, and `gjadwm` records that a gate which false-positives trains agents to bypass it. A citation-form heuristic will have false positives (prose that mentions a line number for a legitimate reason, a quoted traceback), so it must nudge and never refuse. Per `artifact_core.drift_exit_code`, an `info` finding does not drive a nonzero exit, which is the behavior wanted here.
  RESPECT THE EXISTING SCANNER'S FENCE HANDLING rather than re-implementing it: `ipd_lint._structural_lines` already returns only the lines OUTSIDE fenced code, indented code, YAML front matter, and block quotes, as `(1-based line number, line)` pairs, and its docstring names that as what structural checks see. A quoted traceback or a pasted diff inside a fence must not be flagged, and reusing that helper is what makes that true for free.
  - Depends on: E-01
  - Expected outcome: a plan citing `foo.py:123` with no symbol or content anchor draws one `info` diagnostic naming the new code; a plan citing a symbol, or a symbol plus a trailing line number, draws none; a line number inside a fenced block draws none; `aw ipd lint` exit status is UNCHANGED in every case.
  - Execution state: pending

- [ ] E-04 EXEMPT PLANS THAT PREDATE THE RULE, so the diagnostic reports on plans being authored and not on 96 plans nobody is touching. Gate the new diagnostic on the plan's own `- Date:` against a cutover constant, which is the pattern already used for this exact problem by the durable-carrier rule in `check_engine` (a module-level cutover date constant plus a per-artifact severity helper that downgrades a pre-cutover artifact). Set the cutover to this plan's execution date or later.
  WHY A DATE AND NOT A SWEEP: without the gate, the first run reports ~96 findings for work no author can act on, and a diagnostic that fires mostly on untouchable history is one every reader learns to skip, which destroys the value of the 1 finding that matters.
  - Depends on: E-03
  - Expected outcome: `aw ipd lint` over the current pending corpus reports ZERO new-code findings; the same lint over a synthetic post-cutover plan with a bare file:line anchor reports exactly one.
  - Execution state: pending

## Project conventions discovered (Step 0)

- CITATIONS IN THIS PLAN ARE DELIBERATELY SYMBOL-ANCHORED, INCLUDING THE ONES DESCRIBING THE DEFECT. Every location named here is a module, function, constant, heading constant, or quoted content string. That is not stylistic: a plan proposing this rule while citing line numbers would be self-refuting, and the drift it describes would have corrupted its own evidence before an executor read it.
- `ipd_lint` DECLARES STABLE RULE CODES AS `C_*` MODULE CONSTANTS, grouped by area (`IPD-P001` parse, `IPD-M1xx` metadata, `IPD-H2xx` headings, `IPD-I3xx` ids, `IPD-S4xx` states, `IPD-Q501` open questions, `IPD-Z6xx` size, `IPD-N001` name). A new diagnostic adds a constant to that block; codes are stable and are not recycled.
- THE LINTER ALREADY HAS FENCE-AWARE ITERATION in `ipd_lint._structural_lines`, plus a `Diagnostic` carrying a 1-based line and a `render` that formats `path:line:col code message`. A new textual rule reuses that helper; re-implementing fence detection is how a rule starts flagging pasted tracebacks.
- THE CUTOVER-DATE PATTERN FOR A NEW OBLIGATION ALREADY EXISTS in `check_engine`'s durable-carrier rule: a module-level compact `YYYYMMDD` constant, a legacy severity constant, and a per-artifact helper that returns the legacy severity for an artifact dated before the cutover. E-04 follows it rather than inventing a second mechanism.
- `artifact_core.drift_exit_code` EXEMPTS ONLY `info`. Anything else fails the gate. So severity choice IS the gating decision, and it lives in the rule's registration rather than in its message.
- NOTHING IN THE REPOSITORY CURRENTLY VALIDATES A CITATION. Grepping `ipd_lint` for `cite`/`citation` returns nothing, and the IPD spec is silent on anchor form. So this is a NEW obligation, not a tightening of an existing one, which is why it enters at `info`.
- ONE SHIPPED WORKFLOW ACTIVELY ASKS FOR `file:line`: the `assess` workflow instructs a reporter to give "`file:line` where known". That is a FINDINGS REPORT about a tree at a moment, not a plan to be executed later, so it is defensible and is deliberately out of scope here; but an implementer should read it before assuming the phrase should be purged repo-wide.

## Findings

| Id | Severity | Location (symbol / content anchor) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | plan `216rgg`, its `- Concern:` and E-01/E-02/E-04 bullets | Every core code anchor in an APPROVED, twice-reviewed plan has drifted before execution. Its cross-type citation now lands on `seen_ids` initialization and a comment; its `doctor.py` hardcode citation lands on a blank line. | The four cited anchors compared against the current `check_engine.check_collisions` and `doctor` sources at HEAD `d445e6e6` |
| F-2 | HIGH | `.aw/records/plans/pending/*.ipd.md` | The convention is corpus-wide, not local: 96 of 101 pending plans carry file:line citations, 2816 in total, densest single plan 102. RE-MEASURED at `8087387e`: 94 of 99, 2771 citations; the shape (~95% saturation) held while the absolute counts moved within hours, which is why the criteria are written in shape terms. | Regex scan of the pending tree at HEAD `d445e6e6`, re-run at `8087387e` |
| F-3 | HIGH | same corpus | THE INTUITIVE METRIC IS USELESS AND MISLEADING HERE. Only 8 of 2816 citations (0%) are provably dead. A line number stays syntactically valid while becoming semantically wrong, so a validator must key on anchor FORM, never on resolvability. | The same scan, checking file existence and line-count bounds |
| F-4 | HIGH | plan `216rgg` `## Workflow history` | REVIEW IS NOT THE REMEDY. Both reviews verified the citations and recorded that every line number was measured at HEAD. They were correct at the time; the references expired afterward. Diligence cannot preserve an expiring reference type. | The plan's own history entries |
| F-5 | MEDIUM | `ipd_lint` `C_*` constant block (30 constants); `ipd_schema.H_PROJECT_CONVENTIONS`; `ipd_lint._structural_lines` | The three surfaces a new rule needs already exist and are cheap to extend: a stable-code block, a scaffold-emitted conventions section, and a fence-aware line iterator. No new subsystem is required. | Source read; `C_*` constant count grepped |
| F-6 | MEDIUM | `check_engine.CARRIER_CUTOVER_DATE`, `_CARRIER_LEGACY_SEVERITY`, `carrier_severity_for_plan` | The legacy-exemption problem is SOLVED ALREADY in this repository, by a compact `YYYYMMDD` cutover constant plus a per-artifact helper returning the legacy severity for a pre-cutover artifact. E-04 should copy it rather than invent a second mechanism. | Source read |
| F-7 | LOW | `.aw/system/workflows/assess/assess.md` | A shipped workflow asks reporters for `file:line`. Defensible for a point-in-time findings report and deliberately out of scope, but it means "line numbers are always wrong" would be too strong a rule to state. | The workflow text |
| F-8 | INFO | `check.setid-collision` history; backlog `gjadwm` | PRECEDENT FOR ENTERING AT `info`: this repository has already shipped a rule at `error` that flagged correct behavior, and has recorded that a false-positive gate trains agents to bypass it. A heuristic about prose form must not gate. | D153; the `gjadwm` item |

## Proposed changes (ordered, validatable)

1. E-01 states the anchor rule, its rationale, its preference order, and the line-as-subject exception in the IPD structure-and-linting spec.
2. E-02 emits a one-line form of the rule in the scaffold's Step 0 section, so an author meets it before writing findings.
3. E-03 adds one `info` lint diagnostic for a bare file:line anchor, reusing the existing fence-aware iterator.
4. E-04 gates that diagnostic on a date cutover so it reports on new plans only.

## Deferred / out of scope (with reason)

- RETROFITTING THE 2816 EXISTING CITATIONS: deliberately NOT done, and this is the largest deferral in the plan. Rewriting anchors across 96 plans would touch other agents' in-flight and approved work in a shared checkout for cosmetic gain, would produce an enormous diff with no behavior change, and would risk corrupting the evidence in plans currently being executed. The correct posture for an existing plan is the one this conversation used successfully: treat a line number as a HINT, locate the construct by symbol or by grepping the quoted message, and proceed.
  - Carrier-Declined: Deliberately not carried. The deferral is permanent by design rather than pending: the existing citations are historical records that were true when written, and the contract change governs new plans only. There is no future state in which this sweep becomes correct, so filing a carrier for it would imply otherwise.
- FORBIDDING LINE NUMBERS OUTRIGHT: rejected. F-7 shows a legitimate use (a point-in-time findings report), and E-01 records a second (a citation whose subject IS the line). The rule requires a DURABLE anchor to be present, not the absence of a number.
  - Carrier-Declined: A rejected alternative, recorded so it is not re-proposed; there is nothing to carry.
- MAKING THE DIAGNOSTIC GATE (`warning` or `error`): deferred until the `info` rule has run long enough to measure its false-positive rate on real authored plans. Promoting it is a separate, evidence-bearing decision.
  - Carrier: mzc019
- HOW REVIEWS CITE CODE: a review is written and consumed within one sitting against a known HEAD, so its citations expire far less dangerously. Possibly worth the same treatment later; not evidenced yet.
  - Carrier-Declined: Speculative, with no measurement behind it. Filing a carrier would assert a defect this plan has not demonstrated.
- THE `assess` WORKFLOW'S `file:line` INSTRUCTION (F-7): out of scope, defensible as written.
  - Carrier-Declined: Judged correct as-is rather than deferred, so there is no work to hand off.

## Scope check

- Over-scope: none. Each declared path is touched by a named E-item: the IPD spec (E-01), `ipd_schema` (E-02), `ipd_lint` (E-03/E-04), and `tests/test_ipd_lint.py` (the pins for E-03/E-04).
- Under-scope: the spec amendment is DECLARED in `- Scope-Paths:` on purpose, per the plan-may-amend-a-spec contract, so both runners announce the declared spec edit before the run and reconcile it at finalize. An implementer who finds a second surface that must change (for example a second scaffold template) must declare it before editing rather than reconciling it afterward.

## Required tests / validation

`python3 -m pytest` bare. Do NOT add flags: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Establish the baseline IN THE EXECUTING WORKTREE and compare by failing NODE ID rather than by total, since the total moves with concurrent work.

Beyond the suite: `aw ipd lint` over the full pending corpus before and after, showing the count of the NEW code is zero both times (E-04's exemption) and that no plan's disposition changed; the same lint over a synthetic post-cutover plan showing exactly one `info` finding; a scaffolded plan showing the new convention line present and the scaffold still conforming; and the exit status of every `aw ipd lint` invocation above, proving the new rule never changes it.

## Spec / documentation sync

`.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` is DECLARED IN SCOPE and AMENDED by E-01, which adds the citation-anchor rule. This is an ADDITION to the authoring contract, not a reversal: nothing in the spec currently addresses anchor form, so no existing requirement changes meaning and no prior plan becomes retroactively non-conforming (E-04's cutover is what guarantees the second half of that claim).

WHY THE AMENDMENT BELONGS IN THIS CHANGE rather than a follow-up: the lint diagnostic and the scaffold line are both ENFORCEMENT of a rule that must first EXIST in the contract. Landing the nudge without the spec would leave a diagnostic citing no authority, which is the drift between code and contract that `216rgg` is separately having to close for `check.setid-collision`.

## Open questions

### OQ-01: Should the anchor rule also cover citations to NON-CODE artifacts (a spec section, a README paragraph)?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because every E-item here concerns code citations and none depends on the answer. It is worth asking because the same expiry applies in a weaker form: `2lcqno` Section 1 finding 4 is a durable anchor today, but a spec that gains a section renumbers. RECOMMENDATION: leave non-code citations alone for now. Section headings are already near-symbolic (they are titles, not offsets), so the failure mode is far milder, and widening the rule would add scope with no measurement behind it. Revisit only if a drifted spec-section citation is ever observed to mislead someone.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the spec diff showing the anchor rule, its stated RATIONALE (not just the rule), the (a)/(b)/(c) preference order, and the line-as-subject exception. Paste the runner's declared-spec-edit announcement for this run, or if run outside a runner, state that and paste the finalize scope reconciliation instead. Confirm the spec's `- Status:` and history were updated by a tooled verb rather than by hand.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: scaffold a throwaway IPD, paste its `## Project conventions discovered (Step 0)` section showing the new line, and paste `aw ipd lint` on that file reporting conforming. Paste the added line's source in `ipd_schema` and confirm it is ONE line. Delete the throwaway and show `git status --porcelain` clean of it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new `C_*` constant and its code, and confirm by grep that the code is not already used anywhere in `ipd_lint` or the tests. Paste FOUR lint runs over synthetic fixtures with their outputs: (a) a bare `foo.py:123` anchor -> exactly one finding with the new code; (b) a symbol anchor -> zero; (c) a symbol PLUS a trailing line number -> zero, proving the rule keys on a MISSING durable anchor and not on the digits; (d) `foo.py:123` inside a fenced block -> zero, proving the fence-aware iterator is reused. Paste the exit status of all four, all UNCHANGED from the no-rule baseline. Plus a MUTATION CHECK: break the "accompanied by a symbol" condition so case (b) or (c) starts firing, show the pin FAILS, restore, show it passes.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw ipd lint` over the ENTIRE pending corpus showing ZERO findings of the new code, and state the corpus size scanned so the zero has a denominator (order of 100 plans; RE-DERIVE it, do not quote this plan's number, which was 101 at authoring and 99 hours later). Paste the same lint over a synthetic plan dated AFTER the cutover with a bare anchor, showing exactly one. Paste the cutover constant and the date-comparison helper. Confirm no plan's overall disposition changed by comparing the before and after dispositions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 4 E-leaves in 2 groups. Small by design: the contract change plus a non-gating nudge, with the expensive option (retrofitting 2816 citations) deliberately excluded rather than deferred to a child.
- Cohesion rationale: E-01 is the authority the other three enforce, so landing them apart would leave either a rule nobody meets or a diagnostic citing nothing. E-03 and E-04 are one diagnostic and its exemption; shipping E-03 without E-04 fires ~96 findings on untouchable history and trains readers to ignore the rule on its first run.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change. Note `216rgg` is being executed by the maintainer against `check_engine.py` at the time of authoring; this plan does not touch that file.

Post-gate lifecycle: this plan is `to-review` and requires `/plan-review` followed by explicit human approval (`aw ipd set approved mzc019 --by-human --message ...`) before execution. On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
