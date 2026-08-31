---
id: 5ek188
created: 20260830
set: humanchk
order: 00
topic: [human-tasks, attention, records, reminders, cli]
model:
kind: research-prompt
status: todo
outcome: none-yet
summary: Originating prompt: how should this toolkit track and surface a HUMAN-owned checklist (things the maintainer must do) so agents can remind and tools can show them.
consumed-by: []
---

# Originating prompt (upload-ready)

Reports for this set land in orders 01+; reconciliation in the highest order.

---

# Design task: track and surface a HUMAN-owned checklist inside an agent-workflow toolkit

You are an expert in developer-tool information architecture, human-in-the-loop workflow design, and
agent/human division of labor. You have web search. Return your ENTIRE answer as a single downloadable
markdown (`.md`) file, with nothing outside the file.

## The problem in one paragraph

A toolkit called `aw` (agent-workflows) manages a repository's durable work records and is consumed by
BOTH AI coding agents and a human maintainer. Every category of work the system tracks today is work an
AGENT can do: plans, specs, backlog items, research, releases. But a large and growing set of obligations
can ONLY be discharged by the HUMAN: approving a spec, deciding a scope question an agent deliberately
refused to decide for them, enabling a setting in a hosting provider's web UI, running a credentialed
publish, answering a blocking design question, running a live paid model trial. Today those obligations
exist only as prose scattered inside artifacts whose primary subject is something else, so no tool can
list them, no agent can reliably remind the human of them, and they silently rot. Design the mechanism
that fixes this, in a way that fits the system described below rather than fighting it.

## What already exists (facts; design against these, do not re-invent them)

### The record system

Durable artifacts live in a git-tracked tree `.aw/records/<type>/`. Types: `plans` (implementation plan
documents, "IPDs"), `specs`, `backlog`, `research`, `releases`, `reviews`, `walkthroughs`, `roadmaps`,
`prompts`, `comms` (inter-agent messages). Each artifact is a markdown file whose front matter is a block
of `- Key: value` bullet lines (research is the one exception and uses YAML). Every artifact carries a
stable 6-character id (`- Id: h1ksy6`) that never changes, plus a filename grammar
`YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`. Names are minted by tooling, never by hand.

Status is per-type and closed-enum. Two types additionally encode status by DIRECTORY as well as in the
front matter, and the two must agree: `plans` (`pending/ executed/ superseded/ not-executed/ reusable/`)
and `backlog` (`open/ graduated/ blocked/ parked/ done/`). Each type has an owner verb family that is the
only sanctioned writer (`aw backlog set`, `aw specs set`, `aw ipd set`), each of which appends a
`## Workflow history` line and mirrors it to an append-only `history.jsonl` sidecar.

Adding a NEW artifact type is expensive and well-understood: roughly 40 to 50 concrete code touchpoints
across a type registry, a filename-facet enum, a path router, a check-rule registry, the attention
mapping, CLI wiring, a command-surface conformance declaration, installer scaffolding, a per-tree README,
and tests that pin the single-source-of-truth invariants. Adding a FIELD to an existing type is cheap: a
recognized-but-optional front-matter key plus a validator rule.

### The cross-tree "what needs attention" view

`aw attention` (alias `aw att`) is the single consumption surface for "what needs attention across the
repo". It is a PURE, on-demand, read-only scan that writes nothing and commits nothing. It maps every
tracked artifact's native per-type status onto one of five cross-tree classes: `ready`, `active`,
`blocked`, `done`, `parked`. The mapping is total and pure; an unrecognized native status is a contract
violation, never a silent default. `done` and `parked` are collapsed from the default human board and
revealed with `--all`. It emits a versioned JSON view (`schema_version`, `mapping_version`, `valid`,
`items[]`, `violations[]`), fails closed (nonzero exit when the view is invalid, so a consumer cannot
treat an invalid view as authoritative), and it has a closed catalog of rule ids. Its human board also
prints two sections that are deliberately absent from the machine output: outstanding release blockers,
and advisory gate warnings that never affect the exit code.

