# IPD: Require a durable carrier for an unfixed defect an IPD names before it may reach executed

- Date: 2026-09-07
- Kind: child
- Concern: In the maintainer's words (2026-09-05): "A note in an executed IPD is 100% guaranteed to be the same as not writing it anywhere." That is literally true. Once a plan reaches `executed`, `aw attention` classes it `done`, so every unfixed defect named in its prose disappears from every "what needs attention" view, permanently, silently, with no record that anything was dropped. Walkthroughs are worse: they are `tracked=False` by design and get filename-only checking, so a walkthrough may describe any number of live defects and no tool will ever read a word of it.
  TWO REQUIRED IPD MECHANISMS ARE DEAD CODE, both verified at HEAD. (1) `## Deferred / out of scope (with reason)` is MANDATORY in both `CHILD_H2_ORDER` and `ORCHESTRATOR_H2_ORDER` (`ipd_schema.py:48` declares `H_DEFERRED`), and `H_DEFERRED` appears ZERO times in `ipd_lint.py` (`grep -c` = 0). The lint enforces that the section exists and is ordered, and never reads its contents, so every "deferred to its own IPD" row in the entire corpus is unverified prose. (2) The blocking-open-question gate runs at `pre-execution` ONLY, never at `pre-transition`, so a blocking question gates the START of work and not the CLAIM THAT IT IS DONE. And an OQ is "resolved" by any non-empty prose: `open_question_error` (`ipd_schema.py:1338-1354`) checks only that a rationale is non-empty, with its own docstring stating "Semantics are the reviewer's job". `ipd_lint.py` contains ZERO occurrences of `From-Backlog` (`grep -c` = 0): the linter has no concept of backlog linkage at all.
  THE PATTERN TO GENERALIZE ALREADY EXISTS AND WORKS. `evaluate_blocking_close` (`check_engine.py:1951`, verdict type `CloseVerdict` at `:1934`) is the only mechanism here that enforces "an obligation must survive in a place that is revisited": closing a backlog item carrying `Blocks-Release:` FAILS CLOSED unless (1) HANDOFF to a plan carrying `From-Backlog:` and the same gate, (2) SATISFIED with a resolvable citation, or (3) DE-GATED explicitly. One shared predicate backs the setter, the `aw check` rules, and an opt-in hook, "so they cannot diverge". This plan applies that exact shape to an IPD's terminal transition.
- Scope: Add ONE shared predicate that refuses an IPD's transition to `executed` while it names an unfixed defect with no durable carrier, with the same three escapes `evaluate_blocking_close` already uses (handoff, satisfied, declined-with-reason). Wire it into `aw ipd lint --phase pre-transition` and `aw check` from that single predicate. Read TYPED fields only, never prose. Ship warning-for-existing / error-for-new so a 530-plan corpus is not mass-failed on day one.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, tests/test_durable_capture.py
- Item-Dependencies: executed:b7xarm
- Status: to-review
- Set: durablecapture
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: rnkqrc
- From-Backlog: jys5dp
- Blocks-Release: next

## Workflow history
- 2026-09-09 to-review (aw set): MAINTAINER RULING 2026-09-08 (recorded as OQ-04): the runner CANNOT detect an unfixed defect, and this plan never could; it is a DECLARATION gate whose predicate only checks that a typed field exists, resolves, and points somewhere non-terminal. The maintainer challenged the premise directly and ruled that the declaration must be PRODUCED before the check that verifies it is built: an execute turn must report found bugs/gaps/concerns both affirmatively and negatively in a parsable form, and the runner must ask the agent (in the same session) when neither statement exists. Plan b7xarm (defreport-01) was authored to produce exactly that report, so this edge is a real prerequisite rather than a preference: executed before b7xarm, this gate ships with nothing to verify (F-6 already measures the day-one effect, 530 plans and ZERO carrying the field). E-02's predicate should additionally read the NORMALIZED report b7xarm E-06 persists on the run record, since that record is what distinguishes 'found nothing' from 'never asked'. ALSO RESOLVED in the same ruling (OQ-01): the accepted carrier set is a backlog item or a pending plan ONLY; a spec is never sufficient and is supporting material, with no just-a-spec judgement delegated to the agent.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `jys5dp`. Every dead-code claim re-verified by running the greps rather than trusting the item: `H_DEFERRED` in `ipd_lint.py` = 0, `From-Backlog` in `ipd_lint.py` = 0, and `open_question_error`'s rationale check is indeed non-emptiness only (`ipd_schema.py:1338-1354`). The corpus size was re-counted at 530 plans (the item said ~484), which strengthens rather than weakens the rollout caution, so the staged severity is carried into E-05 as a hard requirement rather than advice.

