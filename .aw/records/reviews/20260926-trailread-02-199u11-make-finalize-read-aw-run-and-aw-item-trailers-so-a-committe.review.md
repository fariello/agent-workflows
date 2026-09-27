# Review: Make finalize read AW-Run and AW-Item trailers so a committed out-of-scope path this plan made always needs a reason

- Subject-Id: 199u11
- Subject-Type: ipd
- Reviewed-At: 2026-09-27
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f94dc07f` (the plan was authored at `61ef21d8`). The target plan was committed and
unchanged, so the pre-review snapshot was correctly skipped per Step 1. Structural preflight
`aw ipd lint --phase author` reported `conforming` (exit 0) BEFORE review, and `--phase
review-finalize` reported `conforming` after the edits, including the added E-07/V-07.

THE DIAGNOSIS IS RIGHT, AND I REPRODUCED IT RATHER THAN READING IT, ON THREE VARIANTS INSTEAD OF ONE.
Driving `ipd_lifecycle.finalize_precheck` on scratch repos built to the plan's own fixture shape, the
trailered-own case yields exactly what the Concern claims: `attribution_source: commit-cohesion`,
`out_of_scope_paths: []`, `disregarded_unowned_paths: ['other.py']`. I also built the untrailered and
`AW-Item: zzz999` variants and they yield the IDENTICAL triple. That is a sharper statement of the
defect than the plan makes: the three cases are not merely mis-handled, they are currently
INDISTINGUISHABLE, which is precisely why a reader is the right fix and why `unknown` can safely fall
through (it is falling through today). F-2 holds exactly (`rg` finds trailer syntax only in four
`git_commit_helper` comment lines, and `run_evidence`'s `RUN-COMMIT-CONTENTS` still records
`waiting_on` "a trailer READ-BACK predicate"). F-3 holds: I read the receipt literal in
`ipd_lifecycle.begin` and there is no `run_id` key, so OQ-01's choice of `AW-Item` as the ownership key
is forced by the evidence and not a preference.

THE TWO HIGH FINDINGS ARE BOTH IN THE GIT PLUMBING, AND BOTH WOULD HAVE BITTEN AT EXECUTION. I probed
`%(trailers:key=...,valueonly)` against git 2.43.0 rather than trusting the format string, and it does
not behave as the plan assumes in two independent ways. FIRST (PR-1302), the field is MULTI-VALUED:
with `separator=%x2C` a commit carrying two `AW-Item` trailers returns the single field
`aaa111,zzz999`, so E-02's authored rule "any `AW-Item` value equal to `plan_id6`" has no defined
meaning unless the field is split first, and comparing the field whole would classify that commit
`foreign` for both of its own ids. SECOND, and worse (PR-1301), git's trailer grammar permits a value
to CONTINUE on a following whitespace-indented line, and the continuation comes back INSIDE the field.
Measured output for the range form the plan specifies was `<sentinel><sha>\x00abc123\n  AWHDR1111...\n\ng\n`,
i.e. the second line is neither a header nor a path. E-03's whole design is a LINE-ORIENTED grouping
("an explicit sentinel prefix on the header line rather than a 40-hex heuristic"), and the plan
correctly identifies that a heuristic header test is unsafe while missing that its own replacement
inherits the same class of bug from the other end: the hazard is not a path that looks like a header,
it is a VALUE line that looks like a path. The failure direction matters and is why this is HIGH rather
than MEDIUM: a misparsed line desynchronizes the grouping, which can attribute one commit's paths to a
DIFFERENT commit classified `owned`, and that is the fail-open direction in a plan whose entire safety
argument is "demand-only, so it cannot invert the gate". I replaced it with a record-delimited parse
(`%x1e` record separator, `%x1f` header terminator), verified at review on the folded-value repo, and
required V-03 to paste a measurement on a folded value if the executor chooses different framing.

THE THIRD HIGH IS THAT THE PLAN'S USER-VISIBLE CLAIM IS TRUE ONLY FOR A HAND FINALIZE. The gate tells
the approving human that a trailer-owned out-of-scope path "always needs a `--scope-reason`". Under a
driver it does not need a human at all: `runner_shared.compute_scope_reconciliation` maps every entry
of `out_of_scope_paths` to the fixed string "changed by the plan's approved execution (auto-reconciled
by <host>)" and hands it to finalize, so a newly demanded path is satisfied without a stop. I checked
whether that makes the plan pointless and it does not, which is the interesting part: the auto-reason
is HONEST for a trailer-owned path in a way it is not for a cohesion-attributed one, because a
trailer-owned path genuinely is this execution's own work, whereas cohesion may name a co-worker's
(which is exactly what `gys47u`'s `attribution_source` note warns a human about). So the real gain on
the automated path is a truer PERMANENT RECORD rather than a new gate, and the plan should say so. I
added E-07/V-07 to write that into the code comment and a gate paragraph to say it to the approver. I
deliberately did NOT add any behavioral branch: keying a refusal or warning on `trailer_attribution`
would be an unapproved behavior change and would strand runs, and I said so in the item.

THE TWO MEDIUMS ARE BOTH VALIDATION THEATRE THAT WOULD HAVE PASSED WITHOUT THE WORK BEING DONE. E-05's
expected outcome, echoed by V-05, is that `rg -n "essentially no commit in history carries one
yet|when those land"` returns nothing. It already returns nothing for the first alternation on the
UNMODIFIED file, because that sentence wraps after "no commit in" and `rg` is line-oriented; the second
alternation matches, so the combined grep exits 0 today and would exit 1 after touching only the
`_run_record_committed_paths` sentence while both other docstrings stayed stale. A V-item that a
partially-unperformed E-item satisfies is worse than no V-item, because it launders the gap. I
replaced it with three per-phrase anchors, each measured exiting 0 on the unmodified file today
(`essentially no commit in` at 2141, `when those land` at 2052, `exact fix that would remove` at 2333),
and required the before/after exit status of each. E-06 case (6) has the same shape of hole from a
different direction: it is the plan's only end-to-end proof, and it can pass having written NO trailer,
because Order 1's reader validates `AW_RUN_ID` against the `new_run_id` shape and drops a malformed
one (its own review PR-1203 measured `run-test` failing that pattern). A silently trailer-less case (6)
produces the same `out_of_scope_paths` as case (2) and reads as a reader bug. I required a
pattern-valid run id and a read-back assertion on both keys before the precheck assertion, plus a stop
condition forbidding the two tempting repairs (hand-writing the trailer, or deleting the case).

