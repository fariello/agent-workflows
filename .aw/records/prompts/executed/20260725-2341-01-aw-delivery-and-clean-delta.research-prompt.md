You are a principal-level software architect and release engineer whose specialty is developer tooling that installs INTO other people's git repositories, multi-host AI coding-agent ecosystems (where the host application, not the model, controls file discovery), and safe, reversible, low-footprint installation and uninstallation. Adopt that persona for the entire task. Be rigorous, evidence-driven, and skeptical: challenge our premises, tell us when a stated need should be dropped or reframed, surface risks and failure modes we did not raise, and prefer the SIMPLEST design that meets the real need over a clever one. Where a claim depends on host behavior you cannot verify, say so explicitly and state exactly what evidence would settle it. Do not flatter, and do not agree by default; if our current design or a prior decision is wrong, say so and why.

Produce your answer as a single downloadable Markdown (`.md`) file.

## 1. Who we are and what exists today

We maintain "agent-workflows", a tool-agnostic toolkit that installs reusable AI-agent workflows and instruction directives into a target git repository. Current design (all already shipped and in use):

- Installation writes INTO the target repo: a workflow tree under `.agents/workflows/`; generated per-command shim files under `.opencode/commands/` and `.claude/commands/` whose body is literally `Read and execute @.agents/workflows/<path>`; a managed pointer block in the repo's root `AGENTS.md` (and mirrored into an existing `CLAUDE.md`/`GEMINI.md`); and scaffolding dirs `.agents/plans/`, `.agents/docs/`, `.agents/prompts/`, `.agents/comms/`.
- A per-repo ownership MANIFEST at `.agents/agent-workflows/managed-sections.json` records, per installed file, its repo-relative path, a kind (file / shim / section), host, logical id, and the sha256 of the content the installer last wrote, plus a single top-level `installed_version`. It is tracked by default, git-independent, path-parameterized, and drives a conservative uninstall (unedited owned files removed; user-edited files reported and preserved; the manifest removed last).
- The installer backs up every overwritten file to `.agent-workflows-installer-backups/<timestamp>/` with a `.created-files.json`, keeps the last 5 backups, and has an `--undo` that restores them. Backups are git-independent.
- A managed-block mechanism marks agent-workflows-owned regions of shared files with `<!-- aw:block -->` / `<!-- aw:<slug> -->` markers, rendered in each file's comment syntax (bare HTML in Markdown; `#`-prefixed in a `#`-comment file such as `.gitignore`), tracked per section by slug + normalized hash in the manifest. A foreign, hand-authored block in the same file is left untouched.
- A single-file "untracked" convention: files named `*.untracked.*` / `*.untracked` or under a `*untracked*/` dir are gitignored via a managed block in the repo's root `.gitignore`; there are also gitignored `local/` lanes under `.agents/prompts/` and `.agents/comms/` (the "the directory you write to IS the tracked/untracked choice" pattern).
- The user config is USER-GLOBAL at `~/.config/agent-workflows/config.json` (XDG-honoring); today it stores a flat list of repo paths plus install defaults, with a hard-allowlisted schema. It has no per-repo section.
- The workflow bodies are ALSO shipped as importable package data (an out-of-repo SOURCE for the INSTALLER already exists), but every DISCOVERY/EXECUTION path (shim bodies, the `AGENTS.md` pointer, VERSION detection, drift checks) currently assumes an IN-REPO copy. Whether a given host will RESOLVE and then FOLLOW content that lives outside the repo is unproven per host and per version and is the subject of a separate probe; do NOT assume it works.
- Plan-lifecycle moves (`pending -> executed/...`) are CONVENTION-ONLY (documented; agents perform the `git mv`); no code moves plan files. Git history is today's audit trail for that lifecycle, and about eight producing runbooks instruct the agent to "commit this artifact (never push)".

## 2. The behaviors we want to enable (analyze; do not treat as settled)

Design the best architecture for these needs. Treat each as a hypothesis to evaluate; recommend dropping or reframing any that are not worth their cost.

