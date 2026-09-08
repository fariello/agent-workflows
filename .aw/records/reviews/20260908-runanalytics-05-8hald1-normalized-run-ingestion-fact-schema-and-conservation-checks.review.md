# Review: normalized run ingestion, fact schema, and conservation checks (child 8hald1, Set runanalytics)

- Subject-Id: 8hald1
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `0aea0771`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the eight-item split and
the rewritten V-item bijection.

METHOD, AND IT IS THE WHOLE STORY OF THIS REVIEW. The plan asserted that the checkout contains no live run
corpus. That claim is load-bearing for an ingestion plan, so it was the first thing checked rather than the
last. It is false: 135 real runs are present. Every subsequent finding came from actually parsing them and
COMPUTING the plan's own equations over real data, rather than reasoning about whether the equations looked
right. Two of the plan's central assumptions did not survive that, and neither would have been caught by
reading the document carefully.

WHAT THE PLAN GETS RIGHT, and it is the genuinely difficult part of a metrics layer. The insistence on
storing raw numeric observations and categorical keys rather than chart aggregates is exactly right, and it
is the decision that makes later medians, quantiles and regressions possible without reparsing. The time
model is better than most: representing wall-clock and activity intervals separately, refusing to force
overlapping activities to sum to elapsed time, and publishing `observed_activity_time`,
`unattributed_time` and `overlap_time` so the totals stay honest, is precisely the discipline that stops a
dashboard from quietly inventing attribution. Requiring a derived total to be LABELLED, and refusing to
assume cache is additive when a provider may already include it, shows real familiarity with how usage
reporting actually varies. And the gate's closing rule is the sharpest sentence in the document: missing,
unavailable and not-applicable are distinct, and none of them is zero.

THE ROOT FINDING IS THAT THE PLAN BELIEVED IT WAS FLYING BLIND. "The checkout contains no live run corpus.
Implementers must use checked-in synthetic fixtures." Measured: 135 run directories, ALL carrying
`state.json`, `events.jsonl`, `execution-report.md`, `sessions/`, `outcomes/` and `prompts/`, spanning
THREE driver generations (`oc_runipd.py` 120, `runipd.py` 13, `ipdrunner.py` 2) and ZERO Agy runs. The harm
is specific rather than reputational: a parser validated only against fixtures its own author invented from
its own assumptions is a parser that has never met the format. Order 01's review found and corrected the
identical false claim in its own plan, so this is a property of the Set's authoring rather than one slip.

BECAUSE THE CORPUS EXISTS, THE PLAN'S CONSERVATION EQUATION COULD BE TESTED, AND IT FAILS. This is the
finding that most changes the code. The plan requires that "input/output/cache/total tokens and recorded
cost reconcile at every available grain". Computed over all 176 real attempts carrying usage:
`input + output + cache == total` holds for 174 and FAILS for 2. Both failures are attempts carrying a
`reasoning` key, and in both the shortfall equals `reasoning` EXACTLY (deltas 2658 and 1120). Reformulated
as `sum(every key except total) == total`, it holds for 176 of 176 with zero mismatches. So the authored
equation would have shipped a conservation check that fires a FALSE violation on real runs. The predictable
reaction to a check that cries wolf is to loosen it, and a conservation check with a tolerance detects no
double counting at all, which is the single property this plan exists to provide. E-06 now implements the
all-components form, requires an unknown component key to participate automatically, and V-06 requires BOTH
forms pasted with the two failing runs named, so the choice is evidenced rather than asserted.

THE TOKEN VOCABULARY WAS WRONG IN BOTH DIRECTIONS, which is worth separating from the equation itself. The
plan names "input, output, cache read/write when distinguishable, and total". Measured across 176 attempts:
`input`, `output`, `cache` and `total` at 176 each, plus `reasoning` at 2. There is no cache-read/cache-write
split anywhere in the corpus, only a single `cache`; and `reasoning`, which does exist, went unmentioned. A
schema built from the authored list would have five named columns, silently dropping `reasoning` today and
the next provider key tomorrow. E-05 now requires an OPEN component map, which is also what makes E-06's
all-components equation self-maintaining.

THE PRIVACY REQUIREMENT WAS CORRECT BUT UNTETHERED. The plan rightly forbids retaining prompts, responses,
file content, raw hosts and absolute paths. What it never established is that the risk is LIVE, and it is:
every one of the 135 `state.json` files carries an absolute `repo` path, and scanning that single field with
the shipped detector returns `home-path` and `handle`, BOTH at `fail` severity. The corpus additionally holds
472 prompt files and 460 session files, roughly 238 MB of model conversation. Without that grounding, the
read-side check could reasonably have been run only over sanitized fixtures, where it proves nothing. E-08
now requires the detector be run over facts built from the REAL corpus, with a control run proving the same
invocation flags the raw `repo` field, because a clean report and a detector that was not looking are
indistinguishable. E-08 also settles that this plan CONSUMES Order 02's projector rather than writing a
second one: `bzz5e6` E-04 is explicitly "the only path by which a fact reaches the envelope", and a parallel
projector here would defeat the property that item exists to establish.

