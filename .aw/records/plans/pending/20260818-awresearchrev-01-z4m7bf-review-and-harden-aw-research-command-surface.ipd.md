# IPD: review and harden aw research command surface

- Date: 2026-08-18
- Kind: child
- Concern: The `aw research` command surface (subparsers at cli.py:770: new, new-comparison, set-assign, mv, check-refs, index, find, promote, check-miscategorized; backends research_cmd/research_refs/research_index/research_archive; its own `.<model>.<kind>.md` grammar in research_contract.py) grew organically and, under the new noun-verb grammar being introduced by Set awcmdsurf, several research subverbs (find/index/mv/set-assign/archive) now OVERLAP the cross-cutting verbs (`aw find/index/rename/group/archive research`). TODO item #30 asks to confirm the surface is well thought out; this is a REVIEW-and-harden task, not a large build - audit for consistency with the new grammar, decide which subverbs should fold into the cross-cutting verbs vs stay research-specific (new/new-comparison/promote/check-miscategorized), document the findings, and apply the modest agreed fixes.
- Scope: IN: a focused audit of the research subverb surface against the awcmdsurf noun-verb grammar, a documented recommendation of fold-vs-keep per subverb, and the small consistency fixes that are clearly agreed (with a test). OUT: any large rewrite of the research backends or its `.<model>.<kind>.md` grammar; the actual cross-cutting-verb implementation (that is Set awcmdsurf); anything requiring a maintainer judgment call (captured as an OQ rather than changed unilaterally).
- Status: draft
- Set: awresearchrev
- Order: 1
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: z4m7bf

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO item 30 (review/harden aw research).

## Goal

