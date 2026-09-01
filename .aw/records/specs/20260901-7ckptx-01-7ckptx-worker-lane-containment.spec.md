# Spec: Worker lane containment: one authoritative signal per instruction

- Date: 2026-09-01
- Status: to-review
- Id: 7ckptx
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- From-Backlog: vqv9im
- Blocks-Release: next
- Work-Kind: feature
- Scope: What an isolated (lane) turn may be told and may reach: signal purity in the prompt, layered enforcement beyond prose, bounded missing-input repair, and the retention rules that decide when a lane may be destroyed.

## Workflow history

- 2026-09-01 to-review (aw specs): Authored in response to /aw plan-review PR-005, which correctly refused plan tch3bo for having no normative basis: research x03wgn and backlog vqv9im are evidence of what was measured and decided, not a specification requirements can trace to. 30 requirements, 20 acceptance criteria, full bijection (every requirement cited by at least one criterion). Also answers PR-003 (R2.3 idempotent collection, because requeue_interrupted proves retry is a live path), PR-004 (R3.2-R3.5 carry all five research steps, not just classify-and-copy), PR-009 (R4.3 forbids blindly discarding an operator-supplied config value), and PR-010 (R5.2 requires link-independence, since a hard link passes a symlink check and a digest comparison). Section 5 records three research recommendations DECLINED with evidence, including the noise-gated watchdog: measured over 920 real stream lines with zero noise events, so it is inert on this host, while the measured live risk here is spurious kills, which gating makes more likely. That reverses my own earlier assessment and is recorded rather than quietly dropped.
## 0. Concepts (kept distinct)

These four are routinely conflated, and every requirement below depends on keeping them apart.

- **SIGNAL PURITY**: the property that the instructions handed to a worker contain no statement that contradicts another. It is a property of the EMITTED TEXT, checkable mechanically, and it is independent of whether the worker obeys.
- **CONTAINMENT**: the property that a worker's reads and writes stay inside its lane. This is a property of BEHAVIOR, and it can only ever be made LIKELY by instructions; making it certain requires a boundary the worker cannot cross.
- **ENFORCEMENT**: a mechanism that produces a refusal without the worker's cooperation. An environment selector that a driver-owned verb checks is enforcement; a sentence in a prompt is not.
- **RETENTION**: whether a lane's contents may be destroyed. Distinct from containment: a perfectly contained lane may still hold unclassifiable content that must be preserved.

## 0.1 Actors

- **DRIVER (coordinator)**: `aw oc run` / `aw agy run`. Owns the run directory, the lane lifecycle, every lifecycle transition, and every decision about paths outside a lane. Trusted.
- **WORKER**: the agent process launched for one turn, with cwd inside its lane. NOT trusted to be correct, but ASSUMED to be cooperative: it acts on trained reflex, not malice (see 0.2).
- **HOST**: the agent runtime (opencode, antigravity). Its permission behavior is a third-party variable, not a repository invariant.

## 0.2 Threat model (DECIDED; this is the maintainer's ruling and it shapes every requirement)

The model is ACCIDENT PREVENTION, not adversarial defense.

Agents are strongly trained to operate solo in repositories they own, where `git add -A` and editing any
file are correct. This repository asks for something not in their nature, so the realistic failure is a
trained reflex applied in the wrong context, not a deliberate evasion. Two consequences that would be
wrong under a security model and are RIGHT under this one:

1. A guard that refuses and names the correct alternative is VALUABLE even though a determined process
   could bypass it. Bypassability is a feature against accidents.
2. Therefore a mechanism may be shipped as an honestly-labelled accident guard, provided the artifact
   states plainly that it is not a boundary. Overstating it is the failure, not shipping it.

This ruling was applied by the maintainer to `mjx7ne` OQ-03 on 2026-09-01 and is restated here because
every requirement below inherits it.

## 0.3 Constraints and dependencies

- The two host drivers (`oc_runipd.py`, `agy_runipd.py`) are deliberate near-parity twins. A containment
  rule that lands in one and not the other is a DEFECT, not a partial delivery.
- There is exactly ONE process reaper (`runner_shutdown`), and spec `c4gd2h` R5 forbids a second. Any
  bound defined here must terminate through it.
- Prose cannot be the boundary, by this repository's own admission: `host_sandbox_profile`'s docstring
  records that a same-user agent with shell access "cannot be cryptographically or filesystem-enforced
  from prompts, hooks, environment variables, or Python role checks alone".
