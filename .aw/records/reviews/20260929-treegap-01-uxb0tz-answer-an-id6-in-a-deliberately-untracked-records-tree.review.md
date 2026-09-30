# Review: Answer an id6 that lives in a deliberately untracked records tree instead of refusing it as a typo

- Subject-Id: uxb0tz
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `26197b09`, working tree clean. `aw ipd lint --phase author --agent` reported
`clean` before any edit, so the structural gate passed and every finding below is semantic.

THE PLAN'S CENTRAL CORRECTION OF ITS BACKLOG ITEM IS RIGHT, and it is the best thing about it.
The item claims the impact is "MASKED rather than misleading" and that "no operator is told a real
artifact does not exist". That is false, and the plan falsifies it by execution rather than by
argument. Re-measured independently here: `aw attention 7ny1bg` exits 2 printing
`no artifact matched selector '7ny1bg'` while `aw find 7ny1bg` resolves the same token to
`.aw/records/roadmaps/20260712-7ny1bg-01-7ny1bg-...roadmap.md` at exit 0. An author who had merely
transcribed the item would have written a plan to admit two trees that must not be admitted.

F-2's census reproduces EXACTLY, which is unusual and worth recording. Enumerating both trees for
filename-identity-slot id6s yields 17 tokens; 14 refuse from `aw attention` while resolving under
`aw find`, and the other 3 are precisely the slug words F-11 predicted (`assess`, `agents`,
`mirror`). F-5 also reproduces exactly (21 of 24 walkthroughs carry no parseable `- Status:`; the
3 that do carry the three prose values quoted, and all three are confirmed unparseable by
`attention_contract.SPEC_STATUS_RE`, as is the roadmap's `- **Status:** DRAFT FOR CONSIDERATION`).
F-7 and F-8 verify by execution: `resolve_selectors` returns both files and `_classify_tree` returns
both excluded policies with their `reason` strings populated. F-3, F-6 (owner verbs), F-9, F-10 all
hold as written.

SIX PROBLEMS DOMINATE, three of them mechanical defects that would have broken execution.

FIRST AND WORST, E-04's core deliverable is UNREACHABLE AS DESIGNED, and nothing in the plan
notices. E-03 removes the excluded-tree tokens from `refusable`; `attention.run`'s emission is
guarded by `if selector_facts is not None and selector_facts.refusable:`, so an invocation whose
only token is excluded-tree-explained never enters `_emit_unresolved_selector_refusal` at all.
E-04 then instructs the executor to change the behavior of a function that is no longer called.
Demonstrated by patching `refusable` in memory and driving the four surfaces: every one exits 0
SILENTLY (human board prints `0 artifacts shown`, `--agent` emits `outcome: clean`, `--check`
prints `the view is valid.`, `--paths` prints nothing). So E-03 alone converts a misleading
refusal into a SILENT WRONG ANSWER, which is worse than the defect: the operator is now told
nothing at all. This is PR-001.

SECOND, E-04 requires a schema-INVALID record. It demands exit 0, a record that validates through
`agent_schema.assert_valid_agent_record`, and `kind` not `error`. The shipped
`unresolved_selector_agent_record` emits `kind: error` with `outcome: cannot-run`, and an `error`
record MUST carry exit 2 (verified: `Error record must carry exit=2`), while a `result` record at
exit 0 refuses `cannot-run`, `fail` and `unverified` alike. The plan names three constraints and
never checks they are jointly satisfiable; they are, but only via a narrow combination it does not
name (`kind: result` with `outcome` in `clean`/`ok`/`partial`/`skipped`). PR-002.

THIRD, `--check` is a CONTRACT HAZARD the plan never mentions. On the `--check` surface the exit-0
path prints `aw attention --check: the view is valid.` E-04 as written would have an excluded-tree
token answered by a validity claim about a token the view never resolved, which is the exact defect
the sibling plan `o6ksmw` E-04 is adding a test to FORBID. PR-003.

FOURTH, THE PLAN IS SCOPED TO TWO TREES WHEN THE DEFECT CLASS HAS FIVE. `TREE_POLICY` carries five
excluded trees (`walkthroughs`, `roadmaps`, `comms`, `docs-prompts`, `reviews`), and the `reviews`
tree holds 565 records. E-02's helper is built on a `record_types` tuple that omits `reviews` and
`comms`, so it cannot fire for them. The plan's own generalization claim in F-8 ("a future tree
added as excluded gets the same treatment automatically") is therefore FALSE as designed. Measured
mitigation, which is why this is HIGH and not a BLOCKER: all 565 review records share an id6 with a
tracked artifact today, so no `reviews` token refuses right now. The hole is latent, not live.
PR-004.

FIFTH, E-05 WRITES TO AN INSTALLER-MANAGED TEMPLATE TARGET without saying so.
`.aw/records/walkthroughs/README.md` is emitted by `engine.ensure_docs_readmes` from the shipped
template `agents-docs-walkthroughs-README.md`, under a no-clobber rule. The repo copy has already
diverged from the template, so the divergence widens silently and a fresh install never receives
the admission verdict. PR-005.

SIXTH, F-6 CARRIES A MEASUREMENT ERROR in the direction that flatters the plan's own conclusion.
It states "2 of 24 walkthroughs ... carry `## Workflow history`". Measured: exactly ONE does
(`...u8tiox-lane-to-main-integration...`). Two more mention the phrase in prose (one quoting
another artifact's history, one pointing at per-order records), which is how 1 became 2. The
verdict is unaffected and in fact strengthened, which is precisely why the number must be right:
E-05 pastes these figures into a README as durable reference. PR-006.

Two smaller items: V-05 demanded evidence for a criterion no tree fails as stated (PR-007), and
the plan is silent on a live documentation collision with sibling `o6ksmw`, which is concurrently
publishing the very exit contract this plan adds an exemption to (PR-008).

SEPARATELY, THE PLAN ARRIVED FAILING `aw check plans` and the structural preflight did not notice.
Its `## Workflow history` was ordered oldest-first, so `ipd_lifecycle._plan_status_events` derived
`to-review -> draft` and the repository checker reported a backwards transition against it. This was
true of the committed file before this review touched anything. Worth recording that
`aw ipd lint` reported `clean` at both `author` and `review-finalize` across this defect, so the
deterministic preflight is NOT a substitute for running `aw check plans` on a reviewed plan
(PR-009).

NOTE ON GRADE. The plan inherits `- Work-Kind: chore` and argues in its own history that a
reviewer may dispute it. I am NOT escalating it to `bug`. The plan's reasoning is sound on the
evidence it cites (`aw find` answers all 14 tokens correctly, so no artifact is unreachable), and
the maintainer's perceptibility test is a judgement the filer records with a number, which this
plan does. Recorded as decision D-5 rather than silently accepted.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness / G. Plan executability | `attention.run`, the guard `if selector_facts is not None and selector_facts.refusable:` immediately above `_emit_unresolved_selector_refusal`; `attention._emit_unresolved_selector_refusal` (docstring "ONE function for all eight surfaces"); demonstrated by in-memory patch of `SelectorMatchFacts.refusable` | E-04's DELIVERABLE IS UNREACHABLE AFTER E-03. The emission site is guarded on `refusable` being non-empty; E-03 removes excluded-tree tokens from `refusable`, so an invocation whose only token is excluded-tree-explained never reaches `_emit_unresolved_selector_refusal`, and editing that function changes nothing for the case the plan exists to fix. DEMONSTRATED, not predicted: patching `refusable` to drop `7ny1bg`/`v0nmuv` and driving four surfaces gives exit 0 with NO explanation on any of them (human `0 artifacts shown`; `--agent` `outcome:"clean"`; `--check` `the view is valid.`; `--paths` 0 bytes). So following the plan literally converts a MISLEADING refusal into a SILENT wrong answer, which is strictly worse for the operator than the defect being fixed, and E-06's own assertion that the token "names the tree's reason" would fail with no instruction on how to make it pass. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now states the consequence and forbids treating the subtraction as sufficient. E-04 is rewritten to require a SECOND, SEPARATE branch evaluated BEFORE the refusal guard (so it is reached whether or not any token is refusable), with the emission-point citation corrected from "the function" to "the guarded call site in `attention.run`", and its Expected outcome now names the four surfaces the demonstration drove. V-04 now requires the explanation to be pasted from all four. Added F-12 recording the demonstration. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness / E. Testing | `agent_schema.validate_agent_record`: `elif kind == "error": if exit_code != 2` -> "Error record must carry exit=2"; and for `result`, `if exit_code == 0: if outcome in ("findings","fail","cannot-run","error","unverified")` -> "Exit code mismatch"; driven over the 14 kind/outcome pairs | E-04 NAMES THREE CONSTRAINTS AND NEVER CHECKS THEY ARE JOINTLY SATISFIABLE: exit 0, validates through `assert_valid_agent_record`, and `kind` not `error`. The shipped `unresolved_selector_agent_record` produces `kind:"error"` + `outcome:"cannot-run"` + `exit:2`, so it cannot be reused by adjusting the exit code alone: an `error` record at exit 0 is rejected outright, and a `result` record at exit 0 rejects `cannot-run`, `fail` and `unverified`. The satisfiable combination is narrow (`kind:"result"` with `outcome` in `clean`/`ok`/`partial`/`skipped`) and the plan names none of it, leaving an executor to discover the schema wall after writing the emitter. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now states the measured constraint, names the satisfiable envelope, requires a NEW record builder rather than a mutation of the refusal builder (which must keep emitting exit 2 for genuine refusals), and forbids asserting validity by eye. V-04 now requires the record pasted WITH the validator called on it. Added F-13. |
| PR-003 | HIGH | IN-SCOPE | A. Correctness / D. Anti-regression | `attention.run`'s `--check` branch, `sys.stdout.write("aw attention --check: the view is valid.\n")`; measured: `aw attention --check reusable` exits 0 printing that sentence; sibling plan `o6ksmw` E-04 requires that sentence be ABSENT on a refusal | THE `--check` SURFACE WOULD CLAIM VALIDITY ABOUT A TOKEN IT NEVER RESOLVED. E-04 lists no per-surface behavior for `--check`, and the exit-0 path it routes to prints `aw attention --check: the view is valid.`. An operator running `aw attention --check 7ny1bg` would be told the view is valid, which is a claim about repository state answering a question about one artifact. This is the same defect the concurrently-pending `o6ksmw` E-04 adds a test to forbid for the refusal case, so this plan would introduce on the exit-0 path exactly what its sibling is pinning shut on the exit-2 path. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now enumerates `--check` and `--check --agent` explicitly, requires the excluded-tree explanation to REPLACE the validity sentence for that invocation (the view's validity is not what was asked), and requires that no drift or violation record be appended so `--check`'s meaning is unchanged for every other invocation. V-04 requires both `--check` surfaces pasted. Added F-14. |
| PR-004 | HIGH | UNDER-SCOPE | C. Architecture / F. KISS | `attention_contract.TREE_POLICY` has five `tracked=False` entries (`walkthroughs`, `roadmaps`, `comms`, `docs-prompts`, `reviews`); the `record_types` tuple shared by `filter_items_by_selectors` and `selector_match_facts` omits `reviews` and `comms`; `.aw/records/reviews/` holds 565 `.review.md` files | THE FIX IS SCOPED TO TWO TREES WHILE THE DEFECT CLASS HAS FIVE, AND THE PLAN CLAIMS OTHERWISE. F-8 asserts "a future tree added as excluded gets the same treatment automatically", which is false as designed: E-02 iterates the `record_types` tuple, which has no `reviews` and no `comms` entry, so the helper cannot resolve a token in the largest excluded tree in the repository. Measured mitigation, which is why this is not a BLOCKER: all 565 review records currently share an id6 with a tracked artifact (0 orphans), so no `reviews` token refuses today and the hole is LATENT. It becomes live the moment a review is written for an artifact that is later archived out of a tracked tree. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-8's over-broad generalization corrected in place with the measurement. E-02 now requires the helper to iterate the EXCLUDED POLICIES from `TREE_POLICY` rather than a hand-listed type tuple, so all five excluded trees are covered by construction, and requires the `reviews`/`comms` omission to be handled explicitly rather than inherited. Added F-15 with the 565-file and 0-orphan measurement. V-02 now requires a `reviews`-tree probe. |
| PR-005 | MEDIUM | IN-SCOPE | C. Architecture / G. Plan executability | `engine.ensure_docs_readmes` writes `{dirs['walkthroughs']}/README.md` from template `agents-docs-walkthroughs-README.md` under `if readme_path.is_file(): skipped`; `diff` of template against the repo copy shows the repo copy already carries 3 sections the template does not | E-05 EDITS AN INSTALLER-MANAGED TARGET WITHOUT SAYING SO. The walkthroughs README is emitted from a shipped template under a no-clobber rule, so writing the admission verdict only into the repo copy widens an existing divergence and guarantees a fresh managed repo never receives it. The plan treats both READMEs as ordinary docs. (The roadmaps README is NOT template-emitted, per DECISIONS D73, so the two targets are genuinely different and the plan treats them identically.) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now records that the walkthroughs README is template-emitted and no-clobber while the roadmaps README is not, states that the verdict is being recorded in the REPO copy deliberately (it is a measurement about THIS repository's artifacts, not a statement true of every managed repo), and forbids editing the shipped template, which is outside `Scope-Paths`. Added F-16 and a conventions bullet. |
| PR-006 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | `.aw/records/walkthroughs/`: exactly 1 of 24 files matches `^#{1,6}\s*Workflow history`; 3 match the phrase anywhere (the other 2 quote another artifact's history or point at per-order records); the roadmap matches neither | F-6 OVERSTATES THE HISTORY COUNT AS "2 of 24", MEASURED AT 1 of 24. The error runs in the direction that softens the plan's own conclusion, and it matters because E-05 pastes these figures into a README as durable reference a future author is told to rely on, so a wrong number becomes a wrong citation in a revisited place. The verdict is unaffected and is strengthened. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 corrected to 1 of 24 with the two false-positive causes named so a re-measurement does not re-derive 2. E-05's walkthroughs figures corrected to match, and E-01 now requires the history count to be re-derived by HEADING match rather than substring. |
| PR-007 | LOW | IN-SCOPE | E. Testing and verification | V-05 as authored: "showing for EACH tree the four admission criteria named, which criteria that tree fails"; spec `20260808-1945-01` Section 318 names four criteria; measured: each tree fails 3 of 4 outright and the fourth (exhaustive mapping) is unsatisfiable as a CONSEQUENCE of the second | V-05 DEMANDED EVIDENCE OF A PER-CRITERION FAILURE THAT CANNOT BE STATED AS AUTHORED for one of the four. "An exhaustive mapping" is not independently failable: it is impossible precisely BECAUSE there is no closed status enum, so a README asserting it as a separate failure would be recording one fact twice and a literal-minded executor would look for a fourth measurement that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 and V-05 now require the fourth criterion to be stated as a CONSEQUENCE of the missing status enum rather than as an independent failure, so the README records three measured failures and one derived one. |
| PR-009 | HIGH | IN-SCOPE | G. Plan executability / lifecycle | `aw check plans --agent` at HEAD `26197b09` listed this plan under `check.lifecycle-transition-invalid`; `ipd_lifecycle._plan_status_events` on the AS-COMMITTED text derives `[to-review, draft]`; the checker assumes newest-first | THE PLAN ARRIVED FAILING THE REPOSITORY'S OWN CROSS-TREE CHECK. Its `## Workflow history` had the `draft` line ABOVE the `to-review` line, so the derived status stream read `to-review -> draft`, a backwards transition. This was true of the committed file before this review touched it (verified against `git show HEAD:<path>`), so it is the plan's own defect and not one the review introduced. A plan that fails `aw check plans` cannot be cleanly approved or executed, and `aw ipd lint` does NOT catch it at any phase (it reported `clean` both before and after), so the structural preflight gave no warning. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Swapped the two lines into newest-first order. Verified: `_plan_status_events` now derives `draft -> to-review -> reviewed`, and `aw check plans --agent` reports 0 findings naming this plan (repository total went 56 -> 55). |
| PR-008 | LOW | IN-SCOPE | C. Architecture / contention | Pending plan `o6ksmw` (`attselratify-01`, `Status: reviewed`, `Readiness: go-pending-approval`) declares `Scope-Paths: docs/cli-output-contract.md, tests/test_attention.py, DECISIONS.md, CHANGELOG.md`; its E-02 publishes the standing-question-versus-named-artifact-assertion discriminator into Section 11.1; `grep` shows neither plan names the other | A LIVE DOCUMENTATION COLLISION IS UNRECORDED IN BOTH PLANS. `o6ksmw` is concurrently publishing the zero-match exit contract into `docs/cli-output-contract.md`, stating the discriminator as "standing question versus named-artifact assertion". This plan adds a THIRD class that is neither (a token that names a real artifact the view excludes), so whichever lands second leaves the published contract incomplete. No file conflict exists (the two `Scope-Paths` sets are disjoint), which is exactly why it went unnoticed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-17 naming the collision and the ordering consequence, and a "Deferred / out of scope" row with `Carrier: o6ksmw`. The plan deliberately does NOT declare `docs/cli-output-contract.md` (that is `o6ksmw`'s file and a second declarer would race it); OQ-03 records the case where a reviewer wants the doc updated here. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: should the reviewer redesign the emission point, or escalate the unreachability to the maintainer as blocking? | Fix it in place: require a second branch evaluated BEFORE the `refusable` guard, and record the demonstration | Escalate as a blocking OQ, which would hold a low-priority chore on a maintainer for a mechanical fact; mark REPLAN, which discards a sound plan over one repairable defect | The repository answers it without judgement: the guard `if selector_facts is not None and selector_facts.refusable:` is right there in `attention.run`, and the in-memory demonstration shows exactly what happens (four surfaces, exit 0, no message). Nothing about the remedy is a scope, priority or risk call reserved to the maintainer | yes |
| D-2 | PR-004: should the fix be widened to all five excluded trees, or left at the two the backlog item named? | Widen to all five by iterating `TREE_POLICY`'s excluded policies instead of a hand-listed tuple | Leave it at two and file a backlog item for the rest, which files an item for a hole the same helper closes for free; widen and also add `reviews`/`comms` to `TRACKED_TREES`, which F-5/F-6 refuse | `TREE_POLICY` is the contract's own inventory of excluded trees, so deriving from it is strictly simpler than a parallel list AND is what F-8 already claimed the design did. The `reviews` hole is measured LATENT (565 records, 0 orphans), so widening prevents a future defect at no behavioral cost today | yes |
| D-3 | PR-005: may the reviewer widen `Scope-Paths` to include the shipped walkthroughs README template? | No: forbid touching the template and record why the repo copy alone is correct here | Add `.aw/system/workflows/templates/agents-docs-walkthroughs-README.md` to `Scope-Paths` so a fresh install receives the verdict | The verdict is a MEASUREMENT ABOUT THIS REPOSITORY'S ARTIFACTS (21 of 24 files, one specific roadmap), so it is not true of a fresh managed repo and installing it there would ship a false claim. The general rule that the trees are excluded is already in the template's own `tracked=False` sentence | yes |
| D-4 | PR-008: should this plan update `docs/cli-output-contract.md` for the third exemption class? | No: cross-reference `o6ksmw` as carrier and route the disagreement to OQ-03 | Declare the doc here, which would put two pending plans on one file for a section neither has landed yet; say nothing, which leaves the published contract silently incomplete | `o6ksmw` already declares that file with `Readiness: go-pending-approval` and its E-02 owns the discriminator sentence; a second declarer races it, and the repository's own contention convention is to fix in the owning plan and cross-reference. Recording the collision is what the plan was missing, not the edit | yes |
| D-5 | Should the review escalate `- Work-Kind: chore` to `bug` with a release gate, given F-1 shows the answer is misleading rather than masked? | No: keep `chore`, and record the dispute rather than resolving it silently | Escalate to `bug` + `Blocks-Release: next` on the reviewer's reading of the perceptibility rule | AGENTS.md makes perceptibility a judgement the filer RECORDS WITH THE NUMBER SUPPORTING IT, and this plan does exactly that: `aw find` answers all 14 tokens at exit 0 (re-measured), so no artifact is unreachable and the cost is a confusing second opinion. Grade is also a maintainer call on gating, and the plan surfaces the contrary evidence for them | yes |

### Round 1 close

All nine findings FIXED in place. No finding is left `OPEN` or `DEFERRED`, so no escalation to a
`- Blocking: yes` question is owed under the gate threshold. Three open questions stand, all
`Blocking: no`: OQ-01 (pre-existing, spec-amendment reading), OQ-02 (pre-existing, file ordering
with `1qt1u3`), and OQ-03 (new, from PR-008).
