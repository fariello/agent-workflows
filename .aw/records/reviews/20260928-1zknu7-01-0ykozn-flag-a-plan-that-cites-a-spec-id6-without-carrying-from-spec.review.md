# Review findings: plan 0ykozn

- Subject-Id: 0ykozn
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `100a705f` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after revision. No pre-review snapshot was owed: the plan was committed and byte-identical to the
lane input. No production code was modified by this review; every post-change behavior claim was
measured by running the shipped predicates and by probing a throwaway git repository built inside a
Python `tempfile.mkdtemp`.

THE PLAN DIAGNOSES A REAL AND WIDENING STRUCTURAL GAP, AND ITS CENTRAL MEASUREMENT IS CORRECT AND
REPRODUCED. `check_spec_criteria_uncovered` returns ZERO findings repo-wide; `c4gd2h` declares 10
acceptance criteria and its `plans_by_spec` bucket is empty, so the rule `continue`s before parsing
anything; feeding the plans that cite `c4gd2h` on a front-matter bullet through the same predicate
yields 9 matched criteria and `A9` uncovered. So the plan's claim that the missing EDGE rather than a
missing requirement parser is the binding constraint holds exactly as written. F-08's dating claim also
holds: `git show -s --date=short 8c437188` is `2026-08-30` and the `runstop` plans are dated
`2026-08-29`, so the largest edge-less cluster genuinely predates the field.

Two of the plan's counts had drifted upward between authoring and review, in the direction that
strengthens its own argument: 58 whole-document mentions of `c4gd2h` (plan said 56), 19 front-matter
citers (plan said 18), and 92 whole-tree naive findings (plan said 91). All were corrected in place.

WHAT REVIEW FOUND IS ONE DESIGN DEFECT THAT WOULD HAVE MADE THE ENTIRE DELIVERABLE INERT, plus three
executor-trap defects in the E-item instructions. The plan's goal, severity choice, scope fences, and
deferral reasoning needed no correction.

