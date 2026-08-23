# Changelog

All notable changes to `agent-workflows` are recorded here. Versions are git-tag-driven
semantic versioning (see `RELEASING.md`); the authoritative "why" for decisions lives in
`DECISIONS.md`.

## 2.0.0 (pending) - AW project layout, storage backends, install wizard, and operational state

This is the first release of a MAJOR rewrite, update, and upgrade of `agent-workflows`
now under way. The direction of the 2.x line (in progress, not all shipped in this entry):

- Broader multi-platform support. First-class, tested behavior across the hosts the
  maintainer uses daily: OpenCode, Hermes, Codex CLI, Antigravity CLI, and Claude Code
  (plus continued best-effort support for any other agent that reads instruction files).
- Lower token cost to run commands. Reduce the tokens an agent spends invoking and
  running workflows and tools, so day-to-day operation is cheaper and faster.
- Higher compliance and rigor. Stronger, harder-to-bypass execution guarantees
  (deterministic gates, honest validation, wrapper-owned test verdicts) so "done" and
  "tests passed" mean what they say.
- More consistency and formality. A more uniform, predictable surface across commands,
  documents, and workflows, with clearer contracts and conventions.
- More tools for agents and users. A growing set of dependable, dependency-free tools
  (and CLI verbs) that both agents and humans can rely on.

Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

- Changed (BREAKING): the canonical layout is now the physical `.aw/` hierarchy with four roots on disk: `.aw/system/` (the CLI-owned workflow bundle, nested at `.aw/system/workflows/` with `VERSION`/`manifest`/`templates` as siblings), `.aw/records/` (durable project records: plans, docs, backlog, comms, prompts), `.aw/config/` (`config.json` + allowlist tracked; `local.json` never tracked), and `.aw/state/` (runtime scratch + durable install/migration state; never tracked). Replaces the earlier logical-only four-root model that left canonical content under `.agents/`.
- Changed (BREAKING): a fresh `aw install` now creates ONLY the `.aw/` hierarchy (no `.agents/workflows/`). Generated command shims and the AGENTS pointer reference `.aw/system/workflows/`.
- Added: `aw install`/`aw update`/`aw setup` auto-detect a legacy `.agents/`-only repository and offer to migrate it to `.aw/` (`--to-aw` / `--keep-legacy`); declining keeps updating the legacy layout in place for a documented compatibility window with a one-time deprecation notice, never a second divergent layout.
- Added: `aw migrate-layout` runs as a guided wizard by default (preview, records-destination choice, leftover disposition, confirm, apply) and accepts a JSON `--config` plus flags for non-interactive use; it MOVES material (no retained legacy twin), with a per-item journal for crash-safe resume and rollback, and an interactive keep/remove/defer step for anything not moved (never deletes without an explicit choice).
- Added: the earlier logical roots (`system`, `config`, `state`, `records`) and dual delivery/records orthogonal axes, now realized as the physical `.aw/` roots above.
- Added: User-level `AW_HOME` (`~/.aw/`) and durable project registry (`registry.json`).
- Added: Flexible records storage backends (`home`, `companion`, `repository`) with explicit durability policies.
- Added: Interactive and noninteractive install/update policy wizard (`aw install`).
- Added: Operational action ledger (`aw todo`, `show`, `complete`, `dismiss`, `reopen`, `history`).
- Added: Dual-surface record routing (`aw path records --agent` and `resolve_record_routing()`).
- Added: Transactional layout migration with rollback journal (`aw migrate-layout`) and conservative uninstall preserving config, state, and records by default.
- Added: Clean-delta mode zero-target-write repository guarantees with D113 host evidence gating.
- Added: Never-install exclude list (`aw config exclude {add,list,rm}`). A user-curated blocklist of repos (absolute paths or fnmatch globs) that must never receive an install, distinct from the discovery-only `ignore` noise filter. Discovery drops excluded repos into a separate `excluded` bucket; an explicitly targeted excluded repo warns and asks to continue interactively (default yes, then an offer to unexclude), and is skipped fail-safe under `--yes` or non-interactive runs so automation never silently installs into one.
- Changed: `aw --help` and every subcommand group now list their subcommands in alphabetical order (display only; dispatch is unchanged).
- Changed: `aw <command> --help` now shows a fuller description of what each command does (inputs, outputs, key flags, and caveats), not just the one-line summary from the parent listing.
- Changed (BREAKING, LOUD): dual-audience CLI output with an automatic non-TTY HARD CUTOVER. When stdout is NOT a terminal (piped, redirected, captured, or agent-driven), `aw` now emits the `aw.agent/v1` JSONL machine format instead of human plain text, with no compatibility window. Three legacy byte forms are removed and are now `aw.agent/v1`: (1) piped `aw status` JSON, (2) the `render_agent_drift` TSV lines (`location<TAB>rule<TAB>detail`) that check/doctor-style commands printed, now the `diagnostics` array of a record, and (3) the `aw find`/`aw search` path lines (`path` / `path:line`), now `item` records terminated by a `summary` record. If you scrape `aw` output in a script, you MUST migrate: use `--agent` (machine JSONL) or `--json` (pretty structured) explicitly and parse JSON. There is no flag that restores the old bytes. The 0/1/2 exit classification is unchanged (0 clean, 1 findings, 2 cannot-run). See the migration guide (`docs/cli-migration.md`), the human guide (`docs/cli-human-guide.md`), the agent protocol reference (`docs/cli-agent-protocol.md`), and the normative contract (`docs/cli-output-contract.md`). This supersedes the retired `Drift`/`drift_exit_code` machine convention that spec `20260818-1525-01` G6 previously mandated; `aw.agent/v1` is now the single canonical machine format.
- Added: a generated output-conformance harness (`tests/test_cli_conformance_matrix.py`, `tests/test_cli_quality_gates.py`, `tests/conformance_matrix.py`) that fails CI on any undeclared parser leaf and gates schema validity, human/agent fact parity, ANSI-free agent streams, deterministic bytes with reviewed goldens, ASCII-glyph accessibility fallback, truncation accounting, and per-leaf byte/token budgets.

