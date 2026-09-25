# Review: Share the lane reclaim prompt and the deferred-integration adapter, and delete the dead host _record_forced_stop copies

- Subject-Id: 184tn9
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was correctly skipped per
Step 1. Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0)
before review and again at `--phase review-finalize` after the revisions.

THE PLAN'S CENTRAL CLAIM IS TRUE AND I REPRODUCED IT END TO END, which is worth stating first
because every finding below is a correction to measurement or fixture rather than to reasoning.
Driving both hosts' REAL `retry_deferred_integrations` against a temp git repo, with
`integrate_lane_branch` faked to CALL the validation runner it is handed and return
`INTEGRATION_REFUSAL_CONFLICT`, oc recorded `integration_ladder.kind == 'merge-unchecked'` with
`revalidation_was_unmeasured(item)` True, while agy recorded `'fail-merge'` and False. The mechanism
is exactly as F-1 describes: agy's `_integrate` passes `dict(item)`, so `_record_revalidation` writes
`post_merge_revalidation` onto a shallow copy, and `record_integration_refusal`'s
`revalidation_was_unmeasured(item)` reads the live mapping and finds nothing. The shared reader's own
docstring rests on that assumption in terms ("the item IS the live queue mapping, so the fact is
available at the refusal site for free"), which agy's copy silently breaks. So a recoverable harness
fault is reported on agy as a terminal merge refusal, and the plan is correctly `Work-Kind: bug`
with `Blocks-Release: next`. F-2 also reproduces (both host `_record_forced_stop` definitions have
zero callers anywhere in `agent_workflows/` or `tests/`), as do F-3 (the closure marks
`LANE_PROMPT_TIMEOUT`, `_LANE_PROMPT_DISABLED` and `select` ABSENT-FROM-SHARED) and F-4
(`UnmovableSymbolTests` survives only as a comment in `tests/test_runner_shared.py`, and both cited
test files are absent).

THE DOMINANT FINDING IS PR-601, AND IT WOULD HAVE FAILED THE PLAN ON ITS FIRST AND LAST ITEMS. The
census is 12 divergent forks, not 13. `reconcile_disposition` was single-sourced by commit
`6b94a4d9` ("statusvocab: rename the terminal status vocabulary so a label names its refusing
authority"), which removed the host definitions from both runners; I verified with `git merge-base
--is-ancestor` that `8e74dcac` is an ancestor of `6b94a4d9`, so the de-fork landed AFTER the HEAD
this plan measured at and the authored 13 was already stale when the plan was written. E-01 gated on
`DIVERGENT FORKS (13)` and E-06 on `(10)`; both would have been red on arrival, and the honest fix is
not to substitute 12 and 9 but to stop asserting a live population at all. Both items now record the
observed number and assert the DELTA plus the three names' absence, which is the repository's own
re-derivation convention for live-artifact counts. This also removes a trap: `cdxcbh` is `approved`
and owns four of the remaining forks, so the count can legitimately drop again before this plan runs.

PR-602 IS A VALIDATION ASSERTING A STRING THE CODE CANNOT PRODUCE. V-02 required the agy case to fail
"with `merge-refused` != `merge-unchecked`". But `merge-refused` is not a refusal KIND at all:
`INTEGRATION_REFUSAL_CONFLICT` is `fail-merge`, and `merge-refused` appears only inside legacy-status
allowlists in `oc_runipd`, `agy_runipd`, `attention` and `render_stream`, retained (as the oc comment
says) so a pre-`l2mzxn` run directory stays readable. The refusal-kind and item-status vocabularies
share spellings and are different namespaces. Measured, the agy kind is `fail-merge`. An executor
checking V-02 literally would see a mismatch on a CORRECT measurement, and the cheap repair is to
edit the test toward `merge-refused`, which nothing writes. V-02 now demands the constants and names
both wrong failures explicitly.

PR-603 IS A FIXTURE THAT DIES BEFORE IT ASSERTS. E-02's item shape carries five keys. Running it, the
refusal path reaches `record_integration_refusal` -> host `save_state` ->
`runner_shared.save_state` -> per-host `write_report` -> `runner_shared.write_report`, which builds a
summary-table row indexing `item['position']`, and raises `KeyError: 'position'`. The test fails on
both hosts for a reason unrelated to the defect, and since the oc case is supposed to PASS at HEAD,
the executor sees two failures and no signal. Adding `position`, `setid`, `action`, `file` to the
item and `run_id`, `host` to the state ran clean at review and produced the split above. E-02 now
carries that measurement and the instruction to prefer an existing fixture's item shape, so a future
`write_report` field does not break this test alone.

PR-604 IS AN INJECTION LIST MISSING A NAME THE BODY CALLS. An AST walk of oc's
`retry_deferred_integrations` returns `save_state` among its free names, and both `_finish` and
`_finish_review` call it. `save_state` is per-host by construction: each host's is
`runner_shared.save_state(run_dir, state, write_report=write_report)` closing over its own
`write_report`, and the shared module's own `save_state` requires that keyword, so it is not a
substitute. E-04's parameter list omitted it. The mercy is that this fails loudly at first call rather
than silently, but it is still a lift that cannot be written as specified. The item now names it with
the per-host reason and the `reconcile_interrupted` precedent, and instructs the executor to
re-derive the free-name set rather than trust the list.

I also checked the rest of E-04's closure and found it sound, which is worth recording because it is
the part that looked riskiest. The scanner's `--closure` marks only `integrate_review_lane_branch`,
`lane_containment` and `runner_shared` as ABSENT-FROM-SHARED; `lane_containment` is already imported
function-locally in ten places inside `runner_shared`, so it needs no injection, and the plan's
decision to keep the `validation_runner_for=` lambda's `dict(item)` unchanged is CORRECT rather than
an oversight. That copy is deliberate and documented: `attributed_away_failure_ids`' docstring records
that both hosts' lambdas pass a shallow copy, which is why that reader is read-only. It is also inert,
since `reattempt_deferred_integrations` accepts `validation_runner_for` and never reads it (zero Name
loads in the body). The defect is the OTHER call, and only that one changes. E-04 now says so, so an
executor does not "fix" the wrong copy or delete a documented constraint.

PR-605 IS A CROSS-PLAN OWNERSHIP GAP THAT WOULD HAVE ORPHANED E-05. `afpmdu` (approved) instructs
"DO NOT delete or convert those copies here", correctly excluding the host `_record_forced_stop`
copies from its own scope, and attributes them to "`recovone` (`cdxcbh`) already names
`_record_forced_stop` in its OUT list". An OUT list is a disclaimer, not an assignment: `cdxcbh`'s
Scope OUT clause reads "`_record_forced_stop`/`_lane_reclaim_prompt`/`disable_lane_prompt` (other
residue named by the scanner)" and its Deferred section repeats it. So an executor reading `afpmdu`
could defer this deletion to a plan that will never do it. `afpmdu`'s own F-15 independently measured
the same facts E-05 relies on, which is corroboration rather than conflict. E-05 now carries both
citations and states that this plan is the only owner.

PR-606 IS A PRE-COMMIT GATE THE LIFT TRIPS. `select.` appears on exactly one line in each host, the
`select.select(...)` inside `_lane_reclaim_prompt`, so after E-03 the top-level `import select` is
unused in both. `ruff` is a fail-closed pre-commit hook here, so leaving it makes the COMMIT be
rejected, not a test fail. E-03 said to drop it "only if nothing else uses it", which is correct but
optional-sounding and stated no consequence. It is now required, with a new E-07 running `ruff`
explicitly so the executor does not discover it at commit time.

PR-607 IS AN OPEN QUESTION THAT CONTRADICTS ITS OWN ARTIFACT AND FAILS A GATE. OQ-01 asked whether the
plan should be `bug` with `Blocks-Release: next`, then said the graduation "fixed `chore`" and to
"proceed as `chore`" - while the front matter already carries `- Work-Kind: bug` and
`- Blocks-Release: next`, correctly inherited from source item `5jsjnr`, which carries both. The
question was answered by the artifact it was written on, and its stated default would have invited an
approver to downgrade a correctly gated plan. It also owed a typed durable carrier:
`evaluate_durable_carrier` returned one `error`-severity drift on this plan, which gates
`aw ipd lint --phase pre-transition` as well as `aw check plans`. Resolved from evidence (D-1) with a
`Carrier-Declined:` stating why nothing is outstanding. Re-measured: zero carrier drifts, and
`aw check plans` went from 13 findings to 12 with this plan's gone.

PR-608 and PR-609 are smaller. E-06's `-k "FailClosedIntegrationGuard or VerifierGateAndRunnerBug"`
has no guard against selecting nothing: a zero-match `-k` exits 5 with no failures, which reads as a
pass, so the regression check could certify clean having run no test. V-06 now requires the collected
count. And the gate was two lines plus one sentence on a plan that changes runner behavior on a
release-gating defect and touches a file three other approved plans declare; it now carries a
what-a-human-is-approving paragraph, a per-path scope fence stated as a declaration with an explicit
not-in-scope list, the honesty rule naming the three fakeable claims, three genuine stop conditions,
and conditional runner/executor finalize ownership.

ON CONCURRENCY, since the plan touches the most contended file in the repository. Three approved plans
declare `agent_workflows/runner_shared.py`: `cdxcbh`, `afpmdu` and `87jnym`. I checked each for SYMBOL
overlap and found none - `87jnym` names none of this plan's three symbols, `cdxcbh` disclaims them,
and `afpmdu` touches the SHARED `_record_forced_stop` while this plan touches only the host copies.
File overlap is not a hazard, because the runners isolate each item in its own worktree and merge
through the revalidate gate. That is recorded in the plan's Scope check so a later reader does not
re-raise it as a runtime risk.

ON RIGHT-SIZING. Seven items became eight, still one concern per item: the added E-07 is a single
`ruff` invocation, separated from the suite because it gates the commit rather than the tests. E-04 is
the largest item and was examined against the splitting diagnostics; it is one deliverable (one
function lifted, two wrappers) with one test surface, and splitting the lift from its wrappers would
leave the tree broken between items.

`aw check release-gates` reports `findings: 0`, exit 0, so this plan's inherited gate starts from a
clean baseline. `aw sanitize --agent` is clean. No spec describes these internal symbols (the plan's
N/A is correct), so no spec amendment is owed and `Scope-Paths` correctly declares none.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability (live-artifact count asserted as a constant) | `python3 tools/runner_fork_scan.py` at review: `DIVERGENT FORKS (12)`, `reconcile_disposition` absent; `git log -S "def reconcile_disposition" -- agent_workflows/oc_runipd.py` -> `6b94a4d9` ("statusvocab: rename the terminal status vocabulary..."); `git merge-base --is-ancestor 8e74dcac 6b94a4d9` -> true, so the de-fork POSTDATES the plan's cited HEAD | THE PLAN'S FIRST AND LAST GATES ARE BOTH RED ON ARRIVAL. E-01 requires `DIVERGENT FORKS (13)` and E-06 requires `(10)`; the census is 12, because `reconcile_disposition` was single-sourced between the authoring HEAD and now. So the baseline item fails before any work starts and the proving item fails after all of it, on a number that was already stale when the plan was written. Substituting 12 and 9 would repeat the defect rather than fix it: the census counts a LIVE population, `cdxcbh` is approved and owns four of the remaining forks, and the repository's own convention is that a criterion counting live artifacts must require re-derivation and keep the authored figure as context. | C:Low; U:Low; S:Low; F:Low; Overall:Low (rewording two acceptance criteria; no code effect) | FIXED | E-01 now RE-DERIVES and records the printed count, asserting instead the three properties the plan actually depends on (the three names present under `DIVERGENT FORKS`, `--triples` listing `_record_forced_stop`, zero host/test CALLERS), with the `6b94a4d9` measurement stated as the reason. E-06 asserts a DELTA of exactly minus three plus the three names' absence, never a literal total. The Goal and a new conventions bullet record the 13 -> 12 correction and its cause; V-01 and V-06 carry the matching evidence requirements. |
| PR-602 | MEDIUM | IN-SCOPE | E. Testing and verification (an assertion against a nonexistent value) | Measured at review: `oc: ladder kind = 'merge-unchecked'`, `agy: ladder kind = 'fail-merge'`; `INTEGRATION_REFUSAL_CONFLICT = "fail-merge"`, `INTEGRATION_REFUSAL_UNMEASURED = "merge-unchecked"`, `INTEGRATION_BLOCKED_STATUS = "fail-merge"`; `merge-refused` occurs only in legacy-status allowlists (`oc_runipd.py:4111`, `agy_runipd.py:3062`, `attention.py:1928`, `render_stream.py`) whose own comment says both vocabularies are listed so pre-rename run directories stay readable | V-02 DEMANDS A FAILURE STRING THE CODE CANNOT PRODUCE. It requires the agy case fail "with `merge-refused` != `merge-unchecked`", but `merge-refused` is not a refusal KIND at all - it is a legacy item-STATUS spelling. The refusal-kind and status vocabularies share spellings and are separate namespaces. The observed kind is `fail-merge`. So an executor validating V-02 literally sees a mismatch on a correct measurement, and the cheapest reconciliation is to write the test against a value nothing produces, which would make the regression permanently unfalsifiable. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-8 with both measurements and the vocabulary distinction. V-02 now requires the assertion be written against the CONSTANTS and names the two wrong failures explicitly (a `merge-refused` diff, and a `KeyError` from `write_report`). E-02's expected outcome states the observed kind is `fail-merge` and says not to expect `merge-refused`. A new conventions bullet records the two namespaces and that `merge-refused` is legacy-only. |
| PR-603 | MEDIUM | IN-SCOPE | E. Testing (a fixture that cannot reach its assertion) | Measured at review with E-02's exact item shape: `KeyError: 'position'` raised from `runner_shared.write_report`'s summary-table row (the f-string that formats `item['position']` into the run-summary table), reached via `record_integration_refusal` -> host `save_state` -> `runner_shared.save_state` -> per-host `write_report`. Adding `position`, `setid`, `action`, `file` to the item and `run_id`, `host` to the state ran clean and produced the oc/agy split | E-02'S FIXTURE DIES BEFORE IT ASSERTS ANYTHING, ON BOTH HOSTS. The five-key item omits fields `write_report` indexes, and every refusal path calls `save_state`, so the test raises before reaching the ladder assertion. The oc case is supposed to PASS at HEAD, so the executor sees two failures with no signal about the defect, and the plan's one falsifiability proof yields nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now carries the measurement, the minimum key set that ran clean at review, and the instruction to derive the real minimum by running it and to prefer an existing fixture's item shape so a future `write_report` field does not break this test alone. V-02 names a missing-key error as a FIXTURE defect to repair before recording evidence. Added a conventions bullet on the `save_state` -> `write_report` chain. |
| PR-604 | MEDIUM | IN-SCOPE | A. Correctness / C. Architecture (an injection the lift cannot resolve) | AST walk of `oc_runipd.retry_deferred_integrations` at review: FREE NAMES include `save_state`; `oc_runipd.save_state` and `agy_runipd.save_state` are each `runner_shared.save_state(run_dir, state, write_report=write_report)` over a per-host `write_report`; `runner_shared.save_state` declares `write_report` keyword-only with no default; `_finish` and `_finish_review` both call `save_state` | E-04'S PARAMETER LIST OMITS A NAME THE LIFTED BODY CALLS. `save_state` is a free name in oc's body and is per-host by construction, so the shared module's own `save_state` cannot substitute for it (it would raise `TypeError` for the missing keyword). The lift as specified therefore cannot be written. It fails loudly rather than silently, which limits the damage to a wasted attempt, but the item as authored is not executable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04's signature now includes `save_state`, with the per-host reason, the `TypeError` consequence and the `reconcile_interrupted` precedent, plus the instruction to re-derive the free-name set by AST walk rather than trust the list. The item also records which free names need NO injection and why (`lane_containment` is already function-locally imported in ten places in `runner_shared`; the closure marks only three names ABSENT-FROM-SHARED). V-04 requires the shipped signature be pasted. Added F-7. |
| PR-605 | LOW | IN-SCOPE | C. Architecture / G. Plan executability (cross-plan ownership) | `afpmdu` E-03: "DO NOT delete or convert those copies here: that is host deduplication ... `recovone` (`cdxcbh`) already names `_record_forced_stop` in its OUT list"; `cdxcbh` Scope OUT: "`_record_forced_stop`/`_lane_reclaim_prompt`/`disable_lane_prompt` (other residue named by the scanner)", repeated in its Deferred section; both plans `approved`; `afpmdu` F-15 independently measured the same dead-copy facts | AN APPROVED SIBLING POINTS E-05'S WORK AT A PLAN THAT DISCLAIMS IT, so the residue could survive every plan that mentions it. `afpmdu` correctly excludes the host copies from its own scope but reads `cdxcbh`'s OUT list as ownership, when an OUT list is a disclaimer. An executor who reads `afpmdu` while executing this plan has a documented-looking reason to skip E-05 and wait for `cdxcbh`, which will never do it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now states that this plan is the correct and only owner, quoting both `cdxcbh`'s OUT clause and `afpmdu`'s misattribution, and notes that `afpmdu`'s F-15 corroborates the same measurements. Added F-9 and a conventions bullet that an OUT clause is a disclaimer rather than an assignment. |
| PR-606 | MEDIUM | UNDER-SCOPE | C. Architecture / G. Plan executability (a gate outside the test suite) | `grep -n "select\." agent_workflows/oc_runipd.py` and the agy twin each return exactly one line, the `select.select(...)` in `_lane_reclaim_prompt`; `ruff` runs in this repository's pre-commit hooks and rejects the commit on findings | AFTER E-03 THE `import select` IS UNUSED IN BOTH HOSTS AND MAKES THE COMMIT FAIL, not a test. E-03 said to drop it "only if nothing else in that module uses it" - correct, but phrased as optional and stating no consequence, and nothing in the plan checks `ruff`. The failure therefore surfaces at commit time, after all eight items, which on a lift-only diff is pure waste. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires the deletion, names `ruff`'s fail-closed pre-commit posture as the reason, and tells the executor to re-derive the "nothing else uses it" fact by grep. Added E-07/V-07 running `ruff check` and `ruff format --check` on the three edited modules as a distinct item, with the reason it is separate from the suite. V-03 additionally requires the `import select` grep return nothing. Added F-6. |
| PR-607 | MEDIUM | IN-SCOPE | A. Correctness / D. Anti-regression (a gate the plan fails today, and a self-contradiction) | `evaluate_durable_carrier` on this plan at review: one `error` drift, "OQ-01 records an outstanding obligation with NO durable carrier"; `aw check plans --agent` 13 findings including this plan; OQ-01 text: "The graduation instruction fixed `chore` ... Default: proceed as `chore`" against front matter `- Work-Kind: bug` / `- Blocks-Release: next`; source item `5jsjnr` carries `- Work-Kind: bug` and `- Blocks-Release: next` | OQ-01 CONTRADICTS ITS OWN ARTIFACT TWICE AND FAILS A GATE. It asks whether the plan should be `bug` with `Blocks-Release: next` while the front matter already carries both, correctly inherited from `5jsjnr`; then it states a default of `chore`, which if acted on would DOWNGRADE a correctly gated release blocker. Separately, being `Status: open` it owes a typed durable carrier and has none, so `aw check plans` reports an `error` on this plan and `aw ipd lint --phase pre-transition` would refuse it later rather than now. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved from evidence (D-1): `Status: resolved`, `Owner: none`, with the inheritance chain from `5jsjnr`, AGENTS.md's inheritance obligation, and the independent perceptibility argument from F-1's measurement; the contradictory `chore` default is removed and the de-gate route is named for a maintainer who disagrees. Added a `Carrier-Declined:` stating why nothing is outstanding. Re-measured: zero carrier drifts on this plan, `aw check plans` 13 -> 12 with this plan absent, `aw check release-gates` findings 0. Added F-10. |
| PR-608 | LOW | IN-SCOPE | E. Testing (a selection that can silently select nothing) | `pytest -k <expr>` exits 5 ("no tests collected") with no failures when the expression matches nothing; E-06's regression command is `-k "FailClosedIntegrationGuard or VerifierGateAndRunnerBug"` across two files | E-06'S REGRESSION CHECK CAN CERTIFY CLEAN HAVING RUN NO TEST. The `-k` expression names four classes across two modules by substring, and nothing in the item or its validation requires proof that anything was selected. A renamed or relocated class (both plausible: `19313eed` deleted whole modules, and `cdxcbh`/`afpmdu` are concurrently editing these files) turns the regression gate into a no-op that reports success. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now says to CONFIRM the selection matches something and to paste the collected count, stating that a zero-match `-k` exits 5 and reads as a pass. V-06 requires both pytest summary lines INCLUDING collected counts, and the gate's honesty rule names this as one of the three claims most exposed to faking. |
| PR-609 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: two metadata lines plus one sentence covering commit path, no-push, pasted output and the transition. Compare `0i4fkt`/`8apjpp`, which carry an approval paragraph, a declaration-style scope fence, an explicit not-in-scope list, an honesty rule naming fakeable claims, stop conditions, and conditional finalize ownership | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS on a plan that changes runner behavior, carries a release gate, and edits the file three other approved plans declare. There was no statement of what a human is approving (so the `bug`/`Blocks-Release` classification had no explanation at the approval point), no scope fence to reconcile against despite an explicit OUT list existing in the Scope field, no honesty rule, and no stop conditions. It also instructed a bare move to `executed/`, which is wrong under a runner that owns the transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph separating the one behavioral fix (with its measured consequence) from the three behavior-preserving lifts and naming E-03 as the only lift with residual risk; a per-path scope fence stated as a DECLARATION with an explicit not-in-scope list (the four `cdxcbh` symbols, `afpmdu`'s surface, `87jnym`'s, the five host shells, `handle_audit_command`, `disable_lane_prompt`, the unused `validation_runner_for`, and the deliberate `dict(item)`); the hard-MUST honesty rule naming V-02's string, V-06's `-k` count and the census delta, plus the bare-suite flag prohibitions; three genuine stop conditions; and the lifecycle transition with conditional runner/executor ownership plus the note that the three source items are already `graduated`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 asks the maintainer whether this plan should be `Work-Kind: bug` with `Blocks-Release: next`, while its own front matter already carries both. Ask, or resolve? | Resolve from evidence: `Status: resolved`, keep both fields, delete the contradictory `chore` default. | (a) Leave it open for the maintainer - rejected: the repository already answers it, so asking would spend a round trip on a settled fact, and leaving the stated `chore` default in place is actively dangerous because acting on it would DOWNGRADE a correctly gated release blocker. (b) Change the front matter to `chore` to match the question's default - rejected: it would drop a gate AGENTS.md obliges the plan to inherit from `5jsjnr`, and F-1's measured user-perceptible impact independently earns `bug`. (c) Resolve but leave no carrier - rejected: the `error`-severity carrier rule would still block `pre-transition`. | `5jsjnr` carries `- Work-Kind: bug` and `- Blocks-Release: next`; AGENTS.md's "the gate TRAVELS with the work" inheritance obligation; the review-time reproduction of F-1 on both hosts; `check_engine.evaluate_carrier_obligation`'s DECLINED escape | yes |
| D-2 | The census figure is stale (13 authored, 12 measured). Substitute the correct numbers, or stop asserting a total? | Stop asserting a total: record the observed count, assert a DELTA of minus three plus the three names' absence. | (a) Substitute 12 and 9 - rejected: it repeats the defect one commit later. `cdxcbh` is approved and owns four of the remaining forks, so the total can legitimately move again before this plan executes, and the plan would be red for a reason that is not a defect. (b) Ask the maintainer to freeze the tree - rejected as absurd for a chore. (c) Drop the census check entirely - rejected: it is the plan's only evidence that the three lifts actually landed. | `git merge-base --is-ancestor 8e74dcac 6b94a4d9` true, so the de-fork postdates the cited HEAD; the plan-review rubric's live-artifact-versus-stable-code-fact re-derivation convention; `cdxcbh` `- Status: approved` naming four of the remaining forks | yes |
| D-3 | `afpmdu` (approved) points these deletions at `cdxcbh`, which disclaims them. Who owns E-05? | This plan. Record both citations in E-05 so the executor is not left to reconcile two approved plans at execution time. | (a) Defer E-05 to `cdxcbh` as `afpmdu` says - rejected: `cdxcbh`'s Scope OUT clause and its Deferred section both name `_record_forced_stop` as residue it does not take, so deferring means nobody does it. (b) File a corrective note against `afpmdu` - rejected: it is `approved` and not yet executed, so amending it is another plan's act, and the sentence is a misattribution in prose rather than an instruction that breaks its own work. (c) Say nothing and let E-05 stand - rejected: an executor who reads `afpmdu` has a documented-looking reason to skip the item. | `cdxcbh` Scope OUT and Deferred sections; `afpmdu` E-03's own text; `afpmdu` F-15's independent measurement of the same dead copies | yes |
| D-4 | E-04 keeps `validation_runner_for=lambda item: ...dict(item)...`. Is that copy part of the F-1 defect and should it change too? | No. Keep it byte-identical and record WHY in the item. | (a) Change it to the live item for consistency - rejected: `attributed_away_failure_ids`' docstring records the shallow copy as a LOAD-BEARING constraint ("a READ of the answer record works there while any WRITE would land on the copy and be lost"), which is why that reader is read-only; changing it would invalidate a documented invariant for no benefit. (b) Remove the parameter, since it is never read - rejected: the plan already defers that as a signature change, and it is genuinely out of scope. (c) Say nothing - rejected: two `dict(item)` calls in one function, one of which is the defect, is exactly where an executor fixes the wrong one. | AST walk: `reattempt_deferred_integrations` has zero Name loads of `validation_runner_for` in its body; `runner_shared.attributed_away_failure_ids` docstring; the measured defect is in `_integrate`, not the lambda | yes |
| D-5 | Three approved plans declare `agent_workflows/runner_shared.py`. Is that a hazard to raise? | No. Verify SYMBOL-level disjointness, record it in the Scope check, and do not raise file overlap as a runtime risk. | (a) Raise it as a concurrency warning to the maintainer - rejected: AGENTS.md states plainly that the runners isolate each item in its own worktree and merge through the revalidate gate, so file overlap is settled and repeating it as a hazard wastes the maintainer's time on a question the runner answered. (b) Add an `Item-Dependencies` edge to serialize behind `cdxcbh`/`afpmdu` - rejected: no symbol overlaps, so the edge would delay a release-gating fix for nothing. | AGENTS.md "The runners own ordering, isolation, and orchestrators"; `87jnym` Scope-Paths and body name none of the three symbols; `cdxcbh` disclaims them; `afpmdu` touches the SHARED `_record_forced_stop`, not the host copies | yes |
| D-6 | E-02's fixture raises `KeyError: 'position'` before asserting. Specify the exact key list, or point at an existing fixture? | Both: record the measured minimum AND instruct the executor to prefer an existing fixture's item shape and to derive the real minimum by running it. | (a) Hard-code only the measured key list - rejected: it pins today's `write_report` fields into a new test, so the next field added there breaks this test alone, which is the brittleness the repository retired change-detector tests to avoid. (b) Say only "reuse an existing fixture" - rejected: the executor then rediscovers the failure mode, and the measurement is cheap to hand over. | Measured `KeyError: 'position'` from `runner_shared.write_report`'s row builder; the clean run after adding `position`/`setid`/`action`/`file` and `run_id`/`host`; the plan's own convention bullet that change-detector tests over code text were retired | yes |
