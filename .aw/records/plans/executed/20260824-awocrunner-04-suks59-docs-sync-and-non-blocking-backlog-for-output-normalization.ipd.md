# IPD: Docs sync and non-blocking backlog for output normalization and remaining tools

- Date: 2026-08-24
- Kind: child
- Concern: Once `aw oc runipd` exists (children 01-03), the documentation still points only at `python3 tools/ipdrunner/runipd.py ...` (`tools/README.md`, the ipdrunner runbook). Operators need the new command documented. Separately, the deliberately deferred follow-on work - normalizing the runner's (well-liked) interactive/progress output into a shared renderer, and graduating the remaining tools (runagy/agy_run -> `aw agy run`, pwatch -> `aw pwatch`, agy_sessions -> `aw agy sessions`, view-antigravity-jsonl -> `aw agy view`) - must be captured as a committed backlog item so it is visible to `aw attention`, not lost in prose.
- Scope: Update `tools/README.md` (and the ipdrunner runbook if it instructs invocation) to document `aw oc runipd` (alias `aw opencode runipd`) as the primary way to run the driver, noting the `tools/` path still works as a compat shim; and file a committed medium, non-blocking backlog item via `aw backlog new` capturing (a) output-rendering normalization into a shared `agent_workflows` renderer and (b) graduating the remaining tools under `aw agy`/`aw pwatch`. Child 04 of the awocrunner Set; depends on children 02 and 03.
- Scope-Paths: tools/README.md, tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md, .aw/records/backlog/open/
- Status: executed
- Set: awocrunner
- Order: 4
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: suks59

## Workflow history
- 2026-08-25 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Docs sync: aw oc runipd documented as primary in tools/README.md + runbook (stale ipdrunner.py corrected); filed committed medium/followup backlog item 1sdkvd for output normalization + remaining-tool graduation; all E performed, all V pass with pasted evidence [Scope reconciliation - in-scope-unmodified .aw/records/backlog/open/: new followup backlog item 1sdkvd filed via aw backlog new; committed in 22da425 before the begin baseline; in-scope-unmodified tools/README.md: aw oc runipd documented as primary; committed in 22da425 before the begin baseline; in-scope-unmodified tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md: aw oc runipd primary + ipdrunner.py->runipd.py fix; committed in 22da425 before the begin baseline]
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (fix stale runbook ipdrunner.py->runipd.py), PR-002 (non-blocking is field-absence default, not a flag), OQ-01 marked resolved
- 2026-08-25 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 04 of awocrunner Set (docs sync + deferred-work backlog).

## Goal

Document `aw oc runipd` as the primary driver invocation and record the deferred output-normalization + remaining-tool-graduation work as a committed, attention-visible backlog item.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Documentation sync

- [x] E-01 Update `tools/README.md` (the `ipdrunner/` section) and `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md` (which DOES prescribe invocation) to present `aw oc runipd ...` (alias `aw opencode runipd ...`) as the primary command, with a note that `python3 tools/ipdrunner/runipd.py ...` continues to work via a compatibility shim. Also correct the runbook's STALE driver filename: it currently names the driver `ipdrunner.py` and prescribes `python3 tools/ipdrunner/ipdrunner.py ...` (runbook lines 4,47,61,90,98,108), but the actual script is `runipd.py` - fix every occurrence so the documented legacy/compat path is real. Keep the usage examples accurate to the shipped CLI (child 02). Write user-facing prose with no em/en dashes.
  - Depends on: none
  - Expected outcome: docs describe `aw oc runipd` as the primary entry and the shim as legacy-compatible; the runbook no longer references the nonexistent `ipdrunner.py`.
  - Execution note: commit 22da425; tools/README.md ipdrunner section retitled `aw oc runipd`, presenting the packaged command (alias `aw opencode runipd`) as primary with all examples in that form and a note that `python3 tools/ipdrunner/runipd.py ...` still works as a compat shim. The runbook now presents `aw oc runipd start` as primary (with the legacy form beside it) and the stale `ipdrunner.py` name was corrected to `runipd.py` at all 6 occurrences (Driver header + 5 invocation lines); `grep -c ipdrunner.py` runbook -> 0. AGENTS.md/RELEASING/CONTRIBUTING checked - no driver-path drift there.
  - Execution state: performed

### Task group 2: File the deferred-work backlog item

- [x] E-02 Create a committed backlog item with `aw backlog new --apply --priority medium --kind followup --summary "Normalize runner interactive output into a shared renderer and graduate remaining tools (runagy, pwatch, agy sessions/view) under aw"` (do NOT hand-name the file). In the item body capture: (a) extract runipd's `render_event`/`Palette`/`Heartbeat` streaming into a shared `agent_workflows` rendering utility (currently duplicated inline in `oc_runipd`); (b) graduate `agy_run.py` -> `aw agy run` (renamed runagy), `agy_sessions.py` -> `aw agy sessions`, `view-antigravity-jsonl.py` -> `aw agy view`, `pwatch.py` -> `aw pwatch`; (c) note this is non-blocking and follows the packaged-core + host-subcommand + compat-shim pattern established by the awocrunner Set. Non-release-blocking is the DEFAULT: simply do NOT add a `- Blocks-Release:` field to the item (there is no `--blocks-release` flag on `aw backlog new`, and a backlog item is non-blocking unless it carries that field per AGENTS.md). Do not attempt to "mark" it non-blocking with a flag.
  - Depends on: none
  - Expected outcome: a committed `open`, medium, followup backlog item exists, carries no `Blocks-Release` field, and appears in `aw attention` as `ready`.
  - Execution note: commit 22da425; filed via `aw backlog new --apply` (not hand-named) at `.aw/records/backlog/open/20260825-1sdkvd-01-1sdkvd-normalize-runner-output-and-graduate-tools.backlog.md` (id 1sdkvd, open/medium/followup). Body captures (a) shared-renderer extraction of render_event/Palette/Heartbeat, (b) graduating runagy/pwatch/agy sessions/agy view under aw, (c) non-blocking, follows the awocrunner packaged-core+shim pattern. No `- Blocks-Release:` field (non-blocking by default per AGENTS.md; no flag used). See DECISION 14-suks59-D1 re: pre-existing (unrelated) backlog-check findings.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Committed backlog lives under `.aw/records/backlog/open/`, created via `aw backlog new --apply` (owns the clustering filename + `Id/Status/Set/Priority/Kind/Summary` metadata); do NOT hand-name backlog files. It surfaces in `aw attention` (`open` -> `ready`).
