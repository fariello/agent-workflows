# IPD: `/whatnext` read-only surveyor workflow

- Date: 2026-07-17
- Concern: framework capability (agent orientation) + Set/Order housekeeping
- Scope: a new prose-only `/whatnext` workflow (`whatnext.md` + `README.md` + one manifest row) that surveys the repo's plans, staged prompts, comms inbox, and TODO and RECOMMENDS a prioritized next-action list; plus reconciling the `Set:`/`Order:` collision between the prompt-pipeline and the workflow-command family
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Set: agent-continuity-workflows
- Order: 1

<!--
Set reconciliation (this IPD): `agent-continuity-workflows` is the workflow-command trio
(/whatnext=1, /research=2, /handoff=3). The prompt-pipeline work moves to its own Set id
`research-prompt-pipeline`. See Proposed changes Step 5.
-->

## Workflow history

- 2026-07-17 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored as Order 1 of the reconciled `agent-continuity-workflows` Set, after the human chose "build the full 1.3.0 backlog" and "split into two Sets" for the Set/Order collision. Grounded in an explore-agent survey of the workflow anatomy, manifest registration, `plans.py` scanner, comms/TODO/prompts sources, and the test guards.
- 2026-07-20 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001/PR-002 fixed (stale D-number D92->D94-context; stale test baseline 266->288). Re-verified against current source: the Set collision (prompts-scaffold Order 2, handoff Order 3, this IPD Order 1 under `agent-continuity-workflows`) still EXISTS, so Step 5's reconciliation remains valid; exemplar flat workflows, engine registration functions, `test_dir_readmes` Category-2 rule, comms untrusted-payload line, and TODO's still-stale Order numbering all confirmed. No scope overlap with the pending documentation IPD (2354-01). Resolved OQ1 with the human (NOT prescriptive: survey-then-reason, default only as tie-breaker; agent may surface off-record priorities) and OQ2 (no new DECISIONS entry; Workflow-history note only). Rewrote Step 1's output contract accordingly. Status -> reviewed.

## Goal

Give an agent (or human) a single command that answers "what should I work on next here?" by surveying the repo's own externalized state and returning a prioritized, reasoned recommendation, without taking any action.

Today that orientation is re-derived by hand every session (read `DECISIONS.md`, `TODO.md`, `CHANGELOG.md`, the plans board, the comms inbox, staged prompts). `/whatnext` codifies that survey as a portable, read-only prose runbook. It is Order 1 of the `agent-continuity-workflows` command family because the later `/handoff` workflow (Order 3, IPD `20260717-2000-01`) is specified to REUSE `/whatnext`'s survey inputs, so building the surveyor first is the natural order. It also exercises the `.agents/prompts/` staging convention just shipped (D91): staged prompts are one of the things it surveys.