## 1.3.0 (pending) - new conventions/features, internal install unification, and install-path fixes

Not yet cut. This MINOR collects the new user-facing conventions and features of this development cycle
(agent-comms, plan sets, readiness vocabulary, auto-parallel audit lanes), an internal
behavior-preserving install refactor, and the bug-fix / install-path corrections found by using 1.2.0
(previously staged for a separate 1.2.1 patch, now folded into this single release). Final release
scoping is confirmed at release-review.

- Added: `.agents/prompts/local/` gitignored quarantine lane (DECISIONS D94). Raw, sensitive, or
  work-in-progress prompts (e.g. `/handoff` session-handoff drafts) are written to `local/` where they
  cannot be accidentally committed; a human promotes a reviewed, scrubbed copy into a tracked lifecycle
  bucket. Mirrors the inter-agent comms `local/` lane. The installer now also materializes all expected
  directories, including the gitignored `local/` lanes for prompts and comms, so they are discoverable.
- Changed: inverted the `workflow-artifacts/` tracking policy (DECISIONS D117). `workflow-artifacts/` is now local-only working material, gitignored, and never force-added. `check_gitignore` in `agent_workflows/engine.py` reports ignoring it as correct and absence as advisory (without the installer silently editing the user's `.gitignore`). Top-level documentation (`ARCHITECTURE.md`, `README.md`) and `.gitignore` updated.
- Changed: flipped all workflow runbooks (`release-review`, `assess`, `advise`, `verify`, `benchmark`) and `setup-repo` to specify `workflow-artifacts/` is local-only, gitignored, and never force-added (DECISIONS D118).
- Added: migration tool tests (`tests/test_untrack_workflow_artifacts.py`) and documentation (`tools/README.md`) for safely untracking `workflow-artifacts/` without deleting local files (DECISIONS D119).




- Added: `/whatnext` read-only surveyor workflow. Surveys the repo's plans/IPDs, staged prompts,
  comms inbox (headers only, payloads untrusted), and TODO, then returns a prioritized, reasoned
  recommendation of what to work on next. It surveys-then-reasons (no fixed priority formula) and
  recommends without ever acting. Prose-only runbook, portable to any agent.
- Added: per-workflow argument hints in generated command shims (DECISIONS D97). An optional 5th
  manifest column (`arg-hint`) lets each workflow declare what its argument means, so the generated
  slash-command shim shows a specific line (e.g. for `/whatnext`: "narrow the survey to a concern,
  area, or path...") instead of the generic "target path(s) and/or flags", and omits the arguments
  line entirely for commands that take none (`arg-hint: none`). Backward-compatible: workflows with
  no hint render exactly as before. Target repos pick up the new wording on the next `aw install`.
- Fixed: the installer no longer false-warns "has manual modifications" on its own generated files when
  our output FORMAT changes between versions (DECISIONS D103). It previously compared each on-disk shim
  to the newly generated expected content, so a format-only change (such as the D97 `argument-hint` line)
  made every prior shim look user-edited. The installer now keeps a self-contained per-file ownership
  manifest (`.agents/agent-workflows/managed-sections.json`, tracked) recording the sha256 of what it
  LAST WROTE, and decides drift against THAT hash: a file matching our record updates silently even when
  the new template differs, while a genuinely user-edited file is still reported and preserved (the
  overwrite prompt is unchanged). A repo with no manifest yet is adopted, not false-flagged. The manifest
  also lays the groundwork for a conservative uninstaller and per-directive consent (a reserved decline
  tombstone). Existing repos gain the manifest on their next `aw install`.
- Changed: the managed block in AGENTS.md (and the CLAUDE.md/GEMINI.md mirror) moved from the single
  monolithic `<!-- AGENT-WORKFLOWS:BEGIN -->`..`:END` block to a sectioned scheme (DECISIONS D104): an
  outer `<!-- aw:block -->`..`<!-- /aw:block -->` wrapper containing individually marked
  `<!-- aw:<slug> -->` sections, so each agent-workflows directive can be identified, updated, removed,
  and (via the D103 manifest) individually consented to or preserved when you edit it. Markers render in
  each file's own comment syntax (bare HTML in Markdown, `#`-prefixed in a `#`-comment file). Existing
  repos are CONVERTED in place on the next `aw install` with no human-visible content change and no
  duplicate block; the old markers are recognized but never re-emitted. Any hand-authored sibling block
  you keep in the same file (a different `NAME:BEGIN/END` block) is left untouched. This is the mechanism
  the per-directive-consent and token-economy work builds on; the current pointer is one `aw:pointer`
  section for now.
- Added: an untracked-file safety convention (DECISIONS D105). On install, agent-workflows adds a small
  managed block to your repo's root `.gitignore` (in `#`-comment `aw:block` syntax) that ignores any
  file named `*.untracked.*` / `*.untracked` and any directory whose name contains `untracked`. This is
  a passive, name-based escape hatch: name a sensitive or provisional file `notes.untracked.md` (or put
  it under a `*untracked*/` dir) and a blanket `git add`, the hooks, and the sanitizer will not stage it,
  even inside directories the lifecycle rules say to commit. The install also prints an honest notice
  that agent-workflows tracks IPDs/prompts/research by default and names the safety valves (the untracked
  naming plus the gitignored `.agents/prompts/local/` and `.agents/comms/local/` lanes), and warns about
  any files that ALREADY match the patterns but are git-tracked (with the `git rm --cached` remedy, since
  ignoring does not untrack). The block is identifiable and is removed by `aw uninstall`, leaving your own
  `.gitignore` lines intact. Existing repos get it on the next `aw install`.
- Changed: `aw uninstall` is now conservative and manifest-driven (DECISIONS D106). It removes only
  what agent-workflows installed (per the D103 manifest), PRESERVES any generated file you have edited
  (reporting it and, interactively, offering to show the diff and let you decide; `--force` removes it),
  strips only the managed blocks from AGENTS.md/CLAUDE.md/GEMINI.md/`.gitignore` (leaving your content and
  any hand-authored sibling block intact), and removes its own manifest last. It then OFFERS a deeper
  `.agents/` cleanup of the scaffolding it left behind, announcing how many files it would delete per
  directory, letting you list them or abort, and warning louder when files are not recoverable from git
  (untracked/uncommitted). New flags: `--dry-run` (report the full plan, change nothing), `--deep`
  (perform the deeper cleanup non-interactively), `--force` (also remove edited files, skip prompts).
  Tracked files are removed with `git rm`, and when done uninstall offers to commit ONLY the files it
  changed (never pushes). The separate `--undo` (roll back the last install from backups) is unchanged.
- Added (internal spec): a research/spec for delivering agent-workflows from outside a repo or via
  host-native skills (DECISIONS D107). This is groundwork, not a user-facing feature: it defines the
  delivery tiers (in-repo, packaged data path, host-native `.agents/skills/SKILL.md`, home-dir), a
  per-host probe protocol to prove whether each host actually resolves and follows out-of-repo content,
  and an upload-ready external-research prompt to gather that evidence. No external-delivery behavior
  ships yet; any build is gated on the probe results.
- Changed: the "ask self-contained questions" convention (GUIDING_PRINCIPLES P12) now also guides HOW to
  compose an interactive question, not just where the question set lives (DECISIONS D108, extending D100).
  It tells agents to give a compact, decision-ready synthesis (relevant facts, what changed, why a
  decision is needed, essential constraints/tradeoffs, a recommendation), to omit chronology/filenames/
  quotes unless essential, to keep it screen-sized, and specifically to NOT repeat or preview the choices
  the interactive tool already renders. The installer's AGENTS.md pointer gains a one-line reminder and
  both `/plan-review` variants clarify that their six-part question's "Options" item is satisfied by the
  tool's rendered choices (not restated in prose).
- Added (internal spec): a design spec for clean-delta contribution and artifact-tracking modes
  (DECISIONS D109). Groundwork, not a shipped feature: it defines two modes (the current tracked mode,
  and a clean-delta mode that lets you use agent-workflows in a repo you will PR upstream without adding
  any agent-workflows files to that repo, keeping your own artifacts in a sibling companion repo),
  chooses host-native skills as the primary delivery mechanism (a universal out-of-repo pointer is not
  viable across hosts), and decomposes the build into separate, gated per-phase IPDs starting with a
  conformance harness. No clean-delta behavior ships yet; it consumes and is grounded in the committed
  aw-delivery research bundle.
- Fixed: `/plan-review` (and the parallel `/plan-review-long`) no longer let the reviewer pad its final
  "reviewed / not reviewed" list with unrelated plans (DECISIONS D110). The scope ledger is now bounded to
  the plans you explicitly name plus any the project's own eligibility rules add; a plan that was never a
  candidate is an "incidental file" and is never listed; and the NOT REVIEWED section reads `(none)` when
  you reviewed a single target and skipped nothing, instead of enumerating the whole `.agents/plans/executed/`
  directory. Wording clarification only; the review logic is unchanged.
- Added: the IPD template now includes a `## Detailed Implementation Checklist (TODO)` section, a
  completion rule, and split-into-a-Set guidance (DECISIONS D111). Plans authored from the template now
  carry a tickable per-task checklist (with exact files/symbols and the literal verification command), and
  the execution gate requires every item to be checked AND independently verified before a plan may be
  claimed done or moved to `executed/` (STOP-and-report otherwise); it also advises splitting a large plan
  into an ordered Set of small, independently-verifiable plans. This markedly improves completeness for
  faster/weaker executing models, which have no external todo tool. Target repos get it on the next
  `aw install`.
- Added: a canonical IPD spec (`.agents/docs/specs/...-ipd-spec.md`) and a concise always-loaded directive
  in the managed AGENTS.md block requiring it (DECISIONS D112). Agents now have one authoritative "how to
  author and execute an IPD" reference (consolidating the template, the D111 checklist + completion rule,
  the lifecycle/status/commit conventions by reference), and the always-loaded pointer states the MUST
  explicitly so weaker/faster models follow it reliably. Target repos get the directive on the next
  `aw install`.
- Changed: the IPD template now carries TWO checklists (DECISIONS D114, extending D111): an execution
  checklist near the top (every action/decision/deliverable/validation) and a separate
  `## Validation and cross-check` checklist near the end whose items map 1:1 and require concrete evidence
  per item before reporting success, with an explicit "report incomplete/blocked/skipped/unverified work"
  rule. The completion gate now requires both checklists satisfied before a plan is done/`executed`, and
  the size guidance is sharpened (prefer <=5 major steps; avoid more than ~10 / 12-18 items; beyond that
  split into an ordered Set, coordinated by a `00` orchestrator IPD). Target repos get it on the next
  `aw install`.
- Changed: `/plan-review` (and `/plan-review-long`) now require, for an agent-executable plan, that the
  author included both the execution checklist and the end verification/cross-check checklist, and that the
  reviewer assessed both and confirmed the verification checklist is specific enough to catch a false
  "done" (DECISIONS D115, building on D114). A missing or weak checklist is a finding the reviewer fixes
  in place.
- Added: the canonical IPD spec now documents the two-checklist convention end to end, and a `00`
  orchestrator template is shipped alongside the IPD template (DECISIONS D116). Authors have one reference
  for the execution + verification checklists, the creator/reviewer duties, the size thresholds, and how to
  coordinate a split into a Set via a `00` orchestrator IPD (sequence, dependencies, completion criteria,
  cross-IPD validation). Completes the dual-checklist convention (D114-D116).
- Changed: producing workflows (`/assess`, `/assess-all`, `/incident`, `/migrate`, `/spec`) now end
  with a uniform closing report (DECISIONS D102): which artifact file(s) they created, with paths, or
  that they created none and WHY, plus concrete next steps. `/assess` also now reports the run-record
  path and handles the "assessed, nothing to propose" case explicitly. The shared convention lives at
  `.agents/workflows/assess/templates/closing-report.md`.
- Changed: the installer's interactive overwrite prompt is now clearer and stricter (DECISIONS D101).
  It reads `Do you want to overwrite it? [y/N/d/help]:` with a plain-English legend (Y = overwrite,
  N = do not, D = show differences, help), rejects unrecognized input and re-asks instead of silently
  treating it as "no", and accepts `y/yes`, `n/no`, `d/diff`, `h/help/?`. The stale-file delete prompt
  got the same validation. The safe default (preserve/keep), Ctrl-C abort, and `--yes`/non-interactive
  behavior are unchanged.
- Added: "ask self-contained questions" convention (DECISIONS D100, GUIDING_PRINCIPLES P12). When an
  agent poses a decision through an interactive prompt, the entire question set - the context needed
  to decide, the question, and the options - now belongs INSIDE the prompt, so a human can decide from
  the prompt alone. Reminded in AGENTS.md (every repo) and referenced from the question-asking
  workflows (plan-review, advise, spec, getting-started).
- Added: optional local-leaks backstop install via `/setup-repo` and agent awareness (DECISIONS D99,
  completing the leak-sanitizer Set). `/setup-repo` now asks (never auto-installs) whether to add the
  `local-leaks` pre-commit hook (default yes) and a CI backstop (default no) to your repo; the
  generated CI installs `agent-workflows` and runs the check. The `/assess local-leaks` lens now
  consumes the engine's machine-parseable `--agent` output instead of re-deriving findings in prose,
  and AGENTS.md now tells any agent to run `aw sanitize --agent` before hand-judging identifying-info
  leaks, even in a repo with no hook installed.
- Added: `aw sanitize --configure` interactive config wizard (DECISIONS D98). Walks you through
  the leak-sanitizer's allowlist, the IP and hostname toggles, and your never-committed personal
  hints, explains each control, shows a diff, and writes only on confirmation (re-runnable, safe,
  needs a terminal). Also hardened the minimal TOML parser it builds on: a config value containing
  a `]` (e.g. a `[a-z]` regex character class) is no longer silently dropped, a pre-existing bug
  that also affected hand-authored configs.
- Added: unified `agent_workflows.leak_sanitizer` engine and the `aw sanitize` alias (DECISIONS D96).
  One deterministic stdlib engine now backs every leak surface: it adds `--fix` (opt-in, interactive,
  never in the hook), an `--agent` machine-parseable mode, an off-by-default IP ruleset, a staged-blob
  scan mode, and FQDN hostname derivation, while `aw check-local-leaks`/`local_leaks` keep working
  unchanged (they re-export the engine; the D93 warn/fail split is preserved). Adopts and credits ideas
  from pubrun's `sanitize_paths.py`. New guiding principle: deterministic, no-judgment checks belong in
  agent-friendly scripts (with an `--agent`/`--llm` mode), not in token-burning LLM workflows.
- Added: `aw check-local-leaks` and the `/assess local-leaks` lens (DECISIONS D93). A first-class
  detector for maintainer/machine identifying info that must not appear in a public artifact
  (home paths, usernames, other local accounts, private repo names, hostnames, session ids) - the
  class ordinary secret scanners miss. One shippable engine (`agent_workflows/local_leaks.py`) feeds
  the CLI, the pre-commit hook, the tests, and the interactive lens; it scans the working tree, git
  history (bounded), or a built wheel, auto-derives candidate tokens (advisory), and reads a
  repo-committed allowlist plus a never-committed user-level hints file. A `local-leaks` CI workflow
  is the push-time backstop.
- Fixed (versioning): the git-tag-driven version resolver now considers only semver release
  tags (`git describe --match 'v[0-9]*' --exclude '*-recreated'`) and safely ignores
  non-release marker tags, with a parser guard that degrades any non-conforming tag to
  `0.0.0+g<sha>` instead of bumping it. Previously a stray non-semver tag near HEAD could
  derail version derivation and block the wheel build.
- Fixed (privacy/correctness, DECISIONS D92): removed maintainer-specific references (local
  filesystem paths, private repo names, a second local test account, and captured session ids)
  from tracked files, including one that had shipped inside a packaged reference doc. Added a
  durable guard (`tools/check_personal_paths.py`, a pre-commit hook, and
  `tests/test_no_personal_paths.py`) that fails when a tracked file embeds a personal-path or
  identity token, with an allowlist for the public author email and repo origin. Ephemeral run
  records (`workflow-artifacts/`) and session-recovery dumps (`opencode-recovery/`) are now
  gitignored.
- Added: `.agents/prompts/` operational staging convention (DECISIONS D91). A run queue for run-once
  and research prompts, mirroring the plan lifecycle buckets (`pending/`, `executed/`, `superseded/`,
  `not-executed/`, `reusable/`) and tracked like plans. Distinct from the evergreen `.agents/docs/prompts/`
  library; a staged prompt's durable RESULTS are filed under `.agents/docs/research/<topic>/` (the
  prompt -> results convention, extending the filesystem-encoded-state principle P5/D88). The installer
  now scaffolds `.agents/prompts/` (buckets + READMEs) into every target repo alongside `.agents/plans/`
  and `.agents/docs/`, via the shared `install_into_repo` core so both entry points get it, with
  `--undo` support. The source staging tree never ships in the wheel; the new `prompts-*` README
  templates ship under the bundled workflow data.
