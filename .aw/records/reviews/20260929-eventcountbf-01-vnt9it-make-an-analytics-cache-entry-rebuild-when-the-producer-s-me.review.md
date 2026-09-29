# Review findings: plan vnt9it

- Subject-Id: vnt9it
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `96c97168` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified (`git status --short` empty). No production code was modified by this
review; every post-change measurement was taken by rebinding `run_analytics_cache.source_fingerprint`
or `CACHE_SCHEMA_VERSION` IN MEMORY from scripts under the gitignored `.aw/state/`, with every
fixture corpus built in a fresh temp dir, per the plan's own method rule.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS PRESCRIBED FIX IS PROVEN TO WORK. The defect reproduced
exactly: stripping only `event_count` from a published entry, leaving `schema_version`, `is_complete`
and `source_fingerprint` intact, yields `decide -> ('hit', 'fresh-complete-entry')`, and a further
full ordinary sweep does NOT restore the key. With E-02's fold staged in memory the same four
entries went to `('rebuild', 'fingerprint-changed')` and `entries_with_event_count` went 0/4 to 4/4
after one sweep, with `readable=4 unreadable=0` throughout. F-05's decisive comparison reproduced:
a `CACHE_SCHEMA_VERSION` bump takes the corpus from `readable=6 unreadable=0` to `readable=0
unreadable=6` with no sweep, while the fingerprint route leaves it fully readable. F-06 reproduced in
both directions (`CacheEnvelopeError` on an unknown field, and on an old entry under extended
`ENVELOPE_FIELDS`). F-03, F-04, F-07, F-08, F-09, F-12 and F-13 all reproduced as written, including
`6krsym`'s stat touching `run_analytics.py` and `run_analytics_query.py` but not the privacy module,
and zero `rebuild=True` anywhere under `tests/`.

WHAT REVIEW FOUND IS THAT THE PLAN'S CENTRAL DEFINITION IS AMBIGUOUS AT THE GRAIN, IN A WAY THAT
MAKES ONE ITEM UNSATISFIABLE AS WRITTEN AND ADMITS A SILENT MISIMPLEMENTATION OF ANOTHER. The
design is right; the specification of it was under-determined.

**THE PRODUCER VOCABULARY IS GRAIN-DEPENDENT AND THE PLAN NAMED A SET THE CACHE NEVER STORES
(PR-701, HIGH).** E-01 defined `PRODUCER_METRIC_KEYS` as the keys `_metric_payload` "can emit".
Measured, `_metric_payload` runs at five grains whose union is 26 keys, while the envelope stores
only the RUN grain, because `build_cache_facts` takes `projected.get("run")[0]` as `metric_facts`:
19 keys for a rich run. The seven-key difference is `['attempt', 'event_type', 'ipd_id6', 'position',
'sequence', 'set_id', 'timestamp']`. An executor following the original wording declares a 26-key
constant, and E-03's equality assertion against what the producer emits into the cache can never
pass. The failure is loud, but it stalls execution with no guidance, and the obvious repair
(weakening equality to containment) is precisely what the plan's own silent-failure paragraph
forbids. E-01 and E-03 rewritten to define and derive from `build_cache_facts`; V-01 gains a check
that the four finer-grain-only names are absent.

**FOLDING A PER-RUN KEY SET WOULD FAIL SILENTLY AND LOOK LIKE SUCCESS (PR-702, HIGH).** E-02 said to
fold "the producer vocabulary" without stating it must be the declared constants. Folding each run's
own emitted keys is the natural misreading and is much worse than churn: measured, a rich run emits
19 run-grain keys and a thin run 14, so a thin run's entry would be compared against a token derived
from its own facts and would NEVER invalidate on a vocabulary change. The rich runs would rebuild,
making the fix appear to work, while sparse runs stayed permanently stale, which is the original
defect surviving for the runs most likely to exhibit it. It also puts a measured 1.46ms
`build_cache_facts` call inside a per-run path costing 22.0ms cold, which OQ-01 refuses on principle.
E-02 now mandates the constants explicitly, and V-02 gains (e) a check that the helper does not call
the fact builders and (f) a requirement that a THIN entry also moves to `rebuild`.

**A THIN RUN EMITS A STRICT SUBSET, WHICH BOUNDS E-03's EQUALITY (PR-703, MEDIUM).** Measured, the
thin set is 14 keys and misses exactly `['cost', 'cost_currency', 'cost_is_estimate', 'token_total',
'tokens']`, and a thin run emits zero event facts. This is correct `OMIT, NEVER ZERO-FILL` behavior,
not a defect, but it means the guard is an equality against the RICH reference only. Recorded as
F-15 and noted in E-03 so a future reader meeting a red guard on a thin fixture does not relax it to
containment and reopen F-03.

**V-03's MUTATION PROOF COULD BE MADE VACUOUS (PR-704, MEDIUM).** V-03(d) asked for an extra key
injected into `_metric_payload`. Since only the run grain reaches `metric_facts`, a key injected at a
finer grain leaves the guard GREEN and the proof proves nothing. V-03(d) now requires the executor to
use a key that reaches the run grain and to name which it used.

