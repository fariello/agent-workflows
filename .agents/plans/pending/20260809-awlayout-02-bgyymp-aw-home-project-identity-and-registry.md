# IPD: AW home, project identity, and registry

- Date: 2026-08-09
- Kind: child
- Concern: Give projects stable identities outside their target repositories and maintain an inspectable `AW_HOME` registry.
- Scope: `agent_workflows/project_registry.py`, AW-home configuration and schema migration in `agent_workflows/config.py`, registry-related CLI wiring in `agent_workflows/cli.py`, and `tests/test_project_registry.py`.
- Status: approved
- Approval: 2026-08-09, human maintainer (approved the awlayout Set for execution after /plan-review re-review; spec 20260809-2211-01 approved)
- Set: awlayout (AW project layout)
- Order: 2
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: bgyymp

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L2-01 [HIGH] (`~/.aw` default AW_HOME + config store conflicts with config.py/D46 'never write under ~/'; state which store owns AW_HOME selection). L2-02 [HIGH] (`git rev-parse --git-common-dir` identity primitive does NOT exist in the codebase and is unscoped; name where it is added, do not invent). L2-03 [HIGH] (add a negative test: two projects sharing an origin URL must NOT auto-attach - no identity spoofing via remote). L2-04 (registry loader must canonicalize+reject traversal/symlink-escaping paths and refuse home==target or home-ancestor-of-target). L2-05 (concurrent-writer/atomic-replace guarantee for registry.json). L2-06 (import Order 01 enums, do not restate). L2-07 (enumerate the redaction forbidden-set).
- 2026-08-09 author revision (Codex GPT-5): addressed L2-01 through L2-07. The existing XDG platform config owns the saved `AW_HOME` selector and may point to `~/.aw`; `project_registry.py` owns the new Git common-directory probe; registry writes use lock plus atomic replace; origin-only auto-attachment is forbidden; path and redaction boundaries are explicit.
- 2026-08-09 re-reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED (by the author). Verified against repo evidence that the author's revision RESOLVED every prior finding - H1-H7 and all L0/L1..L11 items - and introduced no new finding; the dependency DAG remains valid and the orchestrator/child dependency lines agree (Order 07 now correctly depends on 01,06). All 12 lint conforming at author + review-finalize. Readiness: GO - PENDING HUMAN APPROVAL, gated ONLY on the controlling spec 20260809-2211-01 being approved (still Status: to-review) before any child executes.
- 2026-08-09 approved (human maintainer): Status reviewed -> approved; controlling spec approved; cleared for execution via ipd-lifecycle (execute in dependency order, per-child gates).

## Goal

Implement a relocatable, non-secret registry that maps a working repository to its durable AW project identity. Make the default home location configurable while refusing ambiguous matches.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Home and registry model

- [ ] E-01 Extend the fixed-allowlist, versioned schema in `agent_workflows/config.py` with the saved `aw_home` selector and migration, then implement `AW_HOME` precedence and normalization as explicit CLI value, `AW_HOME` environment variable, saved XDG platform config value, and platform default, with `~/.aw` as the documented Unix data-root default.
  - Depends on: none
  - Expected outcome: one resolver returns an absolute AW home and explains the selected source without writing it.
  - Execution state: pending
- [ ] E-02 Implement a versioned registry and stable project-ID generator in `agent_workflows/project_registry.py`, importing Order 01 enums, using a same-directory lock plus temporary-file `fsync` and `os.replace`, and allowing only project ID, canonical Git common-directory identity, known target paths, credential-free normalized origin hints, selected policy values, enabled hosts, and last verified version.
  - Depends on: E-01
  - Expected outcome: each project gets a durable opaque ID and a small metadata entry safe to inspect and back up.
  - Execution state: pending

### Task group 2: Matching and lifecycle

- [ ] E-03 Add the previously nonexistent `git rev-parse --git-common-dir` probe as a private, tested primitive in `project_registry.py`; match by explicit project ID, exact Git common-directory identity, then canonical target path, while origin remains a displayed candidate hint that always requires explicit attach and can never auto-select or auto-merge entries.
  - Depends on: E-02
  - Expected outcome: moves and worktrees are supported without allowing a similar URL or basename to select private data silently.
  - Execution state: pending
