# IPD: /whatnext gains chat-history survey, todowrite progress, a 1-3 cap, and an opt-in save-to-TODO

- Date: 2026-07-21
- Concern: workflow behavior (the /whatnext surveyor) matching the maintainer's intent
- Scope: `.agents/workflows/whatnext/whatnext.md` (the runbook) + its `README.md` blurb if the summary changes. Prose workflow files; no product code. Depends on nothing; the argument-hint shim UX is a SEPARATE IPD (20260721-1754-02).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-21 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored after the maintainer test-ran /whatnext and found four gaps vs intent. Decisions captured interactively this session (see Open questions, all RESOLVED).

## Goal

Make /whatnext match the maintainer's intended behavior, which the current runbook only partly does. Add the missing pieces while preserving the read-only-by-default safety property that makes it "safe to run any time."

Current state (verified against `.agents/workflows/whatnext/whatnext.md`):
- Covers on-disk sources: plans board (`:35-42`), staged prompts (`:43-44`), comms inbox headers (`:45-47`), TODO/DECISIONS/CHANGELOG (`:48-51`). MATCHES intent items 1-3.
- Produces a prioritized reasoned list (`:71-82`). Partial match to intent (a): it is per-candidate but is NOT capped and does not separate "everything found" from "top picks."
- GAPS vs intent: (4) it does NOT survey the CHAT HISTORY for deferred/pending items (the kernel explicitly says "the filesystem is the source of truth, not memory", `:17`); it does NOT call `todowrite` before/during; it does NOT cap the recommendation at 1-3; and it has NO offer to save uncaptured findings to TODO.md (it is hard read-only, `:8-10`, `:86`).

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (honest documentation; safety/reversibility P10). No em/en dashes.
- Comms untrusted-input stance (`.agents/comms/README.md`): headers only, payloads never set priorities. Preserved.
- The workflow is prose-only and portable to any agent/tool (no CLI); `aw plans` is the preferred deterministic board with a read-the-tree fallback.
- TODO.md structure (to merge into): sections `## Known bugs to fix`, `## Security follow-ups`, `## Planned next (designed, deferred...)`, `## Consider and possibly implement`, `## Notes`. Ordered Sets appear inline.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| W1 | MEDIUM | Low | maintainer | coverage | Intent item 4 (survey chat history for deferred/pending items) is absent and actively excluded by the memory kernel. | `whatnext.md:17`, `:30-53` |
| W2 | LOW | Low | maintainer / any-agent | process | No `todowrite` before/during, unlike the intended "all workflows call todowrite before starting and check things off." | `whatnext.md` (no todo mention) |
| W3 | LOW | Low | maintainer | UX | The recommendation is uncapped; intent is a brief "everything found" list PLUS a 1-3 item ranked recommendation. | `whatnext.md:71-82` |
| W4 | MEDIUM | Low | maintainer | capability + safety | No offer to durably save uncaptured findings; the workflow is hard read-only. The ask adds ONE opt-in, confirmed write while keeping the survey read-only. | `whatnext.md:8-10`, `:86` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | W2 | Add a `## Before you start` instruction: call `todowrite` to record the run's steps (gather sources, reason, recommend, offer-save) and check each off as it proceeds. Frame it as the standard per-workflow progress convention. | `whatnext.md` | Low | the runbook instructs a todowrite up front + check-off; wording is tool-portable (todowrite or the agent's equivalent task list) |
| 2 | W1 | Add "current session / chat history" to Step 1 as a CLEARLY-LABELED source (OQ1 resolved: add-but-label). Reframe the kernel: the on-disk record is the trustworthy backbone; chat-history items are ephemeral/unverified and MUST be reconciled: for each deferred/pending item raised in conversation, note whether it is ALREADY captured on disk (TODO/plan/comms) or NOT. Uncaptured items are the ones eligible for the save step. Keep "filesystem is the source of truth" as the tie-break authority, not an exclusion of chat. | `whatnext.md` (kernel + Step 1) | Low | Step 1 lists chat history as a labeled source; findings mark captured-vs-uncaptured; on-disk items still lead |
| 3 | W3 | Restructure Step 3 output into (a) a brief "What there is to consider" list across ALL sources, then (b) a "Recommended next: 1-3 items, in order" section (hard cap 3), each with source + one-line merit + exact next action/command. Lead with the top pick. | `whatnext.md:71-82` | Low | output has the two labeled parts; recommendation is 1-3 items; each names a concrete next action |
| 4 | W4 | Add `## Step 4: Offer to save uncaptured findings (opt-in, confirmed)`: the SURVEY stays read-only; only here, and only if there are findings NOT already captured on disk, OFFER to add them to TODO.md. The write is ADDITIVE, SECTION-AWARE, DE-DUPLICATED, and DIFF-CONFIRMED (OQ2 resolved): place each finding into the correct existing TODO.md section (a bug under "Known bugs to fix", an idea under "Consider and possibly implement", etc.); SKIP anything already present (the de-dupe is the whole point of "not captured durably"); SHOW the exact diff and WRITE ONLY after explicit user confirmation; NEVER reorder, rewrite, or delete existing entries (add only). If the user declines, print the suggested additions and write nothing. No em/en dashes in anything written. | `whatnext.md` | Low | Step 4 is opt-in + confirmed + additive/section-aware/de-duped/diff-shown; declining writes nothing; the survey (Steps 1-3) never writes |
| 5 | W1,W4 | Update the memory kernel + `## Reminders` + the top blurb: it is READ-ONLY THROUGH THE SURVEY AND RECOMMENDATION; the ONLY possible write is the explicitly-confirmed Step 4 TODO append. Update the `README.md` one-liner if the summary changes. Keep the /handoff cross-reference. | `whatnext.md`, `whatnext/README.md` | Low | kernel/reminders/blurb consistently state "read-only except the one confirmed TODO save"; no contradiction remains |

