# IPD: Replace the location-plus-token lifecycle gate with one plan-scoped live-holder check

- Date: 2026-09-30
- Kind: orchestrator
- Concern: The terminal lifecycle gate shipped by executed plan `u27oh3` decides "a runner owns this plan" from the FOLDER PATH and then demands a per-run secret to proceed, and both halves are wrong under GUIDING_PRINCIPLES P15, which names this very mechanism as its measured example. The location guess (`ipd_lifecycle.lane_worktree_active`, true for anything under `.aw/worktrees/` or on an `aw/lane/*` branch) wrongly refused a human's own feature worktree (measured 2026-09-26, `feat-partition`, `AW-LIFECYCLE-ROLE-001`) and blocks recovery of a lane whose runner died, because a dead runner's lane is indistinguishable from a live one to a path test. The token stops only honest actors, as the gate's own comment concedes, and honest actors are already stopped by the worker label and its clear message. Backlog `dvonrn` settled the replacement with the maintainer as decisions D1 through D8 on 2026-09-26: refuse only when a LIVE run holds THIS PLAN, allow begin and finalize anywhere, nudge toward the lane, and delete the token and the location guess. Authoring measured that this cannot be one plan: the run records cannot answer the new question at all today (no machine is recorded anywhere, and no predicate is plan-keyed), so the records work must land and be tested BEFORE any refusal changes, and the advisory nudge is a print with no gate that must not be entangled with a deletion of eleven token sites across five modules.
- Scope: Orchestrate three children that together implement decisions D1 through D8. `urv602` records the machine in `driver.lock` and adds the one plan-scoped three-valued live-holder predicate, changing no refusal. `e25iy9` deletes the token and the location guess, places the worker-label and holder checks inside all three core transition functions, adds the recorded `--take-over` override, and amends specs `7ckptx` and `llbr2b`. `m47znv` emits the advisory lane nudge D1 requires, refusing nothing. This plan holds ORCHESTRATION ONLY: every deliverable belongs to a child, and this file contributes no code, no test, no record and no spec edit of its own. EXCLUDES, in every child without exception: the worker-label check's semantics (D1 keeps them verbatim), the opt-in OS sandbox (D7 keeps it as optional isolation), every other anti-malice mechanism in the tree (D5 hands those to backlog `ariaau`), and any attempt to make the new check a hard boundary rather than guidance.
- Scope-Paths: .aw/records/plans/pending/20260930-lifegate-00-u4glub-replace-the-location-plus-token-lifecycle-gate-with-one-plan.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: fail
- Coverage-Fingerprint: 738eddaa0f018fd5147fa381a527d43c44363bf42e0a2ad90c4004b5753fe596
- Coverage-Checked: 2026-10-06 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: high
- From-Backlog: dvonrn
- Blocks-Release: next
- Set: lifegate
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: u4glub

## Workflow history

- 2026-10-06 coverage fail (aw oc run): fingerprint 738eddaa0f01, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated backlog `dvonrn` as a Set of three children rather than one plan. Decisions D1-D8 were settled with the maintainer on 2026-09-26 and are IMPLEMENTED here, not reopened. THREE MEASUREMENTS IN THIS LANE CHANGED THE SET'S SHAPE FROM THE ITEM'S DESCRIPTION. FIRST, D2's liveness rule is unimplementable against today's records: `runner_shared.run_lock` writes only `pid=` and `started=` into `driver.lock`, and `state.json` has no machine field at all (its `host` means the agent program, `oc` or `agy`), so the cross-machine case D3 exists to make safe has no input to read. That is what makes Order 01 a separate, refusal-free plan rather than a paragraph inside the deletion. SECOND, D2 specifies the runner passes its own run id as the holder exception, and the transport already exists AND already reaches the worker: both hosts export `git_commit_helper.RUN_ID_ENV` (`AW_RUN_ID`) into the child environment for commit trailers. That simplifies Order 02 (no new variable) and creates the Set's sharpest hazard, since an environment default for the exception would hand the lane agent exactly the bypass D2 denies it; Order 02's E-05 fences it and its V-05 pins the fence with a mutation case. THIRD, the token's surface is eleven sites across five modules, not the two gate blocks the item describes, including a `get_run_attestation` that lazily MINTS a token for any existing run directory and a `_call_driver_finalize` that signature-inspects for the `attestation` keyword; a two-site deletion would have left a dead parameter threaded through five functions.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the lifecycle gate refuse for the one real reason, that someone else is actively working on this plan,
and allow begin and finalize everywhere else, so a human's own worktree and a dead runner's lane both stop
being collateral damage.

