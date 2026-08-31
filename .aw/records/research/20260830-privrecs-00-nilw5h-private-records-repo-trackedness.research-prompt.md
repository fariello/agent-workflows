---
id: nilw5h
created: 20260830
set: privrecs
order: 00
topic: [storage, trackedness, privacy, records-backend, multi-machine]
model:
kind: research-prompt
status: todo
outcome: none-yet
summary: Originating prompt: when aw records live in a separate PRIVATE repo, which currently-untracked artifacts should become tracked by default, and which stay untracked for reasons a private repo does not dissolve.
consumed-by: []
---

# Originating prompt (upload-ready)

Reports for this set land in orders 01+; reconciliation in the highest order.

---

# Design task: should "private records repo" change what a developer toolkit tracks by default?

You are an expert in developer-tooling storage architecture, git ergonomics, and privacy-by-design. You
have web search. Return your ENTIRE answer as a single downloadable markdown (`.md`) file, with nothing
outside the file.

## The question in one paragraph

A toolkit called `aw` (agent-workflows) installs into a code repository and writes durable work records
(plans, specs, backlog, research, releases) plus a large amount of operational material (run logs, an
activity sidecar, session-handoff drafts, scratch prompts, inter-agent messages). A significant portion of
that material is deliberately git-IGNORED today. Reading the recorded reasons, they fall into at least two
very different families: some things are untracked because they are genuinely ephemeral or machine-bound
and have no durable value, and some are untracked ONLY because the repository they would land in is the
PROJECT's repository, which is often public, shared with collaborators, and permanently archived, so
maintainer-specific and machine-specific content there is pollution and a privacy leak. The second family
is contingent on WHERE the records live. The toolkit already supports putting records in a separate
directory or a separate repository. So: when a developer has deliberately configured a SEPARATE, PRIVATE
repository for their `aw` records, which of today's untracked things should become tracked by default, and
which should stay untracked because their reason survives the change? Design that policy.

## What already exists (facts; design against these, do not re-invent them)

### The storage model: two orthogonal axes, six physical classes

`DeliveryMode` is a closed enum: `tracked` (the project deliberately carries `aw` content in tracked
repository paths) and `clean-delta` (the target repo carries NO toolkit-owned tracked or baseline files;
host integrations are discovered through user-scope mechanisms).

`RecordsBackend` is a separate closed enum of exactly three values:

- `repository` -> records live at `<target>/.aw/records`, inside the project repo.
- `companion` -> records live in a separate directory bound to the target, which MAY be its own git repo.
- `home` -> records live under a per-user home store at `<AW_HOME>/projects/<project-id>/records`.

The two axes are deliberately orthogonal: delivery mode governs where `system`/`config`/`state` land, and
`records` is governed SOLELY by the records backend. One combination is forbidden and raises a security
error: `clean-delta` + `repository`.

The resolver returns SIX physical classes, not four: `system`, `config_project`, `config_local`,
`state_durable`, `state_runtime`, `records`. There is a `Placement` vocabulary describing where a class
sits and how git treats it: `target-tracked`, `target-ignored`, `home-untracked`, `companion-tracked`,
`companion-untracked`, `source-checkout`, `custom`. Each placement carries declared attributes for
containment, git policy, portability, durability, privacy, and clean-target.

Four presets combine them: `private-target`, `public-target-private-companion`, `completely-clean-target`,
`local-only`.

`DurabilityState` is a seven-value observable enum: `unversioned`, `local-git`, `unacknowledged-remote`,
`acknowledged-durable`, `repository-managed`, `unreachable`, `unknown`. A crucial honesty rule governs it:
a configured git remote alone is "a neutral observable fact"; the state only becomes
`acknowledged-durable` when the USER explicitly acknowledges it, recorded in a local file. The toolkit
"never creates remotes, commits code, or pushes data" without a separate explicit action, and never
promises that a repo or a remote is private.

### The enforced-untracked floor (a hard constraint on any answer)

Two of the six classes MUST be untracked in EVERY preset and every custom layout: `config_local` (the
per-machine binding file) and `state_runtime` (locks, transaction journals, staging, cache, tmp). This is
enforced in code in two independent places: a placement-combination validator refuses tracked placements
for those classes, and a git-policy validator raises a security error if either is actually tracked or
staged. So "put it in a private repo, therefore track everything" is already illegal for part of the tree.