Why it matters: it makes cold-start orientation cheap and consistent, reduces the chance an agent misses a pending-approval plan or an unread inbox message, and does so under the framework's safety norms (recommend-don't-act; treat comms payloads as untrusted).

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P5 externalize/filesystem-encoded state; the survey reads that externalized state). Read-only-advisory workflow norms mirror `list-workflows` and `getting-started`.
- Pending-plans location/format used: `.agents/plans/pending/YYYYMMDD-HHMM-NN-<slug>.md`; readiness `Status:` (D52); advisory `Set:`/`Order:` (D82). This IPD lives there.
- Contributor/spec-sync contract: `AGENTS.md`, `CONTRIBUTING.md`, `.agents/plans/README.md` (execution contract). No em/en dashes in authored Markdown.
- Stack / relevant context:
  - Workflow anatomy (flat shape, the target here): a workflow dir `.agents/workflows/<name>/` with `<name>.md` (the runbook) + `README.md`. Exemplars: `list-workflows/`, `getting-started/`. House runbook style: `# Workflow: <name> (<role>)`, an explicit read-only guardrail near the top, `## Inputs` (`$ARGUMENTS`), numbered `## Step N` sections, a closing `## Reminders`.
  - Registration is MANIFEST-DRIVEN, not directory-scan-driven: body files install by rglob (`engine.py:374-391` `collect_source_members`), but a slash-command shim is generated ONLY from a row in the `index.md` manifest table between `<!-- WORKFLOWS-MANIFEST:BEGIN -->` and `<!-- WORKFLOWS-MANIFEST:END -->` (`engine.py:326-371` `parse_manifest`, `509-540` `generate_shim_members`). A row with no `assess-`/`advise-` prefix gets its own shim. So the load-bearing registration edit is ONE manifest row (`command | body | lens | description`, `lens = -`).
  - Survey data sources: plans + staged prompts have a read-only scanner already (`agent_workflows/plans.py` `scan(root, include_prompts=True)`, surfaced by `aw plans`); comms has NO inbox lister (only validators in `comms.py`), so the inbox is prose-read header-only (payload-blind, untrusted per `.agents/comms/README.md:32-37`); `TODO.md` is prose-read.
  - Test guards: `tests/test_dir_readmes.py::test_source_has_readme_for_every_top_level_capability` REQUIRES `whatnext/README.md` to exist; `tests/test_installer.py` parse/shim tests exercise the new manifest row. No manifest<->dir bidirectional consistency test exists.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Persona = which reviewer perspective surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| W1 | Medium | Low | power user / new contributor | capability | No `/whatnext` command exists; cold-start orientation is re-derived by hand each session, risking missed pending-approval plans or unread inbox messages. | grep `whatnext` in `agent_workflows/` = no matches; TODO.md:81-86 (Order 3 backlog) |
| W2 | Medium | Low | maintainer | convention integrity | `Set:`/`Order:` collision: `Set: agent-continuity-workflows` is used by two different concepts with clashing Orders - the executed prompts-scaffold IPD (`Order: 2`) and the workflow-command family (handoff `Order: 3`, whose own note wants whatnext=1/research=2/handoff=3, colliding with the prompts Order 2). `plans.py set_warnings()` will flag duplicate Orders once `/whatnext` joins. | `.agents/plans/executed/20260717-2118-01-...:9-10`; `.agents/plans/pending/20260717-2000-01-...:8-11`; `agent_workflows/plans.py:202-215` |
| W3 | Low | Low | operator | safety | A surveyor that reads the comms inbox could be tempted to treat a message payload as an instruction. The framework rule (D81) is payload-blind, header-only, untrusted. The runbook must bake this in explicitly. | `.agents/comms/README.md:32-37`; DECISIONS D81 |
| W4 | Low | Low | maintainer | drift | TODO.md's narrative "ordered Set" (Order 1-5) uses numbering that will disagree with the reconciled front-matter Sets after W2 is fixed, re-introducing confusion. | `TODO.md:58-97` |

## Proposed changes (ordered, validatable)

