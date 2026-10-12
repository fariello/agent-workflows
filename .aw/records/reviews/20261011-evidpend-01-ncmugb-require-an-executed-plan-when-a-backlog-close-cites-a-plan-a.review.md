# Review findings: plan ncmugb

- Subject-Id: ncmugb
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `bd555fd74`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; `--phase
review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Verified: `check_engine.resolve_evidence_artifact` checks safety, containment, existence and records-tree location
only, and its docstring claims "an executed IPD"; the SATISFIED arm in `evaluate_blocking_close` follows DE-GATED
and HANDOFF and precedes the `if same_gate_carriers:` refusal; `_carrier_is_executed` uses `"executed" in p.parts`
for `.ipd.md`; `specs._evidence_resolvable` delegates to the resolver and then requires an executed plans path;
`check_release_gate_consistency(at_rest=True)` re-runs `evaluate_blocking_close` on `done` gated items closed on
or after the `release_gate_at_rest` cutover (`_item_close_date` from the newest history line); executed plan
`wyk11f` cites pending `tf4jz5` as `Carrier-Evidence:` and that file exists (F-05 holds); `bkprhk` is open and
`7lfe87` is `graduated`; `D162` is the last decision; the AGENTS.md sentence is at line 232, below
`<!-- /aw:block -->` (line 125), and `engine.py` does not carry it; `aw check release-gates --agent` -> `conforms`,
0 findings. Runner path: `runner_shared.evaluate_backlog_close` returns evidence only after every IPD carrier is
`executed` (`_cited` uses the lane's `executed/` path), and `close_backlog_item` passes `--gate-dir` and
`--lane-carrier-*`, so HANDOFF decides first.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D blast radius (evidence) | F-06 / E-05 claim "4 `Close-Evidence:` items, all citing walkthroughs"; review census | The corpus has 52 gated `done/` items carrying `Close-Evidence:`. 48 cite `executed/` plans and 4 cite a walkthrough. The authoring census missed the plan citations, which are exactly the population this change re-judges at rest. The conclusion (zero new findings) still holds, since none cites a non-executed plan, but the stated basis was wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 and E-05 now carry the measured census. V-05 requires re-deriving it at execution. |
| PR-002 | MEDIUM | IN-SCOPE | A/B correctness (containment) | E-02 helper "no `executed` path segment"; review probe (`'executed' in Path('/x/executed/repo/...pending/a.ipd.md').parts` -> True) | An absolute-path segment test accepts every plan in a repo cloned under any directory named `executed`. The "plans tree" test was also loosely defined. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The helper is now root-relative. Plans tree and disposition come from `relative_to(repo_root).parts`. It covers legacy `.md` plans and a plans directory. Scope text and F-09 updated. |
| PR-003 | MEDIUM | UNDER-SCOPE | E test correctness | E-01 (g) at-rest; `check_release_gate_consistency` gating on `_item_close_date >= cutover` | The at-rest case would pass vacuously if the fixture item lacked a dated history line on or after the cutover. "Non-empty finding list" also did not name the rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (g) now requires an explicit dated history line and asserts `check.blocking-item-closed-without-gate`. Its executed half is listed as a must-pass at HEAD. |
| PR-004 | LOW | IN-SCOPE | F UX (honest hints) | Existing refusals' hint "`--evidence <in-tree artifact path>`" | After the fix, both existing refusals would still advertise citing any in-tree artifact, including the now-refused pending plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 rewords both hints. New case (h) asserts that the reason names the path and "has not shipped", and that the item is untouched on refusal. |
| PR-005 | LOW | UNDER-SCOPE | G evidence ordering | E-05 "full suite BARE before E-02", while E-05 runs after E-04 | The before-run could not be taken in an item that runs after the edits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now captures the base bare-suite run and its failing ids. |
| PR-006 | LOW | UNDER-SCOPE | G execution contract; 3.1(5) | Gate paragraph; V-03 dash check scoped to the CHANGELOG line only; OQ-01/OQ-02 `Owner: none` | The gate lacked an OQ statement, a scope-fence declaration, the managed-block fence, conditional finalize ownership, and a no-close instruction for `7lfe87`. The dash check was narrower than the documents edited. The OQs named no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate itemized. V-03's dash check now covers all added lines in the three user-facing files. OQ owner is `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Absolute or repo-relative disposition test for the helper? | Repo-relative. | Mirror `_carrier_is_executed`'s absolute `in p.parts`. Rejected: it is not containment-safe (review probe), and the two agree on every in-repo plan. | Review probe; `resolve_evidence_artifact` already resolves relative to the root. | yes |
| D-2 | Refuse an unshipped-plan citation even when same-gate carriers exist? | Yes, with the specific reason, before the carrier refusal. | Fall through to the carrier refusal. Rejected: that reason does not name the cited plan. | E-02 already orders it before `if same_gate_carriers:`; made explicit. | yes |
| D-3 | Reword the existing refusals' `--evidence` hint? | Yes. | Leave it. Rejected: the hint would then advertise a refused route. | Rubric F (prevent silent failure / honest guidance). | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