### The full inventory of what is untracked today, and the recorded reason for each

The toolkit writes gitignore rules into three surfaces: a framework-owned `.aw/.gitignore`, optional
nested per-lane ignore files in the legacy layout, and exactly one managed block in the target's ROOT
`.gitignore`. A firm rule constrains it: the installer "does not silently edit user gitignores."

| What | Recorded reason (paraphrased from the in-tree comment) |
|---|---|
| `records/*/untracked/` (a glob, so every records type gets a lane) | "box-local, ephemeral quarantine lanes ... hold this machine's raw/WIP/routing content and are never committed; a human promotes a reviewed copy into a tracked bucket" |
| `records/runs/` (per-run driver state: queue state, session logs, prompts, outcomes, lock) | "box-local, ephemeral working material; never committed" and "not a tracked project artifact" |
| `records/history.jsonl` (append-only sidecar written on EVERY status write) | "a local activity log appended on every `aw` status write; local-only, never committed" |
| `setup-repo-needed.md` (post-install reminder marker) | "per-machine ... never committed and never travels with the repo" |
| `.aw/state/` (runtime scratch, migration journals, receipts, relocated backups) | "runtime state and per-machine local config are NEVER tracked ... all of which carry absolute machine paths and session detail" |
| `.aw/config/local.json` | "per-machine local overrides" (also in the enforced floor above) |
| `.aw/workflow-artifacts/` (run scratch for review/assess/verify workflows) | "holds local context, home paths, and session detail, so it MUST stay untracked" |
| `.aw/worktrees/` (per-lane git worktrees the coordinator allocates) | "must never be tracked (it holds a transient working tree, not durable records)" |
| `opencode-recovery/` (session-recovery transcripts) | "machine-local, may contain personal paths and session ids; never track" |
| comms `untracked/` (inbox, sent, archive, scheduled, acks) vs comms `shared/` (TRACKED) | "the directory you write to IS the privilege level: untracked = ephemeral/untracked, shared = durable/tracked" |
| prompts `untracked/` (quarantine lane, notably for session-handoff drafts) | the handoff workflow "captures RAW SESSION CONVERSATION" and the prompts tree is "otherwise a tracked, publicly-pushable area"; "'written but never auto-committed' relies on discipline and is one stray `git add -A` from a leak" |
| credential shapes (`*.pem`, `*.key`, `.netrc`, `.pypirc`, `credentials*.json`, ...) | "should never be committed" |
| the `aw:untracked` managed block: `*.untracked.*`, `*.untracked`, `**/*untracked*/` | a passive escape hatch, see below |

Two important non-members of that list:

- Backlog `parked/` is fully TRACKED. It is a VISIBILITY tier, not a trackedness tier: parked items are
  hidden from the default attention board and shown with `--all`. The stated reason is signal quality, and
  the design explicitly names the symmetric failure modes it is avoiding: omitting committed work from the
  attention view (false confidence) versus flooding it with every "maybe someday" idea (destroying the
  view's meaning).
- The prompts staging tree itself is TRACKED "(like plans), NOT gitignored like comms untracked/". Only its
  `untracked/` lane is ignored.

### The `aw:untracked` escape hatch, and why it is a different kind of thing

The one managed block in the target's root `.gitignore` exists because of a repeated real failure. Its
recorded origin: the maintainer "repeatedly hit a failure mode where sensitive IPDs/notes that should have
stayed local got committed, because a lifecycle directive (or an agent following one) pushed them into
the plans directory and a blanket `git add .` staged them. There was no passive, agent-obvious escape
hatch to keep a file OUT of git."

Its own comment body states its limits with unusual honesty: "This only affects files that are NOT already
tracked. Gitignoring a pattern does NOT untrack an already-committed file, and it does NOT remove a name
from history"; "'.gitignore' is advisory: `git add -f` bypasses it. 'Untracked by default' is the goal, not
an enforcement boundary"; and "DO NOT delete or narrow these patterns to 'clean up' the ignore file: they
are a deliberate safety mechanism."

Note that this mechanism is content-agnostic and USER-DRIVEN: it lets a human mark ANY file untracked by
naming it. It is a per-file override, not a per-class policy. Any policy you design must decide how it
interacts with a class-level default.

### The pollution reasons, stated as such

The sharpest recorded reasons are explicitly about polluting a PUBLIC project repo with
maintainer-specific content, not about the content lacking durable value.

The foundational decision came from a measured leak: this toolkit is a published package with a public
repo, and a sweep "found tracked files embedding the maintainer's local filesystem layout and identity:
absolute home-directory paths, local-checkout sibling-repo names (several private repos plus local clones
of external projects), a SECOND local account from the cross-user security test (its username, home dir,
uid, and real captured session ids), and stray uses of the maintainer's personal handle. One private repo
name even shipped inside a packaged reference doc and is present in the published wheels." The verdict:
"This is a privacy leak AND a correctness bug (paths that resolve only on one machine)."

A later reversal is the clearest case of a trackedness policy flipping on leak grounds. The run-scratch
tree was previously documented as a committed deliverable. Then running the toolkit's own leak sanitizer
over the tree reported roughly 8,472 fail-severity findings, "essentially all inside" that tree:
"pervasive home-path, handle (the maintainer's username), and some session-id leaks ... The values are the
agent's own machine paths and identity." The reasoning that followed is directly relevant to your task:

- "Agents reliably embed machine-identifying info in these records: absolute home paths, the local
  username/handle, hostnames, and session ids."
- "The long-term provenance value of a run's scratch records is low: the durable artifacts that matter
  live elsewhere."
- "The cost (a standing PII/leak exposure in every repo that follows the guidance) far outweighs the
  benefit (keeping disposable run scratch as git provenance)."
- "the framework is contradicting its own tool."

Note that this argument has TWO independent legs: a leak-exposure leg (contingent on the destination being
public) and a low-provenance-value leg (not contingent at all). Your analysis must separate them.

The records-backend documentation already contains an explicit pollution comparison: `home` and
`companion` are recorded as "no target pollution," while `repository` is recorded as "`.aw/records/`
present" with the main risk "candid material can enter the public history." The wizard is required to
present `repository` records "as an intentional collaboration choice, NOT the recommended privacy
default," and to explain that "candid prompts, assessments, and plans may become public or enter pull
requests," that "ignore rules do not remove already tracked files," and that changing to external storage
later "requires a migration and may require separate history remediation." Making repository records the
default was explicitly REJECTED: "it optimizes collaboration at the cost of avoidable publication risk."
Encrypting records inside the public repo was also rejected: "It exposes existence, filenames or change
patterns, and introduces key management."

### The leak sanitizer (the deterministic detector that would police any new tracking)

A shipped, deterministic sanitizer detects the exact content class at issue. Its fail-severity rules are
structural: POSIX home paths, macOS home paths, Windows home paths, the maintainer's local-checkout
directory style, specific private/sibling repo names, a second local test account, captured session ids,
and a bare maintainer handle. Its warn-severity rules are AUTO-DERIVED from the environment: hostname,
FQDN, `$USER`/`$USERNAME`, git identity, and sibling checkout directory names. It can scan the working
tree, git history, a built wheel, and staged blob content. It exists precisely because that class of
defect "is exactly what credential scanners MISS, because it has no secret shape."

Two consequences worth reasoning about: (1) a per-repo tracked allowlist and a never-committed personal
hints file already exist, so "private repo, therefore allowlist everything" has a plausible mechanism; and
(2) the sanitizer's warn rules derive tokens from the CURRENT machine, so what counts as identifying is
machine-relative, which interacts badly with a records repo shared across a developer's machines.

### Evidence that untrackedness has real, measured costs

This is not a one-sided ledger. Concrete recorded costs of the current policy:

- The run-records tree is gitignored and has ZERO tracked files, so the run records the test suite reads
  "exist only on the machine that produced them. In any fresh checkout the directory is absent entirely
  and 15 of these tests fail ... That is also why CI is red." Proven by construction with a fresh clone,
  not inferred.
- The run-scratch tree is gitignored, "which is correct for machine-local run noise, but it means growth
  is invisible in the repo and nothing ever reclaims it." An open item asks for retention/pruning and
  explicitly REFUSES to un-ignore it: "Do NOT un-ignore the tree; it holds run noise and would create
  churn and leak-surface."
- The activity sidecar was untracked deliberately, and the reasons given were mixed: it "can leak local
  operational detail (actors/timestamps) into the public repo," but ALSO that tracking it meant "every
  `aw` status write dirties the tree, produces commit noise / cross-machine merge risk." Note that
  cross-machine merge risk is a reason a private repo does NOT fix, and arguably worsens.
- Execution-start and finalize receipts live in the gitignored state tree, which is "FINE for a
  pre-commit hook (which runs on the acting machine) but means the receipt CANNOT be verified remotely -
  hence local-only enforcement and no CI." So untrackedness directly caps what can be ENFORCED.
- An agent, needing to persist a human question queue, put it in an untracked comms lane, where it is
  invisible to git, to the attention view, and to every consistency check.

### The existing, unelaborated proposal

An open, low-priority backlog item captures exactly one shape of this idea and nothing more. Its entire
content is a summary line: "Records backend variant: repo-local-but-untracked `.aw/records` (git-ignored
in-tree records); own IPD." No body, no rationale, no linked spec.