WHAT I CHECKED AND FOUND CLEAN, stated because the analogous check is what produced Order 1's worst
finding. Order 1's PR-1201 was a shipped assertion in an undeclared file that the change broke. I ran
the same sweep here: no test in the suite references `attribution_source`, `_working_tree_path_is_owned`,
or any symbol E-02/E-03 adds, and the only test touching `disregarded_unowned_paths` is
`tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests`, whose fixture commits through a helper
that writes a plain message with no trailer. That path therefore classifies `unknown` and falls through
unchanged, so the assertion is unaffected. I recorded that in the plan's scope check and added a stop
condition: if it DOES go red, the reader is promoting `unknown` to `owned`, which is the one inversion
this design forbids, and the executor must report rather than adjust the test. I also verified the
plan's claim that `check_engine.check_scope_drift` is untouched-by-design, which holds: it calls
`_paths_changed_by_this_execution` (the deliberately unfiltered union) and never the ownership
predicate.

ONE CROSS-SET CLAIM WAS WRONG AND I CORRECTED IT RATHER THAN PROPAGATING IT. The spec-sync section says
spec `25kzda`'s preamble sentence "nothing reads trailers back" becomes stale when this plan executes.
The spec contains no such sentence (`rg -n "nothing reads|read.back"` finds nothing); what it contains
is the `NOTHING PASSES THEM` clause, which is about the WRITER and is a different claim, and which
plan `olkeju` (Set `spec25kfix`) already owns. I read `olkeju` and its E-01 ALREADY instructs its
executor to check whether `199u11` has executed and to word the reader half accordingly, so the
ordering is handled on that plan's side in either direction and this plan correctly declares no spec
edit. Left as N/A with the reasoning corrected and the dependency named.

