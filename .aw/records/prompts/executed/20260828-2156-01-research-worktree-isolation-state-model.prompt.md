<!-- aw-prompt: Kind: research | Status: pending | Created: 2026-08-28 | Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us) | Targets: GPT-5.6 | Concerns: worktree-isolation state/artifact model for a multi-agent IPD runner | Results-go-to: FILED under .aw/records/research/worktree-isolation-state-model/ once completed. This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
You are a senior systems architect specializing in developer tooling, multi-agent orchestration, and git internals. Your task is to determine the best architecture for isolating concurrent AI-agent code-execution "lanes" in a repository while keeping per-machine tool state coherent. Optimize your recommendation for, in priority order: (1) simplicity and low maintenance burden, (2) architectural cleanliness and clear ownership boundaries, (3) robustness against silent failure and concurrency hazards, (4) portability. Reason from first principles and search the full solution space; do not anchor on the options I list.

# Background (what I am building)

I maintain a CLI tool (call it `aw`) that drives AI coding agents to execute structured plan documents (IPDs) in a git repository. A "driver" process runs a queue of plans. For each plan it launches a headless AI agent (an `opencode`/`agy` subprocess) to do the coding work, then finalizes the plan through a gated lifecycle.

To let multiple plans run concurrently without clobbering each other's working files, the driver was recently changed to run each plan in its own **git worktree**: it runs `git worktree add -b aw/lane/<id> .aw/worktrees/<id> <mainHEAD>`, launches the agent with its working directory set to that worktree, and on success merges the lane branch back to the main working tree, then removes the worktree.

## The problem I discovered

The tool keeps **per-machine, gitignored state and artifacts** in the repo, which the worktree model breaks:

- `.aw/state/` — runtime state: lifecycle "begin receipts" (`.aw/state/ipd-lifecycle/<id>.receipt.json`, an execution-authority token written by `aw ipd begin` and validated by `aw ipd finalize`), migration journals, etc. **Gitignored.**
- `.aw/records/runs/<run-id>/` — the run directory: the run ledger/manifest, a per-lane `driver.lock`, per-plan outcome JSON the agent must write, a decisions register, an execution report. **Gitignored.**
- `.aw/worktrees/` — where the lane worktrees themselves live. **Gitignored.**

Because these are gitignored, `git worktree add` does **not** populate them into the lane: a lane worktree is a checkout of *tracked files only*. This produces two concrete failures:

1. **State forks silently.** When the driver-spawned agent (cwd = the lane worktree) itself runs `aw` (e.g. `aw ipd begin`/`aw ipd finalize`, or any command that reads/writes `.aw/state` or the run dir), that inner `aw` resolves its state root relative to its cwd — the *worktree* — so it writes to `.aw/worktrees/<id>/.aw/state/...` and `.aw/worktrees/<id>/.aw/records/runs/...`. These are **different files** from the real ones at the main repo root. The driver (running from main) then can't find the begin receipt the agent wrote, finalize fails, and anything the inner `aw` wrote in the lane is **destroyed on worktree teardown**. It is invisible to `git status` (gitignored) and to the branch diff (never merged), so it fails silently.

2. **Permission deadlock.** The headless agent is launched non-interactively (`--auto`, no TTY). The driver's prompt instructs the agent to write its outcome JSON / decisions / report to run-dir paths that live under the **main** repo (outside the lane). The agent tool (`opencode`) has an `external_directory` permission gate; the first access to a path outside its working directory triggers an approval **prompt**, which in a non-interactive run has no answerer, so the agent turn **hangs forever** (confirmed from logs: the turn blocked on the permission prompt, zero progress for minutes). A watchdog/timeout is clearly needed as a backstop regardless of the chosen design.

## The core design tension

Two needs conflict:
- **Isolation** wants each lane's *product code changes* confined to its worktree/branch and merged back cleanly, with no cross-lane interference.
- **Per-machine tool state** (`.aw/state/`, the run dir/ledger/receipts) is single-source-of-truth on this machine, gitignored, and must **not** fork per lane. The driver and any inner `aw` must agree on ONE state location. Some of it is single-writer (the run ledger/manifest, the driver lock); some is per-plan (the agent's outcome JSON, that plan's begin receipt).

The central question is: **which `aw` state is single-source machine-state (must resolve to one location shared across lanes) versus per-lane work (must be isolated and reconciled), and what mechanism enforces that split so that (a) an inner `aw` invoked inside a lane always resolves machine-state to the intended place, (b) product code still merges back cleanly, (c) nothing forks or is silently destroyed, and (d) the non-interactive agent never trips a permission prompt it cannot answer?**

# Candidate directions I have sketched (evaluate, improve, or reject; add your own)

