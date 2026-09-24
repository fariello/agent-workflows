# Review findings: plan fwgq2u

- Subject-Id: fwgq2u
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `1eb4a717` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review; `--phase review-finalize` conforms after
revision. `- Kind:` is `child`, so the `IPD-S407` orchestrator row check does not apply. `aw check`
reported `check.ipd-uncarried-obligation` at `error` for this plan (PR-306), now cleared.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
RUNNING the claims rather than re-reading them, which is what produced PR-301 through PR-303.

THE PREMISE HOLDS AND THE GUARD IS WORTH BUILDING, stated first because the findings below are about
design inputs rather than about a false premise:

```text
# F-1 confirmed, precisely
aw backlog new --help  -> no duplicate / similarity / near-match option
inspect.getsource(backlog.run_new):
  'duplicate'  in src -> False
  'similar'    in src -> False
  'candidates' in src -> False
  'existing'   in src -> True   # but ONLY as:
      existing_ids = set()
      for f in _iter_items(repo_root):
          pid = parse_item(f.read_text(...)).id
          if pid: existing_ids.add(pid)
      item.id = core.mint_id6(repo_root, existing_ids)
# i.e. the sole read of existing items avoids an id6 collision; nothing compares CONTENT.

# F-4 confirmed, verbatim
aw graduation --help: "Read-only and ADVISORY: it shows and never refuses, and it adds no
uniqueness rule, because a source decomposing into several children of one Set is correct."
```

THE DISCRIMINATOR IS NOT FALSE-POSITIVE-FREE, WHICH IS THE FINDING THAT MOST CHANGES THE DESIGN:

```text
# PR-301. Recall is perfect; precision is not.
of the 23 enumerated items, carrying "test_turn_bounds" : 23 / 23
UNRELATED backlog items also carrying it                : 12
  open/     q6bbdb  (triage remaining slow failures)  <- quotes the FULL node id
  open/     xuc9v0  (slow-marked failures invisible)
  open/     1z58zm  (stranded backlog items on unmerged lane)
  open/     wnabns  (see PR-302: actually a TRUE duplicate, not unrelated)
  open/     4bhxni  (tell agent remaining turn budget)
  open/     2tiyl8  (agy import count pins stale 56)
  open/     lw1rhj  (artifact audit verdict parity flake)
  done/     q1z9gn, fvl44r, 7dy125
  parked/   w07sbr
  graduated/uj5g58  (this plan's own source)

precision = 23 / (23 + 12) = 66%   false positives = 34%
# and they are GENUINE mentions, not substring artifacts:
q6bbdb: "test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy..."
```

F-5 asserted token overlap "carries almost no false-positive risk" and OQ-01 set the bar "if token
overlap catches 23 of 23 with no unrelated matches, do not build similarity scoring". The recall half is
exactly right; the precision half is falsified, so the literal bar is unreachable.

THE MOTIVATING CORPUS MOVED OUT FROM UNDER THE PLAN:

```text
# PR-302
all 23 enumerated ids resolve to: .aw/records/backlog/graduated/   (23 of 23)
family members still `open`:      1   (wnabns)
aw attention classes of the 23:   {'active': 23}    # not 'ready'

# and wnabns is NOT a negative control - it is a 24th filing of the same defect:
wnabns  : "test_the_permission_policy_by_contrast_IS_isolation_scoped reads the ambient env,
           so it fails inside an OpenCode-driven turn"
mepbmp  : "test_turn_bounds asserts a non-isolated turn carries NO permission policy, but
           run_opencode now always sets OPENCODE_CONFIG_CONTENT, so 1 node fails"
```

E-01 instructs "enumerate OPEN items ... that number is the plan's justification": run literally today it
returns ONE, and an executor could reasonably conclude the problem evaporated. E-02 instructs reporting
"existing OPEN items", which would surface NONE of the 23 the guard is specified against.

THE LATENCY BUDGET IS INVERTED, AND THE REAL DEFECT ON THIS PATH IS ONE THE PLAN DID NOT NOTICE:

```text
# PR-303
_iter_items + full read of every item : 596 items, 2,161,590 chars,  21.8 ms
walk + parse_item(...).id            : 595 ids,                     50.0 ms
artifact_core.mint_id6               : 1852.6 / 1719.9 / 1714.4 ms  (3 trials)
  -> artifact_adopt.repository_id6s  : 1720.6 ms, 1473 ids
end-to-end `aw backlog new` dry run  : 2.12 s / 2.69 s / 1.91 s
python3 -c "from agent_workflows import backlog" : 0.10 s   (so not import cost)
aw --help                                        : 0.34 s   (so not CLI startup)
```

E-02 bounds the guard against "roughly 530ms for ~620 records" and warns a re-walk "could exceed that".
The corpus read is 22 to 50ms against a command already costing about 2 seconds, of which `mint_id6` is
roughly 90 percent. So the guard is nearly free, `run_new` already performs the walk it needs, and by
this repository's own `59t9x5` standard the mint is a larger user-perceptible defect than the one E-02
guards against.

```text
# 59t9x5 verified as the governing standard
- Status: open | - Work-Kind: bug | - Blocks-Release: next
- Summary: "aw find opens every record twice ... costing ~128ms of a ~530ms command an
            operator waits on"
# The cited test-hazard precedents all exist:
jb0sc1  open/     "Six live-corpus tests carry no livecorpus marker ..."
caf5ed  open/     "Six scope-drift test arrangements ... would pass VACUOUSLY ..."
agrlvw  done/     run-viewer tests need live run data
4y7nzh  graduated/ no local records integrity gate
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | A (correctness); F (UX: prevent silent failure) | `grep -rl test_turn_bounds .aw/records/backlog/` -> 23 family + 12 unrelated; full node id quoted from `q6bbdb` | The plan's proposed discriminator is asserted to carry "almost no false-positive risk" and OQ-01 makes that the deciding criterion. Measured precision is 66 percent (12 unrelated matches), several genuine rather than artifacts. A 34 percent noisy advisory is the kind the plan's own OQ-01 says filers learn to skip, returning to the status quo with added latency. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | F-5 split (recall confirmed, precision falsified); F-6 added with the 12 named; E-01 rewritten to require a PRECISION figure and a discriminator beyond bare substring (co-occurrence, rarity weighting, or summary-only); OQ-01 RESOLVED to token overlap plus discriminator, prose similarity rejected on the inverse reasoning; V-01 refuses a recall-only report |
| PR-302 | HIGH | IN-SCOPE | A (correctness); D (anti-regression) | all 23 resolve under `graduated/`; `aw attention` classes `{'active': 23}`; `wnabns` and `mepbmp` summaries quoted | The corpus the plan is specified against is no longer `open`. E-01's open-only count returns ONE today (readable as "problem gone") and E-02's open-only search would surface none of the 23. Separately, `wnabns` is a TRUE duplicate, so using it as the negative control would penalize correct behavior. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-7 added; E-01 counts per status across the whole tree and names the statuses a guard must search; E-02's population choice made decided rather than open, showing status beside each candidate; E-01/E-03 state explicitly that `wnabns` is not a valid control and point at `q6bbdb` instead; F-3 downgraded to INFO |
| PR-303 | HIGH | IN-SCOPE | C (operability); F (KISS: reuse existing mechanisms) | `_iter_items` + read 21.8ms; walk+parse 50.0ms; `mint_id6` 1852.6/1719.9/1714.4ms; `repository_id6s` 1720.6ms; end-to-end 2.12/2.69/1.91s; import 0.10s; `aw --help` 0.34s | E-02's latency constraint budgets against the wrong number by two orders of magnitude, and misses that `run_new` ALREADY walks and fully reads every item for the id6 set. As written it could drive an executor to avoid a read that is nearly free, or to add a second independent walk. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-8 added; E-02 rewritten to re-measure, to require reuse of `run_new`'s existing pass, and to report a DELTA; conventions record the existing walk; tests section requires the delta beside the command's existing total; the mint cost is carried (see PR-304) |
| PR-304 | MEDIUM | OVER-SCOPE (raised, not fixed) | C (operability) | the `mint_id6` / `repository_id6s` timings above; `59t9x5`'s `bug` classification and its ~128ms-of-~530ms threshold | The 1.7s mint is a defect by this repository's own standard on the very command this plan touches, and nothing in the tree records it. Fixing it here would be over-scope (undeclared `artifact_core`/`artifact_adopt`, and it touches id6 collision correctness for every artifact type); leaving it unrecorded would lose a measured finding at this plan's retirement. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Captured in the plan rather than code-fixed (see the Deferred-and-open note). Added as a `## Deferred` row with a reasoned `Carrier-Declined` and as OQ-02 with the maintainer as owner and a recommended `--work-kind bug --blocks-release next` filing; Scope check names it explicitly as over-scope so an executor is not tempted; the honest caveat (redundant vs merely expensive is UNKNOWN) is recorded in OQ-02 |
| PR-305 | MEDIUM | UNDER-SCOPE | E (testing/verification) | `caf5ed`: "would pass VACUOUSLY under lane-scoped measurement"; `tests/test_backlog_duplicate_guard.py` does not exist yet | E-03 correctly forbids pinning the live corpus but does not require the fixture test be shown able to FAIL, which is the specific hazard `caf5ed` records for this pattern. With a 66 percent-precision signal, a test asserting one true pair and one false pair would pass while the advisory was useless. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires enough unrelated fixtures that a regression to bare substring matching REDS the test, plus a demonstrated failure against a deliberately broken discriminator; V-03 requires both pasted |
| PR-306 | MEDIUM | IN-SCOPE | G (plan executability) | `evaluate_durable_carrier` -> `error`, "5 obligation(s) name no durable carrier"; `pre-transition` -> 10 findings | Five deferred obligations named no durable carrier, so the plan would block its own finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Carrier fields added to every deferred row and both open questions; F-9 added; re-measured to 0 findings. Two rows are reasoned `Carrier-Declined` rather than given weak id6s (see D-3) |
| PR-307 | MEDIUM | UNDER-SCOPE | G (execution contract) | the plan's gate; sibling `heglfv`'s measured lane failure (`1 failed, 147 passed` bare vs `148 passed` unset) | The gate lacked conditional lifecycle-transition ownership and a declaration-style scope fence, and the tests section did not warn that this plan's own baseline will contain a failure owned by its sibling, which an executor could try to fix or silently absorb. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with the scope fence as a declaration, conditional runner/executor transition ownership, a summary of the three measurements, and one genuine stop condition (no discriminator reaching usable precision); tests section names the expected sibling-owned failure |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-301 falsifies OQ-01's deciding criterion. Resolve OQ-01 anyway, or leave it to E-01? | Resolve it: token overlap PLUS a cheap discriminator (co-occurrence, rarity weighting, or summary-only), with prose similarity rejected. | Leaving OQ-01 open: rejected because the repository answered the measurable part and the workflow forbids asking what the tree answers. Mandating a specific discriminator: rejected because three candidates are plausible and E-01's own measurement should pick between them; the plan now requires the CHOICE be reported with its precision. Building prose similarity: rejected because token overlap already has 100 percent recall on the corpus, so similarity closes a ZERO recall gap while adding the false positives that are already the binding problem. | measured 23/23 recall and 66 percent precision; OQ-01's own argument that a noisy advisory is skipped; `plan-review.md` Step 3.1 | yes |
| D-2 | Should this review widen the plan to fix the 1.7s `mint_id6` cost it measured? | No. Raise it (OQ-02 + a deferred row), name it over-scope in the Scope check, and recommend filing it `bug`/`blocks-release next`. | Widening `- Scope-Paths:` to include `artifact_core.py`/`artifact_adopt.py`: rejected because the mint is a correctness-critical global collision guard, a change there affects every artifact type, and bundling it would make one reviewable plan into two unrelated ones. Saying nothing: rejected because the measurement would then vanish at this plan's retirement, which is the exact failure the carrier rule exists to prevent. | `59t9x5`'s maintainer ruling (user-perceptible delay is a bug); `mint_id6`'s docstring arguing the repository-wide set is deliberate and "strictly stronger"; the carrier rule | yes |
| D-3 | Two deferred rows (refusing a filing; the mint cost) have no honest carrier id6. Invent one or decline? | `Carrier-Declined` with the reason written in the field. | Naming a loosely-related open item to satisfy the checker: rejected as a FALSE HANDOFF, which passes a machine check while telling a reader that an unrelated item owns the obligation. For the mint cost specifically, the honest remedy is filing a NEW item, which is a filing decision rather than a reviewer's to make on its own authority. | `check_engine.evaluate_carrier_obligation`'s DECLINED escape, whose docstring says the reason's "MERIT is the reviewer's job"; the field resolves against any open item, so resolution is not evidence of fit | yes |
| D-4 | Is `wnabns` the negative control E-01 asks for? | No. It is a true duplicate; the control must come from the 12 unrelated matches (`q6bbdb` recommended). | Accepting it as the control: rejected after reading both summaries, which describe the same test node, the same ambient variable and the same failure. A test asserting the guard does NOT flag it would encode wrong behavior as correct, which is worse than having no control. | `wnabns` and `mepbmp` summaries read side by side; `q6bbdb`'s full-node-id mention for a different concern | yes |
| D-5 | PR-302 shows the corpus is `graduated`. Does that weaken the plan enough to defer it? | No. Keep the plan and re-aim its measurements. | Retiring or deferring it: rejected because F-1 is confirmed (no guard exists at all), the FILINGS are real regardless of disposition, and the guard's value is prospective (stopping the twenty-fourth filing of the NEXT defect), which the corpus's current status does not touch. `wnabns` existing as a 24th filing after `uj5g58` counted 18 is direct evidence the mechanism is still live. | all 23 resolving under `graduated/` while `wnabns` remains `open`; F-1's confirmation | yes |