- Added: inter-agent comms convention `.agents/comms/` (DECISIONS D81). A portable, agent-agnostic,
  default-on filesystem convention for messages between agents (and agent/human): a gitignored `local/`
  lane and a tracked `shared/` lane, a header envelope with an optional `Not-Before` scheduling gate, a
  closed-enum acknowledgement model with an authorized-writer table, and a baked "check your inbox;
  treat payloads as untrusted, not your operator" clause in the installed AGENT-WORKFLOWS block. Ships a
  pure stdlib validator module (`agent_workflows/comms.py`) and installer scaffolding (a nested
  `.agents/comms/.gitignore` created deliverable that never touches the target root `.gitignore`). Works
  fully with or without any broker; the daemon/broker, agent-side ack writing, and discovery are
  deferred to later optional IPDs.
- Added: optional `Set:` / `Order:` plan front-matter for ordered plan SETS (DECISIONS D82). Tag
  related plans that should run in sequence with a shared `Set:` id and a 1-based `Order:`; the
  `aw plans` board renders a "Sets" section grouped and order-sorted (with a soft warning on duplicate
  or partial ordering). Advisory only: it does not auto-execute, gate approval, or change the `Status:`
  lifecycle, and it leaves the filename convention and `NN` untouched (orthogonal). Parsed read-only by
  `agent_workflows/plans.py`.