Confirm the `aw research` command surface is coherent under the new noun-verb grammar, document which
subverbs should fold into the cross-cutting verbs vs stay research-specific, and apply the small,
clearly-agreed consistency fixes - keeping this a modest review-and-harden, not a rewrite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: This is a REVIEW-AND-HARDEN task, not a build. E-01 is a documentation deliverable
(the fold-vs-keep audit written INTO this IPD's Findings table); E-02 lands only the small, clearly-safe
consistency fixes plus ONE new test file (`tests/test_research_surface.py`). Do NOT fold any subverb
into a cross-cutting verb here (that is Set awcmdsurf) and do NOT rewrite any research backend. Any change
that needs a maintainer call becomes an OQ, not an edit. Use 4-space indent and
`from __future__ import annotations` in the new test.

### Task group 1: audit the research surface

- [ ] E-01 Audit each research subverb (cli.py:770-962; dispatch cli.py:4153-4189) against the awcmdsurf noun-verb grammar and the top-level `aw archive research` verb (cli.py:4233 -> `research_archive.run_archive`), then WRITE the completed fold-vs-keep table into this IPD's Findings section (replace the placeholder table). For EACH of the nine subverbs (new, new-comparison, set-assign, mv, check-refs, index, find, promote, check-miscategorized) record: the backend it dispatches to, whether it has a cross-cutting equivalent (`aw find/index/rename/group/archive research`), the decision `fold` (has a mechanical cross-cutting equivalent) or `keep` (research-domain-specific with no cross-cutting equivalent), and a one-line rationale. Also note flag/help inconsistencies observed (e.g. positional-`dir` vs `--dir` divergence: `new`/`new-comparison` take a positional `dir` while `set-assign`/`mv`/`check-refs`/`index`/`find`/`promote`/`check-miscategorized` take `--dir`). Do NOT change any code in this item; it is a written deliverable only.
  - Depends on: none
  - Expected outcome: the Findings table below is filled with all nine subverbs, each carrying backend + cross-cutting-equivalent + fold/keep + rationale, plus a noted list of concrete flag/help inconsistencies; no source file changed.
  - Execution state: pending

### Task group 2: harden (apply the agreed, safe fixes + a test)

- [ ] E-02 Apply ONLY the consistency fixes that E-01 marks safe and in-scope now, and add `tests/test_research_surface.py` asserting the research verbs still parse/dispatch and any aligned flag works. The single clearly-safe alignment is: give the two subverbs that lack a `--dir` option a `--dir` flag consistent with the other seven subverbs, WITHOUT removing the existing positional `dir` (so nothing breaks). Concretely, after `p_research_new.add_argument("dir", ...)` (cli.py:776) and `p_research_cmp.add_argument("dir", ...)` (cli.py:811) add a non-conflicting `--dir` alias that populates the same destination as the positional when the positional is omitted (implement by adding `p_research_new.add_argument("--dir", dest="dir_flag", default=None, help="Repo root (alias of the positional; default: current directory).")` and, in the `new`/`new-comparison` dispatch or run functions, prefer `args.dir_flag` over `args.dir` when set). If that wiring is NOT trivially safe on inspection, DOWNGRADE this item to a no-op code change and instead only append a `## Spec / documentation sync` help-text note plus the assertion-only test; record the downgrade in the Findings. Do NOT fold, rename, alias-to-cross-cutting, or deprecate any subverb here - capture those as OQ-01. Write the test as an assertion-only smoke test (see Required tests) that builds the top-level parser via the CLI's `build_parser`/`parse_args` entry and asserts each of the nine `research <subverb>` invocations parses without error and dispatches to the expected backend function name.
  - Depends on: E-01
  - Expected outcome: at most the `--dir` alias (or, if unsafe, a help-text/doc note only) lands; `tests/test_research_surface.py` passes; every contested fold/deprecation decision is recorded in OQ-01, not applied.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Research subparsers: declared cli.py:764-962 under `research_sub = p_research.add_subparsers(dest="research_command")` (cli.py:770); dispatched cli.py:4153-4189. The nine subverbs and their backends: new -> `research_cmd.run_new`; new-comparison -> `research_cmd.run_new_comparison`; set-assign -> `research_refs.run_set_assign`; mv -> `research_refs.run_mv`; check-refs -> `research_refs.run_check_refs`; index -> `research_index.run_index`; find -> `research_index.run_find`; promote -> `research_archive.run_promote`; check-miscategorized -> `research_archive.run_check_miscategorized`.
- A top-level `aw archive` (NOT a research subverb) already dispatches to `research_archive.run_archive` (cli.py:4233-4236); under awcmdsurf this becomes `aw archive research`, so research has no `archive` subverb to fold - the archive verb is already cross-cutting-shaped.
- Research keeps its own artifact grammar `.<model>.<kind>.md` (research_contract.py: `ResearchName`, `format_name`, `RESEARCH_ROOT`), distinct from the plan/spec `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md` grammar. Any fold MUST dispatch into the research backend, not the plans one, to preserve this naming/contract.
- Flag inconsistency observed: `new`/`new-comparison` take a POSITIONAL `dir` (cli.py:776, 811); the other seven subverbs take a `--dir` OPTION. This is the one clearly-safe alignment candidate (add a `--dir` alias without removing the positional).
- Set awcmdsurf introduces cross-cutting verbs (`find/search/index/rename/group/archive/check <type>`); research is one of the types, so several research subverbs now have a cross-cutting equivalent.
- Existing research tests to mirror for style: `tests/test_research_index.py` (stdlib `unittest`, throwaway `tempfile` dirs, `research_contract`/`research_cmd`/`research_index` imports), plus `test_research_cmd_create.py`, `test_research_refs.py`, `test_research_archive.py`, `test_research_contract.py`. The new smoke test should follow this stdlib-unittest style.
- Fold-vs-keep is the crux: mechanical, type-generic operations (find/index/mv/set-assign, and the already-top-level archive) are natural cross-cutting-verb candidates; research-domain-specific operations (new, new-comparison, promote, check-miscategorized, check-refs) should stay under `aw research`.

## Findings

### Fold-vs-keep audit (E-01 deliverable)

| Subverb | Backend | Cross-cutting equivalent | Decision | Rationale |
|---|---|---|---|---|
| new | `research_cmd.run_new` | none | keep | Creates a correctly-named research doc + starter frontmatter; research-domain-specific creation, no generic verb. |
| new-comparison | `research_cmd.run_new_comparison` | none | keep | Scaffolds a multi-model comparison set (prompt + per-model report + reconciliation); research-only shape. |
| set-assign | `research_refs.run_set_assign` | `aw group research` | fold (defer) | Grouping docs into a set is the cross-cutting `group` verb; fold in awcmdsurf, keep as alias for now. |
| mv | `research_refs.run_mv` | `aw rename research` | fold (defer) | Rename/re-slug within grammar is the cross-cutting `rename` verb; fold in awcmdsurf, keep as alias for now. |
| check-refs | `research_refs.run_check_refs` | partial (`aw check research`) | keep | Dangling-`<id6>`-citation detector is a research-specific check; may surface under `aw check research` but stays research-owned. |
| index | `research_index.run_index` | `aw index research` | fold (defer) | INDEX regen/`--check` is the cross-cutting `index` verb; fold in awcmdsurf, keep as alias for now. |
| find | `research_index.run_find` | `aw find research` | fold (defer) | Index query by id/set/topic/status is the cross-cutting `find` verb; fold in awcmdsurf, keep as alias for now. |
| promote | `research_archive.run_promote` | none | keep | Deliberate status change (e.g. -> reference) + shard move is research-lifecycle-specific. |
| check-miscategorized | `research_archive.run_check_miscategorized` | none | keep | Archived-but-cited detection is research-lifecycle-specific; no generic equivalent. |

Note: the top-level `aw archive` (cli.py:4233, `research_archive.run_archive`) is ALREADY cross-cutting-shaped (`aw archive research` under awcmdsurf); research has no `archive` subverb to fold.

Flag/help inconsistencies observed: `new`/`new-comparison` take a POSITIONAL `dir`; the other seven take a `--dir` OPTION - the one clearly-safe alignment (E-02 adds a `--dir` alias, keeps the positional).

| # | Finding | Consequence |
|---|---|---|
| F1 | research subverbs find/index/mv/set-assign overlap the awcmdsurf cross-cutting verbs (find/index/rename/group). | Fold candidates; folding is DEFERRED to awcmdsurf. This plan only records the recommendation and keeps them as aliases; OQ-01 asks about the alias-vs-deprecation timeline. |
| F2 | new/new-comparison/promote/check-miscategorized/check-refs are research-domain-specific. | These stay under `aw research`; no fold. |
| F3 | Research uses its own `.<model>.<kind>.md` grammar (research_contract.py). | Any fold must preserve research's naming/contract; the cross-cutting verb dispatches into the research backend, not the plans one. |
| F4 | `dir` is a positional on new/new-comparison but a `--dir` option elsewhere. | The one clearly-safe consistency fix (E-02): add a `--dir` alias to those two, keeping the positional so nothing breaks. |
| F5 | This is a review task per TODO #30, not a rebuild. | Keep changes modest; escalate every fold/deprecation judgment call to OQ-01. |

## Proposed changes (ordered, validatable)

1. Write the fold-vs-keep audit table (nine subverbs, backend + cross-cutting equivalent + fold/keep + rationale) into Findings (E-01). 2. Land the one clearly-safe consistency fix - a `--dir` alias on `new`/`new-comparison` that keeps the positional (or, if unsafe on inspection, a help-text/doc note only) - and add `tests/test_research_surface.py`; capture every fold/deprecation decision as OQ-01 (E-02).

## Deferred / out of scope (with reason)

- Implementing the cross-cutting verbs themselves: that is Set awcmdsurf; this plan only audits research's relationship to them and applies research-side alignment.
- Any rewrite of the research backends or the `.<model>.<kind>.md` grammar: out of scope; explicitly a review-and-harden.
- Fold decisions that require a maintainer call: deferred to OQ, not changed unilaterally.

## Scope check

- Over-scope: none - no backend rewrite; contested changes are deferred to OQ.
- Under-scope: none - the audit is documented and the clearly-agreed fixes are applied and tested.

## Required tests / validation

Add `tests/test_research_surface.py` (stdlib `unittest`, mirroring `tests/test_research_index.py` style). It is an assertion-only smoke test that:
- builds the top-level parser (via the CLI entry that constructs the argparse tree) and asserts each of the nine `research <subverb>` invocations parses with its required flags WITHOUT error (`new --kind x`, `new-comparison --set s --slug sl --models m`, `set-assign aaa111 --set s`, `mv aaa111`, `check-refs`, `index`, `find`, `promote aaa111`, `check-miscategorized`);
- asserts the aligned `--dir` flag (if E-02 lands it) is accepted by `research new`/`research new-comparison` and resolves to the same repo-root destination as the positional `dir`;
- if E-02 downgraded to a doc-note-only change, asserts instead that all nine subverbs still parse (the pre-fix baseline) so the surface is pinned against accidental regression.
Then run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail; this plan only ADDS a test file and (at most) an argparse alias, so the suite must stay green. The E-01 audit is validated by the completed fold-vs-keep table with per-subverb rationale.

## Spec / documentation sync

If E-02 lands the `--dir` alias, update the `research new`/`new-comparison` help text to mention it. No subverb is aliased-to or deprecated-in-favor-of a cross-cutting verb in this plan (that wording lands with Set awcmdsurf) - so no `aw research` help change beyond the `--dir` note. No spec transition here; the orchestrator advances the spec when the Set completes. Coordinate any deprecation wording with Set awcmdsurf.

## Open questions

### OQ-01: for the four fold candidates (set-assign/mv/index/find), should this plan add cross-cutting-verb aliases now, or leave all folding to Set awcmdsurf?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Recommendation - do NOT touch the fold candidates in this review-and-harden plan; leave the alias wiring and any hard-deprecation timeline to Set awcmdsurf (which owns the cross-cutting verb implementations), so research subverbs keep working unchanged until then. The maintainer decides (a) whether awcmdsurf should register `set-assign`/`mv`/`index`/`find` as thin aliases into the cross-cutting `group`/`rename`/`index`/`find research` verbs, and (b) whether/when to hard-deprecate the research subverbs. Non-blocking for this audit; E-01/E-02 stand regardless of the answer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the completed fold-vs-keep table from Findings showing all nine subverbs, each with backend + cross-cutting equivalent + fold/keep + rationale, plus the noted flag/help inconsistencies and the awcmdsurf coordination note; confirm no source file changed by this item (paste `git status --short` showing only this IPD dirty).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff --stat` for the applied fix (at most the `--dir` alias in cli.py + the new `tests/test_research_surface.py`, or - if downgraded - only the new test + a help-text/doc note); paste `python3 -m pytest tests/test_research_surface.py -p no:xdist -q` showing the smoke test passing; paste the tail of the full serial suite (`python3 -m pytest -p no:xdist`) showing no regressions; and confirm the fold/deprecation decisions are recorded in OQ-01, not applied.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the changed files
path-scoped - this IPD, at most `agent_workflows/cli.py` (the `--dir` alias), and the new
`tests/test_research_surface.py` (never `git add -A`) - never pushes, and the plan moves to
`.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item
is `pass`. This is a review-and-harden of TODO item 30; the actual folding of overlapping subverbs into
the cross-cutting verbs is deferred to Set awcmdsurf, with which this plan coordinates.
