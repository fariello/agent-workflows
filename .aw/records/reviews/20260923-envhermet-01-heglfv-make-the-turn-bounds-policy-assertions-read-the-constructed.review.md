# Review findings: plan heglfv

- Subject-Id: heglfv
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `3eb35740` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review; `--phase review-finalize` conforms after
revision. `- Kind:` is `child`, so the `IPD-S407` orchestrator row check does not apply. `aw check`
reported `check.ipd-uncarried-obligation` at `error` for this plan (PR-206), now cleared.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
RUNNING the claims rather than re-reading them, which is what produced PR-201 through PR-203.

THE DEFECT IS REAL AND THE FIX IS WORTH MAKING, stated first because every finding below is about
accuracy rather than about a false premise:

```text
# PR-205: reproduced, and the counts have drifted
python3 -m pytest tests/test_turn_bounds.py            -> 1 failed, 147 passed in 4.30s
env -u OPENCODE_CONFIG_CONTENT -u AW_EXECUTION_ROLE \
    python3 -m pytest tests/test_turn_bounds.py        -> 148 passed in 3.24s
# no code change between. Plan records 144 / 1 failed, 143 passed.
# The failing assertion is tests/test_turn_bounds.py:271.
```

TWO ATTRIBUTIONS IN THE PLAN ARE WRONG, AND EACH WOULD HAVE MISDIRECTED AN EXECUTOR.

```text
# PR-201: R4.1 does NOT say what the plan claims.
# Plan: "R4.1 genuinely requires that a non-isolated turn receive NO denial policy"
# Spec 7ckptx, verbatim:
#   "R4.1 An unattended isolated turn MUST run under the STRONGEST permission posture its
#    host supports, and the runner MUST supply that posture itself ..."
grep -n "non-isolated" 7ckptx -> only R1.3 (prompt byte-identity), R4.4a (bounds uniform),
                                 and evidence sections. NOTHING requiring absence of policy.
# The test's OWN docstring already says it correctly:
#   "R4.1 scopes the POSTURE to an unattended ISOLATED turn"
# What the assertion actually defends is run_opencode's comment:
#   "ISOLATED TURNS ONLY, deliberately narrower than the bounds below ... a non-isolated turn
#    legitimately works in the main checkout, where an external-directory denial would refuse
#    its ordinary work"   (ordering spec-normative under R4.6)
```

```text
# PR-202: run_opencode does NOT "always" set the variable.
inspect.getsource(oc_runipd.run_opencode):
  the ONLY OPENCODE_RUNTIME_CONFIG_ENV assignment is inside `if work_dir:`
  child_env = pinned_child_env()
pinned_child_env body: merged = os.environ.copy()
# So: runner sets it for ISOLATED turns only. The leak is one level up - the OUTER driver set it
# for this lane's turn, and the test's INNER run_opencode(work_dir=None) inherits it by copy.
```

THE FINDING I MOST WANT A HUMAN TO SEE IS PR-203. E-01 asks whether the family is wider than one
assertion and says "If only one exists, say so". It is not one:

```text
grep -n "not in main_env" tests/test_turn_bounds.py
  271:  assert policy_key not in main_env, (...)               # FAILING now
  275:  assert "AW_EXECUTION_ROLE" not in main_env             # PASSING, but not hermetic

# 275 passes only because conftest.py pops the variable at import time:
conftest.py: os.environ.pop("AW_EXECUTION_ROLE", None)

# Proof it is the SAME defect - re-set the marking AFTER conftest's pop:
  os.environ["AW_EXECUTION_ROLE"] = "worker"
  env = oc_runipd.pinned_child_env()
  -> "AW_EXECUTION_ROLE in constructed non-isolated env: True"
```

So line 275's protection lives in a different file, which is precisely the `rolevac` shape this plan
is written to avoid. A fix repairing 271 and leaving 275 ships a latent twin.

OQ-01 WAS DECIDED WITHOUT WEIGHING A SHIPPED IN-REPO PRECEDENT (PR-204):

```text
grep -n "monkeypatch.delenv" tests/test_lane_permission_posture.py
  59:  monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)
  135: monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)
  204: monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)

python3 -m pytest tests/test_lane_permission_posture.py -> 27 passed
# GREEN with OPENCODE_CONFIG_CONTENT ambient. Same seam, same variable, and it is the file whose
# docstring records the sabotage lesson this plan cites (test_the_policy_actually_reaches_the_env
# _handed_to_the_child: "Sabotaging the product ... left that test GREEN").
```

