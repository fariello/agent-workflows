# advise / spec-editor session summary

- Persona: spec-editor (requirements analyst)
- Artifact: docs/specs/2026-07-06-pip-distribution-and-multi-repo-setup.md
- Date / run ID: 20260706-215643 (UTC)
- Outcome: all open questions resolved; spec updated in place with per-change consent.

## Key questions raised and decisions reached

1. Discovery targets: dir with a non-submodule `.git`; if a configured path has `.git`, that
   is the target and we do not descend; else scan immediate children with non-submodule `.git`.
   Submodules skipped (via parent `.gitmodules`); independent nested repos are valid targets.
   Recursive is opt-in. (A1/A2)
2. No persisted opt-out; the config `repos` list is the allowlist. (A3)
3. Config JSON schema pinned: `config_version`, `search_roots`, `repos`, `ignore`, `defaults`.
   Paths stored `~`-preserved, expanded at use-time (tilde + Windows). `ignore` uses fnmatch
   globs, discovery-only. (B4/B5, OQ4)
4. Versioning is a big, cross-cutting, PREREQUISITE lift -> split into its own FIRST IPD (IPD-1):
   git-tag-driven semver, baseline `v1.0.0` tagged now, dirty/distance-aware
   (`1.0.1.devN+g<sha>` when ahead/dirty) so a clone that differs from a release cannot report
   a clean version (fixes the observed clone-bug). Baked into the wheel at build; runtime reads
   baked value and may recompute live from a git tree. `status` uses PEP 440 ordering with
   states not-installed / stale / current / ahead(`dev`). (C6, sequencing)
5. Text-identical (line-ending-normalized) install comparison, not byte-identical; exec bit
   re-applied by the installer on write. (C7)
6. One verb `install` (idempotent install+update); `all` is a literal keyword; `uninstall`
   added (asks first, no `all`). (D9, E11)
7. No `doctor` command (naive-user-first): preflight warnings + confirmation inside
   install/setup; environment readout folded into `status`. (D10/OQ6)
8. CLI vs LLM `/setup-repo`: COMPLEMENT via one shared install engine. `install` = per-repo
   workhorse (offers setup if no config); `setup` = guided front door (config + discover +
   install + teach, idempotent on re-run); bare `aw` = smart default (setup-if-unconfigured
   else status). This is the user's Design A (distinct commands + bidirectional handoff) plus a
   smart bare-`aw` entry point. (OQ7)
9. Move deterministic setup artifacts (plan dirs, AGENTS pointer, `.gitleaksignore`,
   secret-scan CI) into the CLI; leave stack-tailored `.gitignore`/CI + judgment to
   `/setup-repo`, and tell users to run it. (setup-repo split)
10. Accessible + polished ANSI CLI is a REQUIREMENT, held to the terminal-accessibility rubric
    in assess/lenses/accessibility.md (color not sole signal, honor NO_COLOR/non-TTY, no
    load-bearing dim). (new)

## Corrections surfaced (spec-editor caught its own draft)

- The "validated manually" acceptance criterion 10 was replaced with an automatable
  `setup --root <tmp> --yes` test; manual pipx-on-fresh-machine moved to a release checklist.
- `doctor` was a draft proposal, not a user requirement; dropped.
- Clarified that "config schema" just means the JSON file contents (no second engineer).

## Edits applied to the spec (with consent)

- Goals 3, 7->8/9 (verbs, artifact move, accessibility), Ship-vs-dev section (prior),
  Open Questions 1-7 all marked RESOLVED, acceptance criteria 10 fixed + 13-16 added,
  Sequencing section (two IPDs), Status line.

## Open follow-ups the author still owes

- Run `/plan-review` on IPD-1 (versioning) and IPD-2 (distribution) once drafted.
- Per-OS `command -v aw` / `Get-Alias aw` checks before public release (from collision doc).
- Decide final glob engine detail (fnmatch vs PurePath.match) at IPD time.
