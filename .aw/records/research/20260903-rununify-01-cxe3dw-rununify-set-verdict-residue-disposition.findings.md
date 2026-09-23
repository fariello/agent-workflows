---
id: cxe3dw
created: 20260923
set: rununify
order: 01
topic: [runner-unification, duplication, set-verification]
model:
kind: findings
status: active
outcome: adopted
summary: Per-symbol disposition of every residue symbol between the host runners at HEAD b61d4252, and the rununify Set's verdict against the maintainer's one-shared-codebase directive
consumed-by: [40it5e]
---

# The rununify residue, dispositioned per symbol, and the Set's verdict

This is IPD `40it5e` (rununify 12) E-02's deliverable, which is in turn the orchestrator `5e4sb6`'s
own E-03. It dispositions EVERY symbol in the measured residue between `oc_runipd` and `agy_runipd`
against the maintainer's test for a legitimate host difference, and it is the input `40it5e` E-04
states the Set's verdict from.

## What this document is NOT, stated first because a sibling already exists

Research `fedqe6` (`runresidue` 00) asked a question of the same shape one day earlier, and this is
not a copy of it. Three differences matter, and the third is the reason this document exists at all.

1. DIFFERENT HEAD. `fedqe6` measured at `2d04ef8b`. This measures at `b61d4252`, after `gqo6if`
   executed and integrated.
2. DIFFERENT SCOPE. `fedqe6` dispositioned the residue in order to decide what `gqo6if` should LIFT.
   This dispositions it in order to answer whether the SET is done, which is a different question with
   a different bar: a symbol that is legitimately host-shaped is a satisfactory END STATE here while it
   was merely "not my work" there.
3. INDEPENDENTLY RE-DERIVED, NOT INHERITED. Every disposition below was re-measured from the source at
   this HEAD. Where it agrees with `fedqe6` that is a reproduction and is stated as one; where the
   underlying facts have moved, this document records the movement. Copying a sibling's table would
   have made this plan's verdict rest on someone else's measurement, and this plan exists precisely
   because a verdict in this area was once taken on trust and was wrong.

## The test being applied

The maintainer's ruling, quoted from the `rununify` Set's child-breakdown note: `oc_runipd` is the
preferred version "unless a difference is a real capability (one host does A, the other NOT A)".

And the maintainer's 2026-09-16 directive, which is the Set's definition of done: "at the end of the
SET, there should be one code base shared by the two runners that contains 100% of the otherwise
redundant code".

THE OPERATIVE WORD IS "OTHERWISE REDUNDANT". A symbol that is genuinely host-shaped is not redundant
code, so leaving it forked does not violate the directive. That is what makes a per-symbol reading
necessary and a count insufficient.

## How to reproduce every figure here

One command, by path:

    python3 tools/runner_fork_scan.py --all

`40it5e` E-01 extended that committed scanner with the `--repo-wide` sweep this document's class (d)
section needs; every other number comes from sections that already existed. For one symbol, add
`--symbols <name>`; for machine consumption, `--json`.

STATE YOUR METRIC BESIDE ANY LINE FIGURE. Three line metrics circulate in this area and differ by more
than 2x on the same symbol. Every line count here is `ast.unparse` with docstrings stripped, and every
similarity is a `difflib` ratio taken AFTER host tokens are normalized to a placeholder.

A SIMILARITY IS NOT A DECISION. The table below contains a 1.000 pair that is a legitimate host
difference and a 0.062 pair that is also one. No threshold reproduces these decisions; each was read.

## Headline measurement at HEAD `b61d4252`

| Quantity | Value | The test that produced it |
|---|---|---|
| co-defined in both runners | 58 | a top-level `def`/`class` of the same name exists in both modules |
| sanctioned thin wrappers | 38 | both sides are a one-statement `runner_shared` delegation (the TARGET form, not duplication) |
| STRICT residue | 8 symbols / 64 agy lines | neither side references `runner_shared` anywhere in its body |
| LOOSE residue | 20 symbols / 602 agy lines | neither side is a single-statement `runner_shared` delegation |
| BOTH-DELEGATE | 49 | each side reaches `runner_shared` somewhere |
| ONE-SIDE-DELEGATES | 1 | exactly one side does (`handle_audit_command`) |
| NEITHER-DELEGATES | 8 | the strict residue |
| runner symbols with ONE definition repo-wide | 65 | defined in exactly one module of `agent_workflows/`, runners included |
| co-defined OUTSIDE `runner_shared` | 5 names / 15 co-definitions | the repo-wide class (d) sweep |
| class (d) re-forks (AST-identical elsewhere) | **0** | of those 15, none has an identical body |

