# Review findings: plan 6krsym

- Subject-Id: 6krsym
- Subject-Type: ipd
- Reviewed-At: 2026-09-18
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `6ff7a7ba`. The plan on disk is byte-identical to the lane input (`diff -q` clean), so no
pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported `clean`,
0 findings, exit 0.

EVERY CODE CLAIM IN THIS PLAN IS TRUE, AND I VERIFIED EACH ONE RATHER THAN TRUSTING IT. The diagnosis is
correct and unusually precise:

- F1/F2 VERIFIED. `AGGREGATE_METRICS` is exactly the seven the plan names (`run_analytics_query.py:153-161`),
  including `duration_seconds` and `event_count`. `_metric_payload` (`run_analytics.py:526`) writes a base of
  5 keys plus conditionals, and its timing loop (`:573-580`) emits exactly `wall_seconds`,
  `observed_activity_seconds`, `overlap_seconds`, `unattributed_seconds`. NEITHER `duration_seconds` NOR
  `event_count` is written anywhere in the function. So both metrics are advertised and unreachable.
- F3 VERIFIED. `run_analytics_telemetry.py:1343` sets `payload["duration_seconds"] = round(self.elapsed_seconds(), 6)`
  on the `end` event, and `duration_seconds` appears NOWHERE in `run_analytics.py` (the producer), so this is
  an ingestion gap exactly as the plan says.
- F4 VERIFIED. `_numbers_for` (`run_analytics_query.py:468-492`) returns a single `missing` integer and
  increments it for any non-numeric value, with no distinction between "not recorded" and "nothing to record".
  Its own docstring already argues absence is meaningful.
- The privacy-allowlist claim VERIFIED: `duration_seconds` is present twice (`run_analytics_privacy.py:114`
  and `:169`), so nothing needs widening, precisely as the plan states.
- The `_metric_payload` OMIT-NEVER-ZERO-FILL docstring quote VERIFIED verbatim, and `median`-as-default
  VERIFIED with its skew rationale (`run_analytics_query.py:163-166`).

I COULD NOT VERIFY THE CORPUS MEASUREMENTS, AND THAT IS THE SUBSTANCE OF THIS REVIEW. Every quantitative
claim in the plan (180 analyzed runs, 0 of 180 carrying either key, 61 telemetry files, the 32-absence
classification, the zero-result loss check) was measured against `.aw/records/runs/`, which is GITIGNORED
(`.aw/.gitignore:14`, "box-local, ephemeral working material; never committed") and DOES NOT EXIST in this
checkout. That does not make the plan wrong; I have no reason to doubt it. It makes the plan's VALIDATION
UNSATISFIABLE by the agent that will execute it, because `aw oc run` executes in exactly this kind of lane.

I MEASURED THE CONSEQUENCE RATHER THAN ASSERTING IT, and it is worse than "less evidence". With no corpus,
a BROKEN metric and a WORKING metric are byte-indistinguishable:

```text
$ aw runs query metrics --metric duration_seconds --agent
{"payload":{"metric":"duration_seconds","stat":"median","value":null,"sample_size":0,"missing_count":0,"coverage":0.0}}
$ aw runs query metrics --metric wall_seconds --agent
{"payload":{"metric":"wall_seconds","stat":"median","value":null,"sample_size":0,"missing_count":0,"coverage":0.0}}
```

`wall_seconds` is the plan's own example of a metric that is COMPLETE for all 180 runs. In a lane it reads
identically to the two defective ones, and both report `outcome: clean, exit 0`. So V-04 and V-05's "pasted
nonzero sample size across the real corpus" cannot be produced, and an executor trying to satisfy them has
no honest path.

THE FIX IS IN-TREE AND I PROVED IT WORKS, which is why this is FIXED rather than escalated. The query views
take an `entries` list as a parameter, and the existing suite already builds synthetic cache entries for
exactly this reason (`tests/test_run_analytics_cli.py:829-834` constructs 30000 of them). Measured this
session against a six-entry synthetic corpus:

```text
wall_seconds               sample= 6 missing=0
duration_seconds           sample= 0 missing=6      <- F1 reproduced, no corpus needed
event_count                sample= 0 missing=6      <- F2 reproduced, no corpus needed
tokens                     sample= 5 missing=1      <- F4 reproduced (the 1 is a legitimately-empty run)
```

