# Review findings: plan 0xmk4e

- Subject-Id: 0xmk4e
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `8d603020`. The plan on disk was byte-identical to the sealed lane input
(`source_sha256` `a471350a4122c980f43af6bf9ba0c5654f4c42ead55cae358e19746135f63bf3`, re-computed and
matched) and `git status --short` was empty, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0; the watermark is unchanged at
05 (no E-item added; every finding was fixed by correcting an instruction, withdrawing a
self-contradictory requirement, or resolving the open question).

DISCLOSURE: same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on
EXECUTING claims rather than re-reading them. This round read `initialize_run_core`'s call order line by
line, resolved every symbol the plan names through both host modules, CONSTRUCTED the refork-guard row
the plan asked for and ran its predicate, computed probe-cache digests across a simulated migration, and
ran the three adjacent suites. Three of the plan's instructions turned out to be unsatisfiable or
self-contradictory against the code they describe.

THIS IS THE CHILD THAT ACTUALLY ENFORCES THE SET'S INVARIANT, and its structural claims are accurate. I
verified each: `enforce_orchestrator_probe_gate` is called from `initialize_run_core` and not from
`run_queue`; the three pre-queue gates do raise before `run_dir` is created (`:11853`, `:11881`,
`:11907` against `:11917`); the probe's post-directory siting is a documented priced exception; the
collect-then-partition batch shape is exactly as described (`outcomes` appended in a loop, then
partitioned into `blocking` and `unavailable`); `queued_orchestrator_targets` scopes to the queue and
skips an unreadable plan; and F-4's one-sided-row observation and F-5's spawn-seam observation are both
quoted correctly from the source. The Set-level ordering rationale is sound.

WHERE THIS REVIEW SPENT ITS EFFORT: two HIGH findings where the plan instructed work that cannot be
done as written, and one where a taste-framed open question had a decisive answer the plan had not
surfaced.

**1. E-01's "re-export it to both hosts" rests on a false premise (PR-304, HIGH).** The plan requires one
object re-exported to both hosts and V-01 demands `oc.<sym> is agy.<sym>`. Measured: NO pre-queue gate
is a host attribute. `hasattr(oc_runipd, "enforce_orchestrator_probe_gate")` is False, and so is the agy
side, and the same holds for `enforce_mixed_type_gate`, `enforce_draft_admission_gate` and
`queued_orchestrator_targets`. A direct attribute read raises `AttributeError` rather than proving
identity, so V-01 as written is unsatisfiable, and the natural way to "make it pass" is to add the
host-surface symbol the same plan forbids in its next sentence. The hosts share these by CALLING
`initialize_run_core` (`oc_runipd.py:3360`, `agy_runipd.py:2137`). The shipped identity pattern is
`getattr(module, name, getattr(module.runner_shared, name))` plus `assertIs`
(`BothHostsShareOneDefinition`), which I verified returns True for both hosts on the probe gate while a
direct `hasattr` is False. E-01 and V-01 now follow that pattern and explicitly forbid adding a
re-export.

**2. E-04's refork-guard row directly contradicts E-01 (PR-305, HIGH).** E-04 required adding a row for
the new symbol and mutation-checking it. I did not reason about whether that works; I constructed the
`Owned` row in-process and ran the identity half's predicate. It reports MISSING on BOTH hosts for a
`runner_shared`-only symbol, and the guard's own violation message names the remedy: "re-export
`<owner>.<symbol>`". So the row cannot pass unless a host re-export is added, which E-01 forbids. This is
why the existing pre-queue gates carry no refork row. An executor following both items would either be
stuck or would add the re-export to unstick itself, which is the worse outcome because it silently grows
the host surface this Set is trying to keep flat. The requirement is withdrawn and replaced with the pin
the probe itself uses: object identity plus a both-hosts BEHAVIOURAL test driving the real
`initialize_run` on each host (`BothHostsActuallyRefuse`), which is the `pgq326` lesson and a stronger
guarantee than a guard row. `tests/test_runner_refork_guard.py` is now expected to reconcile UNCHANGED.

**3. OQ-01 had a deciding fact the plan never surfaced (PR-301, HIGH).** The question framed siting as
invariant-tidiness versus operator-readability, which is a matter of taste, and that is why it was left
open. Reading the call order settled it: `--prepare-only` takes an EARLY RETURN at `:12103`, between
`run_dir` creation (`:11917`) and the probe (`:12122`). So a gate sited "beside the probe" is SKIPPED
under `--prepare-only`, while one sited with the three pre-queue gates is not. That is decisive because
the probe's own skip there is correct on a reason that does NOT transfer, stated in its comment: the
flag's contract is to build and display the queue "WITHOUT launching OpenCode", so a model turn would
break it. The shape check spends no model turn, so skipping it buys nothing and denies the operator the
one thing `--prepare-only` is for, namely learning the queue is not runnable before committing to a run.
And the probe's skip is deliberately ANNOUNCED so "an operator inspecting a queue must not conclude the
orchestrators in it were cleared" - a silently skipped shape check would recreate that exact false
impression with nothing announcing it. Resolved to EARLY, with the accepted cost stated: the refusal is
read from process output rather than `aw runs`.

