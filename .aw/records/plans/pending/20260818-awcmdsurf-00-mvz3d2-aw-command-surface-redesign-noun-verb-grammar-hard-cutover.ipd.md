# IPD: aw command-surface redesign (noun-verb grammar, hard cutover)

- Date: 2026-08-18
- Kind: orchestrator
- Concern: Implement spec 20260818-1525-01 (command-surface redesign, RELEASE BLOCKER). Replace the mixed CLI grammar (flat `plans-*`/`plan-names` verbs + a `plans <verb>` argv-rewrite shim, alongside true noun-verb families) with ONE consistent grammar: cross-cutting VERBS (`check`/`find`/`search`/`index`/`rename`/`group`/`archive`) that take a TYPE noun (`all|plans|specs|prompts|research|backlog|walkthroughs|roadmaps|comms`) + selectors; merge `aw plans` into `aw ipd`; `aw list`->`aw list-repos`; `aw todo`->alias of `aw attention`. HARD CUTOVER: old verbs removed, all in-repo references updated. Addresses TODO items 5,9,19,22,24,25,26,27,28,32.
- Scope: The CLI parser/dispatch (agent_workflows/cli.py) + reference updates across shipped docs/tests. IN: new verb parsers routing into EXISTING backends (plans_index/plans_refs/plans_archive/research_index/research_refs/research_archive/specs/backlog/normalize_plan_names); removal of old verbs + the argv shim; the plans->ipd merge; list-repos + todo alias; --json/exit-code consistency; updating every in-repo reference. OUT: the `check` ENGINE internals (Set D / awcheck), the selector-grammar internals (Set E / awselect), color/pretty (Set C), help-text quality (Set B) - this Set fixes the GRAMMAR + routing and depends on Set D for `check`'s engine and Set E for the selector parser (see dependencies).
- Status: reviewed
- Set: awcmdsurf
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: mvz3d2

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): built from spec 20260818-1525-01 + a code-grounded cli.py investigation (flat dispatch chain cli.py:4018-4241; plans argv shim cli.py:4023-4031; backends mapped).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified against spec 20260818-1525-01 and cli.py:4018-4031; multi-order sequencing and dependency layering sound; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE; re-review (opencode): verified spec + dispatch chain 4018/argv shim 4023; sequencing sound; conforming; no findings.

## Goal

