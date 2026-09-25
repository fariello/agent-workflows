# Review: Split research pipeline position from shelf status so a prompt carries no hot status

- Subject-Id: 5e3nj2
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims re-derived at HEAD `aac47b12`. The target plan was committed and unchanged, so the
pre-review snapshot was correctly skipped per Step 1. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE review and again at
`--phase review-finalize` after every revision.

THE AUTHOR'S SIX FINDINGS ALL HOLD, and I re-derived each independently rather than trusting the
table, because this plan's diagnosis is unusually specific and worth confirming before critiquing the
fix. `research_cmd.plan_new_comparison._mk` does pass `status="todo"` for the order-00 prompt (F-1).
The `awclia` stubs are 224, 228, 236 and 257 bytes, front matter only, and `aw attention` really does
class prompt `f79ve1` as `parked` while classing the ADOPTED `3nlmug` as `ready` (F-2/F-3), which is
the inversion in both directions the plan claims. The `aw set done` probe reproduces exactly: in a
scratch repo `aw set done aaa111 --yes` exits 0 and commits `status: done`, after which
`validate_frontmatter` returns `status must be one of ['active', 'archive', 'reference', 'todo']`
(F-4). F-5's correction of the backlog item is right: `hostprobe`, `awdeliv` and `wtiso` carry a
`research-report` at order 00 and no prompt at all, so only `chkplace`/`rzfaon` is genuinely
double-homed. F-6's corpus numbers re-measure identically (19 of 50 sets carry a prompt; 7 hot, 15
cold), refined to 22 prompts over 122 indexed docs with zero scan drift. I also prototyped E-04's
algorithm end to end and it produces EXACTLY the expected outcome the item claims: `f79ve1` present in
the new `derive_unrun_prompts`, and `3nlmug`, `jd8qhs`, `g5vhpz`, `2838rp`, `q48a20` all absent. The
design is sound.

THE DOMINANT FINDING IS PR-703, AND IT IS THE PLAN DOING THE EXACT THING IT EXISTS TO PREVENT. E-06
mapped pipeline position straight onto the attention class (`unrun`->READY, `partial`->ACTIVE,
`synthesized`->DONE) and applied the cold guard only INSIDE the `unrun` branch of the derivation. So a
prompt that a human deliberately shelved, sitting in a set that happens to be `partial`, takes its
board class from the derived position instead of from its own shelf status. I implemented the mapping
as specified and measured it over the live corpus: EIGHT prompt classes change, and six of those are
resurrections of cold-shelved prompts - `uke9sw`, `p8h6ab`, `zsbirf` (`archive`, set `occomms`),
`75iqeg`, `tsjhfq` (`archive`, set `planrev`) all move `parked` -> ACTIVE, and `yq6aub` (`reference`,
set `awoptimize`) moves `done` -> ACTIVE. Only two of the eight changes (`f79ve1` -> ready, `3nlmug`
-> done) are the intended fix. That is worse than the defect being fixed, because it silently
overrides an explicit human decision rather than mis-deriving an unknown one, and a plan whose whole
thesis is "two axes, not one conflated field" would have shipped the pipeline axis overriding the
shelf axis. The fix is a stated precedence rule, applied once and at all three read sites, plus a
regression test with a cold prompt in a partial set, plus V-08 requiring evidence on all eight
prompts. The plan's own validation named only `f79ve1` and `3nlmug`, which is precisely the spot check
that cannot see the six.