## Goal

An unfixed defect an IPD names cannot vanish when that IPD reaches `executed`: it must first be handed to a carrier something revisits, satisfied with cited evidence, or explicitly declined with a reason.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: define the carrier reference

- [ ] E-01 ADD A TYPED CARRIER FIELD TO THE OQ AND DEFERRED VOCABULARY in `ipd_schema.py`, so a carrier reference is matched STRUCTURALLY and never by prose. Follow the `Finding` precedent exactly: `Finding` was added to `OQ_FIELDS` (`ipd_schema.py:1329-1335`) as the typed field `check.review-finding-unescalated` matches, with the schema comment recording WHY prose matching was rejected ("a substring search over prose would be spoofable by any incidental mention and brittle against rewording").
  NOTE `OQ_FIELDS` IS CURRENTLY UNREAD, and the schema says so in as many words (`:1315-1318`: it "has NO consumer anywhere in the codebase (it is defined here and never read)", the parser is "deliberately OPEN-ENDED and carries any subfield into the parsed dict"). So adding a field there is necessary but NOT sufficient: this plan's predicate is what finally gives it a consumer. Also honor the standing warning at `:1327-1328`: if `OQ_FIELDS` ever becomes a CLOSED allowlist, both `Finding` and this new field must stay in it.
  DEFINE THE FIELD FOR THE DEFERRED SECTION TOO, since that section is the higher-value half (every "deferred to its own IPD" row in the corpus is currently unverified prose). One vocabulary serving both places, not two.
  - Depends on: none
  - Expected outcome: one typed carrier field declared in the schema, usable in an OQ block and in a `## Deferred / out of scope` row, with the anti-prose rationale recorded next to the `Finding` precedent.
  - Execution state: pending

### Task group 2: one predicate, three escapes

- [ ] E-02 WRITE THE SHARED PREDICATE in `check_engine.py`, MIRRORING `evaluate_blocking_close` (`:1951`) rather than inventing a second shape. Return a verdict type in the shape of `CloseVerdict` (`:1934`) so callers get a structured answer, not a boolean. The three escapes must be exactly the proven ones:
  (1) HANDOFF - the named carrier resolves to a `backlog/open/` item or a plan NOT in a terminal directory (i.e. something `aw attention` actually revisits);
  (2) SATISFIED - a resolvable in-tree evidence citation, the same shape `aw backlog set done --evidence` already accepts;
  (3) DECLINED - an explicit recorded decision with a reason, which is the `--blocks-release -` analogue.
  RESOLVE THE CARRIER, DO NOT MERELY PARSE IT. A dangling id6 must FAIL, exactly as `check.from-backlog-dangling` already fails a `From-Backlog` pointing at nothing. A carrier reference that resolves to a plan in `executed/` is NOT a valid handoff, because that is the very hiding place this plan exists to close; assert that case explicitly.
  NEVER RAISE. Follow the parse-then-diagnose split the sibling evaluators use: a malformed row becomes a finding and surrounding good rows still parse. A gate that crashes on bad input is a gate that gets disabled.
  - Depends on: E-01
  - Expected outcome: one predicate returning a structured verdict, with three escapes, resolving carriers against the real trees, refusing a terminal-directory carrier, and never raising.
  - Execution state: pending

- [ ] E-03 WIRE `pre-transition` TO THE PREDICATE in `ipd_lint.py`, which is the gate that currently cannot see any of this. The blocking-OQ check runs at `pre-execution` only and `pre-transition` checks solely E-item state, V-item results, and evidence presence, so "is this claim of doneness honest about what it leaves behind?" is asked nowhere. Add the predicate's verdict to the `pre-transition` phase.
  DO NOT MOVE OR WIDEN THE EXISTING `pre-execution` BLOCKING-OQ CHECK. Its exclusion from `pre-transition` is deliberate and documented; this item ADDS a different question at that phase rather than relocating an existing one. Two gates, two questions.
  - Depends on: E-02
  - Expected outcome: `aw ipd lint --phase pre-transition` reports the new rule; the `pre-execution` blocking-OQ behavior is byte-identical to before.
  - Execution state: pending

