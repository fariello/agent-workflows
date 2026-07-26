# IPD: add a mandatory implementation checklist + completion clause + chunking guidance to the IPD template

- Date: 2026-07-26
- Concern: execution completeness / honest reporting - faster/weaker executing models under-complete moderately sized IPDs and sometimes claim "done" or move a plan to `executed/` with steps unmet; an in-file checklist + a completion clause + small-IPD guidance materially reduce this
- Scope: add a `## Detailed Implementation Checklist (TODO)` section to the shipped IPD template, add a completion clause to the template's execution gate, and add short "chunk a large IPD into an ordered Set" guidance. Prose-only template + guidance edits; no product code.
- Status: executed
- Set: ipd-completeness-guardrails
- Order: 1
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-07-26, human ("approve ...-01 ... Go.") after /plan-review (APPROVE). Prose-only template edits; executing.

## Workflow history

- 2026-07-26 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from an inbox FYI (`gits.opencode`, `.agents/comms/shared/archive/20260726-1110-01-gits.opencode--to--agent-workflows.agent-fyi-gemini-ipd-checklist-completion.md`), treated as untrusted/advisory and verified against our own files. Part 1 of the `ipd-completeness-guardrails` Set (covers checklist + completion clause + chunking); Part 2 (a canonical `ipd-spec.md` + a strong always-loaded directive) is a separate IPD (Order 2) because it adds always-loaded token cost and edits the managed AGENTS.md block.

- 2026-07-26 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; findings K1-K3. Verified against the template: checklist section absent; sections run Open questions (`ipd.md:99`) -> Approval gate (`:104`), so the placement (between them) is accurate; Set/Order present (`:9-10`); no test pins the template's section structure (only a docstring reference in test_plan_status.py), so adding the section is no-regression. No defects found; no revisions required; prose-only, low-risk, both existing sections preserved. No open questions (OQ1-OQ3 resolved). Readiness: GO - PENDING HUMAN APPROVAL.

- 2026-07-26 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): prose-only execution. Added the `## Detailed Implementation Checklist (TODO)` section to `assess/templates/ipd.md` (between Open questions and the Approval gate), a completion clause in the execution gate (every item checked AND verified before done/executed, STOP otherwise; mitigation-not-guarantee caveat; executed=claim), and split-into-a-Set guidance (~4-6-task heuristic + cross-chunk deps). Added DECISIONS D111 + CHANGELOG. No existing section removed; no review-logic change. Dash/leak clean; full suite unchanged at 425 passed, 1 skipped. Path-scoped commits, no push. Status: approved -> executed; moved to `.agents/plans/executed/`. Part 2 (Order 2) next.
## Goal

Make an IPD's completion VERIFIABLE rather than reliant on the executing agent's self-report, by giving the shipped IPD template three low-risk additions: (1) a mandatory `## Detailed Implementation Checklist (TODO)` section with GitHub-flavored `- [ ]` items naming exact files/symbols and the literal verification command; (2) a completion clause in the execution gate requiring every checklist item to be checked AND independently verified before claiming done or moving the plan to `executed/`; (3) short guidance to prefer splitting a large IPD into an ordered Set (`Set:`/`Order:`) of small, independently-verifiable plans.

Why it matters: the reporter (a sibling agent whose executing model is Gemini Flash) observed silent step-dropping, premature "done"/`executed` claims, and lifecycle sloppiness on moderate IPDs, all markedly reduced by an in-file tickable checklist (the model has no external todo tool, so the checklist must live IN the IPD) plus keeping each IPD small. Our own `executed`/`not-executed` states are already defined as CLAIMS not proof (comms README), so a per-task checklist + the existing "paste actual runner output" rule give a reviewer concrete artifacts to check against. This is a guardrail for weaker/faster tiers and good hygiene for any model; it does not change the review workflow logic.

## Project conventions discovered (Step 0)