- OS-level confinement is OUT OF SCOPE here and is owned elsewhere (`fjs11i` for the unreachable
  hardened profile, research `q65sz3` for the cross-platform question). This spec must remain true
  whether or not that lands.
- `wtiso_gate.py` is the designated home for shared containment predicates. It exists as a fail-loud
  skeleton by design: a stub raises `NotImplementedError` naming its owning phase so a premature caller
  breaks visibly rather than silently allowing.

## 1. Goals

1. An isolated turn's instructions are SELF-CONSISTENT: no sentence in them authorizes what another
   forbids.
2. Containment does not depend solely on the worker reading prose correctly: at least one layer produces
   a refusal without worker cooperation.
3. A worker that genuinely needs a file it does not have has a BOUNDED, deterministic route to get it
   that never grants access to the original checkout.
4. A lane is never destroyed while it holds content the driver cannot classify.
5. Every guarantee in this spec is stated with its honest limit, so no artifact can claim a boundary
   where only a guard exists.

## 2. Non-goals

1. Making containment unbypassable. Explicitly out of scope (0.2, 0.3).
2. OS sandboxing, Landlock, per-run user accounts, or separate principals.
3. Relocating machine state out of the repository (`wtiso` Phase 4).
4. Unifying the two host runners (`rununify`).
5. Commit-scope enforcement at the git layer (`wjl471`). This spec's requirements stop at what the
   driver hands the worker and what the driver refuses; a hook cannot see INTENT and needs its own
   design.
6. Changing the lifecycle transaction, the integration gate, or the `runstop` stop levels.

## 3. Requirements

Each requirement is numbered so a plan item can cite it. "MUST" is normative; a plan that cannot satisfy
a MUST is not conforming and must say so rather than reinterpret it.

### R1. Signal purity in the emitted prompt

R1.1 For an isolated turn, the emitted prompt MUST contain ZERO absolute filesystem paths outside the
lane root. This is a property of the text and MUST be verified by pattern-matching the emitted string,
not by inspecting the code that builds it and not by a wording assertion.

R1.2 The prompt MUST NOT contain any clause authorizing an exception to R1.1. A statement of the form
"paths outside the lane are driver-owned control paths, write them exactly as given" is itself a
violation, because it re-introduces the contradiction R1.1 removes.

MEASURED BASIS (2026-09-01, HEAD `cea13ac0`, on the shipped driver): the isolated prompt emits FIVE
absolute out-of-lane paths (the plan file, the run directory, the decisions register, the execution
report, the outcome JSON) and then declares them "the only exceptions ... you write them exactly as
given" nine lines after saying "Do NOT read or write the main checkout". In the live prompt from run
`run-20260901T042331Z-118022` the main-checkout path appears 7 times, only 2 of them inside the lane.

R1.3 A NON-isolated turn's prompt MUST be unchanged by any work satisfying R1.1/R1.2. Non-isolated
execution is a supported mode, not a degraded one.

R1.4 The worker MUST be told, in plain language, that its cwd is the complete authorized workspace, and
MUST be given the ONE deterministic form for reporting a genuinely missing input (R3.1). R1.1 without
R1.4 is a strictness increase with no escape hatch, which converts a recoverable situation into a
failure.

### R2. Closed loop: what the worker writes, the driver reads

R2.1 Where the prompt names a lane-relative submission path, the driver MUST collect that submission
back to the location its own readers already use, BEFORE the disposition for the turn is computed.

RATIONALE, and this is the single most important sequencing rule in this spec: a lane-relative
instruction whose output nobody collects is WORSE than the contradiction it replaces, because it fails
INVISIBLY. The worker writes its outcome inside the lane, the driver's reconciliation reads the run
directory, finds nothing, and scores the turn from the empty-outcome fallback. That fallback disposition
then falls outside the set that gates verification and self-finalize, so a fully successful turn silently
never finalizes. R1 and R2 MUST therefore ship together; a plan that delivers R1 alone is
non-conforming.

R2.2 Collection MUST be a copy, not a move: the lane retains its own evidence for the retention
classification in R5.

R2.3 Collection MUST be IDEMPOTENT with respect to retries. The run-wide decisions register is APPENDED
to and is shared by every item in the run, so a re-attempted turn MUST NOT duplicate its contribution
and MUST NOT remove a sibling lane's. Retry is a real path, not hypothetical: the driver already
re-queues interrupted items for recovery.

R2.4 A turn that produced no submission MUST reconcile to the honest empty-outcome fallback without
error. Absence is a legitimate observation.