PR-701 IS THE ONE THAT WOULD HAVE FAILED FIRST, MECHANICALLY. The spec path the plan declared in
`- Scope-Paths:`, in E-01 and in the spec-sync section does not exist:
`20260824-2000-01-research-lifecycle-reliability.spec.md` was renamed to
`20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md` in commit `d6b2fa00` ("records:
rename specs 25kzda and 5tapom onto the id6 grammar"). An executor would have hit a missing file on
E-01 and the finalize scope gate would have reconciled against a path nobody can edit. Reading the
real spec then surfaced the larger half of the finding: it pins the rules this plan replaces in TWO
MORE places. Section 4's non-goal says "No change to the filename grammar, the four `status` values,
..." and Section 5's AC-1 ("lists exactly the UNRUN prompts (structural derivation)") and AC-2(a) ("an
`intake`/`active` doc whose set is RUN") name the exact two rules E-04 deletes. Amending 3.1/3.2
alone leaves an approved spec contradicting itself and carrying acceptance criteria that test removed
behavior.

PR-702 IS A DEFECT THE PLAN CREATES AND THEN ASSERTS IS FINE. E-05's expected outcome read "`--to
reference` still moves it into the shard." It moves the file, and it does not write the status.
`research_archive._rewrite_status_in_text` walks the front matter for a line
`startswith("status:")` and returns the text UNCHANGED when there is none; `apply_moves` calls it and
then `git mv`s regardless. I measured the helper on a statusless prompt and it is a verbatim no-op. So
the first cold promote of one of the very files E-11 makes statusless would shard a document carrying
no status at all, which `_scan_docs` reads back as `status=""` inside `reference/`. The failure is
silent in the worst way: the command exits 0, the file moves, and the only observable is the moved
file's contents, which is why V-06 now requires reading them.

PR-704 IS TWO SHIPPED TESTS WITH OPPOSITE CONSTRAINTS, AND THE PLAN NAMED ONLY ONE. E-06 said the
position map lives in `attention_contract._PROMPT_PIPELINE_MAP` "mirrored as `_RESEARCH_PAIRS` entries
in `lifecycle_style` so `test_all_owner_enums_are_covered_by_native_maps` holds." That test does hold,
because `_assert_covered` checks only `set(owner_statuses) - mapped == []`, a coverage test a superset
satisfies. But `tests/test_attention_contract.py::MappingTotalityTests` asserts
`set(A.CLASS_MAPS["research"].keys()) == set(research_contract.STATUSES)`, an EQUALITY that a superset
breaks. The two maps therefore have opposite tolerances, and the plan's wording invited widening both.
The item now says explicitly that `_RESEARCH_MAP` stays byte-identical and unregistered-in-`CLASS_MAPS`
is where the new map lives, and V-07 requires a diff of that test file so the easy wrong fix (relaxing
the assertion) is visible rather than passing.

PR-705 IS A CONSUMER THE GREP COULD NOT FIND. The Scope-check bullet claimed completeness on the basis
of a grep for `run_prompt_set_ids`, `derive_unrun_prompts`, `HOT_STATUSES`, `normalize_status` and
`TYPE_STATUSES`. None of those five appears in `selectors.py`, which nonetheless reads research
`status` through `_YAML_KEYS = ("id", "status", "set")` - the YAML-dialect fallback IPD `xo3244` added
precisely because research does not use the bullet dialect. Measured: `aw find research todo -p`
returns 12 paths today and 7 of them are the hot prompts E-11 strips. After E-11 those prompts match
no status selector, and no position selector exists either, since neither `aw find` nor `aw research
find --status` knows about pipeline position. I chose the smaller fix (add `--position` to the verb
that already owns the index, rather than teach `selectors` a second axis) and required a before/after
measurement so the discoverability loss is a recorded decision.

PR-706 IS AN HONESTY CORRECTION RATHER THAN A DEFECT, and I raise it because the plan's justification
is stronger than its evidence. E-04 narrows the `STALE_STATE_RULE` "doc in RUN set" branch to
`synthesized` only, on the reasoning that "a landed `todo` report in a `partial` set is legitimately
awaiting ingestion." Measured: `run_prompt_set_ids` returns 9 sets and the new `synthesized` set is 5,
but of the 12 live `stale-state-to-promote` findings the narrowing removes exactly ONE, which is
`f79ve1` (the fix). The four `awclia` stubs stay flagged only incidentally, through
`cited_by_executed_ids`, because the executed plan `lpqy64` names their id6s. And there is no live
instance of the justifying case at all: every document in the three `partial` sets is already
`reference` or `archive`. The narrowing is correct and forward-looking; describing it as a measured
cleanup would overstate it.

PR-707 IS RIGHT-SIZING AND THE GATE. The count lint passed at ten items and measures only structural
count. The old E-06 named a new contract map, a mirrored style map, a validator relaxation, two
reclass functions, `item_for_path` and two test files across four modules, with four unrelated test
surfaces, and its two halves have entirely different failure modes (a broken shipped test versus six
resurrected prompts). The old E-05 bundled an index band with two unrelated `research_archive`
changes. It is now thirteen items, still one concern. The gate was two sentences: no statement of what
a human is approving, no scope fence over eleven declared code paths, no stop conditions, no honesty
rule, and an unconditional finalize instruction. That matters more than usual here because three of
this plan's four consequences are hard to notice and one is hard to reverse (a front-matter contract
change plus 7 tracked files losing a line).

CONTRACT CHECKS. `aw check release-gates --agent` reports `findings:0`. The plan's `- Work-Kind: bug`
correctly carries `- Blocks-Release: next` inherited from `imntrh` (`graduated`, same gate), satisfying
the every-live-bug rule. `- From-Backlog: imntrh` resolves. The spec amendment is legitimate per
AGENTS.md and is declared in `- Scope-Paths:`; the narrower constraint applies
(`.aw/records/specs/README.md` forbids hand-editing a spec's status or history), so E-01 is now
explicitly body-only. One finding this review INTRODUCED and then fixed: OQ-01 had no durable carrier,
which `evaluate_durable_carrier` reported at `error` severity; adding `- Carrier: imntrh` (a real
`graduated` item that genuinely owns the follow-on) clears it, and the three new Deferred rows each
carry a substantive `Carrier-Declined`. I also recorded the pre-existing suite failure
(`test_blast_radius_zero_across_pending_plans`, stranded prerequisite `72qlya` referenced by pending
plan `je74a0`, reproducing at both `aac47b12` and `25eb9a08`) in the plan, so V-13 cannot absorb it as
this plan's damage nor be blocked by it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-703 | HIGH | IN-SCOPE | A. Correctness / D. Anti-regression / F. UX | Plan E-06 "`unrun`->READY, `partial`->ACTIVE, `synthesized`->DONE ... (absent position: `reference` or no status -> DONE, `archive` -> PARKED)"; the cold guard sits only in E-04's `unrun` branch; prototyped over the live corpus: 8 prompt classes change, of which `uke9sw`/`p8h6ab`/`zsbirf` (`archive`, `occomms`) and `75iqeg`/`tsjhfq` (`archive`, `planrev`) go `parked` -> `active` and `yq6aub` (`reference`, `awoptimize`) goes `done` -> `active`, all because their sets are `partial` | THE ITEM MEANT TO SEPARATE THE TWO AXES COLLAPSES THEM BACK TOGETHER, WITH THE DERIVED AXIS OVERRIDING THE HUMAN ONE. A cold shelf status is an explicit human decision to stop looking at a document; a pipeline position is a derived fact about set shape. Mapping position onto the attention class unconditionally makes the derived fact win, so SIX prompts a human deliberately archived or shelved return to the live board as ACTIVE work. Only 2 of the 8 class changes are the intended fix. This is a worse failure than the one being fixed: the original defect mis-derives an unknown state, while this silently contradicts a known one, and it is invisible in the plan's own validation because V-06 named only `f79ve1` and `3nlmug`. | C:Low; U:Medium; S:Low; F:High; Overall:Medium (the fix is one stated precedence rule plus a regression test; no new derivation) | FIXED | Added F-9 with all six measured resurrections. Added a `## Goal` paragraph and a "SHELF OUTRANKS POSITION AT EVERY READ SITE" paragraph in Proposed changes stating the rule ONCE so the three consumers cannot diverge. Split the old E-06 and rewrote the attention half as E-08: position classifies ONLY a prompt with no shelf status; a `reference`/`archive` prompt keeps its `_RESEARCH_MAP` class and its position is never consulted. E-05 and E-10 carry the same rule for the index band and the new query. V-08 now requires JSON evidence on all EIGHT class-changing prompts and says explicitly that two-prompt evidence does not satisfy it. A new test case (an `archive` prompt in a PARTIAL set -> parked) is the standing guard. The rejected converse precedence is recorded in Deferred so it is not re-litigated. |
| PR-701 | HIGH | IN-SCOPE | G. Plan executability / A. Correctness (stale citation + incomplete spec amendment) | Plan cited `.aw/records/specs/approved/20260824-2000-01-research-lifecycle-reliability.spec.md` in `- Scope-Paths:`, E-01 and the spec-sync section; the file does not exist; the real path is `20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md`, renamed in `d6b2fa00`; that spec ALSO pins the replaced rules at Section 4 ("No change to ... the four `status` values") and Section 5 AC-1 / AC-2(a) | THE DECLARED SPEC DOES NOT EXIST, AND THE AMENDMENT IS INCOMPLETE WHERE IT DOES. Three separate places name a path that was migrated onto the id6 grammar, so E-01 fails on a missing file and the finalize scope gate reconciles against an uneditable path. Reading the real file shows the larger half: amending only 3.1/3.2 leaves Section 4's non-goal forbidding the change the plan makes, and leaves Section 5's AC-1 and AC-2(a) specifying the structural-sibling derivation and the `intake`/`active`-in-RUN-set rule that E-04 deletes. The result is an approved spec that contradicts itself and whose acceptance criteria describe removed behavior - which is exactly the drift the plan's own spec-sync rationale says it exists to prevent. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (a path correction plus two more sections in the same file) | FIXED | Corrected all three citations to the id6 path and noted the rename with its commit. E-01 rewritten to enumerate FOUR amendment sites (3.2's vocabulary bullet, 3.1's sibling definition, Section 4's non-goal, Section 5's AC-1/AC-2(a)) with the reason each is load-bearing, and made body-only with the status/history prohibition and the `aw specs note` route. Scope-sync section rewritten to state the rename and the four sites. Added a stop condition for the spec having moved again or its quoted text having changed. Recorded as F-7. |
| PR-702 | HIGH | IN-SCOPE | A. Correctness / E. Testing | `research_archive._rewrite_status_in_text` matches only an EXISTING `startswith("status:")` line and returns the text unchanged otherwise; `apply_moves` calls it then `git mv`s regardless; measured at review the helper is a verbatim no-op on a statusless front matter; plan E-05's expected outcome read "`--to reference` still moves it into the shard" | THE PROMOTE PATH IS BROKEN FOR EXACTLY THE FILES THIS PLAN CREATES, AND THE PLAN ASSERTS THE OPPOSITE. E-11 makes 7 prompts statusless; the first time anybody promotes one to `reference` or `archive`, the status rewrite silently does nothing and the file is sharded into a cold directory carrying no status at all, which `_scan_docs` then reads as `status=""`. So the fix manufactures a new inconsistency in the same tree it is cleaning, through a command that exits 0 with no diagnostic. The only observable is the moved file's contents, so a test asserting the refusal (which is what the plan specified) passes while the real defect ships. | C:Low; U:Low; S:Low; F:High; Overall:Medium (an insert path in one helper, with the field order already defined by `FRONTMATTER_FIELDS`) | FIXED | Added F-8 with the measurement. Split the promote work into its own E-06 requiring `_rewrite_status_in_text` to INSERT at the canonical `FRONTMATTER_FIELDS` position when no line exists, with the reason stated. V-06 requires TWO pieces of evidence: the current helper shown returning a statusless text UNCHANGED (the defect exhibited), and a full `aw research promote --to reference` whose MOVED file is then read to show `status: reference`. Added an explicit ordering constraint in Proposed changes: E-06 lands before or with E-11, since E-11 creates the first statusless prompts. |
| PR-704 | MEDIUM | IN-SCOPE | D. Anti-regression / C. Architecture | `tests/test_attention_contract.py::MappingTotalityTests` asserts `set(A.CLASS_MAPS["research"].keys()) == set(research_contract.STATUSES)`; `tests/test_lifecycle_style.py::_assert_covered` asserts only `set(owner_statuses) - mapped == []`; measured `lifecycle_style.resolve("research","unrun")` returns stage `unknown` with a diagnostic today; plan E-06 named only the `lifecycle_style` test | THE TWO CONTRACT MAPS HAVE OPPOSITE TOLERANCES AND THE PLAN'S WORDING INVITED BREAKING ONE. Adding the three position tokens to `attention_contract._RESEARCH_MAP` fails a shipped equality assertion; adding them to `lifecycle_style._RESEARCH_PAIRS` is fine because that guard is a coverage check. The plan mentioned "mirrored as `_RESEARCH_PAIRS` entries ... so `test_all_owner_enums_are_covered_by_native_maps` holds", showing awareness of the permissive test and none of the strict one. The likely wrong fix is to relax the equality, which would retire the load-bearing guard that the research class map matches the research status enum - and that guard is what would have caught this plan's own axis confusion at the contract level. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-10 and a Project-conventions bullet stating both tests and their opposite constraints with the asserting expressions. Split the contract work into E-07, which requires the position map be a NEW `_PROMPT_PIPELINE_MAP` NOT registered in `CLASS_MAPS`, leaves `_RESEARCH_MAP` byte-identical, and widens only the superset-tolerant `lifecycle_style` map. V-07 requires both invariants shown by `python3 -c` (equality still True, `resolve("research","unrun")` now diagnostic-free) AND a `git diff` of the test file, failing the item if the existing equality was relaxed. |
| PR-705 | MEDIUM | UNDER-SCOPE | C. Architecture / F. UX | `selectors._YAML_KEYS = ("id", "status", "set")` (the YAML-dialect fallback from IPD `xo3244`); measured `aw find research todo -p` returns 12 paths of which 7 are `.research-prompt.md`; the plan's completeness grep was over `run_prompt_set_ids`, `derive_unrun_prompts`, `HOT_STATUSES`, `normalize_status`, `TYPE_STATUSES`, none of which appears in `selectors.py` | A THIRD STATUS READER WAS MISSED, AND WITH IT A DISCOVERABILITY LOSS NOBODY DECIDED TO TAKE. `aw find research <status>` reads research front matter through its own YAML key list, so it is a consumer of the field this plan removes from prompts, and the plan's five-symbol grep could not match it. After E-11 the 7 stripped prompts answer NO status query, and no position query exists either, since neither `aw find` nor `aw research find --status` knows about pipeline position. A user or script asking "which research is outstanding" by the obvious command gets a silently shorter answer. The Scope-check bullet also claimed consumer completeness on the strength of that grep, which is not a completeness proof. | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | Added F-11 and a Project-conventions bullet naming the reader and the IPD that added it. Added E-10, which takes the SMALLER fix (leave `selectors.py` alone, since a statusless record correctly matches no status selector, and add `--position` to `aw research find`, the verb that already owns the index) plus a `tests/test_cli_find.py` case pinning that prompts no longer answer a status query. V-10 requires the before/after `aw find research todo -p` pair so the loss is recorded rather than discovered. Rewrote the Scope-check under-scope bullet to say plainly that a five-symbol grep is not a completeness proof. |
| PR-706 | LOW | IN-SCOPE | F. Honest documentation | Plan E-04 narrows the `STALE_STATE_RULE` set-branch to `synthesized` "since a landed `todo` report in a `partial` set is legitimately awaiting ingestion"; measured: `run_prompt_set_ids` -> 9 sets, new `synthesized` -> 5, but of 12 live `stale-state-to-promote` findings the narrowing removes exactly ONE (`f79ve1`); the four `awclia` stubs stay flagged via `cited_by_executed_ids` because executed plan `lpqy64` names their id6s; every doc in the three `partial` sets is already `reference`/`archive` | THE NARROWING IS CORRECT BUT ITS JUSTIFICATION HAS NO LIVE INSTANCE, AND THE PROSE IMPLIES A MEASURED CLEANUP. The reasoning describes a landed-but-unignested report in a partial set; no such document exists in the corpus today. The narrowing's actual live effect is one removed finding, which is the fix itself, and four stubs that keep their flag only through an incidental citation. A later reader comparing the rule's before/after counts would find them almost identical and reasonably conclude the change did nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 with the full breakdown (9 -> 5 sets, 12 -> 11 findings, the `lpqy64` coincidence, and the absence of any live justifying case). Added a Deferred row recording that the four `awclia` stubs keep their flag for an accidental reason this plan does not correct, with a `Carrier-Declined` explaining that the verdict is nonetheless correct today so nothing is owed. |
| PR-707 | LOW | UNDER-SCOPE | G. Plan executability (right-sizing + execution contract) | Old E-06 named a contract map, a mirrored style map, a validator relaxation, two reclass functions, `item_for_path` and two test files across four modules with four unrelated test surfaces; old E-05 bundled an index band with two unrelated `research_archive` changes; gate was two sentences with `Cohesion rationale: not required` | THE TWO LARGEST ITEMS FAILED THE PLAN'S OWN RIGHT-SIZING RULE, AND THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS. The count lint passed at ten items and measures only structural count, never conceptual density; the old E-06's two halves have entirely different failure modes (breaking a shipped test versus resurrecting six shelved prompts), which is the clearest possible signal they are separate passes. The gate stated nothing about what a human is approving - and three of this plan's four consequences are easy to miss (a front-matter contract change, a deliberate `aw find` behavior change, an approved-spec non-goal being overruled) while one is hard to reverse (7 tracked files losing a status line). It had no scope fence over eleven declared code paths, no stop conditions, and an unconditional `aw ipd finalize` instruction that is wrong under a runner that owns the transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low (decomposition and contract text; no scope change beyond PR-705's item) | FIXED | Split into thirteen items (E-05/E-06 from the old E-05; E-07/E-08 from the old E-06; E-10 new per PR-705) each with its own `V-*`, giving a 13:13 bijection; `Highest E allocated` updated to 13 and E-13's dependency list completed. Substantive cohesion rationale added naming each split and its reason. Gate rewritten: a what-a-human-is-approving paragraph ranking the four consequences by consequence; a per-symbol scope fence framed as a DECLARATION, cross-referencing the new EXPLICITLY NOT IN SCOPE list; the hard-MUST honesty rule naming V-08, V-06 and V-07 as the three fakeable claims with why each is fakeable; three genuine stop conditions; `aw commit 5e3nj2` with the `imntrh` gate-inheritance statement; and conditional runner/executor finalize ownership. Recorded as F-13. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | When a prompt has BOTH a cold shelf status and a set pipeline position, which one decides its board class? | SHELF OUTRANKS POSITION. A `reference`/`archive` prompt classifies by `_RESEARCH_MAP` and its position is never consulted; position classifies only a statusless prompt. | (a) Position always wins (the plan as authored) - rejected on measurement: it resurrects six deliberately shelved prompts onto the live board, silently overriding an explicit human decision. (b) A new combined class or a compound label - rejected: it would need an `ATTENTION_CLASSES` addition, which is a cross-tree contract change far outside this plan, and the board has no place to render two axes per row. (c) Ask the maintainer - rejected: the repository already answers it, since a cold status is written only by a human-confirmed `aw research promote` and spec `5tapom` Section 4 / H2 record explicit distrust of blind status writes. | Prototyped mapping over the live corpus (8 class changes, 6 resurrections); `attention_contract._RESEARCH_MAP`; spec `5tapom` 3.2's human-confirmed triage requirement | yes |
| D-2 | Where does the pipeline-position vocabulary live, given the two contract maps disagree about growth? | A new `attention_contract._PROMPT_PIPELINE_MAP` NOT registered in `CLASS_MAPS`, plus three appended `lifecycle_style._RESEARCH_PAIRS` entries. | (a) Add the tokens to `_RESEARCH_MAP` - rejected: breaks `MappingTotalityTests`' equality assertion. (b) Relax that assertion to a subset check - rejected: it is the load-bearing guard that the research class map matches the research status enum, and it is the kind of contract test that would have caught this plan's own axis confusion; weakening a guard to admit a change is the wrong direction. (c) Put positions in neither map and inline the mapping in `attention.py` - rejected: `lifecycle_style.resolve("research","unrun")` returns the `unknown` stage today, so a renderer reaching for a style would get the fallthrough. | Both test assertions read at review; `L.resolve(FAMILY_RESEARCH,"unrun")` measured returning stage `unknown` with a diagnostic | yes |
| D-3 | After E-11, prompts answer no status query. Teach `selectors` about position, or add a filter to `aw research find`? | Add `--position` to `aw research find`; leave `selectors.py` untouched. | (a) Teach `selectors._YAML_KEYS` a synthetic position value - rejected: that module's docstring records at length that its key lookup is deliberately narrow and case-sensitive, and that the no-perturbation proof for the other nine record types rests on it; adding a derived pseudo-field there would require a `_scan_docs` inside a hot generic path. (b) Accept the loss silently - rejected: measured, it changes the answer of a command that returns 12 paths today, so it is a user-visible behavior change that must be recorded. | `selectors.py`'s own docstring on the narrow lookup; measured `aw find research todo -p` = 12 paths, 7 prompts; `research_index.query` already owns index filtering | yes |
| D-4 | `_rewrite_status_in_text` no-ops on a statusless file. Fix it here, or file it? | Fix it here, as its own item ordered before E-11. | (a) File it separately - rejected: this plan is what makes statusless files exist, so shipping E-11 without the fix creates a reachable data-corruption path that does not exist today; a fix owned elsewhere would land after the corruption became possible. (b) Have E-11 leave an empty `status:` line instead - rejected: an empty value fails `normalize_status` and would be read as invalid front matter, trading a silent no-op for a scan drift entry on 7 tracked files. | Measured helper no-op; `apply_moves` calling it then moving regardless; `normalize_status("")` returns `ok=False` | yes |
| D-5 | `status` must become optional for one kind only. Skip the field in the presence loop, or remove it from `FRONTMATTER_FIELDS`? | Skip it in the loop for `research-prompt`; never edit the tuple. | (a) Remove it from the tuple - rejected: the tuple is the ONLY thing making `status` required, so removing it drops the requirement for every kind, silently contradicting the plan's own "answer kinds keep `status` required"; the tuple is also the canonical field order `research_cmd.build_frontmatter` emits, so a deletion reorders every newly written document. (b) A separate per-kind required-fields table - rejected as disproportionate for one field on one kind, and it would fork the field-order definition. | `research_contract.FRONTMATTER_FIELDS` and the unconditional presence loop in `validate_frontmatter`; `build_frontmatter`'s emission order | yes |
| D-6 | The stale-rule narrowing removes only one live finding and has no live instance of its stated justification. Keep it, or drop it? | Keep it, and relabel the justification as forward-looking with the measurement. | (a) Drop the narrowing - rejected: without it a `partial` set's landed `todo` report would be flagged stale the moment one lands, which is the false-positive class this whole plan exists to remove; the absence of a live instance is because the corpus is old, not because the case is impossible. (b) Leave the prose implying a measured cleanup - rejected: a later reader comparing before/after counts would find them nearly identical and conclude the change was inert. | Measured 12 -> 11 findings, 9 -> 5 sets, the `lpqy64` citation coincidence, and every doc in the three `partial` sets already cold | yes |
