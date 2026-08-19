# IPD: aw doctor and attention view upgrades

- Date: 2026-08-18
- Kind: orchestrator
- Concern: TODO items #1, #33, #36, #37 (tmp/todo.md): the `aw attention` cross-tree view is too verbose (full per-item paths, no urgency/importance/blocking columns) and there is deliberately NO `aw doctor` verb (cli.py:4) even though every deep-inspection signal already exists scattered across the codebase (dangling refs artifact_core.find_dangling_citations:207, malformed names normalize_plan_names/research_contract.parse_name, status-vs-location backlog.py:149 + attention.py:271, git tracked/untracked/dirty engine.classify_git_state:2464/run_git_diagnostics:2516/git_is_tracked:1431, version drift versioning.status:370). Attention also cannot yet warn that `aw setup`/`/setup-repo` still needs running (bare-`aw` configured-state check cli.py:4035-4053 + the actions ledger open/dismissed) nor surface RELEASE BLOCKERS (the Blocks-Release gate from the awrelease Set / spec 20260818-1525-03).
- Scope: Set F. Ship three child Orders: (01) make the attention board compact (strip the common dir prefix into the section header, bare filenames) and add urgency (from last_history_at attention.py:34-42) + blocking/importance columns (#36, #37); (02) attention highlights setup-needed unless run or dismissed (#1) and surfaces release-blockers from the awrelease Blocks-Release gate (DEPENDS ON awrelease); (03) create the new `aw doctor` verb aggregating every existing check signal into one Drift-based report (#33). OUT: the local->untracked lane rename (#39) is the sibling Set awuntracked; building the Blocks-Release gate itself (owned by awrelease - this Set only CONSUMES its data).
- Status: approved
- Approval: 2026-08-18, human ("Approve ALL 21 IPDs now ... Execute everything one at a time using Gemini ... then do it yourself.") after /plan-review (rigorous, opencode Opus 4.8; APPROVE / APPROVE WITH REVISIONS APPLIED).
- Set: awdoctor
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: zz2dum

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): high-level skeleton from TODO items 1,33,36,37 (+ release-blocker surfacing, depends on awrelease); children to be fleshed out.
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against attention.py:34-42/362/486/507, cli.py:4/1875/4035-4053, and artifact_core.py:207; orchestrator breakdown and cross-set dependencies sound; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.

## Goal

Make the operator- and agent-facing state views actionable: tighten `aw attention` into a compact,
prioritized board (common-prefix folded into the section header, bare filenames, urgency + blocking +
importance columns) that also warns when setup has not been run and surfaces release blockers, and
create a new `aw doctor` verb that aggregates every deep-inspection signal already computed in the
codebase into one Drift-based report. This turns "what needs attention?" and "is the repo healthy?"
into two crisp commands instead of scattered signals and verbose output.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..03 through the IPD lifecycle in dependency order (author -> /plan-review -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing. Sequence: 01 (compact board + urgency/blocking columns) and 03 (`aw doctor` aggregator) are independent of external Sets; 02 (setup-needed + release-blocker surfacing) DEPENDS ON the awrelease Set having landed the Blocks-Release gate that supplies release-blocker data, so schedule 02 after awrelease or gate its release-blocker half on that data existing. Note #39 (local->untracked rename) is the sibling Set awuntracked, not this Set.
  - Depends on: none
  - Expected outcome: Orders 01..03 executed; `aw attention` renders a compact prioritized board that warns on setup-needed and surfaces release blockers; `aw doctor` exists and reports every existing check signal as one Drift-based report; all `--check`s + suite green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Split by concern: 01 is the attention BOARD rendering (compact + priority columns, all-local data),
03 is the new `aw doctor` AGGREGATOR (all-local signals), and 02 is the attention SIGNAL surfacing
that reaches outside this Set (setup ledger + the awrelease Blocks-Release gate). 01 and 03 have no
cross-Set dependency; 02's release-blocker half depends on awrelease.

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | awdoctor-attention-compact-and-signals (to scaffold) | Compact the attention board (strip the common dir prefix into the section header, e.g. `## ready (15) .aw/records/backlog/` then bare filenames; rework the header at attention.py:486 and the line builders at attention.py:507/515) + add urgency (derived from `last_history_at`, attention.py:34-42) and blocking/importance columns (from `gate` + classification). Keep the JSON render (attention.py:362) faithful. Covers #36, #37. | none |
| 02 | awdoctor-setup-and-release-blockers (to scaffold) | Attention highlights that `aw setup`/`/setup-repo` still needs running UNLESS it was run or dismissed (reuse the bare-`aw` configured-state check cli.py:4035-4053 + the actions ledger open/dismissed setup-repo action). Also surface RELEASE BLOCKERS from the awrelease Blocks-Release gate (spec 20260818-1525-03 release-record): once the gate exists, attention shows what blocks the release. Covers #1 + release-blocker surfacing. | 01; awrelease (Blocks-Release gate data) |
| 03 | awdoctor-deep-inspector (to scaffold) | Create the new `aw doctor` verb (currently intentionally absent, cli.py:4; former doctor folded into _preflight_warnings cli.py:1875 + status) that aggregates every existing deep-inspection signal - dangling refs (artifact_core.find_dangling_citations:207), malformed names (normalize_plan_names/research_contract.parse_name), status-vs-location (backlog.py:149, attention.py:271 disposition-mismatch), git tracked/untracked/dirty (engine.classify_git_state:2464, run_git_diagnostics:2516, git_is_tracked:1431), version drift (versioning.status:370) - into ONE Drift-based report using the existing drift_exit_code convention. Covers #33. | none |

## Completion criteria (the whole Set is done only when)

- Orders 01..03 all executed and moved to `.aw/records/plans/executed/`.
- `aw attention` renders a compact board: each section header carries the common dir prefix (e.g.
  `## ready (15) .aw/records/backlog/`) and items are bare filenames; each item shows urgency (age
  from `last_history_at`) and blocking/importance signals; the JSON render stays faithful.
- `aw attention` warns when setup has not been run unless it was run or dismissed, and surfaces
  release blockers sourced from the awrelease Blocks-Release gate (when that data exists).
- `aw doctor` exists as a verb and reports every listed check signal in one Drift-based report,
  exiting nonzero on drift per the drift_exit_code convention.
- Full serial suite green; `aw attention --check` and every other `--check` + `sanitize --agent` clean.

## Cross-IPD validation

- Order 01 (compact board) MUST precede Order 02 because Order 02 adds new attention signals (setup-
  needed, release blockers) that render inside the same board Order 01 restructures; landing 01 first
  avoids a rebase of the render layer.
- Order 02's release-blocker half DEPENDS ON the awrelease Set: the Blocks-Release gate (spec
  20260818-1525-03) must supply the release-blocker data before attention can surface it. If awrelease
  has not landed, gate that half of Order 02 (setup-needed can ship independently) rather than inventing
  gate data here.
