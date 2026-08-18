# Spec: `aw` command-surface redesign (noun-verb grammar, hard cutover)

- Date: 2026-08-18
- Status: draft
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: The `aw` CLI surface grew organically into a MIX of two grammars: true noun-verb subparser families (`ipd`, `research`, `specs`, `backlog`, `storage`, `project`) and flat hyphenated verbs (`plans-mv`, `plans-find`, `plans-index`, `plans-archive`, `plans-set-assign`, `plan-names`, `check-local-leaks`). Only `plans <verb>` fakes noun-verb via an argv rewrite (cli.py:4023-4031). This is inconsistent, hard to learn, and hard to extend. The maintainer wants ONE consistent grammar where cross-cutting operations (check, find, search, index, rename, group, archive) are VERBS that take an artifact-TYPE noun (`all|plans|specs|prompts|research|backlog|...`) plus selectors, and where per-artifact tooling is unified. Addresses TODO items 5, 9, 19, 22, 24, 25, 26, 27, 28, 32.
- Relation to prior work: BUILDS ON the uniform naming grammar (spec 20260817-2147-01, `.type.md`) and the record-class taxonomy (spec 20260817-2124-01). Consumes the existing per-type validators/indexers/finders (plans_index, research_index, specs, backlog) as the BACKENDS the new verbs dispatch into. Companion to the `aw check`/`aw doctor` validation spec (Set D) and the selectors spec (Set E) which this spec references for the shared selector grammar.
- **RELEASE BLOCKER (maintainer-confirmed 2026-08-18):** the maintainer wants the consistent surface before the first `.aw/`-layout release; agent-workflows is not yet widely used, so a HARD CUTOVER (no deprecated-alias retention) is acceptable and preferred. This spec MUST be implemented (or explicitly waived) before release.

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8): authored from the maintainer's 39-item pre-release TODO (tmp/todo.md) + a code-grounded CLI-surface investigation. Decisions settled interactively: full plans+ipd merge, hard cutover (no alias retention).

## 0. Decisions locked (maintainer, 2026-08-18)

- **D1. Hard cutover, no alias retention.** Old verbs (`plans-mv`, `plan-names`, `plans-index`, `plans-find`, `plans-set-assign`, `plans-archive`) are REMOVED, not kept as hidden aliases. Every in-repo doc/workflow/test referencing an old verb is updated in lockstep. Rationale: pre-release, not widely used, maintainer prefers a clean surface over back-compat.
- **D2. Full merge of the plan tooling under one noun.** `aw plans` (the readiness board) and `aw ipd` (author/lint/sync) collapse: plans ARE ipds. The board + authoring + linting live under a single noun. See Section 3 for the exact shape.
- **D3. `.ipd.md` stays** the plan filename facet (spec 20260817-2147-01 already shipped it). Not revisited.
- **D4. `aw list` -> `aw list-repos`.** `list` is too generic; the repo-listing verb is explicitly named.
- **D5. `aw todo` becomes an alias for `aw attention`** (see Set F for the attention upgrades). The operational-action ledger (`show`/`complete`/`dismiss`/`reopen`/`history`) is a SEPARATE concern (STATE/actions) and is out of scope for this rename except that `todo`'s LISTING role folds into attention.

## 1. Goals

- G1. ONE grammar: cross-cutting operations are VERBS taking a TYPE noun + selectors: `aw <verb> <type> [selector...] [flags]`.
- G2. The cross-cutting verbs: `check`, `find`, `search`, `index`, `rename`, `group`, `archive` (defined below). Each accepts a TYPE noun from a closed set and, where sensible, MULTIPLE selectors.
- G3. Per-artifact authoring/lifecycle stays under its noun (`ipd`, `specs`, `research`, `backlog`) but is made consistent; `plans` merges into `ipd` (D2).
- G4. `list` -> `list-repos`; `todo` -> alias of `attention`.
- G5. Hard cutover: old verbs removed, all in-repo references updated, full suite green.
- G6. Every new verb has a machine-readable mode (`--json` and/or `--agent`) and documented exit codes (0 ok / 1 findings / 2 cannot-run), reusing the existing `Drift`/`drift_exit_code` convention (artifact_core.py:247-266).

