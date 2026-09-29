# Review findings: plan h8e3sm

- Subject-Id: h8e3sm
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `0f606374` in an isolated worktree. Structural preflight `aw ipd lint --phase author`
reported `clean` / `conforming` before any edit; re-run at `--phase review-finalize` after revisions, also
clean. No pre-review snapshot was owed: the plan was committed and unmodified. Bare suite at review HEAD:
`3246 passed, 2 skipped, 3 warnings in 47.07s`, matching the plan's F-11 baseline exactly. NO RECORD WAS
RENAMED AND NO CITATION WAS EDITED by this review; the one mutating command I ran (`aw rename specs
--to-id6 --apply --no-commit` on the real spec two, to test the plan's central refusal claim) exited 2 and
renamed NOTHING, which `git status --porcelain` confirmed empty immediately afterwards, so no revert was
needed and none was performed.

THE PLAN IS UNUSUALLY WELL EVIDENCED AND ITS CENTRAL CLAIMS ALL REPRODUCE. The corpus census is exact (38
specs, 19 without `- Id:`, exactly 2 live and both `deferred`), `aw specs check` reports `all specs conform.`
at exit 0 so this is genuinely a reachability change and not a conformance fix, the stamped
`cutovers.spec_id6` is `2026-08-29` so both 2026-07 specs are legitimately grandfathered, and the payoff is
real and observable: `aw attention --format json` emits `"id": ""` for exactly those two specs, each carrying
a live `todo` gate (`ju93oc` and `m15n3k`) and `attention_class: blocked`. The refusal is real (exit 2,
nothing renamed), the guard is genuinely gated on `update_refs` so `--no-refs` bypasses it as described, both
legacy prefixes are unique so no short-handle rewrite is skipped, the commit-pinned permalink in `en5c8i`
exists and is protected by `_PINNED_PERMALINK_RE`, and all four cited precedent commits say what the plan
says they say, including `4c3aa79f`'s `53 files changed, 97 insertions(+), 97 deletions(-)` whose equal
counts are the signature of a pure path repair.

THE PLAN'S JUDGEMENT IS ALSO RIGHT WHERE IT MATTERS MOST. Its per-occurrence classification, its refusal to
rewrite historical `.agents/docs/specs/` paths, its refusal to touch a pinned permalink or a quoted
transcript, its decision to leave the 17 terminal specs grandfathered, and its refusal to build a bulk
repair tool are each correct and each properly reasoned against repository evidence rather than preference.

FOUR DEFECTS WERE FOUND, all in scope reconciliation and stale measurement rather than in the approach. The
most serious is that the plan's `- Scope-Paths:` does not account for four of the 21 files the rename tool
would rewrite, which matters because the runner's finalize gate reconciles declared against actual.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | IN-SCOPE | G (executability) / A (correctness) | plan `- Scope-Paths:` (17 entries) versus both `--to-id6` previews; `.aw/records/plans/executed/20260723-instsafe-05-kemhdg-...`, `...20260101-instsafe-07-qrokie-...`, `...20260726-conformance-harness-00-hypynh-...` | Reconciling the two previews against the declared scope at review: the tool names 21 files, 17 are covered and FOUR are not. Three are LEAVE-only historical `.agents/` citers (verified by reading each) and so correctly need no declaration; the fourth is THIS PLAN'S OWN FILE, which the tool would rewrite in 3 places and which E-02 classifies LEAVE but which the scope check never mentions. The plan's "Over-scope: none. Every declared path is touched" is true in one direction only and says nothing about files the tool would touch that are undeclared, so an executor meets the finalize scope gate with no prepared answer | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | A new Scope-check bullet enumerates all four, states which three are correctly undeclared and why, identifies the plan's own file as the fourth, and explicitly forbids "fixing" the reconciliation by adding LEAVE-only citers to `- Scope-Paths:` |
| PR-602 | MEDIUM | IN-SCOPE | F (honest documentation) / E | plan F-04, F-05, E-01 Expected outcome, OQ-02; `artifact_rename.find_unrewritable_path_citations` | The refusal-set counts are already stale: authoring recorded 11 blockers for spec one, review measures TWELVE, because the plan file ITSELF now cites the spec through a `.agents/docs/specs/` path and became its own twelfth blocker. The class split is correspondingly 7 stale plus 5 historical, not 7 plus 4, and the plan's "all 18 blockers" is now 19. The plan does warn that the refusal set is a live property, which is exactly right, but it then prints the stale figures as the Expected outcome an executor confirms against | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 and F-05 carry the re-measured counts and name the cause; E-01's Expected outcome drops the counts as a target, states that the CLASS SPLIT rather than the count is the property that must hold, and records both the authoring and review measurements so a third number is not read as a defect; OQ-02's dependent count corrected |
| PR-603 | MEDIUM | IN-SCOPE | F / G | plan conventions "THE REFERENCE SCAN IS NARROWER", E-05; `artifact_core.REFERENCE_SCAN_ROOTS` | The plan states "root-level text files are not scanned". FALSE: the constant's 19 entries include `DECISIONS.md`, `README.md` and `ARCHITECTURE.md` BY NAME. This matters concretely because `DECISIONS.md` is one of this plan's own KEEP citers, so the plan mis-describes the status of a file it edits. The plan also attributes the constant to `artifact_refs`, which only re-exports it as a default argument, and does not explain that `README.md` is in the roots yet skipped by `_SKIP_NAMES`. The GAP the plan relies on for E-05 is nonetheless real: `agent_workflows/**`, `tools/**`, `docs/**`, `.aw/system/**` and `TODO.md` are all genuinely absent, verified individually | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The convention bullet now gives the real root list including the three named root files, notes the `_SKIP_NAMES`-versus-roots interaction, corrects the owning module to `artifact_core`, and preserves the (verified) gap list that justifies E-05 |
| PR-604 | LOW | IN-SCOPE | E (testing) / G | plan E-05; review-time `git grep` sweep | E-05 is framed on the `iyi4hc`/`d6b2fa00` precedent in which the out-of-root sweep DID find hand-fixable citations, leaving an executor expecting to find some. Measured at review: a `git grep -l` for both legacy prefixes excluding every scanned tree returns NO files, so this conversion is expected to need zero out-of-root fixes. Without that expectation recorded, an empty sweep reads as a sweep done wrong | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 records the review sweep result as the expectation, keeps the obligation to re-run because the property is live, and directs that a hit found later be reported as a change since review rather than assumed to be a review miss |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is owed
(`check.review-finding-unescalated` satisfied vacuously). No BLOCKER was found.

OQ-01 WAS RESOLVED AT REVIEW AND ITS FIELDS NOW MATCH ITS PROSE. It carried `- Status: open` and
`- Owner: maintainer` while its own rationale began "RESOLVED FROM REPOSITORY EVIDENCE", which asserted an
unanswered maintainer question over a point the repository has settled three times (`AGENTS.md`'s closed list,
the reviewed-and-approved `iyi4hc` convention, and commit `4c3aa79f`'s maintainer-attested repair of the same
defect class at 5x the volume). I verified all three and closed it as `resolved` / `Owner: reviewer`, recording
the decision as D-1. OQ-02 CORRECTLY STAYS OPEN and I did not presume it: its answer is a priority judgement
about whether a cosmetic empty handle justifies a records change at all, which is the maintainer's to make.
Both are non-blocking, so neither makes the plan `NO-GO` (maintainer ruling of 2026-09-10).

WHAT I DELIBERATELY DID NOT FLAG. The plan's four `Carrier-Declined` rows each genuinely decide rather than
defer and each states what is left unbroken, which is the repository's bar. Its refusal to convert the 17
terminal specs is the backlog item's own recommendation and is correctly reasoned (nothing will newly gate,
join, or select on a terminal spec). Its declining of a bulk citation-repair tool correctly points at
`68hdic` and `2wmwf7` as live owners of the detection question rather than inventing a carrier. Its negative
fence is the strongest part of the plan and I added nothing to it. Its spec-sync section correctly explains
that the three `.spec.md` paths in scope are rename and citation targets rather than contract amendments,
which is exactly the declaration the runners' spec-edit announcement needs. And its E-06 instruction to
compare check finding SETS while expecting NO improvement is precisely right, since the specs were
grandfathered rather than nonconformant.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | OQ-01 asked the maintainer to authorize repairing stale path citations in 5 executed plans and 3 reviews, while its own prose called itself resolved. Resolve it, or leave it open for the maintainer? | Resolve it at review as `resolved` / `Owner: reviewer` | Leaving it `open` with `Owner: maintainer`, rejected because the workflow forbids asking a human what the repository already answers, and a false `Owner: maintainer` on a resolved question is the exact anti-pattern the plan-review contract calls out (it passes every mechanical check while misrepresenting who decided). Escalating it to `Blocking: yes`, rejected because the answer changes the plan's scope, not its validity | Verified at review: `AGENTS.md`'s closed list excludes path citations; `iyi4hc` states the reference-rewriting convention and was approved carrying 20 executed plans; `git show --stat 4c3aa79f` gives `53 files changed, 97 insertions(+), 97 deletions(-)` attesting "Paths only; no record's claims change (maintainer-approved)"; `084689ef` is the recorded undo of the one over-reach | yes |
| D-2 | PR-601: four files the tool would rewrite are undeclared. Add them to `- Scope-Paths:`, or document why they are correctly absent? | Document; do NOT add them | Adding all four, rejected because three are LEAVE-only citers that are never edited, so declaring them would assert an intent to edit records this plan must not touch, and the fourth is the plan's own file whose modification is governed by the lifecycle rather than by citation scope. Declaring a file you will not edit also trips the finalize gate's declared-but-unmodified arm, needing a `--scope-ack` for nothing | Read each of the three executed plans at review and confirmed every occurrence is a historical `.agents/docs/specs/` path; E-02's existing rule already classifies this plan's own occurrences LEAVE | yes |
| D-3 | OQ-02 remains open and recommends NOT converting if OQ-01 is refused. Should review resolve it too, now that OQ-01 is resolved? | No. Leave it open, owned by the maintainer | Resolving it as moot, rejected because it is not moot: it encodes a genuine priority judgement (a `low` item whose only measured cost is a cosmetic empty handle) that survives OQ-01's resolution, and the maintainer may still decide the conversion is not worth the records churn. Review verified the cost claim rather than the value judgement | The measured cost is exactly what F-10 says (two `"id": ""` rows in the attention view, no broken workflow), and the item is `- Priority: low`; deciding whether that justifies the change is a scope/priority call the workflow reserves to the human | yes |
| D-4 | The plan has 6 E-items in 4 groups touching 17 declared paths. Does it breach right-sizing? | No. Keep it whole | Splitting the measure/classify phase from the edit phase, rejected because that is the precise coupling that keeps the conversion honest: E-03 and E-04 are authorized ONLY by E-02's classification, and separating them into different plans would let edits run against a classification nobody re-derived. The linter raised no density advisory | The rubric's density diagnostics applied per item (each E-item is one concern over one pass), plus the plan's own stated cohesion rationale which I checked rather than accepted; `aw ipd lint` clean at both phases | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
