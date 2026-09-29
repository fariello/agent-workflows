# Review findings: plan jefifu

- Subject-Id: jefifu
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `aba883ed` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after. No pre-review snapshot was owed: `git status --porcelain` was empty, so the plan was
committed and unmodified. `aw check --agent` reports 21 findings across the repository and NONE names
`jefifu`; `aw check release-gates --agent` conforms, so the `- Blocks-Release: next` inherited from
backlog `03aicr` (a `bug`, per the every-live-bug-gates-the-release rule) is well formed. No production
file was modified at any point: the one probe module written to measure PR-401 was deleted and `git
status --porcelain` is empty again.

EVERY ONE OF THE PLAN'S EIGHT FINDINGS WAS INDEPENDENTLY REPRODUCED AND ALL EIGHT HOLD. F1: a bare
`python3 -m pytest tests/test_dependency_block_reporting.py` reports `8 passed`, so the item's reported
red is gone. F2: `ID6_RE.pattern` is `^[a-z0-9]{6}$`, `parse_dependency_token('executed:drnprereq')`
returns `None` while `'executed:drn999'` returns
`ItemDependency(kind='executed', target_type='ipd', status=None, id6='drn999')`, and a counting spy over
`runner_shared.edge_satisfied` records **0** calls beside reason map
`{'executed:drnprereq': 'executed:drnprereq: unparseable dependency token'}`. F3 reproduces byte for
byte under the `(False, "")` stub. F4 reproduces in BOTH arms: `executed:zzz999` against the live root
yields `'executed:zzz999: Cannot locate IPD zzz999; configured path was '`, and a synthesized `tmp_path`
root containing `20260919-s-01-drn999-dep.ipd.md` with `- Status: approved` yields the resolution reason
verbatim as the plan quotes it, with the spy count going `0` -> `1`. F5's commit body is the bare subject
line with no plan id6. F6 and F7 reproduce (`grep -n 'parents\[1\]' tests/*.py` returns six sites in
five files, one more file than F7's four because `test_executed_transition_gate_e2e.py` has two; neither
is a dependency-verdict coupling, so F7's conclusion is unaffected and the census is noted here rather
than raised, since the plan's claim is about which site feeds `state["repo"]` and that claim is exact).
F8's gate reasoning holds. The plan's citation of `GUIDING_PRINCIPLES.md` P16 resolves to line 179 and
`DECISIONS.md` D78 to line 2084, both saying what the plan says they say. `kmzude` is `- Status:
reviewed` in Set `testlocality` and does answer "synthesize first", so the plan's advance conformance
claim is accurate and needs no dependency edge.

THIS IS A WELL-EVIDENCED, CORRECTLY-FENCED, HONESTLY-SCOPED PLAN that diagnoses a real and subtle
defect, refuses to restate a red it did not observe, and rejects the backlog item's second suggested
fix with a measurement rather than an opinion. Review found exactly one thing wrong with it, and that
one thing is decisive.

**E-02's CHANGE ALONE DOES NOT MAKE THE TEST MUTATION-SENSITIVE, SO THE PLAN'S OWN DECISIVE EVIDENCE
COULD NOT HAVE BEEN OBTAINED (PR-401, HIGH).** V-02 required the mutation check "in BOTH directions":
the test must FAIL after E-02 under a reason-destroying `edge_satisfied` stub and PASS under the same
stub before it. Review implemented E-02 verbatim as a real pytest module (synthetic `tmp_path` root,
plan file `20260919-s-01-drn999-dep.ipd.md` with `- Status: approved`, token `executed:drn999`, every
original assertion preserved) and ran the matrix. The `after / reason-destroy` cell, the one cell V-02
declares must fail, reports `1 passed`.

The cause is a THIRD fallback the plan never accounts for, and F4 could not have found it because it is
not reachable by any TOKEN choice. When `edge_satisfied` returns an empty reason,
`dependency_status_detailed` substitutes `f"{dep}: dependency not satisfied"`
(`agent_workflows/runner_shared.py`, the `_block(dep, reason or f"{dep}: dependency not satisfied")`
line). Under that substitute every surviving assertion still holds: `not sat` holds because the stub
returns `False`; one diagnostic still renders; `(blocked)` is still absent; and the containment check
`un_reasons[tok] in drain_diags[0]` compares the reason map against a line RENDERED FROM THAT SAME MAP,
so it is true by construction for ANY reason string whatsoever. The assertion set is therefore
insensitive to `edge_satisfied`'s reasons both BEFORE and AFTER E-02, and the only mutation it does
catch (`(True, "")`, which flips `sat`) is caught by `assert not sat` and says nothing about reasons.

Why this is the most consequential possible finding for this particular plan: the plan exists to fix a
test whose green does not mean what its docstring says, and as authored it would have produced a test
whose green does not mean what its own validation section says. An executor honoring every one of the
plan's five prohibitions, removing no assertion and weakening none, would have shipped a test as
insensitive as the one it replaced, and would then have been unable to satisfy V-02 honestly. The
failure mode is exactly the one the plan's F5 diagnoses in `f1b5b9ff`, one level up.

FIXED by adding E-04 and V-04 rather than by editing E-02, because the two are genuinely separate
concerns and separate passes: E-02 moves the control flow (provable by the spy count, no mutation
needed) and E-04 makes the assertion able to notice. E-04 adds three negative-substring guards on the
reason read from `un_reasons`, excluding `unparseable dependency token`, `Cannot locate IPD`, and
`f"{token}: dependency not satisfied"`. The form was MEASURED before being prescribed, in a real pytest
run of the prototyped module:

| form | no mutation | `(False, "")` stub | `(True, "")` stub |
|---|---|---|---|
| pre-E-02 token, live root | passed | passed | passed |
| E-02 only | passed | **passed** | failed |
| E-02 + E-04 guards | passed | **failed** | failed |

and the pre-E-02 form WITH the guards fails on the `unparseable dependency token` guard, which is what
proves the guard discriminates the branch rather than merely being true today. V-04 requires all four
cells plus the E-02-only contrast row, because without that row an executor cannot attribute the
restored sensitivity to E-04 rather than assume it from E-02.

**THE PLAN'S FENCE IS NECESSARY BUT NOT SUFFICIENT, AND IT IS WRITTEN AS SUFFICIENT (PR-402,
MEDIUM).** Every prohibition the plan writes is about not REMOVING or RELAXING an assertion ("DO NOT
weaken any assertion", "do NOT 'fix' this by flipping or deleting an assertion", OQ-01's refusal to
strengthen to exact text). All of them would have been honored by the insensitive outcome PR-401
measures. The missing obligation is ADDITIVE, and no amount of preserving the existing set produces it.
Fixed in `- Scope:`, the Goal, the proposed-changes list, the scope check's under-scope entry, and a
sixth gate prohibition that names stopping after E-02 as the specific way this plan fails.

