---
id: fedqe6
created: 20260922
set: runresidue
order: 00
topic: [runner-unification, duplication, hostdedup]
model:
kind: findings
status: active
outcome: adopted
summary: Per-symbol SHARE/HOST-SPECIFIC decision for every symbol still co-defined in both host runners, measured at HEAD 2d04ef8b with the committed scanner
consumed-by: [gqo6if]
---

# The runner residue, decided per symbol

This is IPD `gqo6if` (runresidue 01) E-02's deliverable: the residue between `oc_runipd` and
`agy_runipd`, decided SYMBOL BY SYMBOL against the maintainer's own test for a legitimate host
difference, rather than against a similarity threshold.

## The test being applied

The maintainer's ruling, quoted from the `rununify` Set's child-breakdown note: `oc_runipd` is the
preferred version "unless a difference is a real capability (one host does A, the other NOT A)".

Two corollaries were settled in this plan's own open questions and are applied below. A difference
only in log or prompt WORDING is NOT a capability difference, so it is shared with the wording
injected (OQ-01; `HostLabels` is the established mechanism). A difference in BEHAVIOR is reported and
the symbol left forked, because this is an extraction whose validation rests on nothing changing
(OQ-02).

## How to reproduce every figure here

One command, by path:

    python3 tools/runner_fork_scan.py

For a single symbol, add `--symbols <name>`; for the dependency question, `--closure`; for the
three-way case, `--triples`; for machine consumption, `--json`.

STATE YOUR METRIC BESIDE ANY LINE FIGURE. Three line metrics circulate in this area and they differ
by more than 2x on the same symbol (`reclaim_lanes_on_interrupt` measured 73 by `ast.unparse` and 252
by raw source span). Every line count in this document is `ast.unparse` with docstrings stripped, and
the similarity is a `difflib` ratio taken AFTER host tokens are normalized to a placeholder.

A SIMILARITY IS NOT A DECISION. The table below contains a 0.999 pair that is a legitimate host
difference and a 0.921 pair that is also one, while a 0.976 pair is a DEFECT. No threshold reproduces
the decisions; each was read.

## Headline measurement at HEAD `2d04ef8b`

| Quantity | Value | The test that produced it |
|---|---|---|
| co-defined in both runners | 58 | a top-level `def`/`class` of the same name exists in both modules |
| STRICT residue | 8 symbols / 64 agy lines | neither side references `runner_shared` anywhere in its body |
| LOOSE residue | 20 symbols / 602 agy lines | neither side is a single-statement `runner_shared` delegation |
| sanctioned thin wrappers | 38 | both sides are a one-statement delegation (the target form, NOT duplication) |

RECONCILIATION AGAINST THE PLAN'S OWN FIGURES, which is required rather than optional because this
area has now produced unreproducible numbers three times.

* The plan's `F-01` claimed 58 co-defined, 32 both-delegating, 1 one-side-delegating. Co-defined
  REPRODUCES exactly at 58. The delegation split has MOVED: 49 both-delegate, 1 one-side, 8 neither.
* The plan's `F-02` claimed 23-25 strict and 36-37 loose. Both are now SMALLER: 8 strict, 20 loose.
* THE MOVEMENT IS EXPLAINED AND IS NOT DRIFT IN THE MEASUREMENT. Commit `12a5c05b`
  ("lift(li44r9): give 16 byte-identical runner symbols one definition each") landed after this plan
  was reviewed and shared sixteen of the symbols the plan lists as its own lift targets. This is the
  plan's own stated reason for making the scanner authoritative over its prose.
* The remaining strict-count difference from 23 to 8 is that the review-time measurement's strict
  test was applied to a tree where those sixteen symbols still had real bodies.

## The decisions

### Already one implementation: NOTHING TO DO (verified, not assumed)

Sixteen of the eighteen symbols this plan's cluster items (E-04, E-06, E-07, E-08) name as lift
targets are ALREADY pure single-statement delegations on both sides, with the implementation in
`runner_shared`. They are recorded here as SKIPPED WITH EVIDENCE rather than lifted, because the plan
makes lifting an already-delegating symbol a validation FAILURE:

| Symbol | Plan item that named it | State at this HEAD |
|---|---|---|
| `_escalation_recorder` | E-04 | both sides pure delegation; impl in `runner_shared` |
| `_budget_breach_recorder` | E-04 | both sides pure delegation |
| `build_isolation_notice` | E-04 | both sides pure delegation |
| `run_lock` | E-06 | both sides pure delegation |
| `locked_run` | E-06 | both sides pure delegation |
| `evaluate_clean_base_for_launch` | E-06 | both sides pure delegation |
| `set_plan_approved` | E-07 | both sides pure delegation |
| `_record_checkpoint_stop` | E-08 | both sides pure delegation |
| `_record_deliberate_stop` | E-08 | both sides pure delegation |
| `_observe_between_turn_stop` | E-08 | both sides pure delegation |
| `install_stop_triggers` | E-08 | both sides pure delegation |
| `handle_stop_command` | E-08 | both sides pure delegation |
| `terminate_process` | E-08 | both sides pure delegation |
| `requeue_interrupted` | E-08 | both sides pure delegation |
| `reconcile_interrupted` | removed at review (F-09) | both sides pure delegation, confirmed |
| `driver_finalize` | flagged at review (F-09) | both sides pure delegation, confirmed |

CONSEQUENCE FOR E-06 AND E-07, stated plainly. `run_lock` and `locked_run` are already one
implementation, so spec `c4gd2h` R2's observable `driver.lock` release is already governed by ONE
body and this plan changes nothing about it. `set_plan_approved` is likewise already shared, so the
misattribution hazard E-07 was written to guard against (a per-host `--actor` reaching a plan's
permanent history) is already resolved behind the descriptor; no lift, and therefore no
both-directions attribution test, is available for this plan to perform.

### SHARED by this plan

| Symbol | oc/agy lines | similarity | Decision | Note |
|---|---|---|---|---|
| `reclaim_lanes_on_interrupt` | 73 / 73 | 0.998 | **SHARE (done)** | The anchor. Identical length; the two copies differed in ONE statement and only in its SPELLING (`f"Reason: {reason}."` against `"Reason: {0}.".format(reason)`). One implementation in `runner_shared`, a host shell each, injecting the two per-host prompt symbols keyword-only with no default. |

### HOST-SPECIFIC, with the capability sentence

| Symbol | oc/agy lines | similarity | What one host does that the other does not |
|---|---|---|---|
| `disable_lane_prompt` | 3 / 3 | 1.000 | Each host WRITES ITS OWN module-level `_LANE_PROMPT_DISABLED`, which only that host's `_lane_reclaim_prompt` reads; a shared body would set a flag nobody reads, so prompt suppression on a repeated interrupt would silently stop working and an unattended run would pause on a question nobody can answer. Pinned by `tests/test_runner_shared.py::UnmovableSymbolTests` and `tests/test_hostdedup_identical_lift.py::TheDeliberatelyUnliftedSymbol`. |
| `_lane_reclaim_prompt` | 29 / 29 | 0.951 | READS that per-host flag, which is the other half of the pin above. The two bodies differ only cosmetically (f-string against `.format`), so this is the one residue pair a FUTURE plan could legitimately unify, but only together with the flag, and doing so changes the premise of a shipped pin. Left forked here deliberately; `TheDeliberatelyUnliftedSymbol::test_the_premise_of_the_pin_still_holds` asserts the two stay non-identical, and it is the guard that will flag when this becomes revisitable. |
| `_add_output_mode_flags` | 6 / 6 | 0.921 | A REAL CAPABILITY DIFFERENCE IN THE HELP TEXT, and it is not mere wording: oc's `--raw` is documented "(legacy behavior)" and oc's `-v` promises "line ranges and hit counts" while `-vv` shows "diff hunks and diagnostics"; agy's `-vv` shows "raw tool parameters" instead. The two hosts' event streams genuinely carry different things, so the help text describes different observable behavior per host. Shareable LATER behind `HostLabels` if someone wants to (OQ-01 would then apply), but the strings are not interchangeable today. |
| `_record_forced_stop` | 11 / 11 | 0.999 | NOT A CAPABILITY DIFFERENCE, AND NOT SAFE TO LIFT HERE EITHER. The only difference is an annotation QUOTING style (`stop: runner_stop.StopNowForce` against `stop: 'runner_stop.StopNowForce'`). A `runner_shared` copy ALREADY EXISTS and is byte-different from both. This is therefore a THREE-WAY fork, filed as backlog `2yjc5l`'s sibling case rather than lifted, because choosing which of three bodies is canonical is the reconciliation OQ-02 excludes. |
| `enforce_dependency_preflight` | 8 / 6 | 0.265 | agy ALREADY DELEGATES, but to `oc_runipd` (a PEER HOST) rather than to `runner_shared`. So the symbol is not duplicated, it is mis-layered: there is ONE body and agy imports it. Re-homing it into `runner_shared` is `runnerlayer` Order 02 (`1f7xno`)'s declared work, which owns the `FROZEN_OC_TO_AGY_IMPORTS` table this symbol sits in. Not this plan's to move. |
| `route_recovery_turn` | 16 / 3 | 0.144 | Same shape: agy delegates to `oc_runipd`, so there is one live body. A dead `runner_shared` copy also exists. Filed as backlog `2yjc5l`; move owned by `1f7xno`. |
| `classify_recovery_disposition` | 23 / 3 | 0.082 | Same shape, AND THE DEAD SHARED COPY IS BEHAVIORALLY DIFFERENT: the live body classifies a preserved commit with `worktree_lease.commit_subject_is_interrupted_snapshot(subject)`, the dead shared copy with `subj.startswith('wip(snapshot):')`. Pointing the hosts at the shared copy would change recovery routing on BOTH hosts. Filed as backlog `2yjc5l`. |
| `build_verify_and_continue_notice` | 26 / 3 | 0.084 | Same shape, and its DESTINATION IS FORMALLY CONTESTED: `tests/test_runner_layering.py::MOVE_UNSETTLED` records that a wording function may belong to `render_stream` rather than `runner_shared`, and assigns the question to `1f7xno`. Deciding it here would pre-empt another plan's open question. |
| `handle_audit_command` | 58 / 4 | 0.062 | A GENUINE CAPABILITY DIFFERENCE, and the clearest instance of the maintainer's own test in the whole residue: oc IMPLEMENTS the audit verb, agy REFUSES it with an exit-2 message pointing the operator at the other host, deliberately, because "the verb buys ONE independent opinion, so it is wired on one host deliberately (plan `mp289j`) rather than duplicated". One host does A, the other NOT A. |