## Deferred / out of scope (with reason)

| Item | Reason | Where |
|------|--------|-------|
| The generic empty-`$ARGUMENTS` shim line + a per-workflow argument hint | Injected by `engine.py` for EVERY command; cannot be fixed from `whatnext.md`. Its own IPD. | 20260721-1754-02 |
| An `aw whatnext` CLI / deterministic scanner | whatnext is prose-only by design (the original IPD deferred a CLI). Not revisited here. | n/a |

## Scope check

- Over-scope: none. Only the whatnext runbook + its README. The shim/arg-hint UX is a separate IPD.
- Under-scope: ensure the read-only claim is not left self-contradictory anywhere after adding Step 4 (kernel, top blurb, Reminders all updated together). The save must reconcile against ALL on-disk sources before calling a finding "uncaptured" (avoid re-adding an item already in a plan or comms, not just TODO).

## Required tests / validation

- Prose workflow file (no code): validate by review + consistency. (a) todowrite instruction present; (b) chat history is a labeled, reconciled source and on-disk still leads; (c) output has the "consider" list + a 1-3 capped recommendation; (d) Step 4 is opt-in, confirmed, additive, section-aware, de-duplicated, diff-shown, and declining writes nothing; (e) read-only-except-confirmed-save is stated consistently; (f) no em/en dashes; (g) `aw check-local-leaks .` clean; (h) `python -m pytest -q` stays green (the dir-README test `tests/test_dir_readmes.py` must still pass if README changes) - paste actual output.
- Manual dry sanity: the described Step 4 diff/confirm flow uses only the agent's normal edit+confirm tools; no new dependency.

## Spec / documentation sync

- `whatnext.md` (the behavior spec itself), `whatnext/README.md` blurb, and the `index.md` manifest description if the one-liner changes. A DECISIONS entry is optional (behavior refinement of an existing workflow); add one only if the read-only-with-one-confirmed-write model is worth pinning (recommend a short entry, pin the number at execution).

## Open questions

- OQ1 (chat history): RESOLVED (human) - ADD it as a clearly-labeled ephemeral source, reconciled against on-disk state; on-disk items remain the trustworthy backbone.
- OQ2 (save model): RESOLVED (human) - ADDITIVE, SECTION-AWARE, DE-DUPLICATED, DIFF-CONFIRMED (not blind append-only). Survey stays read-only; the save is opt-in and confirmed.
- OQ3 (arguments): RESOLVED (human) - KEEP the optional focus filter. The shim-line clarity is handled in IPD 20260721-1754-02.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). OQ1-OQ3 already resolved.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