**F-01 AND F-02 ARE NOT REPRODUCIBLE IN A LANE (PR-705, LOW).** Both describe the maintainer's live
298-entry corpus. `cache_root` resolves inside the lane and does not exist; `.aw/records/runs/` is
absent entirely, because the tree is gitignored and machine-local. The MECHANISM F-01 rests on was
verified directly; the 298/297 counts are an authoring report. No `E-*` or `V-*` item depends on
them, and OQ-02 already declines to touch that corpus, so this is a provenance note rather than a
gap. Recorded as F-16 and cross-referenced from the Deferred entry.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. Both authored open questions are `resolved` and both survive review. OQ-01's choice of a
DECLARED constant over a DERIVED one is upheld and strengthened: its cost premise was loose ("called
at least once per run"), and the measured figure is exactly 1.0 calls per run per sweep with
`build_cache_facts` at 1.46ms, so the declared form saves real work in a 22.0ms per-run path while
the derived form would additionally have introduced PR-702's silent failure. OQ-02 is upheld, and
PR-705 supplies the further reason that the live corpus is not even reachable from an execution lane.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | high | IN-SCOPE | G. Plan executability | `agent_workflows/run_analytics.py` `build_cache_facts` (takes `projected.get("run")[0]`); review probe over `project_run_facts` | E-01 defined `PRODUCER_METRIC_KEYS` as what `_metric_payload` can emit. That union across five grains is 26 keys; the envelope stores only the 19 run-grain keys. An executor following the wording declares the wrong set and E-03's equality assertion can never pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 and E-03 rewritten to define and derive the vocabulary from `build_cache_facts`; V-01(d)/(e) and V-03(f) added; new F-14 records the per-grain measurement. |
| PR-702 | high | IN-SCOPE | A. Correctness and data integrity | review probe measuring rich 19 vs thin 14 run-grain keys; `build_cache_facts` timed at 1.46ms against a 22.0ms per-run cold sweep | E-02 said to fold "the producer vocabulary" without mandating the declared constants. A per-run derivation makes the token vary by run, so a SPARSE run's entry never invalidates on a vocabulary change while rich runs do: the fix appears to work and the defect silently survives for the runs most likely to be stale. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | fixed | E-02 now mandates `PRODUCER_METRIC_KEYS`/`PRODUCER_EVENT_KEYS` and forbids calling the fact builders in the helper; V-02(e)/(f) added, (f) requiring a THIN entry to move to `rebuild`; the approval paragraph names this as the second misimplementation risk. |
| PR-703 | medium | IN-SCOPE | E. Testing and verification | review probe: thin run emits 14 keys, missing `['cost','cost_currency','cost_is_estimate','token_total','tokens']`, zero event facts; `_metric_payload`'s "OMITTED rather than zero-filled" docstring | E-03's equality guard is valid only against a RICH reference run; a thin fixture legitimately emits a subset. Unstated, this invites a future reader to weaken the assertion to containment, which reopens F-03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | New F-15; E-03 now states the rich/thin distinction and requires a comment recording it; V-03(c) cites the measured gap. |
| PR-704 | medium | IN-SCOPE | E. Testing and verification | review probe showing only run-grain keys reach `metric_facts` | V-03(d)'s mutation proof (inject an extra key into `_metric_payload`) leaves the guard GREEN if the key is injected at a finer grain, making the load-bearing proof vacuous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | V-03(d) now requires a key that reaches the RUN grain and that the executor name which key was used. |
| PR-705 | low | IN-SCOPE | Evidence provenance (Step 1) | `cache.cache_root(Path('.'))` `.exists()` False in-lane; `ls .aw/records/runs/` absent | F-01's and F-02's 298/297 counts describe a gitignored machine-local tree that does not exist in a lane, so they cannot be re-verified at review or at execution. The mechanism they rely on was verified; the digits are an authoring report. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | New F-16; the Deferred entry now cross-references it so no reader cites those digits as reproducible. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan's vocabulary definition is ambiguous at the grain. Pin it to the RUN grain (what the envelope stores), or to the all-grain union (what `_metric_payload` can emit)? | Pin it to the RUN grain for metrics and the EVENT grain for events, defined via `build_cache_facts`. | (a) All-grain union (26 keys): rejected because the envelope never stores those keys, so folding them means a fingerprint reacting to vocabulary the cache does not hold, and E-03's equality could never pass. (b) Leave it to the executor: rejected because the two readings differ by 7 keys and one of them stalls execution. | `build_cache_facts` taking `projected.get("run")[0]` as `metric_facts` and `projected.get("event")` as `event_facts`; probe measuring run grain 19, all-grain union 26, difference `['attempt','event_type','ipd_id6','position','sequence','set_id','timestamp']`. | yes |
| D-2 | E-02 does not say whether to fold the declared constants or the run's own emitted keys. Mandate the constants, or raise it as a blocking question? | Mandate the declared constants in E-02 and add two V-02 sub-checks that catch the per-run form. | (a) Raise as `Blocking: yes`: rejected because the repository answers it decisively (OQ-01 already refuses per-run derivation on hot-path grounds, and the constants exist precisely to be the token), so it is resolvable from evidence. (b) Leave as-is: rejected because the per-run reading fails SILENTLY, rebuilding rich runs while leaving sparse ones stale. | OQ-01's own resolution refusing a derived vocabulary; probe measuring rich 19 vs thin 14 keys and `build_cache_facts` at 1.46ms against a 22.0ms per-run sweep. | yes |
| D-3 | F-01/F-02's live-corpus counts cannot be re-verified in a lane. Treat that as a blocker on the plan's evidence, or record the limitation? | Record it as F-16 and cross-reference the Deferred entry; do not block. | (a) Block pending a maintainer re-measurement: rejected as disproportionate, since no `E-*` or `V-*` item depends on the counts and OQ-02 already declines to act on that corpus. (b) Silently accept the digits: rejected because a later reader would cite them as reproducible evidence when the tree is not even present. | `cache_root(...).exists()` False in-lane and `.aw/records/runs/` absent; the plan's own OQ-02 and Deferred entry declining to touch the live corpus. | yes |