Types deliberately EXCLUDED from the view today, with recorded reasons: `walkthroughs` and `roadmaps` (no
lifecycle status), `prompts`, `comms` (its own ack lifecycle, deferred), and an evergreen prompt library.

### The typed-gate vocabulary (how "this cannot proceed yet" is already expressed)

An artifact whose own status is `blocked` (backlog) or `deferred` (spec) MUST carry a typed gate:
`- Gate-Kind:` from the closed set `artifact | decision | todo | issue | date | external`, plus a
`- Gate-Ref:` validated per kind (`artifact` = a repo-relative in-tree path, `date` = an ISO date,
`issue` = an http(s) URL, `decision` = `D<digits>` naming an ALREADY-RECORDED decision entry, `todo` = an
opaque id, `external` = an opaque string). Note the sharp edge: none of these kinds is "a person", and
`decision` can only cite a decision that already exists, so the vocabulary cannot today express "blocked
on a human who has not yet decided".

Separately, `- Blocks-Release: <release-id6|next>` on a backlog item, spec, or plan declares that it gates
shipping a release record. `- From-Backlog: <id6>` on a plan or spec records that it inherited a backlog
item's design and gate. A shared fail-closed predicate refuses to close a release-blocking backlog item
unless the gate is provably handed off, satisfied by a cited in-tree artifact, or explicitly cleared, and
that ONE predicate backs the setter, the consistency checker, and an opt-in git hook so they cannot
diverge.

### What already requires a human, and how

- SPEC APPROVAL: the `reviewed -> approved` transition is human-only. It is recorded by an explicit
  `--by-human` attestation flag, deliberately with NO terminal/TTY requirement and no false "I am human"
  claim. It is described in-tree as "a conscious speed bump recording attributed human approval; NOT
  anti-malicious crypto". An agent is expected to PASS this flag when the maintainer instructed it in
  chat, rather than stopping for a separate approval round trip. The recorded actor becomes
  `(aw specs, --by-human)`.
- PLAN APPROVAL is weaker and asymmetric: a plan reaching `approved` carries an `- Approval:` line that
  says either `human ("<quote>")` or the honest-but-weak `recorded via aw ipd set`.
- MARKING A SPEC `implemented` requires a resolvable evidence citation to an executed plan; an agent may
  not self-assert it.
- RELEASING: tagging, publishing a release, and uploading to a package registry may happen only inside one
  workflow section, after an explicit human GO, as separate default-NO confirmations. Anything the tool
  could not complete must be emitted as a loud "REMAINING MANUAL STEPS" block of copy-pasteable commands.
  That block is specified in prose only; no code emits it and its output is a chat message, not a record.
- SETUP: installing the toolkit writes a self-explaining, gitignored, per-repo marker file
  `.aw/setup-repo-needed.md`. `aw attention` prints one line, `NOTE: setup not complete - run the
  /setup-repo workflow in this repo.`, in the HUMAN view only, never in the machine output. A workflow
  deletes the marker on successful completion. This is the ONLY machine-tracked, machine-surfaced human
  obligation in the entire system.
- HOST-SIDE CONTROLS: branch protection and required reviews live in the git host, not the repo. The
  toolkit explicitly cannot set them and can only print recommendations for the human to apply.
- Local git hooks are honestly documented as advisory: local, not cloned by default, bypassable with
  `--no-verify`, and (for a push gate) explicitly "NOT an authority boundary" because its acknowledgement
  signal is an environment variable the agent itself can set.

### Evidence the need is real and currently unmet

1. Pending plans contain a structured `### OQ-NN` open-question block with subfields
   `- Blocking: yes|no`, `- Status: open|resolved|deferred`, and `- Owner: <free text>`. Right now there
   are 18 open questions, 16 of them marked blocking, and 17 owned by the maintainer under four
   unnormalized spellings (`maintainer`, `human maintainer`, `human`, `human (maintainer)`), spread across
   9 pending plan files. The field vocabulary is defined in code and is confirmed to have NO consumer
   anywhere: nothing validates it and nothing aggregates it. A human wanting the list must open every
   pending plan by hand.
