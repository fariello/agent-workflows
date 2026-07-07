# Decisions Log

Append-only, dated record of significant decisions for the `agent-workflows` repository
(formerly named `ai-coding`; see D27), with the reasoning, alternatives considered, and
trade-offs. Newest entries at the
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

### D26. setup-repo establishes the plan/IPD lifecycle and is a drift-aware conformance check

- **Gaps found:** (1) `setup-repo` did not establish or document the plan/IPD lifecycle,
  even though the `assess-*`/`plan-review` workflows depend on it - and the convention
  was documented nowhere an agent would pick it up (not in AGENTS.md/CONTRIBUTING). (2)
  `setup-repo` was framed as first-time setup; its behavior on re-run / after a framework
  update was only a vague "idempotent" claim, not an explicit conformance check.
- **Decisions:**
  1. **Plan/IPD lifecycle is a setup step (1b).** setup-repo offers to create
     `.agents/plans/pending/` and a terminal dir (with `.gitkeep`) AND to write a short
     marker-delimited "Plan/IPD lifecycle" contract into `AGENTS.md`/`CONTRIBUTING` so
     ANY coding agent in the repo follows it, not just our workflows. Respects an
     existing convention; never renames.
  2. **Canonical terminal dir = `.agents/plans/executed/`** (matches the original IPD
     "executed" semantics), with `done/` accepted as an alias when a repo already uses
     it (discover-and-respect, do not forcibly rename - so ai-coding keeps its `done/`).
     Updated the assess harness Step 0 and the IPD template to say so.
  3. **setup-repo is explicitly idempotent + drift-aware = a conformance check.** One
     command for fresh setup, re-run, and post-update: it classifies each area
     conformant/partial/missing/outdated against the current baseline, reports the drift
     up front, and only proposes the gaps. If all conformant, it says so and stops.
  4. **Installer nudges conformance after updates:** the end-message detects whether the
     run actually changed/migrated anything and, if so, recommends re-running setup-repo
     as a conformance re-check (not just first-time setup).
- **Deliberately NOT done:** did not rename ai-coding's existing `.agents/plans/done/`
  to `executed/` - the "respect existing" rule applies to our own repo too.

### D27. Repository renamed ai-coding -> agent-workflows

- **Decision:** Renamed the GitHub repository (and its conceptual name) from
  `ai-coding` to `agent-workflows`.
- **Why:** the repo's center of gravity became a coherent, installable framework of
  agent workflows (`release-review`, `plan-review`, the `assess-*` family,
  `setup-repo`, `scaffold`) under `.agents/workflows/`, not a broad grab-bag of
  AI-coding resources. `agent-workflows` names literally what it is, which aligns with
  the honest-naming/precise-description discipline the project itself preaches
  (GUIDING_PRINCIPLES P2). `ai-coding` was too broad and `-toolkit` implied a loose
  collection of tools rather than a workflow system.
- **Scope of the change:** updated the git remote to
  `git@github.com:fariello/agent-workflows.git`; updated forward-looking references in
  README, ARCHITECTURE, and the installer usage/messages. The framework's INTERNAL
  paths (`.agents/workflows/`) are unaffected, so repos that already installed it are
  NOT broken by the rename.
- **History preserved:** earlier DECISIONS entries still say `ai-coding` because that
  was the true name when those decisions were made; per the append-only rule
  (GUIDING_PRINCIPLES P4) they are NOT rewritten. This entry records the rename instead.
- **Local working directory** left as `ai-coding/` deliberately (the local dir name
  is independent of the repo/remote name; renaming it would disrupt paths for no
  functional benefit).

### D28. assess-prose: a writing-style assessment for all prose

- **Request:** incorporate the maintainer's nonfiction-prose style guides
  (`a-private-repo/Prompts/nonfiction_prose_prompt_toolkit_{revised,updated}.md`) into an
  assessment covering all prose (docs, comments, prose in code, UIs, etc.).