### Reconciling against the three figures already in circulation

Required rather than optional, because this area has produced an unreproducible number four times now
and the plan this document serves was itself written to correct one.

| Source | Its figure | At this HEAD | Why it moved |
|---|---|---|---|
| `40it5e` as authored | 58 symbols / 2711 agy lines, "directive UNMET" | not reproducible under any test | It counted NAMES. A successfully de-duplicated symbol keeps its name in both runners by design (the `818uru` OQ-02 wrapper ruling), so this counted the extraction's SUCCESS as its failure. |
| `40it5e` review (`73e370ae`) | 23 NEITHER-DELEGATES / 661 agy lines | 8 / 64 | `12a5c05b` (`li44r9`) gave 16 byte-identical symbols one definition each, and `2d04ef8b` (`gqo6if`) shared `reclaim_lanes_on_interrupt`. Both landed after that measurement. |
| `fedqe6` (`2d04ef8b`) | 8 strict / 64 lines, 20 loose / 602 lines | 8 / 64, 20 / 602 | REPRODUCES EXACTLY. `gqo6if` changed no runner code after that measurement. |

So the residue has moved in one direction throughout, and the honest summary of the trend is that
every re-measurement since the original name-count has found LESS duplication, not more.

## The dispositions

Every symbol in the strict residue (8) plus the ONE-SIDE-DELEGATES class (1) is dispositioned below:
nine rows, which is the whole judgement set. `40it5e` V-02 requires all of them, so none is elided.

BOTH-DELEGATE SYMBOLS ARE DELIBERATELY NOT DISPOSITIONED, and this is a correction the plan's review
made to its own earlier bar. A BOTH-DELEGATE symbol already has ONE implementation with a host-shaped
shell over it, which is the sanctioned target form; dispositioning 49 of them would pad this table
with 49 "already done" rows and bury the nine that require a decision. Two of those shells nonetheless
carry differences worth naming, and they are recorded in their own section below rather than silently
absorbed.

### Disposition summary

| Disposition | Count | Symbols |
|---|---|---|
| HOST-SPECIFIC by the maintainer's test | 2 | `handle_audit_command`, `_add_output_mode_flags` |
| HOST-SPECIFIC by mechanism (a per-host `global`) | 2 | `disable_lane_prompt`, `_lane_reclaim_prompt` |
| NOT DUPLICATION: mis-layered, ONE body exists | 4 | `enforce_dependency_preflight`, `route_recovery_turn`, `classify_recovery_disposition`, `build_verify_and_continue_notice` |
| STILL REDUNDANT: genuine duplication | **1** | `_record_forced_stop` |

THE STILL-REDUNDANT COUNT IS ONE, and it reconciles with E-01's output as follows: 8 strict residue
plus 1 one-side-delegates is 9 rows; 2 are host-specific by capability, 2 by mechanism, 4 are
mis-layering with a single body, leaving exactly 1.

### HOST-SPECIFIC by the maintainer's own test (one host does A, the other NOT A)

| Symbol | oc/agy lines | sim | What one host does that the other does not |
|---|---|---|---|
| `handle_audit_command` | 58 / 4 | 0.062 | THE CLEAREST INSTANCE OF THE TEST IN THE WHOLE RESIDUE. oc IMPLEMENTS the `audit` verb; agy REFUSES it with exit 2 and names the spelling that works. Read at this HEAD: the agy docstring states the refusal is deliberate because "the verb buys ONE independent opinion, so having it on one host is the whole product, while a second launch path doubles the review burden". It also records WHY a refusal beats no binding at all (the shared declaration would parse `audit <id6>` and fall through to "Unknown command", documenting a verb that does not exist). One host does A, the other explicitly NOT A. |
| `_add_output_mode_flags` | 6 / 6 | 0.921 | A REAL CAPABILITY DIFFERENCE IN WHAT THE TWO EVENT STREAMS CARRY, not mere wording, and re-verified by reading both help strings at this HEAD. oc's `--raw` is documented "(legacy behavior)" and agy's is not; oc's `-v` promises "line ranges and hit counts" and `-vv` "diff hunks and diagnostics", while agy's `-vv` shows "raw tool parameters". The strings describe different observable behavior per host, so they are not interchangeable. Shareable LATER behind `HostLabels` if someone wants the flag PLUMBING unified, but the text is host-specific today. |

### HOST-SPECIFIC by mechanism: the test-pinned pair