2. An agent, finding no mechanism, INVENTED one: an untracked file `comms/untracked/QUESTION-QUEUE.md`
   with its own hand-rolled format, per-entry `Status: OPEN | ANSWERED | MOOT`, a
   `- Artifact that changes if you disagree:` field, an "answer format: add `ANSWER:` under any entry"
   convention, and the self-description "I re-read this file at each item boundary." Because it lives
   under `untracked/`, it is invisible to git, to `aw attention`, and to every check.
3. A release record contains a prose paragraph titled "Interim: sets that cannot yet carry the field",
   self-labelled a "TEMPORARY EXCEPTION to the no-prose-list rule", ending "Once X lands, migrate this
   intent to the per-item field and delete this interim note." A human TODO living inside a release
   record, in prose, in acknowledged violation of the system's own single-source rule.
4. Backlog items record hand-edits a human must later redo through tooling ("re-verify/re-set via the tool
   once this bug is fixed").
5. A typed actor model already exists in the codebase and is UNREACHABLE DEAD CODE: a decision-gate type
   with `requires_human: bool = True`, and a decision record with `approver`, `actor`, `interactive`
   fields. Nothing in the CLI reaches it.

### The prior attempt, and exactly why it was deleted (this is the most important constraint)

The system previously HAD a general operational-action ledger with a full verb surface
(`aw todo`, `aw show`, `aw complete`, `aw dismiss`, `aw reopen`, `aw history`) and its own attention tree.
It was deliberately deleted. The two recorded reasons, verbatim in the tombstone module:

- It "was redundant with the backlog tier (the general operational-task machinery)".
- Its manager object "eagerly created `.aw/state/actions/*`" on construction, "which a read-only attention
  scan reached, stamping `.aw/state/` into every scanned repo (write-on-read)".

The single reminder it actually held (post-install setup) became the gitignored marker file described
above. Residual stale help text and one workflow still reference the removed tree, which is itself
evidence of the maintenance cost of a whole new tier.

Any design you propose MUST explain why it does not recreate either failure: redundancy with the existing
backlog tier, and any write-on-read side effect in what must remain a pure read-only view.

### Constraints from the project's stated principles

- MINIMIZE HUMAN EFFORT: "an unnecessary action is a defect." A mechanism that makes the human maintain a
  list is worse than no mechanism.
- EXTERNALIZE STATE, DO NOT TRUST MEMORY: the authoritative record is files, not conversation. Prefer
  encoding state in DIRECTORY PLACEMENT and FILENAME over a status line inside the file, because a
  directory listing reveals every item's state in one cheap glance while a status line requires opening
  every file (costly for a human, many tokens for an agent).
- SINGLE SOURCE OF TRUTH: each rule or list lives in exactly one canonical place and is referenced
  elsewhere. Duplicated normative content is a correctness hazard. Two mechanisms for one job is a defect.
- KISS AND ANTI-SCOPE-CREEP: "A new noun does not automatically require a new model or abstraction;
  compare semantics, not names." Do not build for hypothetical needs.
- DETERMINISTIC WORK BELONGS IN SCRIPTS, NOT IN LLM PROSE: anything requiring no judgment must be a tested
  command with a machine-readable mode that agent workflows consume instead of re-deriving.
- ASK SELF-CONTAINED QUESTIONS: when an agent needs a human decision it must put the entire decision
  context inside one interactive prompt, one question at a time, screen-sized, without restating the
  options the prompt already renders.
- CONCISE REPORTING: an agent's routine reply is capped near 100 words and must emit at most one short
  progress line. A reminder mechanism that prints a wall of text every turn violates this and will be
  ignored or disabled.
- SAFETY AND REVERSIBILITY: default to non-destructive; never publish, push, or change public contracts
  without explicit permission.
- HONESTY ABOUT ENFORCEMENT: the project refuses to describe an advisory mechanism as a guarantee. Your
  design must state plainly what it does NOT enforce.

### Two structural facts that shape the answer

1. MULTI-REPO. One toolkit installation is registered into many repositories at once (this maintainer has
   roughly 20). There is a per-user home directory outside any repo (`~/.aw/` with `config`, `projects`,
   `state`) holding a cross-repo project registry, plus a separate user config file under the XDG config
   directory. So a human obligation could plausibly live per-repo (tracked), per-repo (untracked), or
   per-HUMAN across all repos. A human's real checklist is arguably not repo-shaped: "enable branch
   protection on 6 repos" is one human task spanning six trees.
2. SHARED CHECKOUT, CONCURRENT ACTORS. Multiple agents and the human may work in the SAME checkout
   simultaneously. Agents are instructed never to stage, revert, or commit another party's changes, and to
   verify the staged set before every commit. Anything your mechanism writes must be safe under
   concurrent, uncoordinated writers.

## What to determine

Answer each of these explicitly. Where the honest answer is "do not build this", say so and defend it.

1. IS A HUMAN OBLIGATION A NEW ARTIFACT TYPE, A FIELD ON EXISTING TYPES, OR A PURE DERIVED VIEW? Evaluate
   at least these four options on their merits, not just the one you like:
   (a) a new tracked record type with its own directory, status enum, owner verb family, and attention
       tree;
   (b) an OWNER/ACTOR facet added to the types that already exist (a recognized optional front-matter
       field, and/or a typed `Gate-Kind: human` extension of the existing gate vocabulary), with the
       checklist computed as a VIEW over them and nothing new stored;
   (c) promoting the existing per-plan open-question block into the machine-readable thing it already
       looks like, and aggregating that;
   (d) a per-human, cross-repo store outside any repository, with the in-repo artifacts merely
       contributing to it.
   For each: what it costs to build, what it costs to maintain, how it satisfies or violates the
   single-source rule, and how it avoids the deleted-ledger failure modes.

2. WHERE DOES THE STATE LIVE, AND IS IT COMMITTED? Decide and defend: git-tracked in the repo (visible to
   collaborators and to CI, and permanently in public history), untracked in the repo (private but
   invisible to every check and lost on a fresh clone), or in the per-user home store (cross-repo and
   private but invisible to the repo's own consistency checks). Address the privacy question directly: a
   human's todo may be personal, may name a third party, or may be embarrassing, and this project ships a
   leak sanitizer precisely because maintainer-identifying content must not reach public artifacts.
   Address the durability question directly: an untracked reminder that vanishes on a re-clone is the
   failure the whole records system exists to prevent.

3. THE DATA MODEL. Give the exact fields, the exact closed status enum, and the mapping of each status onto
   the five existing attention classes (`ready`/`active`/`blocked`/`done`/`parked`), or argue that human
   items need a sixth class and justify why extending a total, pure, versioned mapping is worth it. Say how
   an item expresses: who must act (is "the human" one actor or several?), why the agent cannot do it, what
   becomes unblocked when it is done, whether it blocks a release, its urgency, and its provenance (which
   artifact and which agent raised it). Reuse the existing vocabularies (id6, `Set`, `Priority`,
   `Work-Kind`, `Blocks-Release`, `Gate-Kind`/`Gate-Ref`, `## Workflow history`) wherever they fit, and
   flag every place you are forced to invent a new one.

4. WHO MAY CREATE, AND WHO MAY CLOSE? An agent must be able to RAISE a human obligation without
   interrupting its work. But if an agent may also CLOSE one, the mechanism is worthless the moment an
   agent decides the human "probably already did it". Yet this project has already rejected TTY-gating as
   the answer (it wedged a real run for over an hour and forced a maintainer who had already approved in
   chat to re-approve in their own terminal), and its chosen substitute is the `--by-human` attested flag,
   which an agent can and does pass on the maintainer's verbal instruction. Design the closure rule under
   exactly that constraint, and state its honest limit.

5. THE REMINDER POLICY. Specify precisely when a human obligation is surfaced, by whom, and how loudly.
   Cover: what an agent is instructed to do at a turn boundary (the only existing turn-boundary polling
   instruction in the system is "check your inter-agent comms inbox", and its subject is other agents);
   whether reminders escalate with staleness or priority, and if so on what clock; how the 100-word
   concise-reporting cap is respected; how the human turns the nagging DOWN without turning the record
   OFF; and what stops the mechanism from becoming the thing everyone ignores. Distinguish PULL (the human
   runs a command) from PUSH (an agent volunteers it) and say which obligations deserve push.

6. THE CLI SURFACE. Fit your design into the existing grammar. The tool has both a type-generic
   noun-verb family (`aw check|find|search|index|rename|group <type>`, `aw set <status> <selector>`) and
   per-type owner verb families (`aw backlog new|set|check`). Mutating verbs preview by default and need an
   explicit apply. Name every command and flag you add in plain everyday words, and note that the word
   `todo` is currently an alias of `attention` and that `aw next` does not exist at top level (only
   `aw run next`, scoped to one run's step graph). Say what you would deprecate.

7. MIGRATION. Give the concrete plan for the obligations that exist TODAY: the 16 blocking maintainer-owned
   open questions across 9 pending plans, the untracked hand-rolled question queue, the release record's
   interim prose note, the hand-edit-redo notes in backlog items, and the setup marker. State which of
   these your mechanism should ABSORB and which should stay where they are, and why. Say explicitly whether
   the setup marker should be folded in or left alone.

8. FAILURE MODES AND ANTI-GOALS. Enumerate how your design fails: duplicate truth, agent-generated noise,
   an abandoned list that becomes a lie, staleness with no owner, privacy leak, write-on-read, contention
   in a shared checkout, and gaming (an agent closing its own human gate). For each, name the specific
   guard. Then list what you deliberately do NOT build.

9. PRIOR ART, WITH CITATIONS. Search and cite real systems that solve "a machine tracks work only a human
   can do, and reminds them": human-in-the-loop task queues in agent frameworks, approval gates and
   manual-intervention steps in CI/CD systems, review-request and required-reviewer models in code
   hosting, dependency-bot and security-advisory nudges, personal task managers with plain-text or
   file-backed state, plain-text task formats and their tooling, issue trackers' assignee-plus-due-date
   models, and checklist-style compliance tooling. For each, say what it does, what it proves works, and
   what specifically does NOT transfer to a single-maintainer, agent-authored, git-tracked, file-based
   system with no server and no notification channel. Note that this toolkit has NO daemon, NO server, NO
   scheduler, and NO way to email or message the human: the only channels are a command the human chooses
   to run and text an agent chooses to print.

## Deliverable (one downloadable .md file)

1. A one-paragraph RECOMMENDATION stated up front: the single design you would build, in plain words.
2. The OPTION COMPARISON from question 1, as a table plus prose, with your ranked verdict.
3. The exact DATA MODEL and status enum, shown as a realistic worked example file (or field set) for at
   least three genuinely different obligations: a spec awaiting approval, a blocking design question an
   agent refused to decide, and an out-of-repo action in a hosting provider's UI.
4. The exact CLI SURFACE, with a one-line gloss per command and flag.
5. The REMINDER POLICY, written as instruction text an agent would actually be given, at the length and
   register that a per-turn always-loaded contract can afford.
6. The MIGRATION PLAN for the items listed in question 7.
7. FAILURE MODES with guards, and an explicit NOT BUILDING list.
8. PRIOR ART with citations and a transfers/does-not-transfer verdict per system.
9. THE HARDEST CALLS: where you were torn, the runner-up, and your tie-break reason, so a human can
   overrule you with context you lack.
10. An HONEST LIMITS section: exactly what your mechanism does not and cannot enforce.

Be concrete and decisive. Where the evidence supports a judgment call, make it and justify it briefly.
Where the right answer is that the existing backlog tier plus one new field already suffices, say that
plainly rather than designing a tier the project will delete again.
