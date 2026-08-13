# TODO / backlog

Tracked backlog for `agent-workflows`. Concrete, planned work lives as IPDs under
`.agents/plans/pending/` and goes through the plan lifecycle; this file is for lighter-weight
backlog notes and ideas that are not yet (and may never become) plans. The release-review workflow
triages this file against each release.

## Known bugs to fix

- **Test-isolation flake: `tests/test_setup_artifacts.py::PromptsScaffoldTests::test_undo_removes_prompts_scaffold`.**
  Observed once failing in a full-suite run (pytest-randomly seed 995070605, 2026-07-26) but passes
  standalone and on full-suite re-runs INCLUDING the same seed, so it is a non-deterministic
  test-isolation/temp-state interaction, not a product bug (it surfaced during a prose/template-only
  change that touches no undo/prompts-scaffold code). Investigate cross-test filesystem/cwd/backup-dir
  state leakage in the setup-artifacts + rollback tests; make the test hermetic. Low priority (green on
  normal runs); its own small IPD when addressed.

FIXED 2026-07-13: `test_normalize_plan_names.py` date-relative flakiness (tests now use today-relative
dates; product unchanged). See DECISIONS D78 and
`.agents/plans/executed/20260713-normalize-plan-00-qv04dz-normalize-plan-names-test-date-flakiness.md`.

## Security follow-ups (OpenCode shared-host finding, D86/D87)

Not framework bugs; external-tool finding with coordinated-disclosure obligations. See advisory
`.agents/docs/research/20260716-opencode-unauthenticated-local-server-advisory-00-kams1a-opencode-unauthenticated-local-server-advisory.advisory.md`.

- **Coordinated disclosure to OpenCode maintainers (OPEN).** Send the private report (repro + fix proposal:
  UNIX 0700 socket / require-auth config key / UID check / redact secrets from `/config` / honor permission
  policy on API-injected tool calls). Start the 30-45 day clock; go public only if unfixed by the deadline.
  Human owns whether/when it is sent.
- **HPC user warning (guidance ready).** Circulate the hardening how-to
  (`20260716-0850-02-...`). Consider a LOUD shared-host warning in the framework installer only if we decide
  the framework should carry it (would cite D86/D87); not yet committed.

## Planned next (designed, deferred; not yet drafted as IPDs)

**`/aw <verb>` command-family redesign (own Set/IPD; cross-cutting).** Introduce a single `/aw`
slash-command namespace and move the framework's own workflow commands under it (e.g. `/setup-repo`
-> `/aw setup`, `/assess` -> `/aw assess`, a future `/aw migrate` / `/aw migrate-layout`), mirroring
the `aw <verb>` CLI. `/aw` is very unlikely to collide in agent coding environments. NOT trivial:
(1) per-host slash-command grammar must be verified first - some hosts may not support a real
`/aw <space> subcommand` and would need `/aw-<verb>` or `/aw:<verb>`; (2) it touches every workflow's
shim/installer naming + docs; (3) needs back-compat aliases for the existing top-level command names
and a deprecation path so user muscle-memory and existing shims keep working. Own review. Discovered
2026-08-12 during /plan-review of IPD bsxowq (migdispo); that plan only NAMES its new `migrate-layout`
workflow to fit this future scheme and explicitly does NOT build the namespace or rename existing
workflows.

**`aw ipd scaffold` should enforce the clustering filename grammar + Set metadata (authoring gap).**
Today `ipd scaffold` takes `--path` verbatim and treats `--set` as OPTIONAL: if `--set` is omitted it
writes NO `- Set:` line and does not derive/validate the clustering-grammar filename
(`YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md`), so a hand-supplied `--path` can land in the older
`YYYYMMDD-HHMM-NN-<slug>.md` form with a missing set-id/id6 and no Set metadata. Nothing catches this
until someone runs `aw plans set-assign`. Harden the scaffolder to require a Set (or default a
singleton), emit the clustering-grammar filename itself (or refuse a non-conforming `--path`), and
always write a `- Set:` line. NOTE: this is NOT addressed by the layout-migration script (a
byte-preserving relocation that intentionally never renames plans - naming is the separate `aw plans`
concern) nor by IPD bsxowq (migration dispositions, not filename hygiene). Discovered 2026-08-12 when
plan bsxowq was created with the wrong name and had to be fixed via `aw plans set-assign --rename`.