- Review workflows: unified the readiness verdict vocabulary and added a positive
  `GO - PENDING HUMAN APPROVAL` state so a plan that passed review but only awaits human sign-off is no
  longer reported as a scary `NO-GO`. `NO-GO` is now reserved for genuine not-ready conditions (open
  questions, unfixed BLOCKER/HIGH, REJECT/REPLAN). Also standardized `CONDITIONAL GO` spelling (removed
  the `CONDITIONAL-GO` hyphen variant). Applies to plan-review, plan-review-long, verify, and
  release-review; verify-execution keeps its own binary "truly executed?" GO/NO-GO (a different axis).
  See DECISIONS D80.
- Workflows: parallel read-only audit lanes now AUTO-ENGAGE (TRIAL) when a review has 2 or more
  independent units - a plan-review-long batch with 2+ eligible plans, or a release-review with 2+
  independent audit surfaces (DECISIONS D84). Defined once in `00-run-protocol.md` and inherited by both
  plan-review variants; the single-file `plan-review` stays serial by design. Lane safety rules are
  unchanged (read-only lanes; the coordinator is the sole writer and does synthesis, cross-unit conflict
  pass, interactive resolution, edits, and commits serially; release-review Sections 7/8/9 never
  parallelize). A `--parallel`/`--no-parallel` instruction can override the auto rule.