WHY THIS IS A SET AND NOT ONE PLAN, since that is the decision this file exists to justify. The three
children are not phases of one edit; they are three different kinds of work with different risk and
different validation shapes.

Order 01 is a RECORDS AND PREDICATE change that alters no refusal at all. Its correctness is checked by
driving a predicate against synthetic run directories, and it is safe to land alone because nothing calls
it yet. It must be first for a mechanical reason rather than a stylistic one: D2's liveness rule is the
conjunction of a lock probe and a process check, and the process check is meaningless about a process on
another computer, so without a recorded machine the replacement gate would report a live foreign run as
dead. The records must be complete before a refusal depends on them.

Order 02 is a DELETION AND GATE REPLACEMENT touching five modules, both host drivers, the CLI, two specs
and the CHANGELOG. Its correctness is checked by driving every entry point and by two regression cases that
reproduce the measured defects. It cannot be split further without leaving the repository worse off at the
seam, which its own cohesion rationale records: removing the token before the holder check exists would
leave the terminal transition with no concurrency protection, while adding the check before removing the
location gate would leave BOTH refusals live, which is strictly more blocking than today.

Order 03 is an ADVISORY with no gate: one line on stderr, suppressed in machine-readable modes, that
changes no exit code. Its risk is the opposite of Order 02's, which is why it is separate: the hazard is a
future author "strengthening" it into the location rule Order 02 just deleted, so it needs its own fence
and its own tests rather than being a footnote inside a large deletion.

WHAT THE GATE BECOMES, stated once so a reviewer can hold the whole Set in mind. Each of `begin`,
`finalize` and `retire_orchestrator` performs, in this order: the EXISTING worker-label refusal
(`AW_EXECUTION_ROLE=worker`, `AW-LIFECYCLE-ROLE-001`, unchanged), then the NEW plan-scoped check, which
refuses only when a live run other than the caller's own holds this plan, or when liveness cannot be
determined. Nothing else refuses. No path is consulted and no secret is presented.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm each child reached executed, in dependency order

- [ ] E-01 CONFIRM urv602 REACHED executed
  - Depends on: none
  - Expected outcome: `urv602` reads `- Status: executed` on disk and is in `.aw/records/plans/executed/`, with every `V-*` carrying concrete pasted evidence.
  - Execution state: pending
  Order 01 records `host=<machine>` in the driver lock record and adds the one three-valued plan-keyed live-holder predicate, implementing D2's held-and-alive rule and D3's liveness order. It MUST be first: Order 02's refusal calls that predicate, and D3's cross-machine safety has no input until the machine is recorded. It changes NO refusal, which is what makes it safe to land alone.

- [ ] E-02 CONFIRM e25iy9 REACHED executed
  - Depends on: E-01
  - Expected outcome: `e25iy9` reads `- Status: executed` on disk and is in `.aw/records/plans/executed/`, with every `V-*` carrying concrete pasted evidence.
  - Execution state: pending
  Order 02 deletes the location guess and the token across eleven sites in five modules, places the worker-label and holder checks inside `begin`, `finalize` and `retire_orchestrator` so no caller routes around them, adds the recorded `--take-over '<reason>'` override, and amends specs `7ckptx` and `llbr2b`. It declares `executed:urv602`. It is the only child that changes a refusal, the only one that amends a spec, and the only one that touches the CHANGELOG.

- [ ] E-03 CONFIRM m47znv REACHED executed
  - Depends on: E-02
  - Expected outcome: `m47znv` reads `- Status: executed` on disk and is in `.aw/records/plans/executed/`, with every `V-*` carrying concrete pasted evidence.
  - Execution state: pending
  Order 03 emits D1's advisory nudge when begin or finalize runs in main while a lane for that plan exists. It declares `executed:e25iy9` because the nudge only makes sense once the location rule is gone: emitted before that, it would advise moving to a lane where the transition would then be refused. It refuses nothing and changes no exit code.

## Child IPDs, sequence, and dependencies

| Order | Id | Title | Depends on | Why this order |
|---|---|---|---|---|
| 01 | `urv602` | Record the machine in `driver.lock` and add the plan-scoped live-holder predicate | none | The new refusal's input does not exist today: no machine is recorded anywhere and no predicate is plan-keyed. Refusal-free, so it lands and is tested on its own before anything depends on it. |
| 02 | `e25iy9` | Delete the driver token and the location guess and check the live holder inside all three core transitions | `executed:urv602` | The substantive change. Calls Order 01's predicate, so it cannot precede it; carries the deletion, both spec amendments and the CHANGELOG correction. |
| 03 | `m47znv` | Nudge toward the lane when begin or finalize runs in main while a lane for that plan exists | `executed:e25iy9` | Advisory only and lowest risk, so last. Depends on Order 02 because a nudge toward the lane emitted while the location gate still refuses in the lane would advise an action the tool would then refuse. |