**THE GUARD NEEDS THREE FALLBACK TEXTS, NOT F4's TWO (PR-403, LOW).** V-02 asked for the reason to be
shown "NOT `unparseable dependency token` and NOT `Cannot locate IPD`", which is F4's enumeration of the
two non-drain arms. Measured, a two-text guard still passes under the mutation, because the substitute
reason contains neither string. Recorded as its own finding so an executor writing E-04 does not trim
the third text back out on the reasoning that F4 lists only two.

NOT RAISED, deliberately, each with the reason it was checked and let stand. The plan's `un_reasons[...]
in drain_diags[0]` containment check is tautological with respect to the reason's CONTENT (it can never
fail on wording), but it is NOT worthless: it pins the renderer property the module docstring claims,
that the mapped reason reaches the output exactly once with no `(blocked)` fallback, and that property
does fail if the renderer stops consulting the map. OQ-01's refusal to convert it to exact equality is
correct and its `csjq81` reasoning is sound. E-03's docstring judgement is also correct: the module
docstring's case (c) becomes TRUE under E-02 plus E-04, so not rewriting it is right. The plan's
`Carrier-Declined` entries are honest, and F6/F7's audits were genuinely performed rather than asserted.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. OQ-01 survives review unchanged and remains non-blocking and correctly resolved.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | high | UNDER-SCOPE | E. Testing and verification | `agent_workflows/runner_shared.py` `dependency_status_detailed` (`_block(dep, reason or f"{dep}: dependency not satisfied")`); `tests/test_dependency_block_reporting.py:131` (`un_reasons[...] in drain_diags[0]`); review probe implementing E-02 verbatim | E-02's repoint does NOT make the test mutation-sensitive, so V-02's mandated `after / reason-destroy` FAILURE could not be observed. Under a `(False, "")` stub the empty reason is replaced by `f"{dep}: dependency not satisfied"`, and every surviving assertion holds: `not sat` holds, one diagnostic renders, `(blocked)` is absent, and the containment check compares the map against a line rendered from that map, so it is true for any string. The plan would have shipped a test as insensitive as the one it replaces, which is `f1b5b9ff`'s failure one level up. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-04 added (three negative-substring guards on the reason from `un_reasons`), measured to fail under the stub and on the pre-change token; V-02's mutation demand moved to V-04 as a four-cell matrix requiring the E-02-only contrast row; F9 records the measurement; F3 corrected to say E-04 and not E-02 flips it; Goal, `- Scope:`, proposed changes and gate swept. |
| PR-402 | medium | IN-SCOPE | G. Plan executability | plan `- Scope:`; E-02's "DO NOT weaken any assertion"; the gate's five prohibitions; OQ-01 | The plan's whole fence is SUBTRACTIVE (remove nothing, relax nothing) and it is written as if that were sufficient. Every prohibition would have been honored by the insensitive outcome PR-401 measures. The required obligation is ADDITIVE: an assertion that discriminates the intended branch from the fallback arms. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `- Scope:` now states the repoint is necessary and not sufficient; the Goal names both halves; the proposed-changes list gains step 4; the scope check's under-scope entry records that E-04 adds assertions by design; a sixth gate prohibition names stopping after E-02. |
| PR-403 | low | IN-SCOPE | E. Testing and verification | plan V-02 (as authored, two guard texts); plan F4 (two non-drain arms); review probe | A guard excluding only F4's two texts still passes under the mutation, because the substitute reason contains neither. The decisive third text (`dependency not satisfied`) is absent from F4 because it is unreachable by any token choice and arises only from an empty `edge_satisfied` reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F11 added recording the measurement and warning against trimming the guard to F4's two; E-04 names all three texts explicitly. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-02 as authored cannot satisfy its own V-02 mutation check. Fix E-02 in place, add a new E-item, or raise it as a blocking question for the maintainer? | Add E-04 (plus V-04) and move V-02's mutation demand onto it, leaving E-02's repoint intact. | (a) Fold the new assertion into E-02: rejected on the right-sizing rubric, since the two are separate concerns with separate evidence (a spy count versus a mutation matrix) and separate failure modes, and bundling them would let an executor report one while doing the other. (b) Raise `- Blocking: yes` for the maintainer: rejected because the repository answers it decisively; review ran the matrix and measured which assertion form the mutant kills, so it is resolvable from evidence rather than a judgement call. (c) Weaken V-02 to drop the mutation requirement: rejected outright, as that is the vacuous-green outcome the plan exists to close. | Prototyped E-02 verbatim as a pytest module; `python3 -m pytest -o addopts="" <probe> -q` matrix: E-02-only `no-mutation passed / reason-destroy passed / satisfy failed`; E-02+guards `passed / FAILED / FAILED`; pre-E-02+guards `FAILED`. | yes |
| D-2 | Which assertion form restores sensitivity without pinning prose that `csjq81` may legitimately change? | Three NEGATIVE substring guards on the reason read from `un_reasons`, excluding `unparseable dependency token`, `Cannot locate IPD`, and `f"{token}: dependency not satisfied"`. | (a) Exact equality on the resolution wording: rejected per the plan's own OQ-01 and P16's "do not assert that specific text remains unchanged"; `csjq81` proposes changing exactly that string. (b) POSITIVE substring assertions on `external target` / `needs one of`: rejected as the same prose pin spelled the opposite way, and measured to be unnecessary since the negative form already kills every mutant the positive one does. (c) Asserting the delegated reason equals `edge_satisfied`'s own return: rejected because it re-implements the producer inside the test and would break the moment either composes differently. | Review probe: negative-guard form measured PASS only on the intended branch, FAIL under `(False, "")`, FAIL under `(True, "")`, FAIL on the pre-change token; two-text variant measured PASS under `(False, "")`. | yes |
| D-3 | PR-401 needs a mutation of `runner_shared.edge_satisfied`, a shared-checkout production file outside this plan's `Scope-Paths`. Edit it briefly, or mutate in memory? | In memory, by rebinding `agent_workflows.runner_shared.edge_satisfied` inside a throwaway probe module, which was then deleted. | (a) Edit-then-revert the tracked module: rejected on the shared-checkout rule and on the plan's own fence; a failed revert leaves production mutated with a green suite. (b) Take V-02's mutation claim on trust: rejected, since it is the plan's decisive evidence and running it is what found PR-401. | `git status --porcelain` empty before and after; the probe was written outside `tests/` and removed; `tests/test_dependency_block_reporting.py` reports `8 passed` unmodified. | yes |