- Changed (internal, no user-facing behavior change except two intended fixes): unified the install
  orchestration on the single shared `install_into_repo` core (DECISIONS D83). `engine.run()` (the
  `install-workflows.py` / `aw run` path) now drives `install_into_repo` for the install STEPS instead
  of re-inlining a parallel sequence, so the two entry points can no longer drift. Intended fixes that
  fall out: the CLI install summary now lists migrated files (it silently omitted them before), and
  `aw install --yes` now overwrites a customized shim to match `install-workflows.py --yes`. The
  deliberately-terse `aw install all` batch path is unchanged.
- Fixed (metadata): the author email now matches across `pyproject.toml` and `CITATION.cff`
  (`gfariello@fariel.com`); they previously disagreed (release-review REL-002).
- Fixed (HIGH, install parity - DECISIONS D85): `aw install all` and `aw setup` previously STAGED the
  framework files in every configured repo but never offered to commit them, silently leaving a whole
  fleet dirty. All install entry points (`aw install`, `aw install all`, `aw setup`,
  `install-workflows.py`) now share one per-repo orchestration shell that installs, summarizes, AND
  offers to commit (auto-commits under `--yes`; prompts otherwise; on decline it tells you what is left
  staged and how to commit) - so no path leaves a repo silently dirty. Also finished the batch
  SystemExit-isolation fix in the legacy `engine.run()` multi-repo path (one bad repo no longer aborts
  the batch), made `--undo` rollback survive a corrupt install record, removed em dashes from `NOTICE`,
  corrected stale "3.8 floor" wording to the declared 3.9, and made `make version-file` sync the
  `index.md` version stamp.