All three defects reproduce in a lane in under a second. So the plan's validation can be made both
satisfiable AND stronger: a fixture-based assertion is deterministic and survives corpus churn, whereas
"nonzero sample size over the real corpus" silently changes meaning every time a run is added or pruned.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | E. testing; A. correctness | `.aw/.gitignore:14`; `.aw/records/runs` measured ABSENT; the two indistinguishable `--agent` payloads above; plan `:38`, `:55`, `:60`, `:119-124`, `:150-182` | **EVERY V-ITEM DEMANDS EVIDENCE FROM A CORPUS NO EXECUTOR CAN REACH, AND THE FAILURE IS SILENT RATHER THAN LOUD.** All seven V-items require measurements over `.aw/records/runs/`, which is gitignored and absent from every lane and every fresh clone. Worse than unavailable: with no corpus, `aw runs query metrics --metric duration_seconds` returns `sample_size: 0, outcome: clean, exit 0`, IDENTICAL to the fully-working `wall_seconds`. So an executor cannot tell the defect from the fix, V-04/V-05's "nonzero sample size" is unproducible, and the most likely outcomes are a false "verified" or a stalled item. This is the same class of defect as the plan's own F1 (a surface that reports something it cannot actually support). | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Every V-item re-pointed at DETERMINISTIC FIXTURE evidence as its primary requirement, with corpus figures demoted to an optional corroboration the executor states as unavailable when absent. I proved the fixture route reproduces all three defects (table above) before prescribing it, and E-01 now requires the executor to state up front whether a corpus is present, so the two evidence regimes never get silently mixed. |
| PR-002 | HIGH | IN-SCOPE | G. executability | `ls tests/test_run_analytics_query.py` -> No such file; `tests/test_run_analytics_cli.py:39` imports `run_analytics_query as query_mod` | **A DECLARED SCOPE PATH DOES NOT EXIST, AND IT IS THE ONE THE QUERY-LAYER TESTS WOULD GO IN.** `Scope-Paths` names `tests/test_run_analytics_query.py`; the repo has no such file. The query layer is tested from `tests/test_run_analytics_cli.py` (the only test file importing `run_analytics_query`), and `_numbers_for` has NO direct test anywhere (measured: zero matches across `tests/`). So the plan fences a file that will not exist unless the executor creates it, while the file holding the relevant coverage is undeclared, and `aw ipd finalize`'s scope reconciliation would demand a `--scope-ack` for a path never touched. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `Scope-Paths` corrected: `tests/test_run_analytics_cli.py` added (where the query layer is actually tested and where the new fixture assertions belong), and `tests/test_run_analytics_query.py` retained ONLY as an explicitly-optional new file with a note that creating it is a choice, not an obligation. Recorded that `_numbers_for` currently has no direct test, which makes E-06 a coverage ADDITION rather than a modification. |
| PR-003 | MEDIUM | OVER-SCOPE | F. KISS (work the plan feared it might need) | measured: `grep -rln "duration_seconds\|event_count" .aw/records/specs/` returns nothing; `aw runs query --help` says only "Allowlisted metric to aggregate (default: cost)"; `run_analytics_query.py:573` builds `schema`'s list from `AGGREGATE_METRICS`; `:370-371` refuses from the same tuple | **BOTH CONDITIONAL WORRIES IN THE SPEC-SYNC SECTION RESOLVE TO "NOTHING TO DO", AND MEASURING THAT NOW SAVES THE EXECUTOR A DETOUR.** The section instructs the executor to check whether spec `25kzda` enumerates the queryable metrics (it does not; NO spec mentions either metric) and whether `--help` and the `schema` view separately advertise the list (they do not: help is generic, and both `schema` and the refusal derive from the ONE `AGGREGATE_METRICS` tuple, so a removal propagates automatically). Left as-is, an executor spends a cycle hunting a spec amendment and a second advertising surface, neither of which exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section rewritten from two conditional hunts into two measured statements with their commands, concluding no spec amendment is needed and no second advertising surface exists. The instruction to declare a spec in `Scope-Paths` BEFORE editing one is preserved as the contingency it should have been, in case E-02/E-03 turn up a contract elsewhere. |
| PR-004 | MEDIUM | IN-SCOPE | A. correctness (a determination the plan leaves open that the code already answers) | `run_analytics_schema.py:404-425` (`TimeAccounting`, four published quantities and the docstring's reason); `run_analytics_telemetry.py:1343` (`elapsed_seconds()` on the `end` event) | **E-02's DETERMINATION IS MOSTLY ALREADY MADE BY THE CODE, AND THE PLAN SHOULD START FROM IT.** `TimeAccounting` deliberately publishes `wall_seconds`, `observed_activity_seconds`, `overlap_seconds` and `unattributed_seconds` and NO duration, with a docstring explaining that activities overlap so "distributing elapsed time across them would require a model this layer refuses to impose". Meanwhile telemetry's `duration_seconds` is the TELEMETRY SESSION's own `elapsed_seconds()`, which is a different subject (the sampler's lifetime) from a run's wall clock. E-02 is still worth doing, but framed as an open three-way question it invites re-deriving what two docstrings already state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now opens with both citations and the measured distinction (telemetry's field times the SAMPLER SESSION; `TimeAccounting` refuses a single reconciled duration by design), and asks the executor to confirm-or-refute that reading rather than start from zero. The do-one-or-the-other rule in E-04 is untouched: this sharpens the input, not the decision. |
| PR-005 | MEDIUM | UNDER-SCOPE | D. anti-regression | `run_analytics_query.py:468-492`; measured zero direct tests for `_numbers_for`; V-06's sum requirement | **E-06 CHANGES A FUNCTION WITH NO DIRECT TEST, AND THE PARTITION CHECK IT RELIES ON CANNOT BE RUN AGAINST THE CORPUS EITHER.** V-06 requires the new per-class counts to SUM to the previous single `missing` count, which is the right invariant, but it inherits PR-001's problem: with no corpus both sides are 0 and the sum holds trivially. Combined with `_numbers_for` having no direct test today, E-06 could ship a vocabulary split whose partition property was never actually exercised. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-06 now requires the partition proven on a FIXTURE whose absence classes are known by construction (so the sum is a real constraint rather than 0 == 0), and E-06 must add the first direct test of `_numbers_for`. The agent-record compatibility question (does `missing_count` change meaning) is retained unchanged; it was already right. |
| PR-006 | LOW | IN-SCOPE | G. executability | plan `:189-190` (the gate's fence sentence) vs `- Scope-Paths:` (four paths) | The gate says "this plan declares two analytics modules and their two test files", which was accurate as authored but becomes wrong once PR-002 corrects the fence, and it counts paths in prose where the front matter is authoritative. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now refers to the declared paths without restating a count, so the fence and the prose cannot disagree again. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Every V-item requires evidence from the gitignored, lane-absent run corpus. Escalate as a blocking question, or re-point the evidence? | RE-POINT to deterministic fixtures as the primary evidence, keeping corpus figures as optional corroboration. Not escalated. | (a) Escalate as `Blocking: yes` and stop: rejected, because the repository already supplies the answer (the query views accept an `entries` parameter and the suite already builds synthetic entries at scale), so this is answerable from evidence rather than a maintainer preference. (b) Drop the quantitative requirement entirely: rejected, it is the plan's best feature; a metric fix with no sample-size evidence is exactly the unfalsifiable state the plan exists to end. (c) Require the executor to run in the maintainer's checkout: rejected, it contradicts how `aw oc run` executes and would make the plan unrunnable by its own runner. | `.aw/.gitignore:14` (never committed); `.aw/records/runs` measured absent; `tests/test_run_analytics_cli.py:829-834` builds 30000 synthetic entries; and I measured that a six-entry fixture reproduces all three defects (`duration_seconds` 0/6, `event_count` 0/6, `tokens` 5 with 1 legitimately-empty). | yes |
| D-2 | `Scope-Paths` names a nonexistent `tests/test_run_analytics_query.py`. Delete it, or keep it and add the real file? | Add `tests/test_run_analytics_cli.py` (the real coverage site) and keep the nonexistent path only as an explicitly OPTIONAL new file. | (a) Delete the nonexistent path outright: rejected, an executor may legitimately choose to start a dedicated query-layer test module, and removing it from the fence would make that a scope violation. (b) Leave the fence as authored: rejected, it would force a `--scope-ack` for a path that never existed while leaving the file that must change undeclared. | `ls` shows no `tests/test_run_analytics_query.py`; `tests/test_run_analytics_cli.py:39` is the only test importing `run_analytics_query`; `_numbers_for` has zero test matches across `tests/`. | yes |
| D-3 | Does removing `duration_seconds` (OQ-01's default) break a published contract, making OQ-01 blocking? | NO. OQ-01 stays `Blocking: no` and REMOVAL stays the default, with the measurement recorded so the maintainer can see the blast radius. | (a) Promote OQ-01 to blocking: rejected, no spec enumerates the metric, help does not name it, and the refusal path is generated from the same tuple, so removal is self-consistent and the only externally visible change is that a name which NEVER returned data now refuses. (b) Pre-decide an alias: rejected, that is the maintainer's public-contract call and the plan is right to leave it. | Measured: no `.aw/records/specs/` file mentions `duration_seconds` or `event_count`; `aw runs query --help` says only "Allowlisted metric to aggregate (default: cost)"; `run_analytics_query.py:370-371` and `:573` both derive from `AGGREGATE_METRICS`. | yes |

### Honest limits of this review

- I did NOT verify any of the plan's corpus numbers: 180 analyzed runs, 0-of-180 key coverage, 61 telemetry
  files, the 32-absence classification, or the zero-result token-loss check. The tree they were measured
  against is gitignored and absent here. I found no reason to doubt them and every CODE claim they rest on
  checks out, but this review provides no independent confirmation of the quantities, and PR-001's fix is
  designed so execution does not depend on them either.
- I did not determine whether `event_count` is in fact derivable from `event_facts`. I confirmed the field
  exists (`run_analytics_cache.py:169`, `:113`) and is part of the cache envelope, which is all E-03 needs as
  a starting point; whether it is populated for real runs is a corpus question I cannot answer in a lane.
- I did not test what happens to a consumer of the agent record's `missing_count` if E-06 changes its
  meaning. The plan requires that question be answered and I left that requirement intact rather than
  pre-empting it.
- The suite is green in this lane for the two relevant files (`tests/test_run_analytics.py` +
  `tests/test_run_analytics_cli.py`: `145 passed`), which I ran as a pre-work reference. I did not run the
  full suite as part of this review beyond the sweep's earlier baseline.
