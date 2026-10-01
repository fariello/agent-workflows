# Review findings: plan jge900

- Subject-Id: jge900
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b640a3c9d`. The plan file was committed and clean
(`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, two advisory `IPD-Z602`
diagnostics) BEFORE semantic review. This plan's own first `- Kind:` bullet reads `child`, so the
`IPD-S407` orchestrator child-row check does not apply.

I RE-DERIVED EVERY LOAD-BEARING MEASUREMENT INDEPENDENTLY rather than trusting the plan's findings.
The plan's central argument is sound and is its real contribution: a typed way to cite a maintainer
ruling already ships, it is broken in two measurable ways, and repairing it is strictly cheaper than
backlog `0szu1p`'s options (a) or (c). That judgement survives review intact. What did not survive is
two implementation properties the plan asserted.

WHAT REPRODUCES EXACTLY:

- F-01 reproduces. `validate_gate_ref('decision', X)` is False for all of `D22b`, `D23b`, `D24b`.
  Parsing `^### D\d+[a-z]*\.` over `DECISIONS.md` yields 156 headings, 156 distinct, and exactly
  those three are rejected by the shipped `^D\d+$`. All 156 are accepted by `^D\d+[a-z]*$`, which
  still rejects `D12-garbage`, `d12`, `D`, `D1x2` and `''`, so the widening buys the fix without
  opening a shape hole.
- F-02 reproduces. `validate_gate_ref('decision', 'D99999')`, `('decision','D0')` and
  `('decision','D86')` are all True while the log's highest heading is `D156` and the numbering
  skips 86, 87 and 89.
- F-03 reproduces, with one detail corrected (PR-006). Driven over `backlog.parse_item` for all 820
  items `backlog._iter_items` yields, exactly 1 carries a gate, and its kind is `artifact`.
- F-04's SOUNDNESS PROPERTY reproduces while its absolute numbers drift (PR-004). A bare
  `\bD\d+[a-z]*\b` extractor measured 4670 hits over 3332 files with 166 unresolved occurrences
  across 27 distinct tokens; the plan said 4315 / 3225 / 145 / 25. Every named false class confirms
  at its site: `IPD-D701` in `ipd_lint.py` ("IPD-D701 is RETIRED and must not be revived"), `D401`
  as a `noqa` code in `tests/__init__.py` and `lifecycle_fixtures.py`, `PR-D02` in a `.review.md`
  findings list. The heading parser yields 156 with ZERO unresolved, so E-02's choice of a
  heading-anchored parser is the right one and is now evidenced rather than asserted.
- F-05 reproduces. `decision` is in `GATE_KINDS`; `backlog.validate_item` enforces kind membership
  then `validate_gate_ref` (`backlog.gate-kind-invalid` / `backlog.gate-ref-invalid`); `specs.check`
  does the same through `specs._read_gate`, emitting `attention.gate-malformed`.
- F-06 reproduces. The implemented attention-registry spec's Section 8.4 bullet reads "`todo`/`decision`
  = stable repo identifiers (a TODO id / `Dnn`)" and its OQ6 asks for exactly these validators, so
  E-01 is conformance rather than a contract change and no spec amendment is owed.
- F-10 reproduces. `nllamb` is `- Status: reviewed` with `- Readiness: no-go` and carries the
  "BLOCKED AT REVIEW: DO NOT IMPLEMENT THIS ITEM AS SPECIFIED" marker. This plan takes none of its
  scope.
- F-11 reproduces. `set_records.promote_question_to_backlog` has exactly one hit repository-wide,
  its own definition. No caller, no test.
- F-12 reproduces. `r61br4` declares `attention_contract.py` but matches zero of `GATE_KIND`,
  `validate_gate_ref`, `_DECISION_ID_RE`, `Gate-Ref`. No dependency edge is owed.

THE TWO FINDINGS THAT CHANGE A DELIVERABLE:

PR-001 is the one that mattered. `DECISIONS.md` is THIS repository's own root log; it is not
installed into a managed target repo, but `check_engine` is. I drove it: `git init` a scratch repo,
`python3 -m agent_workflows install <dir> --yes`, and the resulting tree carries `.agents`,
`AGENTS.md`, `.aw`, `.claude`, `.github`, `.gitignore`, `.gitleaksignore`, `.opencode`, `README.md`
and NO `DECISIONS.md`. `engine.py` contains zero `DECISIONS.md` literals. `.aw/records/backlog/`
contains only `.gitkeep`, so the README E-05 writes is not installed either. With E-02 failing open
to an empty set as specified, an unguarded E-03 would have resolved every `decision` gate in every
managed repo against `set()` and reported each as dangling, and because `artifact_core.drift_exit_code`
exempts only `info`, a `warning` would have driven those repos' `aw check all` to exit 1 on a false
positive they cannot fix. The plan's own fail-open was the right instinct pointed at the wrong
consequence: it treated an absent log as a robustness concern when it is the NORMAL case everywhere
but here. Fixed by requiring E-03 to suppress the rule entirely when the log is absent, adding E-04
case (9) to pin it, adding it to V-03's required evidence and to Required tests, and requiring E-05
to record the limit so a target-repo author is not told they have a check they do not have.