- Fixed (install correctness, from an `/assess bugs` pass): (1) `install-workflows.py` / `engine.run()`
  now returns its computed exit code instead of always `0`, so a failed/aborted target repo makes the
  process exit non-zero. (2) `--undo` rollback now removes the installer's setup-artifact files
  (`.gitleaksignore`, the secret-scan CI workflow, and the `.agents/comms/` skeleton), which were
  previously left behind because they were not recorded in `.created-files.json`. (3) `aw install all`
  and `aw setup` now isolate a per-repo `SystemExit` (e.g. a directory conflict), so one failing repo no
  longer aborts the whole batch. Also: fixed an `Optional` type annotation, a preserved-customized-shim
  status tag (now `[preserved]` instead of the misleading `[no change]`), a silent install-record write
  failure (now warns), CSV outputs opened with `newline=""` (no double blank rows on Windows), a dead
  Makefile meta-target skip in the check runner, and short-secret redaction (short secrets are no longer
  nearly fully revealed in scan output).
- Fixed: the installer stamped the wrong version into target repos. `.agents/workflows/VERSION`
  was baked at `1.1.0` even in the `v1.2.0` release, and the installer copies that file into each
  target. The baked VERSION is now re-baked from the intended release version and committed before
  tagging (bake-then-tag), and a test guards against a stale/dev baked value. (The 1.2.0 PyPI wheel
  was unaffected; its version is resolver-computed.)