- [ ] E-04 WIRE `aw check` TO THE SAME PREDICATE, with a rule id registered in `RULE_REGISTRY`, so the sweep and the checkpoint cannot drift apart. That single-predicate property is stated as the design intent of the nearest precedent (`evaluate_review_finding_escalation`, `check_engine.py:3116`, whose docstring calls itself "The ONE evaluator ... shared by both host surfaces"), and this plan must not weaken it.
  CI ALREADY ENFORCES `aw check plans` FAIL-CLOSED, so a new plans rule inherits enforcement with no workflow edit. Note that `check backlog` is ADVISORY there; do NOT change that as a side effect of this plan, and say so in the report if it seems tempting.
  - Depends on: E-03
  - Expected outcome: one rule id in `RULE_REGISTRY` backed by the SAME predicate `pre-transition` calls; `aw check` and `aw ipd lint` provably cannot disagree.
  - Execution state: pending

### Task group 3: roll it out without mass-failing 530 plans

- [ ] E-05 SHIP STAGED SEVERITY: `warning` for existing plans, `error` for newly authored ones. THIS IS MANDATORY, NOT A PREFERENCE. When zero existing artifacts satisfy a new requirement, a fail-closed rule blocks everything on day one; `check.review-finding-unescalated` chose SILENCE on an absent artifact for exactly this reason, recording that "zero .review.md files exist against 428 plan files, so a fail-closed absent case would mass-fail the entire corpus on day one". Re-counted at authoring: 530 plans exist now, and zero carry a typed carrier field.
  GATE ON A DATE OR FORMAT-VERSION BOUNDARY, mirroring how `check.ipd-missing-dependency-statement` is cutover-gated by `config.dependency_cutover_date` so an ABSENT marker grandfathers every existing plan. Reuse that mechanism if it fits rather than inventing a second boundary.
  PROVE THE BLAST RADIUS BEFORE AND AFTER. Run `aw check` over the whole corpus and report the finding count at each severity. A rule that turns 530 plans red is not shippable no matter how correct it is.
  - Depends on: E-04
  - Expected outcome: existing plans WARN, new plans ERROR, the boundary is an existing configurable mechanism rather than a new one, and the measured corpus-wide finding count is reported.
  - Execution state: pending

- [ ] E-06 TEST THE THREE ESCAPES, THE REFUSAL, AND THE ROLLOUT in a new `tests/test_durable_capture.py`. Cover: a plan naming an unfixed defect with NO carrier (refused at `pre-transition`); each of the three escapes accepted; a DANGLING carrier refused; a carrier resolving into `executed/` refused (the hiding place); a malformed row producing a finding rather than an exception; and the staged severity (an old plan warns, a new one errors).
  ASSERT `aw check` AND `pre-transition` AGREE, from the same fixtures, since a single predicate is the design property most likely to erode later. Assert both surfaces on the same inputs rather than testing one and trusting the other.
  ASSERT PROSE DOES NOT SATISFY THE RULE: a plan whose deferred row says "tracked in the backlog" with no typed field must still be refused. That is the spoofability `Finding` was designed against, and it is the most likely way this gate gets quietly defeated.
  - Depends on: E-05
  - Expected outcome: a test failing against pre-change HEAD, passing after, covering three escapes, four refusal cases, the malformed case, staged severity, and cross-surface agreement.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `evaluate_blocking_close` (`check_engine.py:1951`) + `CloseVerdict` (`:1934`) is the proven "obligation must survive" shape, backed by one predicate serving the setter, the `aw check` rules, and an opt-in hook.
