# IPD: read verbs find search index

- Date: 2026-08-18
- Kind: child
- Concern: awcmdsurf Order 02 (spec 20260818-1525-01). Implement the read-only cross-cutting verbs on the Order-01 scaffolding: `aw find <type> <selector...>` (manifest query), `aw search <type> <regex>` (in-file grep), `aw index <type> [--check]` (regenerate/verify manifests). `aw check <type>` ROUTING is wired here too but its ENGINE is the awcheck Set (D).
- Scope: cli.py routers + light glue into existing backends. IN: `find` -> plans_index.run_find/research_index.run_find (+ a clear "not supported" for types without a manifest finder); `index` -> plans_index.run_index/research_index.run_index; `search` -> a new small text-grep over the resolved type trees (new helper); `check` -> dispatch into the awcheck engine (Set D) or a temporary delegation to the existing per-type checks (specs.run_check/backlog.run_check/plans_index --check/research_index --check) until awcheck lands; `all` fans out; `--json`/`--agent`/exit codes. OUT: mutation verbs (Order 03), the check ENGINE (Set D), the full selector grammar (Set E; Order 02 uses the minimal selector from Order 01), removals (Order 05).
- Status: approved
- Approval: 2026-08-18, human ("Approve ALL 21 IPDs now ... Execute everything one at a time using Gemini ... then do it yourself.") after /plan-review (rigorous, opencode Opus 4.8; APPROVE / APPROVE WITH REVISIONS APPLIED).
- Set: awcmdsurf
- Order: 2
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: vaghnb

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from spec 20260818-1525-01 + investigation (find/index backends: plans_index.py:317/346, research_index.py:276/307; per-type checks: specs.py:296, backlog.py:442).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against plans_index.py:317/346, research_index.py:276/307, specs.py:296, and backlog.py:442; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE WITH REVISIONS APPLIED; re-review (opencode): PR-002 fixed - `_run_check` must set check=True when delegating to run_index (getattr-gated at plans_index.py:318). Conforming.
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. PR-001 (MEDIUM): E-03 `search_type` resolved dirs via `resolve_record_read_paths(<class>)`, which RAISES for backlog/roadmaps (not RecordClass members), so `aw search all` (spans every type) would CRASH - same root cause fixed in awcheck-01/02; made E-03 resolve dirs defensively (try/except + `.aw/records/<type>` fallback + legacy `.agents/<type>`) with resolved-path de-dup. (Prior passes checked the find/index backends but not the search-all dir resolution.) Conforms at review-finalize. GO - PENDING HUMAN APPROVAL.

## Goal

Make the read verbs real: `find`/`search`/`index` operate over one type or `all`, routing into the
existing manifest finders/indexers and a new text-grep, honoring `--json`/`--agent` and the 0/1/2 exit
convention. Wire `check`'s routing to the awcheck engine (Set D), delegating to the existing per-type
checks in the interim so the verb is usable before awcheck fully lands.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: index + find

- [ ] E-01 Implement `_run_index(args, term)`: for the resolved type(s), call the backend `index` entrypoint (`plans_index.run_index` cli-lazy import; `research_index.run_index`), passing through `--check`/`--limit`/`--agent`. `all` fans out over every type that HAS an index backend (plans, research) and aggregates exit codes (max: any 1 -> 1, any 2 -> 2). A type without an index backend prints a clear "index not supported for <type>" and does not fail `all`.
  - Depends on: none
  - Expected outcome: `aw index plans --check` == the old `aw plans-index --check`; `aw index research --check` == old `aw research index --check`; `aw index all --check` runs both and aggregates.
  - Execution state: pending
- [ ] E-02 Implement `_run_find(args, term)`: for the resolved type(s), call the backend `find` entrypoint (`plans_index.run_find`, `research_index.run_find`) passing the selector(s) + `--status`/`--set`/`--dir`. Multiple selectors are OR-ed. `all` fans out; a type with no finder reports "find not supported for <type>".
  - Depends on: none
  - Expected outcome: `aw find plans --status approved` == old `aw plans-find --status approved`; `aw find research --id <id6>` works; multiple selectors OR.
  - Execution state: pending

### Task group 2: search

- [ ] E-03 Implement `_run_search(args, term)` + a helper `search_type(repo_root, type, regex)`: resolve the type's record tree(s), walk `*.md` (facets like `.ipd.md` already match `*.md`), and report every `path:line` whose text matches the compiled `regex` (Python `re`). CRITICAL: `record_producers.resolve_record_read_paths` RAISES `Invalid record or state class` for `backlog` and `roadmaps` (they are NOT RecordClass members - verified), so a naive `resolve_record_read_paths(<class>)` makes `aw search all` (which spans every type) CRASH. Resolve dirs defensively: `try: dirs = resolve_record_read_paths(type, target_repo=str(repo_root)) except Exception: dirs = [repo_root/".aw/records"/type]` and additionally include `repo_root/".agents"/type` if it exists (covers backlog/roadmaps/legacy). Keep only existing dirs; de-dup by resolved path. `all` searches every type's tree. Output plain (`path:line: matchtext`) or `--json` (list of `{path,line,text}`). Read-only; no writes.
  - Depends on: none
  - Expected outcome: `aw search plans "release blocker"` lists matching plan files + line numbers; `aw search all "<regex>"` spans all trees INCLUDING backlog/roadmaps WITHOUT crashing; an invalid regex errors with exit 2.
  - Execution state: pending

