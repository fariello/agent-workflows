# Spec: clean-delta contribution and artifact-tracking modes for agent-workflows

- Date: 2026-07-26
- Status: draft spec (evidence-gated; build deferred to per-phase IPDs); produced by IPD `20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec`
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Evidence: `.agents/docs/research/20260726-0054-aw-delivery-and-clean-delta-research/` (clean-delta reconciliation `...-0054-05`, host-probe reconciliation `...-1045-05`, and eight underlying model reports). Documentation-graded as of 2026-07-26; no live host fixture was run, so "Followed" means documented, not reproduced.
- Supersedes/extends: `.agents/docs/specs/20260725-0957-01-external-delivery-and-skills.spec.md` (IPD 05's tier spec, whose open per-host questions this resolves).
- Related: IPD 01 (manifest, D103), IPD 02 (managed sections, D104), IPD 03 (untracked convention, D105), IPD 04 (conservative uninstall, D106), IPD 05 (external-delivery + host-probe).

This spec defines the architecture for letting a developer use agent-workflows in a repo they do not own and will PR upstream, leaving that repo a clean delta while tracking their own artifacts elsewhere; and, generally, how much agent-workflows footprint a repo carries. It builds nothing: the build is decomposed into separate, gated per-phase IPDs (Section 9).

## 1. Modes

Exactly two coherent modes. Per-class opt-out and "do not advertise" are motivations SERVED by these modes plus the existing per-file `.untracked.` convention (D105) and the `local/` lanes (D81/D94); they are not a third mechanism.

- Tracked mode (today's default): agent-workflows content + a tracked per-repo manifest + shims + managed instruction blocks live in the repo and are committed. Unchanged.
- Clean-delta mode: NO tracked or baseline local agent-workflows files in the target. The host discovers workflows via user-scope host-native skills; the developer's tracked artifacts live in a developer-owned sibling companion repository; authoritative per-repo mode/routing lives in user-global agent-workflows config; a separate global ownership manifest owns shared user-scope skill files.

Do not expose independent low-level toggles that can create incoherent states (e.g. untracked manifest + tracked shims).

## 2. Clean-delta definition (the acceptance property)

The target repository's INDEX, its branch diff against the relevant upstream merge base, and the proposed pull request contain ONLY the developer's genuine contribution. No agent-workflows file, managed block, ignore rule, manifest, instruction edit, backup, or generated artifact appears in that delta.

A clean working tree is NOT sufficient proof: `.git/info/exclude` reduces but does not guarantee a clean PR (force-add, already-tracked files, prior commits on the branch, and upstream path collisions all defeat it). Verification MUST compare the merge-base diff, not just `git status`.

## 3. Recommended architecture

```
User-scope host skill (T2)  ->  agent-workflows resolver  ->  packaged workflow/harness
Target repository            =  genuine code changes ONLY
Companion repository         =  tracked plans/prompts/research/runs + lifecycle state snapshot
User-global aw config        =  authoritative target->companion mapping, mode, enabled hosts
User-global ownership manifest = ownership of global skill/host files + dependent repos
Package installation         =  canonical workflow bodies + resolver
```

The target needs no pointer because the host's user-scope skill IS the discovery path.

## 4. Per-host delivery decisions (from the host-probe reconciliation)

Tiers: T1 = passive out-of-repo pointer; T2 = host-native skill; T3 = user-global mechanism. All documentation-graded; each is subject to Phase 0 reproduction before the installer advertises it.

- T2 is the primary cross-host mechanism. Project path `.agents/skills/<name>/SKILL.md` is discovered by OpenCode, Codex, Copilot (CLI + VS Code), Cursor, Antigravity, and Gemini CLI. Claude Code needs a `.claude/skills/<name>/SKILL.md` adapter. Global paths per host (examples): OpenCode `~/.config/opencode/skills/` (and `~/.agents/skills/`); Claude Code `~/.claude/skills/`; Codex `$HOME/.agents/skills`; Copilot `~/.copilot/skills` / `~/.agents/skills`; Cursor `~/.cursor/skills` / `~/.agents/skills`; Antigravity `~/.gemini/config/skills/`; Gemini CLI `~/.gemini/skills/` / `~/.agents/skills/`.
- T1 (passive out-of-repo pointer) is NOT a universal mechanism: OpenCode and Codex do not resolve a passive `@path` (OpenCode needs a configured `opencode.json` instruction; Codex has no `@path` expansion); Copilot CLI explicitly refuses absolute/`~/` imports; Copilot-VS Code and Cursor are unproven for arbitrary out-of-workspace files; only Claude Code, Antigravity, and Gemini CLI resolve absolute imports, some with an approval/consent step. Use T1 only host-specifically where first-party import semantics AND a Phase 0 fixture both support it.
- T3 (user-global) exists for every host but is consent-sensitive, surface-dependent, and subject to same-name shadowing; a machine-local T3 install does not automatically reach a cloud surface (Section 8).
- Locally-excluded in-repo shims/skills (via `.git/info/exclude`, never the tracked `.gitignore`, never `core.excludesFile`) are a TESTED FALLBACK only, used when a host lacks a usable user-scope mechanism and a Phase 0 test shows the excluded file is still discovered.

## 5. State and ownership model

- User-global config (authoritative): a per-repo section in `~/.config/agent-workflows/config.json` recording the repo's mode, target identity, companion path, per-class artifact routes, and enabled hosts. This is the only location common to zero-target-file mode.
- Global ownership manifest (separate): owns shared user-scope skill/host files with per-file hashes, source version, and the set of dependent repositories, so a global skill is not deleted while another repo still needs it (consent to install is machine-scoped; dependency registration is repo-scoped).
- Companion state: a versioned recovery snapshot + a human-readable effective policy in the companion repo.
- Tracked-mode target manifest: the existing D103 manifest is retained only for repos that intentionally adopt agent-workflows.
- A fallback local target manifest exists only if a host-specific excluded-project-file mode actually installs target files; then it is a cache/ownership aid, not the sole authority.

## 6. Resolver and conditional-commit rule

Provide a deterministic resolver:

```
agent-workflows context --repo <path> --json
```

returning: canonical target root, install mode, companion root, per-class routes, effective framework version, enabled host integrations, and whether the current command may commit in the target, companion, neither, or both. Every producing workflow calls the resolver instead of parsing config independently, so the seven runbooks that today hard-instruct "commit this (never push)" (assess, assess-all, incident, migrate, spec, plan-review, release-review) become conditional via ONE source (P8): in clean-delta mode, artifact creation / `git mv` / status / artifact-only commits occur in the COMPANION, never the target; code commits occur in the target only as the explicit development task.

Note: plan-lifecycle moves are convention-only today (no engine code moves plan files; the only `_git_mv` at `engine.py:1795`/`:1869` migrates the legacy release-review artifacts dir), so untracking does not break a code mechanism, only the documented prose and the git-history-as-provenance assumption.

## 7. Same-version reinstall + downgrade preservation

Same-version reinstall is a VISIBLE verified no-op, using this state table (not a silent no-op, not an auto-repair):

| State | Result |
|---|---|
| Same version, manifest present, hashes and routes match | Visible verified no-op, exit 0 |
| Managed file missing | Report drift; recreate only with `--repair` or confirmation |
| Managed file edited | Preserve and report |
| Configuration changed | Show and reconcile only the requested configuration |
| Manifest absent | Inspect and require explicit adoption or clean installation |

Downgrade preservation (keep a future downgrade POSSIBLE without building it now): the D103 manifest and the `.agent-workflows-installer-backups/` + `--undo` (D103/D106) already give recent undo, but five rotating backups do NOT preserve arbitrary downgrade. Record, per install transaction: the effective top-level version; a per-file source version; the per-file installed hash; a transaction id; from-version and to-version; and a source revision only for development/mutable builds. Future downgrade re-renders an immutable older package version through the same conservative transaction engine. No downgrade command is built now.

## 8. Cloud boundary

The initial feature is LOCAL clean-delta. Workstation user-scope skills, sibling companion paths, and `.git/info/exclude` state do NOT necessarily transfer into a remote/cloud clone. Remote clean-delta is a separate design (account-synchronized skills, remote environment bootstrap, plugins, mounted external artifact storage, or a developer-owned fork); none is assumed here.

## 9. Migration

Tracked -> clean-delta (explicit `migrate --to-clean-delta` or `install --clean-delta --migrate`):

1. Show a dry-run.
2. Read the existing D103 manifest.
3. Create and validate the companion before removing anything.
4. Copy/move personal artifacts to the companion.
5. Install and test user skills.
6. Remove only unedited installer-owned target files and managed blocks (manifest ownership + exact paths; NEVER a blanket `git rm --cached -r .agents/`).
7. Preserve edited files and stop for user resolution.
8. Add no tracked ignore changes.
9. Examine the index and the merge-base diff against upstream.
10. If agent-workflows content was already committed on the contribution branch, do not assume a new removal commit yields a clean PR: the branch may need an interactive rebase, amend, or a clean cherry-pick onto a fresh branch.
11. Record completion in user-global and companion state.

Clean-delta -> tracked: explicit confirmation; verify no path conflicts; render in-repo workflows + host shims; add managed instruction/ignore blocks only where selected; write the tracked per-repo manifest last; preserve the companion unless the user re-routes; remove fallback `.git/info/exclude` entries only after target ownership is established; leave global skills installed if other repos depend on them.

## 10. Skill taxonomy

Do not create one skill per persona/lens. Three forms:

- Portable capability skills (one per bounded capability): `plan-review`, `release-review`, `verify`, `scaffold`, `spec`.
- Explicit harness skills (one per harness, resolving the selected packaged persona/lens): `advise <persona>`, `assess <lens>`; disable automatic invocation where the host supports it, else a narrow description + tested trigger behavior.
- Non-skill always-on guidance: only concise, genuinely universal instructions in user rules / global instruction files; not the whole catalog.

## 11. Build decomposition (separate, gated per-phase IPDs)

This spec builds nothing. The build is a sequence of separate IPDs, each with its own `/plan-review` + human approval; no IPD spans more than one phase; no delivery-tier phase runs before Phase 0 reproduces that tier for the exact host/version:

- Phase 0 - Conformance harness (its own IPD; FIRST buildable). Per exact host/version: a clean temp home + empty temp git repo; external content outside every workspace root; a unique nonce and an instruction only in that content to create `PROBE-OK-<host>-<version>-<nonce>.txt`; host diagnostics proving resolution; a conflicting repo instruction to establish precedence; permission-denied / approval-accepted / noninteractive runs; separate local and cloud runs; captured version, settings, fixture tree, commands, logs, final filesystem state. Record "Resolved" only from host diagnostics; "Followed" only when the nonce side effect occurs.
- Phase 1 - Resolver + state/ownership (its own IPD): the `context` resolver, user-global per-repo config section, the separate global ownership manifest, companion mapping, per-class routes, and the single-source conditional-commit rewire of the seven runbooks.
- Phase 2 - Packaged user skills (its own IPD; GATED on Phase 0): the Section 10 subset at documented host paths, only for tiers Phase 0 reproduced.
- Phase 3 - Clean-delta install + migration (its own IPD): transactional zero-target-write install; migration both directions; same-version verified no-op; downgrade-preservation record.
- Phase 4 - Fallback project adapters (its own IPD; only after direct evidence): locally-excluded shims/skills, Claude `--add-dir`, host-specific adapters.

## 12. Open empirical unknowns (Phase 0's job; release blockers for the build, not spec blockers)

- Per-host discovery of a file excluded only via `.git/info/exclude`.
- Cursor 3.11 exact skill roots and duplicate-name collision behavior.
- Arbitrary out-of-workspace T1 resolution in Copilot-VS Code and Cursor.
- Duplicate-name skill precedence in OpenCode, Copilot, Cursor, Antigravity.
- Gemini CLI noninteractive/CI behavior for the activation-consent gate.
- Whether machine-local T3 content is available in each cloud-agent surface.
- Sibling-companion read/write/commit under each host's default sandbox.
