# IPD: Add a probed supports_deny_tcp_port capability proving TCP port denial by attempt

- Date: 2026-09-29
- Kind: child
- Concern: Spec `25kzda` 5.2 requires a host descriptor that answers, from probe evidence, whether the host can deny push-capable network routes. No capability answers it today: `supports_deny_push` was removed by plan `01reg8` precisely because it was declared and never probed. The measured result (research `uq4y6q`) is that kernel TCP denial IS provable but is port-granular, so the honestly-probable claim is narrower than "deny push" and must be named for what it proves.
- Scope: Add ONE new capability to `HostSandboxCapabilities`, `supports_deny_tcp_port`, decided by an EXECUTED two-sided Landlock network probe, reported through the existing `aw host capabilities` surface, and extend `landlock_bootstrap_source` to carry network rules. The capability gates NO action and reintroduces NO finding code. It must NOT be named `supports_deny_push`, because it does not prove push denial.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, tests/test_host_sandbox_profile.py, tests/test_host_capability_extension.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:x2dwu5
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: oq05nc
- Set: denypush
- Order: 2
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: pi3bk8

## Workflow history

- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `oq05nc`. Depends on Order 01 landing the measurement and the spec amendment first.

## Goal

Give spec `25kzda` 5.2's network requirement its first PROBED answer: a capability that is True only
when the kernel actually refused a TCP connect to a denied port while permitting one to an allowed
port, on this host, in this process tree. Name it for exactly what the probe proves
(`supports_deny_tcp_port`) so nothing in the descriptor can be read as a push-denial guarantee the
mechanism cannot deliver.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the mechanism

- [ ] E-01 Extend `host_sandbox_profile.landlock_bootstrap_source` to accept an optional set of allowed TCP ports and emit a ruleset that handles `LANDLOCK_ACCESS_NET_CONNECT_TCP` alongside the filesystem rights it already handles. The generated source currently packs the ruleset attr as `struct.pack("=QQ", ALL, 0)`, whose literal `0` IS `handled_access_net`; set it to the connect-TCP bit when ports are requested and add one `LANDLOCK_RULE_NET_PORT` rule per allowed port. Guard on the reported ABI: network rules require ABI >= 4, so on a lower ABI the bootstrap must add no network rule and must NOT claim network handling. Default the parameter so every existing caller is byte-unchanged.
  - Depends on: none
  - Expected outcome: `landlock_bootstrap_source(...)` with no port argument emits source identical to today's; with ports it emits a ruleset handling connect-TCP. Existing callers and existing tests are unaffected.
  - Execution state: pending

- [ ] E-02 Add `_probe_deny_tcp_port`, a two-sided executed probe modeled on `_probe_landlock` and holding the same standard `_denial_checker_source` sets for the filesystem: it must prove a DENIAL and not a launch. The child binds a loopback listener, applies a ruleset allowing only that listener's port, then (a) connects to the allowed port and requires success, and (b) connects to a denied port and requires the kernel to refuse with `EPERM`. Exit codes must distinguish the three failure shapes the way `_denial_checker_source` does: allowed-connect-denied (jail too tight), denied-connect-succeeded (not enforced), and success. Route the subprocess through `_run_probe` so any nonzero exit, exception, or timeout maps to False, and honor `_PROBE_TIMEOUT_SECONDS` and the `CERTIFIED_PLATFORM` gate.
  - Depends on: E-01
  - Expected outcome: A probe returning `(bool, note)` that is True only on proven two-sided denial, and False with an explanatory note on every other outcome including ABI < 4 and non-Linux.
  - Execution state: pending

### Task group 2: the contract surface

