# IPD: Scaffold `.agents/prompts/` staging convention and wire it into the installer

- Date: 2026-07-17
- Concern: framework capability (operational prompt staging) + convention consistency
- Scope: the `.agents/prompts/` operational-staging area: lifecycle buckets, per-bucket READMEs, installer scaffolding parity with `.agents/plans/` and `.agents/docs/`, the research-prompt -> results convention, and the doc updates that describe it
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Set: agent-continuity-workflows
- Order: 2

<!--
Order 1 of this Set is DONE (D88, filesystem-encoded-state principle). This is Order 2.
Orders 3-5 (/whatnext, /research, /handoff) consume the convention this plan establishes.
-->

## Workflow history

- 2026-07-17 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored as Order 2 of the agent-continuity-workflows Set after the human confirmed the full 1.3.0 backlog is in scope and chose to wire prompts staging into the installer. Grounded in an explore-agent survey of the plans/docs scaffold pattern, D50, D88, and IPD 1544-01.
- 2026-07-17 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED. Verified all engine.py/plans.py/packaging claims against source; added dry-run parity test, single-source wiring note (install_into_repo covers both entry points, D83), pinned DECISIONS D91, noted normalizer already recognizes the buckets, corrected the docstring-accuracy pitfall. Resolved OQ1 (rename+commit the stray file) and OQ2 (defer AGENTS.md pointer) with the human; OQ3 resolved from evidence. Status -> reviewed.

## Goal

Make `.agents/prompts/` a first-class, self-documenting operational-staging area on par with `.agents/plans/` and `.agents/docs/`, and ship that scaffolding in the installer so every target repo gets it.

`.agents/prompts/` is the staging area for run-once / research prompts that are QUEUED to be executed (distinct from `.agents/docs/prompts/`, the evergreen copy-paste prompt LIBRARY). Today the concept is referenced by tooling (the `aw plans` board scans it; the name-normalizer scans it; release-review looks for staged prompts in `.agents/prompts/pending/`) and blessed by decisions (D50 scan scope, D88 consequences, IPD 1544-01 semantics), but it was never actually scaffolded: only `pending/` and `reusable/` exist here by hand, there is no README, no lifecycle-bucket parity, no installer support, and no documented "prompt -> results" convention. Orders 3-5 of this Set (`/whatnext`, `/research`, `/handoff`) all depend on this area existing and being documented.