## Completion criteria (the whole Set is done only when)

All six must hold. Each is falsifiable from artifacts on disk or from pasted evidence, so a reviewer can
check them without re-deriving the design.

1. ALL THREE CHILDREN READ `executed` ON DISK, in `.aw/records/plans/executed/`, each with every `V-*`
   carrying concrete pasted evidence rather than a placeholder. The directory is the harder-to-forge
   signal and is checked alongside the status field.
2. THE TWO MEASURED DEFECTS ARE CLOSED AND PINNED AS TEST CASES, not asserted in prose. A human's own
   worktree under `.aw/worktrees/` with no live run now succeeds (the `feat-partition` refusal of
   2026-09-26), and a lane whose runner died now succeeds (the recovery hole). Both live in Order 02's
   test file.
3. NOTHING KEYS ON LOCATION ANY MORE. `lane_worktree_active` does not exist, neither remaining gate tests
   a path or a branch name, and the only refusals in the three core functions are the worker label and the
   live-holder check.
4. NO SECRET REMAINS. `AW_DRIVER_ATTEST`, the token file, its minting, its verification, its caching and
   its withholding are all gone from the package, with no dead parameter left threaded through any
   function.
5. EVERY ENTRY POINT IS COVERED BY ONE PREDICATE, demonstrated by Order 02's D4 matrix test driving
   `aw ipd begin`, `aw ipd finalize`, `aw set executed`, `aw ipd set executed`, orchestrator retirement and
   the runner's own begin and finalize, each refusing identically against a held plan and each proceeding
   with the holder's run id. This is the criterion that stops a future caller silently skipping the check.
6. THE WORKER-LABEL CHECK STILL WORKS AND STILL RUNS FIRST, including the environment fence: a
   worker-labelled caller with `AW_RUN_ID` set in its environment is still refused. Order 02's V-05 pins
   it with a mutation case, because this is the one way the Set could pass every other test while silently
   reintroducing a lane bypass.

## Cross-IPD validation

Four checks span the children and cannot be performed by any child alone, which is why they live here.

- THE REFUSAL SURFACE SHRANK AND DID NOT MOVE. Read Orders 01, 02 and 03 together and confirm the Set's
  NET effect on refusals is: one refusal deleted (location plus token), one added (live holder, including
  undeterminable), one relocated and otherwise unchanged (the worker label, now inside the core functions),
  and one advisory added that refuses nothing. No child can check this: Order 01 changes no refusal at all,
  Order 02 cannot see whether Order 03 added one, and Order 03 cannot see what Order 02 removed.
- THE ENVIRONMENT FENCE HELD ACROSS THE SET. `AW_RUN_ID` reaches the worker for commit trailers and the
  holder exception must never default from it. Confirm from the COMBINED diff of Orders 02 and 03 that no
  site reads a run id from the environment for authority purposes, rather than from Order 02's scope check
  alone, because Order 03 also edits the same two functions.
- THE TWO QUESTIONS STAYED DISTINCT. Order 01's predicate answers "is a live run working on this plan?"
  and Order 03's query answers "does a lane for this plan exist?". They differ precisely when a lane's run
  has ENDED, which is Order 03's main case, so confirm from the combined diff that Order 03 did not wire
  itself to Order 01's predicate. Order 03 pins this behaviorally, but only the combined view shows the two
  inputs are genuinely separate.
- EXACTLY ONE CHILD AMENDED A SPEC. Only `e25iy9` may touch a `.spec.md` (`7ckptx` and `llbr2b`). Confirm
  from the combined diff that no other spec file was modified by any child and that `7ckptx` R4.5's
  honest-limit sentence survives verbatim. Both runners report declared-versus-actual spec edits per item
  at run end, so a spec changed by a child that declared none is visible there too.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this Set is by symbol or quoted string; `40868bb1` is a durable sha.
- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN (AGENTS.md). This file's three `E-*` items are child-confirmation rows and nothing else: no deliverable, no baseline established before a child runs, no records reconciliation afterwards. That is deliberate and is what makes the runner's retirement of this plan honest, since a rollup SKIPS the pre-transition E/V checkpoint on the premise that a parent's items are performed by nobody. Every deliverable in this Set is owned by a child, so the orchestrator-coverage gate should find no work here that no child covers.
- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT (AGENTS.md). Exactly one child amends specs: `e25iy9` declares both `7ckptx` and `llbr2b` in its own `- Scope-Paths:`, because it changes the refusal those specs describe. This orchestrator declares no spec and no code path.
- GUARD AGAINST HONEST MISTAKES, NEVER AGAINST A MALICIOUS AGENT (GUIDING_PRINCIPLES P15, added 2026-09-26 in commit `40868bb1`). The Set is P15's own worked example, and P15 prescribes all four elements of the replacement: key on the real condition rather than a proxy, refuse with a clear message naming cause and remedy, offer a deliberate recorded override, and make recovery easy.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md; GUIDING_PRINCIPLES P16). Load-bearing across the whole Set rather than in one child, because the obvious test for each child is forbidden: "assert `lane_worktree_active` is gone" for Order 02, "assert the predicate is called from three places" for Order 01's consumer, and "assert the nudge does not import the predicate" for Order 03. Each child states what it pins instead, and in every case the behavioral pin is the stronger check.
- AN EXECUTED PLAN'S RECORD IS IMMUTABLE (AGENTS.md). Executed plans `u27oh3` (which built the token and the location guess) and `1o4eif` (the opt-in sandbox) describe the arrangements this Set changes. Neither is edited. A dated `## Workflow history` line pointing at this Set is the permitted addition and no child requires one.
- RUN THE SUITE BARE (AGENTS.md). `pyproject.toml` `addopts` already supplies quiet, parallel and the fast subset; a second `-q` compounds into `-qq` and suppresses the `N passed` line every child is required to paste.
- COMMENTS AND PLANS ARE NOT USER-FACING PROSE (GUIDING_PRINCIPLES P13). Only two artifacts this Set writes are user-facing and must carry no em or en dashes: Order 02's CHANGELOG entry and Order 03's advisory line.

## Findings

| # | Finding | Evidence | Consequence for this Set |
|---|---|---|---|
| F-1 | The gate is a location guess followed by a secret | `finalize` and `retire_orchestrator` each contain `if lane_worktree_active(repo_root):` then require `verify_driver_attestation`; the predicate tests a path under `.aw/worktrees/` or an `aw/lane/*` branch | Both halves are deleted by Order 02; the proxy is exactly what P15 forbids |
| F-2 | The token's futility is conceded in the gate's own comment | "a same-user agent inside the lane can still read `<main>/.aw/records/runs/<run-id>/driver-attest.token` by absolute path or cd to the main checkout" | Deleting it removes no real protection; the worker label already stops the honest actor |
| F-3 | The new refusal's input does not exist today | `run_lock` writes only `pid=` and `started=`; `state.json` has no machine field, and its `host` means the agent program | Makes Order 01 a separate, refusal-free plan rather than a paragraph in the deletion |
| F-4 | No predicate answers a plan-keyed liveness question | `peer_drivers` reports lock holders without reference to a plan; `peer_held_prerequisites` walks peer queues only for unsatisfied `executed:` edges of a queued item | The predicate is genuinely new work; Order 01 builds it on `peer_drivers` rather than a second discovery |
| F-5 | `begin` has no core-level gate at all | `ipd_lifecycle.begin` performs actor, plan, lint, base-head, freeze and baseline checks and no role or location check; only `run_begin` calls `_refuse_worker_role_verb` | Order 02 gives `begin` its FIRST core gate; D4's table understates this as "CLI handler only" |
| F-6 | The run-id transport exists and already reaches the worker | Both hosts set `child_env[_gch.RUN_ID_ENV] = str(state["run_id"])` for isolated and non-isolated turns | Simplifies Order 02 and creates the Set's sharpest hazard; an env default would grant the worker the exception D2 denies it |
| F-7 | The token's surface is eleven sites across five modules | `ipd_lifecycle` (6 symbols, 2 gate blocks, 2 parameters), `runner_shared` (mint, cache, lazily-minting getter, teardown unlink, 3 threading functions), both hosts (scrub, parameter) | Order 02 carries a dedicated deletion item; a two-site removal would leave dead parameters threaded through five functions |
| F-8 | The token is in NO spec, but the REFUSAL is in two | D8 searched every `.spec.md`; `7ckptx` R4.5 and A11 and `llbr2b` 3.2 and C-8 describe the refusal | Exactly four passages are amended, by one child; the deletion itself needs no amendment |
| F-9 | The runner already finalizes inside its lane | `finalize_repo` is the lane work directory when a worktree handle exists, with the receipt synced in first | Order 03's nudge recommends the shape the tooling already prefers; only hand-run transitions lack it |
| F-10 | Finalize's stdout carries a parsed payload and a refusal contract | `parse_finalize_payload` reads finalize's stdout; `nested_aw_message` keeps both streams and strips the `checkout_pin` advisory prefix | Order 03 emits on stderr and is silent under `--agent` and `--json` |
| F-11 | The nudge's question differs from the holder predicate's exactly where it matters | The predicate reports NOT HELD when no live run holds the plan, which is true of a lane whose run ended | Order 03 must not reuse the predicate, or the advisory would be silent in its main case |
| F-12 | `ROLLUP_SHARED_GATES` is a drift detector that must be updated with the gates | Its own comment records that an earlier short list "would have PASSED while the rollup silently ran with no exclusive lock, no transaction journal and no crash recovery" | Order 02 must update the tuple; a stale one would assert a gate set that no longer exists |

