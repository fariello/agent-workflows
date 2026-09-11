# Review: resolve a setid within the requested type and report candidates per type when it cannot, child w2y5ac (Set setidfix)

- Subject-Id: w2y5ac
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `3e6c6bf4`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0
findings) before semantic review; `--phase review-finalize` conformed after the revisions. No
pre-review snapshot was needed; the plan was already committed.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this
as a near-self-review and worth less than an independent one.

THIS PLAN'S BEST QUALITY IS THAT IT CORRECTED ITS OWN SPEC BY MEASURING, and that correction holds.
Its F-1 and F-2 are exactly right, verified independently: `match_selector('agentadhere', ...,
scoped_type='plans')` returns 7 matches all of type `plans` while the unscoped call returns 13 across
`['backlog','plans','research']`, and the live untyped failure reproduces verbatim as `Validation
error on ...3gr7fk...backlog.md: Status 'approved' is not valid for backlog`. The spec blames the
typed path; the plan proved the typed path resolves correctly for a setid and that the real defect is
on the untyped one. That is the kind of finding that justifies the whole review step, and the plan
also earns credit for refusing to guess a type, for preserving within-type fan-out per `laykok`
E-07, and for insisting on `--dry-run` after its own near-miss.

AND THEN IT DREW ONE MORE INFERENCE THAN THE MEASUREMENT SUPPORTED, WHICH IS THE BLOCKER. From "the
pre-filter narrows `record_types`" the plan concluded that the `Type mismatch` refusal at
`status_set.py:1259-1268` is unreachable dead code, and E-02 instructed the executor to delete it.
The pre-filter narrows which types the RESOLVER is queried about; it does not constrain what
`selectors.resolve` returns for its FIRST precedence rule, the direct path, which matches an existing
file regardless of the type requested, after which the record's type is read from the real path by
`detect_artifact_type`. Measured: `match_selector(<a plan path>, scoped_type='specs')` returns one
match of type `plans`. So the branch fires, and it is the only thing between a type-scoped verb and a
foreign-type artifact.

WHAT DELETION ACTUALLY PERMITS, MEASURED END TO END RATHER THAN ARGUED. On HEAD, `aw specs set
approved <a plan path> --yes --by-human` is refused by that branch: exit 2, file byte-unchanged. With
the branch removed, the same command SUCCEEDS: the plan moved `reviewed -> approved` and its own
history gained `- 2026-09-11 approved (aw set, --by-human): cross-type write`. That is two harms at
once, a cross-type write through a verb the operator invoked for a different tree, and a forged
human-approval attestation on a plan, which is precisely the class of forgery the repository's
`--by-human` speed bump exists to prevent. The vocabulary check offers no protection: 15 statuses are
valid for two or more types, so the overlap is ordinary. And the decisive detail for how this review
weights the finding: the full suite passes with the branch deleted (`5959 passed`, zero failures),
and `grep "Type mismatch" tests/` finds nothing, so the guard is entirely unpinned and E-02 would
have landed invisibly. E-02 is inverted to PIN the branch, E-05's "assert the message appears
nowhere" assertion is replaced by its opposite, and E-01's pin is narrowed to the setid kind with an
explicit note that the path kind is exempt, since the over-generalization is the actual root cause.

TWO FURTHER MEASUREMENTS RE-WEIGHT THE PLAN'S REMAINING WORK. E-04, presented as the residual
ambiguous case after E-03, is in fact the WIDER hole: 15 statuses span types, and `aw set to-review
shared --yes` on a tree holding one plan and one spec was measured transitioning BOTH at exit 0. E-03
covers only the narrower sub-case where a vocabulary error happens to stop the run first. Separately,
E-03 does not need any new CLI surface: the untyped verb already accepts a leading type token
(`status_set.py:1185-1194`), and `aw set plans approved agentadhere --dry-run` previews exactly the 7
plans, so that shipped spelling is what the candidate report should print rather than a new `--type`
flag.