- **A. Symlink set:** after `git worktree add`, symlink the lane's gitignored state dirs (`.aw/state`, the run dir) back to the main repo's. Concern: incomplete-set maintenance burden; symlinks still resolve to a main abspath so the permission gate may still fire; concurrent lanes symlinked to one `.aw/state` reintroduce shared-writer races; `.aw/worktrees` must not be linked (loop); Windows.
- **B. Env-pinned absolute state root:** pass an absolute `AW_STATE_ROOT`/run-dir (pointing at main) into the lane's environment so every `aw` resolves machine-state to one location regardless of cwd. Requires `aw` to honor the override at every state-path resolution site; permission gate still fires on the abspath.
- **C. Per-lane state, harvested/reconciled:** each lane writes its own state locally; the driver harvests and reconciles into main on integration. True isolation, no shared-writer races, but the largest change and forces the single-source-vs-per-lane classification.
- **D. Isolate via full clone / overlay / bind-mount instead of git worktree:** a self-contained clone (or an overlayfs/bind-mount) makes the inner `aw` naturally self-consistent and includes the gitignored state locally; harvest results back. Heavier (disk, time), but sidesteps the gitignored-not-in-worktree problem.
- **E. Abandon worktree isolation; isolate in the main tree via per-lane scratch + strict path leases/guards.** No cross-boundary state problem, but returns to working-tree contention.
- **F. Driver owns ALL `aw`/lifecycle state operations; the agent only edits product code in the lane and never runs `aw` or writes the run dir.** Removes inner-`aw`-in-lane entirely; big change to the agent contract.
- **G. Hybrid:** worktree for product code + a state-pinning mechanism (A or B) for single-source state + a watchdog for the permission gate.

# The core questions to answer

1. **Classification.** Give a principled taxonomy of the state an orchestration tool like this keeps, and classify each class as SINGLE-SOURCE machine-state (shared across lanes), SINGLE-WRITER driver-state, or PER-LANE agent work. Where do begin-receipts, the run ledger/manifest, the driver lock, per-plan outcome JSON, decisions/report, and lifecycle journals fall, and why?

2. **Best mechanism.** Given that taxonomy, what is the cleanest mechanism to make an inner `aw` (running with cwd inside a lane worktree) resolve each state class to the correct location — an environment-pinned root, XDG-style state dir outside the repo entirely, a passed-down config, a state-resolution rule keyed off "am I inside a lane?", or something else? Compare env-var vs. out-of-repo state dir vs. symlink vs. bind-mount vs. clone on the four optimization axes. State the single recommended design and the runner-up.

3. **Where should tool state even live?** Should per-machine runtime state (`.aw/state`, run dirs) live *inside the repo* at all? Evaluate moving it to an out-of-repo per-repo location (e.g. an XDG state dir keyed by repo identity) so worktrees never see it and it never forks. Trade-offs vs. keeping it in-repo-but-gitignored. This may dissolve the whole problem — assess honestly.

4. **The isolation substrate.** Is `git worktree` the right isolation primitive here, versus a full/`--shared` clone, `git worktree` plus a deliberately-populated ignored-file set, an overlay/bind-mount, or a container? Compare on setup cost, self-consistency of an inner tool invocation, merge-back ergonomics, disk, and portability.

5. **Merge-back and cross-lane dependencies.** With product edits on `aw/lane/<id>` branches, how should results integrate to main, and how should a lane that depends on another lane's *result* (a plan B needing plan A's committed output) obtain it — branch from main, branch from A's tip, or a staged merge order? Note conflict and stale-base handling.

6. **The permission-prompt deadlock.** Independently of the state design, how should a non-interactive headless agent turn avoid an unanswerable-permission-prompt hang: pre-scoped grants, an auto-deny-in-non-interactive policy, a no-progress watchdog/timeout, or keeping all agent I/O strictly inside its sandbox so no gate ever fires? Recommend the layered defense.

7. **Failure-mode audit.** For your recommended design, enumerate the silent-failure and concurrency hazards (forked state, lost-on-teardown artifacts, receipt/ledger divergence, partial merges, orphaned worktrees/locks after a crash) and the specific guard that closes each. What must be true for a crashed or killed lane to be recoverable and never leave the machine in an ambiguous state?

8. **Migration.** Sketch the smallest incremental path from the current "git worktree, in-repo gitignored state" implementation to your recommendation, noting what stays backward-compatible.

# Rules for your report

- Reason from first principles; search the full solution space and propose options I did not list if they are better. Do not merely rank A–G.
- Be concrete and implementation-level: name the exact mechanism (env var, path, git command, config key), not generalities.
- Where behavior depends on a specific tool's semantics (git worktree and gitignored files, headless-agent permission models), state what is generally true across such tools versus what must be verified for a specific one, and cite official documentation with URLs and access dates for any nontrivial claim.
- Distinguish documented fact from your inference. If something is undecidable without seeing the code, say so and state what you would check.
- Prioritize simplicity and low maintenance burden; explicitly call out any option (like an incomplete symlink set that must be hand-synced as the tool evolves) that trades a working demo for a long-term maintenance headache, and say so plainly.

# Deliverable

Return your entire answer as a single DOWNLOADABLE markdown file named `worktree-isolation-state-model-research-report.md` (provide it as a downloadable `.md` file, not only inline), structured as:
1. Executive summary and the single recommended design (one paragraph + a labeled diagram or path layout).
2. State taxonomy and the single-source vs. per-lane classification table.
3. Mechanism comparison across the four optimization axes (table), with the recommendation and runner-up.
4. Isolation-substrate analysis (worktree vs. clone vs. overlay/bind-mount vs. container).
5. Merge-back and cross-lane dependency handling.
6. The permission-deadlock layered defense.
7. Failure-mode and concurrency hazard audit, each with its closing guard.
8. Incremental migration path from the current implementation.
9. Open questions / what you would verify in the code, and references with URLs and access dates.