- **Decision - a NEW `assess-prose` lens, separate from `assess-documentation`:** the
  documentation lens checks doc *accuracy/completeness*; this checks *how the words
  read* - style/quality - across every prose surface. Different concern, rubric, lead
  personas (an editor's eye), and a far broader target than "the docs". Reusable across
  repos, so a workflow, not a one-off IPD.
- **Source of truth:** distilled the toolkit's operative rules into a framework-owned
  `assess/references/prose-style.md` (mechanical-fingerprint avoidance: openings,
  transitions, sentence structures, prestige/filler words, rhythm/conclusion habits;
  modifier + rhetorical restraint; honest evidence; quiet-force positive model; no em
  dashes), attributed to the origin toolkit. The lens references it rather than
  duplicating the long banned-lists. The executive/board-specific *prompts* were left
  out (task-specific, not universal).
- **Surface-adapted intensity:** the toolkit targets executive/long-form documents, so
  the lens applies the universal rules everywhere but the full quiet-force bar only to
  long-form; it explicitly does NOT impose memo cadence on a code comment or a one-line
  UI string.
- **Two modes (author chooses; default = assess):** assess mode produces an IPD/run
  record leading with systemic patterns (not hundreds of line nits); an opt-in
  interactive mode walks the author through edits and MAY apply accepted changes in
  place. Prose edits are subjective and voice-bearing, so an author-in-the-loop option
  suits it; the lens makes voice preservation a hard constraint ("sanding off character
  is a defect, not an improvement"), echoing the toolkit's own warnings. This is the
  only assess lens that can edit prose in place, and only by explicit per-item consent.
- **Overlap acknowledged:** partly overlaps this repo's own no-em-dash / honest-docs
  principles and `assess-guiding-principles`, but is far more comprehensive and
  generally applicable, which justifies its own lens.

### D29. Local working directory renamed to match the repo (reverses D27's "keep the dir")

- **Reversal:** D27 renamed the GitHub repo to `agent-workflows` but deliberately left
  the local working directory as `ai-coding/`, arguing the local dir name is
  independent of the repo name. This decision reverses that: the local directory is now
  `<repo-root>/`, matching the repo and remote.
- **Why the reversal:** the name mismatch was a standing footgun. In practice it caused
  a real error - an agent reasoned "the repo is `agent-workflows`, so its files are
  under `<repo-root>/`" and wrote files to a stray path outside the repo. Any
  human or agent is prone to the same slip whenever the dir name and repo name disagree.
  Making dir == repo == remote removes the exception-to-remember and the whole class of
  wrong-path mistakes.
- **Hard rename, no compatibility symlink (deliberate):** a symlink at the old path
  would let stale `ai-coding` references keep working locally, masking exactly the
  forgotten references we want to surface - and it would not help anyone who clones the
  repo fresh (they only get `agent-workflows`). A clean rename surfaces every stale
  reference immediately so it can be fixed.
- **Safe by construction:** a git repo does not depend on its parent directory's name;
  remote, history, and `.git` are path-independent. Verified after the rename: remote,
  HEAD, and working tree intact.
- **Reference cleanup:** forward-looking path references were already `agent-workflows`
  (README install examples, installer, ARCHITECTURE). The only in-repo occurrences of
  `ai-coding` that remain are in DECISIONS.md dated entries and executed plan records,
  which are history and are NOT rewritten (append-only, GUIDING_PRINCIPLES P4). This
  entry supersedes the now-stale "local dir left as ai-coding" statement in D27
  rather than editing D27.

### D30. Installer moved to the repo root

- **Change:** moved `install-workflows.py` and `install-workflows.sh` from
  `.agents/workflows/` to the repo root (`<repo-root>/install-workflows.py`).
- **Why:** the installer is a human-run BOOTSTRAP tool, a different kind of thing from
  everything else in `.agents/workflows/`, which is agent-executed workflow instructions.
  Co-locating them muddied the directory's meaning, and burying the primary entry point
  three levels deep made the main invocation awkward
  (`.../.agents/workflows/install-workflows.py`). An installer is conventionally the
  top-level entry point. It also cleanly separates "things an agent runs" from "the tool
  a human runs to set things up".
- **Code change (not just a move):** `resolve_source_root` previously assumed the script
  sat inside `.agents/workflows/` (source = its own parent). It now derives source =
  `<script dir>/.agents/workflows/`, and `--source` accepts either a repo root
  (resolving the `.agents/workflows` subdir) or that directory directly.
- **Side benefit:** the installer no longer lives under the source tree, so it is
  naturally not part of what gets synced into targets (the old `SOURCE_EXCLUDED_NAMES`
  guard for it is now moot, kept only defensively).
- **Verified:** compiles; default source resolution, `--source <root>`, and
  `--source .../.agents/workflows` all resolve correctly; a full install into a fresh
  temp repo installs the framework + 34 shims and does not copy the installer in.
- **Docs updated:** README (install command + Contents), ARCHITECTURE (tree + prose),
  and the workflow bodies that reference the installer now point to the repo-root
  location and note it is not present inside an installed target repo.

### D31. Command-surface redesign: collapse `/assess-<concern>` into one `/assess <concern>`

- **Change:** replaced the 29 per-concern `/assess-<concern>` commands with a single
  parameterized `/assess <concern> [scope]` command. Executes the command-surface
  redesign IPD (2026-07-04), the `/assess` half only; the `/advise <persona>` half is
  deferred until the advise workflow exists.
- **Why:** 34 commands and growing well past 100 as concerns and personas multiply is an
  unusable slash-command menu and violates KISS. The assess family already shares one
  harness body selected by a lens, so a parameterized command matches the architecture
  exactly. Distinct workflows (release-review, plan-review, setup-repo, scaffold) keep
  their own commands.
- **Mechanism:** the manifest gains a single `assess` row that generates the one command;
  the `assess-<concern>` rows remain as the **concern catalog** (source of truth for each
  concern's lens) but no longer each generate a shim (`is_concern_catalog_row` in
  `install-workflows.py`). The `assess` shim body tells the harness to resolve the first
  argument to a lens (case-insensitive, with curated aliases `a11y`->accessibility,
  `perf`->performance, `deps`/`supply`->supply-chain, and closest-match fallback), and to
  list the concerns and ask when invoked bare.
- **Transition (open Q2, resolved):** the retired per-concern shims are REMOVED on the
  next install, not kept for a deprecation period. The installer's existing prune handles
  this automatically (they are no longer in the generated set); no special-casing needed.
- **Discoverability (sequencing, resolved):** the bare-invocation picker is built into the
  harness NOW so discoverability does not regress while the standalone `/list` catalog
  (the toolkit-discovery IPD) is still pending. The concern table in the README/index
  enumerates the valid `<concern>` values.
- **Aliases (open Q3, resolved):** a small curated alias map PLUS case-insensitive
  fuzzy/closest-match, expressed as harness instructions (LLM-resolved), not code.
- **Unchanged:** no workflow's behavior/content changes; the run-record directory
  convention stays `workflow-artifacts/assess-<concern>/<RUN_ID>/`.
- **Verified:** installer compiles; a fresh install generates exactly 6 shims per tool
  (5 core + `assess`) with the concern-resolution text in the `assess` shim; re-running on
  a legacy install prunes all 29 `/assess-<concern>` shims (`git rm`); the 29 concern
  lenses remain installed as the catalog. Dogfooded on this repo (34 -> 6 shims).
- **Docs updated:** README (quick-start example, assessments section, by-tool table),
  `index.md` (pipeline, cybersecurity/compliance examples, a manifest note documenting the
  `assess`/`assess-<concern>` command/catalog split).

### D32. Toolkit discovery (`/list-workflows`) and framework version stamping

- **Change:** executes the toolkit-discovery-and-version IPD (2026-07-04). Adds (a) a
  `/list-workflows` read-only discovery workflow, (b) a framework `VERSION`, and (c) a
  `--version` flag on `install-workflows.py` and `scan_secrets.py`. Completes the
  discoverability story that D31's command collapse leaned on.
- **Why:** there was no in-agent way to answer "what can this toolkit do, and which
  version is installed here?" - discovery meant reading `index.md` by hand, and that got
  worse once per-concern menu autocomplete went away under `/assess <concern>` (D31).
  Installed copies also carried no version, so neither a user nor `setup-repo`'s
  conformance check could say "you are behind."
- **`/list-workflows` (open Q1, resolved):** named `/list-workflows` (not `/list` or
  `/toolkit`) to avoid colliding with any existing `/list` command in a host tool. It
  READS the manifest (single source of truth) and reports grouped, run-ready output:
  core workflows, the `/assess` concerns (the `assess-<concern>` catalog rows, never as
  separate commands), and personas once they exist; plus the installed version. Optional
  filter argument (`/list-workflows security`, `/list-workflows assess`). Generated from
  the manifest so it cannot drift; read-only (no IPD, no file changes, runs nothing).
- **Version scheme (open Q2, resolved):** date-based `YYYYMMDD-NN` (calendar date plus a
  same-day sequence, e.g. `20260704-01`). Chosen over semver: this is a continuously
  evolving instruction set, not a library with a compatibility contract, so semver would
  overpromise. `NN` disambiguates multiple releases on one day.
- **Version location (open Q3, resolved):** BOTH a `.agents/workflows/VERSION` file (the
  machine source of truth the tools read) AND a `<!-- WORKFLOWS-VERSION: ... -->` header
  line in `index.md` (human/agent-visible when reading the manifest).
- **Installed-version stamping:** the `VERSION` file is copied into each target as part
  of the normal file install (it is not an installer authoring file, so
  `collect_source_members` picks it up automatically). The installed `VERSION` file IS
  the record - no separate state file - so source-vs-installed drift is just comparing
  two `VERSION` files. `read_version()` returns "unknown" when the file is absent (older
  install), and the tools/`/list-workflows` report that honestly.
- **Scope held:** no package registry, no auto-update, no telemetry - just listing plus a
  version string, exactly as the IPD scoped.
- **Verified:** both tools compile; `--version` prints `20260704-01` from source and from
  an installed copy; a fresh install generates 7 shims per tool (adds `list-workflows`),
  copies `VERSION` into the target, and prints the version in the summary. Dogfooded on
  this repo.
- **Docs updated:** README (core-workflows table, discovery hint, versioning bullet +
  `--version` option), `index.md` (version header line), manifest (`list-workflows` row).

### D33. Verification / evidence layer: `/verify` + `run_checks.py` (proof, not prose)

- **Change:** executes the verification-evidence-layer IPD (2026-07-04, the trust-critical
  top priority). Adds a `/verify` workflow and a deterministic helper
  `verify/tools/run_checks.py` that discovers the repo's OWN test/lint/build/type-check
  commands, runs the approved ones, and captures real exit codes/metrics/logs as committed
  evidence. Wires `release-review` and `assess-testing` to CITE that evidence instead of
  self-reporting.
- **Why:** every review/assess claim about tests/lint/build/type-check previously rested on
  the LLM's self-report. An enterprise reviewer will not accept "the agent looked and it is
  fine"; the GO recommendation is only as strong as its evidence. This is what makes the
  rest of the toolkit credible.
- **Command shape (open Q3, resolved):** its own `/verify` command + a reusable
  `run_checks.py`, so `release-review`, `assess`, and CI all share one evidence engine
  (rather than a mode of release-review).
- **Interactivity (open Q1, resolved):** confirm-before-each-check by default, with a
  `--yes` batch mode (CI / trusted). The interactive default DECLINES on no input (never
  runs without an explicit yes).
- **Discovery (open Q2, resolved):** auto-discover from `package.json` scripts, `Makefile`,
  `pyproject.toml`/`tox.ini`, `justfile`, and `.github/workflows/*` - PROPOSE, human
  disposes. `--add` adds a missed command; `--only` narrows categories. CI `run:` steps are
  surfaced as context-only (never auto-run; they often need services/credentials).
- **Safety posture:** allowlist of categories (`test`/`lint`/`build`/`typecheck`) PLUS a
  hard denylist (network/deploy/publish/release/install/push/docker-push/infra-apply/
  destructive) that is NEVER run, even under `--yes`. Unclassified commands are never
  auto-run (need explicit interactive yes; skipped under `--yes`). Each check is
  time-bounded (`--timeout`, default 600s); output captured, not acted upon; no network by
  the tool itself.
- **Stdlib-only,** matching `scan_secrets.py`; `--version`, `--format json|csv|text`,
  `--out`, `--list` (discovery-only).
- **Honesty (non-negotiable):** the result reports `discovered`/`ran`/`passed`/`failed`/
  `timed_out`/`skipped` separately; `all_ran_passed` is true only when at least one check
  ran and every check that ran passed. Skipped/denied/unclassified are NOT passes. Exit
  code: 0 = completed and everything that ran passed (or nothing ran); 1 = a run check
  failed/timed out; 2 = usage error. The exit code reflects only checks actually run.
- **Wiring:** release-review Section 03 (evidence-not-self-report block) and Section 08
  (final validation cites `verify-results.json`; an evidence gate downgrades GO to
  CONDITIONAL GO when relevant checks are unverified); the `assess` testing lens (establish
  pass/fail with evidence; UNVERIFIED with reason otherwise).
- **Scope held:** not a CI system, not its own test runner, no deployment; it runs the
  repo's own checks and records results. Does not write or fix tests.
- **Verified:** helper compiles; on a `package.json` fixture it discovers test/lint/build
  and DENIES deploy/release (even under `--yes`); a passing suite -> exit 0
  `all_ran_passed: true`; a broken test -> `failed: 1`, exit 1, `all_ran_passed: false`; a
  no-checks repo reports honestly with no implied success; interactive default with no
  input declines and runs nothing; metric scraping tightened to avoid false positives from
  version banners (validated against pytest/jest-style output). Fresh install generates 8
  shims/tool (adds `verify`) and copies `run_checks.py`; `--version` works from the
  installed copy. Dogfooded on this repo.
- **Docs updated:** README (core-workflows table, count 6->7), `index.md` (`verify` row).

### D34. `advise` workflow + expert-persona library (interrogate and coach)

- **Change:** executes the advise-workflow-and-personas IPD (2026-07-04). Adds a new
  capability MODE - interactive interrogation and mentoring - as one parameterized
  `/advise <persona>` command (harness + a `personas/` library), mirroring the proven
  assess (harness + lenses) pattern. Activates the `/advise <persona>` half deferred in
  D31 and the personas slot in `/list-workflows` (D32).
- **Why:** the requested "grill me" interrogator and the "spec tutors/experts" are the same
  shape (an expert examines something, asks questions, coaches). A command per expert would
  blow past 100 commands (the sprawl KISS worry); one harness parameterized by a persona
  caps the surface at one while allowing unlimited experts (add a persona file + a manifest
  row). This is a different mode from the eight REVIEW personas: those FIND faults and emit
  a register; advise personas INTERROGATE and MENTOR interactively.
- **Command name (open Q1, resolved):** `/advise` (matches the D31 command-surface design
  and the README; neutral, no known built-in clash). The skeptic persona covers the
  "grill me" role under this neutral name; `/grill-me` is deliberately not used (believed
  to be a Gemini built-in, unverified - avoided regardless).
- **Roster (open Q3, resolved):** all seven built now - `skeptic`, `spec-editor`,
  `architect`, `red-teamer`, `staff-engineer` (mentor), `domain-expert`, `naive-user`.
  Each charter states its questioning style, what "good" looks like from its viewpoint, and
  an explicit "do NOT" guardrail (skeptic not merely contrarian; mentor does not
  rubber-stamp; red-teamer gives no exploit how-tos; etc.) so the voices are genuinely
  distinct. More can be added via `scaffold`.
- **Write behavior (open Q2, resolved):** coaches interactively; MAY edit a planning/prose
  artifact only with per-change consent (editing a plan is allowed, like prose interactive
  mode); defaults to recommending changes; NEVER executes code. Matches the toolkit's
  ask-before-each-change discipline.
- **Run record:** on by default - a `session-summary.md` under
  `workflow-artifacts/advise-<persona>/<RUN_ID>/` (persona, artifact, key questions and
  answers, gaps/risks surfaced, improvements agreed, follow-ups). Consistent with assess/
  verify durability; it is a session record, not an IPD, and gates nothing.
- **Installer generalization:** `is_concern_catalog_row` now matches a `CATALOG_ROW_PREFIXES`
  tuple (`assess-`, `advise-`), so `advise-<persona>` rows are catalog entries (persona
  charters), not commands; a single `advise` row generates the one shim with persona-
  resolution text (aliases: grill/grill-me->skeptic, mentor->staff-engineer,
  red-team/adversary->red-teamer, naive/novice->naive-user, etc.). `/list-workflows` updated
  to surface personas as a real group.
- **Scope held:** no command per persona; personas do not duplicate the review personas'
  fault-finding-register role; roster kept focused and genuinely distinct.
- **Verified:** installer compiles; fresh install generates 9 shims/tool (adds one
  `advise`, no `advise-*`/`assess-*`), copies all 7 persona files, and the `advise` shim
  carries the persona-resolution/picker/alias text. Dogfooded on this repo.
- **Docs updated:** README (core table `/advise` row + a Coaching section + count/prose),
  `index.md` (advise family prose + generalized catalog-collapse note), `/list-workflows`
  persona language.

### D35. Lifecycle workflows: `spec`, `incident`, `release-notes`, `migrate`

- **Change:** executes the lifecycle-workflows IPD (2026-07-04). Adds four distinct
  standalone workflows that fill the enterprise-delivery stages the toolkit under-served,
  so it spans discover -> build -> review -> ship -> operate, not just assess/review.
- **Why:** the toolkit was strong on assess/review but thin at the front of the funnel
  (requirements) and the back (incident, release, migration). These are genuinely distinct
  ACTIVITIES (not concerns or personas), so each warrants its own workflow rather than
  folding into the assess/advise families.
- **Scope (open Q1, resolved):** build all four now (each is a bounded, guided workflow on
  established patterns), rather than shipping only `spec` first.
- **Names (open Q2, resolved):** `spec`, `incident`, `release-notes`, `migrate` (short,
  consistent with `assess`/`verify`/`advise`), not the wordier `draft-spec`/`post-mortem`/
  `changelog`/`migration-plan`.
- **release-notes placement (open Q3, resolved):** its own `/release-notes` command (a
  reusable notes/versioning step), NOT folded into release-review Section 9 - which now
  REFERENCES it in its "Finalize, version, and commit" step.
- **Behavior:** guided/ask-first writes to the repo's conventional location.
  - `spec`: produces a reviewable specification (goals/non-goals/users/requirements/
    testable acceptance criteria/constraints/open questions); the PRODUCE half opposite
    `/advise spec-editor`'s INTERROGATE half; feeds plan-review.
  - `incident`: a blameless post-mortem (timeline/impact/systemic factors/what went right-
    wrong), emitting follow-up action IPDs into pending/. Explicitly REPO-SCOPED and honest
    that the operator holds the real monitoring/SIEM/on-call data; must not fabricate a
    timeline or root cause.
  - `release-notes`: decides the version bump from the actual changes (detects the repo's
    scheme), drafts the changelog + human notes (assess-prose style, breaking changes
    prominent), updates CHANGELOG/version files with confirmation. NEVER publishes, tags,
    pushes, or deploys.
  - `migrate`: assess-and-plan a high-risk migration - blast radius (evidence-based, cites
    files), invariants that must survive, a staged/reversible plan with characterization
    tests first and per-stage rollback + `verify` checks. Emits an IPD via the assess
    pipeline; does not execute. (The installer's own legacy-layout migration, D17/D19, is
    the archetype.)
  - `incident`+`migrate` emit follow-up IPDs into `.agents/plans/pending/`.
- **Scope held:** not project management, ticketing, roadmapping, or actual CI/CD/deploy
  execution. `release-notes` drafts + bumps but does not publish; `incident` structures a
  post-mortem but does not monitor; `migrate` plans but does not execute.
- **Verified:** fresh install generates 13 shims/tool (adds `spec`, `incident`,
  `release-notes`, `migrate`) and copies the four bodies. Dogfooded on this repo.
- **Docs updated:** README (four core-table rows + count 7->11 core), `index.md`
  (lifecycle prose), release-review Section 9 (references `release-notes`).

### D36. Framework self-tests + `assess-all` rollup

- **Change:** executes the self-tests-and-assess-all IPD (2026-07-04), both parts. Part A:
  automated tests (`tests/`) for the framework's own Python tools. Part B: an `assess-all`
  cross-concern rollup workflow.
- **Why (A):** the toolkit preaches assess-testing and the verification/evidence layer
  (D33), yet its own tools had zero automated tests - a credibility gap; every installer
  change had been validated by hand. The framework was failing its own bar. **Why (B):**
  running each assess concern separately yields many IPDs with overlapping/conflicting
  findings and no cross-concern prioritization; a rollup gives a single prioritized view.
- **Scope (open Q1, resolved):** build both parts now (dependencies - parameterized assess
  D31, verify D33 - are done).
- **Test framework (open Q3, resolved):** stdlib `unittest`, zero dependencies, consistent
  with the tools (the framework eats its own zero-dependency dog food); not pytest.
- **Part A coverage:** installer (fresh install, idempotent re-run, prune of stale/legacy
  `assess-<concern>` shims, `--no-prune`, legacy-layout migration, dry-run makes no
  changes, catalog-row collapse + the `assess-all` exception, `--version`, installer not
  copied into target); scanner (planted secret in the working tree AND git history,
  redaction never leaks the raw value, clean-repo zero, `--version`); run_checks
  (classification, denylist blocks dangerous, denylisted never runs even under `--yes`,
  honest pass/fail exit codes, no-checks honesty, metric-scrape cleanliness, `--version`).
  E2E tests run the tools as subprocesses against throwaway git repos; unit tests import
  the pure functions. 25 tests. Scope guard: mechanical tools only, not the instruction
  prose (prose is reviewed by `/assess prose`, not unit-tested).
- **Part B design:** `assess-all` reuses the assess harness per lens and adds the value
  layer - de-dupe overlapping findings, cross-concern priority (a Blocker security finding
  outranks a Low prose nit; uses the Fix Bar), surface conflicts - then emits ONE
  consolidated IPD plus a rollup run record. The lenses stay the single source of truth
  (open Q surface, resolved): `assess-all` is its own command that ORCHESTRATES them, never
  a second place that defines concerns.
- **assess-all default (open Q2, resolved):** confirm scope and cost FIRST - present the
  concern groups, note that a full run is expensive, default to a sensible set, and let the
  user pick all/group/subset. Never silently run all concerns.
- **Installer generalization:** added `CATALOG_PREFIX_EXCEPTIONS = {"assess-all"}` so
  `assess-all` gets its own shim despite the `assess-` prefix (it is a standalone command,
  not an assess concern). Covered by a self-test.
- **Verified:** all 25 self-tests pass; confirmed they FAIL when a tool is deliberately
  broken (temporarily neutered the denylist -> the denylist test failed; restored -> green)
  - proving they are real, not vacuous. Fresh install generates 14 shims/tool (adds
  `assess-all`), which the installer test asserts. Dogfooded on this repo.
- **Docs updated:** README (assess-all in the Assessments section), `index.md` (assess-all
  prose), CONTRIBUTING (a Self-tests section with the runner command; also fixed a stale
  `/assess-secrets` -> `/assess secrets`).

### D37. Guided onboarding: the `getting-started` tour/router

- **Change:** executes the guided-onboarding-tour IPD (2026-07-04), the last of the seven
  roadmap IPDs. Adds a `getting-started` workflow: a guided in-agent tour that orients a
  newcomer and routes them to the right workflow. In-agent complement to the README.
- **Why:** the README is a good written on-ramp, but a first-timer in an agent still has to
  read it and map it to their situation. A guided tour meets them where they are ("what are
  you trying to do?" -> route + run with consent), lowering the adoption friction that
  decides whether a toolkit gets used or installed-and-forgotten. Fits the guided-wizard
  pattern (setup-repo, scaffold).
- **Sequencing:** built LAST, deliberately, so it teaches the FINAL command surface - after
  the parameterized commands (D31), catalog (D32), verification (D33), advise (D34),
  lifecycle (D35), and assess-all (D36) were all settled. (The IPD's open Q2 about
  before/after the surface is thus moot.)
- **Name (open Q1, resolved):** `getting-started` (descriptive and unambiguous), over
  `start`/`tour`/`onboarding`.
- **Scope discipline (open Q3, resolved):** it ORIENTS and ROUTES only - detect context,
  explain the mental model briefly, ask the goal, route (offer to run, with consent), and
  give the exact per-tool invocation. It references `/list-workflows` for the full catalog
  rather than re-enumerating it, and does not restate the README - a guide, not a second
  source of truth. Read-only by default; runs another workflow only with explicit consent;
  must adapt to the detected context/goal rather than recite a fixed script.
- **Verified:** fresh install generates 15 shims/tool (adds `getting-started`) and copies
  the body. Dogfooded on this repo.
- **Docs updated:** README (quick-start "New here?" pointer, core-workflows table row, count
  11->12 core), `index.md` (getting-started prose).
- **Milestone:** with this, all seven 2026-07-04 roadmap IPDs (D31-D37) are executed. Next
  is the batched rollout of the whole set into the other `a local checkout dir/*` repos (exclude a-consuming-repo).

### D38. Installer fixes surfaced by the batched rollout: mode-bit staging + gitignored shim dirs

- **Context:** rolling D31-D37 into 26 `a local checkout dir/*` repos exposed two installer defects (both
  fixed here, with self-tests).
- **Fix 1 - executable-bit staging.** The tool scripts (`scan_secrets.py`, `setup_tools.py`,
  `run_checks.py`) are executable in the source, but `write_file` (a) returned early when
  content was already current, never syncing the mode, and (b) applied the exec bit AFTER
  staging (in `install_all`) without re-staging - so every target repo showed a mode-only
  change (100644 -> 100755) left UNSTAGED, missing the commit. `write_file` now takes an
  `executable` flag, syncs the bit itself, treats a mode-only difference as a real change
  (a `chmod` action) that is applied and staged, and skips only when both content and mode
  match. Result: a re-run leaves nothing unstaged; the index records 100755.
- **Fix 2 - gitignored shim directories.** A repo may legitimately gitignore `.opencode/`
  (or `.claude/`). The installer's hard `git add` on those shims raised `SystemExit`,
  ABORTING the whole install partway (hit in `reddit-data`). Added `git_add_optional`: for
  shim paths, an "ignored by .gitignore" failure warns once and continues (the shim is
  still written to disk and works locally, just untracked); any other git failure still
  raises. Framework-namespace body files under `.agents/workflows/` still hard-fail if they
  cannot be staged (that is the core and must be tracked).
- **Self-tests:** `test_tool_scripts_are_executable_and_staged` (exec bit present, indexed
  as 100755, re-run leaves nothing unstaged) and `test_gitignored_opencode_does_not_abort`
  (install completes, warns, writes shims to disk, stages `.claude`/`.agents` but not
  `.opencode`). Suite now 27 tests, all passing.
- **Rollout note:** the 26-repo rollout was completed before this fix using manual
  follow-up commits for the mode bits and a manual completion for `reddit-data`; this
  decision makes the installer do it correctly on its own going forward. (`reddit-data`
  separately un-gitignores `.opencode/` at the user's request so its OpenCode shims are
  tracked like the other repos.)

### D39. Release-review loudly warns about pending agent plans and staged prompts

- **Context:** a repository driven by agent workflows accumulates prepared-but-unexecuted
  work - IPDs in `.agents/plans/pending/`, plans whose `Status:` line still says pending,
  and staged prompt files queued for a later run. `release-review` already reconciled
  `TODO.md`/backlog and in-code `TODO`/`FIXME`, but it had NO awareness of these pending
  plans/prompts. Shipping while an approved-but-unexecuted plan sits in `pending/` is a
  common, easy-to-miss way to release with known planned work silently skipped.
- **Change:** pending agent plans and staged prompts are now a first-class cross-cutting
  concern. Section 1 discovers and inventories them (path + status), classifies each
  against the release, and never executes them. Section 8 applies a **pending-plans /
  staged-prompts gate**: any in-scope pending plan/prompt (or a status/location mismatch,
  e.g. a `done/` plan still marked pending) forces a loud, bold `WARNING` in the Go/No-Go
  and the summary and blocks a clean GO (at most CONDITIONAL GO, with each item named as a
  prerequisite/decision). Added a dedicated "Pending plans / staged prompts" section (with
  a table) to `templates/final-response.md`, a new ownership-map row and protocol section
  in `00-run-protocol.md`, and matching exit-gate checkboxes in Sections 1 and 8. Docs
  (`README.md`, `MANIFEST.md`) updated to list it among the on-every-run guarantees.
- **Why loud, not silent:** these items are concrete, often-already-approved units of work,
  distinct from open-ended backlog. Burying them in a table would defeat the purpose; the
  user explicitly wants a prominent warning at the Go/No-Go so the release decision is made
  with eyes open. The review still never auto-executes a plan - it surfaces for a human.
- **Scope:** instruction-only change to the `release-review` workflow bodies and templates;
  no code/tool change. VERSION bumped 20260704-01 -> 20260704-02.

### D40. Secret scanner: stop nagging to install a mature scanner when one is present

- **Context:** `scan_secrets.py` printed "RECOMMENDED - install a mature scanner for stronger
  assurance" (and a matching JSON `note`) whenever ANY of the three known external tools
  (gitleaks, trufflehog, detect-secrets) was missing - so it nagged even when gitleaks (a
  mature scanner) was installed and had already been run, just because the other two were
  absent. The recommendation is only meaningful when NO mature scanner is available.
- **Change:** `emit` now branches on whether a mature scanner is actually present/used:
  (a) present -> no nag; any still-missing tools are listed only as "optional - additional
  scanners for broader coverage"; the JSON note says a mature scanner was run alongside the
  built-in one. (b) none present -> keep the "RECOMMENDED - install" nag (the original,
  correct behavior for that case). (c) `--no-external` -> say external scanning was skipped
  this pass rather than implying none are installed (previously it hit case (b) and nagged,
  which was misleading). A `skipped_external` flag is threaded from the caller so the
  all-False `avail` under `--no-external` is not confused with "nothing installed".
- **Why:** the nag existed to push users toward a real scanner; once one is present, the
  push is noise and undermines the tool's credibility. Honest, state-appropriate messaging
  over a blanket recommendation (P2).
- **Self-tests:** three added to `test_scan_secrets.py` calling `emit` directly with a fake
  `avail` (deterministic, independent of what is installed on the test host): no-nag when a
  mature scanner is present, nag when none is present, and skipped-message under
  `--no-external`. Suite now 30 tests, all passing.
- **Scope:** tool + tests only; no workflow-body change. VERSION 20260704-02 -> 20260704-03.

### D41. `benchmark` workflow: informational performance benchmarking, isolated by design

- **Context:** the toolkit covered correctness, security, docs, and release discipline but
  had no way to gather PERFORMANCE information about a repo, and doing this well is
  environment-sensitive (a number is meaningless without the machine it was measured on).
  Requested with concrete requirements: easy reproducible runs, deep environment capture,
  flag known good/bad configs with remedies, warm-up over >=2 iterations, HPC awareness
  (detect Slurm and offer to submit), a share-back mechanism, and zero impact on the
  project's own performance from including the benchmarks.
- **Shape:** a guided wizard body (`benchmark/benchmark.md`) plus a stdlib-only,
  read-only helper (`benchmark/tools/bench_env.py`), mirroring the verify/setup-repo split
  (judgment in the body, deterministic mechanics in the tool). The helper does deep host
  capture, config diagnosis with copy-pasteable remedies, HPC scheduler detection, a
  bounded disk probe, and a cache warm-up; it emits json/csv/text, supports `--scrub` for
  shareable output, and `--version`. Self-tests: `tests/test_bench_env.py` (16 tests:
  each diagnosis fires on its pitfall and stays quiet on a clean env, scrub redacts identity
  but keeps fs type/size, the probe is bounded and cleans up, warm-up reads files, the JSON
  carries all required context fields, bad-path is a usage error, `--version`). Suite 30 ->
  46, all pass.
- **Key decisions and their "why":**
  - *Informational, not a regression gate, by default.* Perf is noisy and environment-bound;
    failing a build on it by default would be dishonest (P2). An opt-in baseline-comparison
    mode (Step 7) exists for users who explicitly want a guardrail, kept out of CI unless
    they wire it in.
  - *"0% impact" means inclusion, not measurement.* The benchmark suite lives in an isolated
    `benchmarks/` dir in the TARGET repo (not this framework) that ships no import into the
    product and adds no runtime cost when unused; timing is out-of-process. We explicitly do
    NOT claim zero measurement overhead - no harness can. Being honest about this beats a
    false absolute (P2).
  - *Cases live in the target repo.* The framework ships only the env tool + the wizard; the
    suite is versioned with the project it benchmarks, so any user can clone and run it. This
    also serves the isolation and reproducibility requirements.
  - *Read-only on system state; suggest, do not apply.* The tool reads proc/sys and read-only
    CLIs and prints remedies (e.g. copy an NFS working set to node-local scratch, set the
    performance governor) rather than changing governors/mounts/swap itself (P10 safety).
  - *HPC submit only on explicit per-submission consent*, never under a batch/`--yes` flag,
    with "generate the script for you to run" as the conservative default - matching verify's
    denylist posture toward actions that affect shared/remote resources (P10).
  - *Offline sharing.* The tool makes no network calls; it produces a bundle and can `--scrub`
    identity. Any actual sharing is the user's explicit action.
- **Alternatives considered:** (a) generic auto-timing of existing entry points with no
  authored suite - rejected as the default for weaker reproducibility and isolation, though
  the wizard can still time an existing harness where one exists; (b) in-process
  instrumentation - rejected because it couples the harness to the product and undermines
  the isolation guarantee; (c) auto-submitting HPC jobs - rejected as unsafe by default.
- **Scope:** new workflow (body + tool + tests + manifest row + shims) and doc-sync
  (README count 12 -> 13 core, ARCHITECTURE tree + a new section). VERSION 20260704-03 ->
  20260704-04.

### D42. Accessibility lens covers terminal / text UIs, not just WCAG 2.1 AA

- **Context:** the `accessibility` lens targeted WCAG 2.1 AA, which is written for web/GUI
  and is largely silent on terminals. In practice coding agents therefore skipped
  terminal/ANSI accessibility entirely (color-only status signals, load-bearing dim text,
  ignoring `NO_COLOR`/non-TTY), even though ANSI-styled CLI output is exactly where a lot of
  developer tooling lives and where colorblind/low-vision/screen-reader users are underserved.
- **Change:** the lens gains a distinct, clearly-labeled "Terminal / text UI (WCAG-inspired,
  not literal WCAG)" rubric that translates POUR to text interfaces with CONCRETE, checkable
  items: color/style never the sole signal (require a word/symbol/prefix); no load-bearing
  `SGR 2` dim or `SGR 5` blink; honor `NO_COLOR`/`FORCE_COLOR`/`TERM`/`isatty()` and degrade
  through 256/16/none; no hardcoded fg that assumes a bg; motion only on a TTY with a plain
  mode; screen-reader/braille-friendly linear alternative to box-drawing/progress redraws;
  structure not conveyed by alignment/color alone. Verification: read the styling code (grep
  `\x1b[`, dim/blink, colorama/chalk/rich/termcolor/tput) and RUN the tool three ways
  (TTY / piped / `NO_COLOR=1`) - identical raw escapes in all three is a finding. The lens
  title and scope now explicitly cover "whichever surfaces the project has" (a repo can have
  both a web UI and a CLI).
- **Preserve the polish (user's key ask).** Accessibility here is NOT "remove color/spinners/
  boxes". The prescribed remedy order is: (1) add the redundant cue (keeps the full
  experience, low risk, propose by default); (2) auto-degrade on signal (full styling on a
  color TTY, plain when NO_COLOR/piped/dumb) so the polished path stays the default; (3) only
  when an accessible variant would MATERIALLY change look/feel, propose a toggle (env var
  `NO_COLOR`/`ACCESSIBLE=1` and/or a `--no-color`/`--plain`/`--accessible` flag) rather than
  forcing a downgrade on everyone.
- **Interactive consult, IPD-only.** The harness already produces an IPD and never executes;
  this lens adds that for any fix which would noticeably change the tool's visual character,
  it must ASK the user interactively (keep-as-default-with-degrade? gate behind a toggle?
  which flag name?) and record the answers/trade-offs in the IPD, rather than baking a
  redesign in silently. Small non-visual fixes (add `ERROR:` prefix, honor `NO_COLOR`, drop
  blink) need no consult. Non-interactive runs propose the least-disruptive option and list
  look/feel-changing alternatives as open questions.
- **Framing decision:** kept WCAG 2.1 AA as the standard for graphical UIs and labeled the
  terminal rubric "WCAG-inspired," honestly NOT claiming formal WCAG conformance for a
  terminal (P2 honest-not-aspirational). Alternative (folding terminal checks inline into the
  POUR bullets) was rejected because it would blur that honesty line.
- **Scope:** lens + manifest description + README concern-table note; no code/tool change, so
  self-tests are unaffected (still 46, and prose lenses are not unit-tested per CONTRIBUTING).
  VERSION 20260704-04 -> 20260704-05.

### D43. Self-review release-review pass (run 20260706-112559): tool/doc/CI hardening

- **Context:** ran the full `release-review` runbook against this repository itself (explicit-
  subject exception; user-confirmed). The run record is `workflow-artifacts/release-review/
  20260706-112559/`. It found no blockers; the repo was already in good shape (secrets scan
  clean via gitleaks 0/65 commits, 46 tests passing, no manifest/shim/version drift, exemplary
  cold-start docs). It surfaced ten mostly-Low findings, and under the Fix Bar all Low-RR ones
  were fixed in-run.
- **Fixes applied (Section 7):**
  - S2-B1: `scan_secrets.py` now skips `workflow-artifacts/` and generated lockfiles via a shared
    `is_skipped_path()` used by both the working-tree and history scans, so the scanner no longer
    re-flags run records (including a prior scan's own output) or lockfile hash-soup. Candidate
    count on this repo dropped 518 -> 289 (all remaining are low-confidence entropy FPs).
  - S2-M1: `setup_tools.py` gained `--version`/`_framework_version()`, matching the other three
    tools (consistency).
  - S2-M2: `scan_secrets.py` computes `shannon_entropy` once per token, not twice.
  - S3-T1: added a `capture_hpc()` parse test; S2-B1/S2-M1 also got regression tests. New
    `tests/test_setup_tools.py`. Suite 46 -> 52.
  - S4-D1/D2/D3: doc-accuracy fixes introduced by D41's incomplete sync - ARCHITECTURE shim count
    15 -> 16 and "three Python tools" -> four (bench_env added), and the getting-started router
    gained a benchmark/performance route.
  - S6-CI1 + S3-T2: added `.github/workflows/tests.yml` (runs the unittest suite on push+PR,
    Python 3.9/3.11/3.13 matrix; no secrets/publish) and a root `Makefile` with a `test` target so
    the framework's own `verify` workflow now DISCOVERS its tests (dogfooding: `run_checks --list`
    finds 3 checks where it previously found 0).
  - S6-P1: softened the README "Python 3.7+" claim to "3.9+" (the CI-verified floor), honestly
    noting older 3.x is expected to work but untested (P2). 3.7/3.8 are EOL and not provisionable
    on current runners.
- **Deferred (not a code fix):** S5-F1 - the `benchmark` workflow (D41) has not been exercised
  end-to-end on a real repo yet; its deterministic tool is unit-tested but the guided flow is
  unproven live. Rated Medium Remediation Risk on the functionality axis: forcing a redesign
  without a live run's evidence is the risk, so the right action is VALIDATION (run `/benchmark`
  on a real target), surfaced to the user, not an in-run change.
- **Scope:** 2 tools, 3 docs, 1 CI workflow, 1 Makefile, 6 new tests. VERSION 20260704-05 ->
  20260704-06. All Low-RR findings fixed; no blocker; downstream rollout still user-gated.

### D44. Version scheme: git-tag-driven semver (baseline v1.0.0), replacing YYYYMMDD-NN

- **Context:** the hand-maintained `YYYYMMDD-NN` string (see the D32 / open-Q2 decision) had
  three problems for the upcoming pip distribution work (IPD-2): it can be forgotten or go stale,
  it is not PEP 440 valid (so it cannot be a wheel version), and it cannot express "this checkout
  DIFFERS from a release" (the observed clone-bug where a stale hand-string masked
  uncommitted/ahead changes). This is IPD-1, the prerequisite for IPD-2. Executed from
  `.agents/plans/done/2026-07-06-versioning-git-tag-semver.md` after two `/plan-review` passes
  (findings V-1..V-9, all Low Remediation Risk, fixed in the plan before build).