- Order 03 (`aw doctor`) reuses the SAME underlying signal functions attention already consumes
  (dangling refs, status-vs-location, git state); after landing, re-run the full check suite to confirm
  doctor and attention agree on shared signals (no divergent second implementation).

## Deferred / out of scope (with reason)

- #39 (local->untracked lane rename): owned by the sibling Set awuntracked, not this Set (referenced,
  not duplicated).
- Building the Blocks-Release gate itself: owned by the awrelease Set (spec 20260818-1525-03); this Set
  only CONSUMES its data in Order 02.
- Any new inspection signal `aw doctor` does not already have a computed source for: out of scope -
  Order 03 aggregates EXISTING signals into one report, it does not invent new checks.

## Scope check

- Over-scope: none. This Set does not build the Blocks-Release gate (awrelease) nor the untracked lane
  rename (awuntracked); it consumes/refers to them.
- Under-scope: none - Order 01 covers the compact board + urgency/blocking/importance columns (#36,
  #37), Order 02 covers setup-needed surfacing (#1) + release-blocker surfacing, Order 03 covers the
  new `aw doctor` aggregator (#33). The two adjacent concerns are the documented sibling Sets.

## Required tests / validation

Per-Order V-items plus the whole-Set completion criteria above; the orchestrator's E-01 verification
re-runs the full serial suite + every `--check` + `sanitize --agent`, confirms `aw attention` renders
the compact prioritized board (with setup-needed + release-blocker signals) and that `aw doctor` runs
and reports each aggregated signal with the drift_exit_code convention.

## Open questions

### OQ-01: Does `aw doctor` REPORT-ONLY, or also offer to fix (auto-remediate) the drift it finds?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Lean report-only for the first cut (aggregate + Drift exit code,
  matching the existing `--check` verbs), leaving any `--fix`/remediation to a follow-up; resolve at
  Order 03 authoring. Not blocking because a read-only aggregator is independently useful and lower risk.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all three child Orders 01-03 show `Status: executed` under `.aw/records/plans/executed/`; paste `aw attention` output showing the compact board (common-prefix section headers + bare filenames + urgency/blocking columns) and the setup-needed + release-blocker signals; paste `aw doctor` output showing each aggregated signal and its exit code; paste full serial suite result + `aw attention --check` + other `--check`s + `sanitize --agent` all clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: three Orders for one coherent objective (make repo state actionable via better attention + a new doctor), split by concern - 01 board rendering (compact + priority columns), 02 external-signal surfacing (setup ledger + awrelease Blocks-Release gate), 03 the `aw doctor` aggregator - each independently reviewable/executable and each maps to distinct TODO items (#37/#36, #1/release-blockers, #33); 01 and 03 are self-contained while only 02 reaches across to the awrelease Set, so the split keeps the cross-Set dependency isolated to one child.

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The
orchestrator (opencode Opus 4.8, or Gemini via `agy` when delegated) drives each child Order through
its own lifecycle, owns all verification + path-scoped commits (`git commit -m msg -- <path>`, never
`git add -A`/`-a`), and NEVER pushes. Each Order (and finally this orchestrator) moves to `executed/`
only after `aw ipd lint --phase pre-transition` conforms and the V-items are verified with pasted
evidence. Order 02's release-blocker half is gated on the awrelease Blocks-Release gate existing; if it
has not landed, that half is deferred rather than faked. Any version bake / tag / publish is Section 9,
human-gated - not part of this Set.
