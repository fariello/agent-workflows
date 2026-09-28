# Review findings: plan iot7hc

- Subject-Id: iot7hc
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b4a75425` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent`
conforms after revision with `findings: 0`. No pre-review snapshot was owed: the plan was committed
and unmodified (`git status --short` clean; the plan's own last commit is `eb1fef9d`) and the
lane-input copy at `.aw/state/lane-inputs/rev-9/` is byte-identical to the tracked file (`diff`
reported no difference). `aw sanitize --agent` clean.

THE PLAN IS GOOD AND ITS CENTRAL JUDGEMENT IS THE RIGHT ONE. The defect is real and still real: at
this HEAD `rg -c preflight_host_capabilities` over the three runner files exits 1 with no output, so a
shipped, 38-case-tested, spec-mandated refusal is reachable from nowhere. The plan's decision to fix
REACHABILITY and refuse to invent a capability requirement is correct and is the honest reading of the
maintainer's `4h7tt0` OQ-02 ruling. Its refusal to write a second cascade is also correct, and
demonstrably so. Eight of its nine authored findings reproduce exactly.

WHAT REVIEW FOUND IS THAT THE TEMPLATE THE PLAN COPIES IS THE WRONG TEMPLATE FOR THE HALF THAT
MATTERS, AND THAT THE ONE MAPPING THE BRIDGE COULD HAVE MADE IS A MAPPING IT MUST NOT MAKE.

**THE REFUSAL WOULD HAVE FIRED AND REPORTED ITS REASON TO NOBODY (PR-101, HIGH).** E-04 instructed the
executor to "write the SAME five things that block writes", including a durable
`item["host_capability_refusal"]` key, copying `execute_item_core`'s stale-scope-target sibling. That
sibling writes a bespoke `item["scope_target_refusal"]`, and measured, NOTHING in production reads it:
`rg` finds one writer and two test reads, zero production readers. So the copy inherits a dead key.
Measured directly: an item with `status='fail-gate'` plus a bespoke `host_capability_refusal` key
yields `derive_item_disposition(...).code == 'acted_on'` with `reason is None`. The same item written
through `render_stream.record_refusal(code='host_capability_unavailable', ...)` yields
`.code == 'host_capability_unavailable'` with the reason
`'host_capability_unavailable (the host could not prove a capability this action requires)'`. This is
decisive for a plan whose entire deliverable is reachability: the operator-visible reason code is the
thing being made reachable, and `SKIP_HOST_CAPABILITY_UNAVAILABLE` would have remained unemittable by
any surface while three V-items reported success. HIGH and IN-SCOPE rather than BLOCKER because the
item's status, event and message would all have been correct; what was missing is the one record the
reason-rendering path actually reads.

**MAPPING `execute` ONTO `read_only` IS A FALSE CLASSIFICATION THAT ALSO CORRUPTS THE SPEC'S MESSAGE
(PR-102, HIGH).** E-03 said to "map the runner's `item["action"]` vocabulary onto the contract's action
vocabulary", and since `ACTION_CLASSES == ('read_only',)` the only non-sentinel mapping available is
`execute -> read_only`. Two measurements make that wrong. `read_only`'s own `spec_basis` reads
"Repository read and captured evidence only; no agent session for a skip", while an `execute` item
starts an agent session and mutates the tree, so the row asserts the opposite of what the item does.
And `format_host_capability_finding` interpolates the action verbatim: measured, an execute item's
refusal under that mapping renders `... required by iot7hc action read_only`, putting the wrong action
into the one string spec `25kzda` specifies byte-for-byte. E-03 now maps all three runner actions to
the NO-POLICY sentinel, and the empty mapping table is stated as the deliberate SEAM `b7tlsh` /
`oq05nc` will add a row to, which converts an apparent hole into a declared handoff.

**THE RECOVERY COMMAND WOULD NOT HAVE BEEN A COMMAND (PR-103, MEDIUM).** E-04 said to pass "the host
label the descriptor was built for, not the driver id", which is right in direction and names no field.
The nearest field in `host_labels` is `.id`, measured `oc_runipd` / `agy_runipd`, and the message ends
`then run: aw {host} run {selector}`, so passing it renders `aw oc_runipd run ...`. E-04 now names
`host_labels.argv_tokens[1]` (measured `opencode` / `antigravity`), verified to be real CLI nouns
(`aw opencode --help` and `aw antigravity --help` both resolve), and the same value
`oc_runipd._apply_execution_profile` passes to `detect_host_capabilities`.

Four smaller items. E-04 never said where the capabilities DESCRIPTOR comes from, leaving an executor
to either thread one through a 14-parameter signature or guess (PR-104); it now names
`detect_host_capabilities` with the measured cost (0.048s cold, sub-millisecond warm, probes
side-effect-free) so the per-item call is justified rather than assumed. E-04 told the executor to copy
the template's `try/except` "posture" without stating that the posture is fail-OPEN (PR-105); it now
says so explicitly, which matters because a crash in a gate that currently refuses nothing must not be
able to kill a run. The whole-suite regression bar had no number (PR-106); re-measured bare at
`2935 passed, 2 skipped, 3 warnings in 45.08s`. And the gate lacked an out-of-scope-edit disposition
and stated the finalize move unconditionally (PR-107); both corrected per the 2026-09-01 scope-fence
ruling, with make-and-justify wording and conditional runner/executor ownership.

OQ-02 is RESOLVED by taking the plan's own default (decision D-2): `host_sandbox_profile.py` joins
`Scope-Paths` for exactly one docstring paragraph, whose "HONEST LIMIT: nothing in the runners consults
this preflight yet" E-04 falsifies. Declaring that at review is also what keeps the finalize scope gate
satisfied. OQ-01 is deliberately LEFT `open` and non-blocking: it asks the maintainer to confirm that
reachability alone is the deliverable, the plan is written to its default, and a non-blocking question
does not gate readiness under the 2026-09-10 ruling.

Every other claim was checked and HELD. F-01 (zero call sites at a newer HEAD, exit 1 confirmed);
F-02 (`UnknownActionError: unknown action class 'execute'; expected one of ['read_only']`, reproduced
for all three runner action names); F-03 (`ACTION_CLASSES == ('read_only',)`,
`ACTION_CAPABILITY_REQUIREMENTS['read_only'].required == ()`, so `read_only` passes on every host);
F-04 (one shared dispatch point, `execute_item_core` called from `oc_runipd:3348` and
`agy_runipd:2880`); F-05 (`supports_fresh_verifier_session` True on linux, False on darwin and win32;
`supports_commit_gateway` False everywhere, declared-never-probed); F-06 (DEMONSTRATED, not merely
read: a `fail-gate` prerequisite drove its dependent to `fail-depend` with
`['executed:aaa111 (target fail-gate)']`); F-07 (both comments located verbatim); F-08
(`RUN-HOST-CAPABILITY` carries `binding=BOUND` naming the three predicates); F-09 (`mjx7ne`'s deferral
and the module docstring's honest limit both read as quoted). All four deferral carriers resolve to
live artifacts (`b7tlsh`, `oq05nc`, `u7bfks` open; the `Carrier-Declined` rows argue their case). Spec
`25kzda` 5.2/5.4/5.7 read exactly as the Concern quotes them, so the no-spec-amendment claim holds.
One drift note, batched and not raised as a finding: the plan cites the template block by the symbol
`scope_target_stale`, which is not a symbol (it is the event string the block writes and the local
variable stem); the block resolves unambiguously and the plan's quoted placement comment matches
verbatim, so this is anchor imprecision, not a bad citation. Corrected in place while editing.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-101 | HIGH | IN-SCOPE | A. Correctness / C. duplicate-path avoidance / E. Testing | Plan E-04 as authored ("a durable `item["host_capability_refusal"]` carrying the preflight's verbatim `message` and its `reason_code`"); `runner_shared.execute_item_core`'s stale-scope-target block writing `item["scope_target_refusal"]`; `rg scope_target_refusal` -> 1 writer, 2 test reads, 0 production readers; measured `derive_item_disposition({status:'fail-gate', host_capability_refusal:{...}}, refusal_of_item).code == 'acted_on'`, `reason is None`; measured via `record_refusal` -> `.code == 'host_capability_unavailable'`; `render_stream.refusal_of_item` docstring "THE ONE READER every surface goes through"; `record_refusal` docstring "THE ONE WRITER, paired with `refusal_of_item`" | **THE PLAN COPIES A BESPOKE DURABLE KEY THAT NO PRODUCTION SURFACE READS, SO THE REFUSAL IT MAKES REACHABLE WOULD REPORT ITS REASON TO NOBODY.** The plan's whole deliverable is that `host_capability_unavailable` becomes emittable; recorded the copied way, the item ends `fail-gate` with a correct message and event while its DERIVED disposition reads `acted_on`, so the spec's reason code is emitted by no surface and `SKIP_HOST_CAPABILITY_UNAVAILABLE` stays as unreachable as before. Three V-items would have passed over this. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now writes through `render_stream.record_refusal` with `code=host_capability_unavailable`, the verbatim message as `reason`, and the shipped `DISPOSITION_REMEDIES` entry as `remedy`, and explicitly forbids the bespoke key with the measurement. E-02 gains case (3) asserting the derived code; V-04 makes a derived code of `acted_on` a FAILURE however correct the status looks. New F-10 records it. Scope unchanged (same file). |
| PR-102 | HIGH | IN-SCOPE | A. Correctness / F. Honest documentation / B. spec-message integrity | `ACTION_CAPABILITY_REQUIREMENTS['read_only'].spec_basis` = "Repository read and captured evidence only; no agent session for a skip"; `ACTION_CLASSES == ('read_only',)`; `format_host_capability_finding` interpolating `action` verbatim into `RUN_HOST_CAPABILITY_MESSAGE`; measured render under that mapping: `... required by iot7hc action read_only`; plan E-03 "map the runner's `item["action"]` vocabulary ... onto the contract's action vocabulary" | **THE ONLY NON-SENTINEL MAPPING THE BRIDGE COULD MAKE IS ONE IT MUST NOT MAKE.** With one contract class, "map the runner's vocabulary onto the contract's" reads as `execute -> read_only`. That both asserts the opposite of what an execute item does (it starts a session and mutates) and writes the wrong action name into spec `25kzda`'s byte-exact operator message. E-03 left this open, and the natural reading of it is the wrong one. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires ALL THREE runner actions to map to the NO-POLICY sentinel, states both measured reasons, and states that the production-row-free mapping dict is the deliberate SEAM a future requirement plugs into (so an empty table is a deliverable, not an omission). V-03 fails a bridge that maps `execute` onto `read_only` even if every test passes. New F-11 records it. |
| PR-103 | MEDIUM | IN-SCOPE | F. UX / operability | `host_labels.id` measured `oc_runipd` / `agy_runipd`; `RUN_HOST_CAPABILITY_MESSAGE` ends "then run: aw {host} run {selector}"; `host_labels.argv_tokens[1]` measured `opencode` / `antigravity`; `aw opencode --help` and `aw antigravity --help` both resolve; `oc_runipd._apply_execution_profile` calls `detect_host_capabilities("opencode")` | E-04 said to pass "the host label the descriptor was built for, not the driver id" but named no field. The nearest available field is `.id`, which renders the recovery command `aw oc_runipd run <selector>` - not a command that exists. The plan's own warning ("a wrong value produces a recovery command an operator cannot run") was therefore correct and unactionable. | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | E-04 names `host_labels.argv_tokens[1]` explicitly, with both measured values and the verification that they are real CLI nouns. V-04 requires the rendered command pasted and the noun confirmed not to be a driver id. New F-12 records it. |
| PR-104 | MEDIUM | UNDER-SCOPE | G. Plan executability | Plan E-04 names no descriptor source; `execute_item_core`'s signature takes no capabilities argument; `detect_host_capabilities` measured at 0.048s cold / <0.001s warm, `_SANDBOX_PROBE_CACHE` memoizing the jail ladder; `_probe_fresh_verifier_session` uses in-memory doubles and a `/nonexistent` worktree path | The plan told the executor to call a function taking a `capabilities` argument without saying where that descriptor comes from inside a function that has no such parameter. The two obvious routes (thread it through a 14-parameter shared signature, or call the detector per item) differ materially, and the plan's silence invites the former. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 states the source (`detect_host_capabilities(<the same host noun>)`) and the measured cost with the memoization and side-effect-freedom that justify a per-item call. New F-13 records it. |
| PR-105 | MEDIUM | IN-SCOPE | A. Correctness / C. failure handling | `execute_item_core`'s template block: `except Exception as ex: scope_target_check_error = str(ex)`, recorded into the attempt and execution CONTINUING; plan E-04 "follow ... its `try/except` posture" | E-04 told the executor to copy the template's exception posture without saying what that posture IS. It is fail-OPEN (record the error, proceed), and that direction is load-bearing here: a crash inside a gate that currently refuses nothing must not be able to kill a run that would otherwise succeed. An executor reading "fail closed" from the plan's Goal could reasonably have made the opposite choice. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now states the fail-open direction explicitly, requires the error be recorded, and gives the reason. |
| PR-106 | LOW | IN-SCOPE | E. Testing | Plan E-07/Required tests said "a baseline taken the same way BEFORE any edit" with no value; `tests/test_host_capability_extension.py` claimed "38 passing at authoring", `tests/test_host_sandbox_profile.py` unquantified | The whole-suite regression check had no number, so an executor could paste any count and call it unchanged, in a plan every other measurement of which is numeric. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-measured bare at review: `2935 passed, 2 skipped, 3 warnings in 45.08s`. Recorded in E-07, Required tests and V-07. The two contract files re-measured at 38 and 28 passing. E-07 also now notes the total will RISE by the new file's cases, so "no new failures" is the bar rather than an identical total. |
| PR-107 | LOW | IN-SCOPE | G. Plan executability (gate) | Plan gate as authored: approval statement, what-an-approver-accepts, scope fence, honesty rule, path-scoped commit and never-push all present; no out-of-scope-edit disposition; "Do not move this plan to `executed/` until ..." stated unconditionally; workflow Step 4 scope-fence ruling of 2026-09-01 | The gate carried every required element except an out-of-scope-edit disposition, and it stated the lifecycle move without the conditional runner/executor ownership the contract requires (under a runner, the RUNNER finalizes and the executor must not). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now states make-and-justify for an out-of-scope edit (`--scope-reason` / `--scope-ack`), explicitly that it is not a reason to stop, and keeps a stop directive only for the genuinely unsafe concurrent-edit case. Lifecycle move states conditional ownership and forbids a hand-rolled `git mv`. Commit clause names the plan file beside the scope paths. A WHAT-REVIEW-CHANGED paragraph records PR-101/PR-102 so an approver sees the two code-shape changes. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | With one contract action class, what should the bridge map the runner's `execute`/`review`/`plan` onto (PR-102)? | ALL THREE onto the explicit NO-POLICY sentinel; no production row maps onto `read_only`. | (a) Map `execute` onto `read_only`: rejected on two measurements. `read_only`'s `spec_basis` is "Repository read and captured evidence only; no agent session for a skip", which is the opposite of an execute item, and `format_host_capability_finding` would render `action read_only` into spec `25kzda`'s byte-exact message. (b) Add a new contract action class for `execute`: rejected as out of scope and as reversing `4h7tt0` OQ-02 by the back door, which the plan's own Deferred section and `01reg8`'s "do not restore parity" comment both forbid; it is also exactly what `b7tlsh`/`oq05nc` own. (c) Let the unmapped case raise: rejected, `UnknownActionError` at the dispatch point crashes every execute item (the defect F-02 already measured). | Measured `spec_basis` string and measured message render; `01reg8` E-04's "restore parity" prohibition at `host_sandbox_profile.py` line 1274; the plan's Deferred rows and their live carriers; measured `UnknownActionError` for all three runner names. | yes |
| D-2 | OQ-02 asks whether to amend `host_sandbox_profile.py`'s now-false module docstring or leave it stale and file a backlog item. | AMEND IT. Added the file to `Scope-Paths` for that ONE paragraph, wrote the edit into E-06 and the evidence into V-06. | Decline and file a backlog item: rejected. It trades a durable false statement in the module whose contract this plan consumes, plus a tracking artifact, for a two-line edit; and the staleness is created BY this plan's own commit, which is the drift E-06 exists to prevent one file over. The plan itself recorded AMEND as its default and asked a reviewer to decide, so this takes the default rather than overriding the author. | The docstring's own text ("HONEST LIMIT: nothing in the runners consults this preflight yet ... so today this prevents nothing on its own"), whose first clause E-04 falsifies and whose last clause stays true; the workflow's Step 4 requirement that declared scope be settled at review rather than mid-execution, since `aw ipd finalize` refuses an undeclared out-of-scope path. | yes |
| D-3 | Does PR-101 make the plan's approach unsound (a REPLAN), or is it a bounded fix? | BOUNDED FIX. The plan's architecture (one call at the one shared dispatch point, template shape, no second cascade) is correct and unchanged; only the refusal RECORD mechanism changed. | Treat it as REPLAN: rejected. The call site, placement, status token, event, cascade reuse and scope are all correct as authored and all verified at review; substituting `record_refusal` for a bespoke key is a within-item edit to one E-item plus one test case, not a different plan. | Measured equivalence of everything else (placement comment verbatim, `fail-gate` in `TERMINAL_STATES_CANONICAL`, cascade demonstrated end to end); `record_refusal` is in the same module the runner already imports at module level, so no new dependency or import direction is introduced. | yes |
| D-4 | Should OQ-01 be escalated to `Blocking: yes`, given it decides whether the plan delivers a protection or only reachability? | NO. Left `open`, `Blocking: no`, owner maintainer, carrier `b7tlsh`. | Escalate to blocking: rejected. The plan is correct and complete under its stated default, the default is the conservative one (it adds no refusal to any host), and the alternative would reverse a maintainer ruling and require a spec decision that two live backlog items already own. Under the 2026-09-10 ruling a non-blocking question does not make a plan NO-GO, and marking it blocking would hold a correct plan for a question its author judged non-stopping. | The 2026-09-10 maintainer ruling on `qhy3i3` OQ-01 recorded in the plan-review workflow's readiness section; `4h7tt0` OQ-02's recorded ruling; `b7tlsh` and `oq05nc` both `open` and both naming this exact question. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. OQ-01 remains `open` and non-blocking by deliberate decision D-4; OQ-02 is now `resolved`.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  after all edits (Scope/Scope-Paths amendment, E-02/E-03/E-04/E-06/E-07 revisions, F-10..F-13,
  V-03/V-04/V-06/V-07 revisions, OQ-02 resolved, gate rewrite, `Status` to `reviewed`,
  `Readiness: go-pending-approval`).
- `aw sanitize --agent` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- Lane input identity: `diff .aw/state/lane-inputs/rev-9/plan-20260928-7bj5sa-01-iot7hc-....ipd.md
  .aw/records/plans/pending/20260928-7bj5sa-01-iot7hc-....ipd.md` -> no difference; `git status --short`
  clean before editing, so no pre-review snapshot was owed.
- **F-01 reproduced.** `rg -c "preflight_host_capabilities" agent_workflows/oc_runipd.py
  agent_workflows/agy_runipd.py agent_workflows/runner_shared.py` -> no output, exit 1.
- **F-02 reproduced**, for all three runner action names:
  `UnknownActionError: unknown action class 'execute'; expected one of ['read_only']. Refusing to guess
  a requirement set: defaulting an unknown action would let a mutating action inherit the read-only
  policy.` Same for `review` and `plan`.
- **F-03 reproduced.** `ACTION_CLASSES == ('read_only',)`;
  `{'read_only': ()}` for required capabilities; `preflight_host_capabilities('read_only', caps, ...)`
  returns `ok=True` on this host.
- **F-04 reproduced.** `runner_shared.execute_item_core` defined once and called from
  `oc_runipd.py:3348` and `agy_runipd.py:2880`.
- **F-05 reproduced exactly.** `supports_fresh_verifier_session`: linux True, darwin False, win32
  False. `supports_commit_gateway`: False on all three.
- **F-06 DEMONSTRATED, not merely read.** Built a two-item queue with a `fail-gate` prerequisite and
  called `cascade_dependency_blocked`: the dependent became `fail-depend` with
  `['executed:aaa111 (target fail-gate)']`. Confirmed `'fail-gate' in TERMINAL_STATES` is True,
  `EXECUTION_SUCCESS_STATES == {'executed'}`, `'fail-gate' not in SUCCESS_STATES`.
- **PR-101, the finding that changed the plan.** Both directions measured:
  - bespoke key: `derive_item_disposition({'status':'fail-gate', 'host_capability_refusal':{...}},
    refusal_of_item)` -> `code='acted_on'`, `reason=None`.
  - `record_refusal`: same call -> `code='host_capability_unavailable'`,
    `reason='host_capability_unavailable (the host could not prove a capability this action requires)'`.
  - `rg scope_target_refusal` -> `runner_shared.py` 1 writer, `tests/test_scope_path_target_stale.py`
    2 reads, zero production readers.
- **PR-102** measured: under an `execute -> read_only` mapping the refusal renders
  `[RUN-HOST-CAPABILITY] Host opencode cannot enforce supports_fresh_verifier_session required by
  iot7hc action read_only. ... then run: aw opencode run 7bj5sa` - the action name is wrong.
- **PR-103** measured: `OC_HOST_LABELS.id == 'oc_runipd'`, `argv_tokens == ('oc','opencode')`;
  `AGY_HOST_LABELS.id == 'agy_runipd'`, `argv_tokens == ('agy','antigravity')`. `aw opencode --help`
  and `aw antigravity --help` both resolve to real subcommands.
- **PR-104** measured: `detect_host_capabilities('opencode')` 0.062s first call, 0.001s/0.000s warm;
  with `_SANDBOX_PROBE_CACHE` cleared, 0.048s. `probe_runner_safety_capabilities` 0.0185s then
  ~0.0003s.
- **F-07 reproduced.** `rg -n "NOT REACHABLE TODAY|no current run can emit|no run can produce it
  TODAY" agent_workflows/` -> exactly the three lines in `run_selection_policy.py` the plan names.
- **F-08 reproduced.** `run_evidence.RUN_FINDING_CODES`' `RUN-HOST-CAPABILITY` row carries
  `binding=BOUND` and the `NonMaskableClass` entry names
  `host_sandbox_profile.preflight_host_capabilities` as the upstream decider.
- **F-09 reproduced.** `host_sandbox_profile.py` module docstring: "HONEST LIMIT: nothing in the
  runners consults this preflight yet. ... so today this prevents nothing on its own."
- Spec `25kzda` checked directly: 5.2's fail-closed rule, the 5.4 reason-table row
  (`Required host capability unavailable` -> `failed` / `host_capability_unavailable`) and the 5.7
  taxonomy row (`Host guarantee unavailable` -> "Refuse the item before session start; cascade
  dependents; continue independent items") all read as the plan's Concern quotes them.
- Carriers resolved: `b7tlsh` open, `oq05nc` open, `u7bfks` open, backlog `7bj5sa` graduated,
  `mjx7ne` / `01reg8` / `4h7tt0` executed. `01reg8` E-04's "restore parity" prohibition and E-06's
  order-dependence hazard for the synthetic action both confirmed in that plan's text.
- Suite baselines, bare: `python3 -m pytest` -> `2935 passed, 2 skipped, 3 warnings in 45.08s`.
  `tests/test_host_capability_extension.py -o addopts=""` -> `38 passed`.
  `tests/test_host_sandbox_profile.py -o addopts=""` -> `28 passed`.
