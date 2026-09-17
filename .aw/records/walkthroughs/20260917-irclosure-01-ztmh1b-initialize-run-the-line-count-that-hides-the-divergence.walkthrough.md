# Walkthrough: `initialize_run`, the line count that HIDES the divergence (`rununify` Order 09, `orziju`)

- Date: 2026-09-17
- Id: ztmh1b
- Target-Id: orziju
- Plan: `.aw/records/plans/pending/20260915-rununify-09-orziju-split-initialize-run-into-a-shared-core-and-a-thin-host-hook.ipd.md`
- Base commit: `87682a3b`
- Executed by: opencode/its_direct-pt3-claude-opus-5-1m-us, in lane `aw/lane/orziju`
- Set: irclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`, because a walkthrough may not reuse the Set id of another artifact type)

## Why this walkthrough exists

Three reasons, in descending order of importance.

FIRST, **the sharpest hazard in the whole `rununify` Set was MEASURED here rather than argued.** The
plan's F-9 claims that relocating this function's body to `runner_shared` would silently make every
run host-unattributable, because `__file__` is evaluated in the DEFINING module and two consumers
read that basename as the host discriminator. That was a code-reading claim. It is now a
measurement: sabotaging agy exactly as a naive relocation would, `tests/test_run_analytics_sources.py`
+ `tests/test_run_viewer.py` + `tests/test_run_analytics.py` stayed **183 passed** while every agy run
became `unknown`. No test in the repository covered the runners' end of that contract. That is the
kind of defect a green suite actively conceals, and it is now pinned in both directions.

SECOND, a reader coming to this plan later will see a title that says "split `initialize_run` into a
shared core and a thin host hook" and a record saying no split was performed, and will reasonably ask
whether the work was abandoned. It was not. The plan as re-scoped at its 2026-09-16 review is a
MEASURE-AND-GUARD plan and it did all five of its items.

THIRD, **this function is the one where the headline number actively misleads**, and the reason
generalizes to every "these two functions are nearly identical" claim. It has the HIGHEST line-level
similarity of the five large functions in this Set and the LOWEST shared content. Both numbers are
correct. Reading either alone gives the wrong answer.

## Number one: the divergence hides inside two lines

Every load-bearing number the plan states about the function body reproduced EXACTLY at execution
HEAD `87682a3b`:

| Quantity | Plan's claim | Measured |
|---|---|---|
| Raw lines, oc / agy | 409 / 339 | 409 / 339 |
| **Differing lines under AST normalization** | **15** | **15** |
| Similarity ratio | 0.9345 | 0.9345 |
| Differing lines bearing a host token | 4 (corrected at review from 6) | 6 by a literal token scan, 4 by the review's stricter reading |

15 differing lines out of ~115 normalized is why the split LOOKS cheap. **Two of those fifteen are
the `state` and `queue.append` DICT LITERALS**, which are one line each only because AST
normalization collapses them. Unpacked, they are where all the divergence lives.

### The `options` partition, three ways, all agreeing on 13

The plan's review counted the keys the two dict bodies SPELL and got 10 shared / 7 oc-only / 6
agy-only = 23. That reproduces. But it omits two things, so this execution measured all three views:

| View | Shared | OC-only | AGY-only | Union | Host-specific |
|---|---|---|---|---|---|
| Source literals, conditional keys excluded (the plan's view) | 10 | 7 | 6 | 23 | **13** |
| Source literals, including the four conditional `verify_*` keys | 10 | 11 | 6 | 27 | 17 |
| **A LIVE frozen run on each host** (includes the 12 shared policy keys) | 21 | 7 | 6 | 34 | **13** |

**The load-bearing number is 13 and it is identical under the first and third views.** That
coincidence is worth stating because it is not a coincidence: the shared count rises from 10 to 21
entirely through the ONE `**runner_shared.freeze_run_policy_flags(args)` expansion, which is
ALREADY de-duplicated. So every additional shared key in this dict arrived by de-duplicating
something else, while the thirteen host-specific ones sit exactly where they were.

Three of the thirteen are not cosmetic:

* `launch_profile` exists only because oc has a launch-profile store. **`agy_runipd` contains ZERO
  `runner_profiles` references against oc's 17**, so this is a concept the other host does not have.
* `agy_executable` is read at `agy_runipd.py:3010` to resolve the binary.
* `no_audit` and `no_verify` are **opposite-polarity spellings of one concept**. Getting the polarity
  wrong would make "verify" mean "do not verify" with no error anywhere (`ybkmzp` E-04's note).

A "shared writer with a thin hook" would therefore take thirteen key parameters. That is not a hook
supplying host specifics. It is the function's entire output supplied by its caller.

## Number two: the `__file__` hazard, measured

`initialize_run` freezes each run's own provenance (`oc_runipd.py:3745`, `agy_runipd.py:2455`):

```python
"driver": {
    "path": str(Path(__file__).resolve()),
    "sha256": sha256_file(Path(__file__)),
},
```

`__file__` is evaluated in the module where the code is DEFINED. A core relocated to `runner_shared`
writes `runner_shared.py` for BOTH hosts. Two consumers then fail:

* `run_analytics_sources.driver_generation` (`:183-207`) maps the BASENAME through
  `DRIVER_GENERATIONS`, and its own docstring records that "the basename is the ONLY discriminator
  that works";
* `run_viewer.load_run_summary` (`:865-870`) substring-matches `oc_runipd` / `agy_runipd` to label a
  run `OpenCode` / `Antigravity`.

**MEASURED, not inferred.** agy was sabotaged to write `runner_shared.__file__`, which is precisely
what the relocation does, and the three analytics/viewer suites were run:

```
$ python3 -m pytest tests/test_run_analytics_sources.py tests/test_run_viewer.py \
      tests/test_run_analytics.py -o addopts=""
