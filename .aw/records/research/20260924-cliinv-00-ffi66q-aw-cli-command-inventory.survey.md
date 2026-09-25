---
id: ffi66q
created: 20260924
set: cliinv
order: 00
topic: [cli, naming, inventory]
model:
kind: survey
status: todo
outcome: none-yet
summary: Every aw command, subcommand and sub-subcommand with what it does, generated from the live parser, as input to the CLI naming review
consumed-by: []
---

# `aw` command inventory (2026-09-24)

Every `aw` command, subcommand, and sub-subcommand currently shipped, with what it does. It is the
input to a whole-CLI naming review (the trigger: `aw ipd scaffold` is jargon and is the only create
verb not spelled `new`; the maintainer's proposed direction is a verb-first `aw new <type>`).

This supersedes the 2026-08-26 inventory `sk94i0` as the current ground truth. That one is a month
stale (for example it predates `aw adopt`, `aw integration-lock`, `aw graduation`, the analytics
verbs, and `aw next`).

## How this list was produced (and how to regenerate it)

There is no single built-in "list every command" view. `aw --help` shows level 1 only, and
`aw <command> --help` shows one level at a time. This table was produced by walking the live argparse
tree (`agent_workflows.cli._build_parser()`), which yields 155 entries (56 commands, 89 subcommands,
10 sub-subcommands), and then adding the three places the walk cannot see:

1. **Commands intercepted before the parser.** `aw runs repair` is routed by hand in `cli.main`
   (`agent_workflows/cli.py:12995`) and is absent from the parser tree.
2. **Forwarded drivers.** `aw oc runipd`, `aw agy runipd`, `aw agy sessions|view|exec`, and
   `aw pwatch` forward everything verbatim to a separate parser (`oc_runipd.build_parser`,
   `agy_runipd.build_parser`, ...). Their own subcommands are listed here as level 3.
3. **Positional action words.** Some commands take a fixed-choice positional that behaves like a
   subcommand (`aw migrate-layout <action>`, `aw completion <shell|install|uninstall>`,
   `aw path <root>`, `aw runs query <view>`) or a TYPE word (`aw check|find|search|index|rename|group
   <type>`, `aw archive <type>`, `aw set [type] <status>`). These are listed in their own table so
   the naming review can see the whole grammar.

Regenerate the parser part with:

```sh
python3 - <<'EOF'
import argparse
from agent_workflows import cli
def walk(p, path):
    for a in p._actions:
        if isinstance(a, argparse._SubParsersAction):
            helps = {c.dest: c.help for c in a._choices_actions}
            seen = set()
            for name, sp in a.choices.items():
                if id(sp) in seen or name == "__complete":
                    continue
                seen.add(id(sp))
                print("aw " + " ".join(path + [name]), "|", helps.get(name, ""))
                walk(sp, path + [name])
walk(cli._build_parser(), [])
EOF
```

**Conventions.** Every command accepts `--no-color`, `--color`, `--agent` (aw.agent/v1 JSONL, also
automatic when piped), and `--json`. Exit codes are `0` clean, `1` findings, `2` cannot-run, unless a
row says otherwise. "Preview" means the command writes nothing without `--apply`. The **R/W** column
is `R` read-only, `W` writes, `R/W` previews by default and writes with a flag.

---

## 1. Framework install and repository management

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw install [targets...]` | | W | Installs or updates the framework in one or more repositories (idempotent, safe to re-run). With no target it acts on the current directory; `aw install all` does every configured or discovered repo. Runs the policy wizard (placement, delivery mode, records backend), writes the managed `AGENTS.md` block and host shims, creates the canonical `.aw/` layout, backs up before overwriting unless `--no-backup`, and prunes old backups unless `--no-prune`. `--to-aw` migrates a legacy `.agents/` layout. Skips repos on the never-install exclude list. Never pushes. |
| `aw setup` | | W | First-run guided wizard. Asks for search roots, discovers git repos under them (honoring the ignore filter and the exclude list), saves the user config, and optionally installs into the repos it found. `--root` supplies roots non-interactively. |
| `aw uninstall <target>` | | W | Removes the framework from a repo: the managed `AGENTS.md` block, host shims, and scaffolded directories. Asks first unless `--yes`; `--deep` also removes framework-owned config and state. Preserves your own content. |
| `aw list-repos` | | R | Lists configured and discovered repos with each one's install currency (current, stale, not installed). `--recursive` searches deeper. |
| `aw status` | | R | One-screen environment summary: resolved versions, config location, git working-tree state, attention summaries, and per-repo install currency. |
| `aw doctor` | | R | Deep read-only health check. Aggregates every check signal (attention-view validity, git state, installed-versus-packaged version drift, artifact naming) into one findings report. `--check-pypi` also compares against the published version. Exit 1 on findings. |
| `aw exclude [repos...]` | | R/W | Adds repos to the never-install exclude list. Bare `aw exclude` lists the current entries. Duplicates `aw config exclude add/list`. |
| `aw include [repos...]` | | R/W | Removes repos from the never-install exclude list. Bare `aw include` lists the entries. Duplicates `aw config exclude rm`. |
| `aw normalize-lanes` | | W | Renames any legacy `local/` quarantine lane under prompts or comms to `untracked/` (in both the `.aw/records/` and legacy `.agents/` layouts), keeping contents and ensuring the lane stays gitignored. Idempotent. |
| `aw migrate-layout [action]` | | R/W | Transactional migration of the on-disk layout (legacy `.agents/` to `.aw/`) and of the records storage backend, with a rollback journal. The action words are listed in section 12. `--target-backend repository\|companion\|home`, `--leftovers keep\|remove\|defer`, `--rename-to-grammar`, `--dry-run`, `--apply --confirm`. |
| `aw completion [shell]` | | R/W | Prints a shell completion script for `aw`, `agentwf`, and `agent-workflows` (`bash`, `zsh`, `fish`; detected from `$SHELL` when omitted), e.g. `source <(aw completion bash)`. The words `install` and `uninstall` manage a drop-in auto-discovery file instead. |

## 2. Configuration, project identity, and storage

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw config` | `conf` | | Parent for the user-level CLI configuration. |
| `aw config show [var]` | | R | Shows where the user config file lives, whether it exists, and every setting, or one group or variable when named. |
| `aw config get <var>` | | R | Prints one variable's value only, for scripts. Exits nonzero when unset, so "unset" differs from "empty". |
| `aw config set <var> <val>` | | W | Replaces a variable's value. Accepts `var val`, `var=val`, `var = val`, `var to val`. Replaces a whole list; use `add`/`remove` for one entry. |
| `aw config add <val> to <var>` | | W | Appends one item to a list variable. Adding an existing item is a no-op. |
| `aw config remove <val> from <var>` | `rm` | W | Removes one item from a list variable. Reports (rather than silently succeeding) when the item is absent. |
| `aw config is <val> in <var>` | | R | Membership test reported through the exit code, for shell conditionals. |
| `aw config exclude` | | | Parent for the never-install exclude blocklist (repo paths or fnmatch globs). Distinct from the discovery-only ignore filter. |
| `aw config exclude add <path>` | | W | Adds a path or glob to the exclude list; `~` is preserved; duplicates are a no-op. |
| `aw config exclude list` | | R | Lists the exclude entries. |
| `aw config exclude rm <path>` | | W | Removes a matching entry; exits nonzero when nothing matched. |
| `aw context` | | R | Shows the resolved project context: project id, delivery mode, `AW_HOME`, records backend, durability, enabled hosts, and the four logical roots (`system`, `records`, `config`, `state`). `--redact` hides local paths. |
| `aw path <root>` | | R | Prints the physical path of one logical root (`system`, `config`, `state`, `records`). With `--agent` it prints only the path, for scripting. |
| `aw layout` | | R | Prints the canonical workspace layout model: record classes (subpath, file pattern, lifecycle subdirectories, aliases), state classes, logical roots, and traversal exclusions. `--json` for the document, `--schema` for its JSON Schema. |
| `aw project` | | | Parent for project identity in the `AW_HOME` registry. |
| `aw project status` | | R | Shows this repo's project identity and whether and how it matches a registry entry. |
| `aw project attach <project_id>` | | W | Binds this repo to an existing project id so it shares that project's external roots. `--dry-run`, `--yes`. |
| `aw project move <project_id> <new_path>` | | W | Updates a project's registered path after the checkout moves or is renamed. |
| `aw storage` | | | Parent for records storage backends and durability. |
| `aw storage status` | | R | Shows the records backend, its location, and whether it is versioned. |
| `aw storage init` | | W | Initializes records storage and, unless `--no-git`, runs `git init` in it. `--acknowledge-remote` records acceptance of a remote durability policy. |
| `aw storage attach` | | W | Binds a private companion storage directory (`--companion-dir`, optionally only some `--classes`) and records the durability policy. |
| `aw storage detach` | | W | Removes the companion binding, leaving the companion directory and its contents in place. |
| `aw storage move` | | W | Points the companion binding at a relocated directory (`--new-dir`). |
| `aw storage reattach` | | W | Rebinds an existing companion repository after a clone or path change. |
| `aw storage preflight` | | R | Checks a companion directory's identity, reachability, and durability before attach or move. |

## 3. Seeing what needs attention and inspecting records

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw next [selectors...]` | `attention`, `att`, `todo` | R | The cross-tree work board. Maps every tracked artifact's native status onto `ready`, `active`, `blocked`, `done`, `parked`, and also reports any stranded lane holding unintegrated work. Filters by selector, `--status`, `--priority`, `--blocking`, `--readiness`; `--order-by depth` sequences by declared dependencies; `--all` shows done and parked; `--format json`; `--check` fails closed on an invalid view (CI gate). A selector that matches nothing is exit 2. |
| `aw show <selector>` | | R | Prints one record in full. Resolves an id6, set id, filename fragment, or status across every records tree, and falls back to the operational action ledger. |
| `aw find [type] [selector]` | | R | Lists artifacts of a type (or all types) by id6, status, Set, or filename fragment. `--paths` prints paths only. Types are listed in section 12. |
| `aw search [type] <pattern>` | | R | Regex content search across artifacts of a type (or all), grouped by file with highlighting. `-n` line numbers, `-l` files only. |
| `aw index [type]` | | W | Regenerates the gitignored manifest (`INDEX.json`, `INDEX.md`) for a type; `--check` fails on drift instead of writing. |
| `aw check [type] [selector]` | | R | Validates artifacts of a type against their contract (names, metadata, status-versus-directory, dangling links, setid length, release gates). `aw check all` is every tree; `aw check release-gates` is the release-gate rule family. Exit 1 on findings. |
| `aw record-history <id6>` | | R | Prints a record's full chronological history from the machine-local `.aw/records/history.jsonl` sidecar. |
| `aw graduation <source-id6>` | | R | Before graduating a spec or backlog item, lists every plan and spec that already names it through `From-Spec` or `From-Backlog`, with type, status, and Set. Advisory; never refuses. |
| `aw reviews` | | | Parent for the typed review records in `.aw/records/reviews/`. Read-only. |
| `aw reviews decisions [selector]` | | R | Lists the judgement calls reviewers made on their own authority instead of asking, from each review's Decisions table. `--irreversible` shows only the ones that cannot be undone. |

## 4. Creating records (current spelling)

These are the create verbs the proposed `aw new <type>` would unify.

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw ipd scaffold` | | R/W | Creates a new plan (IPD) skeleton with the correct headings, metadata, and checklists in `plans/pending/`, deriving the name from `--set` and `--order` (0 for an orchestrator, 1+ for a child; `--kind child\|orchestrator`). Requires `--title`, `--priority`, `--work-kind` unless inherited via `--from-backlog <id6>`, which also copies `Blocks-Release`. Preview; `--apply` writes. |
| `aw specs new` | `specs scaffold` | R/W | Creates a spec in `specs/draft/`, minting an id6 and naming it `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md`. `--title`, `--slug`, `--summary`. Preview; `--apply` writes. |
| `aw backlog new` | | R/W | Creates a backlog item. `--summary`, `--priority`, and `--work-kind` are required; `--status`, `--set`, `--gate-kind`/`--gate-ref` (for `blocked`), `--blocks-release`, `--body`. Preview; `--apply` writes. |
| `aw research new` | | R/W | Creates a research document with correct name and starter front matter. `--kind` (required, from a fixed vocabulary), `--slug`, `--set`, `--model`, `--topic`, `--priority`. Preview; `--apply` writes. |
| `aw research new-comparison` | | R/W | Creates a whole multi-model comparison Set at once: one prompt, one report per `--models` entry, and a reconciliation document. |
| `aw prompts new` | | R/W | Creates a staged prompt in `prompts/pending/` with its leading `<!-- aw-prompt: ... -->` metadata comment and an empty body. `--kind`, `--slug`, `--set`, `--targets`, `--concerns`. Never stages it in git. |
| `aw releases new` | | R/W | Creates a release record. `--version`, `--summary`, `--status`. |
| `aw adopt <inbox-file>` | | R/W | Files ONE raw drop from the gitignored `.aw/inbox/` into a typed tree (research today): mints an id6, derives the name, writes front matter while keeping the body verbatim, refreshes the index, then deletes the inbox original. Refuses on a leak-sanitizer failure unless `--allow-leaks`. Bulk adoption is refused. |

## 5. Changing status and organizing records

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw set [type] <status> <selectors...>` | | W | Generic status setter for plans, specs, prompts, backlog items, and releases (one artifact or a whole Set). Validates every target before writing any, moves files between status directories, and appends history. `--by-human` attests human approval; `--allow-open-questions` and `--allow-terminal-reopen` are recorded overrides; `--gate-kind`/`--gate-ref` for blocked/deferred; `--blocks-release`, `--graduated-to`; `--dry-run`. A plan moving to `executed` hands off to `aw ipd finalize` and needs `--actor`. Offers to commit its own change (`--commit`/`--no-commit`). |
| `aw rename <type> <selector>` | | R/W | Renames or re-slugs an artifact (`--slug`), rewriting every reference to it across the repo. `--to-id6` converts a legacy name to the id6 grammar. |
| `aw group <type> <selector>` | | R/W | Moves an artifact into a Set (`--set`, `--order`), re-clustering its filename while keeping its id6. |
| `aw archive [type] [target]` | | R/W | Deep-shelves artifacts into monthly shards: a targeted move, or an age-based sweep (`--age`) of stale, uncited items. Types `research`, `plans`, `all`. Preview; `--apply` moves. |

## 6. Plans (IPDs)

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw ipd` | | R | Parent for plans. Bare `aw ipd` shows the board. |
| `aw ipd board` | | R | The plan board: pending and reusable plans by default, `--status` for other dispositions. |
| `aw ipd scaffold` | | R/W | See section 4. |
| `aw ipd sync <plan>` | | R/W | Assigns stable ids to new `E-NEW` steps, appends matching `V-*` validation skeletons, and advances the watermark. Preview; `--apply` writes. |
| `aw ipd lint <plan>` | | R | Deterministic structure-and-state check at a `--phase` checkpoint (`author`, `review-finalize`, `pre-execution`, `pre-transition`, `post-transition`): heading order, E/V pairing, state legality, metadata. Proves nothing about correctness. `--all` lints every plan. |
| `aw ipd set <status> <selectors...>` | | W | The plan-only status setter (same behavior as `aw set` restricted to plans), plus `--from-backlog`, `--priority`, `--work-kind`. |
| `aw ipd recheck-readiness <selectors...>` | | R/W | Re-evaluates a stale `Readiness: no-go` whose cause has gone (blocking open question, gating finding, negative verdict). Writes only when all three are clear, and can only reach `go-pending-approval`. |
| `aw ipd dependencies` | | | Parent for a plan's cross-plan `Item-Dependencies` field (distinct from the in-plan `Depends on:` step ordering). |
| `aw ipd dependencies set <selector> <edges...>` | | W | Replaces the dependency list. Edges are `executed:<id6>`, `exists:<type>:<id6>`, `state:<type>:<status>:<id6>`, or `none`/`-` to clear. Refuses malformed, dangling, ambiguous, or cyclic edges. |
| `aw ipd dependencies remove <selector> <edges...>` | | W | Removes the named edges and keeps the rest byte-identical. Removing the last edge writes `none`. `--if-present` makes a missing edge a no-op. |
| `aw ipd begin <plan>` | | W (local) | Starts execution of an approved plan: runs the pre-execution gate, freezes requirements and `Scope-Paths`, and writes a gitignored receipt under `.aw/state/ipd-lifecycle/`. Requires `--actor`. Refuses when the plan's own paths have uncommitted changes. |
| `aw ipd finalize <plan>` | | R/W | The only path to `executed`. Checks the begin receipt, runs pre-transition lint, reconciles changed paths against `Scope-Paths` (`--scope-reason`, `--scope-ack`), writes attributed history, moves the plan, refreshes the index, makes the lifecycle commit, and runs post-transition lint. Preview; `--apply` performs it. |
| `aw ipd execute-set <set_id>` | | R | Compiles an approved Set into a dependency graph and an execution manifest and shows it. `--plan-only` only: launches nothing and grants no authority. |

## 7. Specs, backlog, research, prompts, releases (owner verbs)

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw specs` | `spec` | | Parent for specs. |
| `aw specs new` | `scaffold` | R/W | See section 4. |
| `aw specs set <status> <selectors...>` | | W | Moves a spec through its status table (`draft`, `to-review`, `reviewed`, `approved`, `implementing`, `implemented`, `deferred`, `parked`, `superseded`). Enforces legal transitions, requires a review record for `reviewed`, `--by-human` for `approved`, `--evidence` for `implemented`, and a typed gate for `deferred`. |
| `aw specs note <path>` | | W | Adds a history line without changing status. |
| `aw specs check [path]` | | R | Validates one or all specs (status enum, required sections, gate typing). |
| `aw specs migrate <path>` | | W | One-time normalization of a pre-contract free-form spec status into the bare enum. |
| `aw backlog` | | | Parent for backlog items. |
| `aw backlog new` | | R/W | See section 4. |
| `aw backlog set <status> <selectors...>` | | W | Moves an item among `open`, `graduated`, `blocked`, `parked`, `done`, and appends history. `blocked` needs a typed gate; closing a release blocker needs a handoff, `--evidence`, or `--blocks-release -`. Also updates `--priority`, `--work-kind`, `--graduated-to`. |
| `aw backlog note <item>` | | W | Adds a history line without changing status. |
| `aw backlog check` | | R | Validates the backlog tree (enums, status matches directory, gate iff blocked, unique id6, nonempty summary). |
| `aw research` | | | Parent for research documents. |
| `aw research new` | | R/W | See section 4. |
| `aw research new-comparison` | | R/W | See section 4. |
| `aw research set-assign <ids...>` | | R/W | Groups documents into one Set (shared date and set id, assigned order), keeping each id6. |
| `aw research mv <id>` | | R/W | Renames or re-slugs one document within the naming grammar (`--slug`, `--kind`, `--model`), keeping its id6. |
| `aw research promote [id]` | | R/W | Changes a document's status (`--to todo\|active\|reference\|archive`) and moves it to the right shard. `--suggest` classifies the stale hot set and previews moves. |
| `aw research set-outcome <id>` | | R/W | Records what the research was worth (`adopted`, `informational`, `rejected`, `none-yet`) and which plans or specs consumed it (`--consumed-by`). |
| `aw research set-priority <id>` | | R/W | Sets or clears (`-`) the optional Priority. |
| `aw research index` | | W | Regenerates the research manifest; `--check` fails on drift. |
| `aw research find` | | R | Queries the manifest by `--id`, `--set`, `--topic`, `--status` without reading the documents. |
| `aw research pending` | | R | Lists research prompts that never got an answer (a Set's `00` prompt with no report beside it). |
| `aw research check-refs` | | R | Reports id6 citations that no longer resolve. |
| `aw research check-miscategorized` | | R | Reports archived documents that are still cited (probably should be `reference`). |
| `aw prompts` | | | Parent for staged prompts. |
| `aw prompts new` | | R/W | See section 4. There is no `aw prompts set`; status changes go through `aw set prompts`. |
| `aw releases` | `release` | R | Parent for release records. Bare `aw releases` lists them. |
| `aw releases list` | | R | Lists every release (id6, status, version, summary). |
| `aw releases show [selector]` | | R | Shows one release (default `next`) and every live item that declares it as a blocker. |
| `aw releases new` | | R/W | See section 4. |

## 8. Doing and committing work

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw commit <plan> -- <paths>` | | W | The required commit path. Computes the plan's allowed scope, refuses if the index holds out-of-scope changes, runs the policy engine, and commits only the named paths (never `add -A`, never `--no-verify`, never push). `--no-plan -m <msg>` commits paths no plan governs. Retries once if a formatting hook rewrote a path. |
| `aw test <plan> -- <cmd>` | | W (local) | Runs a command and saves its output, exit code, and environment as evidence bound to the current git tree under the plan's local run area. Exit mirrors the command. |
| `aw finish <plan> --to <status>` | | W | Checks that the evidence from `aw test` exists and matches the current tree, then performs a non-terminal status change. Never performs `executed`. |
| `aw work` | | | Parent for workflow primitives. |
| `aw work begin <plan>` | | W | Validates the plan (fails closed) and creates an isolated git worktree with a recorded lease for executing it. |
| `aw integration-lock -- <cmd>` | | W | Holds the repository integration lock (the same one the runners take) around a publish to `main`, e.g. `aw integration-lock -- git merge --ff-only <branch>`. Waits for a live holder up to `--timeout`, then gives up. `--status` reports FREE, HELD, or UNKNOWN. |

## 9. Agent hosts and runners

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw oc` | `opencode` | | Parent for OpenCode host tooling. |
| `aw oc runipd [sub] <selector>` | `run` | W | The restartable OpenCode driver. Builds a queue from a selector (id6, setid, filename, `reviews`, `all`), reviews `to-review` plans with `/plan-review` and executes `approved` ones in isolated worktrees, commits, integrates, and records durable run state under `.aw/records/runs/`. Its own subcommands are in the next table. `as <profile>` picks a saved launch profile. |
| `aw oc review [selector]` | | W | Shorthand for `aw oc runipd <selector> --action review`; with no selector, reviews every plan awaiting review in one shared session. |
| `aw oc integrate <id6>` | | W | Shorthand for `aw oc runipd integrate <id6>`: merges a lane that finished and verified but failed to integrate, with no agent turn. Re-runs the suite and the merge gate. |
| `aw oc update-models` | `sync-models` | R/W | Refreshes model lists and per-token pricing in your OpenCode config from the gateways it declares. Preview; `--apply` writes (with a backup unless `--no-backup`). |
| `aw oc profile` | `profiles` | | Parent for named OpenCode launch profiles (a short name for a model plus variant plus agent), stored in your user-local `runner-profiles.json`. |
| `aw oc profile add [name]` | | W | Creates a profile: an interactive wizard on a TTY, or `--model ... --yes` for scripts. `--replace` to overwrite; `--set-default`. |
| `aw oc profile list` | `ls` | R | Lists profiles and which one is the default. |
| `aw oc profile show <name>` | | R | Shows a profile and the exact `opencode run` flags it expands to. |
| `aw oc profile remove <name>` | `rm` | W | Deletes a profile; deleting the default needs `--clear-default` or `--replacement`. |
| `aw oc profile default [name]` | | W | Sets (or `--clear`s) the default profile. |
| `aw agy` | `antigravity` | | Parent for Antigravity host tooling. |
| `aw agy runipd [sub] <selector>` | `run`, `runagy` | W | The restartable Antigravity driver; same queue model as `aw oc runipd`. Subcommands in the next table. |
| `aw agy review [selector]` | | W | Shorthand for `aw agy runipd <selector> --action review`. |
| `aw agy integrate <id6>` | | W | Shorthand for `aw agy runipd integrate <id6>`. |
| `aw agy exec <target>` | | W | Runs ONE target (a plan, spec, prompt file, or inline prompt) with Antigravity using a two-turn protocol, where a second clean session audits the first. Deliberately separate from the queue driver. |
| `aw agy sessions` | | R | Lists Antigravity sessions for a workspace so you can find the one a run used. Arguments are forwarded. |
| `aw agy view <log>` | `view-antigravity-jsonl` | R | Renders an Antigravity JSONL event log as readable text. |
| `aw run` | | | Parent for host-neutral dispatch and run-ledger write verbs. |
| `aw run as <profile> <selector>` | | W | Runs a plan with a named profile; the profile decides which host (OpenCode or Antigravity) runs it. |
| `aw run ipd <selector>` | | W | Runs a plan with the configured `default_runner`. Refuses when none is configured. |
| `aw run start <target>` | | W | Takes the single-writer lease on a run ledger and moves a runnable step to running. |
| `aw run record <target>` | | W | Appends a step outcome (`performed`, `blocked`, `failed`) to the append-only ledger. |
| `aw run cancel <target>` | | W | Records a terminal cancellation of a run. |
| `aw run finalize <target>` | | W | Evaluates the completion predicate and, if met, records terminal completion (coordinator only). |
| `aw runs [targets...]` | | R | Table of driver runs and each step's ending status. Filters `--last`, `--active`, `--failed`, `--set`, `--id6`, `--status`, `--since`. |
| `aw runs list` | | R | Same as bare `aw runs`. |
| `aw runs show <target>` | | R | A run's ledger, steps, verifier decisions, and completion-predicate status. |
| `aw runs status <target>` | | R | Reconstructed run and per-step state. |
| `aw runs next <target>` | | R | Steps whose dependencies and gates are satisfied (exit 3 when nothing is runnable). |
| `aw runs resume <target>` | | R | Reports resumable steps; refuses when a side effect was interrupted mid-flight. |
| `aw runs evidence <target>` | | R | Lists and validates the run's captured evidence envelopes and tool events. |
| `aw runs verify-ledger <target>` | | R | Verifies the ledger's hash chain, sequence, schema, and evidence. |
| `aw runs decisions <target>` | | R | A Set run's recorded autonomous decisions. |
| `aw runs questions <target>` | | R | A Set run's unresolved deferred questions. |
| `aw runs repair <run...>` | | W | Marks a run that was abandoned without a terminal status as ended, so it stops showing as running. Not in the parser tree (handled in `cli.main`). |
| `aw runs analyze [targets...]` | | W (local) | Updates the local analytics cache and publishes the HTML report inside the gitignored `analytics/` area. `--path`/`--list` only locate it; `--open` opens it. |
| `aw runs query [view]` | | R | Structured analytics facts and findings for agents, from an allowlisted schema (views in section 12). Bounded pages. |
| `aw runs export [targets...]` | | R/W | Builds a local, inspectable analytics bundle at a sensitivity tier (`metrics`, `events-redacted`, `raw`; `raw` needs `--by-human` and `--include`). Never transmitted. |
| `aw runs submit <bundle>` | | R | Would send a bundle to a configured endpoint; today it always refuses as unavailable because no endpoint is approved. |
| `aw host` | | | Parent for host capability inspection. |
| `aw host probe <host>` | | R | Runs the host capability probes and reports what each observed, with reasons for every not-supported result. |
| `aw host capabilities [host]` | | R | Prints the capability contract and, for each action class, whether the host would be allowed or refused. |
| `aw pwatch` | | R | Watches and summarizes running processes with include/exclude matching, for monitoring a long agent run. Never signals anything. Arguments are forwarded. |

### Runner subcommands (level 3, forwarded)

`aw oc runipd` and `aw agy runipd` share these. Both also accept `as <profile>` immediately after
`runipd`.

| Command | What it does |
|---|---|
| `aw oc\|agy runipd start <selector>` | Creates a run and executes its queue. The default when no subcommand is given, so `aw oc run <selector>` means this. Carries the full option set (model and variant, `--action`, `--full-auto`, isolation, retry budgets, stall timeout, and so on). |
| `aw oc\|agy runipd resume` | Resumes an existing run from its durable state. `--retry-incomplete` retries unfinished items. |
| `aw oc\|agy runipd status` | Shows the status of an existing run (`--json`). |
| `aw oc\|agy runipd report` | Regenerates the run's execution report and prints its path. |
| `aw oc\|agy runipd stop` | Asks a live run to stop gracefully from another terminal: `--after-call`, `--after-set`, `--now`, `--now-force`. |
| `aw oc\|agy runipd integrate <id6>` | Retries integration of an already-verified lane with no agent turn. |
| `aw oc\|agy runipd audit <plan>` | Buys one independent skeptical review of an already-executed plan in a fresh session. Cannot change the finished plan. |

## 10. Safety and leak checks

| Command | Aliases | R/W | What it does |
|---|---|---|---|
| `aw check-local-leaks [dir]` | `sanitize` | R/W | Finds machine-identifying information (home paths, usernames, hostnames, private repo names, session ids) in tracked files, `--staged` changes, `--history`, or the built `--wheel`. One tab-separated record per finding with `--agent`. `--fix` rewrites findings; `--configure` edits the rules. Exit nonzero on a fail. |

## 11. Git hook entry points (called by hooks, not usually by hand)

All are local and bypassable with `--no-verify`; `aw check` and CI are the real authority.

| Command | What it does |
|---|---|
| `aw ipd-executed-gate` | Pre-commit: refuses a commit that moves a plan to `executed` without the finalize journal proving `aw ipd finalize` did it. |
| `aw ipd-status-untooled-gate` | Pre-commit: refuses a commit that changes a plan's `- Status:` without a matching tool-written history line (a hand edit). |
| `aw backlog-blocking-close-gate` | Pre-commit (opt-in): refuses closing a release-blocking backlog item to `done` without a handoff, evidence, or de-gate. |
| `aw ipd-dependency-statement-gate` | Pre-commit (opt-in): refuses a staged plan whose `Item-Dependencies` is malformed, dangling, ambiguous, or cyclic. |
| `aw precommit-scope-gate` | Pre-commit (opt-in): refuses a commit that breaks a repository invariant or strays outside the executing plan's `Scope-Paths`, and prints the recovery command. |
| `aw prepush-authorization-gate` | Pre-push (opt-in): stops an accidental push and explains where real authorization comes from. Feedback only. |

## 12. Positional words that act like subcommands

These are not subcommands in the parser, but a naming review has to treat them as part of the
grammar.

| Command | Accepted words | Meaning |
|---|---|---|
| `aw migrate-layout <action>` | `wizard` (default), `inventory`, `plan`, `apply`, `status`, `resume`, `rollback`, `cleanup` | Guided flow; list what would move; compute the migration plan; perform it (`--apply --confirm`); show journal state; continue an interrupted migration; undo it; remove leftovers. |
| `aw completion <word>` | `bash`, `zsh`, `fish`, `install`, `uninstall` | Print the script for a shell, or install or remove the drop-in auto-discovery file. |
| `aw path <root>` | `system`, `config`, `state`, `records` | Which logical root to resolve. |
| `aw runs query <view>` | `overview`, `schema`, `metrics`, `distributions`, `slices`, `findings`, `evidence`, `data-quality`, `cache-status`, `explain` | Which analytics view to return. `schema` lists the allowed filters, groupings, metrics, and statistics. |
| `aw check\|find\|search\|index\|rename\|group <type>` | `plans`, `specs`, `backlog`, `research`, `prompts`, `walkthroughs`, `roadmaps`, `comms`, `releases`, `all`; `check` also takes `release-gates` | Which records tree to act on. Not every verb supports every type. |
| `aw archive <type>` | `research`, `plans`, `all` (or a research set id / id6 directly) | What to shelve. |
| `aw set [type] <status>` | type: `plan`/`ipd`, `spec`, `prompt`, `backlog`, `release`; status: any status of that type | Optional type scoping plus the target status. |

---

## Observations for the naming review

These are facts from the inventory, not recommendations. They are the inconsistencies a naming pass
would have to resolve.

1. **Create verbs are split across two words.** Six types use `<type> new`; plans alone use
   `ipd scaffold`, and specs still carry a `scaffold` alias. The maintainer's proposal is verb-first
   `aw new <type>` (`plan`, `spec`, `backlog`, `research`, `prompt`, `release`), with no aliases since
   nothing is released. `aw research new-comparison` and `aw adopt` are also create verbs and would
   need a home (for example `aw new comparison`).
2. **Two grammars coexist.** Some commands are verb-first over a TYPE word (`aw check|find|search|
   index|rename|group|archive|set <type>`), and others are noun-first owner verbs (`aw backlog set`,
   `aw specs set`, `aw ipd set`, `aw research promote`). Status changes exist in both forms: `aw set`
   and `aw ipd set` / `aw specs set` / `aw backlog set` do overlapping jobs.
3. **Status changes are not uniform.** Research status changes only through `aw research promote`
   (`aw set` rejects research statuses); prompts have no owner `set` verb and go through `aw set
   prompts`; releases go through `aw set releases`.
4. **"IPD" appears in 19 command paths** (the 13 `aw ipd ...` entries, `aw oc runipd`,
   `aw agy runipd`, `aw run ipd`, and three hook names). The records tree, the docs, and the lifecycle legend call it a "plan".
5. **Plural and singular nouns are mixed.** `specs`/`spec`, `releases`/`release`, `profile`/`profiles`
   are aliases; `backlog`, `research`, `prompts`, `reviews`, `runs` have one form each; `run` and
   `runs` are different commands (write versus read).
6. **Duplicates.** `aw exclude`/`aw include` duplicate `aw config exclude add|list|rm`.
   `aw oc run`, `aw oc runipd`, and `aw oc runipd start` are one thing. `aw next`, `aw attention`,
   `aw att`, `aw todo` are one thing. `aw runs` and `aw runs list` are one thing.
7. **Developer jargon in names:** `scaffold`, `lint`, `sync`, `runipd`, `integrate`, `finalize`,
   `normalize-lanes`, `check-refs`, `check-miscategorized`, `verify-ledger`, `set-assign`, `mv`,
   `pwatch`, `oc`, `agy`.
8. **Two ways to delete a list item** exist in `config`: `remove` (alias `rm`) and `exclude rm`.
9. **Hook entry points share the top-level namespace** with everyday commands (six of the 56
   level-1 commands are hook targets a human should rarely type).
10. **Hidden command.** `aw runs repair` exists but is invisible to the parser tree, and verified
    absent from `aw completion bash` (whose `runs` word list ends at `verify-ledger`).