- **Decision:** adopt git-tag-driven semantic versioning with baseline `v1.0.0` (the toolkit has
  been in production across 27+ repos, well past 0.x). The version is DERIVED from `git describe`
  and baked into the tracked-but-generated `.agents/workflows/VERSION`; it is no longer
  hand-edited.
- **Design (tools stay dumb; intelligence in one resolver):** once copied into a user repo a tool
  is a loose file with no git and no package metadata, so it MUST read its version from the
  neighboring `VERSION` file (the existing three-directories-up read, unchanged). A new top-level
  `versioning.py` holds `resolve_version(repo_root)`, which parses the real
  `git describe --tags --always --dirty --long` forms and produces PEP 440 strings: a clean
  tagged tree -> `1.0.0`; an ahead-of-release or dirty tree -> `1.0.1.devN+g<sha>[.dYYYYMMDD]`
  (next-patch dev of the upcoming release, dirty date appended inside the local segment); no-tags
  -> `0.0.0+g<sha>` (with a `.dDATE` when dirty; the real dirty-no-tags form appends `-dirty` to
  a bare sha, V-7). No git tree -> read the baked `VERSION` (wheel / copied-out / plain clone).
- **Comparator:** a small dependency-free comparator over our OWN controlled format
  (`MAJOR.MINOR.PATCH[.devN][+local]`), NOT the third-party `packaging` library, preserving the
  zero-runtime-dependency rule (P6, D-Q3). `+local` is compared as presence only; `.devN` sorts
  before its final release. `status(target, packaged)` maps to
  not-installed / stale / current / ahead / dev / unknown (a legacy `YYYYMMDD-NN` or a `0.0.0`
  pre-baseline target is reported `unknown` rather than guessed). IPD-2's `list`/`status` consume
  this.