## Proposed changes (ordered, validatable)

1. Confirm `urv602` reached `executed`: the machine is recorded in the driver lock record and the three-valued plan-keyed holder predicate exists, implementing D2 and D3 with no refusal changed (E-01).
2. Confirm `e25iy9` reached `executed`: the token and the location guess are gone, both checks sit inside all three core transitions in the right order, `--take-over` records its reason, and both specs plus the CHANGELOG are corrected (E-02).
3. Confirm `m47znv` reached `executed`: the advisory nudge fires in main when a lane exists, on stderr, suppressed in machine-readable modes, changing no exit code (E-03).

## Deferred / out of scope (with reason)

- THE WORKER-LABEL CHECK'S SEMANTICS (`AW_EXECUTION_ROLE`, `worker_role_active`, `AW-LIFECYCLE-ROLE-001` and its message). D1 keeps them verbatim: it is the one honest mistake actually observed, and D2 requires it to run first. Order 02 relocates WHERE it is checked and changes nothing about what it means or says.
  - Carrier-Declined: Nothing is owed because the check is already in the state P15 wants. It is an environment selector producing a clear message about whose step it is, which is P15's prescribed shape, and its honest limit is already stated in its own comment.
- THE OPT-IN OS SANDBOX (`host_sandbox_profile`, executed plan `1o4eif`). D7 keeps it exactly as shipped: opt-in, off by default, Linux only, selected by explicit request. It is REFRAMED, not rebuilt: it is optional isolation an operator may choose, not the real fix for a malicious agent, and nothing in this Set may depend on it being on. Order 02 removes only the comment that frames it as that fix beside the code it deletes.
  - Carrier-Declined: Nothing is owed because D7 rules the mechanism is kept and only its framing was wrong. The framing beside the deleted token is corrected in Order 02, and every other such comment is already filed under `dmjp0u`.
- EVERY OTHER ANTI-MALICE MECHANISM IN THE TREE. D5 rules explicitly that this design does not sweep them: `wtiso_gate.py`'s raising stubs, the `8zgybk` and `x03wgn` adversarial scaffolding, and the remaining "determined same-user agent" justifications are audited separately under backlog `ariaau`, now graduated into the `malgate` Set, which has already fenced this Set's region out of its own scope.
  - Carrier: ariaau
- THE REMAINING HOSTILE-AGENT JUSTIFICATION COMMENTS ELSEWHERE IN THE PACKAGE (`ipd_lifecycle`'s module header, `orchestrate_isolation`'s docstring). Measured and owned by a sibling plan in the `malgate` Set, which excludes the region Order 02 deletes, so the two do not collide.
  - Carrier: dmjp0u
  - Carrier-Evidence: .aw/records/plans/executed/20260930-malgate-03-dmjp0u-reframe-every-determined-same-user-and-malicious-agent-justi.ipd.md
- MAKING THE NEW CHECK A HARD BOUNDARY. Out of scope by construction rather than preference: P15 says "If real isolation is ever required, it comes from the operating system (a separate user, a sandbox such as the opt-in hardened profile), never from checks in our own code." The backlog item's own honest-limits section states the same: this is guidance for honest actors and is not meant to be a security boundary.
  - Carrier-Declined: Nothing is owed because filing it would assert the repository intends to build a mechanism its own guiding principle forbids, which is the exact machinery this Set is deleting.
- A DURABLE MACHINE FIELD IN `state.json`, IN ADDITION TO `driver.lock`. D3 scopes the fix to the lock record, where the machine sits beside the pid it qualifies and is written under the lock that proves the writer is the holder. A second copy with no reader is the duplication GUIDING_PRINCIPLES P6 forbids.
  - Carrier-Declined: Nothing is owed because there is no latent work: the design's one reader is satisfied by the lock record, and filing an item would assert a second home for a fact already stored once.
- MAKING THE OS FILE LOCK WORK ACROSS NETWORK FILESYSTEMS. D3 records the honest limit that on a shared drive the lock may or may not work across machines depending on the filesystem. The Set does not attempt it and does not need to: the recorded machine converts that case into an explicit undeterminable verdict, which refuses with a recorded override available.
  - Carrier-Declined: Nothing is owed because this is a property of NFS, SMB and cluster filesystems rather than of this repository, and no code here could establish it. The design is safe without it by failing closed, stated as a limit rather than hidden.