- [ ] E-03 Add the capability `supports_deny_tcp_port` to `HostSandboxCapabilities` defaulting False, add the `CAP_DENY_TCP_PORT` constant, register it in `RUNNER_SAFETY_CAPABILITIES`, wire `_RUNNER_SAFETY_PROBES[CAP_DENY_TCP_PORT] = _probe_deny_tcp_port` (a real probe, NOT the `None` sentinel that marks declared-not-probed), and export the constant in `__all__`. Set the verdict and its `probe_notes` entry in `detect_host_capabilities` alongside the existing probed capabilities. Do NOT add it to `ACTION_CAPABILITY_REQUIREMENTS` and do NOT add an action class: `ACTION_CLASSES` stays `(ACTION_READ_ONLY,)`.
  - Depends on: E-02
  - Expected outcome: `aw host capabilities` reports the new row automatically (`host_cmd._capability_rows` introspects `caps.to_dict()` for bool values rather than reading a name list), with a `probe_notes` entry recording the evidence. No action is gated, so no run behavior changes.
  - Execution state: pending

- [ ] E-04 Amend `host_sandbox_profile`'s module docstring: add the new capability to the runner-safety bullet list describing how each is established, stating it is PROBED by attempt and two-sided; update the prose that currently counts the fields ("Two fields and a preflight close that"); and state the port-granularity limit explicitly in the bullet, so a reader of the contract cannot mistake it for push denial. Also state that the capability gates no action today, which is the same honest limit the docstring already records for the preflight.
  - Depends on: E-03
  - Expected outcome: The published-guarantees contract describes the new capability, what it proves, and what it does NOT prove, with the count prose corrected.
  - Execution state: pending

### Task group 3: tests, including the anti-overclaim guards

- [ ] E-05 Append `"supports_deny_tcp_port"` to `tests/test_host_sandbox_profile.py`'s `CONTRACT_FIELDS` tuple. That tuple, not dataclass introspection, drives `test_every_contract_field_exists_and_defaults_false` and `test_to_dict_snapshots_the_contract`, and its own comment warns that "a field absent from it carries NO default-False or snapshot guarantee while the suite stays green". Add a two-sided probe test: with the real probe, assert the reported verdict equals a forced re-run of the probe; and assert a raising probe yields False, mirroring `test_a_raising_probe_is_treated_as_unavailable`.
  - Depends on: E-03
  - Expected outcome: The new field carries the same default-False and snapshot coverage every other contract field has, and the probe's fail-closed behavior is pinned.
  - Execution state: pending

- [ ] E-06 Add a row for the new capability to `tests/test_host_capability_extension.py`'s `PRESENCE_VS_OBSERVATION` table, whose comment states the rule "ONE CLAIM, ONE ROW PER PROBE: no runner-safety capability may be decided by a HELPER EXISTING". The row must prove the capability is False when the MECHANISM IS PRESENT BUT ENFORCES NOTHING, which is the fail-open shape that matters here and is concretely available: `slirp4netns`, `bwrap` and `unshare` are all installed on hosts where no namespace can be created (research `uq4y6q`'s host table). Add a dedicated test asserting the capability is False on a host whose probe reports Landlock ABI < 4, so an older kernel cannot silently inherit a True.
  - Depends on: E-03
  - Expected outcome: A presence signal cannot produce a True verdict, pinned by test rather than by comment.
  - Execution state: pending

- [ ] E-07 Re-point `tests/test_host_capability_extension.py`'s `DenyPushRemovedTests` rather than deleting it, and record why in its docstring. Its purpose (`01reg8` E-02) is to stop `supports_deny_push` being reintroduced, and that purpose SURVIVES this plan intact: this plan adds a differently-named capability precisely because it cannot prove push denial. Keep every assertion that `supports_deny_push`, `CAP_DENY_PUSH`, the three action classes, and the `deny_push` output string remain absent. Only the assertion that `aw host capabilities` prints no `REFUSED  ` needs review, and it should remain true since no action is gated. Update the docstring to name both plans, so a future reader sees the guard was honored rather than worked around.
  - Depends on: E-03
  - Expected outcome: The negative guard still fails if anyone reintroduces the `deny_push` name, and its docstring records that this Set added a narrower capability instead of evading it.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or quoted content string, never by a bare line number (spec `ipd-structure-and-linting` Section 10.2; `IPD-C801`). Enforced throughout; this area has three stale citations of the same rule already (`:88-95`, `:109-115`, and the code-comment twin).