TWO PROMISED SOURCES DO NOT EXIST IN ANY REAL RUN. `ledger.jsonl` is present in ZERO of 135 runs, and
`telemetry/` in ZERO (the latter expected, since Order 04 has not executed). E-01 promised to recognize
"telemetry, and ledger distinctions", which reads as validated support. Both are fixture-only, and saying so
matters because a later reader would otherwise credit this plan with coverage it cannot have.

THE VERSION-TOLERANCE REQUIREMENT HAD NO MEASURED TARGET, and now it does. `schema_version` is uniformly `1`
across all 135 runs, so it cannot discriminate the three driver generations; only the `driver.path` basename
can. The real drift surface is narrow and pleasant: six distinct `state.json` key shapes, fourteen keys
present in every one, and exactly four that vary (`_invocation_start_mono`, `run_order`, `session_id`,
`session_turn_counts`). E-02 now targets that rather than an imagined drift, and requires an unknown key be
recorded and non-fatal, since a newer driver will add more.

ON SIZING. Three E-items, and E-03 alone named five independent deliverables (precedence, deduplication,
conservation, partial-run semantics, quality summaries, cache integration) across unrelated test surfaces,
while E-02 named ten fact grains in one item. Eight of the Set's eleven plans carry exactly three items, and
the count-based lint conformed both before and after the split into eight. This is the fourth sibling split
for the same reason (`bzz5e6` 3->6, `lhccjf` 3->8, `5f2h8i` 3->7), and the fifth consecutive plan whose gate
carried no execution contract. Both patterns are in the authoring pipeline, not in any one plan, and are
worth raising with the maintainer rather than rediscovering in the six remaining unreviewed siblings.

ONE PLEASANT FINDING WORTH RECORDING. The corpus is completely clean on the corruption axis: all 1428 event
lines across 135 runs parse. So the plan's required "corrupt event line" case has no real-data exemplar and
must be driven by a deliberately corrupted fixture. That is not a defect, but an executor who assumed the
smoke corpus exercised it would ship untested error handling.

