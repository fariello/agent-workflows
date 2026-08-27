---
id: sk94i0
created: 20260826
set: aw-cli-surface-inventory
order: 00
topic: [cli, information-architecture, naming, inventory, pre-release]
model:
kind: survey
status: intake
outcome: adopted
summary: Exhaustive named inventory of the full aw CLI surface (all ~44 verbs + subcommands, read/write + operates-on + naming smells) - ground truth for the naming/IA redesign
consumed-by: [25kzda]
---

# Full `aw` CLI surface inventory (named ground truth)

Verified against `--help` and source on 2026-08-26. This is the ACCURATE, NAMED reference. The
model-facing IA/naming prompt is a DE-NAMED projection of this (names stripped, structure + collisions
preserved) so frontier models name from first principles without anchoring on current names.

Global options on every command: `--no-color`, `--agent` (JSONL), `--json`, top-level `-V`. Exit
contract: `0` clean, `1` findings/incomplete, `2` cannot-run/usage. R = read-only, W = writes, R/W =
both (usually `--apply`/`--fix` gates the write; default preview).

## Framework lifecycle / repo-fleet management

| verb / subcommand | R/W | operates on | what it does |
|---|---|---|---|
| `install [targets...]` | W | installed framework files, host shims, AGENTS.md pointer, backups, records-backend config | Install/update framework in repo(s), idempotent; `all` = every configured repo; wizard for placement/backend/delivery; managed pointer + shims; backup/prune; `--to-aw` migrates legacy layout. Never pushes. |
| `setup` | W | user config, repo discovery, installed files | First-run wizard: search roots, discover repos, save config, optionally install. `--root` non-interactive. |
| `uninstall <target>` | W | managed pointer block, shims, scaffolded dirs | Remove framework from a repo (`--yes`/`--deep`/`--force`); preserves your content. |
| `list-repos` | R | repo registry | List configured+discovered repos and currency. |
| `status` | R | versions, config, git, attention, per-repo currency | Environment + currency summary. |
| `doctor` | R | attention + git + version drift | Read-only deep inspection aggregating all signals into one report. |
| `normalize-lanes` | W | prompts/comms quarantine lanes, nested .gitignore | Rename `local/` -> `untracked/` lanes, ensure ignore. Idempotent. |
| `migrate-layout [action]` | R/W | backend cutover, .agents->.aw, rollback journal | Transactional layout + backend migration (wizard/inventory/plan/apply/status/resume/rollback/cleanup). |
| `exclude [repos...]` | R/W | never-install exclude list | Exclude repos from management (bare = list). |
| `include [repos...]` | R/W | never-install exclude list | Re-include repos (bare = list). |
| `config exclude add/list/rm` | R/W | never-install exclude list (user config) | Manage the never-install blocklist (duplicates the top-level exclude/include). |

## Project identity & storage

| verb / subcommand | R/W | operates on | what it does |
|---|---|---|---|
| `project status` | R | project identity, AW_HOME registry | Inspect project id + registry match. |
| `project attach <id>` | W | registry | Bind repo to an existing project id. |
| `project move <id> <path>` | W | registry | Update a project's target-path association. |
| `storage status` | R | records backend, durability | Inspect records-storage backend + durability. |
| `storage init` | W | storage dir, optional git, durability | Init records storage, `git init` unless `--no-git`. |
| `storage attach/detach/move/reattach` | W | companion storage binding, durability policy | Set/bind/move/rebind companion storage + durability. |
| `storage preflight --companion-dir` | R | companion dir identity/reachability | Preflight checks before attach/move. |
| `context` | R | resolved AW project context | Print project id/mode/AW_HOME/backend/durability/hosts/roots; `--public` redacts. |
| `path {system\|config\|state\|records}` | R | logical-root -> physical path | Print a logical root's filesystem path; `--agent` = path only. |

## IPD / plan tooling (`ipd`; plans under .aw/records/plans/)

| subcommand | R/W | operates on | what it does |
|---|---|---|---|
| `ipd board` (bare `ipd`) | R | plans tree | IPD readiness board; `--status` filters disposition. |
| `ipd lint [path]` | R | a plan file | Deterministic STRUCTURAL/STATE lint at a `--phase` (author/review-finalize/pre-execution/pre-transition/post-transition). No semantics. |
| `ipd scaffold` | R/W | new plan file | Write a conformant IPD skeleton; derive canonical name; preview unless `--apply`. |
| `ipd sync <path>` | R/W | a plan file | Assign ids to E-NEW leaves, append V skeletons (E/V bijection), advance watermark. |
| `ipd execute-set <set>` | R | approved Set -> manifest | Compile a Set into a validated dep graph + manifest; `--plan-only` only in this build (no execution). |
| `ipd set <status> <sel>` | W | plans status+disposition dir, history, git | Transition plan status/whole set; plan->executed delegates to finalize; `--blocks-release`/`--from-backlog`/`--by-human`. |
| `ipd begin <plan> --actor` | W (local, gitignored) | .aw/state/ipd-lifecycle/<id6>.receipt.json | Fail-closed execution start: pre-execution lint, freeze requirements+Scope-Paths+base HEAD into a local receipt = execution authority. |
| `ipd finalize <plan> --actor` | R/W | plans tree, index, git commit, history | Atomic terminal transition: validate begin receipt, pre-transition lint, reconcile changed-vs-Scope-Paths, history, terminal status+move, path-scoped commit, post-transition lint. |