**4. E-05's assertion would have been vacuous (PR-303, MEDIUM).** It said to prove zero model calls by
injecting the spawn seam and asserting it was never called. But `_assert_probe_spawn_is_permitted`
RAISES on any real spawn whenever pytest is running, and its docstring says plainly "THIS IS NOT A
PRODUCTION CODE PATH GUARD". So "no tokens were spent" is already true suite-wide and says nothing about
this gate's ORDERING; a test resting on it would pass identically with the gate sited after the probe.
The claim that matters is that `ask_orchestrator_probe` was never REACHED. `probe_orchestrator` already
takes `asker`, `runner` and a `counter` list and appends per attempt (`:8179-8180`), so an empty
`counter` is the direct observation. E-05 and V-05 now require an invocation count plus a
must-fail-first demonstration.

**5. One worry I checked and can rule out (PR-302, MEDIUM).** A plausible concern is that a cached probe
PASS could survive child 04's migration and let a rewritten orchestrator through. It cannot:
`probe_cache_digest` covers E-item action text, and I computed digests across a simulated
prose-row-to-typed-row rewrite, which changed the key. So this child needs no cache-invalidation work and
an executor should not add any. Recorded because the absence of work is worth stating.

WHAT I DELIBERATELY DID NOT CHANGE. The five-item shape is right and the dependency edges are correct.
The probe survives untouched, which criterion 9 requires and which I did not weaken; if anything the
E-04 replacement strengthens the coexistence proof by adding a behavioural both-hosts refusal. I left
F-6's inherited skip-an-unreadable-plan behaviour alone: it is correctly described and correctly
delegated to the existing preflight. I did not relax criterion 11; I made it harder to fake.