- **Scope of this change:** added `versioning.py` + `tests/test_versioning.py` (22 tests); made
  `install-workflows.py:read_version` git-aware (resolver in a git tree, VERSION file otherwise;
  the non-git file-read path is pinned by a characterization test, V-9); added a `make
  version-file` target (regenerate VERSION from the tag) and made `make version` print the
  resolved value; fixed the `scan_secrets.py` docstring "two" -> "three directories up" (V-2);
  migrated forward-facing docs (README, ARCHITECTURE, CONTRIBUTING, index.md scheme note,
  release-notes workflow) from `YYYYMMDD-NN` to semver; created the annotated `v1.0.0` tag on a
  clean tree and baked `VERSION` -> `1.0.0`. Suite 52 -> 75 tests, green.
- **Deferred to IPD-2 (sequencing, not a Remediation-Risk deferral):** the `setuptools-scm` /
  `hatch-vcs` build-backend wiring and `pyproject.toml`, and the `list`/`status` currency UI.
  IPD-1 delivers the resolver, the tag, and the derived VERSION so IPD-2 can build on a settled
  scheme.
- **Historical records untouched (P4):** the D32 / open-Q2 `YYYYMMDD-NN` decision, dated
  DECISIONS entries, and `.agents/plans/done/*` remain as written; only forward-facing docs
  migrated.