## 2. Non-goals

- The DETAILED behavior of `check`/`doctor` internals (name+front-matter+collision validation) is specified in the Set D spec; this spec only fixes the VERB GRAMMAR and how `aw check <type>` routes.
- The selector grammar's full semantics (id6/setid/filename/status/multiple targets) is specified in the Set E spec; this spec references it and defines the shared TYPE-noun vocabulary.
- Color/pretty output is Set C.
- The operational action ledger (`show`/`complete`/`dismiss`/`reopen`/`history`) internals.
- Removing the per-type subverbs that make sense to keep (e.g. `research new`, `backlog set`, `specs set`).

## 3. The target grammar (normative)

### 3.1 TYPE nouns (closed set)

The artifact TYPE noun used by the cross-cutting verbs:

    all | plans | specs | prompts | research | backlog | walkthroughs | roadmaps | comms

- `all` = every applicable type for that verb.
- Singular is accepted as an alias of plural (`plan`==`plans`, `spec`==`specs`, etc.) for ergonomics.
- Not every verb supports every type (e.g. `group` is meaningful for plans/specs/prompts/research that carry a Set; `search` applies to all). Each verb documents its supported subset; an unsupported (type, verb) pair errors with exit 2 and a clear message.

### 3.2 Cross-cutting verbs (normative behavior)

| Verb | Grammar | Replaces | Behavior |
|---|---|---|---|
| `check` | `aw check <type> [names] [selector...] [--legacy] [--json\|--agent]` | `plan-names`, `specs check`, `backlog check`, `plans index --check`, `research index --check` | Validate the type(s). With the literal sub-token `names`, check ONLY filename-grammar conformity; without it, check names AND front-matter/status/reference conformity. `all` checks every type. Detailed rules in the Set D spec. Exit 0 clean / 1 findings / 2 cannot-run. |
| `find` | `aw find <type> <selector...> [--status S] [--set S] [--dir D]` | `plans-find`, `research find` | Query the manifest(s) by id6/setid/partial-filename/status. Multiple selectors allowed (OR). |
| `search` | `aw search <type> <regex> [--dir D]` | (new) | Search WITHIN file contents for a regex; report matching files+lines. |
| `index` | `aw index <type> [--check] [--limit N] [--agent]` | `plans-index`, `research index` | Regenerate the manifest(s) (INDEX.json/INDEX.md); `--check` fails on drift. |
| `rename` | `aw rename <type> <selector...> [--slug S] [--order N] [--set S] [--no-refs] [--apply]` | `plans-mv`, `research mv` | Rename/re-slug the selected artifact(s) to the grammar, keeping Id. BY DEFAULT updates all references across the repo; `--no-refs` disables. Preview by default, `--apply` to write. |
| `group` | `aw group <type> <selector...> --set S [--order N] [--no-refs] [--apply]` | `plans-set-assign` | Assign the selected artifacts into a Set (Set/Order metadata); like rename, updates references by default. Preview/`--apply`. |
| `archive` | `aw archive <type> <selector...> [--apply]` | `plans-archive`, top-level `archive` (research) | Deep-shelve terminal/aged artifacts into shards. `all`/`plans`/`research`/etc. Preview/`--apply`. |

### 3.3 The plans+ipd merge (D2)

- The noun `ipd` becomes the home for BOTH the board and authoring:
  - `aw ipd` (no subcommand) OR `aw ipd board` = the readiness board currently at `aw plans` (grouped-by-lifecycle Status view). Default shows pending + reusable only (TODO item 8; confirmed in the Set F/standalone work).
  - `aw ipd lint` / `aw ipd scaffold` / `aw ipd sync` = unchanged authoring verbs.
- `aw plans` is REMOVED as a distinct noun; the cross-cutting operations on plans go through the verbs with the `plans` type noun (`aw check plans`, `aw find plans`, `aw index plans`, `aw rename plans`, `aw group plans`, `aw archive plans`).
- Rationale: a plan IS an IPD; two nouns for one artifact was the confusion item #9 flagged.