- ENFORCING THE LANE PREFERENCE IN ANY WAY. D1 is explicit that the preference is "never enforced" and that the nudge is "NUDGE, never a refusal". A refusal keyed on a lane's mere existence would be the location rule this Set deletes, keyed on a stale artifact rather than on anyone actually working.
  - Carrier-Declined: Nothing is owed because the maintainer decided this in D1. Filing an item would assert the repository intends to make the preference enforceable, which is the opposite of the decision.

## Scope check

- Over-scope: none. This file declares ONLY itself, which is the correct declaration for a plan that performs no product change: it holds three child-confirmation rows and a child table, and contributes no code, test, record or spec edit. Every deliverable is owned by a child, so the orchestrator-coverage gate should find no work here that no child covers.
- Under-scope: no code path, test path or spec path is declared here, deliberately. `agent_workflows/runner_shared.py` and the new holder-predicate test belong to `urv602`; `agent_workflows/ipd_lifecycle.py`, `oc_runipd.py`, `agy_runipd.py`, `cli.py`, `status_set.py`, both specs, the replaced gate test and `CHANGELOG.md` belong to `e25iy9`; the nudge test belongs to `m47znv`. Note that `ipd_lifecycle.py` and `runner_shared.py` are each declared by more than one child, which is correct and not a collision: the children execute serially by their declared dependencies, each in its own isolated worktree, and each declares its own fence so the finalize scope reconciliation measures the right file set per item rather than one union that would hide which child changed what.

## Required tests / validation

- THIS PLAN RUNS NO TEST OF ITS OWN, because it performs no product change. Stated explicitly so the runner's retirement of this plan is not read as an untested transition: retirement is gated on every child reaching `executed`, and each child's own pre-transition checkpoint is where its evidence lives.
- E-01 is satisfied by `urv602` on disk in `.aw/records/plans/executed/` with `- Status: executed`, its predicate demonstrated across all three verdicts including the queued-not-started held case, and its full-suite summary pasted.
- E-02 is satisfied by `e25iy9` on disk in `.aw/records/plans/executed/` with `- Status: executed`, its D4 entry-point matrix demonstrated row by row, both measured regression cases passing, its `AW_RUN_ID` fence mutation-tested, its spec amendments reconciled against its declared `- Scope-Paths:`, and its full-suite summary pasted.
- E-03 is satisfied by `m47znv` on disk in `.aw/records/plans/executed/` with `- Status: executed`, its advisory shown on stderr with byte-identical structured payloads and identical exit codes in every arm, and its ended-run case shown still nudging.
- THE SET-LEVEL CROSS-CHECKS a reviewer should apply, since no child can apply them alone, are the four in Cross-IPD validation above. The most important is the NET REFUSAL SURFACE: one refusal deleted, one added, one relocated unchanged, one advisory added. A Set that ends with more ways to refuse than it started with has failed regardless of every child passing, because the defect being fixed is a false refusal.

## Spec / documentation sync

