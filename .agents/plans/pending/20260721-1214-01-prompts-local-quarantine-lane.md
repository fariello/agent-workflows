# IPD: add a gitignored `.agents/prompts/local/` quarantine lane (mirror comms local/shared)

- Date: 2026-07-21
- Concern: privacy / safety (prevent accidental commit of raw/sensitive staged prompts) + convention consistency
- Scope: amend the `.agents/prompts/` staging convention (D91) to add a gitignored `local/` quarantine lane alongside the tracked lifecycle buckets, mirroring the shipped `.agents/comms/` `local/`(gitignored)+`shared/`(tracked) split (D81). Installer scaffold + nested `.gitignore` + README/template + a DECISIONS note. No behavior change to the tracked buckets.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-21 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored after the `/handoff` privacy re-review (PR-009). The maintainer proposed a gitignored quarantine dir under `.agents/prompts/` that raw/sensitive prompts (esp. `/handoff` output, which captures raw session context) are written to, then a human promotes a scrubbed/approved copy into a tracked bucket. Chosen shape: mirror the comms `local/`/`shared/` convention rather than a one-off dir. This IPD is a prerequisite the `/handoff` IPD (20260717-2000-01) will depend on (it will default its output to `.agents/prompts/local/`).

## Goal

Give `.agents/prompts/` a quarantine lane so a raw or potentially-sensitive staged prompt is written somewhere that CANNOT be accidentally committed (even by `git add -A`), and only becomes durable/tracked when a human deliberately promotes a reviewed, scrubbed copy.

Why it matters: this repo already leaked a maintainer identifier to a public package once (D92/D93). The `/handoff` workflow (in review) will write RAW SESSION CONTEXT to `.agents/prompts/`; "written to a tracked dir but never auto-committed" relies on discipline and is one stray `git add -A` from a leak. A gitignored `local/` lane makes accidental commit structurally impossible, which is the defense-in-depth the comms convention already uses (D81: "the directory you write to IS the privilege level"). This generalizes beyond `/handoff` to any raw/machine-local/WIP prompt (e.g. session-recovery dumps that currently sit in an ad-hoc `opencode-recovery/`).

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P8 single source of truth - reuse the ONE gitignored-lane pattern; P10 safety/reversibility). No em/en dashes.
- The shipped precedent to mirror: `.agents/comms/` has `local/` (gitignored via a nested `.agents/comms/.gitignore` that is a created deliverable, NOT a change to the repo root `.gitignore`) and `shared/` (tracked). Engine: `COMMS_DIR`/`COMMS_LOCAL_SUBDIRS`/`COMMS_SHARED_SUBDIRS` (engine.py:2332-2334), `_COMMS_GITIGNORE_TEMPLATE` (engine.py:2336-2341), scaffolded in `create_setup_artifacts` (both real + dry-run branches), with the `shared/` `.gitkeep`s tracked and `local/` getting NO tracked `.gitkeep` (the nested `.gitignore` ignores it).
- The prompts convention to amend: `.agents/prompts/` (D91) currently has 5 tracked lifecycle buckets (`pending/executed/superseded/not-executed/reusable`) + a README, scaffolded by `PROMPTS_DIR`/`PROMPT_LIFECYCLE_SUBDIRS` (engine.py:2320-2331) and `ensure_prompts_readmes` (engine.py ~2591-2620). The tracked buckets are DIRECT children of `.agents/prompts/` (no `shared/` wrapper), so a nested `.agents/prompts/.gitignore` need only ignore `local/`.
- Packaging: `.agents/prompts/` source tree never ships in the wheel (tests/test_packaging.py `FORBIDDEN_AGENTS_SUBSTRINGS`); templates under `.agents/workflows/templates/` DO ship. The new `.gitignore` template + README edits follow that boundary.
- Plans lifecycle: `.agents/plans/pending/` + `YYYYMMDD-HHMM-NN-<slug>.md`; IPD born `to-review`.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| Q1 | HIGH | Low | maintainer / user | privacy (accidental commit) | A raw/sensitive staged prompt (notably `/handoff` output) written into a TRACKED prompts bucket is one `git add -A` from being committed and pushed to a public repo. There is no quarantine lane; safety relies on "never auto-commit" discipline alone. | D92/D93 (prior leak); `/handoff` IPD 20260717-2000-01 PR-009; `.agents/prompts/` has only tracked buckets |
| Q2 | MEDIUM | Low | maintainer | consistency | The comms convention already solves exactly this with a gitignored `local/` lane, but prompts (a sibling staging area) lacks the equivalent, so the framework is inconsistent and each raw-prompt case reinvents an ad-hoc dir (e.g. `opencode-recovery/`). | `.agents/comms/` local/shared (D81); `opencode-recovery/` ad-hoc gitignore this session |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | Q1,Q2 | Add engine support for a gitignored prompts `local/` lane, mirroring comms: a `_PROMPTS_GITIGNORE_TEMPLATE` (nested `.agents/prompts/.gitignore` containing `local/`), and extend `create_setup_artifacts` (BOTH real + dry-run branches) to create `.agents/prompts/.gitignore` + a `.agents/prompts/local/` dir. `local/` gets NO tracked `.gitkeep` (it is ignored); like comms, the nested `.gitignore` is a created deliverable, NOT a change to the repo ROOT `.gitignore`. Record created files for `--undo` (D85 F5). | `agent_workflows/engine.py` | Medium | fresh install into a temp repo creates `.agents/prompts/.gitignore` (ignoring `local/`) + `.agents/prompts/local/`; `git check-ignore .agents/prompts/local/somefile` matches; re-run idempotent; `--undo` removes them; root `.gitignore` untouched |
| 2 | Q1 | Update the prompts convention docs to describe the `local/` lane: `.agents/prompts/README.md` and the shipped `prompts-README.md` template + the `.agents/docs/README.md` cross-reference. State: `local/` (gitignored) = quarantine for raw/sensitive/WIP prompts (never committed); the tracked lifecycle buckets = deliberate, durable prompts; the directory you write to IS the privilege level; promote by `git mv local/... pending/...` after review/scrub. | `.agents/prompts/README.md`, `.agents/workflows/templates/prompts-README.md`, `.agents/docs/README.md` | Low | READMEs describe the lane consistently; no em/en dashes |
| 3 | Q1,Q2 | Scaffold THIS repo to match: create `.agents/prompts/.gitignore` (`local/`) + `.agents/prompts/local/`. | `.agents/prompts/.gitignore` (new), `.agents/prompts/local/` | Low | `git check-ignore .agents/prompts/local/x` matches; `.gitignore` tracked; `local/` untracked |
| 4 | Q1 | Tests: extend `tests/test_setup_artifacts.py` (or the prompts scaffold test) to assert the nested `.gitignore` is created and ignores `local/`, `local/` has no tracked `.gitkeep`, the root `.gitignore` is untouched, and `--undo` removes the lane. Update the `create_setup_artifacts` created-count assertion (currently 21 -> new count with the prompts `.gitignore`). | `tests/test_setup_artifacts.py` | Low | tests pass; the count assertion matches reality |
| 5 | Q1,Q2 | Docs/decision sync: DECISIONS entry (next free number, pin at execution) recording the prompts `local/` quarantine lane and its rationale (privacy defense-in-depth; mirrors D81; amends D91). CHANGELOG 1.3.0 bullet. | `DECISIONS.md`, `CHANGELOG.md` | Low | entry + bullet present; no em/en dashes |
| 6 | Q1 | Cross-reference for the dependent `/handoff` IPD: note in this IPD (and, when `/handoff` executes, in its runbook) that `/handoff` writes to `.agents/prompts/local/` by default; the human promotes a scrubbed copy. (No edit to the `/handoff` IPD here beyond noting the dependency; that IPD already says "human promotes" and will point at `local/` at its execution.) | this IPD | Low | dependency recorded |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | Low | complexity | Migrating existing ad-hoc gitignored dumps (`opencode-recovery/`) INTO `.agents/prompts/local/`. Nice-to-have consolidation, not required for the lane to work. | Optional later cleanup. |
| n/a | Low | functionality | Auto-scanning `local/` contents with `aw check-local-leaks` on promotion. The `/handoff` IPD already requires the scan on its output; a general promote-time hook is a separate enhancement. | Consider when the prompts pipeline (`/research`) lands. |

