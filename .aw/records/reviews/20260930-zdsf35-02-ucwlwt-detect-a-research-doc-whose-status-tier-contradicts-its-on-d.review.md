# Review findings: plan ucwlwt

- Subject-Id: ucwlwt
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-1001 (HIGH, fixed), PR-1002 (HIGH, fixed), PR-1003 (MEDIUM, fixed), PR-1004 (MEDIUM, fixed), PR-1005 (MEDIUM, fixed), PR-1006 (LOW, fixed), PR-1007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and unmodified before editing
(`git status --porcelain` empty on the whole tree), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) with NO advisories. This
plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not
apply. No production file, test, document or spec was modified by this review.

THE DESIGN IS SOUND AND THE PREMISE VERIFIES. Everything was re-derived rather than read back:

```
check_drift rule ids, by AST over the module:
  check_drift: check.stale-index-missing, check.stale-index-stale, dangling-citation,
               STALE_STATE_RULE, DANGLING_CONSUMED_RULE, ADOPTED_NO_CONSUMER_RULE,
               UNRECOGNIZED_MODEL_RULE        (7 ids, matching the plan's enumeration)
  _doc_entry: []   _scan_docs: []             (the name/frontmatter classes live in _doc_entry)

check_drift body is NOT directory-aware (the direct form of F-01):
  REFERENCE_DIR 0 | ARCHIVE_DIR 0 | .parts 0 | split('/') 0 | HOT_STATUSES 1 | normalize_status 1

research_contract primitives all present with the stated values:
  STATUSES {archive, reference, todo, active} | HOT_STATUSES {todo, active}
  SHARDED_STATUSES {archive, reference} | STATUS_NORMALIZATIONS {intake: todo}
  REFERENCE_DIR 'reference' | ARCHIVE_DIR 'archive' | normalize_status <callable>

F-07 severity chain, every link:
  check.stale-index-stale   -> RuleSpec(severity='warning', ...)
  check.stale-index-missing -> RuleSpec(severity='info', ...)
  dangling-citation / stale-state-to-promote / adopted-without-consumer -> NOT REGISTERED
  _DEFAULT_RULESPEC         -> RuleSpec(severity='error', ...)
  drift_exit_code: "return 1 if any(getattr(d,'severity','') != 'info' ...)"

F-03 reproduces EXACTLY (the only count that did not drift):
  adopted-without-consumer 35 | stranded 35 | overlap 17 | adopted-not-stranded 18

F-02 counts ALL MOVED (PR-1003):
  review: {dangling-citation: 70, adopted-without-consumer: 35, stale-state-to-promote: 18,
           check.stale-index-stale: 2}  total 125  drift_exit_code 1
  severities: {warning: 2, <empty>: 123}
  authored:  61 / 35 / 17, plus 2 check.stale-index-MISSING at info

PR-1001, the trap, measured the hard way:
  normalize_status(token: str) -> VocabResult        <-- NOT a string
  with the WRONG comparison: COLD-status at hot root = 0      (false)
  with  .value:              COLD-status at hot root = 35     (correct)
                             HOT-status in cold shard = 0
  tier distribution: {<root>: 61, archive: 32, reference: 32}

PR-1002: normalize_status('') -> VocabResult(ok=False, value=None, suggestion='active')
  7 indexed hot-root docs carry status '' (all .research-prompt.md)

PR-1004: research root subdirs = [20260726-...-research, archive, opencode, plan-review, reference]
  plan-review/20260712-0156-14-chatgpt-modular-report-template.md is a real non-README .md
  _doc_entry(...) on it -> (None, []) because parse_name rejects the name, NOT the README skip
  indexed docs outside root/reference/archive: 0   (conclusion holds)

F-08: edge_satisfied / dependency_depth / cascade_dependency_blocked all present; an `executed:`
  edge is judged on "the plan's directory on disk" (maintainer ruling 2026-09-19).
  mg8bag is `- Status: reviewed` and still in pending/, so the edge is UNMET today.

PR-1007: bare python3 -m pytest -> 3902 passed, 2 skipped, 3 warnings in 117.16s (zero failures)
  zdsf35 is `graduated`, Graduated-To: zdsf35, Work-Kind: chore, no Blocks-Release
  aw research promote exists (--help exits 0)
  5tapom Section 4 "ongoing drift is REPORTED by --check, remediated deliberately" verbatim
  5tapom Section 5 item 2 enumerates (a)(b)(c) and no tier class
  README line 89-90 enumeration and line 63-64 invariant both read as quoted; "aw research
  promote" appears 0 times in the README today
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1001 | HIGH | IN-SCOPE | A (correctness), E (verification) | `research_contract.normalize_status`'s signature and its docstring's own idiom ("call `normalize_status(raw).value` BEFORE any map/compare/band selection"); the two census runs (0 versus 35) | `normalize_status` returns a `VocabResult`, not a string, so the natural spelling of this rule (`normalize_status(e.status) in R.SHARDED_STATUSES`) is silently False for EVERY document: it reports zero findings, raises nothing, and passes every negative test. Review wrote exactly that while re-deriving this plan's own census and measured 0 stranded docs where there are 35; it was visible only because a debug print rendered `VocabResult(...)` objects as dict keys. The consequence in E-01 is WORSE than in E-02, because a zero from a broken census SATISFIES E-01's STOP condition and lets the plan proceed on a false premise, so the gate that exists to protect the corpus cannot fire. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | New F-09 records the measurement in both directions. E-02 now mandates comparing `.value`; E-01 requires the census probe be shown capable of returning NONZERO before a zero is trusted, and records that `35` is the correct answer (and the STOP) until `mg8bag` executes; E-04 requires each positive case to assert an EXACT finding count so an inert rule fails; V-01 and V-02 demand the relevant line be quoted |
| PR-1002 | HIGH | IN-SCOPE | A (correctness) | `normalize_status('')` returning `value=None`; 7 of 61 hot-root docs carrying `status: ''` | Seven indexed docs carry an empty status that normalizes to `None`, and the plan never mentions the case. A correct `.value` comparison skips them already (since `None` is in neither status set), but an implementation that defaults an unnormalizable status to a tier, or that dereferences without a guard, would flag seven innocent documents or crash. A missing status is also a DIFFERENT defect, owned by `_doc_entry`'s frontmatter classes, so claiming it here would make one finding ambiguous between two causes | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-10 records the measurement. E-02 now requires an explicit `if st is None: continue` with a comment naming the seven and stating whose defect a missing status is; E-04 gains case (6) asserting no finding for an empty or unrecognized status, which pins the skip as intentional rather than incidental |
| PR-1003 | MEDIUM | IN-SCOPE | G (live-artifact criteria), E | the re-measured per-rule counts against the authored ones | Every count in F-02 moved in a day: `dangling-citation` 61 to 70, `stale-state-to-promote` 17 to 18, and the two manifest findings changed BOTH rule id and severity (`stale-index-missing`/`info` to `stale-index-stale`/`warning`). V-04 and the Required tests section treat them as a comparison basis, so an executor reconciling against the authored figures would report a false regression or a false clean | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 rewritten with both measurements and the rule-id/severity change named. V-04 and Required tests now require BOTH sides of the per-rule comparison to be taken within the same execution, forbid comparing against any figure in the plan, and compare the suite by failure set against an empty set rather than a pass count |
| PR-1004 | MEDIUM | IN-SCOPE | A, F (honest documentation) | the research root's five subdirectories; `_doc_entry` returning `(None, [])` for the `plan-review/` doc; `parse_name`'s rejection path read | F-06's conclusion (no indexed doc outside the three tiers) holds and re-measures, but its stated REASON is false, and the reason is what a future reader would rely on. The tree has THREE other subdirectories, not one, and `plan-review/` contains a real non-README `.md`. That file is excluded because `parse_name` rejects its non-conformant NAME, not by the README skip the row credits. So the actual guarantee is "no CONFORMANTLY NAMED doc lives outside the three tiers", which is weaker: a validly named doc added under `plan-review/` WOULD be indexed with an unrecognized first component | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 rewritten with the three subdirectories, the real exclusion mechanism measured by driving `_doc_entry`, the corrected entry counts (125 indexed, 61 at root, where authoring said 124 and 60), and the consequence restated: the silent-on-unknown-tier branch is NECESSARY, not merely sufficient |
| PR-1005 | MEDIUM | UNDER-SCOPE | G (right-sizing) | the Scope check as authored; `plan-review.md` Section G's four diagnostics | No per-E-item right-sizing assessment, which the workflow requires be evaluated in semantic review rather than cleared by a passing count lint | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added per E-item: E-01 correctly a gate of its own; E-02 one concern even with the two added constraints, since both constrain one comparison; E-03 correctly separate because it is what makes the severity real (landing E-02 alone ships a rule gating at `error` by fall-through); E-04's six cases together because splitting invites landing positives without negatives or the reverse; E-05 separate only by path |
| PR-1006 | LOW | UNDER-SCOPE | G (execution contract) | the gate as authored; AGENTS.md 2026-09-01 scope-fence ruling; `plan-review.md` Step 4 | The gate carried path-scoped commit and never-push but no SCOPE FENCE declaration, and its terminal-transition sentence named neither `aw ipd finalize` nor the conditional runner ownership, nor forbade a hand `git mv` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence added as a DECLARATION naming all four paths, with the `--scope-reason`/`--scope-ack` reconciliation and explicit prohibitions on editing `research_contract` (a second status literal is the desync P8 forbids), moving any document (`mg8bag`'s job), changing an existing rule, or editing a spec. The two genuine STOP conditions are preserved and the second one added (a census probe that cannot return nonzero). Lifecycle now names `aw ipd finalize` with conditional ownership and forbids the hand paths. Staged-set verification added for the shared checkout |
| PR-1007 | LOW | IN-SCOPE | G, E | `zdsf35`'s front matter; the bare suite; `aw research promote --help` | Two live facts worth stating. `zdsf35` is already `graduated` and is the shared parent of BOTH plans in this Set, which the gate did not record, so an executor might close it from Order 02. And the suite is green at `3902 passed, 2 skipped`, so no pre-existing failure may be carried forward as expected | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now records the item as already `graduated` with no transition owed and closing it named as a Set-level decision. Required tests and V-04 state an empty expected failure set and require any member to be shown reproducing on an unmodified tree. (`aw research promote` confirmed to exist, so E-05's remedy-verb instruction is sound) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The `VocabResult` trap (PR-1001) makes this rule silently inert in a way that passes every negative test AND satisfies E-01's own STOP condition. Is pinning it in the plan's prose enough, or does it need a structural guard? | BOTH, and specifically a guard at each of the three places the trap bites: E-02 mandates `.value`, E-01 requires the census probe be demonstrated capable of returning nonzero before a zero is trusted, and E-04 requires every positive case to assert an EXACT finding count rather than mere presence. | (a) Prose warning in E-02 alone, rejected because the worst instance is in E-01's CENSUS, not in the rule: a broken census reports zero, the STOP passes, and the plan proceeds believing the corpus is clean; a note in a different E-item does not reach that. (b) Require a type annotation or an assertion on the return type, rejected as a code-shape mandate that P16's spirit disfavors and that a correct `.value` comparison makes redundant. (c) Add a test that asserts `normalize_status` returns a `VocabResult`, rejected because it pins the contract of a module this plan does not touch and would pass while the new rule stayed inert. (d) Escalate as a blocking question, rejected because this is a mechanical implementation hazard with a known correct spelling stated in the module's own docstring, not a decision needing the maintainer. | `normalize_status`'s signature `(token: str) -> VocabResult` and its docstring's stated idiom; the two measured censuses (0 with the wrong comparison, 35 with `.value`); E-01's STOP text, which keys on a zero; E-04's five authored cases, of which only the positives can fail on an inert rule. Recorded as F-09. | yes |