- A capability may be set True ONLY by code that executed a probe for it: `HostSandboxCapabilities`' docstring states "Every capability defaults to False: an UNPROBED host claims NOTHING (fail-closed)."
- Presence inference is FORBIDDEN IN WRITING, in the module docstring's `supports_commit_gateway` bullet ("Inferring support from the presence of the driver-side `git_commit_helper.offer_commit` helper is FORBIDDEN") and again in the `_DECLARED_UNENFORCED` rationale comment. E-06 pins it for the new capability.
- A probe passes only by proving a DENIAL, never a launch: the module docstring states "EVERY RUNG MUST PROVE A DENIAL, NOT A LAUNCH", with the reason that a misconfigured permissive jail "starts perfectly cleanly and enforces nothing". `_denial_checker_source` encodes it with distinct exit codes per failure shape.
- Probe failures are swallowed to False at three layers: `_run_probe` maps any `OSError`/`SubprocessError` (including `TimeoutExpired`) to nonzero, `_probe_linux_sandbox` catches any exception, and a non-Linux platform short-circuits. A new probe must join that discipline rather than raise.
- Runner-safety verdicts are deliberately NOT cached, unlike the sandbox ladder: `probe_runner_safety_capabilities`' own rationale is that "a stale memo here would be a way for one turn's verdict to outlive the state it was measured against." A capability registered in `_RUNNER_SAFETY_PROBES` inherits that, and also inherits the `forced_runner_safety_verdicts` test seam for free.
- `aw host capabilities` needs no change to show a new field: `host_cmd._capability_rows` introspects `caps.to_dict()` for bool values so that "a field added to the contract cannot silently vanish from the report".
- A test must exercise behavior, never pin code structure (AGENTS.md P16): no `inspect`/`ast`/regex reads of production source. Note `tests/test_host_capability_wiring.py` contains a pre-existing AST-based test; this plan adds no new test of that shape.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | Two-sided kernel TCP denial is provable | Research `uq4y6q` Finding 1: allowed connect `True`, denied connect `PermissionError(13)`, `RESULT: ENFORCED` at ABI 4 | The probe in E-02 is buildable and can meet the prove-a-denial standard. |
| F-2 | The existing bootstrap extends in place | Research `uq4y6q` Finding 2: one ruleset enforced both classes. `landlock_bootstrap_source` already packs `handled_access_net` as the literal `0` in `struct.pack("=QQ", ALL, 0)` | E-01 is a change to one packed value plus a rule loop, not a new mechanism or a new dependency. |
| F-3 | Net rules are port-only, address-blind | Research `uq4y6q` Finding 3: rule struct is `{allowed_access, port}`, 16 bytes, no address; two distinct hosts both connected on the allowed 443 | THE reason the capability is not named `supports_deny_push`. It proves port denial and nothing more. |
| F-4 | Denying 443 would deny the product | `oc_runipd._apply_execution_profile` wraps the worker argv that launches the coding agent, which needs the model API on 443 | The capability must not be described as a push boundary, and no action may be gated on it in this plan. |
| F-5 | A live negative test pins `supports_deny_push`'s absence | `tests/test_host_capability_extension.py` class `DenyPushRemovedTests` asserts the field, `CAP_DENY_PUSH`, the three action classes, and the `deny_push` output string are all absent | E-07 RE-POINTS rather than deletes it. Deleting a deliberate guard to make a new field fit would be the wrong move even though the new field has a different name. |
| F-6 | The three removed action classes must not come back without a consumer | `ACTION_CLASSES` is `(ACTION_READ_ONLY,)`; the comment beside `ACTION_CAPABILITY_REQUIREMENTS` warns a future reader "must not 'restore parity' by re-adding the three unused constants without a consumer" | E-03 adds NO action class and NO requirement row. The capability is reported-only. |
| F-7 | The action preflight is wired but fires for nothing | `runner_shared.execute_item_core` calls `preflight_host_capabilities`, but `RUNNER_ACTION_TO_CONTRACT_ACTION` is empty and `runner_action_contract_class` returns None for every action; the module docstring's HONEST LIMIT says "no production action requires a capability today ... so today this prevents nothing on its own" | Adding a reported capability changes no run behavior, which is the intended blast radius. A plan wanting enforcement would have to populate that mapping, which this plan deliberately does not. |
| F-8 | A forced-verdict test seam already exists | `forced_runner_safety_verdicts` context manager plus the `_FORCED_RUNNER_SAFETY` global; `probe_runner_safety_capabilities` consults it and prefixes the note with `"FORCED VERDICT (test seam): "` | Registering in `_RUNNER_SAFETY_PROBES` gives the new capability a fake/skip seam with no new test infrastructure. |
| F-9 | A real-binary-only test would skip everywhere | The bwrap stub's rationale in `tests/test_host_sandbox_profile.py` records that the real binary cannot create a userns on most CI machines, so a real-only test "would skip everywhere and guard nothing"; a skip "leaves the guarantee UNVERIFIED on that machine" and is never acceptance evidence | E-05/E-06 must include coverage that runs WITHOUT a working kernel jail (forced verdicts and the ABI gate), so the fail-closed behavior is pinned even where the real probe cannot run. |