1. Clean-delta contribution (the strongest driver). A developer wants to use agent-workflows FULLY while working in a repo they do NOT own and intend to open a pull request against. Real cases: contributing to `opencode` and `hermes`, which each carry their OWN `AGENTS.md`. The upstream repo must end up containing ONLY the developer's genuine code delta: no agent-workflows files, no manifest, no modified `.gitignore`, no touched `AGENTS.md`. Yet the developer still wants their own agent-workflows artifacts (IPDs, prompts, research, run records) fully tracked and versioned somewhere THEY control.
2. Do-not-advertise / low-footprint: some users do not want to disclose they use agent-workflows, or simply do not want its files in the repo, independent of the PR case.
3. Per-class tracking opt-out: keep specific artifact CLASSES (plans/IPDs, prompts, research/docs) out of git while still using them locally, without breaking the workflows that produce/move them.
4. Untrackable framework + manifest: optionally keep the framework files and the manifest themselves out of the repo's tracked set (a superset of the clean-delta case).

## 3. The hard problem to confront head-on (do not gloss this)

In the clean-delta case, if we may not add shims and may not touch the repo's `AGENTS.md`, then the usual DISCOVERY path is gone: how does the host find and follow the workflows at all? Address this directly:

- Per host (OpenCode, Claude Code, Codex, GitHub/VS Code Copilot, Cursor, Antigravity, Gemini), what discovery paths exist that do NOT require committing files to the repo? Consider: a locally-excluded `AGENTS.md`/shim (present on disk, excluded from git via `.git/info/exclude` or the user-global `core.excludesFile`, so the host sees it but git does not); host-native global/user-scope config; an out-of-repo or sibling-repo reference; and host-native skills (see below). State which are proven vs unproven per host and version, and how discovery interacts with the repo's OWN `AGENTS.md` (precedence, shadowing, and whether an untouched upstream `AGENTS.md` plus a locally-excluded aw pointer can coexist).
- The requester today handles this by telling the agent to "read and execute" something outside the repo, and finds it unwieldy. Evaluate why, and whether a cleaner mechanism exists.
- Be explicit that modifying the repo's TRACKED `.gitignore` is itself pollution to avoid for the PR case, so `.git/info/exclude` and `core.excludesFile` (local, never committed) are the candidate ignore homes; analyze their limitations (not shared with collaborators; not versioned; per-clone; and whether the host reads a file that git ignores).

### 3a. Host-native skills (`SKILL.md`) - analyze in depth

Some hosts natively auto-discover a skill file at a conventional path (commonly `.claude/skills/<name>/SKILL.md`, and an emerging cross-tool `.agents/skills/<name>/SKILL.md`) WITHOUT any explicit pointer or shim. This is potentially the cleanest low-footprint discovery path, so evaluate it rigorously and separately:

- Per host and version, state precisely: does the host auto-discover a `SKILL.md`? At which exact path(s)? Does discovery require a setting, a marketplace/registry step, or a specific directory layout? Does it discover skills OUTSIDE the repo (user/global skills dir) as well as in-repo? Cite official docs/changelogs with dates; distinguish "documented" from "reproduced".
- Footprint and clean-delta fit: is a `SKILL.md` under `.claude/skills/` or `.agents/skills/` still a committed file (so it pollutes a PR), or can it be locally-excluded and still discovered? Does any host support a purely user/global skills location that leaves the repo untouched entirely?
- Format and portability: what is the required `SKILL.md` schema/front-matter per host, and how portable is one file across hosts? What does a host do with a `SKILL.md` it does not understand (ignore vs error)?
- Suitability of OUR content: our workflows are a mix of on-demand capabilities (e.g. release-review, plan-review, verify, scaffold, spec) and persona/assessor/dialogue runbooks (advise, assess). Which are a good fit for the skills model and which are not? We do NOT want to mechanically convert every workflow to a skill; recommend which subset, if any, should be delivered as skills, and whether skills should REPLACE or COMPLEMENT the shim/pointer model per host.
- Reliability caveats: note where skill discovery is version-dependent, best-effort, or inconsistent, and what would have to be true for us to rely on it for the clean-delta case.
- Interaction with our manifest/uninstall: if a skill file is installed (in-repo or global), how is it recorded for ownership and clean removal, and does the global case risk mutating a shared user skills directory without consent?