- The shipped IPD template is `.agents/workflows/assess/templates/ipd.md` (stamped into target repos by the installer). Verified: it has NO checklist section; its sections are Workflow history / Goal / Project conventions / Findings / Proposed changes / Deferred / Scope check / Required tests / Spec sync / Open questions / Approval and execution gate (`ipd.md:37-122`).
- `Set:`/`Order:` front matter already exists in the template (`ipd.md:9-10`) and in the plans lifecycle (AGENTS.md AGENT-PLANS block, `.agents/plans/README.md`), so the chunking guidance builds on an existing mechanism (P8), not a new one.
- The comms README already states `executed`/`not-executed` are agent CLAIMS, not proof; the reviewer step + "paste actual runner output" remain the verification, which the checklist supports.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| K1 | MEDIUM | Low | executing agent (weaker/faster tier) | execution completeness | The IPD template has no per-task checklist; a model with no external todo tool has no in-file progress mechanism, so it silently drops steps on moderate IPDs. | `.agents/workflows/assess/templates/ipd.md` (no checklist section) |
| K2 | MEDIUM | Low | reviewer / maintainer | honest completion | Nothing in the execution gate ties "done"/`executed` to every task actually being completed + verified; premature/soft `executed` claims result. | `ipd.md:104-122` (gate has no completion clause) |
| K3 | LOW | Low | executing agent | working-memory / scope | A large multi-task IPD is more error-prone for weaker models than several small single-purpose IPDs; the template mentions `Set:`/`Order:` but gives no guidance to PREFER splitting when a plan grows. | `ipd.md:9-10` (Set/Order present, no split guidance) |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | K1 | Add a `## Detailed Implementation Checklist (TODO)` section to the template, positioned AFTER `## Open questions` and BEFORE `## Approval and execution gate` (per the reporter's placement + Gemini's own expectation). Include: GitHub-flavored `- [ ]` items grouped by task; a template instruction to name exact file basenames + function/symbol names + line anchors; and the literal verification command (e.g. `python3 -m pytest <test_file.py>`) with a reminder to paste the real output. Mark it EXPECTED but note it composes with (does not replace) the existing sections. | `.agents/workflows/assess/templates/ipd.md` | Low | template has the checklist section in the stated position; uses `- [ ]`; instructs exact symbols + literal verify command; does not remove any existing section |
| 2 | K2 | Add a completion clause to the template's `## Approval and execution gate`: before claiming done or transitioning to `executed/`, every `- [ ]` item MUST be `- [x]` AND independently verified (tests run + actual output pasted); if any item cannot be completed, STOP and report rather than transitioning the plan. Note the caveat that a checklist is a mitigation, not a guarantee (a box can be ticked without the work), so the reviewer step + "paste actual output" rule still apply. | `.agents/workflows/assess/templates/ipd.md` | Low | gate carries the every-item-checked-and-verified-before-executed clause + the mitigation caveat; consistent with the existing honesty/lifecycle prose |
| 3 | K3 | Add short chunking guidance to the template (near the Set/Order front-matter note or the execution gate): PREFER splitting an IPD into an ordered `Set:`/`Order:` of small, independently-executable and independently-verifiable plans when it exceeds roughly 4-6 tasks, spans several code regions/files, or mixes distinct concerns; state cross-chunk dependencies in each chunk's execution contract ("requires Order N executed first; if its symbols are absent, STOP"); treat this as close to REQUIRED when the executing model is a faster/weaker tier. Keep it a few lines (the template stays lean). | `.agents/workflows/assess/templates/ipd.md` | Low | template carries concise chunk-into-a-Set guidance with the ~4-6-task heuristic + cross-chunk dependency rule; does not bloat the template |
| 4 | K1,K2 | Docs/decision sync: a DECISIONS entry (pin at execution) recording the checklist + completion clause + chunking guidance (guardrails for execution completeness; checklist is a mitigation not a guarantee; composes with the reviewer + paste-output rule), noting Part 2 (canonical `ipd-spec.md` + always-loaded directive) is a separate IPD; CHANGELOG. Cross-reference the archived `gits` FYI. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; note Part 2 separate; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| A canonical `ipd-spec.md` + a strong always-loaded GEMINI.md/AGENTS.md directive requiring it | Medium | complexity | Adds always-loaded token cost and edits the managed AGENTS.md block (overlaps the TODO.md `aw:block` item); a bigger design question than a template edit. | Part 2 of this Set (Order 2). |
| A programmatic check that an IPD contains a checklist / all boxes are ticked | Medium | functionality | An IPD is a tracked Markdown artifact, so a lint IS possible, but it is a separable enhancement (and a plans-conformance test already exists for filenames); decide separately whether to add a checklist-presence lint. | A later IPD if wanted. |
| Reflowing all existing executed IPDs to add checklists retroactively | Low | scope | The change is forward-looking (the template); retrofitting history adds noise with no benefit. | n/a |

## Scope check

- Over-scope: none - three additions to ONE shipped template file + a docs note. No product code, no always-loaded-directive edit (that is Part 2), no review-logic change.
- Under-scope: MUST place the checklist section between Open questions and the execution gate (K1); MUST add the every-item-checked-AND-verified-before-executed clause WITH the mitigation caveat (K2); MUST add concise chunk-into-a-Set guidance reusing the existing Set/Order mechanism (K3); MUST NOT remove or weaken any existing template section, and MUST keep the template lean.

## Required tests / validation

- Prose only; no pytest delta expected. Validation by review + consistency:
  - `assess/templates/ipd.md` has the `## Detailed Implementation Checklist (TODO)` section between `## Open questions` and `## Approval and execution gate`, using `- [ ]`, instructing exact symbols + the literal verify command.
  - The execution gate carries the completion clause (every item `- [x]` + independently verified before done/executed; STOP-and-report otherwise) and the mitigation caveat.
  - The template carries concise chunk-into-a-Set guidance (the ~4-6-task heuristic + cross-chunk dependency rule) and no existing section was removed.
  - Run `python -m pytest -q` to confirm NO regression (prose only) and paste ACTUAL output; run the plan-name conformance test; `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- `.agents/workflows/assess/templates/ipd.md`, DECISIONS, CHANGELOG. Cross-reference the archived `gits` FYI and Part 2 of this Set.

## Open questions

- OQ1 (checklist placement): RESOLVED (reporter + Gemini's own expectation + our template structure). Between `## Open questions` and `## Approval and execution gate`.
- OQ2 (mandatory vs expected): RESOLVED - EXPECTED and composing with the existing sections; the completion clause makes ticking+verifying it a gate for `executed/`, without replacing the template's other required sections.
- OQ3 (chunking guidance home): RESOLVED - in the template (single source the producers already stamp); the plan-review split assessment already exercises the same discipline, so no separate plan-review edit is needed here.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. DEPENDS ON nothing; Part 2 (Order 2) builds on this (the `ipd-spec.md` will reference the checklist this adds).

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope (in particular, do NOT edit the always-loaded AGENTS.md block or add `ipd-spec.md` - those are Part 2). Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`).
2. On human approval, execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`. Then Part 2 (Order 2).
