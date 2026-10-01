# Review findings: plan t6ledu

- Subject-Id: t6ledu
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in a lane worktree at HEAD `5b506a049`. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after. No pre-review snapshot was owed: `git status --porcelain` was empty, so the plan was
committed and unmodified. NO PRODUCTION FILE WAS MODIFIED at any point; every measurement below was
taken in a throwaway script against the real functions, and `git status --porcelain` is empty.

ALL EIGHT OF THE PLAN'S FINDINGS WERE INDEPENDENTLY RE-MEASURED AND ALL EIGHT HOLD AS WRITTEN. This is
an unusually well-evidenced plan and the review found no false claim in it. F-1 reproduces: with
`check_commit_invariants` patched to one enriched finding, `info` gives `drift_exit_code == 0` and hook
`1`, while `warning` (`check.setid-length-warn`) and `error` (`check.scope-drift`) give `1` and `1`.
F-2's quoted reasoning is present in both the item and `iqtt8d` E-04 verbatim. F-3's simulation
reproduces end to end: `check.scope-not-audited` registered `info` and emitted from `check_scope_drift`
arrives in the aggregate at `severity == 'info'`, scores `drift_exit_code == 0`, and the hook returns
`1` with one message. F-4 holds on both facts: `.pre-commit-config.yaml` wires `ipd-executed-transition-gate`
and `ipd-status-untooled-gate` and contains zero occurrences of `aw-precommit-scope-gate`, and all four
ids the three composed rules can emit (`check.status-untooled`, `check.blocking-item-closed-without-gate`,
`check.from-backlog-gate-mismatch`, `check.scope-drift`) are registered `error`. F-5 holds: `iqtt8d` is
`- Status: approved` under `pending/`, a tree-wide search for `not-audited`/`not_audited` across
`agent_workflows/` and `tests/` matches nothing, no registry id contains `audit`, and the `wmnmei`
ruling is preserved verbatim in `_plan_execution_tree`'s docstring ("declined the offered variant that
additionally printed a \"scope not checked, not lane-isolated\" line in favor of the plain silent form").
F-6's quoted aggregator docstring is exact. F-7 holds: a legacy 3-field `Drift` carries `severity == ''`
and scores `1`, and the census is 33 error / 12 warning / 11 info of 56. F-8 holds: `iqtt8d` declares
`worktree_lease.py`, `check_engine.py` and `tests/test_scope_drift_lane_resolution.py`, so the two plans
contend for no file.

THE PLAN'S METADATA AND PROVENANCE ARE CORRECT AND WERE CHECKED RATHER THAN ASSUMED. Backlog `p4hmpz`
is `- Status: graduated` with `- Work-Kind: followup` and `- Priority: low`, both inherited unchanged,
and it carries no `- Blocks-Release:`, so none is invented. `aw check --agent` reports 72 findings
across the repository and NOT ONE names `t6ledu`, which is notable given how many of its peers carry
`check.ipd-uncarried-obligation` or `check.plan-spec-link-missing` rows; this plan's five deferral rows
all already carry a typed `Carrier` or `Carrier-Declined` field.