Note what that would require: it is effectively `records -> target-ignored`, and NO preset permits that
today. All four presets route records to `target-tracked`, `companion-tracked`, or `home-untracked`. The
placement vocabulary classifies `target-ignored` as portability "local", durability "transient", privacy
"target-local". So the existing proposal is the INVERSE of the question in this prompt: it makes in-repo
records untracked, whereas this prompt asks whether out-of-repo records should make currently-untracked
things tracked. Evaluate both directions and say whether they are complementary or competing.

### Implementation reality of the companion backend (do not assume it works)

The companion machinery is substantially implemented (attach, detach, move, reattach, preflight with seven
numbered checks, identity file, materialization, per-repo commit-boundary reporting) but has verified gaps
and defects that any proposal depending on it must account for:

- `aw storage attach --companion-dir` never persists the backend choice into config, so the resolver
  ignores the attachment. Verified: after a successful attach, status still reported the old backend.
  Companion works today only via the install wizard, the layout migration, or a hand-edited local binding.
- The resolver computes the companion records path as `<companion>/records` while the materializer creates
  `<companion>/.aw/records` and the spec says `<companion>/.aw/records`. Verified divergence.
- A routing helper references a records-backend enum member that does not exist, raising an attribute
  error on the `home` backend. Reproduced.
- Two different durability classifiers disagree: a seven-state acknowledgement-aware one, and a
  three-state acknowledgement-blind one, so two commands can report different durability for one repo.
- `storage move` rewrites bindings but moves no data, contradicting its own help text.
- A cross-git staging guard is declared but its body is empty.
- A cross-repository git operation cannot be atomic, and the spec says so plainly.

### Two structural facts that shape the answer

1. MULTI-REPO, ONE HUMAN. A single toolkit installation is registered into many repositories at once (this
   maintainer has roughly 20). There is a per-user home store outside any repo holding a cross-repo project
   registry, plus a user config file in the XDG config directory. So "a private records repo" is
   ambiguous: ONE private repo for all of a developer's projects, or ONE PER project? Each choice has
   different consequences for cross-cutting queries, for blast radius, for merge contention, and for what
   "this record belongs to project X" even means.

2. PRIVATE IS NOT SINGLE-MACHINE. A private repo that a developer pushes is, by design, shared across
   THEIR OWN machines (laptop, desktop, server) and possibly with a small trusted team. That means
   machine-specific content stops being a privacy problem and becomes a CORRECTNESS and CONFLICT problem:
   absolute home paths that resolve on one box, lock files and process ids that are meaningless elsewhere,
   an append-only JSONL that two machines append to concurrently, and a run-state file whose live process
   id refers to a process on another host. Several of the recorded reasons for untrackedness are
   machine-boundness, NOT publicity, and those do not dissolve.

### Constraints from the project's stated principles

- SINGLE SOURCE OF TRUTH: each rule lives in exactly one canonical place. Two mechanisms for one job is a
  defect. A trackedness policy expressed in three places will drift.
- HONEST DOCUMENTATION: the project refuses to describe an advisory mechanism as a guarantee and refuses
  to promise that a repo or remote is private. It states that git ignore rules are advisory and that
  ignoring does not untrack or scrub history.
- MINIMIZE USER EFFORT: "an unnecessary action is a defect." A policy requiring the developer to
  hand-classify each artifact is a failure.
- EXTERNALIZE STATE; prefer encoding state in directory placement and filename over a status line inside a
  file, because a directory listing reveals every item's state in one cheap glance.
