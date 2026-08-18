---
id: lc6898
created: 20260726
set: awdeliv
order: 03
topic: []
model: sonnet5
kind: research-report
status: reference
outcome: adopted
summary: Migrated from 20260726-awdeliv-03-lc6898-aw-delivery-and-clean-delta.sonnet5.research-report.md.
consumed-by: []
---
# Clean-Delta Contribution & Low-Footprint Install for agent-workflows
### A Principal-Architect Review

*Prepared as a rigorous, evidence-driven architecture review. Host-discovery claims below are backed by searches run July 26, 2026 against official/primary docs where available; every claim not directly evidenced is flagged as such, with the specific test that would settle it.*

---

## 1. Restating the goals — what to keep, drop, or reframe

| # | As stated | Verdict | Why |
|---|---|---|---|
| 1 | Clean-delta contribution | **Keep — this is the real product.** | It's the only need with an unambiguous, checkable success condition: `git status` and `git diff` against upstream show *zero* aw-owned files. Everything else in this report should be evaluated by whether it serves this case. |
| 2 | Do-not-advertise / low-footprint | **Fold into #1, don't build separately.** | This is clean-delta's mechanism minus the "must produce a PR" constraint. Any solution to #1 solves #2 for free; a separate code path for #2 would just be untested duplicate logic. Treat #2 as "clean-delta without the upstream-remote requirement" — same mechanism, no separate feature. |
| 3 | Per-class tracking opt-out | **Keep, but you already shipped it.** | The `local/` lane pattern in §1 *is* this feature for prompts/comms. The only real gap is plans/IPDs and docs, and the fix is mechanical: extend the same lane pattern, don't invent a new one. |
| 4 | Untrackable framework + manifest | **Keep as the superset — this is where the hard design work is.** | This is #1's actual precondition: you cannot get a clean upstream delta while the framework and manifest are tracked files in that repo. Needs #1 to work first. |