Why it matters: without a scaffolded, documented convention, each agent re-derives where queued prompts live and where their results go, the buckets drift from the plans pattern they claim to mirror, and downstream repos never get the area at all.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (esp. P5 + its D88 location-over-contents extension; P8 one-canonical-principle).
- Pending-plans location/format used: `.agents/plans/pending/YYYYMMDD-HHMM-NN-<slug>.md`; readiness in front-matter `Status:` (D52); disposition in the directory (D88). This IPD lives there.
- Contributor/spec-sync contract: `AGENTS.md`, `CONTRIBUTING.md`, `.agents/plans/README.md` (execution contract: path-scoped commits, never push, `git mv` lifecycle move, HARD honesty on tests, no em/en dashes).
- Stack / relevant context:
  - Scaffold pattern to MIRROR: `agent_workflows/engine.py` constants `PLANS_DIR` / `PLAN_LIFECYCLE_SUBDIRS` (engine.py:2301-2308) and `DOCS_DIR` / `DOCS_SUBDIRS` (2309-2315); directory creation in `create_setup_artifacts` (2579-2644, `.gitkeep` per bucket, no-clobber, idempotent, with a dry-run mirror); per-bucket READMEs via `ensure_plans_readmes` (2499-2534) / `ensure_docs_readmes` (2540-2576) driven by the same subdir constants so buckets cannot drift; README-ensurers run BEFORE `create_setup_artifacts` (2709-2723, D83) and created files are recorded for `--undo` (D85 F5).
  - Templates (installer source, bundled into the wheel under `agent_workflows/_data/.agents/workflows/templates/`): `.agents/workflows/templates/plans-README.md`, `plans-{pending,executed,superseded,not-executed,reusable}-README.md`, `agents-README.md`, `agents-docs-*-README.md`. No `prompts-*` template exists yet.
  - Board/scan tooling already treats prompts as an area: `agent_workflows/plans.py` `DISPOSITION_DIRS` (31-38, includes a `done` alias), `scan(root, include_prompts=True)` (147-170), `PlanRecord.area` (92); `cli.py:824`.
  - Normalizer scans it: `.agents/workflows/setup-repo/tools/normalize_plan_names.py:29`, `setup-repo/setup-repo.md:127`.
  - Packaging boundary: the source `.agents/` tree (docs/plans/prompts) is dev/meta and NEVER ships; `tests/test_packaging.py` asserts `.agents/docs/`, `.agents/plans/`, `.agents/prompts/` never appear in the wheel (DECISIONS.md:2037, IPD 1544-01:94-100). New scaffold code + templates must respect this: templates ship (they are under `.agents/workflows/`), the scaffolded target dirs do not (they are created in the TARGET repo at install time).

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for whether to act now. Persona = which reviewer perspective surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| P1 | Medium | Low | maintainer | `.agents/prompts/` | The area is referenced by tooling and blessed by D50/D88/1544-01 but never scaffolded: only `pending/` + `reusable/` exist (by hand), missing `executed/`, `superseded/`, `not-executed/` that the board's `DISPOSITION_DIRS` already scans. | `agent_workflows/plans.py:31-38`; on-disk `.agents/prompts/` has only pending/+reusable/ |
| P2 | Medium | Low | new contributor | docs | No `.agents/prompts/README.md` and no per-bucket READMEs exist; nothing documents the staging convention or the prompt->results destination, so the area's purpose is discoverable only by reading decisions. | absent `.agents/prompts/README.md`; `.agents/README.md:10` lists docs buckets but not the sibling prompts staging area |
| P3 | Medium | Medium | operator | installer | The installer scaffolds `.agents/plans/` and `.agents/docs/` into every target repo but not `.agents/prompts/`, so downstream repos never get the area even though `aw plans`/normalizer/release-review expect it. | `engine.py:2621-2626` (plans+docs scaffolded; no prompts); no `PROMPTS_DIR` constant |
| P4 | Low | Low | maintainer | convention | The one staged file `.agents/prompts/pending/20260717-1450-ses_<redacted>.compacted.md` does not follow `YYYYMMDD-HHMM-NN-<slug>.md` (no `NN`, non-kebab slug) that the normalizer scans `.agents/prompts/` for; it is also untracked. | on-disk filename; normalizer `normalize_plan_names.py:29` |
| P5 | Low | Low | maintainer | consistency | `.agents/prompts/` has no per-repo `.gitignore` decision documented (unlike comms `local/`). Prompts staging is tracked (like plans), which is the intended default, but that is nowhere stated. | comms precedent `engine.py:2633-2644`; plans are tracked |
| P6 | Low | Low | maintainer | architecture | The `ensure_docs_readmes` docstring (engine.py:2546) is stale (claims research/walkthroughs only, but the code loops ALL `DOCS_SUBDIRS`). The new `ensure_prompts_readmes` must NOT copy that error; its docstring should state it loops every bucket and skips any without a template. | `engine.py:2540-2556` |

## Proposed changes (ordered, validatable)