- KISS AND ANTI-SCOPE-CREEP: "A new noun does not automatically require a new model or abstraction;
  compare semantics, not names." Adding a fourth backend, or a fifth placement, or a per-class trackedness
  matrix, must be justified against just using the presets that exist.
- SAFETY AND REVERSIBILITY: default non-destructive. Note the asymmetry that dominates this whole problem:
  making something tracked is EASY to do and HARD to undo (history rewrite), while making something
  untracked is cheap and reversible. Any default you propose must be argued under that asymmetry.
- DETERMINISTIC CHECKS BELONG IN SCRIPTS: anything requiring no judgment must be a tested command with a
  machine-readable mode.

## What to determine

Answer each explicitly. Where the honest answer is "change nothing", say so and defend it.

1. IS TRACKEDNESS ACTUALLY A FUNCTION OF DESTINATION PRIVACY? State the general principle. Then classify
   EVERY item in the inventory table above into a reason taxonomy of your own construction, with at least
   these families distinguished: (a) publicity/pollution of a shared project history; (b) machine-boundness
   and cross-machine correctness; (c) genuine ephemerality and low provenance value; (d) merge/contention
   mechanics; (e) secrets; (f) mechanism-not-content (the user-driven escape hatch); (g) signal quality and
   view noise. For each item say which families apply, and crucially which of its reasons SURVIVE a move to
   a private repo. Multi-reason items are the interesting ones: an item is only a candidate for tracking if
   ALL of its reasons dissolve.

2. THE CONCRETE VERDICT PER ITEM. For each inventory item, give a ruling: track by default in a private
   records repo, keep untracked always, or make it configurable (and if configurable, what the default is
   and who flips it). Pay specific attention to the hard cases and say what makes each hard: the activity
   sidecar (an append-only JSONL two machines will append to concurrently); the run records (whose
   untrackedness demonstrably breaks the test suite and CI on a fresh clone, yet which are the single
   largest source of machine-identity leaks); session-handoff drafts (raw conversation, the most sensitive
   content the toolkit produces, and the reason a quarantine lane exists at all); the setup marker (a
   per-machine reminder that would be WRONG on another machine); the state tree (partly under an enforced
   untracked floor, partly not); and backlog `parked/` (already tracked, so the question is whether the
   private-repo case changes anything about visibility rather than trackedness).

3. MACHINE-BOUNDNESS AS THE REAL BLOCKER. For the items whose only surviving objection is that they embed
   absolute paths, hostnames, process ids, or session ids: is the right answer to keep them untracked, or
   to make them PORTABLE and then track them? Evaluate concrete portability techniques and their cost:
   path relativization to a declared root, symbolic roots and placeholder tokens, per-machine subdirectory
   sharding so two machines never write the same file, a machine-id dimension in the record itself, and
   append-only formats with union merge drivers. Say which are worth it and which are over-engineering.
   Note that the existing sanitizer already DETECTS exactly the non-portable tokens, so a detector exists
   and a rewriter partially exists.