### 3.4 Renamed simple verbs

- `aw list` -> `aw list-repos` (D4). (No `aw list <x>` namespace; it is a single verb `list-repos`.)
- `aw todo` -> alias of `aw attention` (D5): `aw todo` runs the attention board. The action-ledger listing that `todo` used to do is folded into attention's scan of the STATE/actions tree (attention already scans actions: attention.py:166-209).

## 4. Requirements

- R1. Implement the seven cross-cutting verbs (Section 3.2) as true subcommands dispatching into the existing backends (plans_index, research_index, specs, backlog, plans_refs, plans_archive, research_archive, normalize_plan_names, and the new check engine from Set D).
- R2. Remove the old flat verbs (`plans`, `plans-mv`, `plans-find`, `plans-index`, `plans-set-assign`, `plans-archive`, `plan-names`) and the `plans <verb>` argv-rewrite shim (cli.py:4023-4031). Keep `ipd` (with the merged board) + `research`/`specs`/`backlog` authoring subverbs.
- R3. `aw list-repos` (rename of `list`); `aw todo` -> attention alias.
- R4. Every cross-cutting verb: `--json` (structured) where a machine consumer benefits, documented exit codes (0/1/2), reuse `drift_exit_code`.
- R5. Update EVERY in-repo reference to a removed verb: shipped workflow bodies under `.aw/system/workflows/`, `AGENTS.md`, `RELEASING.md`, `CONTRIBUTING.md`, READMEs, tests, and the assess/release-review/plan-review workflow docs. Hard cutover (D1) - no old verb may survive except as the new grammar.
- R6. `aw --help` lists the new grammar cleanly (the TYPE-noun verbs grouped/legible). Full help text quality is Set B, but the verb list must be correct here.
- R7. Backends stay where they are; this is a ROUTING/parser change plus reference updates, not a rewrite of validators/indexers.

## 5. Testable acceptance criteria

- AC1. `aw check plans`, `aw find plans --status approved`, `aw index plans --check`, `aw rename plans <id6> --slug x --apply`, `aw group plans <id6...> --set s --apply`, `aw archive plans <id6> --apply`, `aw search plans "<regex>"` all work and route to the correct backend.
- AC2. The removed verbs (`plans-mv` etc.) no longer exist (argparse errors), and `aw plans` is gone (the board is `aw ipd`/`aw ipd board`).
- AC3. `aw list-repos` works; `aw list` is gone. `aw todo` shows the attention board.
- AC4. `grep -rn` over `.aw/system/`, `AGENTS.md`, `RELEASING.md`, `CONTRIBUTING.md`, tests finds NO reference to a removed verb (each is the new grammar).
- AC5. Every cross-cutting verb honors `--json`/`--agent` and returns 0/1/2 per the convention.
- AC6. Full serial suite green; `aw check all`, `aw index all --check`, `aw attention --check`, `aw sanitize --agent` all clean.

## 6. Open questions

### OQ-1: `aw ipd` bare = board, or require `aw ipd board`?

- Blocking: no
- Status: open
- Owner: maintainer (resolve at Set A orchestrator authoring)
- Resolution or deferral rationale: `aw ipd` with no subcommand could either print help (current ipd behavior) or run the board. Recommendation: `aw ipd` with no subcommand runs the BOARD (the most common read), and `aw ipd --help` shows the authoring subverbs; this preserves the "quick glance" ergonomics of the old `aw plans`. Non-blocking: the board is reachable either way.

### OQ-2: does `search` scan file BODIES only, or also names/front-matter?

- Blocking: no
- Status: open
- Owner: opencode (resolve at the search child IPD)
- Resolution or deferral rationale: Recommendation: `aw search <type> <regex>` matches the regex against the full file TEXT (body + front-matter) and reports `path:line`. `find` remains the metadata-field query; `search` is the free-text grep. Non-blocking.