183 passed in 4.25s
```

183 green on code where every agy run is now host-unattributable. The rest of the suite was checked
too: `tests/test_oc_runipd.py` produced a failure set BYTE-IDENTICAL to its pre-sabotage baseline
(9 failures, the `AW_EXECUTION_ROLE=worker` lifecycle guard, `diff` empty), so nothing anywhere
noticed. The only tests that failed were the four this plan added.

That is why E-02 precedes any split, and why the identity is now asserted at FOUR levels (recorded
basename, digest-matches-that-same-module, `driver_generation` label plus `generation_host`, and the
viewer's rendered name) plus a fifth assertion that the two hosts record DIFFERENT paths.

### The non-vacuity control that changed the design

Control (b) from the plan's Required tests item 6 was run as specified: weaken the driver-path
assertion to accept `runner_shared.py`, which is exactly the edit an agent performing the relocation
would make to "fix" a red test. The weakened suite passed on unmodified code, as expected. Then the
sabotage was RE-APPLIED with the weakening still in place:

```
$ python3 -m pytest tests/test_rununify_initialize_run_characterization.py -o addopts=""
3 failed, 32 passed          # weakened: the basename assertion is silent, the other three still fire
$ # ... versus, with the guard intact:
4 failed, 31 passed          # all four fire
```

**Weakening one assertion silenced exactly that one, and the other three still caught the hazard.**
That was not the expected result (the plan anticipated a single load-bearing assertion) and it is the
better one: the four levels are defence in depth rather than four spellings of one check. Recorded
because it changes what a future agent may safely delete: no single edit to this class can make the
F-9 hazard invisible.

## Number three: the fork count IMPROVED, because a sibling landed

The closure was re-measured with full scope tracking. **37 free module-level names** where the plan's
review said 34, and **7 still-double-defined where the plan said 8**:

| Class | Count | Members |
|---|---|---|
| resolves-in-runner-shared | 12 | `DriverError`, `EmptyStatusSelection`, `SCHEMA_VERSION`, `action_for`, `append_jsonl`, `atomic_write_json`, `load_json`, `new_run_id`, `resolve_plan_path`, `sha256_file`, `state_root`, `utc_now` |
| already-one-object | 6 | `Any`, `Path`, `announce_run_order`, `is_plan_review_approved`, `run_order_rationale`, `runner_shared` |
| thin-wrapper (the sanctioned `818uru` form) | 3 | `discover_plans`, `git_common_dir`, `validate_manifest` |
| equal-constant | 2 | `DEFAULT_RUNBOOK_TEXT`, `DEFAULT_STALL_TIMEOUT` |
| oc-only, NO agy counterpart | 2 | `launch_profile_record`, `resolve_launch_pair` |
| agy-only, no oc counterpart | 3 | `DEFAULT_MODEL`, `DEFAULT_TIMEOUT`, `_plan_kind` |
| agy-only but already DELEGATING | 1 | `resolve_verification_decision` |
| **still-double-defined** | **7** | `build_dynamic_manifest`, `enforce_dependency_preflight`, `enforce_requested_action`, `expand_selectors`, `parse_plan_file`, `set_plan_approved`, `write_report` |
| **non-relocatable** | **1** | `__file__` |

12 + 6 + 3 + 2 + 2 + 3 + 1 + 7 + 1 = 37.

**`EmptyStatusSelection` moved from fork to shared** between this plan's review and its execution:
sibling `i3d6ml` lifted it into `runner_shared` at commit `d26c1061`. So the count improved by one
through the Set working as designed, and it is recorded rather than silently absorbed. That is the
opposite direction from what the plan feared (a stale measurement overstating progress) and it is why
E-01 refuses to proceed on a table it did not re-derive.

Two classification refinements this measurement adds, both adopted from siblings:

* **The thin-wrapper class is not duplication** (sibling `yrqyxb`'s contribution). `discover_plans`,
  `git_common_dir` and `validate_manifest` are each a `def` in both modules whose body is a single
  delegating `runner_shared.X(...)` call. That is the form the maintainer's `818uru` OQ-02 ruling
  ESTABLISHED. Counting them as forks would overstate the work by three.
* **`resolve_verification_decision` is not a fork either**, and this matters for F-3. agy defines it,
  oc does not, so a naive scan calls it an asymmetry; in fact it is a one-line binding over
  `runner_shared.resolve_verification_decision`, which plan `ybkmzp` built and wired BOTH hosts to.
  oc reaches the same shared resolver through `resolve_launch_pair`, which ADDITIONALLY resolves the
  launch profile. So F-3's instruction not to collapse the launch half into the verification half is
  not stylistic advice: the verification half is ALREADY shared, and collapsing them would UN-share
  it.

## Number four: `__file__` is not a dependency, and saying so precisely matters

The plan's E-01 requires `__file__` to be named as NON-RELOCATABLE rather than listed among the
injectable dependencies. That distinction is doing real work, so it is worth stating why.

Every other name in the closure is a BINDING: a shared core can receive it as a parameter and a
per-host wrapper can supply it, which is the sanctioned form. `__file__` is not a binding a caller
can pass in the same sense, because its VALUE is a property of where the code text physically lives.
Injecting it is possible (pass `Path(__file__)` from each host's wrapper) and is the only correct
route, but it is a DIFFERENT act from injecting a function: it means the shared core can no longer
answer "which file am I" and must be TOLD, permanently, by every caller forever. Listing it as
dependency number eight would have made it look like one more parameter among many rather than a
contract change.

## Number five: the pins are 14 across 6 files, not the plan's 11 across 3

Measured with the committed scanner, which finds all four ways a test reaches this function's text:

| # | Pin | Kind | Asserts | Thin-caller verdict |
|---|---|---|---|---|
| 1 | `tests/test_dirty_base_gate.py:179` | getsource, BOTH hosts | `report_untracked_dirt_at_run_start` present in `initialize_run` and ABSENT from `execute_item` | **BREAKS** |
| 2 | **`tests/test_dirty_base_gate.py:191`** | getsource, BOTH hosts | **ORDERING**: `refuse_unimplemented_run_flags` < the report < `expand_selectors(` | **BREAKS** |
| 3 | `tests/test_lane_clean_base.py:627` | split-def | the once-per-run seam names `report_untracked_dirt_at_run_start` | **BREAKS** |
| 4 | `tests/test_run_flag_surface.py:370` | getsource | `enforce_mixed_type_gate` present | **BREAKS** |
| 5 | `tests/test_run_flag_surface.py:676` | getsource | `resolve_retry_budget` present | **BREAKS** |
| 6 | **`tests/test_run_flag_surface.py:745`** | getsource | **ORDERING**: splits on `run_dir = state_root`, requires `refuse_unimplemented_run_flags` in the PREFIX | **BREAKS** |
| 7 | `tests/test_run_flag_surface.py:775` | getsource | `freeze_run_policy_flags` present | **BREAKS** |
| 8 | `tests/test_run_flag_surface.py:874` | getsource + regex | the exact spelling `getattr(args, "full_auto", False)` | **BREAKS** |
| 9 | `tests/test_run_flag_surface.py:1319` | getsource + AST call-set | `runner_shared.enforce_draft_admission_gate` is CALLED (AST, not substring, because the comments name it) | **BREAKS** |
| 10 | **`tests/test_run_flag_surface.py:1340`** | getsource | **ORDERING**: same `run_dir = state_root` split, AND `expand_selectors` must precede the draft gate. Cites SPEC 2.5a by name | **BREAKS** |
| 11 | `tests/test_run_flag_surface.py:1564` | getsource | EXACTLY ONE call site each for the two gates | **BREAKS** |
| 12 | `tests/test_runner_backlog_close.py:255` | getsource, BOTH hosts | the literal `"from_backlog"` | **BREAKS** |
| 13 | `tests/test_oc_runipd_shim.py:41` | text literal | `"def initialize_run"` is **ABSENT** from the shim | **SURVIVES** (negative, gets stronger) |
| 14 | `tests/test_agy_runipd_shim.py:38` | text literal | the same negative assertion | **SURVIVES** |

**Verdict: 12 BREAK, 2 SURVIVE. Three assert ORDERING** (#2, #6, #10), which is the class whose
GUARANTEE must survive a move rather than merely its text.

**One pin file was NOT in `Scope-Paths`: `tests/test_lane_clean_base.py`.** The plan's review counted
11 pins across 3 files and fenced those 3; the scanner found this fourth, plus the two negative shim
pins. That is the same class of miss sibling `yrqyxb` hit (three undeclared files), so the fence
being incomplete is now a pattern across three of the four split children rather than an accident.
No test file was edited by E-03, so nothing here needed an out-of-scope justification, but a plan
that DID perform the split would have been refused at finalize.

Baseline, taken before anything changed:

```
$ python3 -m pytest tests/test_run_flag_surface.py tests/test_dirty_base_gate.py \
      tests/test_runner_backlog_close.py -o addopts=""
186 passed in 10.95s
```

**186, where the plan measured 183 at review.** The three-test growth is ordinary suite growth since
2026-09-15, not drift in what is pinned; the pin SITES all still resolve, which the scanner verifies
by line number.

### The three ordering pins and their behavioral equivalents

Each is **already implemented and passing** in
`tests/test_rununify_initialize_run_characterization.py`, so this is a demonstrated route rather than
a proposal.

| Ordering pin | Guarantee | Behavioral equivalent (implemented in E-02) |
|---|---|---|
| `test_run_flag_surface.py:745` | a refused invocation costs the operator nothing and leaves NO durable state | `ARefusalLeavesNoDurableState`, which drives four refusal classes (unimplemented flag, out-of-range retry budget, non-repository, bad dependency graph) and asserts `state_root(repo)` contains no run directory afterwards. Plus `test_the_control_a_valid_invocation_DOES_create_exactly_one_run_directory` as the non-vacuity control, without which a function that refused EVERYTHING would pass |
| `test_run_flag_surface.py:1340` | spec 2.5a: the draft gate runs AFTER resolution and BEFORE any durable state, so an exclusion has nothing to reconcile | `TheDraftAdmissionGateExcludesRatherThanRefuses`, which asserts the draft is withheld while the rest of the queue PROCEEDS, that the gate's excluded set is drawn from RESOLVED ids (the after-resolution half), and that a drafts-only selection freezes no run directory at all |
| `test_dirty_base_gate.py:191` | the untracked report fires ONCE per run, not once per item, and cannot fail the run | `TheUntrackedDirtReportFiresOncePerRun`, which counts occurrences in captured output with a THREE-item queue, so "once" is measured against a varying N rather than fixed at one |

The non-ordering pins have equivalents too: #11's call-site count becomes
`TheMixedTypeGateIsReachedExactlyOnce` (exactly one ledger record per run, which also catches the
zero case that was `uyeko5`'s original dead-gate defect); #12's `"from_backlog"` literal becomes an
assertion that the LINK reaches the frozen entry and that an absent one freezes `None`; #8's spelling
regex becomes "a Namespace with the attribute DELETED freezes `False`", which is the property the
spelling exists to produce.

**The caveat, stated plainly.** A behavioral ordering assertion is weaker than a source-offset one in
one specific way: it can be satisfied by a call on an unrelated branch. It is stronger in the way
this Set needs: it survives the relocation the split performs. That trade is deliberate and is the
maintainer's 2026-09-16 ruling applied.

## What the analysis concluded (E-04)

OQ-03 is `resolved` on disk and the maintainer's directive is unambiguous: one shared code base with
100% of the otherwise-redundant code. So "should this be split?" is settled and E-04 does not re-ask
it. What remains is HOW, and the measurement answers it.

### (a) How a shared writer would supply thirteen host-specific keys, and whether that is a hook

It would not be a hook. Three routes exist and all three are the same thing wearing different
clothes:

1. **Thirteen keyword parameters.** The shared function's signature then describes oc's option set
   and agy's option set concatenated, and its body is a dict literal reassembling what its caller
   already knew.
2. **One `host_options: dict` parameter.** Honest about the shape, and it makes the shared core's
   contribution exactly the ten shared keys plus a `**host_options` splat, i.e. a `dict.update`.
3. **A host descriptor object** (the form sibling `tx6q0h` uses for host STRINGS). This is the best
   of the three, and it works there because those symbols differ by a TOKEN. Here the descriptor
   would need to carry seven oc fields and six agy fields with no overlap, so it is route 2 with a
   type annotation.

**The answer to the plan's question is therefore: no, a 13-of-34-key writer is not worth sharing as
a unit.** But that is NOT the same as "do not share this function", and conflating them is the trap.
The `options` dict is one STATEMENT inside a 409-line function. The right reading is that the
function has two halves with a clean seam between them, which is (d).

### (b) How `__file__` would be handled

By passing the caller's module path in, which is the only correct answer, and it must be PROVEN
rather than assumed. That proof now exists and is demonstrated failing (see Number two). Concretely:
each host's wrapper passes `Path(__file__)`, the shared core takes it as a required parameter with no
default (a default is how this silently regresses), and
`EachHostRecordsItsOwnDriverIdentity::test_the_recorded_driver_path_basename_is_this_hosts_runner_module`
is what fails if a future edit lets the core reach for its own `__file__`.
`TheDriverIdentityIsEvaluatedInEachRunner::test_runner_shared_does_not_write_a_driver_record` catches
the narrower error of a shared HELPER acquiring its own driver writer, which the behavioral test
would not see while each host still had its own.

### (c) The pins

12 break, 2 survive, 3 assert ordering, 1 file was unfenced. Tabulated in full above.

### (d) The oc-only launch-profile pair

**They should stay host-owned, and the reason is measured rather than aesthetic.** `agy_runipd`
contains ZERO `runner_profiles` references against oc's 17, and `launch_profile_record` /
`resolve_launch_pair` have no agy counterpart at all. Under the maintainer's oc-preferred ruling this
is an **A / NOT-A case, not an oc-preferred case**: there is no agy version to prefer oc's over.

`tests/test_runner_profiles_e2e.py` (34 tests, green) reads
`state["options"]["launch_profile"]["config_digest"]` directly. So a shared writer that emitted the
key for BOTH hosts would fabricate provenance agy cannot supply, and one that emitted it for NEITHER
would break that suite. Both directions are now asserted
(`test_only_oc_freezes_a_launch_profile_because_only_oc_has_one`), which is what makes the asymmetry
a guarded decision rather than a fact someone might tidy away.

The implication for a shared writer is the sharpest single argument in this analysis: **it must emit
a key for one host and not the other**, which means the shared core contains either a host branch or
a caller-supplied dict. A host branch inside the shared core is the duplication this Set exists to
remove, wearing a different shape (the plan's own OQ-01 states this test).

### (e) Route recommendation

**Route (B) as a TACTIC for reaching route (A)'s objective: share the PREFIX, leave the state writer
host-owned, and let the seam fall exactly where the ordering pins already say it is.**

The seam is unusually clean here, and cleaner than in any sibling:

* **The prefix** (repository validation, manifest/runbook resolution, the five shared flag refusals,
  the untracked report, `expand_selectors`, the draft gate, the dependency preflight, the `--action`
  preflight, the mixed-type gate) is genuinely identical apart from a `host='oc'`/`host='agy'`
  argument, needs NO `options` decision, and is where all three ordering pins live.
* **The boundary** falls at `run_dir = state_root(repo) / run_id`, which is LITERALLY the string two
  of the pins split the source on. The tests already agree that this is the meaningful line.
* **The suffix** (the run directory, the queue build, the `state` dict, the ledger records) is where
  the thirteen host-specific keys and `__file__` live.

Sequencing, in dependency order:

1. Let `tx6q0h` (04) land. It lifts `write_report` and `enforce_requested_action`, **two of this
   function's seven forks**, taking the injection count to five without this function moving.
2. Lift the closure-clean remainder as individual acts, each with its own behavioral pin.
   `build_dynamic_manifest`, `expand_selectors`, `parse_plan_file` and `set_plan_approved` are the
   candidates; note `parse_plan_file` is the one sibling `sy7uwh` (06) owns, and sibling `i3d6ml`'s
   review recorded `discover_plans`/`expand_selectors` as blocked on it, so that edge is real and
   points the other way from what `orziju`'s own `Item-Dependencies` declares (see the honest limits).
3. Extract the PREFIX into `runner_shared`, converting the three ordering pins to the behavioral
   equivalents this plan has already implemented and leaving them in place as parallel assertions
   until the move is proven.
4. Decide EXPLICITLY that the state-and-options writer stays host-owned, or that it takes a
   host-options dict, so "100% de-duplication" for this function has a stated, reachable definition
   rather than being reached by attrition.

After step 1 the fork count is five; after step 2 it is one or two. Each step is small, independently
verifiable and independently revertible. The alternative (share the whole function now) means one
change that relocates the run-creation control plane, injects seven dependencies, decides thirteen
option keys, converts the driver identity to a passed parameter, and rewrites twelve pins including
all three ordering ones. Either half alone is fine.

## Honest limits

- **No split was performed.** `initialize_run` still has two definitions, one per host, and there is
  no shared core. `tests/test_rununify_initialize_run.py::TheSplitHasNotBeenPerformed` asserts that
  state MECHANICALLY, including the inverse assertions that the seven are still double-defined and
  that neither host delegates, so the omission is a recorded, guarded state rather than an oversight
  a later reader might "finish" without reading this analysis.
- The characterization net pins what `initialize_run` DECIDES and FREEZES: what it refuses, in what
  order relative to durable state, what shape it freezes, what it records in the ledger. It does NOT
  pin the correctness of the work the run later performs; that stays with `run_queue`'s and
  `execute_item`'s coverage. Stated in the file's docstring so it cannot be over-read.
- The `--prepare-only` seam is used throughout, so no real `opencode` or `agy` binary is launched.
  That is the right instrument for this function (it returns after freezing state) but it means the
  tests never observe a turn.
- The resume proof drives the resume path's own state CONSUMERS (`load_state`,
  `reconcile_interrupted`, `requeue_interrupted`, `apply_run_policy_flags_on_resume`, and the
  `action_for` re-derivation), not `main(["resume", ...])`, which acquires the driver lock and enters
  the dispatch loop. A proof that hangs is not a proof. What is established is that state frozen by
  `initialize_run` is readable and re-derivable by resume, and that the driver identity survives a
  resume's own `save_state` round trip.
- **`- Item-Dependencies: executed:sy7uwh` is declared and `sy7uwh` has NOT executed.** The plan's
  F-14 recorded this. The edge is well founded in substance (agy's `_plan_kind` fallback exists only
  because `agy.PlanRecord` lacks `kind`, and `_plan_kind` still exists at `agy_runipd.py:1735`), but
  every item this plan actually performed is a measurement, a pin, an analysis or a guard, none of
  which needs the record unified. So this execution proceeded and the residual is stated rather than
  hidden: the `_plan_kind` fallback branch is CHARACTERIZED
  (`test_an_orchestrators_kind_is_frozen_so_a_resume_rederives_its_action` drives both routes and
  asserts the same frozen result) but not removed.
- No independent reviewer re-examined this execution. The plan's readiness rested on a maintainer
  attestation rather than a fresh review round, which the plan itself records.

## The 31 bare-suite failures that are not failures

A bare `python3 -m pytest` in this lane reports **31 failed, 7645 passed**. That number needs its
explanation attached wherever it appears.

The 31 are an artifact of running inside a runner-managed worker lane: `AW_EXECUTION_ROLE=worker` is
set, which makes `ipd_lifecycle` refuse driver-only lifecycle verbs by design, and the affected tests
call `driver_begin` and friends directly. Four measurements establish that they are not mine:

```
$ python3 -m pytest                              # PRE-change, at HEAD 87682a3b, my files stashed
31 failed, 7584 passed, 3 skipped, 2 xfailed in 99.93s
$ python3 -m pytest                              # POST-change, with my two files
31 failed, 7645 passed, 3 skipped, 2 xfailed in 88.84s
$ diff <(pre FAILED lines | sort) <(post FAILED lines | sort)
IDENTICAL
$ env -u AW_EXECUTION_ROLE python3 -m pytest     # POST-change, role unset
7676 passed, 3 skipped, 2 xfailed in 93.96s
```

**Byte-identical failure sets before and after; +61 passing tests and no new failure. With the role
unset the suite is COMPLETELY clean**, which is a stronger result than sibling `ty3cj6` obtained (it
had one load-dependent sigint flake remaining).

---

# Appendix A: reproducing the measurements

Four scripts, run from the repository root, their output quoted verbatim above:

    python3 options_scan.py    # E-01(a): the `options` key partition, per host, three views
    python3 closure_scan.py    # E-01(b): the 37-name closure classified into nine classes
    python3 pin_scan.py        # E-03: every test that reads this function's source text
    python3 resume_proof.py    # F-2: both hosts resume their own frozen state

`options_scan.py` unpacks the `state` and `options` dict literals from the AST, separating literal
keys from CONDITIONAL ones (a `**({...} if cond else {})`) and from the `**` expansion whose members
live in another module, then reads that expansion's key set from `freeze_run_policy_flags` itself.
`closure_scan.py` implements the closure test with full scope tracking (parameters, assignments,
walrus, `for`/`with`/`except` targets, comprehension and lambda scopes, nested `def`/`class`,
function-local imports, `global`) and classifies each free module-level name against `runner_shared`
and against the other host, separating a genuine fork from the sanctioned thin-wrapper form by
checking whether the body is a single delegating `runner_shared.X(...)` call. `pin_scan.py` finds the
four ways a test reaches this function's source (`inspect.getsource`, an AST lookup by name, a
`split("def initialize_run")`, and a bare `"def initialize_run"` text literal), de-duplicates sites
that two detectors both see, reports the enclosing test name for each, and also lists every test file
that merely NAMES `initialize_run` (14 files, 6 of which read its source) so nothing is missed
silently.

All four live under this run's lane submission at
`.aw/state/lane-submissions/<run>/10-orziju/attempt-1/evidence/`. **That tree is GITIGNORED**, which
is why every number they produce is quoted in full above rather than only cited: the tables here are
the durable record. The E-01 classifications are additionally asserted MECHANICALLY in
`tests/test_rununify_initialize_run.py`, so they are re-derived by the suite on every run and cannot
go stale unnoticed.