- (Pending) `aw install` now runs the full git-diagnostics pre-flight (parity with the
  deprecated installer), and the diagnostics no longer offer a no-op "git pull" for a repo that is
  merely dirty from untracked files and already in sync.
- Internal: fixed wall-clock-proximity flakiness in the plan-filename normalizer tests (they now use
  today-relative dates); no product behavior change.
- Fixed (bug): `aw plan-names` now recognizes the `specs`/`prompts` doc buckets - the shipped
  `normalize_plan_names.py` `DOCS_SUBDIRS` had drifted from the engine's; added a drift-guard test.
  (The rest of the docs/consistency pass that shipped alongside it is documentation-only; see below.)
- Docs/consistency pass (repo-wide `.md` audit, documentation-only; DECISIONS D79): corrected
  `RELEASING.md` first-PyPI-release fact (`1.2.0`, not `1.1.0`); synced the
  `.agents/workflows/index.md` version stamp to `VERSION` (`1.2.1`); added a DECISIONS erratum (D79)
  disambiguating duplicate `D22/D23/D24` numbers as `D22b/D23b/D24b` and fixed the affected
  `ARCHITECTURE.md` references; corrected `CONTRIBUTING.md` to the bake-then-tag release order; documented
  the `auto-approved` status in the plans READMEs; and assorted small reference/label fixes. (The one
  behavioral change from that pass, the `aw plan-names` bucket fix, is the separate "Fixed (bug)" bullet
  above.)