### Deferred and open

None of the findings is DEFERRED, OPEN, or REPLAN; all seven are FIXED, so no escalation to a
`- Blocking: yes` question is owed under the `review_findings_gate` rule. PR-304 is recorded as FIXED in
the sense the Fix Bar means it: the finding is fully captured in the plan (deferred row, OQ-02, Scope
check) rather than silently carried, and the code change it describes is deliberately out of scope.

OQ-02 remains `- Status: open` deliberately: it is `Blocking: no`, maintainer-owned, and records the
measured mint cost. Per the 2026-09-10 maintainer ruling a non-blocking open question does not make a
plan `NO-GO`.

### A note on D-4's reversibility, because I first classified it wrong

`D-4` was initially recorded `Reversible: no`, and `check.review-decision-unescalated` correctly flagged
it as an unescalated irreversible decision. Re-judging it against the stated test (the COST OF BEING
WRONG, not the reviewer's confidence) it is `yes`: if an executor wrongly encoded `wnabns` as a negative
control, the damage is a test asserting the wrong behavior, and a later maintainer undoes that by editing
the test. Nothing is published, migrated, deleted, or depended on by another party, which is what the
`no` tier is for. The original `no` conflated "would be bad and hard to notice" with "cannot be undone".

The correction is recorded rather than quietly applied, because the mis-tier is itself instructive: a
judgement that is hard to SPOT later is not thereby irreversible, and inflating it would have escalated a
non-question into a `Blocking: yes` gate that no human needs to answer (the decision rests on two items'
measured content, not on a maintainer's preference).

Difficulty of noticing is still a real risk, and it is addressed by REDUNDANCY IN THE PLAN rather than by
a blocking gate: E-01 states "`wnabns` versus the 23 is NOT a valid negative control ... a signal that
flags it is CORRECT", E-03 states "NOT `wnabns`, which review established is a genuine duplicate that
SHOULD be flagged", V-01 requires the executor to state explicitly that `wnabns` was considered and
rejected as a control, and the gate names it in its three-point summary.

### Notes on what was NOT changed, and why

- `agent_workflows/backlog.py` was NOT touched. Measuring `run_new`'s existing walk and the mint cost is
  measurement; building the guard is this plan's execution work.
- `artifact_core.py` / `artifact_adopt.py` were NOT touched. See D-2: the 1.7s mint is raised, not fixed.
- No backlog item was filed for the mint cost. See D-3: filing is the maintainer's or the executor's act,
  and a reviewer minting a new tracked artifact on its own authority would be a records change outside
  this workflow's remit (it edits plans and its own review record only).
- Sibling plans `uvwqvz` and `heglfv` (both reviewed separately in this sweep) were not edited; neither
  was in this review's ledger.
