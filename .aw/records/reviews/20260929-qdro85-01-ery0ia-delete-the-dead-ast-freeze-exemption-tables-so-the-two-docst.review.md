# Review findings: plan ery0ia

- Subject-Id: ery0ia
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-401 (HIGH, fixed), PR-402 (HIGH, fixed), PR-403 (MEDIUM, fixed), PR-404 (LOW, fixed), PR-405 (LOW, fixed)

## Round 1

Reviewed at HEAD `174b98b7` in an isolated review lane. The plan file was already committed and is
byte-identical to the lane input (`diff` reports no difference), so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `conforming`, exit 0, ZERO findings
BEFORE semantic review; `--phase review-finalize --agent` reports `conforming` after revision. The plan
is `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

THE PLAN'S CENTRAL JUDGEMENT IS CORRECT AND I REPRODUCED EVERY LOAD-BEARING MEASUREMENT RATHER THAN
TRUSTING IT. The plan's whole shape rests on refuting its own backlog item's premise, which is the most
consequential claim it makes, and it holds. An independent AST `Load`/`Store` census over
`tests/test_runner_shared.py` returns `Store=1 Load=0` for all three target names, and for sixteen
module-level assignments the live/dead partition is exactly what F-04 states: `BOTH` 19 loads, `_MODULES`
24, `HOST_LABELS` 2, `INJECTED` 1, everything else dead or transitively dead through
`ALL_SHARED_RUN_CHECKED_CALLERS` (I read lines 217-220 and confirmed both "transitively dead" loads occur
inside that dead table's own construction). F-02 is right that the enforcing harness is GONE, not relaxed:
`test_every_clean_symbol_is_a_STRICT_fingerprint_match`, `test_a_redocumented_symbol_is_still_held_to_its_executable_body`,
`_capture_without_docstring`, `fingerprint_of` and `drop_docstring` all measure `defs=0`, and the first two
survive only as comment prose. F-03's cause is real (`git show --stat 19313eed` shows
`tests/test_runner_shared.py | 3539 +++--------------`). F-05's measurement trap is real and reproduces
exactly: `grep -o -w DOCUMENTED_SINCE_MOVE` returns 0 hits in `b02ohu` while the substring form returns 1,
so the boundary-safe requirement in E-01 is load-bearing rather than pedantic; `b02ohu` names nine of the
twelve, does not name `LANE_INTEGRATION_MOVED` or `SUPERSEDED_SINCE_MOVE` at all, and is `- Status:
reviewed` (not approved), which is what makes OQ-01's refusal to declare an `executed:` dependency edge the
right call rather than a convenience. F-08's baseline reproduces at review HEAD: `119 passed in 6.05s`.
OQ-02's fixture facts are exact (`captured_at_head: 1ecc5891f6bf...`, `symbol_count: 34`, no `.py` reader).

THE ONE SERIOUS CLASS OF DEFECT IS THAT THE PLAN VALIDATED ITS OWN CITATIONS BY FILE EXISTENCE WHILE
CORRECTING A FILE FULL OF CITATIONS THAT FAIL BY SYMBOL. That is PR-401, and it is the finding I would keep
if I could keep only one, because the plan would have committed the exact defect it exists to remove. E-02
instructed the executor to preserve "the two replacement-coverage pointers" and certified each with the
parenthetical "(that file EXISTS, measured)". The block embeds SIX pointers, and file existence is the wrong
predicate for all of them. Measured by `def`/`class` definition: four resolve (`ResolvePlanPathTypedTests`,
whose 13 tests I ran and which pass; `CanonicalRunsRootTests`, in this same file; `ShouldColorGridTests` in
`tests/test_term.py`; `SharedColorDecisionTests`, in this same file), and two do NOT. `tests/test_artifact_audit.py`
exists but contains only `TestAllowedLifecyclePairs` and `TestArtifactAuditEngine`: there is no
`EvidenceIndexTests`, and `test_it_passes_an_explicit_timeout` and `test_a_timeout_is_unknown_not_a_pass`
have `defs=0` with their ONLY two occurrences in the entire repository being the comment lines the plan was
about to preserve verbatim. `tests/test_graduation_dispatch.py::RefusalContentTests` names a file that is
ABSENT outright. So "preserve these because they point at coverage that EXISTS" would have MINTED TWO NEW
STALE CITATIONS, of precisely the shape open item `pn7rw3` was filed to record, inside the plan whose stated
purpose is deleting misleading prose. I also confirmed the two names were never merely renamed:
`git log -S test_it_passes_an_explicit_timeout` shows them added in `70792b53` and removed in `19313eed`,
the same trim that took the harness.

THE SECOND HIGH IS THAT E-02 COULD NOT SATISFY V-02, which is a defect visible only by reading the two
checklists against each other rather than either alone. E-02 deleted "each assignment with its own preceding
block"; V-02 demanded "zero occurrences of each deleted name, including in comments". But
`SUPERSEDED_SINCE_MOVE` has TWO word-boundary occurrences, and the second is roughly 4500 lines below the
first, inside the docstring of the LIVE and PASSING `SharedColorDecisionTests`: "This symbol is enumerated in
`SUPERSEDED_SINCE_MOVE` above, which exempts it from the byte-identical pre-move capture". No block-scoped
deletion reaches it. An executor following E-02 literally would leave a live class pointing at a name the
file no longer defines, then fail V-02's own bar, with the only two exits being an undeclared edit to a live
class or a quietly weakened validation. That is PR-402.

PR-403 cuts in BOTH directions, which is why it is worth stating carefully rather than as "the docstring is
wrong". F-07 invites deleting the "THREE INDEPENDENT ASSERTIONS" framing wholesale, and the three assertions
do not share a truth value. Assertion 1 (fingerprint equality) is dead and the text already concedes it.
Assertion 2 (OBJECT IDENTITY, "both runners must resolve each moved name to the SAME object") is LIVE and
genuinely enforced, by `CrossHostSuccessBarEqualityTests.test_cross_host_success_bar_constants_and_tokens`
and `DriverErrorUnificationTests`, across 54 `assertIs` call sites in this file, which I counted by AST and
whose relevant blocks I read; a rewrite that dropped the framing would delete the file's one remaining TRUE
structural claim while leaving the suite green, so nothing would catch it. Assertion 3 is dead for the
34-symbol set but survives narrowly in two named tests I located
(`test_no_divergent_codefined_constants_in_runner_shared`, `test_add_output_mode_flags_not_reforked_in_hosts`),
so it needs narrowing rather than deletion. Separately F-07 stops at the docstring while the SAME false
counts recur as comments one screen lower: "The 4 symbols that take an injected dependency" over a 7-entry
`INJECTED` (the file's own next comment already concedes "THE COUNT IS 7, NOT THE PLAN'S 4"), and "The 2
symbols that could NOT move, with the reason pinned in `UnmovableSymbolTests`" over a 1-entry `UNMOVABLE`
naming a class with `defs=0`. Fixing only the docstring leaves a reader the same wrong number in the same
file, and both comments are inside the plan's one declared path.

PR-404 is a precision improvement to an out-of-scope routing the plan already got right. Its Deferred section
correctly sends production-file guard citations to `pn7rw3` without widening scope; I measured the specific
surviving lines so the next reader of that item does not repeat the work, and named each by SYMBOL:
`runner_shared.should_color`'s docstring cites `test_exactly_one_definition_package_wide` (`defs=0`), and
three sites cite `LaneIntegrationExtractionTests` (`defs=0`) - `oc_runipd.integrate_lane_branch`'s docstring,
`runner_shared.integrate_lane_branch`'s docstring, and the module-level decision comment preceding
`INTEGRATION_CAUSE_TOKEN_PREFIX = "[aw-integration-cause="`.

PR-405 IS MY OWN DEFECT, RECORDED BECAUSE A REVIEW THAT INTRODUCES A REGRESSION AND DOES NOT SAY SO IS WORSE
THAN ONE THAT FINDS NOTHING. The plan arrived with ZERO lint findings. My first pass at PR-404 wrote five
bare `path:line` citations with no durable anchor, and `--phase review-finalize` then reported five fresh
`IPD-C801` advisories that the authored plan did not have. I resolved each line to its enclosing symbol by
AST and rewrote all five to lead with the symbol or a quoted content string, keeping the offset only as a
trailing convenience; the advisory count is back to zero. This is exactly the rule the plan's own
"Project conventions discovered" section cites (spec `ipd-structure-and-linting` Section 10.2), so I broke a
convention the plan had already recorded.

I ALSO CHECKED THREE THINGS THE PLAN DOES NOT CLAIM, none of which produced a finding. First, whether
deleting a module-level name could break a cross-module import: four test modules do
`from tests.test_runner_shared import ...`, but every imported name is a helper (`_passing_suite`,
`_write_run_state`), never one of the three tuples, so V-04's bare-suite requirement is the right guard and
no additional one is needed. Second, whether `b02ohu`'s E-06 might also delete the comment BLOCKS and so
collide beyond the one acknowledged name: it does not mention comment blocks at all, which makes the
idempotency in OQ-01 sufficient. Third, whether the `_run_git` timeout capability the deleted pointer claims
is covered anywhere else: `timeout` appears nowhere in `tests/test_artifact_audit.py`, so deleting that
pointer loses no reachable coverage and creates no gap to carry, which is what makes deletion (rather than
re-pointing) the correct disposition.

One residue is worth naming honestly: after PR-401, the `_run_git` timeout and
`describe_unresolved_plan_selector` capabilities have no located behavioral coverage. That is a PRE-EXISTING
state created by `19313eed`, not something this plan causes, and this plan cannot fix it within one declared
test-file path; the deletion makes it VISIBLE instead of papered over by two citations that resolve to
nothing. It belongs to `pn7rw3`'s neighbourhood, which the plan already routes.

Bare suite not re-run at review: this review changed only plan and review records, no code. The plan's own
V-04 requires a bare `python3 -m pytest` at execution, and `tests/test_runner_shared.py` reports
`119 passed in 6.05s` at review HEAD.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | IN-SCOPE | Rubric D (anti-regression), G (executability) | `tests/test_runner_shared.py:298` (`# tests/test_artifact_audit.py::EvidenceIndexTests`), `tests/test_runner_shared.py:322` (`RefusalContentTests`); `grep -rn -E "^\s*(def\|class) EvidenceIndexTests"` returns `defs=0`; `tests/test_artifact_audit.py` defines only `TestAllowedLifecyclePairs` and `TestArtifactAuditEngine` | E-02's preserve instruction validated a coverage pointer by FILE existence, not by SYMBOL resolution, and certified two unresolvable pointers as "(that file EXISTS, measured)". Preserving them would mint two new stale citations of exactly the shape open item `pn7rw3` records, inside the plan whose purpose is removing misleading prose. Six pointers are embedded, not two: four resolve, two do not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now resolves each pointer by `def`/`class` definition, preserves the four that resolve, and DELETES the two that do not. V-02 requires a pasted per-pointer resolution table and explicitly refuses a `Path.exists()` check as evidence. |
| PR-402 | HIGH | IN-SCOPE | Rubric G (executability), E (verification) | `grep -n -w SUPERSEDED_SINCE_MOVE tests/test_runner_shared.py` returns 2 hits: the assignment and `class SharedColorDecisionTests`'s docstring ("This symbol is enumerated in `SUPERSEDED_SINCE_MOVE` above") | E-02 deleted assignments with their preceding blocks; V-02 demanded ZERO occurrences of each name including comments. One reference lives ~4500 lines away inside a LIVE passing class's docstring, unreachable by any block-scoped deletion, so E-02 as written could not satisfy its own V-02. The executor's only exits were an undeclared edit to a live class or a weakened validation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now names the surviving reference and requires the clause restated without the dead name, preserving the class and its test; V-02 requires the new docstring text pasted and the test shown passing. |
| PR-403 | MEDIUM | IN-SCOPE | Rubric D (do not freeze accidental behavior), F (honest documentation) | AST count of 54 `assertIs` sites; `CrossHostSuccessBarEqualityTests.test_cross_host_success_bar_constants_and_tokens` at `tests/test_runner_shared.py:418`; `len(INJECTED)==7` vs the comment "The 4 symbols that take an injected dependency"; `UnmovableSymbolTests` `defs=0` | F-07 understates and overstates in different directions, so E-03 could destroy a true claim while leaving a false one. The three docstring assertions do not share a truth value: 1 is dead, 2 (OBJECT IDENTITY) is LIVE and enforced across 54 `assertIs` sites, 3 survives narrowly in two named tests. A wholesale drop would silently delete the file's one true structural claim with the suite staying green. F-07 also stops at the docstring while the same false counts recur in two in-file comments within the declared path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now dispositions the three assertions individually (keep identity, narrow no-re-definition, drop fingerprint) and corrects the `INJECTED` and `UNMOVABLE` count comments. V-03 requires a per-assertion disposition and makes silently dropping the identity property a FAILED validation. |
| PR-404 | LOW | IN-SCOPE | Rubric G (follow-up ownership) | `git grep -n test_exactly_one_definition_package_wide`; `runner_shared.should_color` docstring; `oc_runipd.integrate_lane_branch` docstring; `runner_shared.integrate_lane_branch` docstring; the comment preceding `INTEGRATION_CAUSE_TOKEN_PREFIX = "[aw-integration-cause="` | The plan correctly routes production-file guard citations to `pn7rw3` without widening scope, but names none of them, so the next reader re-measures. Four specific production citations name tests with `defs=0`, and deleting this file's copy removes only the test-side instance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 and expanded the Deferred row to name all four sites BY SYMBOL, with no scope change. |
| PR-405 | LOW | IN-SCOPE | Spec `ipd-structure-and-linting` Section 10.2 (`IPD-C801`) | `aw ipd lint --phase review-finalize` reported 5 fresh `IPD-C801` advisories after my PR-404 edit; the authored plan had 0 | SELF-INFLICTED AT REVIEW. My first PR-404 text cited four production sites by bare `path:line` with no durable anchor, introducing five advisories into a plan that arrived clean, and breaking a convention the plan's own Step 0 section already records. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved each line to its enclosing symbol by AST and rewrote all five citations to lead with the symbol or a quoted string, offset trailing only. `review-finalize` advisory count back to 0. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the two unresolvable coverage pointers (`EvidenceIndexTests` with its two tests, `RefusalContentTests`) be preserved as the plan instructed, re-pointed at whatever now covers those capabilities, or deleted? | DELETE them, and say in the evidence that they were deleted as unresolvable. | (a) Preserve verbatim as authored: rejected, it mints a stale citation inside a plan that exists to remove one. (b) Re-point at real coverage: rejected, because there IS none to point at - `timeout` appears nowhere in `tests/test_artifact_audit.py` and `tests/test_graduation_dispatch.py` does not exist, so any substitute would be invented. (c) File a new backlog item for the missing coverage: rejected as premature; the gap is pre-existing residue of `19313eed` and sits in `pn7rw3`'s neighbourhood, which the plan already routes. | `grep -rn -E "^\s*(def\|class) EvidenceIndexTests" --include='*.py'` returns `defs=0`; `test_it_passes_an_explicit_timeout` and `test_a_timeout_is_unknown_not_a_pass` have `defs=0` with their only 2 repository occurrences being the comment lines themselves; `git log -S` shows both added in `70792b53`, removed in `19313eed`; `.aw/records/backlog/open/20260928-pn7rw3-...backlog.md` names this exact defect class | yes |
| D-2 | E-03 could drop the whole "THREE INDEPENDENT ASSERTIONS" framing. Should it? | NO. Disposition each assertion separately: drop 1, KEEP 2 (object identity), narrow 3. | (a) Drop all three, the reading F-07 invites: rejected, it would delete a property 54 `assertIs` sites actually enforce, and no test would fail, so nothing would catch the loss. (b) Keep the framing as-is and fix only the counts: rejected, assertion 1 is genuinely dead and assertion 3 genuinely over-claims its reach. | AST count of 54 `assertIs` sites in `tests/test_runner_shared.py`; `CrossHostSuccessBarEqualityTests.test_cross_host_success_bar_constants_and_tokens` and `DriverErrorUnificationTests` read and confirmed to assert cross-host identity; `test_no_divergent_codefined_constants_in_runner_shared` and `test_add_output_mode_flags_not_reforked_in_hosts` located as assertion 3's narrow survivors | yes |
| D-3 | The `IPD-Z602` density advisory now fires on E-02, which my PR-401/PR-402 fixes grew. Split E-02 or keep it whole? | KEEP IT WHOLE, with the reasoning recorded in the gate. | (a) Split into delete-tuples / decide-pointers / reconcile-docstring: rejected on a mechanical ground, not a convenience one. The pointer decision cannot follow the deletion, because deleting the block is the moment the pointers are destroyed. The docstring reconciliation cannot follow either, because `SUPERSEDED_SINCE_MOVE` has exactly 2 word-boundary occurrences and V-02's zero-occurrence bar is unreachable while one survives, so the first item would fail its own validation. (b) Weaken V-02 to permit the leftover: rejected, that trades a real guard for a lint number. | `aw ipd lint --phase review-finalize --json` detail on E-02; `grep -n -w SUPERSEDED_SINCE_MOVE` = 2 occurrences; the linter's own contract that a passing count-based size check does not clear conceptual density (`plan-review.md` Structural preflight) | yes |
| D-4 | OQ-02 (retire the 153KB unreferenced fixture?) is `open`, `Blocking: no`, `Owner: human`. Answer it at review, or leave it? | LEAVE IT OPEN and do not treat it as a `NO-GO` condition. | (a) Resolve it myself as "keep": rejected, it is a judgement about what historical evidence the repository wants, which `AGENTS.md` assigns to the human, and the plan's `Carrier-Declined` reasoning for it is sound. (b) Escalate to `Blocking: yes`: rejected, it would gate a low-priority followup on a question whose either answer leaves this plan unchanged. | Maintainer ruling of 2026-09-10 (plan `qhy3i3` OQ-01) that a non-blocking open question does not make a plan `NO-GO`, recorded in `plan-review.md`; the fixture is untouched and undeclared by this plan, confirmed `symbol_count: 34`, `captured_at_head: 1ecc5891`, zero `.py` readers | yes |
