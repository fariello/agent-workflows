# Review findings: plan 9zvl2w

- Subject-Id: 9zvl2w
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `f348b227`. The plan on disk was byte-identical to the sealed lane input (`diff`
empty) and `git status --porcelain` was clean, so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0, before and after
the revisions.

THE PLAN'S SCOPE BASIS WAS INVALID, AND THE WAY IT WAS INVALID IS INSTRUCTIVE. The plan did the right
thing by measuring instead of guessing: it grepped `status_256`/`status_label` callers and used the
result to define scope. I re-ran that grep and it is EXACTLY right, all seven modules. The error is one
layer down: `status_256` is not a lifecycle helper. It styles any word against `term.py`'s 56-key
table, and that table mixes lifecycle statuses with generic command outcomes. So a correct measurement
of the wrong predicate produced a scope that is partly empty and partly blind.

Measured lifecycle share of each module's `status_256` calls:

```text
plans_index.py     0 of 4     "up to date" / "wrote" / "updated"      ZERO lifecycle
research_index.py  0 of 4     the same four words                     ZERO lifecycle
status_set.py      2 of 3     "unchanged" is generic; old/new are not
ipd_lint.py        1 of 2     "- Status:" lifecycle; disposition col generic
run_viewer.py      4 of 4     but 29 MORE color256 calls it cannot see
cli.py             5 of 5     but the id6 beside them is hardcoded
```