- EXACTLY TWO SPECS ARE AMENDED IN THIS SET, and not by this file. `e25iy9` declares both in its own `- Scope-Paths:`. In `7ckptx` (worker lane containment, `approved`), R4.5 and A11 are restated so the refusal is worker-label-plus-live-holder rather than location, while R4.5's honest-limit sentence ("an environment selector and not a hardened boundary") is KEPT VERBATIM because D8 measured that it already matches P15. In `llbr2b` (lifecycle automation policy, `to-review`), 3.2's note that a worker-role process "is refused outright at the CLI wrapper" is corrected because the check moves into the core functions, and invariant C-8 gains the held-by-a-live-run refusal as a second lifecycle invariant. D8's condition for an in-place update is that `llbr2b` is still `to-review`, which held at authoring and Order 02 re-checks.
- THE PER-RUN TOKEN AND THE LOCATION GUESS ARE IN NO SPEC, which is a measured claim rather than an assumption. D8 searched every `.spec.md` for the token (`AW_DRIVER_ATTEST`, `driver-attest`, "driver attestation"), the location guess (`lane_worktree_active`), the refusal code (`AW-LIFECYCLE-ROLE-001`), the role vocabulary and lifecycle ownership. D8 also records that the earlier assumption that `c4gd2h` must be amended was WRONG: that spec holds stop-protocol rules, and its R2 on `driver.lock` release is consistent with D2.
- FOUR SPECS ARE RE-READ AND EXPECTED TO NEED NOTHING, each named so a child checks rather than assumes: `77tr3o` (orchestrator retirement, `approved`), which mentions the `aw set executed` worker-role bypass as outside its scope and MAY receive a one-line history note from Order 02 pointing at the closure; `25kzda` (run-and-verify, `approved`), whose begin-receipt rules are untouched; `c4gd2h` (runner lifecycle, `implementing`), consistent as above and re-confirmed by Order 01 for the lock-record change; and `pqsx96` and `i4gpto` (both `draft`), which mention begin receipts only.
- A CONCURRENT SET ALSO DECLARES `7ckptx`, and Order 02 carries the instruction. Pending plans `e9ekuj` and `uuh71v` (Set `specfin7ck`) declare the same spec file and `uuh71v` intends to advance it toward `implemented`. The passages differ (R6.1's porcelain fork and A12b's coverage sentence versus R4.5 and A11), so the edits are compatible, but the spec may no longer be in `approved/` by execution time; Order 02 is instructed to re-resolve the path by `<id6>` rather than assuming the directory.
- ONE CHANGELOG ENTRY, written by `e25iy9`, and it must CORRECT the existing one rather than merely supplement it: the shipped entry claims the token closed "an authority bypass", which F-2 shows the gate's own comment concedes it did not. Order 03 deliberately adds no entry, so the Set's user-visible change is described once; if the nudge is worth mentioning, the correct home is a clause in Order 02's entry.
- `GUIDING_PRINCIPLES.md` IS NOT EDITED BY ANY CHILD. P15 already exists, was added on 2026-09-26 in commit `40868bb1`, and already cites this design as its measured example. The Set APPLIES the principle; amending it here would be circular. Stated because "update the principle" is a plausible misreading of a Set whose subject is that principle.
- NO `docs/` FILE DESCRIBES THE TOKEN, THE LOCATION GUESS, OR THE LIFECYCLE VERBS' ADVISORY OUTPUT, measured by search at authoring: the only mention outside code and tests is the CHANGELOG entry Order 02 corrects. Each child re-confirms by search rather than assumption, since a missed mention would leave the repository documenting a deleted mechanism.

## Open questions

### OQ-01: Should Order 03 (the nudge) be executed at all, or dropped as unnecessary polish?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: The Set keeps it, and the case rests on what the location rule was actually protecting. Its refusal was wrong, but the preference behind it is real: when the transition happens in the lane, the plan's move to `executed/` travels with the code it records and both reach main in one reviewed merge, which is why the runner already does exactly that for its own turns (F-9). Delete the rule with no replacement signal and a human finalizing in main separates the record from the work silently. Against keeping it: it is one printed line, it refuses nothing, so its absence costs no correctness, and every line of advisory output is a small maintenance surface and a small risk that a future author "strengthens" it back into the location rule. NOT BLOCKING because the Set's correctness does not depend on it: Orders 01 and 02 close both measured defects on their own, and Order 03 is last in the queue precisely so dropping it costs nothing already built.
- Carrier-Declined: No carrier is owed under either answer. Keeping it is realized by `m47znv` as authored; dropping it leaves no latent work, because a nudge that was never required by any contract and refuses nothing has no obligation left behind when it is not built.

### OQ-02: Should the Set wait for the `malgate` Set, which also applies P15 to shipped gates?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: No, and the two are already deconflicted in writing rather than by luck. `malgate`'s orchestrator and all three of its children EXPLICITLY exclude "the driver attestation token and the `lane_worktree_active` location guess (designed in backlog `dvonrn`)" from every child without exception, and its own deferred section names `dvonrn` as the carrier. The file overlap is narrow and non-colliding: `malgate`'s `dmjp0u` edits `ipd_lifecycle.py` comment text and fences out the region this Set deletes. Ordering considerations point the other way if anything: this Set carries `Blocks-Release: next` on a `bug`, while `malgate` is a `chore`, so making a release-blocking fix wait on a cleanup sweep would invert the priority. NOT BLOCKING because both Sets read each other's fences and neither declares a dependency on the other, so either order works; the one real consequence is that whichever runs second sees a slightly smaller comment surface than its plan describes, which its own E-01 re-measurement catches.
- Carrier-Declined: No carrier is owed. Both orderings are fully realizable with the plans as written, no deliverable goes unbuilt either way, and the deconfliction is already recorded in both Sets' scope fences rather than needing a new artifact.

## Coverage findings

