# Review findings: plan uvwqvz

- Subject-Id: uvwqvz
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a16698cc` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review; `--phase review-finalize` conforms after
revision. Because this plan's own first `- Kind:` bullet reads `orchestrator`, the `IPD-S407` typed
child-tracking row check was run: it reports `conforming=True` for both rows (`E-01 CONFIRM heglfv REACHED
executed`, `E-02 CONFIRM fwgq2u REACHED executed`), so the bounded repair loop was NOT entered and no
attempt logging is owed. `aw check` reported `check.ipd-uncarried-obligation` at `error` for this plan
(PR-104), now cleared.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
RUNNING the claims rather than re-reading them.

THE PLAN'S CENTRAL PREMISE IS TRUE, AND THAT IS WORTH STATING FIRST because every finding below is about
accuracy and completeness rather than about a false premise. Measured directly in the lane:

```text
# PR-101: the defect reproduces deterministically, and the counts have moved
python3 -m pytest tests/test_turn_bounds.py
  -> 1 failed, 147 passed in 4.80s
  FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn
         ::test_the_permission_policy_by_contrast_IS_isolation_scoped
  tests/test_turn_bounds.py:271: AssertionError

env -u OPENCODE_CONFIG_CONTENT -u AW_EXECUTION_ROLE python3 -m pytest tests/test_turn_bounds.py
  -> 148 passed in 6.19s

# no code change between the two runs. The ambient trigger is present in this lane:
OPENCODE_CONFIG_CONTENT = {"permission": {"external_directory": "deny", "question": "deny"}}
AW_EXECUTION_ROLE       = worker

# line 271 is exactly the assertion the plan names:
assert policy_key not in main_env, (
    "a non-isolated turn must get NO denial policy; ... (R4.1)")
```

The plan records `144 passed` / `1 failed, 143 passed`. Both halves have drifted by four tests, which is
the reason CID-4 was added rather than the numbers simply being corrected: the same drift will happen again
before execution.

THE CENSUS HALF IS SUBSTANTIALLY STALE, IN THE DIRECTION THAT WEAKENS THE PLAN'S OWN F-3. The plan
describes "twenty-three open backlog items" all carrying `Blocks-Release: next`:

```text
# PR-102: re-measured over the whole backlog tree
family filings matching the ambient-env signature : 25
  graduated/ : 24   (every one carrying `- Graduated-To: envhermet`)
  open/      :  1   (wnabns)

aw attention: uj5g58 -> backlog | graduated -> active  | gate=next
              wnabns -> backlog | open      -> ready   | gate=next
```

So 24 of 25 already class `active` rather than `ready`, and the board-noise argument F-3 rests on was
largely discharged by graduation before this review. The other three open release-blockers in the tree
(`q6bbdb`, `2tiyl8`, `lw1rhj`) were checked and are unrelated defects, not members of this family.

THE ONE FINDING WITH REAL OPERATIONAL CONSEQUENCE IS PR-103, and it is what the census correction exposed:

```text
# wnabns: the sole surviving open member
- Status: open
- Blocks-Release: next
- Graduated-To:      (absent)
grep -rn wnabns .aw/records/plans/  -> only two incidental mentions inside EXECUTED plans;
                                       no plan carries `- From-Backlog: wnabns`
# child 01 carries a DIFFERENT representative:
heglfv: - From-Backlog: mepbmp   (and mepbmp IS graduated, with `- Graduated-To: envhermet`)

# the close-legitimacy predicate refuses it:
evaluate_blocking_close(wnabns, 'done')
  legitimate = False
  reason     = "backlog item carries Blocks-Release 'next'; closing it `done` would
                silently drop that release gate"
  fixes      = ['hand the gate to a plan: add `- From-Backlog: <this id6>` ...',
                'cite satisfying evidence: `aw backlog set done <item> --evidence <path>`']
```

So as authored, this Set fixes the defect `wnabns` describes and then leaves `wnabns` permanently `ready`
and release-blocking, because nothing carries its gate and the setter refuses to close it. That is a gap
the plan's own completion criteria did not cover.

PR-104 UNDERCUT THE PLAN'S OWN F-4, which is the finding I found most instructive. F-4 correctly reasons
that consolidation must be declared OUT rather than parked on the parent, because a retiring orchestrator
would mark parent-only work done unperformed. But declaring it out does not PRESERVE it:

```text
evaluate_durable_carrier(uvwqvz) -> severity=error
  "5 obligation(s) name no durable carrier: deferred row 1 records an outstanding obligation
   with NO durable carrier; once this plan reaches `executed` it classes `done` in
   `aw attention` and this vanishes with no record; ... "