## The engine run ledger (`run`; ledger events.jsonl under .aw/state/runs/ -> .aw/records/runs/ -> .aw/runs/)

NOTE: top-level `run` help claims "Read-only; makes no writes" but the parser also registers mutating subcommands - an inaccuracy (run_cli.py:193-196 resolution; :1136 stale "read-only" comment).

| subcommand | R/W | operates on | what it does |
|---|---|---|---|
| `run show <target>` | R | run ledger | Inspect run state/steps/verifier decisions/completion predicate. |
| `run evidence <target>` | R | ledger evidence envelopes | List+validate captured evidence/tool events/artifact refs. |
| `run verify-ledger <target>` | R | ledger hash chain | Verify SHA-256 chain, sequence, schema, evidence validity. |
| `run start <target>` | W | run ledger | Lease + transition a step pending->runnable->running. |
| `run next <target>` | R | ledger + DAG/gates | List steps whose deps + gate approvals are satisfied. |
| `run record <target>` | W | run ledger | Append a step_attempt (performed/blocked/failed). |
| `run resume <target>` | R | run ledger | Reconstruct + report resumable steps; refuse on interrupted side effect. |
| `run cancel <target>` | W | run ledger | Record a terminal cancellation. |
| `run status <target>` | R | run ledger | Reconstruct + print run + per-step state. |
| `run finalize <target>` | W | run ledger | Completion predicate + record terminal completion (coordinator only). |
| `run decisions/questions <target>` | R | workflow-artifacts projection | Print a Set run's recorded decisions / open questions. |

## Host runners (`oc`/`opencode`, `agy`/`antigravity`; a SECOND run store: .aw/records/runs/<run-id>/ state.json)

`oc runipd` (alias `run`); `agy runipd` (aliases `run`, `runagy`). Both expose the same 4 sub-subcommands. This is the ACTUAL "execute a plan" command.

| subcommand | R/W | operates on | what it does |
|---|---|---|---|
| `<host> run start <selectors>` | W (spawns model CLI + writes run state) | host-runner run dir; source IPDs; git (via child) | Durable queue of IPDs; auto-routes by status (to-review->/plan-review; approved->execute step-by-step); `--full-auto`/`--no-verify`/`--model`/`--session`/`--run-id`/etc. |
| `<host> run resume <run_id>` | W | run dir | Resume interrupted run; `--retry-incomplete` recovery. |
| `<host> run status <run_id>` | R | state.json | Inspect queue positions/attempts/statuses. |
| `<host> run report <run_id>` | R/W | execution-report.md | Rebuild the report, print its path. |

agy extras: `--effort`, per-turn `--timeout`, `--dangerous` (default on), `--new-session`, turn-2 clean-session self-validation.

## Type-generic artifact verbs (verb-first; `type` positional in plans/specs/prompts/research/backlog/walkthroughs/roadmaps/comms/releases/all)

| verb | R/W | operates on | what it does |
|---|---|---|---|
| `find [type] [sel]` | R | artifact index/tree | Find by selector (id6/status/Set/fragment), or across all types. |
| `search [type] [sel]` | R | file contents | Regex content search across a type/all. |
| `index <type> [sel]` | R/W | the type's manifest | Rebuild+print manifest; `--check` = fail on drift. |
| `check <type> [sel]` | R | the type's contract | Validate against contract; `check all` = every tree. |
| `rename <type> [sel]` | R/W | filename + citing docs | Rename/move an artifact, rewrite refs; `--no-refs`/`--force`. |
| `group <type> [sel]` | R/W | Set assignment + filename cluster | Assign to a Set/group, re-cluster filename. |
| `set [type] <status> <sel>` | W | plan/spec/prompt/backlog status+dir, history, git | Transition lifecycle status across types/whole set; plan->executed delegates to ipd finalize. |
| `archive [type_or_target] [target]` | R/W | research (and plans/all) -> archive/reference shards | Deep-shelve: targeted OR age sweep (default 14d) of stale uncited research; polymorphic first positional. |

## Type-specific owner verbs

`research` (.aw/records/research/): `new`, `new-comparison`, `set-assign`, `mv`, `check-refs`, `index`, `find`, `pending`, `promote`, `set-outcome`, `check-miscategorized` - create/regroup/index/curate research docs + outcome/consumed-by provenance.

`backlog` (.aw/records/backlog/): `new`, `set <status>`, `check` - create item / transition status (blocked needs typed gate; done can carry `--evidence`) / validate tree.