4. ONE PRIVATE REPO OR ONE PER PROJECT? Decide and defend. Address: cross-project queries a single human
   actually wants ("what needs attention across all 20 of my repos", "every blocking question anyone has
   asked me"); blast radius if the private repo leaks; merge contention across machines; whether a record
   needs a project dimension in its path or its front matter; how the existing per-user home store and its
   cross-repo project registry fit; and whether the answer differs for durable records versus run scratch.
   Consider whether the honest answer is a hybrid (durable records per project, operational material per
   human) and if so where the seam is.

5. HOW DOES THE TOOLKIT KNOW, AND HOW HONESTLY? The toolkit refuses to promise a repo is private, and it
   already models durability as OBSERVABLE state with an explicit user acknowledgement rather than an
   inference from a configured remote. Design the privacy analogue with the same honesty discipline. Is
   there an observable "this destination is private" signal, or must it be a user assertion? What can be
   checked (is it a distinct repo, does it have a remote, is the remote reachable, is the target repo
   public, does the destination git-ignore what it should)? What must NEVER be inferred? What is the
   failure mode when the developer asserts private and is wrong, and how does the design keep that
   failure small and recoverable rather than a history rewrite?

6. THE POLICY MECHANISM. Given the six physical classes, the placement vocabulary, the four presets, and
   the enforced untracked floor on `config_local` and `state_runtime`, express your answer as a
   MECHANISM. Options to evaluate on their merits: a new preset; a new placement value; a per-class
   trackedness matrix keyed by destination privacy; a records-backend-conditional gitignore template; a
   per-artifact-type default declared in the type registry; or nothing new at all because an existing
   preset plus the existing user-driven escape hatch already suffices. Say exactly which existing gitignore
   patterns become conditional and how the condition is evaluated. Say what happens on a BACKEND CHANGE in
   both directions, including the dangerous one: records that were tracked in a private companion and then
   move to the project repo, taking their history with them.

7. MIGRATION AND THE ONE-WAY DOOR. Give the concrete plan for a developer who has been running with the
   current defaults and now attaches a private records repo. What becomes tracked, what is imported, what
   is deliberately left behind, and what is scanned first. Address directly: an ALREADY-PUBLIC repo whose
   records were tracked and now move private (ignore rules do not untrack or scrub history, so what is the
   honest offer?); the reverse move; and the sanitizer's role as a mandatory gate rather than an advisory
   nag. State plainly which parts are irreversible.

8. FAILURE MODES AND ANTI-GOALS. Enumerate how your design fails and name a specific guard for each. At
   minimum: a developer asserts private and is wrong; the private repo is later made public; two machines
   append to one file; a record embeds a path that exists on one machine only; a tracked run record pins a
   process id that means something else elsewhere; the private repo becomes an unbounded dumping ground
   nobody prunes; the policy differs from what an agent believes and the agent stages the wrong thing; and
   the "is it private" check becomes an oracle people learn to satisfy without meaning it. Then list what
   you deliberately do NOT build.

9. PRIOR ART, WITH CITATIONS. Search and cite real systems that separate a project's shared history from a
   developer's or operator's private-but-durable material, and systems that make trackedness conditional on
   destination. Consider at least: dotfile and configuration managers that sync personal state across
   machines; per-repo local ignore mechanisms versus tracked ignore files; tooling that keeps notes,
   metadata, or annotations in a side repo, an orphan branch, or a git-notes-style ref; editor and IDE
   local-state conventions and why some are tracked and some are not; build and dependency caches with
   machine-relative paths and the reproducible-build practice of path remapping; log and telemetry
   retention policy in developer tools; append-only file formats with merge strategies for multi-writer
   sync; secrets-in-git patterns and their failure record; and monorepo versus split-repo tradeoffs for
   metadata locality. For each, state what it does, what it proves works, and what specifically does NOT
   transfer to a single-maintainer, agent-authored, file-based system with no server, no daemon, and no
   scheduler.

## Deliverable (one downloadable .md file)

1. A one-paragraph RECOMMENDATION up front: what you would change, in plain words, and what you would
   leave exactly as it is.
2. The REASON TAXONOMY from question 1, with the full inventory classified, as a table: item, reason
   families, which reasons dissolve in a private repo, verdict.
3. The PER-ITEM VERDICT table from question 2, with the hard cases argued in prose beneath it.
4. The MECHANISM from question 6, concretely: which patterns become conditional, how the condition is
   evaluated, what a worked configuration looks like, and the behavior on a backend change in each
   direction.
5. Your answer to ONE-REPO-OR-MANY with the reasoning that decided it.
6. The PRIVACY-SIGNAL design from question 5, written to the same honesty standard the durability enum
   already meets (observable facts, explicit acknowledgement, no promises).
7. The MIGRATION PLAN from question 7, with the irreversible steps flagged.
8. FAILURE MODES with guards, and an explicit NOT BUILDING list.
9. PRIOR ART with citations and a transfers/does-not-transfer verdict per system.
10. THE HARDEST CALLS: where you were torn, the runner-up, and your tie-break reason, so a human can
    overrule you with context you lack.
11. An HONEST LIMITS section: what your design does not and cannot guarantee, stated in the register this
    project uses ("untracked by default is the goal, not an enforcement boundary").

Be concrete and decisive. Prefer a small, well-argued change over a large speculative one, and remember
the asymmetry: tracking is easy to start and hard to undo. If the correct answer is that ONE existing
preset plus a conditional gitignore template covers the whole need, say that plainly rather than designing
a new axis the project will have to maintain forever.