Deliver ONE consistent `aw` command grammar per spec 20260818-1525-01, sequenced so every intermediate
state stays runnable: first stand up the shared TYPE-noun vocabulary + selector plumbing and the new
verb parsers dispatching into existing backends, then merge plans into ipd + rename list/todo, then do
the hard-cutover removal of old verbs and sweep every in-repo reference. The `check` verb's ENGINE
comes from the awcheck Set (D) and the selector parser from the awselect Set (E); this Set owns the
grammar, the parsers, the routing, and the reference sweep.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..05 through the IPD lifecycle in dependency order (author -> /plan-review -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing. Coordinate the cross-Set dependency: Order 02's `check` routing needs the awcheck engine (Set D) and the verbs need the awselect selector parser (Set E); sequence so those land first or stub cleanly. On completion, confirm the full new grammar works and no removed verb survives anywhere in-repo.
  - Depends on: none
  - Expected outcome: Orders 01..05 executed; new grammar in force; old verbs gone; full suite + all --check green; spec 20260818-1525-01 advanced to implemented.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Split by layer so each intermediate state is runnable (new verbs added alongside old, old removed LAST):

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | (to scaffold) awcmdsurf-parser-and-type-vocab | Add the shared TYPE-noun vocabulary (`all|plans|specs|prompts|research|backlog|walkthroughs|roadmaps|comms` + singular aliases) as a module constant + a resolver mapping each type to its backend module; add the top-level subparser scaffolding for the seven cross-cutting verbs (parsers only, dispatching to thin routers). No old verb removed yet. + tests. | none (Set E awselect provides the selector parser; may land first or this Order stubs a minimal selector) |
| 02 | (to scaffold) awcmdsurf-read-verbs | Implement `aw find <type> <selector...>`, `aw search <type> <regex>`, `aw index <type> [--check]` routing into plans_index/research_index (+ specs/backlog where applicable). `check` routing is wired to the awcheck engine (Set D). + tests. | 01, Set D (awcheck) for `check`, Set E (awselect) for selectors |
| 03 | (to scaffold) awcmdsurf-mutation-verbs | Implement `aw rename <type> <selector...>`, `aw group <type> <selector...>`, `aw archive <type> <selector...>` routing into plans_refs/plans_archive/research_refs/research_archive, with default reference-updating + `--no-refs` + preview/`--apply`. + tests. | 01, 02 |
| 04 | (to scaffold) awcmdsurf-ipd-merge-and-renames | Merge `aw plans` (board) into `aw ipd` (bare `aw ipd`/`aw ipd board` = the board, default pending+reusable per item 8); rename `aw list`->`aw list-repos`; make `aw todo` an alias of `aw attention`. + tests. | 01 |
| 05 | (to scaffold) awcmdsurf-cutover-and-refs | HARD CUTOVER: remove old verbs (`plans`,`plans-mv`,`plans-find`,`plans-index`,`plans-set-assign`,`plans-archive`,`plan-names`) + the argv-rewrite shim (cli.py:4023-4031); sweep + update EVERY in-repo reference (shipped workflows, AGENTS.md, RELEASING.md, CONTRIBUTING.md, READMEs, tests) to the new grammar; advance spec 20260818-1525-01. + full suite. | 01,02,03,04 |

## Completion criteria (the whole Set is done only when)

- Orders 01..05 executed.
- The seven cross-cutting verbs work with the TYPE-noun grammar and route to the correct backends; `aw ipd` is the merged board+authoring noun; `aw list-repos` + `aw todo`(->attention) work.
- No removed verb survives: `grep -rn` over `.aw/system/`, `AGENTS.md`, `RELEASING.md`, `CONTRIBUTING.md`, `tests/` finds only the new grammar; argparse errors on an old verb.
- Every cross-cutting verb honors `--json`/`--agent` and returns documented exit codes (0/1/2).
- Full serial suite green; `aw check all`, `aw index all --check`, `aw attention --check`, `aw sanitize --agent` clean.
- Spec 20260818-1525-01 -> implemented.

## Cross-IPD validation

- Order 05 (removal) MUST run last; Orders 01-04 add the new grammar ALONGSIDE the old so every intermediate state is runnable and the suite stays green. Re-run the full suite after each Order.
- Cross-Set: Order 02's `check` needs the awcheck engine (Set D) and all verbs need the awselect selector parser (Set E). The orchestrator sequences awselect + awcheck before/with this Set; if executed first, Order 01 may ship a minimal internal selector to keep intermediate states runnable, replaced by awselect's.

## Deferred / out of scope (with reason)

- The `check` engine internals (name+front-matter+collision): Set D (awcheck).
- The selector-grammar internals (id6/setid/filename/status + multiple targets): Set E (awselect).
- Help-text quality: Set B (awhelp). Color/pretty: Set C (awcolor).
- Removing per-type authoring subverbs that stay (`research new`, `backlog set`, `specs set`, `ipd scaffold/lint/sync`).

## Scope check

- Over-scope: none - every Order maps to spec 20260818-1525-01 goals; engine/selector/help/color internals are explicitly delegated to Sets D/E/B/C.
- Under-scope: none - the five Orders cover the vocabulary, all seven verbs, the merge/renames, and the cutover+reference sweep; per-type authoring subverbs correctly stay.

## Required tests / validation

Per-Order V-items + the whole-Set completion criteria. E-01's verification re-runs the full serial
suite and greps the repo to prove no removed verb survives, after all Orders land.

## Open questions

### OQ-01: `aw ipd` bare = board or help? (mirrors spec 20260818-1525-01 OQ-1)

- Blocking: no
- Status: open
- Owner: maintainer (resolve at Order 04)
- Resolution or deferral rationale: Recommendation: bare `aw ipd` runs the BOARD (preserving the old `aw plans` quick-glance), `aw ipd --help` shows authoring subverbs. Non-blocking; the board is reachable either way.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all five child Orders show `Status: executed` under `.aw/records/plans/executed/`; paste the new-grammar smoke run (`aw check plans`, `aw find plans --status approved`, `aw index plans --check`, `aw rename`/`aw group`/`aw archive`/`aw search` on plans, `aw list-repos`, `aw todo`), a `grep -rn` proving no removed verb survives in `.aw/system/`/AGENTS.md/RELEASING.md/CONTRIBUTING.md/tests, the full serial suite tail, and `aw check all`/`aw index all --check`/`aw attention --check`/`aw sanitize --agent` clean; spec 20260818-1525-01 is `implemented`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: five Orders for one coherent objective (the single command grammar), split by layer (vocabulary -> read verbs -> mutation verbs -> merge/renames -> cutover+refs) so each is independently reviewable/executable and every intermediate state stays runnable (new verbs added alongside old; removal last).

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The orchestrator
(opencode Opus 4.8) drives each child Order through its own lifecycle, owns all verification + path-scoped
commits, never pushes, and moves each Order (and finally this orchestrator) to `executed/` only after
`aw ipd lint --phase pre-transition` conforms and the V-items are verified with pasted evidence. Large
mechanical Orders may be handed to Gemini via `agy` (blocking), but the orchestrator OWNS verification
and commits and never trusts a report on faith. On completion, advance spec 20260818-1525-01 to
implemented. RELEASE BLOCKER. Coordinates with Sets awselect (E) + awcheck (D).