THE SUBSTANTIVE FINDING IS PR-001, AND IT WAS FOUND ONLY BY PROTOTYPING THE PRESCRIBED FIX. Reading
E-02 does not reveal it; running it does. The plan correctly diagnosed a real defect, correctly located
the fix at the exit-code boundary, correctly rejected the aggregator-filtering alternative, and then
prescribed a one-line change that does not work for the one rule the whole plan exists to serve.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | Rubric A (correctness); Rubric G (plan executability) | `agent_workflows/check_engine.py` `check_commit_invariants` final line `return [enrich_drift(d) if not d.recovery else d for d in drift]`; `check_engine.check_scope_drift` setting `recovery="restrict the change to Scope-Paths, ..."` inline; `agent_workflows/artifact_core.py` `drift_exit_code` ("A legacy 3-field ``Drift`` carries an empty ``severity`` and is therefore still treated as failing"); `.aw/records/plans/pending/...iqtt8d...ipd.md` E-04 | **THE PRESCRIBED FIX DOES NOT ACHIEVE THE PLAN'S OWN GOAL FOR THE RULE THAT MOTIVATED IT.** E-02 as authored says return `artifact_core.drift_exit_code(drift)`. But the aggregator enriches CONDITIONALLY, so a finding whose producer already set `recovery` is never enriched, reaches the hook with `severity == ''`, and `drift_exit_code` scores an empty severity as FAILING by design. `check_scope_drift` IS such a producer, and `iqtt8d` E-04 emits its new advisory from `check_scope_drift` while requiring a message naming the plan and its lanes. Measured: that rule registered `info` with a pre-set `recovery` arrives at `severity == ''` and scores `1`, so the bare fix STILL REFUSES THE COMMIT. Worse, the plan would have passed its own V-02, which patched the AGGREGATOR and thereby bypassed the exact mechanism that breaks it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires scoring over SEVERITY-BACKFILLED findings via the shared `enrich_drift` (`[d if getattr(d, "severity", "") else _ce.enrich_drift(d) for d in drift]`), demonstrated at review as idempotent and recovery-preserving and correct on all four shapes (`info`+preset-recovery `1 -> 0`, `info`+no-recovery `0 -> 0`, `error`+preset-recovery `1 -> 1`, `warning` `1 -> 1`). The fix stays inside the declared `- Scope-Paths:` (hook only) because changing the aggregator's conditional enrich would alter what `aw check` sees. E-04 case (e) must now carry a pre-set `recovery` and drive the REAL aggregator (patching `check_scope_drift`, not `check_commit_invariants`); V-02 and V-04 require the un-backfilled form shown RED on that row; F-9 records the measurement; the Goal and the gate both name this as the most likely way to get the fix wrong. |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric F (UX, prevent silent failure); `docs/cli-output-contract.md` | `agent_workflows/hooks/precommit_scope_gate.py` `main` (`status="clean" if exit_code == 0 else "findings"`, and the `"gate passed"` / `"refused (N finding(s))"` summary pair); `docs/cli-output-contract.md` Anti-Greenwashing Invariant | **E-02 FIXED ONLY `main`'s HUMAN BANNER AND LEFT ITS MACHINE ENVELOPE UNADDRESSED.** Post-fix an advisory-only run is exit `0` with one message, so the agent record reads `outcome: clean` with `findings: 1` and the summary says `gate passed` while a finding is attached. Measured verbatim at review on the post-fix shape. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now covers the envelope, but deliberately changes only the SUMMARY WORDING and NO field. The shape itself is correct house convention, measured at review: `aw check specs` on this checkout already emits `outcome: conforms, exit: 0, findings: 1` for a live advisory and prints `✓ CONFORMS` above a `Findings:` block, and the Anti-Greenwashing Invariant is not engaged because nothing was skipped, partial or unverified. F-10 records both the defect and the precedent, so a later reader does not "fix" the envelope into a contract violation by forcing exit `1`. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric G (executability); internal consistency sweep | `agent_workflows/hooks/precommit_scope_gate.py` module docstring (the "Honest limits" paragraph, whose last sentence is "Fail-closed on a refusal (exit 1); ..."); `agent_workflows/check_engine.py` `_receipt_is_live` quoting `hooks/precommit_scope_gate.py:17-19` | **E-03's TWO INSTRUCTIONS CONTRADICT EACH OTHER.** It requires the "Fail-closed on a refusal (exit 1)" contract corrected AND the "honest-limits paragraph" preserved byte-identically, but that sentence IS the last sentence of that paragraph. Measured: the span `_receipt_is_live` actually quotes ends at "phase-5 CI running the same engine." and does NOT contain "Fail-closed", while the paragraph does. As written an executor could satisfy neither instruction without violating the other, and the likely resolution would be to leave the stale contract standing beside the new one. Separately, the citation is a BARE LINE RANGE with no symbol anchor, and this item edits that very docstring, so the offset will move while `check_engine.py` is deliberately out of scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now scopes the preservation obligation to the QUOTED SPAN (explicitly narrower than the paragraph), requires the stale sentence corrected, and states that the two are only jointly satisfiable for that reason. It also requires the `:17-19` offset either verified still-accurate or its drift RECORDED in V-03 with the one-line follow-up named, rather than editing the out-of-scope citing file or silently leaving a wrong range. V-03's evidence is restructured into three mechanical proofs matching the narrowed obligation. F-11 records both halves. |
| PR-004 | LOW | IN-SCOPE | live-artifact re-derivation convention | bare `python3 -m pytest`; `python3 -m pytest tests/test_check_engine_release_gate.py`; `ls tests/test_precommit_scope_gate_severity.py`; `aw check --agent` | **BASELINES WERE UNSTATED OR STALE AND SEVERAL VALIDATION PRECONDITIONS WERE UNVERIFIED.** The validation section demanded the bare suite summary with no figure to compare against, and the configured marker expression it quotes (`-m 'not slow'`) omits `and not livecorpus`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Measured and recorded at review, each with an explicit re-derive instruction rather than as a literal to match: bare suite `3802 passed, 2 skipped, 3 warnings`; `tests/test_check_engine_release_gate.py` `31 passed`; NO test file for this hook exists today (so E-04 is genuinely new coverage, verified rather than assumed); `aw check --agent` exits 1 with 72 findings and names no row against `t6ledu`. The quoted `addopts` marker expression is corrected. F-12 records all four. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001's fix needs a severity present before scoring. Backfill inside the HOOK, or make `check_commit_invariants` enrich unconditionally? | Backfill inside the HOOK, through the shared `enrich_drift`, leaving the aggregator untouched. | (a) Make the aggregator enrich unconditionally (drop the `if not d.recovery` guard): rejected because it changes what `aw check` sees through the same function, which is the divergence the aggregator's documented no-new-policy property exists to prevent, and because `check_engine.py` is deliberately outside this plan's `- Scope-Paths:` precisely so no severity-adjacent behavior can move. (b) Hand-roll a severity lookup in the hook: rejected as a second implementation of the registry mapping, which is what `enrich_drift` already is. (c) Treat an empty severity as non-gating in the hook: rejected because it inverts `drift_exit_code`'s deliberate fail-closed direction for legacy findings. | `check_commit_invariants`'s docstring ("introduces NO new policy logic, so the pre-commit hook that delegates here and `aw check` can never diverge"); `enrich_drift`'s docstring ("Idempotent-safe"), confirmed at review to preserve a pre-set `recovery` verbatim while stamping `severity`; the plan's own `- Scope-Paths:` exclusion of `check_engine.py`; four-shape table measured correct with the hook-local backfill. | yes |
| D-2 | Post-fix an advisory-only run emits `outcome: clean` with `findings: 1`. Is that a contract breach to fix by forcing exit `1`, or acceptable with better wording? | Acceptable; fix only the summary WORDING and change no envelope field. | Forcing exit `1` so `findings > 0` always pairs with `findings` status: rejected because it would reintroduce the exact refusal this plan exists to remove, making the whole change a no-op. Rewriting `status` to a new token: rejected because `clean`/`findings` and exit-code parity are published contract in `docs/cli-output-contract.md`. | `aw check specs --agent` on this checkout already emits `outcome: conforms, exit: 0, findings: 1` for a live advisory, and its human surface prints `✓ CONFORMS` above a `Findings:` block, so advisory-with-success is the established convention; `docs/cli-output-contract.md`'s Anti-Greenwashing Invariant covers `skipped`/`partial`/`unverified`/`cannot-run` work, none of which applies. | yes |

### Deferred and open

(none)

OQ-01 remains OPEN with `Owner: maintainer` and `Blocking: no`, and this review deliberately did NOT
resolve it. Both of the plan's grounds for refusing to answer were re-checked and both hold (F-5): the
residual-rate datum cannot exist until `iqtt8d` ships, and promotion partially reverses a recorded
maintainer ruling, making it a risk-appetite call no agent has standing to make. A non-blocking open
question does not make a plan `NO-GO` (maintainer ruling 2026-09-10, plan `qhy3i3` OQ-01). PR-001
STRENGTHENS the question's premise rather than touching its answer: before the corrected E-02, "leave
it at `info`" would not have meant what the maintainer thought he was choosing, and after it, it does.