## 4. Candidate mechanisms to evaluate (extend this list; it is not exhaustive)

For each: fit to needs 1-4, footprint on the target repo, host-discovery dependency (and how to prove it), reversibility/uninstall, and interaction with the manifest / backups / managed blocks / lifecycle.

- A) In-repo install, all aw paths excluded locally via `.git/info/exclude` or `core.excludesFile` (never the tracked `.gitignore`); the developer's own artifacts written to a sibling location outside the repo that they track in their own git.
- B) A sibling "mini-repo" beside the target (e.g. `../<repo>.aw/`), its own git repo the developer controls; the target repo gets only a locally-excluded pointer or nothing tracked. (Depends on host resolve-and-follow of out-of-repo content.)
- C) Home-dir / global install of the framework, referenced from the repo (depends on host resolve-and-follow; consent-gated; must not mutate global host config without consent).
- D) Per-class nested-`.gitignore` opt-out (like the `local/` lanes) for plans/prompts/research, and optionally the framework and manifest.
- E) Status quo: document `.git/info/exclude` + the `.untracked.` convention + `local/` lanes; build nothing new.
- F) Host-native skills (`SKILL.md`) delivery per Section 3a: deliver the skill-eligible subset as `SKILL.md` (in-repo, locally-excludable, or a user/global skills dir), possibly composed with A/B/C for the non-skill content. Evaluate whether this is the cleanest clean-delta path where a host supports it, and how it degrades on hosts that do not.

## 5. Effect on current and prior releases (analyze explicitly)

- Migration and backward compatibility: what happens to a repo already installed the old (tracked) way if the user later chooses a low-footprint/clean-delta mode; and to an untracked/clean-delta repo on a normal upgrade.
- Re-installing the EXACT version already installed: should the installer warn, no-op silently, or reconcile? Today without a manifest it is effectively a no-op; WITH the manifest we can detect it. Recommend the behavior and what the user should see.
- Keeping a future "revert to an older aw version" POSSIBLE without building revert now: we do not want to build revert, but we cannot undelete later, so we must not foreclose it. Evaluate the minimum the manifest/backups should record to preserve that option: e.g. a per-file `installed_version` stamp, and/or the install commit id, and/or relying on the timestamped file backups (the files are tiny). We do not expect hundreds of installs. Recommend the SIMPLEST record that keeps clean uninstall + reversion feasible, and say when backups alone suffice versus when a per-file version/commit stamp earns its keep.

## 6. Deliverables (in the report)

1. A crisp restatement of the goals, with any you would drop or reframe and why.
2. A recommended architecture (possibly a small composition of mechanisms) and an END-TO-END walkthrough of the clean-delta PR case: install, use, keep the developer's artifacts tracked elsewhere, produce a PR with zero aw footprint, and cleanly uninstall.
3. A full COST / BENEFIT / RISK table per candidate mechanism (A-F and any you add), including host-discovery dependency and the proof required. For F, incorporate the Section 3a skills analysis (which hosts, which subset of our workflows, replace vs complement, and the clean-delta footprint of a `SKILL.md`).
4. Your Section 5 analysis (migration, re-install-same-version, revert-preservation) with concrete recommendations.
5. Recommendations on the open design questions: where a per-repo choice is recorded (a per-repo section in the global config, vs the per-repo manifest, vs filesystem-only via the exclude file); whether the choice is materialized as a committed artifact or kept purely local (and the collaborator-visibility tradeoff); interactive vs flag-driven selection (`--clean-delta` / `--no-track` / `--deep`); and whether any PRIOR choice (tracked-by-default manifest, in-repo shims, the `AGENTS.md` pointer) should be revisited.
6. A phased plan: what is safe to build first, what must wait on per-host discovery evidence, and what to defer or not build at all.
7. Open questions and the specific evidence needed to close each.

Justify every recommendation against the constraints in Sections 1 and 3. Prefer concrete mechanisms over abstractions, and call out anywhere our existing design is working against these goals. Return the whole report as one downloadable `.md` file.