evaluate_carrier_obligation -> legitimate=False for all four deferred rows
aw ipd lint --phase pre-transition -> 7 findings (IPD-S404 x6 + check.ipd-uncarried-obligation)
```

The same mechanism F-4 defends against (an obligation silently classing `done` at retirement) applies to
the prose that declares it out of scope. After revision: `evaluate_durable_carrier` -> 0 findings.

TWO CLAIMS I CHECKED AND CONFIRMED RATHER THAN CORRECTED, recorded because a reviewer should say what held:

```text
# child 02's cited precedent is real and is advisory exactly as described
aw graduation --help
  "Read-only and ADVISORY: it shows and never refuses, and it adds no uniqueness rule ...
   Every answer states which of the three cases it can detect ... cannot detect at all"

# the conftest scrub the children deliberately do NOT copy
conftest.py: os.environ.pop("AW_EXECUTION_ROLE", None)   # at import time
# and OPENCODE_CONFIG_CONTENT is NOT scrubbed there, which is why the defect survives.
# Child 01's OQ-01 rejects adopting that mechanism, citing rolevac `8i0xa7` (verified: that
# plan exists, is to-review, and records the conftest scrub making a guard vacuous).
# That rejection is evidence-based and I did not disturb it.

# CID-1's disjointness holds:
heglfv: tests/test_turn_bounds.py
fwgq2u: agent_workflows/backlog.py, tests/test_backlog_duplicate_guard.py  (module not yet created)
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | MEDIUM | IN-SCOPE | E (testing/verification); G | `python3 -m pytest tests/test_turn_bounds.py` -> `1 failed, 147 passed`; `env -u ...` -> `148 passed`; `tests/test_turn_bounds.py:271` | The defect premise is CONFIRMED, but the plan's suite counts (`144`/`143`) have drifted by four tests since authoring. A child quoting them as a bar rather than re-deriving would assert a false number in a `V-*` evidence block. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-1 re-measured with the failing assertion named; completion criteria 1 and 4 rewritten to require re-derivation; CID-4 added binding both children to measure rather than quote |
| PR-102 | MEDIUM | IN-SCOPE | A (correctness); F (honest documentation) | family enumeration: 25 filings, 24 `graduated` with `- Graduated-To: envhermet`, 1 `open`; `aw attention` classes | The census is stale in the direction that weakens the plan's own argument: the "twenty-three open items, all release-blocking" figure is no longer true, so F-3's blocker-wall claim overstates the current cost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern corrected; F-3 downgraded to INFO with the corrected counts; F-2's corpus size corrected to 25; OQ-01's rationale updated to record that the pressure behind it dropped |
| PR-103 | HIGH | UNDER-SCOPE | A (correctness); C (operability) | `wnabns` front matter (`open`, `Blocks-Release: next`, no `Graduated-To:`); `grep -rn wnabns .aw/records/plans/` finds no carrier; `evaluate_blocking_close(wnabns,'done')` -> `legitimate=False` | The sole still-`open` member of the family is a release blocker NOTHING carries. This Set fixes the defect it describes and then leaves it permanently `ready`, un-closeable because the close-legitimacy predicate refuses to drop its gate. No completion criterion covered this. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added F-5; added completion criterion 6; V-01 extended to verify it with a pasted `aw check`; OQ-02 added and RESOLVED to a HANDOFF, naming the mechanical trap that `--from-backlog` SETS rather than appends so `mepbmp`'s gate is not stranded instead; Scope check states the act is a CHILD's, never the parent's |
| PR-104 | MEDIUM | IN-SCOPE | G (plan executability) | `evaluate_durable_carrier` -> `error`, "5 obligation(s) name no durable carrier"; `aw ipd lint --phase pre-transition` -> 7 findings | Four deferred rows named no durable carrier, so the plan would block its own finalize. Worse, this defeats the plan's own F-4: declaring consolidation out of scope does not preserve it, because at `executed` the obligation classes `done` in `aw attention` and vanishes unrecorded. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Carrier fields added to every deferred row and both open questions (`uj5g58`, `8i0xa7`, `wnabns`, plus two reasoned `Carrier-Declined`); F-6 added recording the F-4 interaction; re-measured to 0 findings |
| PR-105 | MEDIUM | UNDER-SCOPE | E; D (anti-regression) | 24 of 25 filings already moved `open` -> `graduated` since authoring; child 02's declared `tests/test_backlog_duplicate_guard.py` does not yet exist | CID-2 warned that child 02's guard must not depend on the family staying open, but stated it as a hypothetical. It is already REALIZED: a guard whose tests read live `open` items now faces a corpus of one, so the test would be vacuous rather than merely fragile. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | CID-2 rewritten with the measured corpus shrink and a requirement to confirm by inspection that no test reads `.aw/records/backlog/`; E-02's expected outcome and V-02 both extended to demand that confirmation |
| PR-106 | MEDIUM | UNDER-SCOPE | G (execution contract) | the plan's `## Approval and execution gate`; `ipd_lifecycle.retire_orchestrator` vs `finalize`; executed plan `ty7w6o`'s baseline improvisation | The gate lacked the conditional lifecycle-transition ownership (runner rollup vs executor finalize), lacked a declaration-style scope fence, and named no stop condition. It also did not warn that a child running the suite in a lane will SEE this Set's own defect in its baseline, which is the reporting trap `ty7w6o` had to improvise around. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with the scope fence as a declaration (`--scope-reason`/`--scope-ack`), conditional runner/executor transition ownership, the OQ-02 precondition, and one genuine stop condition (baseline failures beyond the single known node); `## Required tests` extended with the bare-pytest rule and the expected-failure reporting discipline |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `wnabns`'s stranded release gate be preserved (PR-103): handoff, satisfied-evidence, or de-gating? | HANDOFF: a plan in this Set carries `- From-Backlog: wnabns` with the same `- Blocks-Release:`. | DE-GATED (clear the gate): rejected because the defect is real and release-blocking until child 01 lands, so clearing it would assert something false. SATISFIED (cite evidence): rejected because it requires an in-tree artifact that already discharges the item, and none exists until child 01 executes. | `AGENTS.md` close-legitimacy ladder (the three fixes); `evaluate_blocking_close(wnabns,'done')` -> `legitimate=False` with those exact fixes listed | yes |
| D-2 | Should this review ADD the `- From-Backlog: wnabns` bullet to child 01 itself? | No. Record it as completion criterion 6, resolve the mechanism in OQ-02, and verify it in V-01; leave the edit to the executor. | Editing child 01 here: rejected on two grounds. Child 01 is not in this review's ledger (Step 0 admits only explicitly named targets), and the edit is an ACT that must be owned by a child so a retiring orchestrator cannot mark it complete unperformed. | `plan-review.md` Step 0.1 (ledger contains only named targets); `AGENTS.md` orchestrator-coverage rule; `ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']` | yes |
| D-3 | Should a third V-item be added for completion criterion 6, since neither child's validation covers it? | No. Fold the required evidence into V-01, preserving the 1:1 E/V bijection. | A standalone V-03: ATTEMPTED and REVERTED during this review. `aw ipd lint --phase author` immediately reported `IPD-I302`, because a V-item with no corresponding E-item breaks the bijection; and adding a matching E-item would have parked an ACT on the orchestrator, which is exactly what PR-103's own reasoning forbids. | `aw ipd lint` -> `IPD-I302` measured on the attempt; `AGENTS.md` orchestrator-coverage rule | yes |
| D-4 | Child 01 rejects the session-wide conftest scrub of `OPENCODE_CONFIG_CONTENT` even though the symmetric scrub for `AW_EXECUTION_ROLE` is shipped. Overrule it? | No. Uphold the rejection and surface the reasoning at parent level so a reader does not re-litigate it. | Recommending the scrub as the simpler fix: rejected because the repository has MEASURED that mechanism producing a vacuous guard (`rolevac` `8i0xa7`, verified to exist and to record exactly that), so adopting it would knowingly create the same debt. | `conftest.py`'s own scrub and its "honest limits" note; child 01 OQ-01; `rolevac` `8i0xa7`'s Concern | yes |
| D-5 | Is F-3's overstated blocker count a reason to strip this plan's `Blocks-Release: next`? | No. Leave the gate in place. | Clearing it: rejected because PR-101 confirms the underlying defect is live and reproducible, and `wnabns` (PR-103) is itself a live `bug`-kind release blocker in the family. The gate is earned even though the COUNT was overstated. | `AGENTS.md` release-gates section ("every live bug gates the next release"); the measured `1 failed` run | yes |

### Deferred and open

None. Every finding is FIXED. No finding is DEFERRED, OPEN, or REPLAN, so no escalation to a
`- Blocking: yes` question is owed under the `review_findings_gate` rule.

OQ-01 remains `- Status: open` deliberately: it is `Blocking: no`, maintainer-owned, and now carries
`uj5g58`. Per the 2026-09-10 maintainer ruling a non-blocking open question does not make a plan `NO-GO`.

### Notes on what was NOT changed, and why

- Child plans `heglfv` and `fwgq2u` were NOT edited. Neither was in this review's ledger, and both lint
  `conforming` at `author` and `review-finalize`. PR-103's and PR-105's consequences for them are recorded
  in the parent's criteria and CIDs, which is the cross-plan convention (fix in the owning plan, and where
  this review is not the owner, state the obligation where the executor will read it).
- `tests/test_turn_bounds.py` was NOT touched. Reproducing the failure is measurement; fixing it is child
  01's work and this workflow reviews plans only.
- The plan was NOT retired or replanned. Its premise is confirmed true by direct measurement.