### Task group 3: check routing (engine is Set D)

- [ ] E-04 Implement `_run_check(args, term)` routing: parse the optional literal sub-token `names` (from the selector list); resolve type(s); dispatch to the awcheck engine if present, ELSE (interim) delegate per type to the existing checks - `specs.run_check`, `backlog.run_check`, `plans_index.run_index`, `research_index.run_index` - and for `names` delegate to the normalize_plan_names conformance path. NOTE: `plans_index.run_index`/`research_index.run_index` gate on `getattr(args, "check", False)` (plans_index.py:318), so when delegating to them for a CHECK the router MUST pass an args namespace with `check=True` set (build a shallow copy/SimpleNamespace with `check=True`, plus `dir`/`agent`/`limit` passed through) - do not rely on the caller's args carrying it. Aggregate exit codes. Document (code comment + help) that the unified engine is Set D and this is the routing layer.
  - Depends on: none
  - Expected outcome: `aw check specs` == old `aw specs check`; `aw check backlog` == old `aw backlog check`; `aw check plans names` runs name conformance; `aw check all` fans out; exit codes aggregate.
  - Execution state: pending

### Task group 4: tests

- [ ] E-05 Add `tests/test_awcmdsurf_read_verbs.py` covering `index`/`find`/`search`/`check` over a fixture repo (single type + `all` + an unsupported (type,verb) message), exit-code aggregation, `--json` shape for search, and parity with the old verbs (`aw index plans --check` matches `aw plans-index --check` behavior while both still exist). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: new module passes; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Find/index backends: `plans_index.run_index` (plans_index.py:317), `plans_index.run_find` (:346), `research_index.run_index` (research_index.py:276), `research_index.run_find` (:307). Per-type checks: `specs.run_check` (specs.py:296), `backlog.run_check` (backlog.py:442). Name conformance: `normalize_plan_names` via `_run_plan_names` (cli.py:2920).
- Tree resolution for search: `record_producers.resolve_record_read_paths(<class>)` (record_producers.py:597) returns `[primary, legacy]`.
- Exit convention: reuse `artifact_core.drift_exit_code` (artifact_core.py:262); aggregate over `all` by taking the max severity.
- The minimal `selector nargs="*"` from Order 01 is what E-02/E-04 parse; the full grammar (id6/setid/filename/status/multiple) is Set E (awselect) and will slot into the same positional.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Backends already implement find/index per type. | `index`/`find` are thin fan-out routers, not rewrites. |
| F2 | No text-search exists anywhere. | `search` is genuinely new (a small `re`-based walker); the only net-new behavior in this Order. |
| F3 | The check ENGINE is Set D. | `check` here is ROUTING with an interim delegation so it works before awcheck lands; awcheck replaces the interim body. |
| F4 | `all` needs exit aggregation. | Define once (max severity) and reuse across all read verbs. |
| F5 | `resolve_record_read_paths` RAISES for backlog/roadmaps (not RecordClass members). | `search_type` (which `all` runs over every type) must resolve dirs defensively (try/except + `.aw/records/<type>` fallback), or `aw search all` crashes. Verified empirically. |

## Proposed changes (ordered, validatable)

1. `_run_index` fan-out (E-01). 2. `_run_find` fan-out (E-02). 3. `_run_search` + walker (E-03). 4. `_run_check` routing + interim delegation (E-04). 5. Tests + suite (E-05).

## Deferred / out of scope (with reason)

- Mutation verbs: Order 03. ipd merge/renames: Order 04. Removals: Order 05.
- The unified check engine (name+front-matter+collision): Set D (awcheck); `check` here only routes.
- Full selector grammar: Set E (awselect).

## Scope check

- Over-scope: none - only the read verbs + check routing.
- Under-scope: none - find/search/index fully functional; check routes correctly with a working interim engine.

## Required tests / validation

`tests/test_awcmdsurf_read_verbs.py` (E-05) + full serial suite. Each V-item pins one E.

## Spec / documentation sync

No AGENTS.md change here (grammar documented at Order 05). Spec stays draft.

## Open questions

### OQ-01: does `check` interim-delegate, or hard-depend on awcheck landing first?

- Blocking: no
- Status: open
- Owner: opencode (resolve via Set sequencing)
- Resolution or deferral rationale: Recommendation: interim-delegate to the existing per-type checks so `aw check` works the moment this Order lands, and swap to the awcheck engine when Set D lands (a one-line router change). Keeps intermediate states runnable. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw index plans --check`, `aw index research --check`, `aw index all --check` runs + exit codes; show parity with the old `plans-index`/`research index`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans --status approved` and a multi-selector find; show parity with old `plans-find`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `aw search plans "<regex>"` (path:line hits), `aw search all "<regex>"`, `--json` shape, and an invalid-regex exit-2.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `aw check specs`/`aw check backlog`/`aw check plans names`/`aw check all` with aggregated exit codes; parity with old per-type checks.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the full serial suite tail showing the new module + no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification + commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions only after
`aw ipd lint --phase pre-transition` conforms and every V is `pass`. Order 02 of awcmdsurf; depends on 01.