| Symbol | oc/agy lines | sim | Why it cannot move |
|---|---|---|---|
| `disable_lane_prompt` | 3 / 3 | 1.000 | A 1.000 SIMILARITY THAT IS NOT A DEFECT, which is why this document says a ratio is not a decision. Each host writes its OWN module-level `_LANE_PROMPT_DISABLED` through `global`, and only that host's `_lane_reclaim_prompt` reads it. A shared body would set a flag nobody reads, so prompt suppression after a repeated interrupt would silently stop working and an unattended run would block on a question nobody can answer. RECORDED IMMOVABILITY, CHECKED BEFORE CALLING IT REDUNDANT: pinned by `tests/test_runner_shared.py::UnmovableSymbolTests` and `tests/test_hostdedup_identical_lift.py::TheDeliberatelyUnliftedSymbol`. |
| `_lane_reclaim_prompt` | 29 / 29 | 0.951 | READS that per-host flag, so it is the other half of the pin above. Re-diffed at this HEAD: the two bodies differ in exactly TWO statements and both differences are cosmetic (`print(file=...)` against `print('', file=...)`, and an f-string against `.format`). So this is the one residue pair a FUTURE plan could legitimately unify - but only TOGETHER WITH THE FLAG, and doing so changes the premise of a shipped pin. `TheDeliberatelyUnliftedSymbol::test_the_premise_of_the_pin_still_holds` asserts the two stay non-identical and is the guard that will flag when this becomes revisitable. |

### NOT DUPLICATION AT ALL: mis-layering, with exactly ONE live body

These four are the most important correction in this document, because a count of "symbols defined in
both runners" reports them as duplication and they are not. In each case the agy definition is a
delegation, so ONE implementation exists; what is wrong is WHERE it lives. agy delegates to
`oc_runipd`, a PEER HOST, rather than to `runner_shared`.

Verified by reading each agy body at this HEAD; all four contain `from agent_workflows.oc_runipd
import <name>` and call it.

| Symbol | oc/agy lines | sim | Reading | Carrier |
|---|---|---|---|---|
| `enforce_dependency_preflight` | 8 / 6 | 0.265 | agy delegates to oc and keeps an `except DriverError: raise` its own docstring calls a DELIBERATE no-op. One body. | `1f7xno` |
| `route_recovery_turn` | 16 / 3 | 0.144 | agy body is a three-line delegation whose docstring says "Delegate to the ONE definition in `oc_runipd`". One body. | `1f7xno` |
| `classify_recovery_disposition` | 23 / 3 | 0.082 | Same shape, same docstring form. One body. | `1f7xno` |
| `build_verify_and_continue_notice` | 26 / 3 | 0.084 | Same shape. Its DESTINATION is formally contested: `tests/test_runner_layering.py::MOVE_UNSETTLED` records that a wording function may belong in `render_stream` rather than `runner_shared`, and assigns that question to `1f7xno`. | `1f7xno` |