- "Four checks span the children and cannot be performed by any child alone, which is why they live here."
- "- THE REFUSAL SURFACE SHRANK AND DID NOT MOVE. Read Orders 01, 02 and 03 together and confirm the Set's"
- "- THE ENVIRONMENT FENCE HELD ACROSS THE SET. `AW_RUN_ID` reaches the worker for commit trailers and the"
- "- THE TWO QUESTIONS STAYED DISTINCT. Order 01's predicate answers"
- "- EXACTLY ONE CHILD AMENDED A SPEC. Only `e25iy9` may touch a `.spec.md` (`7ckptx` and `llbr2b`). Confirm"
- "- THE SET-LEVEL CROSS-CHECKS a reviewer should apply, since no child can apply them alone, are the four in Cross-IPD validation above."
- "2. THE TWO MEASURED DEFECTS ARE CLOSED AND PINNED AS TEST CASES, not asserted in prose. A human's own"
- "3. NOTHING KEYS ON LOCATION ANY MORE. `lane_worktree_active` does not exist, neither remaining gate tests"
- "4. NO SECRET REMAINS. `AW_DRIVER_ATTEST`, the token file, its minting, its verification, its caching and"
- "6. THE WORKER-LABEL CHECK STILL WORKS AND STILL RUNS FIRST, including the environment fence: a"

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `urv602`'s path shown inside `.aw/records/plans/executed/` and its `- Status: executed` line pasted. Its `V-01` through `V-06` shown carrying concrete pasted evidence rather than placeholders, including the driver lock record read back with all three fields, all three predicate verdicts driven, the queued-not-started held case, and its bare `python3 -m pytest` summary. Plus the check that NO refusal changed in that child: its diff touches no gate block and no verb's accept or refuse behavior.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `e25iy9`'s path shown inside `.aw/records/plans/executed/` and its `- Status: executed` line pasted, with every `V-*` carrying pasted evidence. Specifically: the D4 entry-point matrix enumerated row by row; BOTH measured regression cases passing (a human worktree under `.aw/worktrees/` with no live run, and a dead runner's lane); the `AW_RUN_ID` fence mutation-tested; the search output proving the six deleted symbols are gone; the `ROLLUP_SHARED_GATES` diff with the drift test passing; both spec diffs with `7ckptx` R4.5's honest-limit sentence unchanged; and the CHANGELOG entry checked for em and en dashes.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `m47znv`'s path shown inside `.aw/records/plans/executed/` and its `- Status: executed` line pasted, with every `V-*` carrying pasted evidence. Specifically: the advisory line as a human sees it for both verbs; the exit code shown identical to the no-lane case in every arm; the `--agent` and `--json` payloads shown byte-identical to the no-lane case; and the ENDED-RUN case shown still nudging, which is what proves it did not wire itself to Order 01's predicate. Plus THE FOUR CROSS-IPD CHECKS, performed here and nowhere else, each from the COMBINED diff of all three children: the net refusal surface (one deleted, one added, one relocated unchanged, one advisory added); no site reads a run id from the environment for authority; the two questions stayed distinct; and exactly one child amended a spec, with no other `.spec.md` modified.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT FOR THIS FILE. This plan makes no product change. It is retired when every child reads `executed` on disk, and the runner retires it automatically once that holds, spending no agent turn. An agent executing the Set by hand should run the children in Order (01, 02, 03) and then confirm the three rows above plus the four cross-IPD checks. Commit only declared paths through `aw commit`, never `git add -A`, and never push.

THE SET'S ONE INVARIANT, worth stating where a reviewer of any child will see it: the Set must end with FEWER ways to refuse than it started with. One refusal is deleted (location plus token), one is added (a live run holds this plan, including the undeterminable case), one is relocated but otherwise unchanged (the worker label), and one advisory that refuses nothing is added. The defect being fixed is a FALSE REFUSAL, so a Set that ends up refusing in more situations has failed even if every child's tests pass.

THE TWO THINGS MOST LIKELY TO GO WRONG, both owned by Order 02 and both mutation-tested there. First, the check order: the worker label must run FIRST in all three functions, or the runner's own agent gets a message about a live holder instead of the message written for it, which is worse than today's behavior for the one honest mistake actually observed. Second, the environment fence: `AW_RUN_ID` already reaches the worker for commit trailers, so an exception that defaults from the environment hands the lane agent the bypass D2 denies it, silently, with every other test still green.

DO NOT WIDEN THIS SET INTO A GATE SWEEP. D5 hands every other anti-malice mechanism to backlog `ariaau`, whose `malgate` Set is already pending and has already fenced this Set's region out of its own scope.

POST-GATE LIFECYCLE MOVE. Do NOT perform a hand-rolled terminal move for this plan or any child. In a managed lane the runner performs `aw ipd begin` and `aw ipd finalize` and retires this orchestrator itself; in an unmanaged or manual run each child is finalized with `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` after `aw ipd lint --phase pre-transition` reports conforming and every `V-*` carries concrete pasted evidence. Never `git mv` a plan and never hand-edit `- Status:`.