## Proposed changes (ordered, validatable)

1. Extend the bootstrap to carry optional network rules, defaulted off so every existing caller is
   byte-unchanged (E-01).
2. Add the two-sided executed probe, fail-closed at every layer the existing probes are (E-02).
3. Add the capability, register its real probe, and report it; gate nothing (E-03).
4. Amend the published-guarantees docstring to describe what it proves and what it does not (E-04).
5. Extend the contract-field tuple and pin the probe's fail-closed behavior (E-05).
6. Pin the anti-presence-inference rule for the new capability with a table row (E-06).
7. Re-point the `deny_push` removal guard, preserving its purpose and recording why (E-07).

## Deferred / out of scope (with reason)

- GATING any action on the new capability, which would require populating
  `RUNNER_ACTION_TO_CONTRACT_ACTION` and re-adding an action class. Deliberately excluded: the
  capability proves port denial, and no action's safety argument rests on port denial alone while the
  443 hole (F-3, F-4) is open. Gating on it would imply a boundary that does not exist.
  - Carrier: sv9ce4
- REINTRODUCING a `RUN-NO-PUSH`-shaped finding code in spec 4.2. Backlog `oq05nc` gates this on a
  probe existing, and after this plan the probe proves PORT denial, not push denial, so the gate is
  still unmet. `run_evidence.validate_finding_table` also hard-fails on a code count other than 12.
  - Carrier-Declined: NOT WANTED and not owed. Binding a push-denial code to a port probe is exactly
    the fail-OPEN inference `run_evidence`'s retirement comment forbids ("DO NOT REINTRODUCE THE CODE
    BOUND TO A PRESENCE CHECK ... strictly worse than having no code at all"). The condition for a
    legitimate reintroduction is recorded in the spec, findable without asserting pending work.
- HOST-GRANULAR filtering (network namespace plus filtering proxy), the only mechanism that would
  close the 443 gap and make a real push-denial claim possible.
  - Carrier: sv9ce4
- WITHHOLDING remote credentials, the other half of 5.2's bullet. Already built and shipped:
  `oc_runipd._hardened_credential_paths` makes `~/.ssh`, `~/.netrc`, `~/.git-credentials`,
  `~/.config/gh` and peers inaccessible in hardened mode.
  - Carrier-Declined: Already done, so nothing is owed. Order 01 records this in the spec.
- Naming the capability `supports_deny_push`. Refused on measured grounds (F-3, F-4), not on caution.
  - Carrier-Declined: DELIBERATELY NOT WANTED. The name would assert what the mechanism cannot do,
    which is the overclaim plan `4h7tt0` retired and `01reg8` deleted.

## Scope check

- Over-scope: none. `host_sandbox_profile.py` is changed by E-01 through E-04; both test files by
  E-05 through E-07; the spec by the capability's appearance in 5.2's descriptor narrative, which is
  a one-paragraph addition recording that the first probed answer now exists.