- `evaluate_review_finding_escalation` (`check_engine.py:3116`) is the nearest precedent for a lint+check shared evaluator, and its own comment concedes the adjacent weakness this plan closes: it escalates a finding into an OQ INSIDE the same plan, so once that plan is `executed` the OQ is frozen in a terminal artifact.
- TYPED FIELDS ONLY. The `Finding` field exists precisely because prose matching is "spoofable by any incidental mention and brittle against rewording" (`ipd_schema.py:1321-1323`).
- `OQ_FIELDS` is currently declared and never read (`ipd_schema.py:1315`), and the OQ parser is deliberately open-ended, so a new subfield parses today and simply has no consumer until this plan adds one.
- Severity vocabulary must be SHARED, not forked (see `review_findings.is_gating`).
- The suite runs BARE. Shared checkout: run `aw runs` first; `check_engine.py` is large and widely imported, so re-locate symbols before editing.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | invisible on executed | An `executed` plan classes `done` in `aw attention`, so any unfixed defect in its prose leaves every attention view with no record it was dropped. | maintainer 2026-09-05; `attention_contract` maps executed -> done |
| F-2 | HIGH | dead required section | `## Deferred / out of scope (with reason)` is mandatory in both H2 orders and its contents are never read. | `H_DEFERRED` at `ipd_schema.py:48`; `grep -c H_DEFERRED agent_workflows/ipd_lint.py` = 0 |
| F-3 | HIGH | wrong phase | The blocking-OQ gate runs at `pre-execution` only, so it gates starting work and not claiming it is done. | `ipd_lint.py` phase split; the exclusion is deliberate and documented |
| F-4 | HIGH | prose-resolvable OQ | An OQ is "resolved" by any non-empty rationale; semantics are explicitly the reviewer's job. | `open_question_error`, `ipd_schema.py:1338-1354` (`if status == "resolved" and not has_rationale`) |
| F-5 | HIGH | no linkage concept | `ipd_lint.py` has ZERO occurrences of `From-Backlog`: the linter cannot see backlog linkage at all. | `grep -c From-Backlog agent_workflows/ipd_lint.py` = 0 |
| F-6 | MEDIUM | rollout hazard | 530 plans exist and none carries a typed carrier field, so a fail-closed rule would block everything on day one. The precedent chose silence on absence for this exact reason at 428 plans. | `ls .aw/records/plans/*/*.ipd.md \| wc -l` = 530; `check.review-finding-unescalated` absent-case comment |
| F-7 | MEDIUM | schema field is unread | `OQ_FIELDS` is declared and never consumed, so E-01 alone changes no behavior; E-02 is what gives it meaning. | `ipd_schema.py:1315-1318` |
| F-8 | LOW | walkthroughs unreachable | Walkthroughs are `tracked=False` and filename-only checked, so a defect recorded only there is invisible by construction. This plan does not fix that; it makes the IPD route reliable. | item's own measurement; `attention_contract` walkthrough policy |

## Proposed changes (ordered, validatable)

1. Declare a typed carrier field for OQ blocks and Deferred rows (E-01).
2. Write one shared predicate with three escapes, resolving carriers for real (E-02).
3. Wire `pre-transition` to it without disturbing the `pre-execution` gate (E-03).
4. Wire `aw check` to the SAME predicate under a registered rule id (E-04).
5. Ship staged severity on an existing cutover mechanism, with the blast radius measured (E-05).
6. Test three escapes, four refusals, the malformed case, staged severity, and cross-surface agreement (E-06).

## Deferred / out of scope (with reason)

- MAKING WALKTHROUGHS READABLE (F-8): they are `tracked=False` and filename-only checked by design. Changing that is a records-policy change with its own blast radius; this plan makes the IPD route reliable instead.
- PER-REQUIREMENT SPEC COVERAGE (the "which half of this approved spec is unbuilt" gap): the item explicitly says this must NOT block, and it is tracked separately as `f1sw71`.
- RETIRING `TODO.md`: tracked by `ld08f1` (open). The item names it only to explain why a `TODO.md` entry is not an acceptable carrier: it holds zero items, is in `SCAN_ROOTS`, and is silently dropped as unclassified, i.e. invisible by construction.
- SCANNING SOURCE-CODE COMMENTS for defects: `artifact_core.py` limits reading to `.md`/`.txt`, and the one TODO/FIXME scanner that exists is diff-scoped and unwired. Out of scope.
- MAKING `aw check backlog` FAIL-CLOSED in CI: currently advisory. Adjacent and tempting, but a separate decision with its own consequences.
- THE `releases` TREE having no scan root, and the `reviews` tree having no TreePolicy: both found while investigating, both their own items.

## Scope check

- Over-scope: none. Three production modules and one test file.
- Under-scope: this plan does NOT read walkthroughs, does NOT add per-requirement spec tracking, does NOT retire `TODO.md`, does NOT scan code comments, and does NOT change `aw check backlog`'s advisory posture in CI.

## Required tests / validation