### R3. Bounded missing-input repair

R3.1 The contract MUST be a single deterministic token form carrying the repo-relative path and the
reason it is required. The worker emits it and continues with independent work; it does not wait.

R3.2 On receiving it, the driver MUST preserve and pause the lane rather than opening an interactive
permission prompt.

R3.3 The requested path MUST be resolved in coordinator code only, and MUST be REJECTED if it is
absolute, escapes the checkout, names a coordinator-owned surface, names a sibling lane or the worktrees
root, names machine-local state, names the git administration directory, is a directory rather than a
file, or does not exist. The reject set MUST be the SHARED worker-forbidden predicate, not a second copy
of the rules, so the two cannot drift.

R3.4 If policy permits, the driver MUST materialize a digest-verified copy into the lane, record a new
manifest revision, record the corresponding authorization, and resume the same session or a new attempt
with the change stated explicitly. A classification-and-copy that omits the manifest revision and the
authorization record is NOT a conforming repair cycle: without them the lane's input set silently
diverges from its sealed manifest.

R3.5 If policy does not permit it, the driver MUST block with a precise missing-input record naming the
path and the reason for refusal.

R3.6 No path in this cycle may grant access to the live original checkout. This MUST be structural (the
decision type cannot represent a live grant), not a convention.

R3.7 A denied host permission event pointing into the original checkout MUST route through this same
classification path, so there is one rule rather than two.

### R4. Layered enforcement, each with its honest limit

R4.1 An unattended isolated turn MUST run under a host permission policy that denies external-directory
and interactive-question requests, supplied by the runner in the child environment and never by editing
repository configuration.

R4.2 The driver MUST OBSERVE the effective policy rather than assume its request won, and MUST record
either the observed values or an explicit unverified marker with its reason. Host configuration
precedence can place a managed source above the runner's, so a run that only SETS the policy can believe
it is protected when it is not.

R4.3 Constructing the child environment MUST NOT silently discard an operator-supplied value for the
same variable. The policy MUST either be merged with validation or override explicitly and loudly; a
blind overwrite is non-conforming.

R4.4 The driver MUST bound an unattended turn independently of the host's permission decision: a
seconds-scale deadline armed by an observed permission request (including a nested child-session
request), and an absolute per-turn deadline that output cannot extend. Expiry MUST terminate through the
ONE shared reaper and record a safe-failure disposition naming which bound fired.

R4.5 An isolated turn's child environment MUST carry the execution-role selector that causes
driver-owned lifecycle verbs to refuse inside a lane. Any artifact describing it MUST state that it is
an environment selector and not a hardened boundary.

R4.6 R4.1 MUST NOT be delivered before R1.1. Denying access to paths the prompt still names would
convert a currently-working run into a hard failure. MEASURED: on opencode 1.18.25 with `--auto` and no
user-level permission block, the host currently PERMITS the out-of-lane writes (run
`run-20260901T042331Z-118022` recorded zero permission events and both workers wrote all five paths), so
this ordering is load-bearing rather than theoretical.

### R5. Lane inputs and retention

R5.1 Required inputs MUST be materialized into the lane BY COPY, with a sealed manifest recording per
entry the repo-relative path, its class, a source digest, and the materialization mode.

R5.2 No manifest-listed lane path may be a symlink OR a hard link to a file outside the lane. Both are
violations: a hard link satisfies a symlink check and a digest comparison while still sharing an inode
with the original, which reintroduces exactly the coupling the lane exists to remove. Verification MUST
therefore establish link independence, not merely symlink absence.

R5.3 Every `--file` style attachment handed to an isolated worker MUST resolve inside the lane.

R5.4 Before an unattended isolated turn, the target checkout MUST have no dirty TRACKED paths, and a
refusal MUST name them and occur BEFORE any worker process is spawned. Untracked files are deliberately
EXCLUDED: a lane is created from a commit, so untracked content was never silently omitted the way an
uncommitted tracked edit is, and refusing on untracked files would make an unattended run unstartable in
any working checkout.

R5.5 Teardown MUST be refused while a lane holds content the driver cannot classify: a dirty tracked
file, an unknown untracked OR IGNORED file, or an unimported submission. The enumeration MUST include
ignored files; "ignored means disposable" is the specific reasoning that previously destroyed lane
content silently.

R5.6 A refusal under R5.5 MUST be recorded as an event naming the reason, so preservation is auditable
rather than inferred from a surviving directory.

### R6. Shared predicates, single definition