## Scope check

- Over-scope: none. Mirrors an existing, shipped pattern; touches only prompts scaffolding + docs + tests. No change to the tracked buckets' behavior.
- Under-scope: confirm the nested `.gitignore` placement. Comms puts it at `.agents/comms/.gitignore` ignoring `local/` (with tracked lanes under `shared/`). Prompts' tracked buckets are direct children, so `.agents/prompts/.gitignore` with a single `local/` line is correct and does not accidentally ignore a tracked bucket. Verify the glob ignores only `local/`.

## Required tests / validation

- Step 4 tests (nested `.gitignore` created + ignores `local/`; no tracked `.gitkeep` in `local/`; root `.gitignore` untouched; `--undo` removes the lane; created-count updated).
- Manual: `install_into_repo` into a temp repo; `git check-ignore .agents/prompts/local/handoff.md` matches; `git status` never offers `local/` contents; `git rm --cached`/undo clean.
- Full suite `python -m pytest -q` stays green; paste ACTUAL output (baseline 293 passed, 1 skipped).
- `aw check-local-leaks .` stays clean.

## Spec / documentation sync

- `.agents/prompts/README.md` + `prompts-README.md` template + `.agents/docs/README.md`: describe the `local/` lane (Step 2).
- `DECISIONS.md` + `CHANGELOG.md` (Step 5).
- Dependent: the `/handoff` IPD (20260717-2000-01) defaults its output to `.agents/prompts/local/` (recorded there at its execution).

## Open questions

- OQ1 (DECISIONS number): pin at execution (current max D93 -> likely D94, but re-check; other plans in flight may claim it first).
- OQ2 (promote-time scan): should promotion out of `local/` auto-trigger `aw check-local-leaks`? Lean: not in this IPD (the `/handoff` workflow already scans its own output); revisit as a general hook later. Deferred above.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review this IPD (optionally `/plan-review`). Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, run validation, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
4. Then the `/handoff` IPD can execute, defaulting its output to `.agents/prompts/local/`.