New `tests/test_durable_capture.py` covering the three escapes, the four refusal cases (no carrier, dangling carrier, terminal-directory carrier, prose-only), the malformed-input case, staged severity, and `aw check`/`pre-transition` agreement on identical fixtures. Plus a whole-corpus `aw check` run reporting counts at each severity, and the bare suite on a self-measured delta.

## Spec / documentation sync

No `.spec.md` is amended, so none is declared in `- Scope-Paths:`. This plan adds an enforcement rule over an EXISTING required IPD section and an existing OQ vocabulary; it introduces no new contract for a spec to describe. If review finds that the IPD structural contract (the `ipd-spec` document) must record the new typed field, that is a spec amendment and this plan must gain the path explicitly rather than editing an undeclared file.

The new rule's message is operator-facing: it must name the offending row AND the three ways to satisfy it, because a refusal an author cannot act on is what trains people to bypass gates (`gjadwm`). Write no em or en dashes there.

## Open questions

### OQ-01: Should the carrier field be permitted to name a SPEC, not only a backlog item or a pending plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: NO. The accepted carrier set is a BACKLOG ITEM or a PENDING PLAN only. A spec is never sufficient. THE REASONING GIVEN, which goes further than this question asked and binds E-03's prompt guidance in the precursor plan `b7xarm`: an agent may and SHOULD write a spec where a spec is genuinely what the work needs, and should reference it, but the durable carrier is ALWAYS a backlog item, with any spec treated as supporting material. Offered the alternative of letting the agent judge whether a case was "just a spec" and then file a spec-review backlog item, the maintainer instead chose the rule that removes the judgement entirely, having said plainly "I don't know when 'just a spec' would be enough". So do NOT implement a spec-only branch: it delegates exactly the judgement this rule exists to prevent. The reading offered at authoring (accept a non-terminal spec as weaker-but-better-than-prose) is REJECTED. E-02's accepted-carrier list stays one list in one predicate, and it contains two entries.
  ORIGINAL FRAMING, retained because it records what was weighed: AGAINST a spec, the item argues there is no per-requirement tracking, no notion of partial implementation, and no join from a requirement to an implementing plan, so "a spec can sit `approved` for weeks with half its requirements unbuilt and nothing asks which half". FOR a spec, `aw attention` DOES map spec `approved` -> `ready`, so a spec is not invisible the way an executed plan is, and the repository already treats a spec as a legitimate release-gate carrier. The maintainer weighed both and chose the stricter set.

### OQ-04: Can this gate work at all before an execute turn is required to declare its findings?