**1. Task group 1 would have caused a regression and reported it as compliance (PR-604, BLOCKER).**
All eight `status_256` calls in `plans_index.py` and `research_index.py` render an index OUTCOME, not a
status. `up to date`, `wrote` and `updated` each grep to ZERO in spec `uonrjg`. They are precisely the
class R10.3 keeps out ("Generic `Term` outcomes such as command-level OK, WARN, and FAIL remain valid...
Do not mechanically replace every checkmark"). Routing them through the shared resolver sends each to
criterion A20's unknown path, so `aw index plans` would print `?` where a user reads `up to date`
today. I checked whether the indexes have a lifecycle view I was missing: they write statuses into
`INDEX.md`, but that is a COMMITTED markdown file (verified 0 ANSI bytes, header "do not edit by hand"),
which Section 9.5 and A14 keep ANSI-free, so the correct action there is none.

What IS real in those modules is a live A14 violation the plan did not notice: `aw index plans --agent`
emits an ANSI-bearing line, while `aw find plans --agent` and `aw ipd lint --all --agent` emit zero.
E-01 is now that fix plus the recorded determination. This also means E-05's "byte-identical before and
after" bar was wrong for one of three commands: for `aw index` the diff MUST change.

**2. The grep is blind to hardcoded lifecycle colors, and four of them contradict the spec (PR-607).**
`run_viewer.py` has 4 `status_256` calls and 29 direct `term.color256(...)` calls. Several of the latter
paint lifecycle states with a literal index:

```text
:1628 "[in flight]"     214   spec `active` is 220; 214 means waiting-input ONLY
:1847 "YES (in flight)" 214   same
:1401 "[review]"        226   spec `reviewing` is 220; 226 is not a spec index at all
:1995 "[<phase>]"        40   spec `ready` is 45; 40 is not a spec index at all
:1382 "[verified]"       46   matches spec `done`, by luck
:1388 "[verify-failed]" 196   matches spec `failed`, by luck
```

Spec Section 5 uses exactly 11 indices and reserves 214 for `waiting-input`. So the run view currently
paints in-flight work the color the spec reserves for "a human is being asked", which is the exact
collapse Section 5 exists to prevent. Criterion A17 ("no second lifecycle color or glyph table remains")
cannot pass while these literals stand, and `qdd5jq`'s Set-level A17 assertion would fail against them.
E-04 now requires enumerating and classifying all 29.

**3. A10 is violated in two more places, one of them in every row of `aw find` (PR-608, PR-605).** The
id6 is hardcoded to 39 at `cli.py:9475`, `:9536`, `:9573`, independent of status, so A10's "glyph, id6 and
status use the same resolved color" fails on sight. Measured from real output:
`^[[1;38;5;46mexecuted^[[0m ^[[1;38;5;39md5tz36^[[0m`. Separately, the colored artifact TYPE word I
raised against `attention.py` in `f9t5hz` is REPLICATED here in three modules via
`attention._TREE_COLOR_256` (`status_set.py:453`, `ipd_lint.py:1508`, `run_viewer.py:23,1358`). Four views
now share one violation, and no plan in the Set owned it before these two reviews.

**4. E-03 conflated two columns and hid a genuine conflict (PR-606).** `ipd_lint.py` has one lifecycle
`status_256` call (`- Status:`, `:1477`) and one DISPOSITION call (`:1520`) whose vocabulary is
`conforming`/`advisory`/`quarantined`/`legacy/not evaluated`/`error`. One column therefore mixes a value
the spec claims with four generic outcomes it excludes. Both mechanical routes are wrong: converting the
column routes generic outcomes through the resolver, and converting only `quarantined` gives it `parked`'s
gray 244, which is exactly what `legacy/not evaluated` already falls back to. So the spec-conforming
color makes `quarantined` LESS distinguishable than today's 214, cutting against Section 7.2's own reason
for listing it ("the lint view must show it without calling it a pass"). The `◇` glyph is what saves it,
which makes the glyph load-bearing rather than decorative. I left this as a recorded decision for the
executor with both routes and their costs, because either can be made to conform and the choice is a
presentation judgement against code being written.

WHAT I RESOLVED RATHER THAN ASKING. OQ-01 asked whether a backlog index exists that the measurement
missed. Measured across all nine types: `aw index` is supported ONLY for `plans` and `research`; every
other type answers `WARN 'index' is not supported`. So R10.3's "spec index" and "backlog index" name
commands that do not exist, and both trees reach a human through `status_set.py` (which branches on
`record_type == "specs"` and `"backlog"`) and `attention.py`. The question was the right instinct and its
answer also disposes of the other half of R10.3's index clause.

I also found that NO shipped test pins any color this child changes: `grep -c '38;5;'` returns 0 for all
five relevant test files, so the conversion could regress silently and E-05 must ADD assertions rather
than refresh them. Two undeclared files do assert escapes; I checked both. `tests/test_term_components.py`
pins generic badge and path roles, unaffected. `tests/test_cli_find.py:104,118-119` asserts 214 and looks
like a lifecycle assertion but is a filename SEARCH-MATCH highlight from
`cli._highlight_filename_matches`, so it must NOT be recomputed; that near-miss is now recorded so an
executor does not "fix" it.

Suite baseline at review HEAD, run bare: `7468 passed, 3 skipped, 2 xfailed in 100.23s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | MEDIUM | IN-SCOPE | A. correctness | `cli.py:9473,9534,9572`; `ipd_lint.py:1477`; `status_set.py:402,407`; `run_viewer.py:1350,1411,1806,2535` | F-01 claimed "six modules render lifecycle state"; measured, only FOUR surfaces do. The count came from the caller set rather than from what each call renders | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-01 corrected to the four real surfaces with per-site citations |
| PR-602 | MEDIUM | IN-SCOPE | C. architecture | `grep STATUS_COLOR_256` outside term/attention returns nothing; direct `color256` counts `plans_index` 1, `research_index` 1, `status_set` 4, `ipd_lint` 7, `run_viewer` 29 | F-02 concluded from "no local tables" that the work is "call-site routing, not table deletion", which understates it: hardcoded per-call lifecycle colors exist and the caller-set grep cannot see them | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-02 rewritten to keep the true half and point at PR-607; Step 0 carries the measured `color256` counts |
| PR-603 | MEDIUM | IN-SCOPE | E. verification | Measured: `aw index plans --agent` -> 1 ANSI-bearing line (`^[[1;38;5;46mup to date^[[0m`), `aw find plans --agent` -> 0, `aw ipd lint --all --agent` -> 0; source `plans_index.py:429,432` | A14 is not uniformly satisfied, so E-05's single "byte-identical before and after" bar would either mask a live ANSI leak or fail a correct fix | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-03 records it; E-01 owns the fix; E-05 and V-05 now state the per-command bar (empty diff for two commands, NON-empty for `aw index`) |
| PR-604 | BLOCKER | OVER-SCOPE | A. correctness; D. anti-regression; F. UX | `plans_index.py:432,436,440,446` and `research_index.py:650,654,658,664` all pass `up to date`/`wrote`/`updated`; each greps to 0 in `uonrjg`; `status_set.py:396` passes `unchanged`; `uonrjg` R10.3; criterion A20; `INDEX.md` verified 0 ANSI and marked generated | THE SCOPE BASIS IS INVALID. Scope was derived from `status_256` callers, but that helper also styles generic outcome words R10.3 excludes. E-01's two modules contain ZERO lifecycle calls, so the plan's entire Task group 1 would route generic words through the resolver, printing `?` via A20's unknown path where users read `up to date`: a regression presented as compliance | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | E-01 inverted: records the determination and fixes the real A14 leak instead of converting; F-04 added as BLOCKER with the measurement; "convert by VALUE, not by call site" stated in Concern, Step 0, E-02 and the scope fence; generic words added to Deferred; V-01 forbids pasting a fabricated marker |
| PR-605 | HIGH | UNDER-SCOPE | B/F. accessibility and UX | `status_set.py:453`, `ipd_lint.py:1508`, `run_viewer.py:23,1358` all using `attention._TREE_COLOR_256` = 33 bold; legitimate path-segment use at `attention.py:1729`; criterion A10; Section 11 item 5 | The colored artifact TYPE word raised against `attention.py` in `f9t5hz` is replicated in three of this child's modules and was owned by no plan. The Section 11 exemption covers a path's tree segment, not a bare type word, so relying on it makes A10 untestable across four views | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | F-05 added; E-02 names the site and points at the shared decision; V-02 demands the type word show NO escape or a written justification; the gate ties the decision to `f9t5hz`'s so the two cannot diverge |
| PR-606 | HIGH | IN-SCOPE | A. correctness; B. accessibility | `ipd_lint.py:1477` vs `:1520`; `ipd_schema.py:1470-1472`; measured `term.STATUS_COLOR_256`: `conforming` 46, `quarantined` 214, `error` 196, `legacy/not evaluated` ABSENT -> 244; spec `parked` = 244 + `◇`; Section 7.2; D15; `ipd_lint.py:1123` | E-03 conflated the lifecycle `- Status:` column with the DISPOSITION column, whose vocabulary mixes `quarantined` with four generic outcomes. Converting wholesale violates R10.3; converting only `quarantined` gives it the same gray 244 that `legacy/not evaluated` falls back to, making it LESS distinguishable than today and cutting against Section 7.2's stated purpose | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-03 split into the lifecycle column plus a RECORDED DECISION for the disposition column, with both routes and the measured cost of each, and the `◇` glyph made load-bearing if gray is adopted; F-06 added; V-03 demands the decision and a distinguishability proof; Spec sync records that keeping 214 would need a spec amendment |
| PR-607 | HIGH | UNDER-SCOPE | A. correctness; D. anti-regression | `run_viewer.py:1628` and `:1847` (214 where `active` is 220 and 214 means waiting-input), `:1401` (226, not a spec index), `:1995` (40, not a spec index), `:1382`/`:1388` (46/196, match by luck); 29 direct `color256` calls vs 4 `status_256`; Section 5's 11 indices; criterion A17 | The caller-set measurement sees a fraction of this module's lifecycle styling. Four hardcoded colors contradict Section 5, including painting in-flight work the color reserved for "a human is being asked". A17 cannot pass while they stand, and `qdd5jq`'s Set-level assertion would fail | C:Medium; U:Medium; S:Low; F:Medium-High; Overall:Medium | FIXED | E-04 now requires enumerating all 29 `color256` sites, classifying each lifecycle or generic, and converting the lifecycle ones, with the four contradictions named; F-07 added; V-04 item 2 demands the enumeration as evidence |
| PR-608 | HIGH | UNDER-SCOPE | B/F. accessibility and UX | `cli.py:9475`, `:9536`, `:9573` (`color256(..., 39, bold=True)`); measured `^[[1;38;5;46mexecuted^[[0m ^[[1;38;5;39md5tz36^[[0m`; criterion A10; `cli.py:9473` reads `e.disposition or e.status` | In `aw find`, the id6 is hardcoded to 39 regardless of status, so A10's shared-color requirement fails in every row. Unaddressed, the first converted view still shows a mismatched id6 | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-04 now covers the id6 explicitly and notes the disposition-or-status column needs the same value-based split; F-08 added; V-04 item 3 demands a row showing one shared escape, contrasted with the measurement |
| PR-609 | MEDIUM | UNDER-SCOPE | E. testing and verification | `grep -c '38;5;'` -> 0 in `tests/test_plans_index.py`, `tests/test_research_index.py`, `tests/test_status_set.py`, `tests/test_ipd_lint.py`, `tests/test_run_viewer.py`; `tests/test_cli_find.py:104,118-119` (search-match highlight); `tests/test_term_components.py:145-156` (generic roles) | No shipped test pins any color this child changes, so the conversion could regress silently and E-05's "update snapshots" framing implies assertions that do not exist. Two undeclared files DO assert escapes, and one is a near-miss that must not be recomputed | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `tests/test_status_set.py` and `tests/test_research_index.py` added to `- Scope-Paths:`; E-05 requires ADDING escape-level assertions; F-09 added; V-05 demands the new node ids and an explicit statement that the `cli_find` highlight was left alone; the gate forbids recomputing it |
| PR-610 | LOW | IN-SCOPE | G. executability | Measured across all nine types: only `plans` and `research` are supported; the rest answer `WARN 'index' is not supported for <type>`; `status_set.py:516,582,603` branch on `record_type` `specs`/`backlog` | OQ-01 was deferred to execution but is answerable from the code now, and leaving it open invited an execution-time investigation plus a possible wrong guess about a view that does not exist | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved with the measurement; Deferred records that the two named indexes do not exist and where those trees' lifecycle actually reaches a human; F-10 added |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01 would route `plans_index`/`research_index` `status_256` calls through the lifecycle resolver, but every one renders a generic outcome word. Fix in place, or escalate as blocking? | FIX IN PLACE: invert E-01 to record the determination and fix the module's real defect (the A14 ANSI leak). Classify by VALUE rather than by call site throughout the plan. | (a) Leave E-01 as authored: rejected, it is a measurable regression, printing `?` via A20's unknown path where users read `up to date`. (b) Escalate as `Blocking: yes` for a maintainer: rejected, R10.3 answers it in as many words ("Generic `Term` outcomes... are outside this spec. Do not mechanically replace every checkmark"), so no contract question is open and stalling the plan would spend a maintainer's turn on a settled point. (c) Delete E-01 and drop both modules from scope: rejected, it would silently discard the live A14 violation I measured in exactly those modules, leaving a release-gating criterion broken with no owner. | `plans_index.py:432,436,440,446`; `research_index.py:650,654,658,664`; `up to date`/`wrote`/`updated` each grep to 0 in `uonrjg`; R10.3; criterion A20; measured `aw index plans --agent` -> 1 ANSI-bearing line; `INDEX.md` verified 0 ANSI and marked generated; Section 9.5. | yes |
| D-2 | The lint disposition column mixes `quarantined` with four generic outcomes, and the spec's `parked` gray collides with `legacy`'s fallback gray. Decide the treatment, or hand it to the executor? | HAND IT OVER as a RECORDED DECISION with both routes, their measured costs, and the constraint that the `◇` glyph is load-bearing if gray is adopted. | (a) Mandate converting only `quarantined` to `parked`: rejected as under-informed, because 244 is exactly what `legacy/not evaluated` already falls back to, so the spec-conforming color reduces distinguishability and Section 7.2's purpose ("show it without calling it a pass") is then carried entirely by the glyph. (b) Mandate leaving the whole column generic: rejected, it contradicts the spec's Section 7.2 table and D15, which name `quarantined` explicitly. (c) Escalate as blocking: rejected, both routes can be made to conform and nothing irreversible turns on it; the choice depends on the glyph support the executor actually has from `bn026f`. | `ipd_lint.py:1477` vs `:1520`; `ipd_schema.py:1470-1472`; measured `conforming` 46, `quarantined` 214, `error` 196, `legacy/not evaluated` absent -> 244; spec `parked` 244 + `◇`; Section 7.2; D15; `ipd_lint.py:1123`. | yes |
| D-3 | OQ-01: does a backlog index (or spec index) exist that the caller-set measurement missed? | NO, resolved by measurement. Record in Deferred that both name commands which do not exist, and where those trees' lifecycle actually reaches a human. | (a) Leave it open for execution as authored: rejected, it is answerable in one command and an open question invites an execution-time detour plus a wrong guess about a nonexistent view. (b) Treat R10.3's mention as an obligation and author a new child for a backlog index: rejected, that would build a command the spec only mentions in passing, which is scope creep from an imprecision in prose. | Measured across all nine types: only `plans` and `research` are supported, the rest answer `WARN 'index' is not supported for <type>`; `status_set.py:516,582,603` branch on `record_type` `specs`/`backlog`; `attention.py` covers both trees and is converted by `f9t5hz`. | yes |
| D-4 | `run_viewer.py` has four hardcoded colors that contradict Section 5. Convert them here, or leave them to `qdd5jq` which owns the runners? | CONVERT HERE. `run_viewer.py` is this child's declared module and is not a runner driver. | (a) Defer to `qdd5jq`: rejected, `qdd5jq`'s scope is `oc_runipd.py`/`agy_runipd.py`/`runner_shared.py`/`render_stream.py`, and `run_viewer.py` appears in THIS plan's `Scope-Paths`; deferring would leave its Set-level A17 assertion failing against literals nobody was assigned to fix. (b) Convert only the `status_256` sites and leave the literals: rejected, that is precisely the blind spot that makes A17 unsatisfiable while every item here passes. | `run_viewer.py:1401,1628,1847,1995` versus Section 5's 11 indices (214 = waiting-input only, `active` = 220, `ready` = 45); `qdd5jq` `- Scope-Paths:` excludes `run_viewer.py`; criterion A17. | yes |
| D-5 | `tests/test_cli_find.py` asserts `38;5;214` on id6-looking tokens. Is that a lifecycle assertion this child must recompute? | NO. It pins a filename search-match highlight; leave it unchanged and record the near-miss. | (a) Recompute it with the rest: rejected, `cli._highlight_filename_matches` colors matched SUBSTRINGS of a path and is a text-search affordance outside this spec; recomputing it would change unrelated behavior and could fold search highlighting into lifecycle styling. (b) Say nothing: rejected, it asserts 214 on six-character id6-shaped tokens, so it reads exactly like a lifecycle assertion and an executor sweeping for escape changes would plausibly "fix" it. | `tests/test_cli_find.py:98-121`; `cli._highlight_filename_matches(path, tokens, term)` takes match tokens and highlights them within the filename; the assertion's own comment says "highlights match in filename in bold orange-yellow (214)". | yes |