### The five large host-shaped functions: out of scope by prior ruling

`run_queue`, `main`, `build_parser`, `execute_item` and `initialize_run` all appear in the loose
residue and are NOT residue. They are the CORE-PLUS-HOOK end state the maintainer chose on
2026-09-14, and each already delegates into `runner_shared` on both sides. `expand_selectors`,
`retry_deferred_integrations`, `reconcile_disposition`, `StallWatchdog`,
`_integrate_stranded_lanes` and `handle_integrate_command` are in the same class: both sides
delegate, and what remains per host is the host-shaped shell.

TWO OF THOSE SHELLS NONETHELESS CARRY DIFFERENCES WORTH NAMING, found while reading them and
reported rather than absorbed:

* `reconcile_disposition` (40 / 40, 0.976) - oc indexes `item['configured_file']` where agy uses
  `.get(..., '')`, so oc RAISES `KeyError` where agy returns `('partial', None)`. Reproduced
  directly. Filed as backlog `2t4v1j`, `Work-Kind: bug`, because the call sites are inside
  `dispatch_turn`'s deliberate-stop handlers.
* `expand_selectors` (94 / 94, 1.000 after normalization) and `retry_deferred_integrations`
  (46 / 46, 0.998) differ only in a loop variable name (`setid` against `_setid`) and in one
  defensive copy (`item` against `dict(item)`). Neither is a defect; both are noted so a later
  reader does not mistake them for one.

## What the directive's remainder actually is, stated honestly

The maintainer's 2026-09-16 directive asked for "one code base shared by the two runners that
contains 100% of the otherwise redundant code". After this plan, the honest answer is:

1. ONE symbol of genuine copied code remained and is now shared (`reclaim_lanes_on_interrupt`,
   73 lines).
2. TWO symbols are genuinely host-specific by the maintainer's own test
   (`handle_audit_command`, `_add_output_mode_flags`).
3. TWO symbols are a deliberate, test-pinned pair that cannot move while a module-level `global`
   backs them (`disable_lane_prompt`, `_lane_reclaim_prompt`), with the guard that will tell a
   future reader when that stops being true.
4. FOUR symbols are NOT duplication at all but MIS-LAYERING: agy delegates to `oc_runipd` instead of
   to `runner_shared`. There is one body each. Re-homing them is `runnerlayer` Order 02 (`1f7xno`)'s
   declared scope, and this plan must not race it.
5. SIX symbols carry a DEAD THIRD COPY in `runner_shared` that no host reaches, and at least one of
   those copies is behaviorally different from the code actually running. That is strictly worse than
   a two-way fork and is filed as backlog `2yjc5l`.

So the directive is substantially met, the remainder is enumerated rather than estimated, and the two
things standing between here and "100%" are one other plan's declared work (4) and one maintainer
decision about which of three bodies is correct (5). Neither is a measurement gap.
