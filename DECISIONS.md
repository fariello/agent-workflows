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