Fix by default; each item should be safe, well-scoped, and verifiable.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | P1,P3 | Add `PROMPTS_DIR = ".agents/prompts"` and `PROMPT_LIFECYCLE_SUBDIRS = ("pending", "executed", "superseded", "not-executed", "reusable")` engine constants, mirroring the plans constants. | `agent_workflows/engine.py` | Low | new unit test asserts the constants exist and match the plans bucket tuple ordering |
| 2 | P3 | Extend `create_setup_artifacts` BOTH branches - the real branch (engine.py:2621-2626 region) AND the dry-run branch (engine.py:2598-2619 region) - to create/report a `.gitkeep` per prompts bucket, no-clobber and idempotent, exactly like the plans/docs loops; the real branch's created paths flow into `newly_created` (engine.py:2725) for `--undo`. | `agent_workflows/engine.py` | Medium | new test: fresh scaffold into a temp repo creates all 5 prompts buckets with `.gitkeep`; re-run is idempotent; `--undo` removes them; AND a dry-run scaffold REPORTS the 5 buckets without writing them (dry-run/real parity) |
| 3 | P2 | Add installer source templates: `.agents/workflows/templates/prompts-README.md` (area overview + prompt->results convention) and `prompts-{pending,executed,superseded,not-executed,reusable}-README.md` (per-bucket), mirroring the plans templates' tone/length. | `.agents/workflows/templates/prompts-*.md` (new) | Low | files exist; content-lint (no em/en dashes) passes; packaging test still sees them bundled under `_data` |
| 4 | P2,P6 | Add `ensure_prompts_readmes` driven by `PROMPT_LIFECYCLE_SUBDIRS` (mirroring `ensure_plans_readmes`), with an accurate docstring (it loops ALL buckets, skipping any without a template - the `ensure_docs_readmes` docstring at engine.py:2546 is stale on this point; do not copy that error). Add a `_PROMPTS_README_TARGETS` fixed target for `.agents/prompts/README.md`. Wire the call into `install_into_repo` (engine.py:2713-2715 region) in the canonical order (README-ensurers BEFORE `create_setup_artifacts`, D83). Because `run()` (the `install-workflows.py` path) delegates to `install_into_repo` (engine.py:2816), wiring it there covers BOTH entry points with no drift. | `agent_workflows/engine.py` | Medium | new test: scaffold writes `.agents/prompts/README.md` + 5 bucket READMEs from templates; idempotent; recorded for `--undo` (READMEs are auto-captured in `newly_created` at engine.py:2717-2718 via the `[install]` tag) |
| 5 | P1,P2 | Scaffold THIS repo to match: create the missing `.agents/prompts/{executed,superseded,not-executed}/` buckets and all prompts READMEs (from the new templates) so the reference repo is exemplary. | `.agents/prompts/**` | Low | `aw plans` renders prompts buckets without error; `ls .agents/prompts/` shows 5 buckets + README |
| 6 | P2 | Document the convention in the durable record: DECISIONS **D91** (pinned; current max is D90) capturing the prompt->results convention (queued prompts stage in `.agents/prompts/<bucket>/`; RESULTS land under `.agents/docs/research/<topic>/`; the evergreen library stays `.agents/docs/prompts/`); update `.agents/README.md` to mention the sibling staging area and cross-reference the two prompt homes; add a CHANGELOG 1.3.0 bullet. | `DECISIONS.md`, `.agents/README.md`, `.agents/docs/README.md`, `CHANGELOG.md` | Low | links resolve; no em/en dashes; DECISIONS D91 does not collide (re-check max at execution time) |
| 7 | P4 | Per OQ1 (resolved): normalize the one staged file to `YYYYMMDD-HHMM-NN-<slug>.md` and commit it to `.agents/prompts/pending/` (tracked). `git add` the renamed file. No normalizer CODE change is needed: `normalize_plan_names.py:64` `LIFECYCLE_SUBDIRS` and `DEFAULT_AREAS` (line 63) already recognize all 5 prompts buckets. | `.agents/prompts/pending/*` | Low | filename matches the convention; `aw plan-names` (dry-run) reports no rename-eligible offenders in `.agents/prompts/`; file is tracked |
| 8 | P5 | State the tracked-by-default decision for prompts staging in the `prompts-README.md` (prompts staging is tracked like plans; it is NOT gitignored like comms `local/`), and confirm no `.gitignore` is emitted for it. | `.agents/workflows/templates/prompts-README.md` | Low | README states it; `create_setup_artifacts` emits no prompts `.gitignore` |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | Medium | functionality | The `/whatnext` (surveyor), `/research` (producer), and `/handoff` (generator) workflows that CONSUME this convention. | Orders 3-5 of this Set; each its own IPD -> plan-review -> approval. `/handoff` already has IPD `20260717-2000-01`. |
| n/a | Medium | complexity | An `aw prompts` board command (a prompts-only view distinct from `aw plans`). The existing `aw plans` already scans prompts via `include_prompts`; a dedicated command is a separate enhancement. | Later enhancement IPD if surveyor work shows a need. |
| n/a | Low | usability | Auto-migration of legacy non-conforming staged filenames across downstream repos. This IPD normalizes only THIS repo's one file; the normalizer already handles others on demand. | Existing `aw plan-names` covers it; no new work. |

## Scope check

- Over-scope (untraceable to a need; propose removal/deferral): none identified. Every step traces to P1-P6. The installer wiring (Steps 1-4) is explicitly in scope per the human's decision (Order-5 open question resolved: installer scaffolds it).
- Under-scope (needed capability missing; propose adding): Step 5's validation should eyeball `release-review/08-final-ship-review.md` staged-prompt expectations (it reads `.agents/prompts/pending/`); the fuller bucket set is additive so no change is expected, but confirm. NOTE (plan-review PR-001): `ensure_prompts_readmes` must be wired into `install_into_repo` (not a per-entry-point copy), because `run()` delegates there (engine.py:2816); this keeps the two install entry points single-sourced (D83).