OQ-01 dispreferred the scoped control as "one step further from what production does" without noting
that the repository already settled on it for this exact variable.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | A (correctness); F (honest documentation) | spec `7ckptx` R4.1 quoted; `grep -n "non-isolated" 7ckptx` returns only R1.3/R4.4a; `run_opencode`'s "ISOLATED TURNS ONLY" comment | The plan attributes the assertion to `R4.1`, which is a floor on the ISOLATED turn and is silent on the non-isolated one. E-02's instruction to keep "`R4.1`'s assertion unchanged in strength" names a requirement that does not say that, so an executor could defend the wrong contract and satisfy the letter while losing the property. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Concern corrected with the spec quoted; F-5 added; E-02 rewritten to name the runner's deliberate narrowing (R4.6-ordered) as the property and to fix any R4.1 miscitation in the test comment; spec-sync section records the real gap; OQ-02 raises it |
| PR-202 | HIGH | IN-SCOPE | A (correctness) | `inspect.getsource(run_opencode)`: the sole assignment is inside `if work_dir:`; `pinned_child_env` = `os.environ.copy()`; `child_env = pinned_child_env()` | The plan's stated trigger is false: `run_opencode` does not "always" set the variable, it sets it for isolated turns only. E-01 instructs the executor to "confirm `run_opencode` sets it for a turn", which cannot be confirmed as written. The conclusion (every lane agent sees the failure) survives; the mechanism does not. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern and F-2 corrected with the real inheritance chain; E-01 rewritten to verify the chain by symbol and to state explicitly that no unconditional assignment exists |
| PR-203 | HIGH | UNDER-SCOPE | E (testing/verification); D (anti-regression) | `grep -n "not in main_env"` -> lines 271 and 275; probe re-setting `AW_EXECUTION_ROLE` after conftest's pop -> present in constructed env; `conftest.py`'s `os.environ.pop` | The audit E-01 requests already has a second hit. Line 275 carries the identical non-hermetic construction and passes ONLY because `conftest.py` scrubs its variable, not because the test controls it. Fixing 271 alone leaves a latent twin protected by another file, which is the `rolevac` shape this plan exists to avoid. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-6 added; E-01 now names both lines with the evidence that 275 is scrub-protected; E-02 requires both fixed; the tests section requires 275's proof be a constructed-env check rather than a passing run, since a passing run proves nothing there |
| PR-204 | MEDIUM | IN-SCOPE | C (architecture: use existing canonical mechanisms); F (KISS) | three `monkeypatch.delenv(OPENCODE_RUNTIME_CONFIG_ENV, raising=False)` call sites; `pytest tests/test_lane_permission_posture.py` -> `27 passed` with the variable ambient | OQ-01 weighs two options and omits the shipped in-repo precedent for one of them. The sibling file tests the same seam with the same variable, is green under the ambient value, and is the file whose docstring records the sabotage lesson this plan cites. Choosing differently without weighing it risks two idioms for one problem. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-7 added; OQ-01 RESOLVED to the scoped `delenv` control with the precedent cited, leaving construct-and-compare acceptable if recorded; E-02 names the precedent; the tests section requires the sibling file stay green |
| PR-205 | MEDIUM | IN-SCOPE | E; G | `1 failed, 147 passed` / `148 passed` at review vs `144` / `1 failed, 143 passed` in the plan | The plan's suite counts drifted by four in four days. An E-item quoting them would paste a false number into a `V-*` evidence block. The plan also does not warn that inside a lane the BARE run is the FAILING condition, which inverts the usual reading. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-1 re-measured; E-01 requires re-derivation with the head stated; tests section warns that bare is the failing condition in a lane |
| PR-206 | MEDIUM | IN-SCOPE | G (plan executability) | `evaluate_durable_carrier` -> `error`, "5 obligation(s) name no durable carrier"; `aw ipd lint --phase pre-transition` -> 10 findings | Five deferred obligations named no durable carrier, so the plan would block its own finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Carrier fields added to every deferred row and both open questions; F-8 added; re-measured to 0 findings. One row is deliberately `Carrier-Declined` rather than given a weak id6 (see D-3) |
| PR-207 | HIGH | UNDER-SCOPE | A (correctness); C (operability) | `wnabns` front matter (`open`, `Blocks-Release: next`, no `Graduated-To:`); `grep -rn wnabns .aw/records/plans/` finds no carrier; `evaluate_blocking_close(wnabns,'done')` -> `legitimate=False` | This plan carries `mepbmp`, which is already `graduated`, while `wnabns` is the one family member still `open` and is a release blocker nothing carries. The parent's review made preserving it completion criterion 6 and assigned the ACT to this child (an act on a retiring orchestrator would be marked done unperformed). This plan had no item for it. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-9 added; E-04 and V-04 added (with `Highest E allocated` bumped to 04) requiring a SECOND `- From-Backlog:` bullet rather than an overwrite, and a pasted `aw check`; gate states the trap |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-201 shows the assertion defends no stated requirement. Amend spec `7ckptx` here, or raise it? | Raise it as OQ-02 (maintainer-owned) and require E-02 to stop misciting `R4.1`; do not amend the spec in this plan. | Amending `7ckptx` as part of this plan: rejected because a spec amendment is a contract change needing its own review, and this plan is scoped to making one test hermetic. Also rejected: deleting the assertion, since the property it defends is real and `run_opencode`'s comment states it deliberately. | `AGENTS.md` spec-amendment rule (declare the `.spec.md` before editing; a plan MAY amend but must declare); spec `7ckptx` R4.1 and R4.6 as read | yes |
| D-2 | Resolve OQ-01, or leave it to the executor? | Resolve it: adopt the scoped `monkeypatch.delenv` control, citing the shipped sibling; explicitly leave construct-and-compare acceptable if the executor records why. | Leaving it open: rejected because the repository already answered it (`test_lane_permission_posture.py`, 3 call sites, green under the ambient value), and the workflow forbids asking a human what the tree answers. Rejected mandating one mechanism absolutely: E-02's real requirement is that the test still FAILS under mutation, which either mechanism can satisfy. | `plan-review.md` Step 3.1; the three `delenv` call sites; `27 passed` measured with the variable ambient | yes |
| D-3 | The OQ-02 spec-amendment row needs a carrier field. Give it an id6 or decline it? | `Carrier-Declined`, with the reason stated in the field. | Naming a loosely-related id6 (for example `wnabns`, which resolves and would silence the checker): rejected as a FALSE HANDOFF. It would satisfy a machine check while telling a reader that an unrelated item owns a spec decision. The honest next step, if pursued, is `aw backlog new`, which is a filing decision for the maintainer. | `check_engine.evaluate_carrier_obligation`'s DECLINED escape, whose docstring says the reason's "MERIT is the reviewer's job"; the field resolves on any open item, so resolution is not evidence of fit | yes |
| D-4 | Should line 275 be fixed here, given `rolevac` `8i0xa7` owns the role-variable vacuity? | Yes, fix it here. | Deferring it to `rolevac`: rejected on a scope reading. `rolevac` owns the guard made VACUOUS BY the conftest scrub, in a different file; line 275 is a non-hermetic read INSIDE this plan's declared `tests/test_turn_bounds.py`. Leaving it would ship a latent twin and split one file's fix across two plans. | this plan's `- Scope-Paths: tests/test_turn_bounds.py`; `rolevac` `8i0xa7`'s Concern naming `test_driver_own_process_is_not_worker_role` as its subject | yes |
| D-5 | Add E-04 for the `wnabns` gate, or leave it to the parent? | Add E-04 here. | Leaving it on the parent (`uvwqvz`): rejected because a retiring orchestrator SKIPS the pre-transition E/V checkpoint, so an act parked there is marked complete having never been performed; the parent's own review recorded that and assigned the act to this child. Rejected performing the edit during this review: it is an execution act, and this workflow revises plans rather than executing them. | `AGENTS.md` orchestrator-coverage rule; `ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`; the parent's completion criterion 6 | yes |

### Deferred and open

None. Every finding is FIXED. No finding is DEFERRED, OPEN, or REPLAN, so no escalation to a
`- Blocking: yes` question is owed under the `review_findings_gate` rule.

OQ-02 remains `- Status: open` deliberately: it is `Blocking: no`, maintainer-owned, and records a real
spec gap PR-201 exposed. Per the 2026-09-10 maintainer ruling a non-blocking open question does not make
a plan `NO-GO`.

### Notes on what was NOT changed, and why

- `tests/test_turn_bounds.py` was NOT touched. Reproducing the failure and probing line 275's hermeticity
  are measurement; fixing them is this plan's execution work.
- Spec `7ckptx` was NOT amended. See D-1: the gap is real and is raised as OQ-02 rather than closed by a
  reviewer on its own authority.
- `wnabns` was NOT modified and no `- From-Backlog:` bullet was added. That is E-04's act for the
  executor; this review added the item, the validation, and the warning about the overwrite trap.
- Sibling plans `uvwqvz` (reviewed separately) and `fwgq2u` were not edited; neither was in this
  review's ledger.