### D45. Plan lifecycle: canonical `pending/` + `reusable/` + `executed/`; rename this repo's `done/`

- **Context:** the plan/IPD lifecycle convention was inconsistent. This repo's terminal dir was
  `.agents/plans/done/` (kept as the accepted `executed/` alias per D26), and plan files were
  named `YYYY-MM-DD-<slug>.md`. Neither matched the intended convention, and there was no home
  for recurring, re-runnable plans. This is a deliberate reversal of D26's "do not rename this
  repo's `done/`" choice.
- **Decision (canonical, framework-wide):** the plan lifecycle has THREE states:
  - `.agents/plans/pending/` - new / awaiting-approval IPDs.
  - `.agents/plans/reusable/` - recurring plans meant to be re-run repeatedly (e.g. a periodic
    audit, a rollout or release runbook). These STAY here across runs rather than moving to
    `executed/` after each run.
  - `.agents/plans/executed/` - terminal; completed one-off IPDs.
  Plan files are named `YYYYMMDD-<slug>.md` (compact date, no hyphens in the date). `done/`
  remains an accepted alias for `executed/` for repos that already use it (discover-and-respect),
  but `executed/` is canonical and this repo now uses it.
- **Applied to this repo:** `git mv .agents/plans/done .agents/plans/executed`; renamed all 16
  plan files from `YYYY-MM-DD-<slug>.md` to `YYYYMMDD-<slug>.md`; added `.agents/plans/reusable/`
  (with a committed `.gitkeep`). This supersedes D26 decision 2's "keep `done/`" for THIS repo;
  D26's discover-and-respect rule for OTHER repos still holds.
- **Forward-facing docs updated:** the canonical three-state lifecycle and the `YYYYMMDD-<slug>`
  naming are now taught in `assess/assess.md` (Step 0), `assess/templates/ipd.md`,
  `setup-repo/setup-repo.md` (Step 0 + Step 1b), `index.md`, and the pip-distribution spec's
  setup-artifacts step. `setup-repo` now creates all three dirs.
- **Historical records untouched (P4):** executed-plan BODY text and `workflow-artifacts/*` run
  records still reference `done/` and the old `YYYY-MM-DD` names as written; those are immutable
  history. Only filenames, the directory, and forward-facing docs changed.