- AGENTS.md: committed backlog must not be kept only in prose (e.g. a TODO), where the attention view cannot see it; hence a real `aw backlog` item, not a doc paragraph.
- `tools/README.md` currently documents the driver as `python3 tools/ipdrunner/runipd.py ...`; the runbook is `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md`.
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | Med | Toolkit user | Docs point only at the `tools/` path; the new `aw oc runipd` command must be documented as primary. |
| F-02 | Med | Maintainer | The deferred output-normalization + remaining-tool graduation must be a committed backlog item so `aw attention` can see it, not buried in prose. |

## Proposed changes (ordered, validatable)

1. Update `tools/README.md` (+ runbook if applicable) to document `aw oc runipd`/`aw opencode runipd`, shim noted as compatible.
2. File a committed medium, non-blocking followup backlog item for output normalization + remaining-tool graduation.

## Deferred / out of scope (with reason)

- Actually normalizing the output or graduating the other tools is the SUBJECT of the backlog item, not work done here; this child only documents and records.
- No code changes: docs and a backlog record only.

## Scope check

- Over-scope: none. Docs and one backlog record.
- Under-scope: none. Completes the Set's documentation and cleanly hands off the deferred work in an attention-visible form.

## Required tests / validation

- Manual/verifiable: `tools/README.md` shows `aw oc runipd` as primary (snippet); `aw backlog` / `aw attention` lists the new followup item as `ready`.
- `aw check` clean (no dangling refs introduced by the new backlog item).
- No test suite change required (docs + backlog only); `python3 -m pytest tests/` remains green.

## Spec / documentation sync

- This child IS the documentation-sync step for the Set. AGENTS.md/RELEASING references to the driver path, if any, should also be checked and updated to `aw oc runipd`; verify during execution and update only genuine drift.

## Open questions

### OQ-01: Should the deferred work be one backlog item or split (output-renderer vs. tool-graduation)?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED as one item now (they are closely related follow-ons and the user asked for a single non-blocking medium backlog). It can be split later when picked up if it proves too large; recording it is what matters for attention-visibility. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted snippet of the updated `tools/README.md` and runbook showing `aw oc runipd`/`aw opencode runipd` as the primary invocation with the shim noted; and a grep confirming no remaining `ipdrunner.py` occurrences in the runbook (the stale name is corrected to `runipd.py`).
  - Observed evidence: (commit 22da425) tools/README.md now heads `## aw oc runipd (the OpenCode IPD runner)` with usage `aw oc runipd 5ahblp`, `aw oc runipd status --repo ... <run-id>`, etc., a note "`aw opencode runipd ...` is an accepted alias" and "The legacy source-checkout path continues to work unchanged as a compatibility shim: `python3 tools/ipdrunner/runipd.py status ...`". The runbook now shows `aw oc runipd start \ ...` as primary with the legacy `python3 tools/ipdrunner/runipd.py start ...` beside it. `grep -c "ipdrunner.py" runbook` -> 0 (corrected to `runipd.py`); `grep -c "aw oc runipd" tools/README.md` -> 8.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the path of the created backlog file and pasted `aw attention` (or `aw backlog`) output listing it as an `open`/`ready`, medium, followup item; confirmation the file carries NO `- Blocks-Release:` line (so it is non-release-blocking by default); pasted `aw check` clean.
  - Observed evidence: (commit 22da425) File: `.aw/records/backlog/open/20260825-1sdkvd-01-1sdkvd-normalize-runner-output-and-graduate-tools.backlog.md`. `aw attention --format json` lists it: `{'id': '1sdkvd', 'tree': 'backlog', 'native_status': 'open', 'attention_class': 'ready', 'priority': 'medium', 'blocks_release': None}`. `grep -c Blocks-Release <file>` -> 0 (non-release-blocking by default). `backlog.parse_item` -> open/medium/followup, single-line summary, blocks_release None. `aw check backlog --agent` reports 5 diagnostics, NONE referencing 1sdkvd (`any('1sdkvd' in ...)` == False) - the new item introduces zero findings; the 5 are pre-existing, unrelated older-item drift (DECISION 14-suks59-D1).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (document the new command and record the deferred follow-on work), confined to docs and a single committed backlog record.

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved (one backlog item now). No blocking open question remains.
2. Scope fence: touch ONLY `tools/README.md`, the ipdrunner runbook (if it prescribes invocation), and the new backlog file under `.aw/records/backlog/open/` (created via `aw backlog new --apply`; do NOT hand-name it). Do NOT change code. If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting done, paste the ACTUAL evidence (doc snippet, `aw attention`/`aw backlog` listing, `aw check` output); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
