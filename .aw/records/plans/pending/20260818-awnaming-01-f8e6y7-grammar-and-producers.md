# IPD: awnaming grammar + producers (all-repos, ships): teach the filename grammar and emit .type.md

- Date: 2026-08-18
- Kind: child
- Concern: Spec 20260817-2147-01 (RELEASE BLOCKER, backlog 047ce9), awnaming Order 01. Adopt ONE artifact-naming grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md` for all durable record types by moving the TYPE signal into the filename. This Order is the ALL-REPOS, shipped half: teach the two filename-grammar sites to accept an optional `.<type>` before `.md`, make the name generator + producers EMIT `.type.md`, and make `aw plan-names` validate it. The record readers already glob `*.md` and read metadata from front-matter, so dual-read is free and this Order adds no reader breakage.
- Scope: The shipped grammar + producers + validator. IN: `plans_refs._CLUSTERED_RE`/`clustered_name`, `normalize_plan_names._CLUSTERED_RE`/`is_conformant`/`parse_name`, `aw plan-names`, `aw plans mv`/`research mv` Order-preservation, `aw backlog new` name, `aw ipd scaffold` name derivation, tests. OUT: renaming this repo's existing files (Order 02); AGENTS.md prose (Order 02); the version number (S6-V01); research `.<model>.<kind>.md` (already type-style); run-artifacts; the optional rename-on-migrate nicety (follow-up backlog item).
- Status: reviewed
- Set: awnaming
- Order: 1
- Highest E allocated: 08
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: f8e6y7

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): built from spec 20260817-2147-01 + code investigation (2 grammar sites, front-matter-driven readers => dual-read free).
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE WITH REVISIONS APPLIED; cited lines verified (plans_refs.py:31/125/162/374, backlog.py:324, normalize_plan_names.py:110); PR-003 (closed-enum facet to avoid dotted-slug mis-parse, E-01/E-02) and PR-004 (scaffold --path backward-compat, E-05) fixed in place.

## Goal

Ship the uniform `.type.md` naming grammar as new-file behavior for ALL repos: the two filename-aware
sites accept an optional `.<type>` facet before `.md`, the name generator and every durable-record
producer EMIT `.type.md` (`.ipd.md`/`.prompt.md`/`.spec.md`/`.walkthrough.md`/`.roadmap.md`/
`.backlog.md`/`.comms.md`; research keeps its `.<model>.<kind>.md`), and `aw plan-names` validates the
grammar. Existing bare-`.md` files keep reading and validating (permanent dual-read), so no
intermediate state is broken and this repo's own files are renamed separately in Order 02.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: teach the grammar to the two filename-aware sites

- [ ] E-01 Extend `plans_refs._CLUSTERED_RE` (agent_workflows/plans_refs.py:31, which uses `\A...\Z` and a non-greedy `<slug>`) to accept an OPTIONAL `.<type>` facet before the trailing `.md`, as a CLOSED enum group `(?:\.(?P<type>ipd|prompt|spec|walkthrough|roadmap|backlog|comms))?` inserted before `\.md\Z`. The closed enum (not `.+`) prevents a dotted slug from being mis-parsed as a facet. Keep the existing groups (date/set/nn/id6/slug) intact.
  - Depends on: none
  - Expected outcome: `_CLUSTERED_RE.match("20260818-awnaming-01-f8e6y7-grammar-and-producers.ipd.md")` and the same name without `.ipd` both match with identical date/set/nn/id6/slug groups; a name with an unknown facet like `.foo.md` does NOT match as a facet.
  - Execution state: pending
- [ ] E-02 Extend `normalize_plan_names._CLUSTERED_RE` (.aw/system/workflows/setup-repo/tools/normalize_plan_names.py:110, which uses `^...$` and a greedy kebab `<slug>`) with the SAME closed-enum `.<type>` facet group adapted to its anchors, and update `parse_name` (:165) + `is_conformant` (:198) so a `.type.md` clustered name is parsed and reported conformant (and bare `.md` remains conformant). This is the tool `aw plan-names` loads (cli.py:2897). Because the two regexes differ in anchors/slug greediness, insert the facet in each without altering their existing anchor/slug semantics.
  - Depends on: none
  - Expected outcome: `is_conformant("20260818-awnaming-01-f8e6y7-grammar-and-producers.ipd.md")` is True; `parse_name(...)` returns the same Parsed as the bare name; bare `.md` stays conformant; an unknown `.foo.md` facet is not treated as a valid type.
  - Execution state: pending

### Task group 2: make the name generator + producers emit .type.md

- [ ] E-03 Add an optional `artifact_type` parameter to `plans_refs.clustered_name` (agent_workflows/plans_refs.py:125) that appends `.<type>` before `.md` when given, and thread the plan type (`ipd` for a plan) through its callers at plans_refs.py:162 and :374 so `aw plans mv` produces `<...>.ipd.md`. Preserve backward behavior when no type is passed.
  - Depends on: E-01
  - Expected outcome: `clustered_name(date=..., set_id=..., order=1, id6=..., slug=..., artifact_type="ipd")` returns a `...-<slug>.ipd.md` string; called with no type it returns the current bare `.md`.
  - Execution state: pending
- [ ] E-04 Make `aw backlog new` emit `.backlog.md`: change the filename construction at agent_workflows/backlog.py:324 (`f"{today}-{item.set}-01-{item.id}-{slug}.md"`) to append `.backlog.md`, and update the backlog reader glob/`check` so both `.backlog.md` and legacy bare `.md` are found and validated.
  - Depends on: E-01
  - Expected outcome: `aw backlog new` writes a `<...>.backlog.md` file; `aw backlog check` passes on both a new `.backlog.md` item and a legacy bare `.md` item.
  - Execution state: pending
- [ ] E-05 Make `aw ipd scaffold` derive the canonical clustered `.ipd.md` filename when `--set`/`--order` are given (closing part of vf03z3 scaffold-name gap): in `ipd_authoring.run_scaffold` (agent_workflows/ipd_authoring.py:210) compute the destination name via `clustered_name(..., artifact_type="ipd")` (date=today, id6 minted or from `--id`) WHEN `--path` is omitted. BACKWARD COMPAT: an explicit `--path` remains fully honored (existing callers, tests, and workflow docs that pass `--path` must behave exactly as before); the derivation is additive, only for the no-`--path` case. Also ensure the minted id6 is written into the front-matter `- Id:` so name and Id agree.
  - Depends on: E-03
  - Expected outcome: `aw ipd scaffold --kind child --set demo --order 1 --title X` (no `--path`) writes `.aw/records/plans/pending/<today>-demo-01-<id6>-x.ipd.md` with front-matter `- Id:` == the filename id6; an invocation WITH `--path` still writes exactly that path (compat test green).
  - Execution state: pending

### Task group 3: validate the grammar + preserve Order on rename

- [ ] E-06 Make `aw plan-names` (via `_run_plan_names`, cli.py:2908) report `.type.md` clustered names as conforming and legacy bare `.md` as conforming, and flag a name whose `.<type>` does not match the artifact's actual type (e.g. a plan named `.spec.md`) as nonconforming. + a focused test.
  - Depends on: E-02
  - Expected outcome: `aw plan-names` over a tree containing both `.ipd.md` and bare `.md` plans reports all conforming; a deliberately mistyped `.spec.md` plan is flagged.
  - Execution state: pending
- [ ] E-07 Fix `aw plans mv` (and `research mv`) to PRESERVE `- Order:` and NOT recompute the date to "now" while renaming to the `.type.md` grammar (closing the vf03z3 mv-clobber): in the mv path (plans_refs.py:374 area, artifact_core mv at :141) keep the plan's existing `- Order:` and `- Date:` front-matter untouched; only the on-disk name + refs change. + a regression test asserting Order and Date survive an `aw plans mv --slug X`.
  - Depends on: E-03
  - Expected outcome: a test renames a plan with `- Order: 3` and a past `- Date:` via `aw plans mv` and asserts both survive unchanged and the new name carries `.ipd.md`.
  - Execution state: pending

### Task group 4: cover it with tests

- [ ] E-08 Add `tests/test_awnaming_grammar_and_producers.py` covering: both grammar regexes accept `.type.md` + bare `.md`; `clustered_name` emits the facet; `aw backlog new` -> `.backlog.md`; `aw ipd scaffold` derives an `.ipd.md` name; `aw plan-names` conformance incl. a mistyped-facet failure; `aw plans mv` preserves Order + Date. Run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04,E-05,E-06,E-07
  - Expected outcome: the new test module passes and the full serial suite is green (no regressions from the dual-read/producer changes).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Record READERS are front-matter-driven and glob `*.md` (plans.py:184, plans_index.py:91, ipd_lint.py:758, backlog.py:238, research_refs.py:105), so `.type.md` files already read; dual-read is FREE and PERMANENT.
- Filename grammar is enforced in exactly two sites: `plans_refs._CLUSTERED_RE` and the shipped tool `normalize_plan_names.py` (loaded by `aw plan-names` at cli.py:2897). Research (`research_contract.parse_name`, :265) is already `.type`-style and OUT of scope.
- Name generator is `plans_refs.clustered_name` (:125), used at :162 and :374; `aw plans mv` has the known vf03z3 bug of clobbering `- Order:` to 0 and recomputing `- Date:` to now.
- `aw ipd scaffold` currently requires a hand-built `--path` and does not derive the canonical name (the vf03z3 scaffold gap).
- Slug group forbids `.`, so a `.type` facet must be its own optional regex group, not part of the slug.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Readers ignore the filename tail (front-matter driven). | Dual-read is free; this Order changes no reader logic, only generators + the 2 grammar checkers. |
| F2 | Only 2 grammar sites + 1 generator to touch. | Small, contained change; the risk is producer breakage, covered by E-08 + the full suite. |
| F3 | `mv` clobbers Order/Date (vf03z3). | E-07 fixes it as part of adopting the grammar so Order 02's rename does not corrupt front-matter. |
| F4 | Not every type has a `new` verb (roadmap/walkthrough/prompt-library). | Those emit no new files programmatically; their `.type.md` naming is enforced by Order 02's rename + `plan-names`, not a producer here. Noted in OQ-01. |

## Proposed changes (ordered, validatable)

1. Extend the two grammar regexes for an optional `.<type>` facet (E-01, E-02).
2. Thread an `artifact_type` through `clustered_name` and its callers (E-03).
3. Emit `.type.md` from the producers that create files: backlog (E-04), ipd scaffold (E-05).
4. Validate via `aw plan-names` incl. a mistyped-facet failure (E-06).
5. Fix `mv` Order/Date preservation (E-07).
6. Lock it with a dedicated test module + full serial suite (E-08).

## Deferred / out of scope (with reason)

- Renaming this repo's ~267 existing files + AGENTS.md prose: Order 02.
- Roadmap/walkthrough/prompt-library file creation: no programmatic `new` verb creates them, so there is no producer to flip here; their names are enforced by Order 02's rename + `plan-names` (see OQ-01).
- The optional rename-on-migrate migration nicety (OQ-02 in the orchestrator): a follow-up backlog item, not this Set.
- Research naming (`.<model>.<kind>.md`): already type-style; unchanged.

## Scope check

- Over-scope: none - every E maps to the shipped grammar/producer/validator surface.
- Under-scope: none for the ALL-REPOS half - Order 02 owns the this-repo rename + docs; the two together satisfy the spec.

## Required tests / validation

`tests/test_awnaming_grammar_and_producers.py` (E-08) + the full serial suite + `aw plan-names` clean.
Each V-item below pins one E to falsifiable evidence.

## Spec / documentation sync

Spec 20260817-2147-01 stays `draft` until the whole Set lands (advanced by the orchestrator). AGENTS.md
grammar prose is reconciled in Order 02 (this Order ships code + the validator, not the prose).

## Open questions

### OQ-01: Do comms/roadmap/walkthrough/prompt-library files get a producer here, or only rename+validate?

- Blocking: no
- Status: open
- Owner: opencode (resolve during execution when touching each type)
- Resolution or deferral rationale: those types have no programmatic `new` verb that mints a filename (unlike plans/backlog), so there is no producer to flip in this Order. Their `.type.md` naming is enforced by Order 02's rename + `aw plan-names` validation. If a `new`-style verb is later added for one, it emits `.type.md` via `clustered_name(artifact_type=...)`. Not blocking: the grammar + validator (this Order) already recognize the facets.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python snippet result showing `plans_refs._CLUSTERED_RE` matches the `.ipd.md` name and the bare name with identical named groups.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `is_conformant`/`parse_name` results for the `.ipd.md` and bare names (both conformant, same Parsed).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `clustered_name(...)` output with and without `artifact_type="ipd"`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste an `aw backlog new` run showing a `.backlog.md` file created + `aw backlog check` passing on both a `.backlog.md` and a legacy bare `.md` item.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste an `aw ipd scaffold ... --set demo --order 1` (no `--path`) writing a `<...>.ipd.md` whose front-matter `- Id:` equals the filename id6.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `aw plan-names` over a mixed tree (all conforming) + a mistyped `.spec.md` plan flagged nonconforming.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the regression test output proving `- Order:` and `- Date:` survive an `aw plans mv --slug X` and the new name carries `.ipd.md`.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste the tail of the full serial suite (`python3 -m pytest -p no:xdist`) showing the new module + total pass count with no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(opencode Opus 4.8) performs each E, verifies each V with pasted evidence, commits ONLY the files it
changed path-scoped, never pushes, and moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every V-item is `pass`. Part of the awnaming Set
(orchestrator 6gy9rf); precedes Order 02.