I ALSO STRENGTHENED OQ-01 RATHER THAN RESOLVING IT. The question (should the governing spec's stale
example be amended) stays non-blocking and maintainer-owned, because the plan's deliverables do not
depend on it and a plan editing its own governing spec's problem statement is a reviewer-sanctioned
act. But its stakes changed: the stale example did not merely mislead a problem statement, it
produced an instruction to delete a live safety guard. If the spec is amended, one sentence should say
that scoped resolution filters every selector kind EXCEPT the direct path and that this refusal is
the intended guard for that kind. That sentence would have prevented the worst instruction in this
plan.

WHAT I LEFT ALONE. The untyped-path diagnosis, the refusal to guess a type, the preservation of
within-type fan-out, the `--dry-run` discipline, and the deferral of confirmation-by-default to its
own carrier are all correct. I did update the confirmation cross-reference: `f5pttg` is now carried
by plan `4bc1nd`, reviewed the same day, so E-04 must not implement confirmation a second time.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | IN-SCOPE | B/A (safety guard; attestation integrity) | `agent_workflows/status_set.py:1259-1268`; `agent_workflows/selectors.py:509` (path precedence rule 1); two measured scratch runs | E-02 orders the removal of a refusal it calls dead code. It is LIVE: the direct-path selector kind bypasses the type pre-filter, so `match_selector(<plan path>, scoped_type='specs')` returns a `plans` record. On HEAD `aw specs set approved <plan path> --yes --by-human` refuses (exit 2, unchanged); with the branch deleted it SUCCEEDS, writing the plan to `approved` and appending a forged `--by-human` history line. The suite is green with the branch gone (`5959 passed`) and no test mentions the message, so the deletion lands silently. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-02 inverted to PIN the branch and correct its comment; E-05's third assertion replaced by the refusal pin with a delete-the-branch mutation check; F-3 withdrawn as measured-false; F-7 added; the Concern records the corrected inference. |
| PR-002 | high | IN-SCOPE | G/E (over-claimed pin) | `selectors.resolve` precedence rules 1 versus 2-6; the two `match_selector` probes | E-01's pin was described as proving the typed path type-safe, which is true only for id6/setid/status/stem/substring. Stated that broadly it licenses exactly PR-001's inference, and a reader who trusts it will believe the path kind is filtered too. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 narrowed to the SETID kind with a required docstring stating the path kind is exempt and pinned separately by E-02; the conventions section restated accordingly. |
| PR-003 | high | IN-SCOPE | E (unpinned guard) | `grep "Type mismatch" tests/` -> no matches; suite green with the branch deleted | Nothing pins the type-mismatch refusal, which is why an incorrect instruction to delete it would have produced no test failure. This is a coverage gap independent of PR-001's diagnosis. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 must add the pin and V-02 requires the mutation check that proves it bites. |
| PR-004 | high | IN-SCOPE | A/G (case weighting) | `TYPE_STATUSES` census: 15 multi-type statuses; measured `aw set to-review shared --yes` writing a plan AND a spec at exit 0 | E-04 is framed as the residual case after E-03, but it is the wider hole: the multi-type-valid path is ordinary rather than exceptional, and today it writes silently across types. An executor could reasonably treat E-04 as optional polish. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 carries the census and the reproduced two-type write, states it is the wider hole, and gains a recommendation (refuse and require the type scope, one code path with E-03). |
| PR-005 | medium | IN-SCOPE | C/F (reuse an existing mechanism) | `status_set.py:1185-1194`; `aw set plans approved agentadhere --dry-run` previewing 7 plans | E-03 asks for a "runnable disambiguating command" without naming one, inviting a new `--type` flag when the untyped verb already accepts a leading type token. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires printing `aw set <type> <status> <selector>` and forbids a new flag; F-9 records the measurement; V-03 requires confirming no flag was added. |
| PR-006 | medium | IN-SCOPE | D (contradictory assertion) | E-05's third assertion versus PR-001 | E-05 required asserting the `Type mismatch` string appears NOWHERE. After PR-001 that assertion is either vacuous or actively harmful: it would pressure a later executor into deleting the guard to make a test pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the opposite assertion (a foreign-type path must refuse), plus the E-04 case; V-05 states the removal explicitly. |
| PR-007 | medium | IN-SCOPE | G (stale cross-reference) | plan `4bc1nd` (Set `setterguard`), reviewed 2026-09-10, carrying `f5pttg` | E-04 and the deferral list point at backlog `f5pttg` for the confirmation question, but that item has since graduated into a reviewed plan whose E-01 implements it. Following the plan as written risks two implementations of the same fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04, F-5 and the deferral bullet now name `4bc1nd` as the owner and require the executor to say so; the recommendation avoids the overlapping option. |
| PR-008 | low | IN-SCOPE | E (reproducible baseline) | measured `5959 passed, 3 skipped, 2 xfailed`; identical with the branch deleted | No baseline was recorded, and the predicted environmental `test_reporting_contract.py` failure did not reproduce in a clean worktree. The E-02 experiment's result (green either way) is itself load-bearing evidence and belongs in the plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both measurements written into Required tests, with the three before/after CLI reproductions enumerated. |
| PR-009 | low | IN-SCOPE | G (spec accuracy stakes) | PR-001's measured harm; the spec's Section 1 finding 3 | OQ-01 treated the spec's stale example as bookkeeping. Its real cost is demonstrated: the same inference chain produced an instruction to remove a safety guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 strengthened with the measured stakes and a concrete sentence the amendment should contain; still non-blocking and maintainer-owned. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the type-mismatch branch dead, as the plan asserts? | No. It is live via the direct-path selector kind, so E-02 is inverted from "remove" to "pin". | Accepting the plan's reading (rejected: measured false in two independent ways, the resolver probe and the end-to-end CLI run). Deleting it but adding a different guard (rejected: no simpler guard was needed, since the existing one already refuses correctly and only lacked a test). | `selectors.resolve(root,"specs",<plan path>)` returning `kind=path` with a plans record; `aw specs set approved <plan path>` refused at exit 2 on HEAD | yes |
| D-2 | How severely should the E-02 instruction be rated? | BLOCKER, on the grounds that following it permits a cross-type write AND a forged `--by-human` attestation, both silently. | HIGH (rejected: the repository treats a forged human-approval attestation as a top-tier failure, and this is a normal-path write through a documented verb, not an exotic condition). | the scratch run producing `- 2026-09-11 approved (aw set, --by-human): cross-type write` in a PLAN's history | yes |
| D-3 | Should E-01's pin be described as proving the typed path type-safe? | No: narrow it to the setid kind and require the docstring to name the path-kind exemption. | Leaving the broad wording (rejected: that generalization IS the root cause of the bad E-02 instruction, so leaving it would preserve the trap while fixing only its first victim). | the four-kind probe showing only the path kind reaches a foreign type | yes |
| D-4 | Is E-04 the residual case the plan implies? | No: it is the wider hole, and the item is re-weighted with a recommendation to refuse. | Leaving it as the ambiguous leftover (rejected: 15 statuses span types and the silent two-type write reproduces immediately, so an executor treating E-04 as optional would ship the larger defect). | the `TYPE_STATUSES` census; `aw set to-review shared --yes` writing both types | yes |
| D-5 | Should E-03 get a new `--type` flag or use an existing spelling? | Use the shipped leading-type-token form, `aw set <type> <status> <selector>`. | A new flag (rejected: duplicates a working spelling and adds a second way to say one thing, which this repository's conventions treat as a defect). | `status_set.py:1185-1194`; `aw set plans approved agentadhere --dry-run` resolving 7 plans | yes |
| D-6 | Should the review resolve OQ-01 (amend the governing spec) itself? | No: keep it non-blocking and maintainer-owned, but strengthen it with the measured stakes and the exact sentence to add. | Resolving it and editing the spec (rejected: the spec is `to-review`, and a plan amending its own governing spec's problem statement is a reviewer-sanctioned act, not a reviewer-performed one). Dropping it (rejected: the stale example demonstrably caused real harm in this plan). | the spec's Section 1 finding 3; PR-001's measured outcome | yes |
| D-7 | Does the confirmation cross-reference still point at the right artifact? | No: `f5pttg` graduated into plan `4bc1nd`, so name that plan as the owner. | Leaving the backlog reference (rejected: an executor picking E-04's confirmation-flag option would implement a fix another reviewed plan already owns). | plan `4bc1nd` reviewed 2026-09-10 with E-01 extending the confirmation refusal | yes |