PR-002 is the live-artifact-count rule the review rubric names explicitly. E-02's Expected outcome
read "exactly 156 ids" and V-02 expected 156. `DECISIONS.md` is append-only and grows: measured over
its own history, 153 headings at 2026-09-10, 154 at 2026-09-18 and 2026-09-20, 155 at 2026-09-25,
156 at 2026-09-27 and at today's HEAD, so three arrived in the 17 days before authoring. A count
pinned at authoring is a bar that an unrelated ruling breaks. Fixed by requiring re-derivation at
execution with the measured number demoted to context, requiring V-02 to cross-check the parser
against an independent `grep -c` and assert AGREEMENT plus a floor, and requiring E-04 case (2) to
assert a floor above 100 rather than equality.

THREE STALE MEASUREMENTS CORRECTED. These are PR-004 (the bare-extractor counts above), PR-006 (F-03
named the gated item `yvvf98` where the gate-carrying file's id6 is `adgtqb`; harmless to the
conclusion but it is the citation a later reader would follow), and PR-005, which is the one worth
naming: the deferred section claimed two `deferred` specs "still carry `Gate-Ref: TODO.md`". They do
not. Driven over `specs._read_gate` across all 38 `.spec.md` files, exactly 2 carry a gate and both
are `Gate-Kind: todo` with a bare id6 ref (`ju93oc`, `m15n3k`). The underlying point survives and is
in fact cleaner, since an unresolved `todo` ref is the same hole, but the stated evidence was wrong.
NOTE FOR A LATER READER: backlog `2rnswc` carries the same stale `Gate-Ref: TODO.md` claim in its
SCOPE paragraph. I did not edit it, because a backlog item is not in this review's scope and the
error does not change that item's question; it is recorded here so whoever takes `2rnswc` re-measures
rather than inheriting it.

PR-003 records a consequence the plan did not state: `backlog.validate_item` validates
`- Release-Exempt-Kind:`/`- Release-Exempt-Ref:` through the SAME `GATE_KINDS` and the SAME
`validate_gate_ref`, so E-01 widens the exemption pair too while E-03's sweep reads `Gate-Kind` only.
An exemption citing a nonexistent ruling therefore stays undetected. I did not widen scope to cover
it: no live record carries the pair, and it is the same general hole backlog `2rnswc` already owns.
Recorded as accepted under-scope with a carrier rather than shipped silently.

PR-007 is a one-line convention correction: the plan quoted `addopts` as `-m 'not slow'` where
`pyproject.toml` reads `-m 'not slow and not livecorpus'`.

ON RIGHT-SIZING, which a passing count lint does not clear. Six E-items across two groups, and the
decomposition is genuinely by concern: E-01 is a one-line regex, E-02 a parser, E-03 a registry entry
plus a sweep, E-04 tests, E-05 the recorded answer, E-06 a CHANGELOG line. E-03 is the densest and I
considered splitting the registry entry from the sweep, but they are one deliverable (an unregistered
rule id silently defaults to `error`, so shipping the sweep without the entry would be a defect), and
V-03 verifies both in one evidence pass. No split recommended.