One reframe you should make explicit to yourselves: **"clean delta" and "low footprint" are not the same axis.** Clean-delta is a binary, verifiable property (upstream repo diff is empty except the developer's own code). Low-footprint is a spectrum (fewer files, smaller diffs, less visible tooling) that matters even when you're not producing a PR — e.g., a solo maintainer who just finds `.agents/` clutter annoying in their own repo. Don't conflate "I want zero footprint for a PR" with "I want less footprint generally"; the former has a hard bar (zero), the latter doesn't, and conflating them will pull you toward over-engineering the general case to hit a bar only the specific case needs.

A premise worth challenging directly: **the manifest's `installed_version` and tracked-by-default posture were reasonable defaults for the single-owner-repo case you built for, and they are actively working against you for clean-delta.** A manifest that is itself a tracked file is pollution in the PR case by definition — no amount of clever design around it changes that; it must either not exist in-repo, or exist somewhere the upstream repo never sees. This isn't a new insight so much as the direct consequence of goal #1, but it's worth saying plainly: **the "tracked-by-default manifest" decision from Section 1 should be revisited, not preserved as a constraint you design around.**

---

## 2. Recommended architecture

### 2.1 The core move: split "framework + manifest" from "developer's own artifacts," and give each its own tracking home

- **Framework files, shims, manifest** → **not tracked in the target repo at all.** They live on disk (so hosts can find them) but are known to git only via `.git/info/exclude` (never the tracked `.gitignore`). This is Candidate A from your list, and it is the right default for clean-delta — not because it's clever, but because it's the *only* candidate that doesn't depend on unproven host behavior (see §3 below on why B/C are conditional, not default).
- **Developer's own artifacts** (IPDs, prompts, research, run records) → **a sibling directory outside the repo, in its own git repo the developer controls** (Candidate B's sibling-repo idea, but applied only to the developer's content, not the framework). This isn't "depends on host resolve-and-follow of out-of-repo content" in the risky sense, because the *host doesn't need to follow anything there* — the developer's artifacts are for the developer's own reference and versioning, not for agent discovery. Only the framework/pointer side has a discovery dependency.

This split matters because it cleanly separates a *proven, low-risk* need (versioning your own notes outside a repo you don't own — this is just "have a git repo," nothing host-dependent) from an *unproven, host-dependent* need (getting the agent to find and follow instructions that live outside the repo). Bundling them, as candidate B does if applied wholesale, needlessly makes the safe part depend on the risky part.

### 2.2 Discovery: skills first, locally-excluded shim second, converged pointer never

Section 3a's research changes the recommendation from what a conservative reading of "outside-repo resolve-and-follow is unproven" would suggest. Here is the load-bearing finding:

**Every host surveyed that has documented skill support also documents a *global/user-scope* skills directory, entirely outside any repo, that is discovered with no pointer, no shim, and nothing tracked in the target repo:**

| Host | Project-scope skill path (would need in-repo or excluded file) | User/global-scope skill path (fully outside repo) | Source |
|---|---|---|---|
| Claude Code | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` | Claude Code docs (code.claude.com/docs/en/skills); Claude Platform docs |
| OpenCode | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` (walks up to git worktree root) | `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/` | opencode.ai/docs/skills |
| Codex CLI | `.agents/skills/<name>/SKILL.md` in repo | `~/.codex/skills/` (also documented as `~/.codex/agents/` in one source — treat as **unproven/inconsistent**, see caveat below) | Multiple third-party guides agree on `.agents/skills/`; global path is less consistently documented — **needs verification against OpenAI's own docs, not just secondary sources** |
| Cursor | `.cursor/skills/<name>/SKILL.md` or `.agents/skills/` (discovered in nested dirs too) | `~/.cursor/skills/<name>/SKILL.md` | cursor.com/docs/skills.md (official) |
| GitHub Copilot (VS Code / CLI / cloud agent) | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | **Not documented as having a global/user-scope directory** — Copilot's skill model in the sources found is project-scoped (committed to the repo, "whole team benefits") | code.visualstudio.com/docs/agent-customization/agent-skills (official); docs.github.com (official) |
| Gemini CLI | `.gemini/skills/` or `.agents/skills/` alias | `~/.gemini/skills/` or `~/.agents/skills/` alias | github.com/google-gemini/gemini-cli/docs (official, primary source) |
| Antigravity | `.agents/skills/<name>/SKILL.md`, project-scoped | User/global scope is asserted by a third-party guide but **not confirmed in Antigravity's own docs pages found** (antigravity.google/docs/skills and /docs/ide/skills describe project-scope only) — **unproven, flag for verification** |

Two hosts in your list — I found no documentation of skill support at all for what you called "Codex" as a distinct case (it's covered above) — and I did not find Agent Skills documentation for a plain "GitHub/VS Code Copilot" split from the "GitHub Copilot" entry above; treat that as one row.

**This is the cleanest zero-footprint discovery path where it holds, for one reason that matters a lot: it is not a `.gitignore`-adjacent trick at all.** A global skills directory under `~/` is never inside the target repo's working tree, so there is no git-ignore interaction, no `.git/info/exclude` maintenance, and no risk of the host's own gitignore-respecting behavior suppressing it (see the critical caveat in §3 below — this is precisely the failure mode that undermines the locally-excluded-shim approach on at least two hosts).

**But it only replaces *discovery*, not *content ownership*, and it has a consent problem you must not wave away:** a global skills directory is shared across every repo the developer works in. If `agent-workflows`-authored skills land there, (a) they apply to repos that never asked for agent-workflows, and (b) an uninstall must not touch skills the developer or some other tool put there. This is exactly the "does the global case risk mutating a shared user skills directory without consent" question posed in §3a, and the honest answer is **yes, it's a real risk, and the fix is a strict manifest discipline**: agent-workflows must record, per global skill file it writes, an owned-artifact entry (same shape as your existing manifest rows) and must never delete or overwrite a same-named file it does not recognize as its own by hash. Global installs are opt-in and consent-gated per repo, not a silent side effect of running the installer once.

**Recommended composition (this is Candidate F composed with a reduced form of A), in priority order per host:**

1. **If the host supports global/user-scope skill discovery (Claude Code, OpenCode, Cursor, Gemini CLI — proven; Codex CLI and Antigravity — plausible but needs the host-specific verification noted below):** install the skill-eligible subset of workflows (see §2.3) into the user's global skills directory, gated behind explicit opt-in, manifest-tracked there. **Zero footprint on the target repo, full stop.** No `.git/info/exclude` entry needed for this content at all.
2. **For workflows that are not skill-shaped (see §2.3), and as the fallback for GitHub Copilot (no global scope found) or any host where global-skill discovery is unproven:** fall back to Candidate A — an in-repo, `.git/info/exclude`-excluded shim/pointer, written to disk but never committed. Accept the caveat below about gitignore-respecting agents.
3. **Never** rely on modifying the target repo's tracked `AGENTS.md`/`.gitignore` for the clean-delta case. That's non-negotiable given the goal, not a candidate to weigh.

### 2.3 Which workflows fit the skills model

Per your own taxonomy: **on-demand capability workflows (release-review, plan-review, verify, scaffold, spec) are a good fit — they're exactly what a `SKILL.md`'s "description triggers on task match, body loads on demand" model is built for.** **Persona/assessor/dialogue runbooks (advise, assess) are a poor fit** — skills are activated by *task* pattern-matching against a description; a persona that's meant to be invoked deliberately and sustained across a conversation doesn't naturally trigger off "the user's prompt looks like X." Forcing these into skill descriptions either produces false-positive triggering (the persona hijacks unrelated requests that superficially match keywords) or a description so vague it never triggers at all. **Recommendation: ship the capability subset as skills; keep the persona/dialogue subset on the existing shim/command model** (`.claude/commands/`, `.opencode/commands/`), which is explicit-invocation by design and doesn't have this mismatch. Skills **complement**, they don't **replace**, the shim model — and this is itself a reason the shim/pointer path in §2.2 step 2 isn't just a fallback, it's a permanent second track for the persona workflows regardless of skill support.

Format portability: every host surveyed uses the same core `SKILL.md` shape (YAML frontmatter with `name` + `description`, then markdown body), described repeatedly as following "the open Agent Skills standard" (agentskills.io). A skill written with only the standard frontmatter fields is broadly portable; host-specific extensions (Codex's optional `openai.yaml` for UI metadata, Claude Code's `context`/`disable-model-invocation`/tool-restriction fields) are additive and are documented to be ignored by hosts that don't recognize them, not treated as errors — so a single skill body can serve multiple hosts as long as you don't lean on host-specific frontmatter for correctness.

### 2.4 End-to-end walkthrough: the clean-delta PR case

1. **Setup (once, outside any target repo):** developer runs `agent-workflows install --clean-delta` in `opencode` (a repo they don't own). The installer:
 - Detects no prior aw manifest in-repo.
 - Prompts (or reads a `--global-skills` flag) for whether to also install skill-eligible workflows into the developer's global skills directories (`~/.claude/skills/`, `~/.opencode`-equivalent, etc.) — **consent-gated, once per machine, not per repo**, since it's a global resource.
 - Writes the capability-class workflow bodies as `SKILL.md` files under the developer's global skills dirs (if opted in), recording each in a **new global manifest** at e.g. `~/.config/agent-workflows/global-skills-manifest.json` (see §5.2 on why this needs its own record, separate from the per-repo manifest).
 - For the persona/dialogue workflows (and as the fallback for hosts without global-skill support), writes shim files into `.claude/commands/`, `.opencode/commands/`, etc. **inside the `opencode` working tree**, and adds each path to `.git/info/exclude` in that same working tree.
 - Writes the per-repo manifest to `.agents/agent-workflows/managed-sections.json` **inside the working tree**, and adds *that path too* to `.git/info/exclude`.
 - Does **not** touch `opencode`'s own `AGENTS.md`.
 - Creates (or points at) a sibling directory, e.g. `../opencode.aw/`, which the developer initializes as their own git repo, for IPDs/prompts/research/run records. Nothing here is git-related to `opencode` itself — it's just "put your notes in a folder you version separately."
2. **Use:** the developer works in `opencode` normally. Claude Code / OpenCode / Cursor find the global skills (proven) and the locally-excluded shims (present on disk, `git status` in `opencode` shows nothing because `.git/info/exclude` is honored by git itself — this part is 100% certain, it's core git behavior, not a host-dependent claim). **Caveat carried forward from discovery evidence below: whether the *host itself* additionally consults `.gitignore`/`.git/info/exclude` and therefore fails to proactively surface the excluded shim is a real, host-specific risk — see §3.**
3. **Artifacts:** plans, prompts, research produced during the session are written to the sibling `../opencode.aw/` repo (or its own gitignored lanes, mirroring the existing `local/` pattern), never into `opencode`'s tree.
4. **PR:** developer runs `git status`, `git diff` against upstream — sees only their code changes, because every aw file is either (a) in a directory `git` was told to ignore via `.git/info/exclude`, which is local-only and never shows up in `git diff`/`git status`/`git add -A` by construction, or (b) not in the `opencode` tree at all (global skills, sibling repo). They open the PR. **Zero aw footprint is structurally guaranteed by git's own ignore semantics for path (a), and by physical absence for path (b) — this part of the design does not depend on any host behavior, only on git, which is a solved, well-understood mechanism.**
5. **Uninstall:** `agent-workflows uninstall` reads the per-repo manifest (still readable — it's on disk, just excluded from git), removes owned shim files and the `.git/info/exclude` entries it added, removes the manifest itself last. If global skills were installed, a separate `--purge-global` step (never automatic) removes only the entries recorded in the global manifest, leaving any skills the developer or other tooling placed in the same directories untouched.

---

## 3. The hard problem, confronted directly

### 3.1 Per-host discovery paths that don't require committing files — status

| Host | Locally-excluded in-repo shim (via `.git/info/exclude`) | Host-native global config | Skill-based discovery (in-repo, excludable) | Skill-based discovery (global, zero footprint) |
|---|---|---|---|---|
| Claude Code | Present-on-disk file is readable **if explicitly referenced/read**; but Claude Code is documented to exclude gitignored files from "general file awareness... unless explicitly requested" (GitHub issue #2305, describing current behavior) — **so a locally-excluded `CLAUDE.md`/shim will likely not be proactively discovered**, only followed if the developer or another mechanism explicitly points at it | `~/.claude/CLAUDE.md` exists as user-global instructions (per OpenCode's docs describing Claude Code compatibility) | `.claude/skills/` — proven, official | `~/.claude/skills/` — proven, official |
| OpenCode | Not directly evidenced either way in the sources found — **unproven, needs a direct test** | `~/.config/opencode/AGENTS.md` (global rules, proven, official) | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` — proven, official, and notably walks *up* from cwd to the git worktree root, so a skill placed above the repo root inside a monorepo-like layout is still found | `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/` — proven, official |
| Codex CLI | Not evidenced | `~/.codex/AGENTS.md` (global instructions, third-party but consistent across sources) | `.agents/skills/` in-repo — consistently reported across multiple sources, but **not confirmed against OpenAI's own primary docs in this pass** — treat as probable, not proven | Global skills path inconsistently named across sources (`~/.codex/skills/` vs `~/.codex/agents/`) — **unproven, resolve against OpenAI's official docs before relying on it** |
| GitHub/VS Code Copilot | Not evidenced; Copilot's model (per official VS Code and GitHub docs) is squarely project-scoped and committed — "Existing skills within the `.github/skills` directory... used automatically," framed around team-shared, tracked files | Content-exclusion is admin-configured via github.com org settings, not a developer-side global instructions file — **not a discovery mechanism, a suppression mechanism, and org-level not developer-level** | `.github/skills/`, `.claude/skills/`, `.agents/skills/` — proven, official (VS Code + GitHub docs both confirm) | **Not found in official docs.** Treat as **unsupported** until shown otherwise — this is the one host in your list where the clean, zero-footprint global path does not appear to exist |
| Cursor | `.cursor/`-prefixed content is subject to Cursor's own ignore-file handling: official docs state "Cursor automatically respects your `.gitignore` patterns" and that ignored files are "blocked from indexing and Agent" — **this directly implies a `.git/info/exclude`'d shim will be treated the same as a `.gitignore`'d one and will likely be blocked from Agent by default**, a serious caveat, not a footnote | Not clearly documented as a global instructions file distinct from skills | `.cursor/skills/` or `.agents/skills/`, including nested per-subdirectory scoping — proven, official | `~/.cursor/skills/` — proven, official |
| Gemini CLI | Not evidenced | Not applicable in the same shape — Gemini CLI's precedence model is built around the skill tiers directly (built-in → extension → user → workspace), documented officially | `.gemini/skills/` or `.agents/skills/` alias — proven, official, primary source | `~/.gemini/skills/` or `~/.agents/skills/` alias — proven, official, primary source |
| Antigravity | Not evidenced | Not evidenced as distinct from skills | `.agents/skills/` project-scope — proven, official (antigravity.google/docs) | Asserted by third-party guide (RuleSell) as "project scope vs. user-specific/global scope," but **Antigravity's own docs pages retrieved in this pass describe only project scope** — treat as **unproven**, verify directly before depending on it |

### 3.2 The critical finding that should change your design: gitignore-respecting hosts may not "see" a locally-excluded shim at all

This is the single most important piece of evidence from this research, and it cuts against the assumption embedded in your own framing of Candidate A ("present on disk, excluded from git via `.git/info/exclude`... so the host sees it but git does not"). That assumption is **not safely generalizable**:

- **Cursor's own documentation states plainly that ignored files — and this explicitly includes files matched by `.gitignore` patterns — are "blocked from indexing and Agent."** `.git/info/exclude` and the tracked `.gitignore` are both just inputs to git's ignore logic; git itself does not distinguish "committed ignore rule" from "local-only ignore rule" when answering "is this path ignored" (that's the whole point of `git check-ignore`, which treats both the same). If Cursor's ignore-respecting behavior is implemented by asking git (or an equivalent gitignore-pattern matcher) whether a path is ignored, a `.git/info/exclude` entry produces the identical answer to a `.gitignore` entry, and Cursor's Agent would be blocked from it exactly as if it were tracked-and-ignored. **This needs to be tested directly, not assumed** — the test is: add a file to `.git/info/exclude` only (no `.gitignore` entry), open the repo in Cursor, and check whether Agent can read/act on that file without an explicit override. But the *prior* — based on what Cursor documents about its own ignore-handling — should be that it fails, not that it works.
- **Claude Code's GitHub issue #2305 (a live, acknowledged feature request as of the search date) confirms current behavior excludes gitignored files from "general file awareness and reading (unless explicitly requested)."** The parenthetical matters: an explicit read (e.g., the developer or another workflow step tells Claude Code to `@`-read the exact path) still works even if the path is gitignored. So the locally-excluded shim is **not dead** for Claude Code, but it is **not passively discovered** either — it needs something to point at it explicitly, which is exactly the "unwieldy read-and-execute" pattern your requester already dislikes (see §3.3).
- This means: **for at least two of your seven target hosts, the mechanism you designed (`.git/info/exclude` + shim) is likely to under-perform your expectation of "host sees it, git doesn't"** — instead you get "neither git nor the host's default awareness sees it, only an explicit instruction does." That's a materially weaker discovery guarantee than the global-skills path, and it's exactly why **skills-first (§2.2) is not a nice-to-have, it's compensating for a real gap in the excluded-shim approach.**

**What would settle this, precisely, per host:** create a throwaway git repo; add a marker file to `.git/info/exclude` only; open the repo in each host's client; without any explicit `@`-mention/read instruction, ask a question whose correct answer requires the content of that file (e.g., "what does the special instruction file in this repo say"); record whether the host's response reflects the file's content. Repeat with the file additionally added to the tracked `.gitignore` to confirm the two ignore mechanisms behave identically (they should, since both feed the same git ignore-matching logic) — if they *don't* behave identically for some host, that's a more interesting and separately reportable finding.

### 3.3 Why the requester finds "read and execute X outside the repo" unwieldy, and whether skills fix it

The existing workaround (telling the agent, in-session, to read and execute an out-of-repo file) is unwieldy for three concrete reasons, not just vague friction:

1. **It's a per-session, per-conversation instruction** — nothing makes the host do it automatically at session start, so the developer re-types or re-pastes the pointer every time, which is exactly the manual overhead the shim mechanism was built to eliminate for the in-repo case.
2. **It doesn't compose with the shim-per-command pattern** — your existing shims give you `/plan-review`, `/scaffold`, etc. as first-class, discoverable commands. A single "read and execute this file" instruction is one undifferentiated blob; it can't cleanly expose N separate workflows the way N shim files do.
3. **It has no ownership/versioning story** — there's no manifest entry, no drift check, nothing recorded about what was read or when, because "read this file" isn't an installed artifact, it's an ad hoc instruction.

**Skills fix exactly these three problems** where they're discoverable: skill discovery happens automatically at session start (per the Gemini CLI and Claude Code docs, the host scans and injects skill name+description into context without being asked), each skill is a separately named, separately triggered unit, and — critically for your manifest — a skill file *is* a normal file on disk with normal content and a normal path, so it fits your existing "kind: file, sha256 of content" manifest schema without any new concept. **This is the single strongest argument for treating skills as more than an equal-weight alternative in your candidate table — for the hosts where global skill discovery is proven, it directly replaces the awkward mechanism the requester is already unhappy with, and it does so with a *stronger* discovery guarantee than the shim.**

### 3.4 `.git/info/exclude` vs `core.excludesFile`: limitations, and which to default to

- **`.git/info/exclude`** lives inside `.git/info/` — it is **per-clone**, not shared with collaborators, not versioned, and disappears if the developer deletes and re-clones. This is exactly right for the clean-delta case (you *want* it invisible to collaborators and to the PR), but it means every fresh clone needs the installer re-run to re-populate it — this is a feature, not a bug, for your use case, but document it as a consequence, not a surprise.
- **`core.excludesFile`** (commonly `~/.gitconfig` → `~/.config/git/ignore`) is **global to the developer's git config**, shared across every repo on their machine. This is the right home for patterns the developer wants excluded everywhere (e.g., their own `*.untracked.*` convention, if they want it repo-independent) but the **wrong** home for repo-specific paths, since it pollutes ignore behavior in repos that never installed agent-workflows.
- **Recommendation: default to `.git/info/exclude`, per-repo, written by the installer at install time.** Reserve `core.excludesFile` only for a developer's personal, cross-repo conventions they set up themselves — agent-workflows should not write to it, to avoid silently changing git behavior in repos it was never installed into.
- Both are, as your prompt notes, never committed — that's their entire value here, and it's unaffected by the §3.2 caveat (the caveat is about whether the *host* treats them the same as a tracked `.gitignore`, not about whether *git* does — git's own behavior is identical and certain for all three ignore-file types).

---

## 4. Candidate mechanisms — cost / benefit / risk

| Candidate | Fit to needs 1–4 | Footprint on target repo | Host-discovery dependency | Reversibility | Manifest/backup interaction |
|---|---|---|---|---|---|
| **A — In-repo, `.git/info/exclude`'d shim + manifest; artifacts to sibling location** | Strong fit for 1, 2, 4; adequate for 3 (sibling dir subsumes per-class opt-out) | **Zero tracked footprint** — files exist on disk, invisible to `git status`/`diff`/`add -A` | **Real risk, evidenced (§3.2):** at least Cursor and Claude Code may not proactively surface an excluded shim without an explicit read instruction | High — delete the excluded paths, remove the exclude entries, remove the manifest; nothing was ever committed so there's nothing to revert in git history | Manifest itself must also live outside git tracking (same exclude treatment) or it's pollution too — this is a change from the current design, not an addition to it |
| **B — Sibling mini-repo, pointer (or nothing) in target repo** | Strong fit for 1, 4; good for 2; adequate for 3 | **Zero footprint** if the pointer is itself excluded; some designs need *no* pointer at all if discovery is global-skill-based | **Depends entirely on host resolve-and-follow of out-of-repo content — unproven across the board**, and this is a stronger claim than A's (A only needs the host to read a file *on the same disk in the same working tree*; B needs the host to follow a *cross-directory* reference, which is a different and less-evidenced capability) | High, same reasoning as A | The sibling repo's own git history is a much better fit for the "revert to older version," "audit trail" needs in §5 than anything inside the target repo could ever be, since it's fully under the developer's control |
| **C — Home-dir/global framework install, referenced from the repo** | Strong fit for 1, 2, 4 *where global skill discovery is proven* (Claude Code, OpenCode, Cursor, Gemini CLI); weak/no fit for GitHub Copilot | **Zero footprint, and zero discovery dependency on the excluded-shim mechanism** — this is its main advantage over A | **Proven for 4 of 7 hosts (§3.1), probable for 2, unsupported for 1 (Copilot)** | High — global manifest tracks ownership, uninstall is scoped to owned entries only | **New requirement, not present today:** needs its own manifest, separate from the per-repo one, because it's not "per repo" at all — see §5.2 |
| **D — Per-class nested `.gitignore` opt-out (extend the `local/` pattern)** | Good fit for 3 only; doesn't solve 1 on its own (a nested `.gitignore` is still a change to the repo's ignore behavior *if the `.gitignore` itself is tracked* — and if it's a new untracked `.gitignore`, you're back to A's mechanism) | Low but nonzero if implemented as a tracked nested `.gitignore`; zero if the nested ignore file is itself handled via `.git/info/exclude` | None beyond what A already carries | High — this is the least risky candidate precisely because you already ship it | Already fits your manifest today (it's a "section" kind); trivial extension |
| **E — Status quo: document only, build nothing** | Fails 1, weakly serves 2/3 via existing patterns, fails 4 | N/A | N/A | N/A | N/A |
| **F — Host-native skills (`SKILL.md`), global-first, composed with A/D for non-skill content** | **Strongest overall fit across 1, 2, 4**, and folds 3 in naturally (skill-eligible workflows go to skills, everything else to the existing local-lane pattern) | **Zero, for the global-scope portion, on any host** | Proven for Claude Code, OpenCode, Cursor, Gemini CLI; probable-but-unverified for Codex CLI and Antigravity; **absent for GitHub Copilot**, which must fall back to A | High, if the ownership discipline in §2.2 is followed; **new risk if not**: a global skills directory is shared state across every repo and every tool, so sloppy tracking here is worse than sloppy tracking in a per-repo manifest | **Requires a new global manifest** (§5.2) and a hard rule: never overwrite/delete a same-named global skill file that doesn't hash-match what agent-workflows last wrote |

**Overall recommendation: F (global-first) composed with A (excluded in-repo shim, as fallback and for persona/dialogue workflows) and D (extended local-lane pattern for per-class opt-out), with B available as an *opt-in* upgrade for developers who want their own artifacts under real version control rather than just "a folder."** C is not a separate candidate in practice — it's F's mechanism, generalized past skills to cover framework files that aren't skill-shaped, and it inherits F's host-support gaps.

---

## 5. Effect on current and prior releases

### 5.1 Migration and backward compatibility

- **Tracked-install repo → later opts into low-footprint/clean-delta mode:** this is a real migration, not a toggle, because the files physically move from tracked to untracked (or to a different disk location entirely). The installer must: (1) read the existing manifest to know exactly which files it owns, (2) `git rm` the tracked copies (this is a real, visible commit the developer must make and push themselves — the tool should not do this silently), (3) re-write the same content to the new untracked location(s), (4) rewrite the manifest to reflect the new `kind`/location for each entry. **Recommend requiring an explicit `--migrate-to-clean-delta` flag with a dry-run preview**, because this changes the repo's tracked file set, which is exactly the kind of change your users in this scenario are trying to avoid making by accident.
- **Clean-delta/untracked repo → normal upgrade:** low risk, since nothing is tracked to conflict with. The installer just needs to know to write new/changed content to the *same* untracked/global locations it used before, which means the manifest's `kind` and `host`/location fields (already present per your Section 1 description) are sufficient — no new fields needed for this direction.

### 5.2 Re-installing the exact version already installed

**With the manifest (which you have), this should be a detected no-op, not a silent no-op and not a warning by default.** Recommend: compare `installed_version` (and, better, the per-file sha256 the manifest already records) against what would be written; if identical, print a one-line confirmation ("agent-workflows vX.Y already installed, no changes") and exit 0. Only warn if the manifest exists but is *inconsistent* with what's on disk (e.g., a file the manifest thinks it owns has different content than the manifest's recorded hash — someone edited an "owned" file, or a previous install was interrupted). That inconsistency case is the one worth a loud message; the pure re-install-same-version case is not.

**One new requirement this report surfaces that Section 1 didn't have to consider: with global skill installs (Candidate F), "already installed" must be checked per-machine, not per-repo**, since the same global skill file could be asked-for by five different repos' install runs. The global manifest should track this as a reference count or at least "installed by which repos," so uninstalling agent-workflows from one repo doesn't rip out a global skill still wanted by another — this is a real gap the current per-repo manifest schema has no analog for, and it needs a small schema addition (a `referenced_by: [repo_path, ...]` list per global entry), not a redesign.

### 5.3 Keeping revert possible without building it now

You already have the right instinct — don't build revert, but don't foreclose it. The minimum that keeps it feasible, in order of how much it costs to add:

1. **Timestamped file backups (already shipped) are sufficient for the *tracked-install* case** — you have the actual bytes of every prior version, going back 5 installs, and the files are tiny per your own description. Nothing more is needed there.
2. **For the untracked/clean-delta case, backups need to happen wherever the *live* content is written** — i.e., if a skill file lives in `~/.claude/skills/`, the backup-before-overwrite step needs to run there too, not just for in-repo paths. This is a mechanical extension of existing backup logic, not new design.
3. **A per-file `installed_version` stamp in the manifest is worth its keep specifically because backups alone don't tell you *which* backup corresponds to *which* released version** — without it, "revert to v1.3" means grepping timestamps and guessing; with it, it's a manifest lookup. Given you "don't expect hundreds of installs," this is a cheap field to carry and a real gap to leave open if you don't.
4. **Do not add an install-commit-id field.** For the clean-delta case specifically, there usually *is* no commit — the whole point is nothing gets committed. For the tracked case, the file backups already give you the actual content, which is strictly more useful than a commit id (a commit id requires the commit to still exist and be reachable; a backup file requires nothing but itself). Recommend dropping this idea rather than building it.

**Simplest sufficient record: keep the timestamped backups (extended to cover untracked write locations) plus a per-file `installed_version` stamp in the manifest. Skip the commit-id idea entirely.**

---

## 6. Open design questions — recommendations

- **Where is the per-repo choice recorded?** Recommend the **per-repo manifest**, not the global config and not filesystem-only-via-exclude-file. Reasoning: the manifest already exists, already has a place for exactly this kind of metadata, and — unlike the global config — travels with the developer's mental model of "this repo's install." A filesystem-only record (just "the exclude file has entries, infer the mode from that") is fragile: you can't distinguish "clean-delta mode, working as intended" from "someone manually edited the exclude file" without an explicit flag somewhere. Put one field, e.g. `"install_mode": "clean-delta" | "tracked"`, in the manifest.
- **Committed artifact or purely local?** **Purely local, and this is not a close call.** A materialized, committed "we're in clean-delta mode" marker is itself pollution in the exact repo where the whole point is zero pollution. It must live in the manifest, and the manifest itself must be untracked in clean-delta mode (per §2's core recommendation) — so the record and the untracked-ness are the same fact, not two separate decisions.
- **Interactive vs. flag-driven selection?** **Flag-driven for CI/scripting reproducibility (`--clean-delta`, `--no-track`, `--deep` or similar), with an interactive prompt as the *default* when no flag is given** — this matches how you've evidently designed other parts of the installer (conservative-by-default, explicit for anything destructive or hard-to-reverse). Don't make clean-delta the default even for repos the developer doesn't own; require them to ask for it, since silently *not* leaving a manifest behind if they expected one would be a worse surprise than the reverse.
- **Should tracked-by-default manifest, in-repo shims, or the `AGENTS.md` pointer be revisited?** **Yes, and this report has said why throughout, but to state it plainly once: tracked-by-default is the right default for the "I own this repo" case, and should stay the default there. It is not, and should not become, the default for the "I don't own this repo" case — clean-delta mode should invert every one of those three defaults (untracked manifest, excluded or global-only shims, untouched `AGENTS.md`) as a package, selected together via the single mode flag above, not toggled independently.** Independent toggles would let a user end up in an inconsistent state (e.g., untracked manifest but tracked shims), which defeats the whole point.

---

## 7. Phased plan

**Phase 1 — build now, no host-evidence dependency:**
- Extend the manifest schema: `install_mode` field, per-file `installed_version` stamp, `referenced_by` list for (future) global entries.
- Extend backups to cover non-in-repo write locations.
- Implement Candidate A cleanly: excluded shim + excluded manifest, sibling-directory artifact convention, `--clean-delta` flag with interactive fallback.
- Implement Candidate D's extension: per-class nested-ignore opt-out for plans/docs, mirroring the `local/` pattern you already have for prompts/comms.

**Phase 2 — build once host-skill-discovery evidence is confirmed (start with the direct tests in §3.2, then move to global-skill support):**
- Ship the skill-eligible workflow subset (§2.3) as `SKILL.md`, with a global-manifest-backed installer path, for the hosts already **proven** in this report (Claude Code, OpenCode, Cursor, Gemini CLI).
- Add the consent-gated, opt-in global-install flow and the reference-counted uninstall logic.

**Phase 3 — defer until specifically verified, don't build speculatively:**
- Codex CLI and Antigravity global-skill support (currently probable-not-proven — verify against primary docs before investing).
- Any GitHub Copilot low-footprint path — none was found; don't build a workaround until GitHub documents one, since the project-scoped, committed-by-design model may simply not have a zero-footprint answer for this host today.

**Do not build:** install-commit-id tracking (superseded by backups + version stamp); a separate "do-not-advertise" feature distinct from clean-delta (same mechanism); revert itself (out of scope per your own framing, and the above keeps it feasible without building it).

---

## 8. Open questions and the evidence needed to close each

1. **Does a `.git/info/exclude`-only file get proactively surfaced by Claude Code and Cursor, or only when explicitly read?** Evidence needed: the direct test described in §3.2 (marker file, exclude-only, no explicit read instruction, ask a question whose answer requires the file's content). This is the single highest-priority open question — it determines whether Candidate A works as designed or only works as a "referenceable but not proactive" fallback.
2. **What is Codex CLI's actual global skills path, per OpenAI's own documentation (not third-party guides)?** Sources here disagreed (`~/.codex/skills/` vs `~/.codex/agents/`); this needs to be resolved against `platform.openai.com`/OpenAI's Codex CLI docs directly before Phase 2 work targets Codex.
3. **Does Antigravity support a genuine user/global skills scope, or is it project-scope only as its own docs pages (retrieved here) suggest?** The one third-party source claiming global scope should be checked against Antigravity's changelog or a direct empirical test (place a skill in a claimed global path, open a project that never referenced it, see if it's discovered).
4. **Does GitHub Copilot have any zero-footprint discovery path at all** (global config, a personal-scope skills directory, anything not committed to the repo)? Every source found described `.github/skills/` as committed/team-shared by design; if that's a firm architectural choice on GitHub's side rather than a documentation gap, Copilot may be the one host where clean-delta simply cannot reach zero footprint via skills, and the fallback (excluded shim, with its own Cursor/Claude-style caveat unconfirmed either way for Copilot) is the only option. Evidence needed: direct outreach to GitHub docs/changelog for any "personal skills" or "local skills" feature, since the ecosystem is moving fast enough that this could change within the year.
5. **For OpenCode specifically, does an excluded (via `.git/info/exclude`) `AGENTS.md` or shim get read?** Not evidenced either way in this pass — worth the same direct test as #1, since OpenCode's rules-loading docs describe walking up directories for `AGENTS.md`/`CLAUDE.md` but don't state whether that walk consults gitignore state at all (unlike Cursor, which explicitly says it does).