- [ ] E-04 Add `aw project status`, `aw project attach`, and `aw project move` with dry-run output, explicit confirmation for identity changes, and stable JSON or agent output.
  - Depends on: E-03
  - Expected outcome: users can inspect and repair associations without manually editing registry files.
  - Execution state: pending
- [ ] E-05 Add `tests/test_project_registry.py` for precedence, config-schema migration, stable IDs, lock contention and interrupted atomic replacement, worktrees, moved paths, origin changes, two unrelated projects sharing one origin, ambiguity, dry runs, canonical containment, traversal and symlink escape refusal, `AW_HOME == target`, `AW_HOME` as target ancestor, and redaction boundaries.
  - Depends on: E-04
  - Expected outcome: registry behavior is deterministic across the supported identity and relocation cases.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Configuration behavior belongs in `agent_workflows/config.py`; CLI dispatch belongs in `agent_workflows/cli.py`.
- Existing Git helpers should be reused where their behavior matches this plan.
- D46's platform config remains under `$XDG_CONFIG_HOME/agent-workflows/` or `~/.config/agent-workflows/`; its "never under `~/` directly" rule governs the selector file, not the data root to which `aw_home` points.
- File replacement must be atomic where interrupted writes would corrupt future resolution.
- Machine-facing output must be ANSI-free and stable enough for workflows.

## Findings

| Finding | Consequence |
|---|---|
| A target path alone does not survive repository moves. | Identity needs additional Git and origin hints. |
| Remote URL equality is not proof that two checkouts should share candid records. | Origin is a hint and ambiguity requires user action. |
| Worktrees share a Git common directory. | Registry matching must distinguish intentional sharing from unrelated clones. |

## Proposed changes (ordered, validatable)

1. Resolve AW home consistently.
2. Persist a minimal versioned registry.
3. Apply strict matching rules.
4. Provide repair and inspection commands.
5. Test relocation, ambiguity, privacy, and atomicity.

## Deferred / out of scope (with reason)

- Record directory creation and Git initialization are Order 03.
- Target-repository layout creation is Order 05.
- Automatic identity merging is excluded because a false positive can expose private records.

## Scope check

- Over-scope: no record backend, install wizard, target layout, or migration writes.
- Under-scope: home precedence, identity, registry persistence, matching, repair, and inspection are covered.

## Required tests / validation

- `python3 -m unittest tests.test_project_registry -v`
- `python3 -m unittest discover -s tests -v`
- `python3 -m agent_workflows project status --json`

## Spec / documentation sync

- Keep registry fields and matching order aligned with the canonical 2026-08-09 layout specification.
- Do not place secret values or record content in examples or fixtures. The forbidden set is credentials and tokens, URL userinfo/query/fragment values, secret-like environment values detected by the existing leak sanitizer, conversation or action bodies, generated record content, and unredacted machine identifiers in public-safe output. Credential-free origin identity and canonical local paths may exist only in the machine-local registry; display modes must use safe home-relative or redacted forms.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: focused tests show every precedence case, XDG-owned selector migration, `~/.aw` as a data-root value rather than a directly written selector file, absolute normalization, source explanation, and zero writes during resolution.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: registry round-trip, concurrent-writer serialization, `fsync` plus atomic-replace, and interrupted-write tests pass; schema inspection confirms only the enumerated metadata fields and imported Order 01 enum values.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: tests cover the new Git common-directory probe, explicit ID, worktree, path move, clone separation, ambiguous-candidate refusal, and prove two projects with the same origin URL are never auto-attached.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: command transcripts prove dry-run behavior, confirmation gates, stable machine output, and no mutation on rejection.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: focused and full suites pass with temporary homes and repositories only; traversal, symlink escape, unsafe containment, and the complete forbidden redaction set all fail closed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: home resolution, identity matching, and registry repair are inseparable parts of one project-association boundary.

STOP if Order 01 is not complete or its serialized schema changed without spec review. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.