**Inventory tool must honor .gitignore (bug; own follow-up).** `tools/awphysical/aw_layout_inventory.py`
`_walk()` only skips `.git`; it descends into gitignored subtrees, so running the migration inventory
over the source repo enumerated `.opencode/node_modules/` (3926 gitignored dependency files) and
`_legacy_class` blanket-classified them as `host-adapter-candidate`. The inventory should skip
gitignored subtrees (at least `node_modules`) so it does not sweep dependency/runtime noise into the
migration map. Discovered during Order 11 self-migration Stage 1, 2026-08-12 (worked around there by
scoping the roots; the tool fix is the durable answer).

**Records backend variant: repo-local-but-untracked `.aw/records/` (deferred; own IPD).** Today
`RecordsBackend` has exactly three values: `home`, `companion`, `repository` (the last =
`<repo>/.aw/records` TRACKED in the repo's git). There is a genuine fourth option we never modeled:
records living at `<repo>/.aw/records` (repo-local, so tooling/locality is trivial) but NOT committed
(git-ignored). It is NOT a one-line `.gitignore` change: it needs a new enum member (or a
`records_git: tracked|ignored` sub-flag), the resolver git-policy mapping (`project_context.py`
~L599/691/733), the durability classifier (`storage.py`, would report local-only/unversioned), the
wizard presets, the postcheck records-git-ownership assertion, an emitted `.gitignore` entry (and an
optional `git rm --cached` for an existing tracked tree), and tests. Useful for private/local repos
that want records in-tree without committing them. Deliberately NOT added during the awphysical Set
(scope creep onto just-executed orders); do it as a clean follow-up IPD if wanted. Source: maintainer
question during Order 11 (self-migration) execution, 2026-08-12.

**Cross-tree attention view + owner-written spec status shipped (`attnview` Set, D125).** `aw attention`
(read-only, on-demand, fail-closed) maps every tracked `.agents/` artifact onto a `ready`/`active`/
`blocked`/`done`/`parked` class; `aw specs set`/`note`/`check`/`migrate` own spec status+history with an
anti-self-approval floor; `/whatnext` consumes the view first; CI gates `aw attention --check` +
`aw specs check`. Deferred future work from this Set: (1) `prompts/` and `comms/` are named Phase-3
attention-view adopters (add their native-status contracts + mappings, then include them in the tree
policy inventory); (2) `walkthroughs/`/`roadmaps/` stay excluded until they have real lifecycle
semantics; (3) an optional persisted `aw attention snapshot` only if a non-CLI consumer needs it; (4)
the two specs migrated to `deferred` (`20260725-external-delivery-and-skills`, `20260726-clean-delta`)
carry `Gate-Kind: artifact -> TODO.md` and now surface as `blocked` in `aw attention` - resolve them by
the SKILLS delivery-model re-evaluation (below) and the clean-delta build phases respectively; (5) plans
gain a native `executing` state later if approved-vs-executing should show as `active` in the view.

**Apply the artifact-organization model to `prompts/` (the next adopter after research and plans).**
DONE: research (`research-org`, D123) and plans (`plans-adopter`, D124) now share the area-agnostic
core (`agent_workflows/artifact_core.py`): stable id, tiered manifest + `--check`, weekly cold shards,
deliberate archival verbs. `prompts/` is the WEAKEST remaining case (low volume, an existing
pending/executed lifecycle, filenames already the stable stem, and the research-prompt lineage already
handled in the research spec 4.6), so it is lowest priority; `comms/` and `walkthroughs/` are subsequent
adopters after that. Each is its own IPD Set (reusing the shared core) + `/plan-review` + human approval;
not release-gating. When authored, mirror the plans-adopter shape: a shared-core reuse, a stable Id in
the area's existing metadata (no duplicate frontmatter), a manifest, and a migration with a dry-run STOP
gate.

The agent-comms convention (D81) was IPD 1 of a designed 4-IPD split; IPDs 2-4 are intended future work
(not "maybe" ideas). They are OPTIONAL and OpenCode-specific, and the convention works standalone without
them, so none is release-gating. Full design + the load-bearing unknowns are in
`.agents/docs/research/20260714-same-box-agent-wakeup-mechanisms-00-j2000q-same-box-agent-wakeup-mechanisms.research-report.md`. Each still needs its own IPD
and human approval before any build.

- **IPD 2 - the payload-blind broker (OpenCode-only, opt-in).** A long-lived per-box notifier that
  watches `.agents/comms/local/inbox/` (inotify), enforces `Not-Before`, delivers a FIXED content-free
  "check your inbox" nudge to the target OpenCode instance via its server API, and writes the
  broker-authored delivery acks (scheduled/queued/delivered/agent-not-running/agent-not-responding/
  expired). HARD INVARIANT: the broker is payload-BLIND (reads envelope headers only, never the payload;
  carries no attacker-controlled text). Attended TUIs get a gentle nudge (never a forced turn); headless
  targets can be woken. FEASIBILITY NOW CONFIRMED (live test + source-grounded consult, 2026-07-16; see
  `.agents/docs/research/20260716-broker-feasibility-confirmation-00-xawbsa-broker-feasibility-confirmation.research-report.md`): cross-instance
  delivery/wake works; there is NO discovery API (port must be injected / scraped / enumerated); a plugin
  and an external daemon share the same HTTP-client channel (external daemon is cleaner); `OPENCODE_SERVER_PASSWORD`
  Basic auth (user `opencode`) works. This IPD can now be drafted. HARD INVARIANT reinforced by the D86
  security finding: the broker is payload-BLIND (reads envelope headers only; never a filesystem-to-injection path).
- **IPD 3 - agent-side ack writing + status aggregation.** The target agent writes its own
  read/in-progress/done/not-done/executed/not-executed acks; a status view aggregates ack files into a
  per-message lifecycle board. Depends on IPD 1 (format) + IPD 2 (broker acks to interleave).
- **IPD 4 - discovery/registry.** How the broker finds live targets + their mode/endpoint: prefer
  OpenCode's own mDNS/`attach`, with a filesystem descriptor as fallback; stale-entry reaping. Depends on
  IPD 2. Cross-box is out of scope for this line.
- Deferred beyond the split: conditional scheduling (`Depends-On` marker files), Telegram/Signal and
  other transports, cross-box comms.

### Two reconciled 1.3.0-era Sets (prompt pipeline + agent-continuity workflows)

Two DISTINCT ordered Sets came out of the 2026-07-16 discussion, reconciled 2026-07-20 (IPD
`20260717-agentcont-01-6a3myl-whatnext-surveyor-workflow` Step 5) so their `Order:` numbers no longer collide. Each item needs its own IPD +
`/plan-review` + human approval before any build. Grounding: D88 (filesystem-encoded state, extends P5);
`.agents/prompts/` staging is blessed by D50 / IPD `20260712-consolidate-reference-00-7waz4b-consolidate-reference-material-and-docs-bucket-standard`.

**Set `research-prompt-pipeline`** - where run-once/research prompts and their results live:

- **Order 1 - DONE (D88).** Codify the filesystem-encoded-state principle (location over contents) by
  extending GUIDING_PRINCIPLES P5. Listed for provenance.
- **Order 2 - DONE (D91).** Scaffold `.agents/prompts/` lifecycle buckets + document the
  research-prompt->results convention (prompts stage in `.agents/prompts/<bucket>/`; RESULTS under
  `.agents/docs/research/<topic>/`; `.agents/docs/prompts/` stays the evergreen library). Executed via IPD
  `20260717-researchprompt-02-2txx9b-scaffold-agents-prompts-staging-convention` (now tagged this Set, Order 2).
- **Order 3 - `/research [topic]` workflow (producer; prompt-authoring walk-through).** Clarifies the
  research question, drafts a house-conformant prompt into `.agents/prompts/pending/` (ENFORCING the
  AGENTS.md handoff-prompt rules: upload-ready, self-contained, no user-instructions inside, returns a
  downloadable `.md`), tells the operator how to run it, and states where results go (`research/<topic>/`).
  Narrow-to-medium scope, NOT a do-everything blob overlapping `/assess` or `/spec`. Depends on Order 2.
- **Order 4 - OPEN: should the installer scaffold `.agents/prompts/`?** `aw install` already scaffolds it
  as of D91, so this is largely RESOLVED; confirm and close. (Kept for the record.)

**Set `agent-continuity-workflows`** - the surveyor/producer/snapshot command trio:

- **Order 1 - `/whatnext` workflow (surveyor; read-only, recommend-don't-act).** DONE via IPD
  `20260717-agentcont-01-6a3myl-whatnext-surveyor-workflow`: a `.agents/workflows/whatnext/` prose runbook that surveys plans/prompts/comms/TODO
  and returns a prioritized, reasoned recommendation (survey-then-reason; never mutates/acks/moves).
- **Order 2 - `/research`** is the pipeline producer above; it is cross-listed here as the natural producer
  that `/whatnext` surveys, but its home Set is `research-prompt-pipeline`.
- **Order 3 - `/handoff` workflow (session-handoff generator; human request 2026-07-17).** Produces a
  DETAILED cold-start handoff document on demand (facts PLUS a working-style/preferences/nuance layer). HAS
  A FULL IPD (Status: to-review): `.agents/plans/pending/20260717-agentcont-03-5twbwf-handoff-workflow-session-continuity.md`.
  The hand-authored `.agents/plans/pending/20260717-1950-01-session-handoff-resume-here.md` is the
  golden-output example. Needs `/plan-review` -> approval before building; 1.3.0-era.

## Consider and possibly implement (not committed, may be declined)

Ideas worth revisiting; each needs a real decision before it becomes a plan. Do not implement any of
these without an approved IPD.

- **Refine the `aw specs` `reviewed -> approved` approval mechanism ergonomics (attention-registry spec OQ10).**
  D125's anti-self-approval floor is working as intended: an AGENT cannot set a spec to `approved` - the
  `aw specs set --status approved` path requires an interactive TTY human confirmation, and a `--yes-i-am-human`
  flag is honored ONLY when stdin is a real TTY. That correctly stops an agent from self-declaring a human
  decision. But it produced a real ergonomic rough edge in practice (2026-08-09, awlayout spec approval): when a
  human says "approved, go" in chat, the orchestrating AGENT cannot record it (no TTY), so approval had to be
  hand-run by the human in their own terminal - a clunky round-trip for an approval the human already gave.
  Note the asymmetry that caused the surprise: PLANS/IPDs still approve via the simple metadata convention (an
  agent records the human's chat "approved, go" as `Status: approved` + an `- Approval:` line - unchanged), while
  only SPECS carry the strict TTY floor. Consider a cleaner human-token design that keeps the "agent can never
  self-approve" guarantee without forcing the human into a terminal: e.g. accept a maintainer's explicit
  in-session approval when the operator is demonstrably human (an out-of-band token/marker the human issues, a
  one-time approval file the human drops, or a signed marker), rather than only a live TTY prompt. This resolves
  attention-registry spec OQ10 (still an open Phase-0 candidate). Keep the floor's INTENT intact; only improve HOW
  the human's real approval is captured. Do NOT weaken it into something an agent harness can satisfy.
  - RECURRED 2026-08-10 (awphysical physical-layout spec approval). The maintainer hit the friction again and
    considers the current gate DISPROPORTIONATELY strict for the risk class ("we're not asking an agent to drop
    bombs on a building"). Two concrete rough edges observed: (1) the command surface is clunky - a mandatory
    `--message`, a long `--yes-i-am-human` flag that is redundant on a TTY (the code already prompts interactively
    when stdin is a TTY, so the flag only skips the typed `approve` confirmation), plus a type-the-word-`approve`
    prompt; the maintainer noted "that will dissuade people from using this." (2) The deeper mismatch: the
    maintainer's real workflow is "human decides in chat, agent operates the terminal," and there is NO honest path
    for the agent to record that delegated approval for SPECS (unlike PLANS, which accept an attributed `Approval:`
    metadata line). When asked "how would you approve for me - lie?", the honest answer was no: the tool refuses
    non-TTY approval outright (`_human_confirmed`, agent_workflows/specs.py:538-553) and `--yes-i-am-human` is
    TTY-gated, so an agent genuinely cannot approve; the honest options are to hand the human the one-liner or to
    record "the human approved via chat" as attributed provenance (a claim, not an impersonated TTY confirmation).
    DECISION DEFERRED to a future IPD: reconsider the strictness for this risk class and add an honest delegated-
    approval path for specs (candidate: an attributed `Approval:` line like plans, or a human-issued out-of-band
    token/one-time approval file), plus fix the CLI ergonomics (make the interactive prompt the whole story / drop
    the redundant flag / default or relax `--message` for approvals). Preserve the "an agent harness alone cannot
    self-approve" guarantee;     the goal is proportionality + honest delegation, not removing the human from the loop.
    Source: awphysical spec approval session 2026-08-10.

- **Unify lifecycle-status transitions behind ONE verb across every status-bearing artifact, with
  group/Set operations and a format/syntax checker (maintainer request 2026-08-10).** Today the
  status-transition surface is inconsistent and incomplete: SPECS have `aw specs set --status <enum>`
  (enforces the transition table + anti-self-approval floor + typed gates); RESEARCH has `aw research
  promote`; but PLANS/IPDs have NO status-setting verb at all - `--status` on `aw plans find` is only a
  FILTER, and setting a plan `to-review`/`reviewed`/`approved` (plus its `- Approval:` line and resolving
  the human-approval OQ) is a hand-edit metadata convention. That gap is exactly why, in the awphysical
  approval (2026-08-10), the 13 plan approvals were applied by a hand-written bulk script instead of a
  tool (an error: it should have been per-file edits at minimum, and ideally a verb) - there was no
  `aw` verb to record a plan approval. Desired design (discuss + IPD before building):
  1. A SINGLE consistent transition verb usable across every artifact that carries a lifecycle status
     (specs, plans/IPDs, and anything else that is `draft`/`to-review`/`reviewed`/`approved`/terminal),
     with the SAME syntax for every artifact type. SYNTAX DIRECTION (maintainer, 2026-08-10): prefer
     POSITIONAL arguments over `--long`/`-short` flags wherever possible. The target shape is a top-level
     `aw set <status> <identifier...>` where `<status>` is the bare enum positional (`aw set approved ...`,
     `aw set to-review ...`, `aw set reviewed ...`, `aw set executed ...`) and `<identifier...>` is one or
     MORE positionals, each of which may be an `<id6>`, a `<set-id>`, or a filename - mixed freely. The
     tool AUTO-DETECTS what each identifier refers to (IPD/plan vs spec vs other) and applies the correct
     per-artifact transition table + enforcement; the caller does not name the area or pass `--status`.
     Reserve flags only for things that cannot be positional (e.g. the human-approval token/`--message` if
     still required, though see the delegated-approval item above about capturing approval honestly).
     Keep the enforcement uniform (legal transition table, honest human-approval capture, required history
     line) rather than one-off per area. (Contrast today's inconsistent, flag-heavy surface: `aw specs set
     --status <enum> --message ...` positional path last; no plan verb at all.)
  2. GROUP/Set transitions: because we frequently act on a whole IPD Set at once (e.g. approve all 13
     awphysical plans, or move a Set reviewed->approved together), passing a `<set-id>` positional to
     `aw set <status> <set-id>` MUST apply the transition to all members atomically (the set-id is one of
     the accepted identifier kinds in item 1), as must an explicit multi-identifier list, with one shared
     approval record and a single consolidated history stamp - not 13 manual
     edits. Respect the anti-self-approval floor for the human-only transitions even in group mode.
  3. A FORMAT/SYNTAX CHECKER that validates the structure/metadata/status-legality of one file, a named
     subset, or a whole directory class - `one | some | --pending | --executed | --all` (and per area:
     specs, plans, research). Today `aw ipd lint` checks a single IPD and `aw specs check` does one-or-all
     specs; unify/extend into a consistent "check the format+status of these artifacts" surface with the
     same selector vocabulary as the transition verb, deterministic `--agent` output, and fail-closed
     `--check` for CI. Keep the existing deterministic guarantees (structure/state only; no semantic
     claims). Source: maintainer request during the awphysical plan-approval session, 2026-08-10.

- **Re-evaluate the bounded-iteration + agent-agnostic skill-modifiers roadmap
  (`.agents/docs/roadmaps/20260712-1426-agent-workflows-bounded-iteration-skills-roadmap-for-consideration.md`).**
  It was drafted 2026-07-12 against version 1.1.0 and is now stale relative to the many changes since
  (the install-safety Sets, the untrack-workflow-artifacts policy, the dual-checklist convention, the
  research-organization spec, and the IPD-structure-and-linting spec). Before treating any of its
  proposals as live, re-read it against the current design and decide per-item keep/revise/retire; it
  is tracked for the record, not endorsed as-is. Source: roadmap draft committed 2026-08-02.

- **Audit all workflows for deterministic work that can move into agent-friendly scripts (from
  GUIDING_PRINCIPLES P11 / DECISIONS D96).** The leak-sanitizer established the pattern: deterministic,
  no-judgment checks belong in a robust script with an `--agent`/`--llm` output mode that LLM surfaces
  DELEGATE to, rather than re-deriving in prose and burning tokens. Sweep the workflows (release-review
  sections, assess lenses, verify, scaffold) for pattern matches / structural validation / config checks
  currently done by the model, and list candidates to extract into scripts. One audit, then per-candidate
  IPDs. Also on the roadmap: the leak-sanitizer Set Order 2 (re-runnable config wizard) and Order 3
  (agent/workflow rewire consuming `--agent` output + OPTIONAL setup-repo install of the hook/CI, off by
  default, with agents made AWARE of the script even without hooks) are designed follow-ups to D96.
- **Extract the push-then-verify CI loop into its own instruction file (from vistab.agent, 2026-07-17;
  verified against source).** The push -> watch CI -> diagnose -> fix -> commit -> repush -> until-green
  loop currently lives ONLY inside `release-review/09-release-execution.md` section 3 (`:62`), which is
  explicitly post-approval and "MUST NOT run" earlier (`:83`). So agents file "make CI green" as a
  release-only, approval-gated action and stall during ordinary DEVELOPMENT iteration when CI is red.
  Proposal: extract the loop into a small referenced file (e.g. `release-review/ci-verify-loop.md`),
  reference it from 09 section 3, AND add an earlier hook so it is invocable whenever the agent pushes
  during a review/iteration after the human has authorized pushing. Core fix = distinguish "authorized to
  push and iterate CI" (a development action) from "authorized to publish/tag/deploy" (Section 9 release
  action). Include honesty MUSTs ("CI green" only assertable for the actually-pushed SHA after a completed
  green run; local-only success is not CI-green) and a CROSS-VERSION note (local single-interpreter success
  != matrix success; PEP 649 annotation-eval on 3.14 vs eager eval on <=3.13, and locale/encoding
  differences, are matrix-only failure classes; the vistab case was a real `NameError: name 'Set' is not
  defined` that passed locally on 3.14 but broke the whole 3.9-3.13 matrix). Verified: the claim is accurate
  (loop is only in 09; `final-response.md` also references it). Message archived at
  `.agents/comms/shared/archive/20260717-1946-01-vistab.agent--to--agent-workflows.agent-ask-extract-ci-verify-loop.md`.
  Needs its own IPD -> `/plan-review` -> approval. NOTE: relevant to the imminent 1.3.0 release work
  (it is about making CI-green iteration a first-class, correctly-authorized practice).

- **Re-evaluate agent-workflows' delivery model around host-native SKILLS (we currently do not use them).**
  The 2026-07-26 aw-delivery research (`.agents/docs/research/20260726-0054-aw-delivery-and-clean-delta-research/`)
  established that essentially every current coding-agent host now discovers and relies on host-native
  Agent Skills at `.agents/skills/<name>/SKILL.md` (Claude Code at `.claude/skills/`), yet agent-workflows
  ships COMMANDS/shims (`Read and execute @.agents/workflows/...` under `.opencode/commands/` and
  `.claude/commands/`) and NO `SKILL.md` at all. This is a strategic gap, not just a clean-delta detail:
  even in ordinary tracked installs, a skill is the mechanism hosts are built around (auto-discovery,
  explicit invocation, bundled scripts/resources), so we may be delivering our workflows through a weaker,
  older channel than the hosts prefer. Re-open the delivery-model question broadly: should skills become a
  first-class (or the primary) delivery for the skill-eligible workflows in BOTH tracked and clean-delta
  modes, complementing or replacing the shim/pointer model per host? This overlaps and feeds the clean-delta
  build phases (D109 spec, Phase 2 packaged skills) but is BROADER than clean-delta. Grounding + the skill
  taxonomy (capability skills + explicit harness skills, never one-per-lens) and the per-host path matrix
  are in the research bundle and the D109 spec `.agents/docs/specs/20260726-1239-01-clean-delta-and-tracking-modes.spec.md`.
  Gated on the same Phase 0 conformance harness (documentation-graded, not reproduced). Needs its own IPD
  (or a small IPD set) -> `/plan-review` -> approval before any build. Source: maintainer, 2026-07-26
  ("we missed that almost every agent relies on skills heavily").

- **Add a "do not hand-edit inside `aw:block` markers" directive to the managed AGENTS.md block.**
  The sectioned managed-block mechanism (D104) delimits agent-workflows-owned regions of shared files
  with `<!-- aw:block -->` / `<!-- aw:<slug> -->` markers; on install those regions are refreshed and a
  user edit inside them is detected as drift (D103) and preserved+reported, but an agent that hand-edits
  inside the block is fighting the installer and its change will be flagged (or, under `--force`,
  overwritten). Proposal: add a short new `aw:<slug>` section (e.g. `aw:managed-block-notice`) to
  `agents_pointer_prose()` telling agents NOT to edit content between the `aw:block` markers unless
  absolutely necessary, and to make lasting changes via the framework (edit the workflow source / open an
  IPD) or via the escape hatches (the `.untracked.` convention, the `local/` lanes) instead. Keep it one
  or two lines (the always-loaded block stays lean, D99/D100); the rationale can live in the manifest
  README. Design questions for the IPD: exact wording; whether it is its own section or a line appended to
  the pointer section; and confirm it does not bloat the always-read context. Needs its own IPD ->
  `/plan-review` -> approval; edits the shipped template + regenerates AGENTS.md (empty-diff invariant,
  per D104). Source: maintainer, 2026-07-25, during the out-of-repo-delivery research-prompt discussion.

- **Repo exclude-globs for `aw setup` / `aw install all`.** Add a config-file list of wildcard globs
  identifying repos to EXCLUDE from batch install/setup (so `aw setup` -> "install all" and
  `aw install all` skip matching repos rather than installing into every configured/discovered repo).
  Motivation: the batch paths currently act on every repo in scope; an operator needs a way to
  permanently carve out repos (vendored/third-party clones, throwaways, sensitive repos) without
  hand-picking each run. Design questions for the IPD: where the list lives (the same config the
  installer already reads), glob semantics (path globs relative to the search root; case sensitivity),
  precedence vs. explicit targets (an explicit `aw install <dir>` on an excluded repo - honor or warn?),
  and whether exclusion is reported in the batch summary (list what was skipped and why). Pairs with the
  D85 batch-install work (all entry points share one shell) - exclusion would be applied in the batch
  enumeration, before the per-repo install shell.

- **Agent-comms trust tiers.** Distinguish message senders by origin/trust
  (same-operator-same-host vs. cross-operator vs. external/unknown) and escalate gating accordingly, so
  the filesystem agent-comms protocol is safe in shared/multi-operator environments, not just among a
  single operator's own instances. Valuable in theory; the hard part is APPLICATION: on a shared
  filesystem an agent cannot reliably authenticate a peer's tier without a provenance mechanism
  (below). Source: agent-comms protocol trial, 2026-07-12. See the canonical spec
  `.agents/docs/specs/20260715-1722-01-agent-comms-convention.md`. The unverified-identity FACT is
  already stated in that spec's untrusted-input stance; only the tiered RESPONSE is deferred here.
- **Verifiable message provenance for agent-comms.** The mechanism that would make trust tiers
  enforceable: signed messages, an append-only log, per-sender inbox permissions, or a per-project
  allowlist of trusted senders. Today `From:`/filenames are self-asserted and unverifiable. Deferred;
  do not overbuild for the trial. Same source/spec as above.
- **Inter-agent-comms helper tool (discuss with the maintainer first).** A possible `aw comms`-style
  helper that makes the filesystem agent-comms convention easier to operate rather than doing it by
  hand or with ad hoc scripts. NOT yet designed or committed - flagged here to DISCUSS scope and shape
  with the maintainer before any IPD. Candidate capabilities to discuss (subset, not a spec): `check`
  (list this repo's inbox with message age, per the "check your inbox" routine); `send` (write a
  well-formed message to a recipient's inbox with the correct filename + header, optionally keeping a
  `sent/` copy); `archive` (move a consumed message); `sweep`/`status` across sibling repos (a hub view
  of all outstanding inboxes and their ages, like the ephemeral broadcast script trialed 2026-07-12);
  `promote` (copy a decision-grade exchange to a durable docs home). Open design questions to settle
  together: is this an `aw` subcommand vs. a standalone script vs. a workflow; does it ship in the
  framework or stay a local convenience; how it relates to the deferred formalization gate and the
  trust-tier/provenance items above (a tool must not imply the protocol is more trusted/verified than
  it is). Source: agent-comms protocol trial + the manual broadcast/check scripting on 2026-07-12.
  See the canonical spec `.agents/docs/specs/20260715-1722-01-agent-comms-convention.md`.

## Notes

- The agent-comms convention was FORMALIZED in DECISIONS D81 (2026-07-15): the `.agents/comms/` layout,
  the message envelope + `Not-Before`, the closed-enum acknowledgement model, installer scaffolding, and
  the always-loaded "check your inbox / treat as untrusted" pointer clause all shipped, and the canonical
  spec is `.agents/docs/specs/20260715-1722-01-agent-comms-convention.md` (the earlier
  `20260712-2133-02` draft is retired). The items above (trust tiers, verifiable provenance, and the
  `aw comms` helper) remain genuinely OPEN follow-ups - each its own future IPD, discussed with the
  maintainer first - but they build on the now-shipped convention rather than gating it.