R6.1 A containment rule consumed by more than one surface MUST live in one predicate that every surface
calls. Forking the rule is non-conforming even when the copies agree at the time of writing.

R6.2 A predicate that is declared but not yet implemented MUST fail loudly rather than return a
permissive default, and MUST name its owner.

R6.3 Implementing a predicate body and wiring its callers are SEPARABLE deliverables and may be owned by
different plans. A plan that implements a body it is not chartered to wire MUST NOT wire it.

## 4. Testable acceptance criteria

Each is falsifiable and names the requirement it proves. "A test exists" is not evidence; the pasted
result of running it is.

- A1. Build an isolated prompt from BOTH drivers and pattern-match the emitted text: zero absolute paths
  outside the lane root, and no exception clause. Reword the exception and the check must still fail.
  (R1.1, R1.2)
- A2. Build a NON-isolated prompt before and after the change for identical inputs and compare digests:
  identical. (R1.3)
- A3. A worker writes a lane-relative outcome declaring success; the driver's reconciliation returns that
  disposition, not the empty-outcome fallback, and the submission is present at the driver-side path.
  (R2.1)
- A4. Run the same attempt's collection twice; the run-wide decisions register contains the lane's
  contribution exactly once, and a sibling lane's contribution is still present. (R2.3)
- A5. A turn that wrote nothing reconciles to the empty-outcome fallback without raising. (R2.4)
- A6. Drive the missing-input cycle with a SAFE repo-relative file: a digest-verified lane copy appears, a
  new manifest revision is recorded, an authorization record is written, the lane was paused and then
  resumed, and no live grant was emitted. (R3.2, R3.4, R3.6)
- A7. Drive it with each forbidden shape (absolute, `..` escape, coordinator surface, sibling lane,
  machine state, git dir, directory, nonexistent): each is rejected with a precise record, no copy, no
  grant. Show the reject decision comes from the SHARED predicate. (R3.3, R3.5, R3.6)
- A8. Decode the child environment for an unattended isolated turn: the policy denies external-directory
  and question, inherited PATH and the import pin survive, and the attempt record carries either the
  OBSERVED effective policy or an explicit unverified marker with its reason and the host version.
  (R4.1, R4.2)
- A9. With an operator-supplied value already set for the policy variable, the resulting child environment
  either merges it verifiably or overrides it with an explicit loud record. A silent overwrite fails this
  criterion. (R4.3)
- A10. Feed a synthetic unanswered permission request, including the nested child-session shape: the
  process is terminated within the permission deadline, demonstrably not at the coarse no-progress bound,
  the disposition is the safe-failure value, the reason names which bound fired, and the termination is
  attributable to the shared reaper with no second reaper introduced (checked structurally, not by text
  grep, since a test file contains the symbols). (R4.4)
- A11. An in-lane invocation of a driver-owned lifecycle verb refuses with the documented code and
  performs NO state transition; the driver's own invocation still succeeds. (R4.5)
- A12. Materialize a lane: every manifest entry records a copy with a source digest; no listed path is a
  symlink; and each listed file's inode link count and identity establish it is NOT a hard link to a file
  outside the lane. (R5.1, R5.2)
- A13. Every attachment handed to an isolated worker resolves inside the lane, asserted over ALL
  attachments with at least two checked. (R5.3)
- A14. With a dirty TRACKED file, an unattended isolated run is refused before any worker process is
  spawned, naming the dirty paths; with a clean tree it proceeds; an UNTRACKED file does NOT trigger the
  refusal. (R5.4)
- A15. A lane holding an unknown untracked file is not torn down and an event records the reason; the same
  for an unknown IGNORED file; a fully classified clean lane is torn down. (R5.5, R5.6)
- A16. Each implemented shared predicate has unit tests; each unimplemented one still raises naming its
  owner; and a predicate implemented but not chartered for wiring has no product caller. (R6.1, R6.2,
  R6.3)
- A17. The isolated prompt states the cwd-is-the-workspace rule in plain language AND names the exact
  missing-input token form, so R1.1's strictness always ships with its escape hatch. Assert both are
  present in the emitted text. (R1.4, R3.1)
- A18. After collection, the lane STILL holds its own copy of each submission, proving collection copied
  rather than moved and that the retention classification in R5.5 has evidence to inspect. (R2.2)
- A19. A denied host permission event pointing into the original checkout produces the SAME decision
  record as the equivalent missing-input token for that path, proving one classification path rather than
  two. (R3.7)