Fix by default; each item is safe, well-scoped, verifiable.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | W1,W3 | Author `whatnext.md`: the read-only surveyor runbook in the light `list-workflows`/`getting-started` style - title + read-only guardrail + a small memory kernel (recommend-don't-act; comms payloads untrusted/header-only; filesystem is the source of truth) + `## Inputs` (`$ARGUMENTS` optional focus filter) + numbered survey Steps that first GATHER from every place lingering items live (plans board via `aw plans`/`plans.py`; staged prompts in `.agents/prompts/pending/`; comms inbox header-only; TODO.md; recent DECISIONS/CHANGELOG for context) and then have the AGENT REASON about priority itself and produce a prioritized recommendation OUTPUT contract (a ranked list, each item with a one-line reason and the exact next command). NOT-PRESCRIPTIVE ranking (OQ1 resolved): the runbook must NOT impose a fixed priority order; the agent surveys everything, then decides the order on the merits and STATES its reasoning. It may (a) offer the loose default order in OQ1 ONLY as a last-resort tie-breaker if it genuinely cannot decide, and (b) surface an off-record item ("this thing not in the plans/TODO record needs to happen before X") with its justification (OQ2 resolved: agent judgment is explicitly allowed to override the recorded ordering). + `## Reminders`. | `.agents/workflows/whatnext/whatnext.md` (new) | Low | file exists; content-lint (no em/en dashes); the runbook is not prescriptive (survey-then-reason, default only as tie-breaker) and permits off-record priorities; manual dry-run against this repo yields a sensible, reasoned ranked list |
| 2 | W1 | Author `README.md` (4-6 lines): capability blurb + `/whatnext` invocation + universal fallback ("read and execute `.agents/workflows/whatnext/whatnext.md`") + pointer to `index.md`. | `.agents/workflows/whatnext/README.md` (new) | Low | `tests/test_dir_readmes.py` passes (this README is REQUIRED by it) |
| 3 | W1 | Register the command: add ONE manifest row to `index.md` between the BEGIN/END markers: `whatnext | .agents/workflows/whatnext/whatnext.md | - | <read-only surveyor: recommends what to work on next by surveying plans/prompts/comms/TODO; recommends, never acts.>`. | `.agents/workflows/index.md` | Low | `parse_manifest` sees the row; a temp `install_into_repo` generates `.opencode/commands/whatnext.md` + `.claude/commands/whatnext.md` |
| 4 | W1 | Optional narrative: add a one-line mention of `/whatnext` in an `index.md` prose section if the other standalone commands are mentioned there (match existing convention; skip if none). | `.agents/workflows/index.md` | Low | reads consistently; no duplicate manifest |
| 5 | W2 | Reconcile the Sets (human chose "split into two Sets"): (a) this IPD is `Set: agent-continuity-workflows, Order: 1`; (b) re-tag the executed prompts-scaffold IPD from `Set: agent-continuity-workflows`/`Order: 2` to `Set: research-prompt-pipeline`/`Order: 2` (a mis-tag CORRECTION, recorded in its Workflow history, not a silent rewrite of frozen history); (c) leave the handoff IPD at `agent-continuity-workflows`/`Order: 3` (already correct); `/research` will later take Order 2. | `.agents/plans/executed/20260717-2118-01-scaffold-agents-prompts-staging-convention.md`, this IPD | Low | `plans.py set_warnings()` reports NO duplicate-Order warning across either Set; `aw plans --write-index` Sets view renders both Sets with unique Orders |
| 6 | W4 | Update `TODO.md`: retitle/renumber the narrative Set so it matches the reconciled front-matter (the prompt-pipeline items become `research-prompt-pipeline`; the surveyor/producer/snapshot trio is `agent-continuity-workflows` 1/2/3), and mark Order 1 (prompts scaffold) DONE. | `TODO.md` | Low | reads consistently with the two Sets; no lingering "Order 3 = /whatnext" claim |
| 7 | W1 | Add a CHANGELOG 1.3.0 "Added" bullet for `/whatnext`. | `CHANGELOG.md` | Low | bullet present; no em/en dashes |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | Medium | complexity | An `aw whatnext` CLI helper (deterministic survey in code). TODO explicitly says "portable prose runbook first; promote to `aw whatnext` later if it proves useful." Building CLI code now is speculative before the prose runbook is used. | Later IPD once the runbook proves its shape; it would reuse `plans.py` and add a comms inbox lister. |
| n/a | Medium | functionality | A comms inbox LISTER in `comms.py` (programmatic unread detection via ack index). `/whatnext` reads the inbox as prose (header-only) for v1; a scanner is a separate capability. | Part of the broker/ack-writing IPDs (comms line) or the `aw whatnext` promotion. |
| n/a | Low | functionality | `/research` (Order 2) and `/handoff` (Order 3) workflows. | Their own IPDs; `/handoff` already has `20260717-2000-01` (to-review). |

## Scope check

- Over-scope: none. Steps 1-4,7 build the command; Steps 5-6 are the direct W2/W4 reconciliation the human approved (split into two Sets). No CLI code (correctly deferred).
- Under-scope: confirm the runbook's survey Step names the `aw plans` command AND a prose fallback (for agents/tools without the CLI installed), since `/whatnext` must be portable to any agent. Step 1 validation covers this.

## Required tests / validation

- `tests/test_dir_readmes.py` (esp. `test_source_has_readme_for_every_top_level_capability`): must pass with the new `whatnext/README.md`.
- `tests/test_installer.py` parse/shim tests: the new standalone manifest row parses and produces a shim (not collapsed like an `assess-*`/`advise-*` catalog row).
- `tests/test_plans_board.py` / `plans.py set_warnings()`: after Step 5, no duplicate-Order warning within either Set. Add or extend a test only if the reconciliation is programmatically assertable; otherwise validate manually via `aw plans --write-index` and inspect the Sets view.
- Full suite: `python -m pytest -q` stays green; paste actual output (current baseline as of this review is 288 passed, 1 skipped; expect the same, since this is prose + manifest + front-matter edits with no new product code unless a Set-warning test is added).
- Manual: (a) `install_into_repo` into a temp repo, assert `.opencode/commands/whatnext.md` and `.claude/commands/whatnext.md` are generated and point at the runbook; (b) dry-run the `whatnext.md` runbook against THIS repo and confirm it produces a sensible, correctly-prioritized list (pending-approval plans surfaced, unread inbox flagged, staged prompts listed) without taking any action.

## Spec / documentation sync

- `index.md`: the manifest row IS the registration/spec (Step 3).
- `TODO.md`: Set reconciliation + mark prompts-scaffold done (Step 6).
- `CHANGELOG.md`: 1.3.0 Added bullet (Step 7).
- The executed prompts-scaffold IPD gets a Workflow-history line noting the Set-tag correction (Step 5).
- No `DECISIONS.md` entry: `/whatnext` applies existing principles (P5, D81, D82); the Set-split is housekeeping (OQ2 resolved: no new decision; record it in the executed IPDs' Workflow history only). Current DECISIONS max is D93 as of this review.
- No `AGENTS.md` change (consistent with other standalone workflows; the managed block is not per-command).

## Open questions

- OQ1 (recommendation ranking): RESOLVED (human, 2026-07-20 /plan-review). The surveyor is NOT prescriptive: it GATHERS from every place lingering items live, then the AGENT reasons about priority on the merits and states its reasoning. The order below is offered ONLY as a loose last-resort tie-breaker if the agent genuinely cannot decide (which is rare): (1) unfixed BLOCKER/HIGH or known bugs, (2) pending plans `approved` then `reviewed`, (3) unread comms inbox (header-only), (4) next `Order:` in an active Set, (5) staged prompts, (6) TODO. The agent also has explicit liberty to surface an OFF-RECORD priority ("this thing not in the record needs to happen before X") with justification. Encoded in Step 1.
- OQ2 (record a decision?): RESOLVED (human, 2026-07-20 /plan-review). No new DECISIONS entry - the two-Set split is an application of the existing D82 (Set/Order convention); record it in the executed IPDs' Workflow history only. Separately, the human affirmed the surveyor should have ample liberty to say "this un-recorded thing really needs to happen before this other thing" (folded into Step 1's non-prescriptive output contract).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload (that is release-review Section 9 after explicit human GO).

Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it; that sets `Status: reviewed`). Update `Status:` as it progresses, appending a Workflow-history line at each step.
2. On human approval, set `Status: approved` (+ the `Approval:` line), execute the ordered changes, run the validation, and sync specs/docs.
3. Only then set the terminal `Status: executed` and `git mv` this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`. Plan files are named `YYYYMMDD-HHMM-NN-<slug>.md`.