WHY APPROVE WITH REVISIONS RATHER THAN OPEN QUESTIONS. Nothing needed a human. The conservation form was
settled by measurement, the projector ownership by reading the sibling's own text, and the corpus question by
the same resolution Order 01 reached; all three are recorded as decisions. No BLOCKER or unfixed HIGH
remains.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-063 | HIGH | IN-SCOPE | D. domain invariants; evidence accuracy | enumerated and parsed all 135 `state.json` files; driver basenames `oc_runipd.py` 120 / `runipd.py` 13 / `ipdrunner.py` 2 / Agy 0 | **"THE CHECKOUT CONTAINS NO LIVE RUN CORPUS" IS FALSE, AND IT IS THE CLAIM AN INGESTION PLAN LEANS ON MOST.** 135 run directories exist, all with the full artifact set, across three driver generations. A parser validated only against fixtures written from its author's assumptions is a parser that has never met the format, and this false premise is what allowed PR-064 and PR-065 to go unnoticed. Order 01's review corrected the identical claim, making it a Set-wide authoring error | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The conventions bullet is REPLACED with the measured corpus description (135 runs, the three generations, zero Agy), designating it a read-only smoke corpus with fixtures authoritative and nothing committed; the Goal states the correction and why it is not cosmetic; E-01 builds the inventory against it; V-01 requires the counts re-measured at execution. OQ-03 records the usage decision. New F-1 |
| PR-064 | HIGH | IN-SCOPE | A. correctness and data integrity | computed both forms over all 176 real attempts: four-term 174 pass / 2 FAIL with deltas 2658 and 1120 equal to `reasoning`; all-components 176/176 | **THE STATED CONSERVATION EQUATION FAILS ON REAL DATA.** `input + output + cache == total` fires a false violation on the two attempts carrying a `reasoning` key. Reformulated over all component keys it holds universally. Shipping the authored form means a check that cries wolf, and the predictable response is to add a tolerance, which detects no double counting at all: the one property this plan exists to deliver | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | New E-06 implements `sum(all keys except total) == total`, requires an unknown component key to participate automatically, and requires a genuine injected mismatch to still fail; V-06 requires BOTH forms pasted with the two failing runs and exact deltas named, so the implemented form is evidenced rather than asserted; OQ-01 records the decision and rejects both the five-named-keys and the tolerance alternatives. New F-2 |
| PR-065 | HIGH | IN-SCOPE | A. correctness; C. architecture (schema) | key frequency over 176 attempts: `input`/`output`/`cache`/`total` 176 each, `reasoning` 2; no cache-read/write key anywhere | **THE TOKEN VOCABULARY WAS WRONG IN BOTH DIRECTIONS.** The plan names a cache read/write split that does not exist in the corpus and omits `reasoning`, which does. Five named columns would silently drop `reasoning` today and the next provider key tomorrow, and would also make the conservation check un-maintainable | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 requires an OPEN component map plus a total, with the measured five keys covered and an unseen sixth preserved; V-05 requires a `reasoning` attempt and an invented-key attempt both shown surviving; the Findings prose corrected with the measurement. New F-3 |
| PR-066 | HIGH | UNDER-SCOPE | B. security and privacy; E. testing | `scan_text` over the `repo` field of a real `state.json` -> `home-path` and `handle`, both `fail`; 472 prompt files, 460 session files, ~238 MB; `bzz5e6` E-04 text | **THE PRIVACY REQUIREMENT WAS CORRECT BUT UNTETHERED, AND THE OWNERSHIP OF THE PROJECTOR WAS UNSTATED.** All 135 `state.json` files carry an absolute `repo` path that the shipped detector flags at `fail`, and the corpus holds ~238 MB of conversation, so the hazard is live; without that grounding the read-side check could have been run only over sanitized fixtures and proven nothing. Separately the plan never said whether it writes its own projector, while Order 02's E-04 is explicitly "the only path by which a fact reaches the envelope" | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | New E-08 requires facts to reach the cache ONLY through Order 02's projector and forbids a second projector or sanitizer; V-08 requires the detector run over facts built from the REAL corpus PLUS a control run proving it flags the raw `repo` field, and forbids committing a canary as a literal; a conventions bullet records the measurement. New F-4 |
| PR-067 | MEDIUM | IN-SCOPE | Honest documentation; E. testing | presence counts across all 135 runs: `ledger.jsonl` 0, `telemetry/` 0 | **TWO PROMISED SOURCES EXIST IN ZERO REAL RUNS.** E-01 promised to recognize "telemetry, and ledger distinctions", which reads as validated support; neither has a real-data exemplar (telemetry legitimately so, since Order 04 has not executed). Left unsaid, a later reader credits this plan with coverage it cannot have | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 states which adapters are FIXTURE-ONLY (Agy, ledger, telemetry) and why; V-01 requires that statement explicitly; the conventions bullet on `ledger.jsonl` records the zero count; the required-tests section names the four cases the real corpus cannot exercise. New F-5 |
| PR-068 | MEDIUM | UNDER-SCOPE | A. compatibility; E. testing | `schema_version` uniformly `1` across 135 runs; six distinct top-level key shapes; 14 keys in all shapes, 4 varying | **"VERSION-TOLERANT" HAD NO MEASURED TARGET, AND THE OBVIOUS DISCRIMINATOR DOES NOT WORK.** `schema_version` is `1` everywhere, so it cannot distinguish the three driver generations; only the `driver.path` basename can. The real drift is a stable 14-key core plus exactly four optional keys | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-02 targets the measured lattice: the 14-key core required, the four optional keys tolerated, an unknown key recorded and NEVER fatal; E-01 requires generation inference from the `driver.path` basename with `schema_version` treated as insufficient; V-02 requires a test per key shape plus a mutation check. New F-6 |
| PR-069 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | `grep -c` across the Set -> eight of eleven at exactly 3 E-items; lint conforming BOTH before and after the split | **THE E-ITEMS WERE MECHANICALLY SIZED.** E-03 named five independent deliverables across unrelated test surfaces; E-02 named ten fact grains in one item. The count-based lint cannot see this. Fourth sibling with the identical finding (`bzz5e6` 3->6, `lhccjf` 3->8, `5f2h8i` 3->7) | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into EIGHT items across four groups (sources / facts / integrity / privacy-handoff); `Highest E allocated` 03 -> 08; V-01..V-08 rewritten to bijection; a right-sizing note records the measurement; cohesion rationale restated to say it justifies one PLAN, not one ITEM |
| PR-070 | MEDIUM | UNDER-SCOPE | G. executability | plan gate as authored (two sentences); four sibling review records | **THE GATE CARRIED NO EXECUTION CONTRACT**: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle move, no re-measure warning. Fifth consecutive sibling with the same omission | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full contract added: approval requirement, both load-bearing dependencies with WHY each matters, and the four consuming Orders that make the fact schema a contract; a fence naming seven measured prohibitions with the finalize `--scope-reason`/`--scope-ack` mechanics; path-scoped commit with re-verify-after-failed-hook; a never-commit-the-corpus rule with the leak measurement behind it; the honesty rule; re-measure-every-corpus-number; and THREE stop conditions |
| PR-071 | LOW | IN-SCOPE | E. testing; evidence accuracy | parsed every line of all 135 `events.jsonl`: 1428 of 1428 parse | The corpus is clean on the corruption axis, so the required "corrupt event line" case has no real-data exemplar and must be fixture-driven. Not a defect, but an executor assuming the smoke corpus exercised it would ship untested error handling | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 and V-07 state the 100 percent clean measurement and require a deliberately corrupted FIXTURE, with the run still producing facts and other runs unaffected; the required-tests section lists it among the cases the corpus cannot exercise. New F-9 |
| PR-072 | LOW | IN-SCOPE | Evidence accuracy; Presentation | bare `python3 -m pytest` at `0aea0771` -> `2 failed, 5655 passed, 3 skipped, 2 xfailed`; `grep -c '\\`'` -> 16 before the fix | Two mechanical gaps: no measured baseline despite requiring a bare suite run, so an executor meeting two pre-existing failures could not tell them from its own; and 16 escaped backtick pairs rendering as literal backslashes, after Order 01's six, Order 02's four, Order 03's ten and Order 04's eighteen from the same pipeline | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline recorded with both node ids named and attributed as pre-existing, plus compare-node-ids-not-totals and the empty-delta criterion; a fixtures-are-authoritative rule added noting both current failures are themselves live-corpus couplings; all 16 backticks unescaped and verified zero remaining |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What exactly must the conservation equation reconcile? | `sum(every component key except total) == total`, with an unknown key participating automatically | The authored four-term `input+output+cache == total`, rejected on measurement: it fails on 2 of 176 real attempts, both carrying `reasoning`, with the shortfall equal to `reasoning` exactly. Enumerating five named keys including `reasoning`, rejected because it merely relocates the failure to the next unseen provider key. Adding a tolerance, rejected outright because a conservation check that tolerates a mismatch detects no double counting, which is the sole property this plan exists to deliver | both forms computed over all 176 attempts (174/2 versus 176/0); the two failing runs and their deltas identified | yes |
| D-2 | Does this plan write its own privacy projector? | NO. It consumes Order 02's, which is declared the only path a fact may take to the envelope | A local projector "just for facts", rejected because two allowlists drift and the weaker becomes the effective boundary, defeating the property `bzz5e6` E-04 exists to establish. Relying on `leak_sanitizer` as the boundary, rejected because a detector is a denylist by nature and cannot be a write-side guarantee; it is the read-side oracle. Saying nothing, rejected because the plan is a fact PRODUCER and an executor would reasonably build its own | `bzz5e6` E-04's text ("the only path by which a fact reaches the envelope"); `Item-Dependencies` already requiring `executed:bzz5e6`; measured `scan_text` results at `fail` on the real `repo` field | yes |
| D-3 | How is the real 135-run corpus used, now that it is known to exist? | Read-only SMOKE corpus and the source of format measurements; checked-in fixtures remain authoritative for every assertion; never committed | Ignore it and use fixtures only, as authored, rejected because it produced two undetected defects (the conservation form and the token vocabulary) and yields a parser that has never met the format. Use it as test fixtures, rejected because it is gitignored, mutable, grows with every run, and carries absolute paths the detector flags at `fail`; the suite's two current failures are exactly this mistake made earlier. Commit a sample, rejected on the same leak measurement | corpus enumerated; `scan_text` on the `repo` field; the two live-corpus-coupled suite failures; Order 01's identical resolution | yes |
| D-4 | Split the three E-items, or accept them since the lint passes? | SPLIT into eight across four groups | Accept the authored three, rejected because E-03 named five independent deliverables and the controlling workflow states a passing count-based size lint does NOT clear right-sizing. Split into separate child PLANS, rejected because the cohesion claim is genuine: precedence, schema grain and conservation constrain each other and must be designed as one data contract. Keep privacy inside the conservation item, rejected because the privacy boundary is the one property with an external owner (Order 02) and deserves its own verification | eight of eleven Set plans at exactly 3 items; lint conforming before and after; plan-review's right-sizing diagnostics answering YES for E-03 | yes |
| D-5 | How is version tolerance specified, given `schema_version` is uniformly 1? | Infer the generation from the `driver.path` basename; require the measured 14-key core, tolerate the four measured optional keys, record an unknown key and never fail on it | Key on `schema_version`, rejected on measurement: it is `1` across all 135 runs and discriminates nothing. Require every observed key, rejected because four keys legitimately vary and a newer driver will add more, so a strict shape would reject future runs. Fail on an unknown key, rejected because ingestion of a newer run is exactly the case that must degrade gracefully rather than abort | `schema_version` parsed across the corpus; the six-shape key lattice with its 14-key intersection and 4-key symmetric difference | yes |
