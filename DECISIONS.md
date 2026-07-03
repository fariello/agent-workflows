# Decisions Log

Append-only, dated record of significant decisions for the `ai-coding` repository,
with the reasoning, alternatives considered, and trade-offs. Newest entries at the
bottom of each dated section. This log exists so a future maintainer or an LLM with
no prior context can understand not just *what* the project is, but *why* it is the
way it is.

This is the same discipline the `release-review/` framework asks of every project it
reviews (see `release-review/00-run-protocol.md`, "Durable project knowledge and LLM
cold-start orientation"). We hold ourselves to it.

---

## 2026-06-29 - Establishing and hardening the release-review framework

The bulk of this repository's value is `release-review/`: an executable, modular
runbook that an AI coding agent (OpenCode, Antigravity, etc.) follows to perform a
deep pre-release review of *another* repository and leave it materially better. The
following decisions shaped it.

### D1. One canonical copy lives in `ai-coding`; other repos get copies

The framework had drifted across eight project repositories (`fariel.com`,
`a-consuming-repo`, `a-private-repo`, etc.), each having evolved different improvements.

- **Decision:** Treat `ai-coding/release-review/` as the single source of truth and
  synthesize the best of every divergent copy into it.
- **Alternatives considered:** (a) edit all copies in place - rejected as
  unmaintainable and guaranteeing further drift; (b) start from the single most
  evolved copy - rejected because valuable improvements were scattered across
  several copies.
- **Trade-off:** Other repos' copies are now stale until re-installed from here. We
  accept that in exchange for a coherent canon.

### D2. Generic framework, not project-specific checklists

Some copies (notably `a-consuming-repo`) had embedded project-specific checklists
(Node/Express/React/SQLite). These are useful as *examples* but wrong for a generic
runbook.

- **Decision:** Keep the canon project-agnostic. Generalize project-specific
  insights into universal concepts (e.g. the "live-interaction-surface" class of
  bugs) and drop hardcoded stack checklists. Section 9 (release execution) was
  rewritten from project-specific (npm/React, PHP/SSH deploy) to a generic,
  derive-the-commands-from-the-repo procedure.
- **Trade-off:** Slightly less turn-key for any one stack; far more broadly correct.

### D3. The eight reviewer personas

- **Decision:** Conduct the review from eight explicit expert viewpoints (QA/QC,
  testing/regression, UI/UX, architect, software engineer, power user, complete
  novice, stakeholder). A finding obvious to one persona is invisible to another;
  the novice and stakeholder views in particular catch usability and
  fitness-for-purpose problems engineers miss.
- **Problem found later & fixed:** "Reason from 8 personas in every section" is a
  large, unforced instruction that weaker models reduce to a token gesture. We
  mapped 2-3 lead personas to each section and added a forcing function (one
  recorded observation per lead persona per section) so the pass is real and
  verifiable without 8x redundant analysis.

### D4. The Fix Bar: fix-by-default, gated by Remediation Risk

Sourced from `prompts/fix-bar.md`.

- **Decision:** Replace the older "favor high-priority / minimize changes" framing
  with: **fix every finding by default; defer only when the Remediation Risk of the
  fix itself is Medium-High or higher** (the four axes: complexity, usability,
  security, functionality). Severity is for *reporting*; Remediation Risk is for
  *deciding*. Effort/time/token cost are explicitly excluded as reasons to skip.
- **Why:** The executing model is cheap and fast, so "is this important enough to
  fix?" is the wrong question; "is there a strong reason NOT to fix this?" is right.
  This closes the recurring loophole where cheap, safe correctness/usability fixes
  were dropped as "not important enough".
- **Trade-off / guard:** Fix-by-default invites scope creep, so the Complexity axis
  is the explicit counterweight against gold-plating, and over-scope items are
  flagged for removal. The `LIVE`/High data-integrity non-deferral rule overrides
  the Fix Bar (those must be fixed or escalated regardless).

### D5. Run artifacts are committed deliverables

- **Decision:** `repository-review/<RUN_ID>/` (per-phase reports, registers, plans,
  final report) is tracked and committed by default, not git-ignored local notes.
- **Why:** The reasoning trail is as valuable as the changes; making it durable lets
  a later run or person understand what was done and why. It also makes the run
  authoritative state (see D7).
- **Trade-off:** Adds review artifacts to project history; opt-out exists for users
  who want local-only artifacts.

### D6. Memory/resource and live-interaction-surface rigor as first-class

- **Decision:** Treat `MEM` (leaks, unbounded growth, lifetime, concurrency) and
  `LIVE` (resume/idempotency, multi-process coordination, spend/cap accounting,
  fetch completeness, overwrite-of-verified-output) as first-class, with a High
  severity floor and a mandatory non-deferral / release gate for the data-integrity
  class.
- **Why:** These are the defects hermetic unit tests pass over and that cause real
  production incidents; green tests are not evidence of correctness here.

### D7. Authoritative run directory over conversational memory

- **Decision:** `repository-review/<RUN_ID>/` is the authoritative record; TodoWrite
  and chat memory are only live progress aids.
- **Why:** Long multi-step runs degrade if state lives only in context. Externalizing
  state to files makes runs recoverable and (later) enables phase-isolated execution
  (see D11). This was the enabling decision for much of the reliability work.

### D8. Durable cold-start knowledge as a constructive objective

- **Decision:** Make "a no-context engineer or LLM can orient from the project's own
  docs" a first-class objective: establish/maintain intent, philosophy
  (`GUIDING_PRINCIPLES`), architecture (`ARCHITECTURE`/`DESIGN`), and decision
  rationale (`DECISIONS`/ADR) - creating missing docs by default under the Fix Bar,
  respecting the project's existing convention.
- **Why:** Prior versions only audited docs if they existed; a project with no
  rationale docs got a pass, which is the opposite of the goal.

### D9. Mine the conversation for intent - as a guarded secondary source

- **Decision:** When authoring "why" docs, recover intent from the current chat, but
  treat code/tests/existing-docs as authoritative for behavior; verify material
  claims with the user or mark passages "inferred, needs confirmation"; degrade
  gracefully when no history exists; never commit sensitive/ephemeral transcript.
  A bounded exception permits a few high-value questions to the user when intent is
  missing and unrecoverable.
- **Alternative rejected:** Treating chat as authoritative - would manufacture
  fiction and violate the honest-documentation principle.

### D10. Instruction-design hardening for reliable LLM execution

After the feature work, an instruction-design review fixed nine execution hazards,
notably: resolving the `09` filename collision (run artifact renamed
`implementation-plan.md` vs section `09-release-execution.md`); a mandatory
per-section execution loop (re-open the section file rather than work from memory);
de-duplicating the Fix Bar (canonical in `fix-decision-policy.md`); a single
canonical final-report table shape; a cross-cutting ownership map; planning-only
clarifications; and a restart loop guard.

- **Why:** The set had grown to ~15 always-on obligations; density (not context
  size) causes weaker models to silently drop low-salience rules. The fix is
  structural (forcing functions, single sources of truth), not deletion.

### D11. Reliability under model-capability differences (in progress as of this date)

Triggered by the question of whether Opus-class and Gemini-Flash-class models can
both execute the (large) set well.

- **Assessment:** It fits any modern context window many times over; the real risk
  is instruction-following degradation under *density*, worst on fast/small models.
- **Decisions:** (a) move reference material out of the always-read core into
  `reference.md`; (b) tier obligations MUST vs SHOULD so weaker models shed the right
  things first; (c) add a context-assembly ordering rule (front = MUST rules +
  section contract; middle = reference + prior registers; end = active section +
  exit-gate) to exploit recency/primacy and counter "lost in the middle"; (d) add
  per-section context contracts and exit-gate checklists; (e) document an optional
  phase-isolated execution mode (fresh context per audit phase, state carried by the
  run directory), keeping Sections 7 and 8 continuous.
- **Key nuance:** Recency-ordering and re-loading registers fix *instruction
  salience* but not *evidence grounding*. A re-loaded register is a summary, not the
  lived reading of the code. Therefore Sections 7-8 stay continuous, and Section 7
  must **re-open the actual source files cited by High/`LIVE`/`MEM` findings** rather
  than trust summaries.
- **Single instruction set, not a fork:** One set tiered by MUST/SHOULD, rather than
  a separate "lite" variant, to avoid drift between two copies.
- **Progress (2026-06-29):** Step (a) done - `reference.md` created and the
  type-code table, ID examples, and schema/CI lists removed from
  `00-run-protocol.md` (460 to 389 lines), leaving single sources of truth.
- **Completed (2026-06-29):** D11 fully implemented. Added to `00-run-protocol.md`
  an "Execution model" section defining MUST vs SHOULD tiers (with a small fixed
  global MUST set), the context-assembly ordering rule (front = MUST set + Fix Bar
  + section contract; middle = `reference.md` + prior registers; end = active
  section + exit gate), the model-capability expectation (MUST always required,
  SHOULD depth best-effort and honestly scaled on fast/small models), and an
  optional phase-isolated execution mode (fresh context per audit phase, run
  directory carries state, Sections 7-8 kept continuous). Each section file
  (01-09) now opens with a context contract and ends with an exit-gate checklist.
  Section 7 now MUST re-open the actual source files cited by High/`LIVE`/`MEM`
  findings before fixing (grounding mitigation), since a re-loaded register is a
  summary, not the lived reading of the code. README points at all of this.

### D12. The checked-in `release-review.zip`

- **Decision:** Ship a git-tracked zip of the framework plus a conservative Python
  installer, rebuilt whenever the source changes and verified with an installer
  dry-run.
- **Trade-off:** The zip is redundant with the unzipped source and can drift if not
  rebuilt; we accept that for one-step distribution into other repos. (Open future
  option: build it on demand instead of checking it in.)
- **Superseded (2026-06-29):** Reversed. The committed `release-review.zip` was
  removed (`git rm`, not git-ignored) and the installer now copies directly from the
  live `release-review/` + `.opencode/commands/` directories. Reasons: the zip was a
  redundant binary blob that bloated diffs and could not be reviewed, and it had to
  be rebuilt and re-verified after every source change - exactly the drift the
  trade-off warned about. Install-from-directory is correct by construction (no
  drift) and simpler. The "one-step distribution" benefit was illusory: the normal
  path is a git checkout, from which the files are already present. If a detached
  single-file artifact is ever needed, build a zip on demand at release time (e.g. a
  CI/release-tag asset) rather than committing it. While rewriting the installer we
  also fixed a stale bug: it had been adding `repository-review/` to `.gitignore`,
  which contradicts D5/D14 (run artifacts are committed deliverables). The installer
  no longer touches `.gitignore`; it only warns if the target repo ignores
  `repository-review/`.

### D13. Style conventions

- **No em dashes** in the framework Markdown/CSV (a package validation check
  enforces this); use hyphens or rephrase.
- **Numbered artifacts are proper-noun filenames, not a strict sequence:** when the
  implementation plan moved out of the `09` slot, the numbered set became
  `00-08, 10-12` with the plan unnumbered. The gap is intentional and signals the
  move.

### D14. Review scope excludes the framework's own directories

- **Problem:** With `repository-review/` no longer git-ignored (D5) and
  `release-review/` living inside the target repo, a run could review its own
  runbook and its own prior run records - wasting effort, generating findings/`KD`
  docs about the framework, and tempting the agent to edit the very instructions it
  is executing.
- **Decision:** Add a global "Review scope exclusions" rule: `release-review/` and
  `repository-review/` are out of *review* scope (no findings, not counted in
  project size/structure/tests/docs/cold-start), with a self-modification guard
  (never edit `release-review/` during a run; raise runbook concerns as a `DEC`
  note instead). It is an exclusion from *review*, not from *action* - the run still
  creates, writes, and commits `repository-review/<RUN_ID>/` and may read prior run
  records as input.
- **Exception:** if the user explicitly makes the framework itself the subject of
  the review (e.g. the repo that maintains `release-review/`), the exclusion on
  `release-review/` is lifted; `repository-review/` run records stay excluded.
- **Note:** these directories are not git-ignored (they are committed deliverables),
  so the exclusion is an instruction-level rule, not a `.gitignore` effect.

### D15. Installer performs a clean, git-aware sync (prunes stale framework files)

- **Problem:** After D12 the installer copied from the source directory but was
  additive-only: it added/overwrote files and never removed any. A target that had
  an older version of the framework would keep orphaned files when the framework
  renamed or dropped one (e.g. an old section file), so the agent could read stale
  instructions. There was no "clean install".
- **Decision:** Make the installer a clean sync by default. It computes the desired
  file set and prunes framework files in the target that are no longer in the source.
  Pruning is strictly scoped to the framework namespace (`release-review/` and the two
  `.opencode/commands/` wrappers) with defense-in-depth checks; it never touches
  `repository-review/`, user code, or anything outside that namespace, and never
  prunes the authoring/installer files.
- **Git handling:** the installer is git-aware but NEVER commits. Installed files are
  staged with `git add`; pruned tracked files are removed with `git rm` (staged);
  untracked files are written/removed on disk. The user reviews and commits with their
  own message. In a non-Git target it just writes/removes files. Pruned and
  overwritten files are backed up first (timestamped) unless `--no-backup`.
- **Alternatives considered:** (a) prune only with an explicit `--prune` flag -
  rejected because the default would still leave stale instruction files, defeating
  the goal; (b) auto-commit the sync - rejected as too surprising to do inside a
  user's repo; printing a suggested commit and leaving changes staged is the right
  boundary. `--no-prune` remains as an additive-only escape hatch.
- **Trade-off:** prune-by-default deletes files, which is more aggressive; mitigated
  by the strict namespace scope, backups, `--dry-run`, git staging (reviewable before
  commit), and `--no-prune`.

### D16. Generic pre-execution plan reviewer (`plan-review`)

- **Origin:** `a-consuming-repo/.agents/prompts/reusable/prompt_ipd_reviewer.md` was a
  strong but RhodyPACT-specific reviewer that checks a proposed Implementation Plan
  Document *before code is written* and revises it in place. Notably, its fix/defer
  gate was an independent re-derivation of our Fix Bar, which is good evidence the
  policy is sound.
- **Decision:** Generalize it into `release-review/plan-review.md` plus a
  `/plan-review` command wrapper - the plan-time sibling of release-review (plan
  review before building; release review before shipping).
- **Reuse over duplication:** the generic version references
  `fix-decision-policy.md` (the Fix Bar) and the eight personas in
  `00-run-protocol.md` instead of inlining its own copy, keeping single-source-of-
  truth. It falls back to applying the rules from memory if those files are absent.
- **Discover, don't hardcode:** a Step 0 discovers the project's guiding principles,
  contributor contract, plan location/format, production stack, and domain
  invariants, replacing RhodyPACT's hardcoded `GP-1..9`, `.agents/plans/` lifecycle,
  procurement edge cases, and Postgres specifics. The generic A-I rubric (data
  integrity, security, scalability, anti-regression, observability, testing, KISS,
  principles, domain invariants) is kept as a checkable baseline.
- **Safety property preserved:** it edits planning documents only, never code.
- **Form factor:** a single prompt, not a modular multi-phase framework, because plan
  review is a lighter job (KISS; the complexity axis of the Fix Bar applied to our own
  tooling). It ships with the framework and is installed/pruned like the other command
  wrappers (added to the installer's `COMMAND_FILES`).

### D17. Restructure into `.agents/workflows/<capability>/` with generated shims and an AGENTS.md pointer

- **Problem:** Two questions converged: (a) "do we keep adding top-level directories
  as we add capabilities (release-review, plan-review, ...)?" and (b) "how do we make
  these runnable across OpenCode, Claude Code, Codex, Antigravity, and plain VSCode
  agents without polluting the repo or duplicating instructions?"
- **Key distinction:** a capability has a tool-agnostic *body* (the runbook/prompt)
  and a per-tool *invocation shim* (the `/command` file). Conflating them is what
  created the "keep adding directories" worry. There is no cross-tool command
  standard; native `/commands` are inherently per-tool. But "read and execute <body>"
  works everywhere and is the universal fallback.
- **Decision:**
  1. Bodies live under `.agents/workflows/<capability>/` - each capability its own
     subdir (even single-file ones), so growth is "new subdir + manifest row", never a
     new top-level dir. Repo root stays clean. (Moved `release-review/` and
     `plan-review/` here from the repo root.)
  2. `.agents/workflows/index.md` is the manifest (a `command | body | description`
     table between markers). It is the single source of the capability list.
  3. The installer (`install-workflows.py`, moved up from inside release-review and
     renamed) reads the manifest and *generates* per-tool shims into
     `.opencode/commands/` and `.claude/commands/`; shims are never hand-maintained.
     Shims accept OpenCode `$ARGUMENTS` (e.g. `/plan-review <plan-path>`).
  4. `AGENTS.md` gets a one-line *pointer* block to the index - never the payload, so
     always-loaded context stays tiny (consistent with keeping reference material out
     of the always-read core).
- **Naming pushback applied:** the parent is `workflows/`, not `commands/` - the
  bodies are workflows; "command" is the per-tool invocation, which lives in each
  tool's own dir. Naming the body dir `commands/` would re-conflate the two.
- **Rejected:** putting the framework (or pointers to all of it) directly into
  `AGENTS.md`/`CLAUDE.md` - those are always-loaded context and would bloat every
  unrelated prompt with tens of thousands of tokens of occasionally-used instructions.
- **Cross-sibling dependency:** `plan-review` references `release-review`'s shared
  policy via `../release-review/...` (relative across siblings), preserving
  single-source-of-truth at the cost of a slightly longer path.
- **Run output unchanged:** `repository-review/<RUN_ID>/` stays at the target repo
  root (it is the project's review record, not agent tooling).
- **Also folded in:** removed the stale one-time `release-review-validation-report.md`
  (superseded by MANIFEST/index and direct installer testing); the scope-exclusion
  rule (D14) now refers to "the framework's own directory wherever installed" instead
  of a hardcoded `release-review/`.

### D18. Single-concern assessment workflows (the `assess-*` family)

- **Goal:** a set of focused workflows that each review/assess/improve ONE concern
  (performance, security, accessibility, UI/UX, self-documentation, documentation,
  functionality, use-cases, edge-cases, bugs, reliability, testing, architecture,
  API design, compatibility, supply-chain, guiding-principles, compliance,
  memory/resources) using the same approaches as release-review, but producing an IPD
  for human approval rather than fixing in place or auto-executing.
- **Where they sit:** between `plan-review` and `release-review` in a pipeline -
  `assess-<concern> -> IPD in pending/ -> plan-review (optional) -> approval ->
  execution`. `release-review` remains the broad, all-concerns, fix-in-place review;
  the assess family is the deep, single-concern, propose-a-plan front end.
- **Architecture - shared harness + lenses (not N standalone prompts):** one
  `assess/assess.md` defines the common protocol (Step 0 discovery, eight personas,
  Fix Bar applied as "what to propose", write a dated IPD into the project's
  pending-plans dir, never execute, report format). Each concern is a thin
  `assess/lenses/<concern>.md` (focus, lead personas, rubric). This avoids duplicating
  the persona/Fix-Bar/IPD preamble across 20 files (the drift trap) and makes adding a
  concern cheap: one lens + one manifest row.
- **Manifest carries the lens:** `index.md` gained an optional `lens` column so many
  commands can share the harness body; the installer (back-compatible with 3-column
  rows) passes the lens into each generated shim ("read and execute the harness,
  applying lens X"). The list we built: the very-high + strong-high tier from the
  exhaustive concern table, 20 lenses total.
- **Compliance is parameterized, not per-regime:** a single `assess-compliance` lens
  discovers (or takes via `$ARGUMENTS`) the applicable regimes (GDPR/CCPA, HIPAA, PCI,
  SOC2/ISO, accessibility law, responsible-AI, ...) rather than many near-empty
  regime-specific workflows. WCAG stays its own `assess-accessibility` lens because it
  is broad (any UI) and deep. The compliance lens is explicit that it assesses
  technical conformance signals, not legal advice, and separates "repo can fix" from
  "org-level control".
- **Never auto-execute:** every assessment writes an IPD with an explicit approval +
  execution gate and stops. Output location is discovered (the project's plan
  convention) or defaults to `.agents/plans/pending/`. `repository-review/` run output
  is unaffected.
- **Rejected:** composite "do 8+9 together" convenience workflows (the pipeline lets a
  user just run two), and a single `/assess <concern>` argument-only command (loses
  discrete discoverable `/assess-security` etc. slash commands).

### D19. Unified artifact location `workflow-artifacts/<workflow>/<run-id>/`, with installer migration

- **Problem:** `repository-review/<RUN_ID>/` was named when release-review was the only
  workflow. With a family of workflows (release-review, assess-*), a single
  release-review-centric output directory is misleading.
- **Decision:** Run records go to `workflow-artifacts/<workflow-name>/<RUN_ID>/` at the
  repo root - one timestamped directory per run, namespaced by the workflow that
  produced it. The run ID already encodes `YYYYMMDD-HHMMSS`, so there is no separate
  date level (rejected the deeper `.../<workflow>/YYYYMMDD/<run-id>/` form as redundant).
- **At the root, not under `.agents/`:** `.agents/` is agent *tooling/configuration*;
  run *outputs* are review evidence about the project. Keeping outputs at the root
  preserves a clean boundary (`.agents/` = tooling, `workflow-artifacts/` = outputs,
  your code = the rest) and keeps the scope-exclusion rule simple (exclude
  `.agents/workflows/` and `workflow-artifacts/`). IPDs are the middle case and stay in
  `.agents/plans/pending/` (a living, team-owned, lifecycle'd plan, established
  convention), not in `workflow-artifacts/`.
- **Volume:** deferred retention. One subdir per run is harmless (dozens/year);
  add retention/archival only if real volume appears (avoid premature complexity).
- **Migration of legacy repos (the install-time story):** the installer now detects a
  pre-restructure layout and migrates it, staged and reviewable, never committed:
  - Pre-D17: removes the old root `release-review/` framework dir (the new copy is
    installed under `.agents/workflows/`), backed up first.
  - Pre-D19: `git mv`s old `repository-review/<RUN_ID>/` run records into
    `workflow-artifacts/release-review/` so committed history moves (renames) rather
    than being lost. We chose to migrate historical artifacts (not just leave them) for
    a consistent end state; git rename detection preserves history.
  - Guarded so it never fires on the framework's own repo (`is_self`) or a repo already
    on the new layout; reports exactly what it moved/removed; honors `--dry-run`.
- **Verified** on a simulated legacy repo: artifacts moved as git renames, old root
  framework staged for deletion, user code and new install intact; and confirmed no
  false migration on ai-coding itself or a fresh new-layout repo.

### D20. Cybersecurity assessment lenses + an honest compliance-readiness lens

- **Request:** workflows for ransomware mitigation, intrusion detection, data
  exfiltration, broader cybersecurity, and readiness assessment for FIPS /
  NIST 800-171 / CMMC L2 federal regimes.
- **Key distinction (drove the design):** these split into two groups with very
  different feasibility for a repo-scoped, static, agent-driven assessment.
  1. **Security engineering practices** are partly repo-assessable - a codebase
     contains the building blocks (egress paths, security logging, backup/immutability,
     least privilege, integrity checks). Built as five new `assess-*` lenses:
     `data-exfiltration`, `intrusion-detection`, `ransomware-resilience`,
     `threat-model` (broad defense-in-depth, complementing the focused `security`
     lens), and `logging-audit` (foundational, cross-referenced by the others).
  2. **Formal compliance regimes (FIPS, NIST 800-171's 110 controls, CMMC L2)** are
     *mostly organizational/operational* - policies, training, physical security, IR
     processes, assessor evidence - none of which live in a repo. A repo agent can see
     only a thin technical slice.
- **Decision on Group 2 - build it, but as an HONEST readiness assessor, never a
  "compliance checker":** one parameterized `assess-compliance-readiness` lens with
  per-regime control catalogues. Non-negotiable honesty constraints baked into the
  lens: it states it is NOT a certification/audit/assessor-substitute; classifies every
  control as repo-verifiable / repo-partial / org-level-out-of-scope / N/A with
  evidence; **never emits an overall "compliant"/"ready" verdict**; and recommends a
  qualified human assessment (e.g. C3PAO for CMMC). In a federal/CUI context, a
  repo-scan that printed "CMMC L2 ready" would be actively harmful; under-claiming is
  the safe default.
- **Why not separate per-regime workflows:** one parameterized lens (regime via
  `$ARGUMENTS`) with internal FIPS / 800-171 / CMMC-L2 catalogues, consistent with the
  existing parameterized `compliance` lens; avoids many near-duplicate workflows.
- **Architecture:** all six are thin lenses on the existing `assess` harness + manifest
  rows (the cheap-to-extend path D18 was designed for); no new machinery. 29 commands
  total now. They reuse the Fix Bar/personas and emit IPDs for human approval, never
  auto-executing, and consistently route infrastructure/organizational controls to the
  operator as out-of-repo notes.

### D21. Installer updates an existing AGENTS file safely, in place

- **Problem:** the installer wrote the pointer to a root `AGENTS.md`, but a target may
  keep its agent instructions elsewhere (a-consuming-repo uses `.agents/AGENTS.md`). Writing
  root would create a second, ignored file. Also raised: is modifying a user-owned
  AGENTS file safe, or is it the `echo >> .bashrc` antipattern?
- **Decision - update the existing file, with a disciplined contract:**
  - **Discovery:** prefer an existing candidate (`AGENTS.md`, then `.agents/AGENTS.md`)
    and update that one; create root `AGENTS.md` only if none exists.
  - **Marker-delimited, idempotent:** the installer owns ONLY the region between
    `<!-- AGENT-WORKFLOWS:BEGIN -->` / `END`. A well-formed pair is replaced in place,
    so re-runs never stack blocks (the key difference from append-to-config installers).
  - **Touches only its region:** never reflows or edits the user's own prose.
  - **Fail-safe on malformed markers:** if exactly one well-formed BEGIN..END pair is
    not present (partial/hand-edited), it appends a fresh block rather than risk a
    destructive regex over user text.
  - **Backup first:** backs up the existing file before the first modification (unless
    --no-backup), and stages (never commits).
- **Verified** across four cases: existing `.agents/AGENTS.md` updated (no duplicate
  root file, prose intact); idempotent re-run (one block); malformed marker -> safe
  append with prose preserved; no AGENTS -> root created.

### D22. Generalization/productization review adopted as a lens, not a standalone workflow

- **Origin:** an external, detailed review prompt for making a repository more generic,
  extensible, configurable, and administrable (reuse across organizations, tenants, and
  deployments) was proposed for inclusion. It was a strong statement of the concern but
  ~700 lines of prose with its own personas, method, output format, and constraints.
- **Decision:** adopt its substance as a single lens,
  `assess/lenses/generalization.md`, on the shared `assess` harness, wired via one
  `index.md` manifest row and the generated `/assess-generalization` shims. Do not
  import it as a standalone workflow.
- **Why:** the harness already owns the personas, the Fix Bar, the IPD template, and the
  output format. Importing the full prompt would duplicate all of that (violating P8,
  single source of truth) and add bloat (violating P6, KISS). The prompt's unique value
  is its concern framing and rubric, which distill to a peer-sized (~45-line) lens. This
  is exactly the "a new lens file plus a manifest row" extension path the family was
  designed for (P7, solve the general case).
- **Boundary:** `generalization` is the reuse/productization sibling of the
  `architecture` lens (structural soundness); it cross-references and defers to
  `security` for authorization and secrets. Stated in the lens and docs so users know
  which to run.
- **Trade-off:** the concern overlaps `architecture` at the edges (configurability,
  extensibility). Accepted, because the center of gravity (de-hardcoding org-specific
  assumptions, config architecture, admin/operability, clean handoff) is distinct and
  was previously unserved; the boundary note manages the overlap.

### D23. Installer updates framework files by default; `--force` removed

- **Problem:** the installer refused to overwrite any framework file that differed from
  the source unless `--force` was passed, aborting the whole sync. But "the target file
  differs" is the normal case for an *update* (e.g. `index.md` after a new lens ships
  upstream), so the ordinary update path required `--force`. That trained users to pass
  `--force` reflexively, and it was internally inconsistent with D15, which already
  *prunes* (deletes) stale framework files by default.
- **Decision:** framework-namespace files are updated in place by default. A differing
  file is overwritten (backed up first unless `--no-backup`) rather than treated as a
  conflict, and `--force` is **removed entirely**. The only remaining hard error is a
  directory where a file must go, which still aborts with a clear message.
- **Why it is safe (same mitigations as D15's prune-by-default):** strict framework
  namespace scope, timestamped backups on by default, `--dry-run` to preview, and git
  staging (never commit) so the user reviews before committing. Overwriting a stale
  framework file is strictly safer than deleting one, which D15 already does by default.
- **Backup-gate fix:** the backup previously fired only when `--force` was set. With
  overwrite-by-default, the backup condition was changed to run on every overwrite
  unless `--no-backup`, so the default path is never a silent, un-backed-up overwrite.
- **User-owned surface unaffected:** the `AGENTS.md` prose region keeps its careful,
  marker-delimited, idempotent handling (D21). Only framework-owned files (everything
  under `.agents/workflows/` plus the generated shims) update by default.
- **Trade-off:** removing `--force` is a (tiny) CLI breaking change; a script passing
  it will error. Accepted: it had no remaining purpose once framework files update by
  default, and leaving a no-op flag would mislead. `--no-prune` and `--no-backup` are
  unchanged.

### D24. Installer skips Python build cruft and ignores its own backups dir

- **Problem (found while updating a target repo):** the installer copies every file
  under the source `.agents/workflows/` via `rglob`, so a stray `__pycache__/*.pyc`
  (e.g. from running `python3 -m py_compile` on the installer) would be installed into
  every target. Separately, the installer's own backup dir
  (`.agent-workflows-installer-backups/`) was left untracked in the target and could be
  committed accidentally by `git add -A`.
- **Decision (two hygiene fixes):**
  - **Skip build cruft:** a single shared `is_ignored_source_path` helper excludes
    `__pycache__` components and `.pyc`/`.pyo` files (alongside the installer's own
    files and `:Zone.Identifier`). It is applied at BOTH filesystem-walk sites (the
    source-collect walk and the prune walk) so the install set and the prune set cannot
    diverge. Applying it to the prune walk matters: otherwise a stray target `.pyc`
    would be seen as a stale framework file and deleted.
  - **Ignore the backups dir:** the installer adds `.agent-workflows-installer-backups/`
    to the target's `.gitignore` (idempotently; creating the file if absent). This is a
    deliberate, narrow exception to the installer's "does not modify `.gitignore`"
    posture: it manages only its own local scratch, never user or artifact ignores.
- **Contrast with `workflow-artifacts/`:** run artifacts are committed deliverables, so
  the installer still only *warns* if a target ignores them (D5); it never auto-ignores
  them. Only the local backup scratch is auto-ignored. The two are opposite on purpose.
- **Trade-off:** modifying `.gitignore` at all is a small departure from the previous
  absolute policy; scoped to one self-owned line, idempotent, staged-not-committed, and
  documented, so the risk is negligible.

### D22. assess-* workflows persist a run record to workflow-artifacts/

- **Gap found:** the `assess-*` workflows produced only the IPD (in the pending-plans
  dir); their report and evidence trail were shown in chat and then lost. This was
  inconsistent with `release-review`, which persists a durable run record, and it meant
  the reasoning behind an assessment was not auditable after the session.
- **Decision:** the assess harness now also writes a lightweight run record to
  `workflow-artifacts/assess-<concern>/<RUN_ID>/` - `report.md` (the full report),
  `findings.csv` (all findings, not just the top ones), `decisions.md` (decisions,
  assumptions, what was intentionally not proposed and why), `evidence.md` (what was
  inspected, for reproducibility), and `ipd-link.md` (cross-link to the IPD). Added
  `templates/run-report.md` and `templates/findings.csv`.
- **Committed by default**, consistent with release-review's artifact policy (D5), and
  out of review scope like other `workflow-artifacts/`.
- **Two outputs, distinct roles:** the IPD (pending-plans dir) is the living proposal
  in the approval/execution lifecycle; the run record (workflow-artifacts) is the
  durable evidence/report of the assessment run. The IPD location is unchanged.
- **Answer to "were they supposed to already?":** no - by original design (D18) the
  IPD was their only durable output; this decision adds the run record to match
  release-review.
- Target repos that already installed the assess workflows must re-run the installer
  to pick up the updated harness and the two new templates.

### D23. Committed-secrets/PII scanning: a deterministic tool + a lens + a release-review step

- **Gap found:** the workflows treated secrets as a *design habit* ("don't hardcode
  secrets", in the `security` lens) and outward *leakage* (`data-exfiltration`), but
  nothing systematically hunted for secrets/keys/PII/PHI actually **committed** to the
  repo - and crucially nothing scanned **git history**, where a secret removed from HEAD
  still lives and remains compromised.
- **Decision - deterministic tool + LLM judgment, not LLM-crawls-everything:** add
  `assess/tools/scan_secrets.py`, a dependency-free (stdlib), strictly read-only,
  redacting scanner of the working tree AND git history. It detects secrets
  (API/cloud/SaaS keys, PEM private keys, JWTs, tokens, passwords, connection strings,
  high-entropy strings, sensitive filenames) and PII/PHI (SSN, Luhn-checked cards,
  email, phone, IBAN). The tool does the exhaustive crawl; the LLM triages false
  positives and severity. Findings are CANDIDATES, never verdicts.
- **Safety properties (a scanner is itself a data hazard):** read-only (never rotates/
  purges/writes to the repo), no network, redacts every match to a masked preview so
  the report/artifact never becomes a new leak, bounded (size caps, binary skip,
  `--max-commits`/`--since`).
- **Prefer mature tools; recommend installing them:** if `gitleaks`/`trufflehog`/
  `detect-secrets` are present the tool runs and merges them; if absent it prints
  install guidance and the lens/report recommend installing one and adding it to CI.
  The built-in is a dependency-free safety net, explicitly not a replacement.
- **Remediation order is rotate-first:** any confirmed committed secret is assumed
  compromised, so the proposed plan is (1) rotate/revoke at the provider, (2) purge
  from history (`git filter-repo`/BFG - operator action, rewrites history), (3) prevent
  (secret manager, `.gitignore`, pre-commit hook, CI scan). Never surface a raw secret
  value in any artifact/finding/chat.
- **Wiring:** new `assess-secrets` lens (uses the shared harness -> IPD + run record);
  new manifest row; and a **mandatory committed-secrets scan step + exit-gate item in
  release-review Section 02**. Installer preserves the executable bit for tools/scripts.
- Target repos already installed need a re-install to get the tool, lens, and shims.

### D24. Guided wizard workflows: setup-repo and scaffold (interactive, may change files)

- **Request:** (1) a `setup-repo` "command" that walks the user through best-practices
  and security setup wizard-style, including installing useful tools; (2) a wizard-style
  way for repo owners to add custom assessments/workflows/commands with easy-to-edit
  files.
- **Key design tension resolved:** our workflows are agent-executed instruction files,
  not TUIs. "Wizard" therefore means an **agent-driven conversational wizard** (a `.md`
  that instructs the agent to ask step-by-step and act), not a standalone terminal TUI.
  This fits every agent, needs no new runtime, and - crucially - lets the wizard *reason
  about this specific repo* (stack, what is missing), which a dumb script cannot. For
  the purely mechanical tool installs, a small deterministic helper script does the work
  the wizard orchestrates.
- **setup-repo:** `setup-repo/setup-repo.md` (wizard) + `setup-repo/tools/setup_tools.py`
  (detect/report/install helper). Covers: install the framework, secret scanning (CI +
  local hook + baseline), `.gitignore` hygiene, hygiene files (README/CONTRIBUTING/
  LICENSE/.editorconfig), a stack CI baseline, a pre-commit multi-hook config, dependency
  hygiene, and branch-protection ADVICE (out-of-repo, cannot set from a repo).
  Principles baked in: **ask before each change, idempotent, respect existing, stage
  do-not-commit, never push**; tool installs go through the helper only after
  confirmation and use the platform package manager (no curl-pipe-to-shell).
- **scaffold:** `scaffold/scaffold.md` (wizard) to create a new `assess-*` lens,
  standalone workflow, or command, generate from the existing pattern, add the manifest
  row, and re-run the installer to regenerate shims - the guided form of the D18
  "new subdir + manifest row" extension path. Authoring/meta; edits framework files only.
- **These two are a new KIND:** interactive and file-changing (with consent), unlike the
  `assess-*` reviewers (propose-only) and `release-review` (broad fix-in-place). The
  index/README/ARCHITECTURE call this out so the distinction is clear.
- **Helper install script safety:** read-only detect by default; installs only with an
  explicit `--install NAME` (which the wizard runs only after the user confirms); tries
  the platform's known package managers in order; never downloads-and-pipes to a shell.
- 33 commands total now; dogfooded onto ai-coding.

### D25. Cross-tool support: honest per-tool docs + tailored shim frontmatter; installer end-message

- **Trigger:** two asks - (a) have the installer tell the user to run `/setup-repo` (or
  the equivalent read-and-execute in other tools) at the end; (b) verify this all works
  in Codex/Antigravity/etc. and is documented.
- **Verified reality (against current docs), not assumed:**
  - OpenCode: native `/command` from `.opencode/commands/*.md` (frontmatter uses
    `agent:`). Confirmed.
  - Claude Code: `.claude/commands/*.md` still works, but its frontmatter fields differ
    (`description`, `argument-hint`, `allowed-tools`, ...; NO `agent:`). Commands have
    also been merged into "skills" (`.claude/skills/<name>/SKILL.md`), which Anthropic
    now recommends; the commands form remains supported.
  - Cursor, Codex, Antigravity, VS Code Copilot: **no repo-file slash-command
    mechanism**. They can only use the universal "read and execute <path>" fallback.
  - The universal fallback works in ALL of them, because the bodies are plain Markdown +
    stdlib Python invoked via `python3`. The *substance* is portable by construction;
    only the `/command` convenience is tool-specific.
- **Decisions:**
  1. Installer end-message now recommends the next step in tool-aware form: "OpenCode/
     Claude Code: run /setup-repo" and "other agents: Read and execute
     .agents/workflows/setup-repo/setup-repo.md".
  2. Shim generator tailors frontmatter per tool: `.opencode` keeps `agent: build`;
     `.claude` drops it and adds `argument-hint` (matching Claude Code's documented
     fields). Both remain valid command files.
  3. Documented the truth: added a per-tool "Running a workflow (by tool)" table to
     `index.md` and README, explicitly stating that Cursor/Codex/Antigravity/Copilot use
     the read-and-execute fallback (no native commands), and that AGENTS.md aids
     discovery. ARCHITECTURE's invocation section rewritten to match.
- **Deliberately NOT done (Fix Bar complexity axis):** did not build a Claude Code
  `.claude/skills/` generator. The commands form works and is supported; a second
  generation path is complexity we do not yet need. Revisit if Claude Code deprecates
  `.claude/commands/`.