- A20. Ordering is verifiable, not merely asserted: demonstrate that with the policy denial active and
  the prompt still naming out-of-lane paths the turn FAILS, and that with R1.1 satisfied it does not. A
  plan may satisfy this by citing the sequencing constraint and showing the two states, but it MUST NOT
  claim R4.6 holds without evidence that the ordering was actually respected. (R4.6)

## 5. Research recommendations NOT adopted, and why

Recorded so a later reader does not treat the research report as the contract. Research `x03wgn` is
EVIDENCE; this spec is the norm, and it deliberately declines three of the report's positions.

1. NOISE-GATED NO-PROGRESS WATCHDOG, DECLINED AS A BUG FIX, ACCEPTED ONLY AS A FUTURE-HOST GUARD. The
   research prescribes that the no-progress watchdog reset only on meaningful events, and the `wtiso`
   Phase-1 design implemented a predicate for it. MEASURED 2026-09-01 over 920 real stream lines from run
   `run-20260901T042331Z-118022`: ZERO unparseable lines, ZERO noise-typed events, and 100% of lines
   already in the meaningful set (`step_start`, `step_finish`, `tool_use`, `text`). So on the current host
   the gate would change nothing. Worse, the measured failure mode on this host runs the OTHER WAY: the
   subagent-progress module documents a real turn with 570 stdout events and a largest stdout silence of
   246.5s while a child session progressed, i.e. the live risk is SPURIOUS KILLS, and gating the reset
   makes the watchdog fire MORE easily. Therefore this spec does NOT require it. If it is ever
   implemented it MUST fail toward meaningful for uncatalogued event types, and it MUST be described as a
   guard against a future host that emits noise on stdout, never as a fix for a present defect.
2. RELOCATING THE DRIVER'S CONTROL PATHS INTO THE LANE, DECLINED IN FAVOUR OF COLLECT-BACK (R2). The run
   directory is RUN-WIDE and shared by every item; the decisions register is appended to by all lanes.
   Relocating it into one lane would either fork it per item or make one lane authoritative over its
   siblings. Collect-back also leaves every existing driver-side reader untouched, which is why R2.1 is
   phrased as collection rather than reader migration.
3. GATING THE SUBAGENT PROGRESS POLLER, DECLINED. The poller already filters to agent-loop progress kinds
   and counts only lines proven to belong to a child session of the current turn, which is the same
   policy applied to a different data source. Applying an event-JSON predicate to its plain-text log input
   would reject essentially every line and re-break the sub-task keepalive the poller exists to provide.
   HONEST RESIDUAL RISK: if a stuck turn's only output is agent-loop-shaped log lines from a live child,
   the poller can still hold the turn open. By the poller's own definition that child IS progressing; if
   that ever proves a real failure mode it needs its own design and a log-line-specific notion of
   progress.

## 6. Open questions

### OQ-01: Is the containment guarantee in this spec strong enough for 2.0.0, given it is explicitly not a boundary?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER'S THREAT MODEL (0.2), which is a ruling
  rather than an inference: the model is accident prevention, so a layered guard that refuses and names
  the alternative is the correct target, and bypassability is not disqualifying. The spec's obligation is
  to state the limit honestly (R4.5, Goal 5) rather than to close it. Hard confinement remains owned by
  `fjs11i` and research `q65sz3`, which this spec is deliberately independent of.

### OQ-02: Should this spec require the noise-gated watchdog that research `x03wgn` prescribes?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, resolved on measurement rather than preference; see 5.1 for the
  full evidence. The short form: 920 real stream lines contained zero noise events and zero unparseable
  lines, so the gate is inert on the current host, while the measured live risk on that same host is
  spurious kills, which gating makes more likely. Declining it is the conservative choice, and this
  reverses an earlier assessment (recorded rather than quietly dropped) that called it a live defect.

### OQ-03: Does R2.3's idempotency requirement need attempt-keyed dedup or per-lane files?

- Blocking: no
- Status: deferred
- Owner: the implementing plan
- Resolution or deferral rationale: DEFERRED AS AN IMPLEMENTATION CHOICE, not a contract question. R2.3
  fixes the REQUIREMENT (a retry must not duplicate, and must not remove a sibling's contribution) and
  A4 fixes the test. Whether that is achieved by keying the appended block to the attempt or by writing
  deterministic per-lane files is a design decision the implementing plan should make and justify, and
  either satisfies the requirement. Recorded as deferred rather than silently left open so a reviewer can
  see it was considered.