## 1.2.0 - first PyPI publish

This is the first release of `agent-workflows` published to PyPI. The project has been
git-tag-released since `v1.0.0` and used across multiple repositories before this publish, so
the PyPI history begins mid-story at `1.2.0` (continuing the existing `v1.0.0` -> `v1.1.0` tag
line) rather than at `1.0.0`. Numbering it `1.0.0` would make `1.0.0` refer to two different
trees (the existing git `v1.0.0` tag and a much newer PyPI build), which the project's
versioning decisions (DECISIONS D44/D50/D51/D74) deliberately avoid.

Highlights since `v1.1.0` (all backward-compatible, hence a MINOR bump):

- Release consent decision tree (close-out / release-candidate / full release) and a
  release-candidate version convention (`vX.Y.Z-rc.N`), with an rc-aware version resolver.
- A standing agent execution contract in the managed pointer block, plus enforcement in the
  plan-review workflows; MUST-mirror rules for private "brain"-dir plans and walkthroughs.
- Mirroring of the workflow pointer into existing `CLAUDE.md` / `GEMINI.md` so it reaches
  Claude Code and default Gemini.
- A new `data-modeling` assess lens and sharpened UX/data-modeling guiding principles.
- A `.agents/docs/` bucket standard (research / walkthroughs / specs / prompts / roadmaps);
  the reference prompt library and design specs were consolidated under `.agents/docs/`.
- A `/verify-execution` workflow and an `auto-approved` plan-readiness status.

## Earlier (git tags, not on PyPI)

- `v1.1.0`, `v1.0.0` - git-tagged releases prior to PyPI publication. See `git log` and
  `DECISIONS.md` for the full history.
