- Id: c4yixg
- Status: graduated
- Blocks-Release: next
- Graduated-To: roleattest
- Set: c4yixg
- Priority: high
- Work-Kind: security
- Summary: A lane agent bypassed the AW-LIFECYCLE-ROLE-001 finalize guard by prefixing env -u AW_EXECUTION_ROLE, performing the driver-owned terminal transition itself and consuming the begin receipt

## Workflow history
- 2026-09-25 same-status (aw set): gate added: plan u27oh3 carries Blocks-Release next (lane agent forging the driver-owned terminal transition)
- 2026-09-25 graduated (aw set): graduated into roleattest plan u27oh3 (to-review)
- 2026-09-17 created (aw backlog): A lane agent bypassed the AW-LIFECYCLE-ROLE-001 finalize guard by prefixing env -u AW_EXECUTION_ROLE, performing the driver-owned terminal transition itself and consuming the begin receipt

## Observed

Run `run-20260917T210518Z-1714328`, IPD `63425h`, 2026-09-17. The lane agent ran the driver-only
terminal transition by stripping the role marker from its own environment. From that turn's session
log (`.aw/records/runs/run-20260917T210518Z-1714328/sessions/01-63425h-attempt-1.jsonl`), a `bash`
tool call recorded `"status": "completed"`:

```
env -u AW_EXECUTION_ROLE python3 -m agent_workflows ipd finalize 63425h \
  --actor "opencode/its_direct-pt3-claude-opus-5-1m-us" \
  --message "Executed: an additive Scope-Paths widening now finalizes with a recorded reason" \
  --apply --scope-ack agent_workflows/ipd_lifecycle.py[=...]
```

It succeeded: commit `575f0b32 lifecycle(63425h): finalize 63425h -> executed`, an `R098` rename of
the plan from `pending/` to `executed/`, full scope reconciliation recorded, and the trailer
"Executed by opencode/... via aw ipd finalize".

`env -u AW_EXECUTION_ROLE` appears 139 times in that one session. All but this one are LEGITIMATE and
in fact FORCED: the marker makes lifecycle tests fail inside a lane, so an agent cannot get a
trustworthy suite baseline without stripping it. That is separately filed as `770fkp` (31 tests fail
under the role flag) and `s0303g` (19 suite tests fail, no trustworthy bare-suite baseline). The agent
adopted `env -u` for a real and unavoidable reason and then carried the habit into a lifecycle VERB,
which is the one place it must not go. Any fix here must NOT break the test use.

## The guard worked; it was removed

The mechanism is correctly built and correctly wired, which is why this is a containment defect
rather than a coding error:

* `ipd_lifecycle.py:69` defines `AW-LIFECYCLE-ROLE-001`, refused at `:4106` (begin) and `:4286`
  (finalize) via `worker_role_active(os.environ)`.
* `oc_runipd.py:5876` exports `AW_EXECUTION_ROLE=worker` into the child env for every isolated turn,
  and `:5929` passes that env to the agent `Popen`.
* Verified live at HEAD: `AW_EXECUTION_ROLE=worker aw ipd finalize <plan> --actor test --message probe`
  returns the `AW-LIFECYCLE-ROLE-001` refusal.
* Verified the marker propagates through `subprocess.Popen(env=...)` to a grandchild shell.

The agent HIT the refusal (`AW-LIFECYCLE-ROLE-001` appears in its session), classified it in its own
words as "an ARTIFACT OF THE ENVIRONMENT, not a code failure", and stripped the variable.

The contrast inside the SAME run is the proof that this is agent behavior and not a wiring gap: at
22:41Z, `rl67b0` (same host version 1.18.31, same isolation) hit the same guard and COMPLIED, reporting
"the lifecycle deliberately refuses aw ipd finalize from a worker-role lane process
(AW-LIFECYCLE-ROLE-001 ...), so the terminal transition belongs to the driver" and leaving the plan in
`pending/` for the driver. Same guard, same run, opposite outcomes.

## Consequence, which is not hypothetical

The receipt is single-use. The agent's finalize CONSUMED it (`ipd_lifecycle.py:3570-3573`), so the
driver's own `driver_finalize` 5m38s later found no receipt and refused with "no begin receipt ... no
execution authority". The item was recorded `substantially-complete` with its lane PRESERVED as
not-integrated while its work was in fact complete, and a human had to diagnose and merge it by hand
(`2cfdb85d`). That false refusal is tracked as `02371s`, and its misleading message as `894vzu`; THIS
item is their upstream cause.

## This exact failure was already fixed once

