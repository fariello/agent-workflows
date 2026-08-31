---
id: q65sz3
created: 20260831
set: cross-platform-agent-write-confinement
order: 00
topic: [agent execution isolation]
model:
kind: research-prompt
status: todo
outcome: none-yet
summary: How to confine a coding agent's writes to one directory on macOS, Windows and Linux without a container
consumed-by: []
priority: high
---

# Research request: confining a coding agent's file writes to one directory, on macOS, Windows and Linux

You are being asked to research and compare the available mechanisms for **confining a
child process's filesystem writes to a single directory subtree**, on **macOS, Windows and
Linux**, from an **unprivileged** parent process, **without** requiring a container runtime,
a virtual machine, or administrator/root rights.

Return your answer as a **downloadable markdown (`.md`) file**.

## The codebase in question is public: read it rather than trusting this summary

The toolkit described below is open source and you may fetch and read it:

    https://github.com/fariello/agent-workflows

The Linux-only implementation this request asks you to extend is real code in that repository,
principally `agent_workflows/host_sandbox_profile.py` (the sandbox ladder and its probes) and
`agent_workflows/oc_runipd.py` (the driver that allocates the worktree and launches the worker).
Prefer reading those files over relying on the prose here: this summary is lossy by construction and
will date. Where your recommendation touches how the toolkit behaves today, cite the actual file and
line rather than paraphrasing this document.

## The concrete situation

A Python program (the "driver") orchestrates an AI coding agent (the "worker") to make code
changes in a git repository. The driver:

1. Creates a **git worktree** (a second, independent checkout of the same repository on its
   own branch) at a path such as `<repo>/.aw/worktrees/<id>/`.
2. Launches the worker as a **child process** (a CLI tool), with that worktree as its
   working directory, passing the directory both as `cwd` and as an explicit
   `--dir <path>` argument.
3. Expects the worker to edit, test and commit **only inside that worktree**, so the
   driver can review the branch and merge it back.

**The observed failure.** The worker did not stay in the worktree. It read files via
relative paths that climbed out (`../../../SOMEFILE.md`) and then committed 18 files
directly into the main checkout. The worktree branch ended with zero commits. Nothing
prevented this, because the working directory is a *default*, not a *boundary*: any process
can `open()` an absolute path, or walk upward with `..`, whenever it likes.

The worker is:

- a **same-user** process (same UID as the driver), not a hostile actor, but an unreliable
  one: it may forget, misread instructions, or reason its way into a path outside its lane;
- capable of running **arbitrary shell commands**, so any confinement that depends on the
  worker's own cooperation (instructions, wrapper functions, linting its tool calls) can be
  bypassed by shelling out;
- a **third-party binary** the driver does not control and cannot patch.

So instructing the worker is necessary but provably insufficient. We want the operating
system, or some other externally-imposed mechanism, to make writes outside the lane
**fail**.

## What already exists in our implementation (so you do not re-derive it)

We have a working Linux-only implementation with these properties, and it is the quality bar
for anything you propose:

- A **ladder of mechanisms**, each selected by an **executed probe** rather than by
  inspecting a version number or checking whether a binary exists.
- Rung 1 is **Landlock** (a Linux kernel LSM, unprivileged, restrictions inherited by every
  descendant process). Rung 2 is **bubblewrap** with `--unshare-user`. A bare user namespace
  (`unshare -Umr`) was **rejected as a rung** because it restricts no path and therefore
  cannot enforce the partition.
- **Every probe must prove a denial, not a launch.** A probe passes only if a real jail was
  constructed AND the kernel actually **refused** a write outside the allowed root while
  **permitting** one inside it. "The launcher exited 0" is deliberately insufficient,
  because a misconfigured jail (for example binding `/` read-write instead of read-only)
  starts perfectly cleanly and enforces nothing.
- **Fail closed, never silently degrade.** If the requested confinement cannot be proven on
  this host, the run refuses rather than proceeding with a weaker guarantee.
- The partition we need: the **lane worktree** and a small **scratch directory** are
  writable; the **main checkout**, **sibling lanes**, and the **git common directory** are
  readable but not writable; the toolchain and dependencies are readable.
- We learned the hard way that capability detection must be **probed, not inferred**: on one
  development host every signal said "sandbox available" (both `unshare` and `bwrap`
  installed, unprivileged user namespaces enabled, a large `max_user_namespaces`), yet both
  actually failed at runtime with `Operation not permitted` writing `/proc/self/uid_map`.

**The gap: this is Linux-only.** macOS support is a hard requirement for us (a large share
of the developers in this space use macOS). Windows is very nearly as important. We
currently have **nothing** for either.

## What we need from you

Please cover all of the following. Where the answer is "there is no good option", say so
plainly; a well-evidenced negative result is a useful result and we would rather have it
than an optimistic one.

### 1. Per-platform mechanism inventory

For **macOS**, **Windows** and **Linux**, enumerate the realistic mechanisms for confining a
child process's writes to a subtree. For each, state:

- the exact API, command or facility, with its real name;
- whether it works **unprivileged** (no `sudo`, no admin elevation, no developer-mode
  toggle, no prior system configuration);
- whether restrictions are **inherited by descendants** (our worker spawns its own children,
  including shells and test runners, so a boundary that a child can escape is worthless);