WHAT I DID NOT CHANGE. The demand-only design and its asymmetry argument, which is the strongest thing
about this plan and which I checked from the other side: because a trailer can only ADD a demand, a
forged trailer costs an attacker an extra reason to write and can never manufacture a false EXCUSE,
which is what makes trusting a locally-writable record acceptable here and what makes OQ-02's refusal
to excuse on `foreign` correct rather than merely conservative. I added that property to the gate as
"THE HONEST SECURITY PROPERTY" because the code is told to state it and the approving human was not.
Also unchanged: OQ-01's choice of `AW-Item` (forced by F-3, which I verified in the receipt literal);
the decision to keep `_working_tree_path_is_owned`'s misleading name; both Carrier-Declined deferrals,
including the refusal to bind `RUN-COMMIT-CONTENTS`, whose reasoning matches `run_evidence`'s own
`waiting_on` text; and the `followup`/`medium` classification with no release gate (verified: neither
the plan nor `am1g38` carries `- Blocks-Release:`, and `followup` is not in the gating set).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1301 | HIGH | IN-SCOPE | A. Correctness (an unsound parse in the plan's core helper) | git 2.43.0, review scratch repo: the authored range form `--format=<sentinel>%H%x00%(trailers:key=AW-Item,valueonly,separator=%x2C) --name-only` returns `<sentinel><sha>\x00abc123\n  AWHDR1111...\n\ng\n` for a commit whose `AW-Item` value carries a folded continuation line. The continuation line is indistinguishable from a path line | **E-03'S ONE-CALL GROUPING IS LINE-ORIENTED, AND A TRAILER VALUE MAY CONTAIN A NEWLINE, SO THE SENTINEL DOES NOT MAKE IT SAFE.** The plan correctly rejects the 40-hex header heuristic but replaces it with a scheme that inherits the same class of bug from the other end: not a path misread as a header, but a VALUE line misread as a path. A desynchronized grouping can attribute one commit's paths to a different commit classified `owned`, which is the FAIL-OPEN direction in a plan whose safety argument is that it can only add demands. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-03 rewritten to require a RECORD-DELIMITED parse, `--format=%x1e%H%x00<item field>%x1f --name-only`, split on `\x1e` then `\x1f` then `\x00` then newlines; verified at review on the folded-value repo. An alternative framing is permitted but must be record-delimited and must paste a folded-value measurement in V-03. Expected outcome extended to require the continuation text be absent from `paths`. Added F-4 note in Proposed changes and a conventions bullet. |
| PR-1302 | HIGH | IN-SCOPE | A. Correctness (a scalar comparison against a non-scalar field) | git 2.43.0: two `AW-Item` trailers with `separator=%x2C` yield one field `aaa111,zzz999`; the default separator yields them newline-joined. A folded value also embeds a newline | **E-02 COMPARES A MULTI-VALUED, POSSIBLY MULTI-LINE FIELD TO A SINGLE id6.** "Any `AW-Item` value equal to `plan_id6`" is undefined until the field is split, and comparing it whole classifies a commit carrying its OWN id alongside another as `foreign`, i.e. silently drops a demand the plan exists to add. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 gains an explicit split rule (split on `,`, then on newlines, then strip, then drop empties; `owned` iff any surviving token equals `plan_id6` exactly) with the measurement cited and the naive comparison explicitly forbidden. Expected outcome extended with the two-`AW-Item` case. Added F-5. |
| PR-1303 | HIGH | UNDER-SCOPE | C. Architecture / G. Plan executability (the approval text does not describe the automated path) | `runner_shared.compute_scope_reconciliation` maps every `out_of_scope_paths` entry to `"changed by the plan's approved execution (auto-reconciled by <host>)"` and hands it to finalize; both hosts reach it via `record_item_spec_edits(..., reconcile=...)` | **UNDER A DRIVER, EVERY DEMAND THIS PLAN ADDS IS AUTO-ANSWERED, SO THE GATE'S "ALWAYS NEEDS A `--scope-reason`" IS TRUE ONLY OF A HAND FINALIZE.** An approver reads it as a new stop that does not exist, and a later maintainer measuring the demand through a runner log would conclude the reader is inert. The auto-reason is nonetheless HONEST for a trailer-owned path (unlike the cohesion case), so the real gain is a truer permanent record, which the plan never states. | C:Low; U:Medium; S:Low; F:Low; Overall:Medium | FIXED | Added E-07/V-07, COMMENT-ONLY, stating the auto-reconciliation, why it is correct rather than a hole, and that the effect is a truer record and not a new stop; explicitly forbids any branch keyed on `trailer_attribution`. Gate gains "WHO ACTUALLY FEELS THE NEW DEMAND". `Highest E allocated` 06 -> 07. Added F-6 and a conventions bullet. |
| PR-1304 | MEDIUM | IN-SCOPE | E. Testing (a validation item an unperformed E-item satisfies) | `rg -n "essentially no commit in history carries one yet" agent_workflows/ipd_lifecycle.py` -> exit 1 on the UNMODIFIED file; the sentence wraps after "no commit in" (line 2141 continues on 2142). `when those land` matches at 2052; `exact fix that would remove` at 2333 | **V-05'S GREP ALREADY HALF-PASSES BEFORE ANY EDIT, SO IT WOULD ACCEPT AN E-05 THAT TOUCHED ONE DOCSTRING OF THREE.** A validation item a partially-unperformed execution item satisfies launders the gap rather than catching it, which is worse than having no item. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 and V-05 now name three per-phrase anchors, each measured exiting 0 on the unmodified file today with its line number, and require the before-AND-after exit status of each. The authored wrapped-phrase grep is explicitly forbidden as a substitute. Added F-7 and named this as one of the two easiest-to-fake claims in the honesty rule. |
| PR-1305 | MEDIUM | IN-SCOPE | E. Testing (the only end-to-end case can pass vacuously) | `a6xbso` E-03 validates `AW_RUN_ID` against the `new_run_id` shape and drops a malformed value with a warning; its review PR-1203 measured `run-test` failing that pattern. `AW_ITEM_ID6` is validated separately against `artifact_core.ID6_RE` | **E-06 CASE (6) CAN PASS HAVING WRITTEN NO `AW-Run` TRAILER, AND ITS FAILURE MODE MIMICS A READER BUG.** It is the plan's only proof that Order 1's writer and this reader agree on the format; if the run id is not pattern-valid the writer emits nothing for that key, and a fully trailer-less commit yields the same `out_of_scope_paths` as case (2). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Case (6) must use a pattern-valid run id and must assert BOTH trailers read back off the produced commit BEFORE asserting the precheck result; V-06 must paste that read-back. A stop condition forbids hand-writing the trailer or deleting the case if Order 1's channel is absent. Added F-8. |
| PR-1306 | MEDIUM | IN-SCOPE | A. Correctness (a cross-artifact claim about a sentence that does not exist) | `rg -n "nothing reads\|read.back" <spec 25kzda>` -> no match. The spec's clause is `NOTHING PASSES THEM`, about the WRITER. Plan `olkeju` E-01 already instructs its executor to check whether `199u11` has executed and word the reader half accordingly | **THE SPEC-SYNC SECTION QUOTES A SPEC SENTENCE THAT IS NOT IN THE SPEC.** It asserts this plan makes "nothing reads trailers back" stale; that sentence is absent, and the clause that IS there is about the writer and is already owned by another plan. A reader checking the claim finds nothing and cannot tell whether a spec edit is owed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section corrected: records what the spec actually says, names `olkeju`/`j0ag0u` as the owner, records that `olkeju` E-01 already handles both orderings, and states that this plan needs and declares no spec edit, with "do NOT edit the spec from here". |
| PR-1307 | LOW | UNDER-SCOPE | D. Anti-regression (the blast radius on shipped tests was unstated) | `grep -rln "attribution_source" tests/` -> nothing; `grep -n "disregarded_unowned_paths" tests/test_ipd_lifecycle_cli.py` -> one line, `AdditiveScopeWideningTests` asserting `tests/test_extra.py` IS disregarded; that fixture's `_commit_all` writes a plain message with no trailer | **THE PLAN NEVER IDENTIFIED WHICH SHIPPED ASSERTIONS SIT IN THE BLAST RADIUS**, which is exactly the omission that produced Order 1's worst finding (a shipped assertion in an undeclared file). The one real neighbour is benign and the reason it is benign is load-bearing: its fixture is untrailered, so the path classifies `unknown` and falls through. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope check records the sweep and its result (no undeclared test file is forced into scope, unlike `a6xbso` PR-1201). Required tests section names the one assertion and why it is unaffected. A stop condition forbids weakening it and states that if it DOES go red the reader is promoting `unknown` to `owned`, the one inversion this design forbids. |
| PR-1308 | LOW | IN-SCOPE | B. Security / G. Plan executability (thin fence; an unstated property the code is told to state) | Fence as authored: "`agent_workflows/ipd_lifecycle.py` and the new test file". E-02 requires the CODE to state that a trailer is "a consistency record, not tamper-proof provenance", while the gate said nothing about it. `- Blocks-Release:` absent from both the plan and `am1g38`; `followup` not in the gating set | **THE FENCE NAMED NO SURFACES AND THE GATE OMITTED THE HONEST SECURITY PROPERTY E-02 REQUIRES THE CODE TO CARRY.** A trailer looks like provenance and is forgeable by any same-user process; the approving human was not told, and the finalize instruction asserted runner ownership unconditionally. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence now names the in-scope surface per file plus four expected-read-not-modified surfaces (`git_commit_helper`, `runner_shared.compute_scope_reconciliation`, `check_engine.check_scope_drift`, `tests/test_ipd_lifecycle_cli.py`). Gate gains "THE HONEST SECURITY PROPERTY" including the ADD-only asymmetry that makes the weak guarantee acceptable and links it to OQ-02. Finalize ownership made conditional; the verified absence of a release gate recorded. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-1301: the authored one-call parse is unsound. Prescribe a specific framing, or tell the executor to "parse robustly"? | PRESCRIBE the `\x1e`/`\x1f` record-delimited framing, verified at review, while permitting an alternative that is record-delimited AND measured in V-03. | (a) "Parse robustly" with no framing named: rejected, the plan already tried a specific scheme and got it wrong, so restating the goal without a mechanism hands the same trap back. (b) Drop to one `git log -1` per commit (reuse E-02 per sha): rejected, it abandons the plan's one-call requirement for a range that can hold hundreds of commits and would make finalize measurably slower on a busy tree. (c) Parse `--name-only` in a separate call from the trailers: rejected, two calls over the same range can disagree if HEAD moves between them. | The measured folded-value output; the verified `\x1e`/`\x1f` form; `\x1e`/`\x1f` cannot occur in a git path or trailer value | yes |
| D-2 | PR-1303: the runner auto-answers every demand. Should the plan add a runner-side stop or warning so the demand is felt? | NO. Record the fact in a comment (E-07) and in the gate; change no behavior. | (a) Refuse or warn when `trailer_attribution.owned_paths` is non-empty: rejected, that is a behavior change nobody approved, it would strand runs, and it contradicts the plan's own demand-only safety argument which is what makes it reviewable at all. (b) Say nothing and leave the gate's claim as-is: rejected, it misdescribes the automated path to the approving human and would make a later "is the reader inert?" measurement come out wrong. (c) Widen scope to `runner_shared` to distinguish the auto-reason wording for trailer-owned paths: rejected as a separate, genuinely useful change that needs its own plan; noted in the scope check rather than smuggled in. | `compute_scope_reconciliation` read verbatim; the plan's own demand-only argument; `gys47u`'s `attribution_source` note distinguishing honest from heuristic attribution | yes |
| D-3 | PR-1304: V-05's grep is vacuous. Fix the grep, or drop the grep and rely on the pasted diffs? | FIX IT with three per-phrase anchors and require before/after exit status of each. | (a) Rely on the pasted docstring diffs alone: rejected, a diff proves an edit happened somewhere, not that all three sites moved, and E-05 names three sites precisely because they drifted apart before. (b) Use `rg -U` / multiline mode: rejected as needlessly clever and platform-fragile when three single-line anchors are available and were measured. (c) Assert on a post-edit phrase instead: rejected, a new phrase can be added while a stale one survives, which is the exact failure this checks for. | Each anchor's measured exit status and line number on the unmodified file at review HEAD | yes |
| D-4 | PR-1306: the spec-sync section cites a nonexistent spec sentence. Correct it here, or declare a spec edit? | CORRECT THE CLAIM; declare no spec edit. | (a) Declare the spec in `- Scope-Paths:` and amend it here: rejected, the clause that exists is about the WRITER and is already owned by `olkeju`, whose E-01 explicitly handles the case where `199u11` has executed; two plans editing one clause is the collision the ownership convention exists to prevent. (b) Leave the claim and let the executor discover it: rejected, it reads as an owed spec edit and an executor may amend an approved spec on a false premise. (c) File a backlog item: rejected, `olkeju` already exists and already covers it. | The spec read for the quoted phrase (absent); `olkeju` E-01 read verbatim | yes |

### Deferred and open

- (none). All eight findings are FIXED in place. Three were HIGH and none was polish: PR-1301 and
  PR-1302 are unsound git parsing in the plan's two core helpers, and PR-1301's failure direction is
  fail-OPEN in a plan whose whole safety argument is that it cannot open anything; PR-1303 is a gate
  that misdescribes what a human is approving for the execution path that produces nearly every
  finalize in this repository. No finding was left OPEN or DEFERRED, so no escalation to a
  `- Blocking: yes` question is owed. Both pre-existing open questions (OQ-01 key choice, OQ-02
  foreign-excuse) were already resolved; I re-derived each from evidence rather than accepting it, and
  both stand. OQ-01's answer is forced by the begin receipt carrying no `run_id`, which I verified in
  the receipt literal. OQ-02's answer is stronger than the plan states, and I added the reason to the
  gate: because a trailer can only ADD a demand, forging one cannot manufacture a false excuse, so the
  add-only direction is what makes trusting a locally writable record defensible at all.