WHY THIS IS STILL A REAL FINDING even though one body exists: it makes the two hosts non-peers. The
`rununify` orchestrator recorded the same structural point at authoring time ("agy_runipd already
imports 40 names FROM oc_runipd, so the runners are not peers and a shared library is a layering
correction"). Re-homing them is `runnerlayer` Order 02 (`1f7xno`, `Status: approved`), which owns the
`FROZEN_OC_TO_AGY_IMPORTS` table these four sit in. Not this plan's to move, and not `gqo6if`'s
either.

### STILL REDUNDANT: the one genuine duplication

| Symbol | oc/agy lines | sim | Finding |
|---|---|---|---|
| `_record_forced_stop` | 11 / 11 | 0.999 | GENUINE DUPLICATION, AND A THREE-WAY ONE. Diffed at this HEAD: the oc and agy bodies differ in EXACTLY ONE token, the annotation quoting `stop: runner_stop.StopNowForce` against `stop: 'runner_stop.StopNowForce'`. That is not a capability difference under any reading. It is nonetheless NOT safely liftable by a verification plan, because a THIRD copy exists in `runner_shared` that is byte-different from both, so lifting means choosing which of three bodies is canonical - a reconciliation, not an extraction. Carried by backlog `2yjc5l`. |

### The dead third copies, measured independently

Six residue-or-shell symbols also have a `runner_shared` definition. For four of them I checked
whether ANY host reaches the shared copy, by searching `agent_workflows/*.py` for
`runner_shared.<name>`: `_record_forced_stop`, `build_verify_and_continue_notice`,
`classify_recovery_disposition` and `route_recovery_turn` have ZERO such references. The shared copies
are DEAD CODE.

That is strictly worse than a two-way fork, and one of them is worse still: `fedqe6` measured the dead
`classify_recovery_disposition` copy as BEHAVIORALLY DIFFERENT from the live body (the live one tests a
preserved commit with `worktree_lease.commit_subject_is_interrupted_snapshot`, the dead one with
`subj.startswith('wip(snapshot):')`), so pointing the hosts at the shared copy would change recovery
routing on BOTH hosts. Carried by backlog `2yjc5l` (`Work-Kind: bug`, `Blocks-Release: next`).

### Differences inside BOTH-DELEGATE shells, named rather than absorbed

Not residue, and not dispositioned above, but recorded so a later reader does not rediscover them as
new:

* `reconcile_disposition` (40 / 40, 0.976) - oc indexes `item['configured_file']` where agy uses
  `.get(..., '')`, so oc RAISES `KeyError` where agy returns `('partial', None)`. A real behavioral
  divergence inside a shell. Carried by backlog `2t4v1j` (`Work-Kind: bug`, `Blocks-Release: next`).
* `expand_selectors` (94 / 94, 1.000 normalized) and `retry_deferred_integrations` (46 / 46, 0.998)
  differ only in a loop variable name and one defensive copy. Neither is a defect.

### The five large host-shaped functions are NOT residue

`run_queue`, `main`, `build_parser`, `execute_item` and `initialize_run` appear in the LOOSE residue
and are excluded from the strict one, correctly. They are the CORE-PLUS-HOOK end state the maintainer
chose on 2026-09-14, and each already delegates into `runner_shared` on BOTH sides. Counting them as
duplication is the single largest component of the original 2711-line figure and is the error this
document exists to avoid repeating.

### Class (d): the repo-wide question, answered

`rununify` E-03 requires the single-implementation check be repo-wide rather than pairwise, because
"a pairwise check passes while a third copy sits in another module" (its F10, which cost a real drift:
`Heartbeat` was fixed in `render_stream` and the fix silently never reached `aw agy run`).

Measured with E-01's new `--repo-wide` sweep: 15 co-definitions across 5 names live outside
`runner_shared`, and ZERO of them is AST-identical to the runner body. Every one is a NAME COLLISION.

| Name | Also defined in | Verdict |
|---|---|---|
| `main` | 9 modules | collision; nine modules define a `main` |
| `build_parser` | 3 modules | collision, max similarity 0.067 |
| `terminate_process` | `runner_shutdown` | NOT a collision but NOT a fork: the runners delegate to `runner_shared`, which delegates to `runner_shutdown`. That is the OWNING module and the chain is correct. |
| `validate_manifest` | `benchmark_manifest` | collision, 0.085; different domain entirely |
| `resolve_agy` | `agy_run` | THE ONE WORTH A SECOND LOOK, at 0.887. Two bodies, differing in their raise type (`DriverError` against `ScriptError`) and one variable name. `tvnq50` already flagged it in 2026-09-03 and declined to call it a re-fork because `agy_run` is a separate single-target multi-mode runner, not the queue driver. That reading holds: the two modules have different error vocabularies, so neither can import the other's raise without a translation. Left as-is, reported rather than filed, since no plan in this Set scopes `agy_run`. |

So the class (d) re-fork set is EMPTY at this HEAD. The `rununify` child 01 (`2r306y`) work that
deleted the `render_stream` re-forks has held, and the symmetric guard
(`tests/test_runner_refork_guard.py`) is what keeps it holding.

## The verdict this supports

Stated here as the measurement's conclusion; `40it5e` E-04 is where it is formally recorded.

Against "one code base shared by the two runners that contains 100% of the otherwise redundant code",
the literal answer is **NO, with a residue of ONE symbol (`_record_forced_stop`, 11 agy lines by
`ast.unparse`, under the STRICT test)**.

And the magnitude is what makes that NO honest rather than alarming. Of 58 co-defined symbols, 38 are
sanctioned thin wrappers and 49 delegate on both sides; the class (d) re-fork set is empty; 65 runner
symbols have exactly one definition repo-wide. Of the nine symbols requiring a judgement, four are
genuinely host-shaped (two by capability, two by a pinned mechanism), four are one body in the wrong
place with a named carrier, and one is duplication. The eleven children plus `gqo6if` took this from
"two copies of one program" to one shared library with host-shaped shells over it.

What stands between here and a literal 100 percent is: one maintainer decision about which of three
bodies is canonical (`2yjc5l`), and one other plan's declared layering work (`1f7xno`). Neither is a
measurement gap, and neither is `rununify`'s to do.