`specs` (alias `spec`; .aw/records/specs/): `set <status>`, `note`, `check`, `migrate` - transition (legal table + anti-self-approval + typed gates), append history note, validate, first-normalize legacy status.

## Records / history / actions inspection

| verb | R/W | operates on | what it does |
|---|---|---|---|
| `show <ref>` | R | records artifacts, then action ledger | Inspect a record OR an operational action (silent fallback across stores). |
| `record-history <id6>` | R | .aw/records/history.jsonl sidecar | Print an artifact's chronological workflow history (READ-only despite imperative name). |
| `todo` | R | operational action ledger | List open operational actions; `--all` includes done/dismissed. |
| `attention` (alias `att`) | R | every tracked .aw/ records tree | Cross-tree ready/active/blocked/done/parked view; `--check` fails closed; `--all`/`--long`. |

## Workflow authoring / compilation (`workflow`)

`workflow validate` (R, schema-validate a canonical package), `workflow compile` (R/W, source -> `_generated/` projections, preview unless `--apply`), `workflow check-generated` (R, drift gate).

## Security / leak sanitization

`check-local-leaks` (alias `sanitize`) `[dir]` - R/W: detect (and `--fix` rewrite home paths to `~`) identifying info in public artifacts; `--history`/`--wheel`/`--staged`/`--warn`/`--configure`. Nonzero on fail.

## Local pre-commit gate shims (invoked by hooks, not by hand)

`ipd-executed-gate` (dulzpy): refuse raw plan->executed commit without finalize evidence. `ipd-status-untooled-gate` (79li67): flag untooled intermediate plan status change. `backlog-blocking-close-gate` (f1dhht, opt-in): refuse committing a release-blocking backlog done without preserved gate. All local best-effort (`--no-verify` bypasses; `aw check`/CI is the backstop).

---

## Naming smells / observations (for the IA redesign)

1. **`run` doesn't run, and its help is a lie.** Top-level `run` says "Read-only; makes no writes" + advertises only show/evidence/verify-ledger, but registers mutating start/record/cancel/finalize. The real "execute a plan" action lives under `oc/agy ... run start`. Two contradictory meanings of "run" ship at once.
2. **Two different "run" stores collide under one word.** (a) engine ledger `events.jsonl` via `aw run *`; (b) host-runner dirs `.aw/records/runs/<run-id>/` via `oc/agy runipd`. Both "runs", both have a `status`, both use `run-<...>` ids; distinct lifecycles/schemas.
3. **`status` at three levels, three meanings:** `aw status` (env/currency), `aw run status` (engine ledger), `oc/agy runipd status` (host queue); plus `project status`/`storage status`. Five, no shared contract.
4. **`show` collision:** top-level `show` (records artifacts -> action ledger, silent fallback) vs `run show` (run ledger). Same verb, unrelated stores.
5. **"History" split three ways:** `record-history` (history.jsonl per-artifact), the run ledger events.jsonl, and in-file `## Workflow history`. `record-history` sounds like a writer but is read-only.
6. **Type-generic vs type-specific = two-axis grammar with duplicate doors.** Generic verb-first (find/search/index/check/rename/group/set/archive) vs specific noun-first (ipd/backlog/specs/research). Same op reachable two ways: `set` vs `ipd/backlog/specs set`; `check plans` vs `ipd lint`/`backlog check`/`specs check`; `index plans` vs `research index`; `find` vs `research find`. Unpredictable which door.
7. **`check` overloaded across >=8 surfaces:** `check <type>`, `backlog check`, `specs check`, `research check-refs`/`check-miscategorized`, `workflow check-generated`, `attention --check`, `index --check`, `doctor`. No single validate entry point.
8. **Three doors to one transition:** `set approved` vs `ipd set approved` vs (plan->executed) `ipd finalize`; `--actor` silently ignored some places, mandatory others.
9. **Kick-off synonyms:** `ipd begin` + `ipd finalize` vs `run start` + `run finalize` vs `oc start`; begin/start/(implicit) = three words for "start."
10. **`config` near-empty:** only wraps `config exclude`, which duplicates top-level exclude/include - three surfaces for one blocklist.
11. **`archive` irregular polymorphic positional** breaks the uniform `<verb> <type> <selector>` shape.
12. **Host-runner alias inconsistency:** `oc runipd`=`run`; `agy runipd`=`run`+`runagy`; runagy/runipd distinction cosmetic (same 4 subcommands) - argues for dropping the sub-name: `oc <start|resume|status|report>`.
13. **Move/rename verbs scattered:** normalize-lanes, migrate-layout, specs migrate, research mv, rename, group, research set-assign, project move, storage move - no shared vocabulary.
14. **Tense doesn't signal read vs write:** read-only verbs sound imperative (`record-history`, `check-refs`); some writers preview by default (`new`, `scaffold`, `set-outcome`). No convention encodes "this writes."
15. **`todo` vs `attention` vs `backlog` overlap:** "what should I do next?" has three plausible commands at different scopes (operational actions vs cross-tree records view vs the backlog tier).