ON THE EXECUTION CONTRACT. The gate already carries resolved-question handling, a declaration-style
scope fence with no prohibited "STOP and report" clause for the out-of-scope case, the paste-the-actual-output
honesty rule, path-scoped `aw commit` with never-push, and a finalize-gated transition that does not
hand-roll a `git mv`. No addition was needed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C. Architecture and operability | `agent_workflows/artifact_core.py:389` (`SCAN_ROOTS`, first entry `"DECISIONS.md"`); `agent_workflows/check_engine.py:3654` (`if types == ["all"]:`) | `DECISIONS.md` is repo-local and is NOT installed into a managed target repo, but `check_engine` ships there. With E-02 failing open to an empty heading set, the new rule would report EVERY `decision` gate in every managed repo as dangling, and at `warning` `drift_exit_code` returns 1, turning their `aw check all` red on an unfixable false positive. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now suppresses the rule entirely when the log is absent; E-04 gains case (9) pinning it; V-03 and Required tests demand the driven absent-log evidence; E-05 must record the portability limit; new finding F-13 and a convention bullet state it. |
| PR-002 | HIGH | IN-SCOPE | G. Plan executability (live-artifact success criteria) | plan E-02 `Expected outcome` ("exactly 156 ids") and V-02 ("expect 156") | A heading count pinned at authoring is a live-artifact count, not a stable code fact. The log is append-only and grew 153 -> 156 in the three weeks to 2026-09-27, so an unrelated ruling would break the bar and the test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and V-02 now require re-derivation at execution with the measured number as context; V-02 must cross-check the parser against an independent `grep -c` and assert agreement plus a floor; E-04 case (2) asserts a floor above 100, not equality. New finding F-14. |
| PR-003 | MEDIUM | UNDER-SCOPE | A. Correctness | `agent_workflows/backlog.py:514` and `:522` (`Release-Exempt-Kind not in ...`, `validate_gate_ref(item.release_exempt_kind, ...)`) | The release-exemption pair shares the kind vocabulary and the ref validator, so E-01 widens it too, but E-03's sweep reads `Gate-Kind` only. An exemption citing a nonexistent ruling stays undetected, and the plan did not state this. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as new finding F-15, as accepted under-scope in Scope check, and as a deferred entry carrying `Carrier: 2rnswc`. Scope deliberately not widened: no live record carries the pair. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence accuracy (Step 1) | plan F-04 Evidence ("3225 files. Bare: 173 distinct tokens, 25 distinct unresolved") | The bare-extractor census does not reproduce: review measured 3332 files, 4670 hits, 166 unresolved occurrences, 27 distinct unresolved. The soundness RATIO and every named false class reproduce, so the conclusion stands, but the numbers were stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 rewritten to state the property with both measurements and to require the executor to report its own; E-02's prose no longer pins the hit count. |
| PR-005 | MEDIUM | IN-SCOPE | Evidence accuracy (Step 1) | `.aw/records/specs/deferred/20260725-0957-01-external-delivery-and-skills.spec.md:5` (`- Gate-Kind: todo`) and `:6` (`- Gate-Ref: ju93oc`) | The deferred section claimed two `deferred` specs "still carry `Gate-Ref: TODO.md`". Driven over `specs._read_gate` across all 38 specs, the 2 gated ones are `Gate-Kind: todo` with bare id6 refs. The cited evidence was wrong even though the point survives. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Deferred entry corrected in place with the driven values and an explicit note of what was wrong. Backlog `2rnswc` carries the same stale claim and was deliberately NOT edited (out of review scope); noted in this round so its taker re-measures. |
| PR-006 | LOW | IN-SCOPE | Evidence accuracy (Step 1) | `.aw/records/backlog/blocked/20260908-idxuntrack-01-adgtqb-finalize-leaves-tracked-index-dirty.backlog.md:4` (`- Gate-Kind: artifact`) | F-03 named the single gate-carrying item `yvvf98`; the file's id6 is `adgtqb`. The finding (one gate, kind `artifact`, so the new rule ships green) is unaffected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 Evidence rewritten with the driven item path, the 820-item denominator, and the corrected id6; the specs half corrected from "three carry gates, two `todo` and one `issue`" to the driven 2, both `todo`. |
| PR-007 | LOW | IN-SCOPE | Project conventions | `pyproject.toml:171` (`addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`) | The conventions bullet quoted the marker expression as `-m 'not slow'`, understating it by one deselected category. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bullet corrected to the exact quoted value, with the discrepancy named so a reader does not re-introduce it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the new rule behave in a managed repo that has no `DECISIONS.md`? | Suppress the rule entirely when the log is absent; emit nothing. | (a) Report every decision gate as dangling (rejected: a false positive in the population that cannot fix it, and at `warning` it drives exit 1); (b) emit one `info` notice that resolution was unavailable, mirroring `check.collisions-not-checked` (rejected as gold-plating: no managed repo carries a decision gate today, so the notice would attach to nothing, and `0szu1p`'s question is about THIS repo); (c) register the rule at `info` so it cannot fail a build (rejected: it would also stop mattering here, which is the whole point). | Driven install of a scratch target repo shows no `DECISIONS.md` and no `engine.py` literal creating one; `artifact_core.drift_exit_code` exempts only `info`, so a `warning` would set exit 1; `check_review_dangling`'s docstring is the in-tree precedent for what `warning` is for. | yes |
| D-2 | Is the stale `Gate-Ref: TODO.md` claim in backlog `2rnswc` this review's to fix? | No. Correct it in the reviewed plan only, and record the defect here for `2rnswc`'s taker. | Editing the backlog item directly (rejected: a backlog item is not in the Step 0 ledger, and the controlling workflow says a file referenced only as evidence is not in scope unless explicitly added); leaving it unmentioned (rejected: a later author would inherit a wrong measurement). | `plan-review.md` Step 0.1 ledger rule and its "a file referenced only as evidence is not in scope" clause. | yes |
| D-3 | Should E-03 be split into a registry-entry item and a sweep item on right-sizing grounds? | No; keep it as one item. | Splitting into two E-items (rejected: an unregistered rule id falls back to `_DEFAULT_RULESPEC` at `error` severity, so a sweep shipped without its entry is itself a defect; the two are one deliverable and V-03 verifies both in one evidence pass). | `check_engine.rule_spec` returns `_DEFAULT_RULESPEC` for an unregistered id; `plan-review.md` right-sizing diagnostics (a) through (d) answer no for this item. | yes |
| D-4 | Does OQ-01 being open make this plan `NO-GO`? | No. It carries `- Blocking: no` and the maintainer ruling of 2026-09-10 narrowed the condition to an unresolved BLOCKING question. | Treating any open question as `NO-GO` (rejected: that is the literal reading the 2026-09-10 ruling replaced, measured as holding 43 of 104 pending plans for reasons their authors judged non-stopping). | `plan-review.md` "A NON-BLOCKING open question does NOT make a plan `NO-GO`" and the plan's own `- Blocking: no` with a stated rationale. | yes |