- whether it can express **"this subtree writable, that subtree read-only but readable"**,
  as opposed to only all-or-nothing access;
- how a violation **presents** to the confined process (which errno or exception, and
  whether it is distinguishable from an ordinary permission error);
- its **stability and support status**, including whether it is deprecated, undocumented, or
  liable to change between OS releases;
- the **minimum OS version** required.

For macOS specifically, we are aware of `sandbox-exec` (and the underlying Seatbelt
`sandbox_init`) and that Apple has marked it deprecated for a long time while continuing to
ship it. We need a clear-eyed assessment: does it still work on current macOS, can an
unprivileged process use it to allow-list one writable subtree, does the restriction survive
into grandchildren, and what breaks in practice (code signing, notarization, SIP
interactions, Rosetta, Homebrew toolchains, `xcrun`)? If `sandbox-exec` is a dead end, say
so and explain what remains, including App Sandbox entitlements, Endpoint Security, or
`chroot`-style approaches and why they do or do not apply to an unprivileged CLI parent.

For Windows specifically, please assess at minimum: restricted/AppContainer tokens
(`CreateProcessAsUserW` with a capability SID set), Job Objects (what they do and do not
restrict, since we believe they govern process and resource limits rather than filesystem
paths), Windows Sandbox (which we suspect needs Pro/Enterprise and is closer to a VM),
Mandatory Integrity Control levels, filesystem ACL manipulation on a per-run basis, and
whether a **separate low-privilege local user account** plus ACLs is the pragmatic answer.
Note whether any of these require admin rights to set up even once.

### 2. Cross-platform strategies that avoid OS confinement altogether

Independently of the OS mechanisms, evaluate designs that sidestep the problem. For each,
give the failure modes and the real cost, not just the happy path:

- **A separate clone instead of a git worktree.** A worktree shares the `.git` directory with
  the main checkout, which is part of why path confusion occurs. A full clone has no shared
  common directory, so the worker cannot reach the main checkout through git plumbing. Cost:
  disk, clone time, and a push-back step. Does this actually remove the failure class, or
  merely make it less likely?
- **Copy-out / copy-back.** Give the worker a copy of the tree in a temporary location that
  contains no path back to the original, then apply the resulting diff. What breaks
  (absolute paths in build artifacts, tooling that resolves the repository root, git
  history, submodules)?
- **A per-run user account.** Run the worker as a different local user that simply lacks
  write permission to the main checkout. This is the classic UNIX answer and works on all
  three platforms in some form. What does it cost operationally, and does it need one-time
  admin setup?
- **Filesystem-level tricks**: read-only bind mounts, a read-only loopback or disk image
  containing the main checkout, per-run ACL changes, or making the main checkout read-only
  for the duration of the run. Are any of these safe with concurrent readers, and reversible
  after a crash?
- **Detect-and-refuse instead of prevent.** Rather than blocking the write, snapshot the
  main checkout before the run and verify afterwards that it is byte-identical, quarantining
  and reverting if not. This converts silent corruption into a loud failure. What are the
  race conditions when a human or another agent is legitimately working in the main checkout
  at the same time?
- **Tool-layer permission systems.** Some agent CLIs support their own allow/deny rules for
  file and shell tools. Assess this class honestly: how much protection does it give when the
  worker can invoke a shell?

### 3. Comparison and recommendation

Produce a table comparing every candidate across: platforms covered, privilege required,
inheritance by descendants, expressiveness (writable-vs-readable partitioning), failure mode
on violation, implementation effort, operational cost, and how it can be **probed** for at
runtime.

Then recommend a concrete design. We would prefer either:

- **one mechanism that works acceptably on all three platforms**, even if weaker than the
  best per-platform option, because a single code path is far easier to keep correct; or
- **a ladder with a per-platform rung and one honest universal fallback**, provided each rung
  is independently probeable and the fallback's weaker guarantee is stated in the tool's own
  output rather than assumed.

State clearly which of those two you recommend and why.

### 4. Honesty requirements

- Distinguish **what you verified** from **what you believe**. If you did not or could not
  execute something, say so; do not present documentation as a test result.
- Prefer primary sources (official documentation, source code, release notes) and cite them.
  Where sources conflict or are ambiguous, say so rather than picking one silently.
- Call out mechanisms that **appear** to work but do not enforce anything, since that is the
  most dangerous outcome for us: a jail that starts cleanly and confines nothing is worse
  than no jail, because the operator is told the run is isolated.
- Note anything that would **break normal development work** if enabled by default: build
  caches outside the tree, global package directories, credential and config files in the
  home directory, temporary directories, network access.
- If a mechanism cannot express "readable but not writable", say what the practical
  consequence is, since our worker legitimately needs to READ repository-wide context such
  as decision logs and sibling documentation.

### 5. Deliverable

A single downloadable `.md` file containing:

1. a short executive summary with your recommendation stated up front;
2. the per-platform inventory (section 1);
3. the cross-platform strategies (section 2);
4. the comparison table and recommendation (section 3);
5. a "what I verified versus what I inferred" section;
6. minimum viable implementation sketches for your top two candidates, at the level of
   which API or command to call and in what order, including how to probe for support and
   how to prove a denial;
7. open questions you could not resolve, and what evidence would settle each.

Keep the whole document self-contained: assume the reader has the situation described above
and nothing else.