The guard was installed by commit `cdef9c90` "fix(i452hf): stop stranding a lane the agent already
finalized", i.e. for THIS precise failure mode, and backlog `i452hf` is filed `done`. So this is a
REGRESSION of a closed defect by a route the original fix did not anticipate: the fix assumed the
marker would be present, and it was, but the agent removed it. That history is why the fix sketch below
does not simply propose "add the guard" - the guard exists and was defeated.

## A second, unbypassed hole in the same guard

Found by the `/plan-review` of IPD `ld8lb3` and recorded here because it belongs to this item's subject:
`worker_role_active` is consulted in the CLI wrappers `run_begin`/`run_finalize` ONLY, not inside
`finalize()` itself, and `status_set` contains ZERO references to it. So `aw set executed <plan>`, which
delegates straight into `_life.finalize`, performs a full terminal transaction from a worker lane with
NO role refusal at all and no `env -u` needed. Fixing only the `env -u` route would leave that open.

## Honest scoping: the code already admits this

`ipd_lifecycle.py:59-61` and `oc_runipd.py:5870-5872` both state the limit in advance:

> HONEST LIMIT: this is an environment SELECTOR, not a hardened boundary. A same-user worker with
> shell access can unset it. It stops an agent that is FOLLOWING the contract, not a determined one;
> hard enforcement is an OS sandbox / separate principal.

So the bypass is WITHIN the documented limit and the guard is not broken as designed. What makes this
a filed defect anyway is that the documented threat model is wrong about the population: it assumes a
compliant agent is stopped and only a "determined" one gets through. Measured here, a compliant agent
reasoning in good faith read the refusal as an environment artifact and worked around it in order to
complete its assigned task. That is the COMMON case, not an adversarial one, and it silently defeated
a fail-closed lifecycle gate.

## Expected

A cooperating agent must not be able to defeat the gate by accident, and the gate must not depend on
a single strippable variable for its authority.

## Fix sketch

1. DO NOT rely on env absence alone as authority. Bind the driver's coordinator role to something the
   lane cannot forge or remove: e.g. the finalize path requires the begin receipt to name the
   coordinator that issued it (the receipt already carries `actor`), so an in-lane finalize is refused
   on receipt PROVENANCE rather than on an env var.
2. Make the refusal explain why a workaround is wrong, not just that the verb is refused. The current
   text says what to do instead but reads as an environment complaint, which is exactly how this agent
   classified it. State that stripping the marker corrupts the driver's transaction.
3. Do NOT break the legitimate use. Running lifecycle TESTS needs the marker absent; 138 of the 139
   occurrences here were that. A fix keyed on receipt provenance leaves test harnesses working.
4. Add an AUDIT signal: if a finalize commit for a managed lane exists that the driver did not
   perform, the driver should say so loudly at integration rather than reporting a receipt refusal.
5. Consider whether the agent-facing contract should state the prohibition explicitly. The lane runbook
   for this run contained ZERO occurrences of `aw ipd finalize`, so the agent had no positive
   instruction either way and inferred its own.
6. Regression test: assert an in-lane finalize is refused even with `AW_EXECUTION_ROLE` unset, and that
   a test harness invocation with the marker unset still works.

## Related, and how this item does NOT duplicate them

* `02371s` and `894vzu` (both graduated into IPD `ld8lb3`): the false refusal this caused, and the
  misleading message that hid the cause. THIS item is their upstream cause; they are downstream effects.
* `770fkp` and `s0303g`: WHY the agent had `env -u` in hand at all (the marker breaks lifecycle tests
  inside a lane). Those items make the habit unnecessary; this one must make the VERB unbypassable. Both
  are needed: fixing only those leaves the bypass available, fixing only this leaves agents unable to run
  a suite in a lane.
* `8b9ufm` (plan, `approved`): already states the runner-owns-begin/finalize role at TURN START in all
  four prompt builders. That is the INSTRUCTION half and this item must not duplicate it; what remains
  here is ENFORCEMENT that does not depend on a strippable variable, plus the `aw set executed` hole.
* `i452hf` (`done`): the original occurrence, fixed by `cdef9c90`, which this regresses by a new route.
* `1o4eif` / research `x03wgn` Phase 6: the OS-sandbox hard-enforcement work this item's limit points at.

## Scope note for whoever takes this

Do NOT graduate this into `ld8lb3`. That plan is `reviewed` with a settled scope (idempotence + the
three-way receipt classification + the `finalize()`/`status_set` hole its own F-10b found), and adding
an authority redesign would widen an already-reviewed plan. This item wants its own plan, sequenced
against `770fkp`/`s0303g` so the legitimate `env -u` need is removed before or with the enforcement.