- Under-scope: none. `host_cmd.py` is deliberately NOT in scope and needs no change, because
  `_capability_rows` introspects `to_dict()` for bools (F-7's sibling finding), so the new row appears
  automatically; V-03 verifies that by running the real command rather than assuming it.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. This plan changes a
  shipped dataclass and two test files, so the suite is the primary gate.
- The new probe tests must pass ON THIS HOST, and a SKIP is not acceptance evidence
  (`tests/test_host_sandbox_profile.py`'s stated policy: "a skip leaves the guarantee UNVERIFIED on
  that machine"). If the executing host reports ABI < 4, the real-denial test legitimately skips and
  the ABI-gate and forced-verdict tests MUST still run and pass; say so explicitly in the evidence
  rather than pasting a green line that hides a skip.
- `aw host capabilities opencode` must be run and its actual output pasted, showing the new row and
  its probe note.
- `aw ipd lint` conforming; `aw check` reporting no new violations.
- `aw sanitize --agent` exiting zero: probe notes and pasted command output can carry host paths.

## Spec / documentation sync

- Spec `25kzda` is AMENDED (declared in `Scope-Paths`) with one paragraph in 5.2 recording that the
  network requirement now has its first PROBED answer, what that answer proves (port denial, two-sided,
  per host), and what it still does not prove (push denial, because the mechanism is address-blind).
  WHY this belongs in the same change: 5.2 requires descriptor entries be "backed by positive and
  fail-closed probe evidence" and states "`supported` without current evidence is not sufficient", so
  adding the first such entry for this requirement changes what the contract can claim, and leaving
  the spec silent would leave the next reader unable to tell a probed row from a declared one.
- `host_sandbox_profile`'s module docstring is the published-guarantees contract and is amended by
  E-04, including the field-count prose it currently carries.
- CHANGELOG: an entry IS warranted here, since `aw host capabilities` gains a user-visible row. Add it
  under the unreleased section when executing; it is not in `Scope-Paths` as a separate concern
  because the capability row is the user-visible change and belongs with it. If the reviewer prefers
  the CHANGELOG edit be declared, add the path at review time.

## Open questions

### OQ-01: Is `supports_deny_tcp_port` the right name, or should it be `supports_deny_outbound_tcp_port`?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: wcbpqf
- Resolution or deferral rationale: NOT BLOCKING; either name is honest and the plan works unchanged
  with either. The requirement the name must satisfy is that it describe what the probe PROVES and
  not what an operator wishes it meant, which is the whole lesson of `supports_deny_push`'s removal.
  `supports_deny_tcp_port` is recommended for being shorter while still naming the granularity that
  matters (a PORT, not a host). The argument for the longer name is that Landlock's connect-TCP right
  governs OUTBOUND connects specifically and a separate bind-TCP right exists, so the short name is
  mildly ambiguous about direction. Either way the `probe_notes` entry states the direction
  explicitly, so the ambiguity is resolved at the point of use. A reviewer preferring the longer name
  should say so at review time; it is a mechanical rename before execution.

### OQ-02: Should this capability be registered in RUNNER_SAFETY_CAPABILITIES, or is it a sandbox-ladder capability like supports_os_sandbox?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: register it in
  `RUNNER_SAFETY_CAPABILITIES`. Two properties of that group decide it. FIRST, membership is what
  wires a capability into `_RUNNER_SAFETY_PROBES`, and that group's verdicts are deliberately NOT
  cached ("a stale memo here would be a way for one turn's verdict to outlive the state it was
  measured against"), which is the correct semantics for a network verdict that can change with host
  configuration between turns. The sandbox ladder, by contrast, memoizes in `_SANDBOX_PROBE_CACHE`.
  SECOND, membership grants the `forced_runner_safety_verdicts` test seam for free, which F-9 shows
  this plan needs, since a real jail is unavailable on many hosts. The ladder is also the wrong home
  on its own terms: `_SANDBOX_LADDER` rungs are ALTERNATIVE mechanisms for one filesystem-partition
  question, chosen strongest-first, whereas this is an independent question with its own answer.

### OQ-03: Should the probe allow the model API port so the capability could eventually be enabled in production, rather than proving denial on an arbitrary port?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: no, and the distinction matters. The probe's job is to
  establish whether THE KERNEL ENFORCES a port partition on this host, which is a question about the
  host and not about our port policy. Proving it with a loopback listener is strictly better evidence
  because it is hermetic, needs no external network, and gives a genuine two-sided result in CI. What
  ports a production hardened profile would allow is a POLICY decision that belongs with the work that
  actually applies network rules to a worker, and that work is carried by `wzhe4n`, because applying a
  policy requires solving the 443 problem first (F-3, F-4). Conflating the two would put a policy
  choice inside a capability probe, where it would be untestable and would quietly change what the
  capability means.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: A pasted assertion that the no-port call is byte-identical to today's output, e.g. comparing `landlock_bootstrap_source(w, r, argv)` before and after via a captured digest, plus the pasted `python3 -m pytest tests/test_host_sandbox_profile.py` result showing `LandlockBootstrapTests` still passes. Also paste the generated source for a WITH-ports call showing the connect-TCP bit in the ruleset attr and one net-port rule per requested port, and showing the ABI >= 4 guard around the network rules.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The probe's own returned `(bool, note)` for three arrangements, pasted: the real host (whatever it reports), a forced ABI < 4 condition, and an induced probe exception. The first must show a note that states the evidence rather than a bare False. Additionally show the probe distinguishes the two failure shapes by exit code: a jail that denies the ALLOWED connect must not report True, and a jail that permits the DENIED connect must report False with a note saying it was not enforced. A single True with no failure-shape evidence FAILS this item, since that is the launch-only criterion the module docstring forbids.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Actual pasted output of `aw host capabilities opencode` showing the new row and its probe note, plus `python3 -c` output printing `CAP_DENY_TCP_PORT in hsp.__all__`, `hsp.RUNNER_SAFETY_CAPABILITIES`, `hsp._RUNNER_SAFETY_PROBES[hsp.CAP_DENY_TCP_PORT] is not None` (proving it is PROBED, not the declared-not-probed `None` sentinel), and `hsp.ACTION_CLASSES` still equal to `(hsp.ACTION_READ_ONLY,)`. The last is what proves no action was gated.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff` of the docstring showing the new bullet, the corrected count prose (no longer claiming "Two fields"), and an explicit statement of the port-granularity limit and of the gates-nothing limit. A diff that adds the bullet without the limit FAILS, since an unqualified bullet in the published-guarantees contract is the overclaim this Set exists to avoid.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `git diff` showing `"supports_deny_tcp_port"` appended to `CONTRACT_FIELDS`, plus pasted output of `python3 -m pytest tests/test_host_sandbox_profile.py` showing `test_every_contract_field_exists_and_defaults_false` and `test_to_dict_snapshots_the_contract` passing with the new field included. Paste the new probe tests' results too; if any SKIPPED, paste the skip reason and state which guarantee is consequently unverified on this host.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted result of the `PRESENCE_VS_OBSERVATION` test showing the new row passing, and the row's arrangement demonstrating that a PRESENT mechanism enforcing nothing yields False. To prove the test is not vacuous, temporarily invert the probe to return True unconditionally, paste the resulting FAILURE, then revert and paste the restored pass. A row that passes both before and after that inversion is not guarding anything.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `git diff` of `DenyPushRemovedTests` showing every `supports_deny_push`/`CAP_DENY_PUSH`/action-class/`deny_push`-string assertion RETAINED and only the docstring updated, plus the pasted test result showing it passes. Also paste `aw host capabilities opencode | grep -c deny_push` returning 0, which is the behavioral proof that the new capability did not smuggle the forbidden name into the report.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

The whole design of this plan is to deliver the smallest thing that is HONESTLY TRUE. The measured
mechanism proves port denial, so the capability is named for port denial, reports port denial, and
gates nothing. A reviewer should specifically check that no artifact this plan touches can be read as
claiming push denial, because that overclaim is the exact defect plan `4h7tt0` retired and plan
`01reg8` deleted, and the cheapest way to recreate it is to build a working probe and then describe it
generously.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. Paste actual test output, including skips, rather than claiming
success. On completion, verify `aw ipd lint --phase pre-transition` conforms and every `V-*` carries
concrete observed evidence before moving this plan to `.aw/records/plans/executed/`.