## Required tests / validation

- New unit tests (stdlib unittest, zero runtime deps, to keep the suite green on the full 3.9-3.14 matrix):
  1. constants: `PROMPT_LIFECYCLE_SUBDIRS` exists and equals the plans bucket tuple.
  2. scaffold (real): fresh install into a temp git repo creates `.agents/prompts/` with all 5 buckets + `.gitkeep` + README (from templates) + the 5 bucket READMEs; re-run is idempotent (no clobber); `--undo` removes exactly the created files.
  3. scaffold (dry-run): a dry-run scaffold REPORTS the 5 prompts buckets (and READMEs, via the ensurer's dry-run path) WITHOUT writing them - guards dry-run/real parity for the new dry-run branch code (PR-002).
  4. no-gitignore: `create_setup_artifacts` emits no `.gitignore` under `.agents/prompts/` (prompts staging is tracked).
  5. packaging: `tests/test_packaging.py` still asserts the source `.agents/prompts/` target tree does NOT ship in the wheel, and that the new `prompts-*` TEMPLATES DO ship under `_data`.
  6. board: `plans.scan(..., include_prompts=True)` over a repo with the new buckets returns records with `area == "prompts"` and does not error on the empty buckets.
- Full-suite regression: `python -m pytest -q` must stay green (paste actual output; current baseline 262 passed, 1 skipped, so expect a higher passed count with the new tests).
- Manual: `aw install` into a throwaway temp repo, confirm `.agents/prompts/` scaffolds with READMEs and offers the commit prompt; `aw install --undo` rolls it back.

## Spec / documentation sync

- `DECISIONS.md`: new entry **D91** (pinned) for the prompts-staging convention + prompt->results destination.
- `.agents/README.md`: add the `.agents/prompts/` sibling staging area to the overview; cross-reference `.agents/docs/prompts/` (library) vs `.agents/prompts/` (staging).
- `.agents/docs/README.md`: cross-reference note so the two prompt homes are not confused.
- `CHANGELOG.md`: 1.3.0 "Added" bullet for the prompts-staging scaffold + installer support.
- The new `prompts-*-README.md` templates ARE the shipped spec for the convention in downstream repos.
- `AGENTS.md` "Writing prompts for another AI" block: OUT OF SCOPE per OQ2 (deferred to a later IPD; revisit with `/research` or `/whatnext`).

## Open questions

- OQ1 (disposition of the existing staged file): RESOLVED (human, 2026-07-17 /plan-review). Normalize `20260717-1450-ses_<redacted>.compacted.md` to the `YYYYMMDD-HHMM-NN-<slug>.md` convention and commit it to `.agents/prompts/pending/` (tracked). Encoded in Step 7.
- OQ2 (AGENTS.md block): RESOLVED (human, 2026-07-17 /plan-review). DEFER the AGENTS.md / managed-block pointer to a later IPD (revisit when `/research` or `/whatnext` land). This IPD documents the convention only in `.agents/README.md`, `.agents/docs/README.md`, and the new prompts READMEs. The `AGENTS.md` "consider" note is removed from Spec/documentation sync.
- OQ3 (bucket set): RESOLVED from repo evidence (plan-review, no human needed). Prompts mirror ALL FIVE buckets (`pending/executed/superseded/not-executed/reusable`) because the tooling already assumes them: `plans.py:31-38` `DISPOSITION_DIRS`, `normalize_plan_names.py:64` `LIFECYCLE_SUBDIRS`, and `reusable/` is already populated (the OpenCode verification runbook). `done/` is a board-only alias (`plans.py`), NOT scaffolded (matches plans; a repo already using `done/` keeps it). Steps 1-5 already encode the 5-bucket set; this OQ is closed.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first, `git mv` then commit both paths for the lifecycle move. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload (that is release-review Section 9 after explicit human GO).

Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it; that sets `Status: reviewed`). Update `Status:` as it progresses (`to-review` -> `reviewed` -> `approved`), appending a Workflow-history line at each step. Pin the DECISIONS D-number during review to avoid a collision.
2. On human approval, set `Status: approved` (+ the `Approval:` line), execute the ordered changes, run the validation, and sync specs/docs.
3. Only then set the terminal `Status: executed` and `git mv` this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`. Plan files are named `YYYYMMDD-HHMM-NN-<slug>.md`.