**THE AUTHORED COMMIT-SCOPED DETECTOR WOULD HAVE BEEN OBSERVABLE BY NOBODY (PR-501, BLOCKER).** This
is the finding that matters. The plan chose commit-scoping to avoid F-03's unactionable terminal
findings, and that diagnosis is right, but the chosen mechanism makes the finding invisible. A
commit-scoped rule's firing window is exactly the interval between `git add` and `git commit`: probed in
a scratch repository, the staged-diff query returns empty before staging and empty again after the
commit lands. Inside that window there are exactly three consumers and every one of them drops an
`info` finding. `work_cmd._validate_plan_via_engine` `continue`s on `severity == "info"` under its own
comment "advisory nudge, dropped silently", so `aw commit` never prints it.
`check_engine.check_commit_invariants` composes exactly three named rules (`check_status_untooled`,
`check_release_gate_consistency`, `check_scope_drift`) and the new one is not among them, so the
pre-commit hook never reaches it. CI runs `aw check plans` on a clean tree, where the rule fast-returns
`[]`. The plan would therefore have shipped a registry entry, a predicate, a dispatch site, and a test
file that together produce no signal any human or tool ever sees, which is strictly worse than shipping
nothing because it also teaches the next reader that the rule covers this case. The causal error is
identifiable and worth naming: the plan copied `check_status_untooled` for its COMMIT-SCOPING while
copying `check_spec_criteria_uncovered` for its SEVERITY, and those two properties are not
independent. `check_status_untooled` is registered `error`, which is precisely why it has consumers at
commit time. FIXED by scoping to `pending/` on the `check_ipd_draft_ready` precedent, which is the
repository's other `info`-severity pending-plan nudge and scopes itself with `if "pending" not in
p.parts: continue`. Measured equivalence: the pending-scoped predicate reports the SAME 5 plans, so
F-03's unactionability fix is fully preserved while the finding becomes visible on every `aw check
plans` for as long as the plan is editable. Recorded as OQ-03 in the plan with the rejected alternative
(wiring an advisory into the refusal hook) and its reason.

**E-01'S "MIRROR THE TWIN EXACTLY" WOULD HAVE COPIED A LATENT DUPLICATION BUG (PR-503, HIGH).**
Measured on the shipped twin: `set_from_backlog_line("- Status: to-review\n- From-Backlog:\n- Id:
abc123\n", "zzz999")` returns text containing TWO `- From-Backlog:` lines. `_FROM_BACKLOG_LINE_RE`'s
`\S+` value group cannot match an empty value, so the idempotent strip misses the existing line and the
insert adds a second. The resulting duplicate is undiagnosable downstream because
`_ITEM_FROM_SPEC_RE.search` reads only the first match. The correct precedent sits two functions away
in the same module: `set_priority_line` and `set_work_kind_line` use `[^\n]*` and their docstrings state
the reason outright, "Tolerates any value so an existing malformed line is still replaced". FIXED by
pinning the value group and naming those two as the shape to copy. The plan's blanket instruction to
mirror `set_from_backlog_line` "EXACTLY" was narrowed to mirror it on ANCHOR AND CLEARING only, and a
new conventions bullet records that `releases.py`'s five metadata writers do not agree with each other,
so "mirror the twin" is an unsafe instruction in that module.

**E-03'S BULLET PARSER WOULD HAVE SILENTLY EXEMPTED 21 PLANS, INCLUDING ONE CITING `c4gd2h` ITSELF
(PR-502, HIGH).** E-03 said "front-matter lines" without specifying continuation handling. Measured
over the corpus: of 2423 `- Concern:`/`- Scope:`/`- Scope-Paths:` bullets, 238 wrap onto a continuation
line, and on 21 plans a resolvable spec id6 appears ONLY on such a continuation, `jxxec8` among them
with `c4gd2h` as the id. So the obvious single-line implementation is a false-negative bug rather than a
simplification. FIXED by requiring the parser to consume a bullet plus its continuation lines, with the
measurement recorded inline so the requirement is not re-simplified later, and with a V-03 evidence
demand that pins the `jxxec8` case on the real corpus rather than a fixture.

**E-02 CONTAINED TWO CONTRADICTORY INSTRUCTIONS IN ONE ITEM (PR-504, MEDIUM).** It told the executor to
mirror the `from_backlog` handling AND to refuse an unresolvable id6. Measured:
`status_set.apply_status_change` performs NO value validation on `from_backlog` whatsoever, so an
executor following the mirror literally ships no validation and writes exactly the dangling link this
plan's own rule exists to prevent. FIXED by stating the asymmetry explicitly, requiring a comment at the
validation site explaining why the new flag is deliberately stricter than its twin, requiring the id set
to be reached through the same helper E-04 uses rather than constructed twice (P8), and requiring the
refusal to be SKIPPED when the spec-id union is empty so an externally-redirected project cannot fail
every write.

TWO MEASURED DEFECTS IN SHIPPED CODE ARE NOW CARRIED RATHER THAN LEFT AS PROSE. PR-503 and PR-504 each
uncovered a real latent bug in the `From-Backlog` setter that this plan correctly should not fix.
Both were added to `## Deferred` with carrier obligations, and V-06 now requires the minted backlog
id6s as pasted evidence, so the rows cannot decay into bare promises. Verified NOT live today: no
artifact in the corpus carries an empty-valued `From-Spec` or `From-Backlog` line, so nothing is
corrupt right now and the classification as latent is honest.

Three smaller corrections were applied without separate findings. F-06 listed `7dz3wv` among its live
pending findings; it is in `executed/`, so under the revised pending scope it is correctly not live, and
OQ-01's resolution carried the same error in its supporting example. E-05 named the dispatch branch
`record_type == "plan"` where the code reads `"plans"`, and omitted the `include_untracked` argument its
neighbours pass. Every bare `path:line` citation added during review was re-anchored to a durable symbol
or quoted string after `aw ipd lint` reported `IPD-C801`, and all seven anchors were verified to resolve.

Scope fences were tightened to forbid reverting each fix: no reversion to a staged-diff rule, no `\S+`
value group, no dropping continuation handling, no retrofitting validation onto `--from-backlog`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | BLOCKER | IN-SCOPE | C. Architecture and operability | `work_cmd._validate_plan_via_engine` (`work_cmd.py:291`, `continue  # advisory nudge, dropped silently`); `check_engine.check_commit_invariants` (`check_engine.py:3403`); `.github/workflows/tests.yml:172` | A COMMIT-SCOPED `info` rule is observable by nobody. Its firing window is only between `git add` and `git commit`, and all three consumers in that window drop `info`: `aw commit` by severity, the pre-commit aggregator by composition, CI by timing on a clean tree. The authored design would have shipped an inert rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-scoped the detector to `pending/` on the `check_ipd_draft_ready` precedent. Same 5 live findings measured, F-03's unactionability fix preserved, finding now visible on every `aw check plans`. Recorded as OQ-03 with the rejected alternative. |
| PR-502 | HIGH | IN-SCOPE | A. Correctness | 238 of 2423 front-matter bullets wrap; 21 plans cite a resolvable spec id6 ONLY on a continuation line, including `jxxec8` citing `c4gd2h` | E-03's single-line bullet reading would silently exempt 21 plans, one of them citing the very spec the plan is about. A false negative, not a simplification. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now requires consuming a bullet plus its continuation lines; the measurement is recorded inline and V-03 demands the `jxxec8` case be proven on the real corpus. |
| PR-503 | HIGH | IN-SCOPE | A. Correctness | `set_from_backlog_line("- Status: to-review\n- From-Backlog:\n- Id: abc123\n", "zzz999")` yields TWO `- From-Backlog:` lines; `set_priority_line` on the same shape yields ONE | "Mirror `set_from_backlog_line` EXACTLY" would copy a latent duplication bug: `\S+` cannot match an empty value, so the strip misses the line and the insert duplicates it. The duplicate is undiagnosable because readers `search` only the first match. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Pinned `_FROM_SPEC_LINE_RE`'s value group to `[^\n]*`, named `set_priority_line`/`set_work_kind_line` as the precedent, narrowed the mirror instruction to anchor and clearing only, and added a conventions bullet recording that the module's five writers disagree. |
| PR-504 | MEDIUM | IN-SCOPE | B. Security and privacy (input validation) | `status_set.apply_status_change`'s `from_backlog` block performs no value validation | E-02 told the executor both to mirror `from_backlog` handling and to refuse an unresolvable id6. The twin validates nothing, so a literal mirror ships no validation and writes the dangling link this plan's rule exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states the asymmetry, requires an explanatory comment at the validation site, requires the shared id-set helper (P8), and requires the refusal to be skipped on an empty union. V-02 demands the hunk as evidence. |
| PR-505 | MEDIUM | UNDER-SCOPE | G. Plan executability | Two latent defects measured in shipped code during PR-503/PR-504 with no carrier in the plan | The plan measured real bugs in `releases._FROM_BACKLOG_LINE_RE` and in `--from-backlog`'s absent validation and correctly declined to fix them, but recorded nothing, so the knowledge would have been lost on execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added two `## Deferred` rows with carrier obligations and made V-06 require the minted backlog id6s as pasted evidence. Verified neither defect is live today (no empty-valued line exists in the corpus), so the latent classification is honest. |
| PR-506 | LOW | IN-SCOPE | Evidence accuracy | `rg -l -- c4gd2h` -> 58 (plan said 56); front-matter citers 19 (plan said 18); naive whole-tree 92 (plan said 91) | Three counts had drifted upward since authoring, all in the direction that strengthens the plan's own argument. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in the Concern, F-01, F-02, F-03, F-05 and the scope check, with HEAD `100a705f` recorded and re-derivation required at execution. |
| PR-507 | LOW | IN-SCOPE | Evidence accuracy | `7dz3wv` resolves to `.aw/records/plans/executed/`, not `pending/` | F-06 and OQ-01 both cited `7dz3wv` as a live pending finding. Under the revised pending scope it is correctly not live. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected both sites; the mechanism claim in OQ-01 is unaffected and `ghna7l` carries the same example. |
| PR-508 | LOW | IN-SCOPE | G. Plan executability | The dispatch branch reads `record_type == "plans"`; neighbours pass `include_untracked=include_untracked` | E-05 named the branch `"plan"` (singular) and omitted the visibility argument its neighbours pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the branch label and required the argument to be passed. |
| PR-509 | LOW | IN-SCOPE | Citation durability | `aw ipd lint` reported `IPD-C801` on a bare `status_set.py:1040-1046` offset added during review | Bare line offsets expire before execution and then misdirect the executor to unrelated valid code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-anchored all seven citations added at review to durable symbols or quoted strings, and verified each resolves. Lint reports conforming. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the detector stay commit-scoped as authored, or be re-scoped so its `info` finding is observable? | Re-scope to `pending/`, copying `check_ipd_draft_ready` | (a) keep commit-scoping and accept invisibility, rejected because the deliverable would be inert; (b) keep commit-scoping and add the rule to `check_commit_invariants` so the pre-commit hook sees it, rejected because that is a refusal surface and OQ-02 already settled that this rule must not block; (c) raise the severity to `warning` so existing consumers surface it, rejected because `artifact_core.drift_exit_code` exempts only `info`, so `warning` would fail the gate exactly as `error` does and F-06 measures that most live findings are conforming plans | `work_cmd._validate_plan_via_engine` drops `info`; `check_engine.check_commit_invariants` composes three rules not including this one; `.github/workflows/tests.yml:172` runs on a clean tree; `check_engine.check_ipd_draft_ready` is the `info` pending-plan precedent; pending-scoped predicate measured to report the same 5 plans | yes |
| D-2 | Should this plan also fix the `\S+` duplication bug it uncovered in `releases._FROM_BACKLOG_LINE_RE`? | No; avoid inheriting it, and carry the fix as a backlog item | Fixing it here, rejected as outside the declared concern and a behavior change to a shipped writer on a path no finding measures as live | AGENTS.md scope-fence discipline; verified no artifact carries an empty-valued `From-Backlog`/`From-Spec` line today, so the defect is latent rather than live | yes |
| D-3 | Should E-02 validate its value when its twin `--from-backlog` does not? | Yes, and say in the code why it is stricter | Matching the twin's absent validation, rejected because `check.from-spec-dangling` is `error` severity so an unresolvable write manufactures a gate failure the setter could have prevented | `check_engine.check_from_spec_dangling` registry severity `error`; `status_set.apply_status_change` measured to perform no validation | yes |
| D-4 | Does the plan need a spec amendment? | No | Amending `pqsx96` to add an I-* row for the new rule, rejected following the precedent `check.spec-criteria-uncovered` set by claiming invariant `""` | `check_engine.RULE_REGISTRY["check.spec-criteria-uncovered"]` carries invariant `""` with a comment recording that choice; `25kzda` Section 2.1 governs host run flags, and `aw ipd set` is not one, so `tests/test_run_flag_surface.py` is unaffected | yes |

No `Reversible: no` decision was taken, so no escalation is owed. No finding was left `OPEN` or
`DEFERRED`, so no `- Blocking: yes` escalation question is owed under the gate threshold.