VALIDATION RUN AT REVIEW. `aw ipd lint --phase author` and `--phase review-finalize` both conform.
Carrier rule CLEAN at `pre-transition` (OQ-01 now `resolved`). The three adjacent suites this child
touches: `python3 -m pytest tests/test_orchestrator_probe.py tests/test_orchestrator_probe_cache.py
tests/test_runner_refork_guard.py -o addopts=""` -> `142 passed`. Bare suite: `1 failed, 7305 passed, 3
skipped, 2 xfailed`, the single failure being the corpus-pinned
`test_no_pending_plan_is_refused_on_a_verdict_today` naming three `reaskscore` plans another party is
editing, proven pre-existing during child 01's review. `aw check all` reports 0 findings against this
plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | C (architecture); OQ resolution | `initialize_run_core` call order: gates `:11853`/`:11881`/`:11907`, `run_dir` `:11917`, `--prepare-only` early return `:12103`, probe `:12122`; the probe's own skip comment | OQ-01 was left open on a taste framing (invariant tidiness vs `aw runs` readability) while a DECIDING fact existed: `--prepare-only` returns between `run_dir` and the probe, so a gate sited beside the probe is SKIPPED under that flag. The probe's skip is justified on a no-model-turn contract that does not transfer to a free check, and it is ANNOUNCED precisely to prevent the false "these orchestrators are cleared" reading a silent skip would cause. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | OQ-01 resolved to EARLY with the `--prepare-only` reasoning; E-02 rewritten from "decide and record" to "site it early, here is why"; expected outcome and V-02 now require the `--prepare-only` refusal be demonstrated; accepted cost (no `aw runs` record) stated. Recorded as F-7. |
| PR-304 | HIGH | IN-SCOPE | A (correctness); host sharing | `hasattr` False on both hosts for all four pre-queue gate symbols; `BothHostsShareOneDefinition` resolving via `getattr(module, name, getattr(module.runner_shared, name))`; `oc_runipd.py:3360`, `agy_runipd.py:2137` | E-01 required re-exporting the gate to both hosts and V-01 demanded `oc.<sym> is agy.<sym>`. No pre-queue gate is a host attribute, so that read raises `AttributeError` and V-01 is unsatisfiable; the natural fix is to add the host symbol the same item forbids. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now forbids a re-export and states the hosts share via `initialize_run_core`; the shipped `getattr` fallback + `assertIs` pattern prescribed; V-01 rewritten and explicitly FAILS a bare attribute comparison. |
| PR-305 | HIGH | IN-SCOPE | A (correctness); internal contradiction | constructed the `Owned` row in-process: identity half reports MISSING on both hosts; the guard's remedy string "re-export `<owner>.<symbol>`" | E-04 required a refork-guard row plus mutation check for the new symbol. The guard's identity half REQUIRES a host attribute, so the row fails for a `runner_shared`-only gate unless a re-export is added - directly contradicting E-01. The existing pre-queue gates carry no row for this reason. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Row requirement withdrawn; replaced with object identity plus a both-hosts BEHAVIOURAL refusal following `BothHostsActuallyRefuse`; `tests/test_runner_refork_guard.py` now expected to reconcile UNCHANGED with a `--scope-ack`; F-4 rewritten; Scope check updated. |
| PR-303 | MEDIUM | UNDER-SCOPE | E (verification) | `_assert_probe_spawn_is_permitted` docstring ("NOT A PRODUCTION CODE PATH GUARD"); `probe_orchestrator` `asker`/`runner`/`counter` at `:8135`, `:8179-8180` | E-05's evidence would have been vacuous: the real spawn raises under pytest by construction, so absence-of-spawn is guaranteed suite-wide and proves nothing about ordering. A test resting on it passes identically with the gate sited after the probe. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 and V-05 now require counting invocations of an injected double (an empty `counter`) rather than observing no spawn, plus a must-fail-first demonstration (move the gate after the probe, show the assertion FAILS, revert). F-5 corrected, F-9 added. |
| PR-302 | MEDIUM | IN-SCOPE | A (correctness); cache interaction | two `probe_cache_digest` values across a simulated prose-row-to-typed-row rewrite | Worth recording because the opposite is a plausible worry: a cached probe PASS cannot survive child 04's migration, since the digest covers E-item action text and the rewrite changes it. So no cache-invalidation work is needed here and none should be added. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-8 and as a Step-0 convention so an executor does not add unnecessary invalidation. |
| PR-306 | MEDIUM | UNDER-SCOPE | E (verification); baseline honesty | bare suite `1 failed, 7305 passed`; the three adjacent suites `142 passed` | The plan named no suite baseline, and one unrelated corpus-pinned failure exists naming another party's plans. It also did not name the three suites guarding the module it edits, which is where a regression from this change would actually land. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Baseline recorded with the failing NODE ID, its cause and the proof it is pre-existing, plus an explicit instruction to run `test_orchestrator_probe.py`, `test_orchestrator_probe_cache.py` and `test_runner_refork_guard.py` with their measured `142 passed`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where should the shape gate be sited (the plan's own OQ-01)? | EARLY, with the three pre-queue gates, before `run_dir` exists. | Beside the probe for `aw runs` readability (rejected on a measured consequence, not taste: `--prepare-only` returns at `:12103` between `run_dir` and the probe, so that siting is silently skipped under the one flag an operator uses to check a queue BEFORE committing, and the probe's own skip there rests on a no-model-turn contract that does not transfer to a free check). Siting it early AND recording it durably (not chosen now, but named as the honest future change if durable readability is wanted). | the call order read at review; the probe's skip comment including "an operator inspecting a queue must not conclude the orchestrators in it were cleared" | yes |
| D-2 | E-04 requires a refork-guard row that cannot pass. Add the re-export, or drop the row? | Drop the row; pin with object identity plus a both-hosts behavioural refusal. | Adding the host re-export to make the row pass (rejected: it creates the new host-surface symbol E-01 forbids and that this Set exists to avoid, and it would be a change made solely to satisfy a test rather than a need). Leaving E-04 as written (rejected: the executor would be stuck or would unstick itself the wrong way). | the constructed row reporting MISSING on both hosts; the guard's own "re-export" remedy string; the existing pre-queue gates carrying no row | yes |
| D-3 | How should criterion 11's "zero model calls" be evidenced so it is not vacuous? | Count invocations of an injected probe double (empty `counter`), plus a must-fail-first check. | Asserting the real spawn never happened (rejected: `_assert_probe_spawn_is_permitted` raises under pytest regardless of ordering, so the assertion holds even with the gate sited after the probe - it cannot fail and therefore proves nothing). Reading the code path (rejected: the plan itself correctly demands observation over inspection). | the guard's docstring disclaiming production-path semantics; `probe_orchestrator`'s `counter` appending per attempt | yes |
| D-4 | Should this child do anything about a cached probe verdict surviving the migration? | No. Record that it cannot happen and forbid adding invalidation. | Adding a cache-invalidation step (rejected as unnecessary work on a measured basis: the digest covers E-item action text, so the migration moves it by construction). | two digests computed across a pre- and post-migration fixture at review | yes |