- Blocking: yes
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08, AND THE ANSWER ADDED A PREREQUISITE THIS PLAN DID NOT HAVE. Asked to approve OQ-01, the maintainer rejected the framing instead: "I do want to know how the system (runner) 'knows' there is an 'unfixed bug that has no durable home somewhere else' since I am skeptical you can do this. Settle this before moving forward." THAT SKEPTICISM WAS CORRECT AND IS NOW RECORDED AS THIS PLAN'S HONEST LIMIT. The runner cannot detect an unfixed defect and this plan never claimed to: E-01 matches STRUCTURALLY and explicitly refuses prose matching as "spoofable by any incidental mention and brittle against rewording", so the predicate only ever decides mechanical facts (does a typed field exist, does its id6 resolve, is the target non-terminal). It is a DECLARATION gate, not a detector. The consequence the maintainer drew out: an author who mentions a defect in prose and writes no typed field is NOT caught, and F-6 already measures the day-one effect (530 plans exist, ZERO carry the field), so shipped alone this gate initially catches nothing.
  THE RULING: the declaration must be PRODUCED before the check that verifies it is built. In the maintainer's words, the execute instructions "must ask the agent to report any found bugs, gaps, concerns both affirmatively and negatively ... If neither exists, the runner must ask the agent to add it", with the preferred design being that when the agent is done, "the runner asks the agent (in the same session) to fill out an outstanding bugs/gaps/etc. report", and this is "a requirement before we can implement the check to see if a backlog / IPD exists for each item".
  CONSEQUENCE FOR THIS PLAN: `b7xarm` (`defreport-01`) was authored to produce that report, and this plan now declares `Item-Dependencies: to-review:b7xarm`. E-02's predicate should read the NORMALIZED report `b7xarm` E-06 persists on the run record rather than only the plan's typed fields, since that record is what distinguishes "found nothing" from "never asked". Resolved rather than open because the decision is made and the dependency is declared; BLOCKING is recorded as `yes` to reflect that executing this plan before `b7xarm` would ship a gate with nothing to verify.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new field's declaration beside the existing `Finding` entry in `OQ_FIELDS`, and paste the comment recording why prose matching is refused. State explicitly that `OQ_FIELDS` has no consumer TODAY (quote `ipd_schema.py:1315`) and that E-02 is what gives this field meaning, so this item alone is provably behavior-neutral: paste a test or a run showing no existing plan's lint result changed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the predicate and its verdict type, and paste the side-by-side comparison with `evaluate_blocking_close` / `CloseVerdict` showing the shape was MIRRORED rather than reinvented. Demonstrate each of the three escapes returning a satisfied verdict on a real fixture.
    THE LOAD-BEARING REFUSALS: paste a DANGLING carrier refused, and paste a carrier resolving into `executed/` refused. The second is the whole point of the plan (an executed plan is the hiding place), so a predicate that accepts it has inverted the requirement. Paste a malformed row producing a finding rather than a traceback.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw ipd lint --phase pre-transition` reporting the new rule on a fixture plan with an uncarried defect. THEN PROVE THE `pre-execution` GATE IS UNTOUCHED: paste its behavior before and after on the same fixture and show them identical, and paste `git diff` for `ipd_lint.py` showing the existing blocking-OQ check was not moved or widened.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `RULE_REGISTRY` entry, and paste `aw check` and `aw ipd lint --phase pre-transition` producing the SAME verdict on the SAME fixture, for both a passing and a failing case. Show by symbol that both call ONE predicate (object identity or the single call site), since drift between the two surfaces is the failure the precedent's docstring warns about. Confirm `aw check backlog`'s advisory posture in CI is unchanged (`git diff` on the workflow file EMPTY).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: THE BLAST RADIUS IS THE EVIDENCE. Paste `aw check` over the whole corpus BEFORE and AFTER, with counts at each severity, and show existing plans produce WARNINGS not ERRORS. State the plan count you measured (authoring measured 530) and how many carry a typed carrier field (expected 0). Paste an OLD plan warning and a NEW plan erroring, and name the date/format-version mechanism you gated on, citing the existing cutover mechanism you reused rather than a new one.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the test FAILING against pre-change HEAD and passing after. Enumerate every covered case with its result: three escapes accepted; no-carrier, dangling, terminal-directory, and PROSE-ONLY all refused; malformed producing a finding; staged severity both ways; and `aw check`/`pre-transition` agreeing on identical fixtures.
    The PROSE-ONLY case is mandatory: a deferred row saying "tracked in the backlog" with no typed field must be REFUSED. If that case passes the gate, the rule is spoofable and the item's central design requirement is unmet.
    Paste the bare `python3 -m pytest` summary line with a self-measured BEFORE baseline and the AFTER-minus-BEFORE failure set EMPTY. Inside a lane worktree, ~14 `test_run_viewer.py` failures belong to the separate `agrlvw` defect (plan `utwr6y`); do not report them as this plan's.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). OQ-01 is open but `Blocking: no`; E-02 keeps the accepted-carrier set as one list so the answer is a one-line change plus a test.

STAGED SEVERITY IS NOT OPTIONAL. 530 plans exist and none carries a typed carrier field, so shipping this as a hard error would turn the entire corpus red and train every agent to bypass `aw check`, which is the exact failure mode `gjadwm` records. If the staged rollout cannot be made to work, STOP and report rather than shipping a fail-closed rule over a corpus that cannot satisfy it.

ONE PREDICATE, TWO SURFACES. `aw check` and `aw ipd lint --phase pre-transition` must call the SAME function. Two implementations that agree today will disagree later, which is precisely why the nearest precedent's docstring insists on one evaluator.

TYPED FIELDS ONLY. Never satisfy this rule by grepping prose for "TODO", "future work", or a bare id6 mention. Prose matching is spoofable by incidental mention and brittle against rewording, and the schema already records that reasoning for the `Finding` field.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: `check_engine.py` is large and widely imported, so re-locate every cited symbol before editing.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence. Note the pleasing recursion: once this plan lands, its own terminal transition is subject to the rule it adds.

On completion, close backlog `jys5dp` (this plan carries `- From-Backlog: jys5dp` and inherits its `Blocks-Release: next`).
