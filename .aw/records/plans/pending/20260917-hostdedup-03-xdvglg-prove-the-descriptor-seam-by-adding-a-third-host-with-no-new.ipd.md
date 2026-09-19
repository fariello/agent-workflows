# IPD: Prove the descriptor seam by adding a third host with no new runner

- Date: 2026-09-17
- Kind: child
- Concern: Nothing currently PROVES that adding a host does not mean writing another runner. The claim rests on `HostLabels` existing, but both of its instances were written by extracting from two runners that already existed, so the descriptor has never been exercised in the direction it will actually be used: adding a NEW host that has no runner module of its own. Until that is demonstrated, 'add a descriptor, not a runner' is an assertion. The measured risk is concrete: `oc_runipd.py` is 9708 lines and `agy_runipd.py` 5887 (RE-MEASURED AT REVIEW; the authored 9588/5784 are stale but the order of magnitude stands), so if the seam is insufficient the third host arrives as several thousand more duplicated lines, and the fourth and fifth after it.
- Scope: Add a THIRD host end to end without adding a runner module, and let the attempt find whatever the seam is missing. The deliverable is either a working third host reached through `HostLabels` plus a thin entry point, or a precise, evidenced list of what the descriptor cannot express. Both outcomes are valuable; only an unexamined assumption is not. **RE-SCOPED AT REVIEW: the honest expected outcome is the SECOND one.** Measured at review HEAD, `HostLabels` models eight STRINGS plus one capability flag and models NONE of the three things a host actually needs to run a turn: the argv construction (fully host-specific, `oc_runipd.py:5648` vs `agy_runipd.py:2730`, different flags and different stream formats), the spawn function (`run_opencode` vs `run_agy_turn`, materially different signatures), and the 13 host-only `options` keys their `initialize_run`s write. So E-03 is expected to produce a gap list, not a working host, and the plan is now written so that outcome is a success rather than a shortfall.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_hostdedup_third_host.py, .aw/records/research, agent_workflows/run_analytics_sources.py, agent_workflows/run_viewer.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/host_cmd.py, tests/test_rununify_initialize_run_characterization.py
- Item-Dependencies: executed:nmlx47
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: dstnso
- Set: hostdedup
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: xdvglg
- Approval: 2026-09-18, human ("approved"): Approved by maintainer: initialize_run unified into runner_shared.py; OQ-03 resolved and PR-001 discharged

## Workflow history
- 2026-09-18 approved (aw set, --by-human): Approved by maintainer: initialize_run unified into runner_shared.py; OQ-03 resolved and PR-001 discharged
- 2026-09-18 reviewed (antigravity pair with maintainer): /plan-review ROUND 3: APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. OQ-03 RESOLVED by maintainer direction and execution: initialize_run was unified into runner_shared.initialize_run_core (commit 7a28ed11), so the identity write is unified in runner_shared.py and parameterized by caller. PR-001 dispositioned FIXED. All blocking questions resolved; readiness promoted to go-pending-approval.
- 2026-09-18 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): /plan-review ROUND 2 (audit of round 1): REVIEWED - OPEN QUESTIONS; readiness stays `no-go`; PR-001 CARRIED FORWARD still OPEN at BLOCKER, plus PR-101..PR-105 all FIXED. OQ-03 IS STILL UNANSWERED (no commit since round 1's own hardening touches it), so the plan remains correctly blocked by both gates (`IPD-Q501` and the typed finding gate). I RE-DERIVED EVERY LOAD-BEARING MEASUREMENT ROUND 1 WROTE INTO THIS PLAN AND ALL OF THEM HOLD (8 `HostLabels` fields with no defaults; 10 shared / 7 oc-only / 6 agy-only options with all 13 names exact; 9 binding sites per runner; both identity writes; `initialize_run` 446/353; argv divergence at the cited lines; the two consumers' differing mechanisms; `DEFAULT_HOSTS`; the three `25kzda` N-host citations). THREE ROUND-1 DEFECTS FOUND: a NINTH file is affected and was undeclared (`tests/test_rununify_initialize_run_characterization.py` pins `driver.path == __file__` and `driver.sha256` in three places, exactly what E-02 changes, now fenced with a deliberate re-base specified); round 1 mandated pre-cutover evidence from `.aw/records/runs/`, which is GITIGNORED and absent from every lane, re-pointed at tracked fixtures in `tests/test_run_analytics_sources.py`; and the `HostLabels` anchor round 1 corrected has drifted again 9425 -> 9509. Also closed round 1's open question about `driver.sha256`: exactly ONE reader exists and it is that characterization test, no product consumer. A TRAP WORTH NAMING: advancing to round 2 silently released round 1's BLOCKER from the typed gate (current-round semantics, `check_engine.py:3161-3162`), measured going from one gating block to none, so PR-001 is deliberately restated in round 2 to keep it gating.
- 2026-09-18 reviewed (aw set): plan-review complete: REVIEWED - OPEN QUESTIONS; 10 findings, 9 FIXED, PR-001 left OPEN at BLOCKER and escalated as blocking OQ-03 (the maintainer's resolved OQ-02 commits E-02 to editing the __file__-derived driver identity inside BOTH forked initialize_run functions, two of the five large functions this Set deliberately leaves alone); fence widened from 3 to 8 paths; HostLabels measured to model neither argv, spawn nor the 13 host-only options keys, so a gap list is now the PREDICTED outcome; spec 25kzda verified already N-host; readiness no-go; typed review record under .aw/records/reviews/
- 2026-09-18 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-010; readiness `no-go` on ONE blocking finding. Reviewed at HEAD `2c3722d8`; `aw ipd lint --phase author` conforming before revision. **THE EXPERIMENT IS THE RIGHT ONE AND ITS FRAMING IS THE BEST THING IN THIS SET**: "a seam extracted from two instances is fitted to those two instances; the third is where an over-fitted abstraction reveals itself" is exactly right, and declaring a gap list an ACCEPTABLE outcome is what makes it an experiment rather than a demo. F-1 verified (`HostLabels` at `runner_shared.py:9425`, 8 fields, `_field_defaults` empty, both instances bound). F-3 verified almost exactly: the `options` literals split 10 shared + 7 oc-only + 6 agy-only, matching the claimed 7/6 asymmetry. F-4 verified in BOTH consumers, and note `run_viewer.py:865-871` uses SUBSTRING matching with a `Path(...).stem` fallback rather than the basename lookup `run_analytics_sources.py:206` uses, so the two consumers do not even agree on the mechanism. F-6 verified (`host_launchers.py:17` "No live models are launched in tests (doubles only)"; `host_runner.run_worker_process` takes an injectable `runner`). **BUT THE BLOCKER IS THAT THE FENCE MAKES THE PLAN UNEXECUTABLE, and the gap is far wider than one file.** `- Scope-Paths:` declared three paths while the maintainer's own resolved OQ-02 commits E-02 to editing FIVE more: both analytics consumers, and both runners' `initialize_run` where `state['driver']['path']` is written from `__file__` (`oc_runipd.py:3641-3643`, `agy_runipd.py:2349-2351`). `initialize_run` is one of the FIVE LARGE FUNCTIONS THIS SET DELIBERATELY LEAVES FORKED (446 oc / 353 agy raw lines), so the identity write cannot be changed in one shared place, and a third host needs `host_cmd.DEFAULT_HOSTS` (`:37`) too or `aw host capabilities` cannot see it. All five added to the fence. **AND THE SEAM IS NARROWER THAN THE PLAN ASSUMES, which is the finding E-01 should have started from:** `HostLabels` carries no argv, no spawn and no options contract, its 9 binding sites per host all live INSIDE a runner module (measured: 9 `HOST_LABELS` references in each), and the two hosts' argv construction shares nothing (`[opencode, "run"]` with `--dir`/`--session` versus `[agy_bin, "-p", prompt, "--output-format", "stream-json", "--print-timeout", ...]`). GOOD NEWS THE PLAN UNDERSELLS: spec `25kzda` is ALREADY N-host by design, not two-host as the spec-sync section fears (A4 "host asymmetry", a mandatory "Per-host capability descriptor" section stating "`oc` may support a capability that `agy` does not", and `required_host_capabilities` per action packet), and `host_sandbox_profile.detect_host_capabilities` is host-name-driven with ONE hardcoded `opencode` branch, so a third host is fail-closed legible to it today. V-02's pre-cutover evidence is also readily available: 181 run records in the corpus across four historical driver basenames (`oc_runipd.py` 160, `runipd.py` 13, `agy_runipd.py` 5, `ipdrunner.py` 2), all four already in `DRIVER_GENERATIONS`. ALSO FIXED: the Proposed-changes list was misnumbered against the E-items (it named 5 steps for 6 items and mapped E-02 to two different things); the suite baseline was unstated and is now `7975 passed, 3 skipped, 2 xfailed`; `- From-Backlog: dstnso` added to match its siblings. OQ-03 raised `Blocking: yes` carrying PR-001.
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from an AST measurement at HEAD (34 forked symbols / ~1752 oc lines across the two runners); complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Turn "a new host is a descriptor, not a runner" from a claim into a demonstrated property, before the
codex/claude/hermes work starts and the cost of being wrong is multiplied by three.

WHY A THIRD HOST IS THE ONLY HONEST TEST. Orders 01 and 02 reduce duplication between two EXISTING
runners. That is necessary but it does not answer the question the maintainer actually asked, which is
about hosts that do not exist yet. A seam extracted from two instances is fitted to those two instances;
the third is where an over-fitted abstraction reveals itself. Doing this as a DELIBERATE experiment, whose
acceptable outcome includes "the descriptor is insufficient, here is exactly how", is much cheaper than
discovering the same thing halfway through a real host integration.

SCOPE DISCIPLINE: this plan does not need a working AI host. A third host that is real enough to exercise
every seam the runners touch (a scripted or dry-run host) answers the structural question completely, and
does so without depending on a vendor CLI, credentials, or spend.

WHAT THE SEAM ACTUALLY COVERS, MEASURED AT REVIEW, because the plan assumed more than `HostLabels`
delivers and E-01 should start from the measurement rather than re-derive it:

| a host must supply | does `HostLabels` model it? | evidence |
|---|---|---|
| 8 operator-facing strings + 1 capability flag | YES, and that is ALL it models | `class HostLabels` in `runner_shared.py` (at `:9509` when round 2 measured; the SYMBOL is authoritative, the line is a hint, because this file grows weekly and the anchor has now drifted twice: `:8530` -> `:9425` -> `:9509`). Fields, verified: `command`, `review_command`, `argv_tokens`, `argv_subcommands`, `product`, `report_title`, `shell_tool`, `emits_launch_identity`; `_field_defaults` empty |
| the ARGV to launch a turn | **NO** | `oc_runipd.py:5648` builds `[opencode, "run"]` with `--dir`/`--session`/`--model`; `agy_runipd.py:2730` builds `[agy_bin, "-p", prompt, "--output-format", "stream-json", "--print-timeout", ...]`. Different flags, different stream format, zero overlap |
| the SPAWN function | **NO** | `run_opencode` (13 params) vs `run_agy_turn` (12, different set); each host's own, and `execute_item` calls its own by name |
| the host-only `options` keys | **NO** | measured 10 shared + 7 oc-only + 6 agy-only in the two `initialize_run` literals |
| the DRIVER IDENTITY | **NO**, and it is written from `__file__` | `"path": str(Path(__file__).resolve())` at `oc_runipd.py:3642` and `agy_runipd.py:2350`, inside the FORKED `initialize_run` (re-verified at round 2). AND IT IS PINNED BY A TEST: `tests/test_rununify_initialize_run_characterization.py:230-233` calls the basename assertion "The load-bearing assertion", `:248-252` pins `path == module_file` AND `sha256 == sha256_file(module_file)`, `:292` re-derives the basename. That file is now in the fence (round 2, PR-101) |
| where the labels get BOUND | inside a runner module, 9 sites per host | 9 `HOST_LABELS` references in each runner (measured) |

THE LAST ROW IS THE STRUCTURAL POINT AND IT SHAPES E-03: a `HostLabels` instance is currently bound by
call sites that live INSIDE a runner module, so "a host that is only a descriptor" has nowhere to put its
nine bindings. That is not a reason to abandon the experiment; it is the experiment's likely FIRST finding,
and stating it here stops an executor mistaking it for their own mistake.

SO THE EXPECTED OUTCOME IS A GAP LIST, NOT A WORKING HOST, and the plan is now written for that. E-03's
"either a completed execution or a precise failure list" is preserved exactly because it was right; what
changes is that the second branch is now the PREDICTED one, with the prediction recorded above so the
result can be compared against it rather than judged against an optimistic hope.

ONE PIECE OF GOOD NEWS THE PLAN UNDERSELLS. Spec `25kzda` is ALREADY WRITTEN FOR N HOSTS, not two: its
assurance A4 is "host asymmetry", it mandates a "Per-host capability descriptor" whose text says
"`oc` may support a capability that `agy` does not, or vice versa; the descriptor controls the decision for
the current installation", and each action packet declares `required_host_capabilities`. And
`host_sandbox_profile.detect_host_capabilities` is host-NAME driven with a single hardcoded `opencode`
branch, so an unknown third host is already legible to it and fails closed. The spec-sync section's fear
that the spec "assumes exactly two hosts" is therefore mostly unfounded, which is worth knowing before
E-03 starts looking for a spec amendment it probably does not need.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Enumerate what a host must supply

- [ ] E-01 Derive, from the code rather than from intuition, the COMPLETE set of things a host must supply to the shared runner: every `HostLabels` field, every host-specific `options` key, the driver-identity contract (`state['driver']['path']`, whose value two analytics consumers key on BY DIFFERENT MECHANISMS), the argv/launch shape, the SPAWN function's signature, the permission-posture inputs, and any remaining host-specific branch in shared code. Produce it as a checklist a new host integrator could work through. **START FROM THE REVIEW'S MEASURED TABLE IN THE GOAL rather than re-deriving it, and EXTEND it; the four rows marked "NO" are the ones that decide whether this plan's premise holds.** Include for each entry whether `HostLabels` models it TODAY, because "what the descriptor covers" and "what a host must supply" are different sets and conflating them is what made this plan's scope optimistic.
  - Depends on: none
  - Expected outcome: an enumerated host contract with each entry citing the consumer that reads it, and each marked modelled / not-modelled by `HostLabels`. MUST include: the 8 `HostLabels` fields (verified at review: exactly 8, no defaults); the 13 host-only `options` keys (verified: 7 oc-only `agent`/`auto`/`launch_profile`/`no_audit`/`opencode`/`validate`/`variant`, 6 agy-only `agy_executable`/`dangerously_skip_permissions`/`effort`/`new_session`/`no_verify`/`timeout`); the argv construction and the spawn signature, NEITHER of which the descriptor models; the `__file__`-derived driver identity; and the NINE per-host label BINDING SITES that today live inside a runner module. `orziju`'s "23 keys" figure re-measured at review as 10 shared + 7 + 6 in the `options` literal, so cite your own measurement and note any divergence.
  - Execution state: pending

### Task group 2: Add the third host and let it find the gaps

- [ ] E-02 Implement the maintainer's OQ-02 ruling: add an explicit host-id field to `HostLabels`, have a run record that identity, and re-point `run_analytics_sources.driver_generation` and `run_viewer` at the id. MUST include the fallback for PRE-CUTOVER records, which hold a module path and cannot be rewritten, so historical runs keep attributing correctly.
  **THE FILES THIS TOUCHES WERE NOT DECLARED AND NOW ARE; READ THIS BEFORE STARTING.** Measured at review, the ruling's four commitments reach FIVE files beyond the authored fence. (1) The field goes in `runner_shared.py` (declared) and, being a no-defaults `NamedTuple`, FORCES an edit to BOTH host bindings. (2) `run_analytics_sources.driver_generation` (`:183-207`) looks up `DRIVER_GENERATIONS[basename]`, while `run_viewer` (`:865-871`) does SUBSTRING matching (`"oc_runipd" in driver_path`) with a `Path(...).stem` fallback: two different mechanisms, so "re-point both consumers" is two different edits, not one pattern applied twice. (3) THE IDENTITY WRITE IS INSIDE `initialize_run`, WHICH THIS SET DELIBERATELY LEAVES FORKED (`oc_runipd.py:3641-3643` and `agy_runipd.py:2349-2351`, each `str(Path(__file__).resolve())`, in a 446-line and a 353-line forked function). So the write must be changed in TWO places and cannot be unified here; do NOT attempt to lift `initialize_run` to make it one place, that is explicitly out of this Set. (4) A third host must also be added to `host_cmd.DEFAULT_HOSTS` (`:37`) or `aw host capabilities` cannot report it, which E-01's own convention note requires.
  KEEP THE `sha256` FIELD HONEST: the driver record carries `path` AND `sha256: sha256_file(Path(__file__))` beside it (`oc_runipd.py:3643`). A runner-less host has no module to digest, so state what it records there rather than leaving a field that silently becomes meaningless. ROUND 2 TRACED THE READERS so this is a bounded decision rather than an open migration: **no product code reads `driver.sha256` at all.** Its only reader in the repo is `tests/test_rununify_initialize_run_characterization.py:240-252`, so the field's fate is a test re-base decision, not a consumer migration, and it does not add a further file beyond the one below.
  **A NINTH FILE IS IN THE FENCE AND IT PINS EXACTLY WHAT THIS ITEM CHANGES (added round 2, PR-101).** `tests/test_rununify_initialize_run_characterization.py` asserts against BOTH hosts that `Path(state["driver"]["path"]).name == DRIVER_IDENTITY[name]["basename"]` (`:230-233`, docstring: "The load-bearing assertion. `__file__` must be evaluated in the RUNNER"), that `Path(state["driver"]["path"]) == module_file` and `state["driver"]["sha256"] == sha256_file(module_file)` (`:248-252`), and re-derives the basename at `:292`. Measured green before this work (`35 passed`). RE-BASE THOSE ASSERTIONS DELIBERATELY, under the maintainer's 2026-09-16 rule quoted in `orziju:287-296`: "re-base it on the code's new location, record what it now asserts, and prove it still catches the regression it was installed for ... WHAT REMAINS FORBIDDEN is WEAKENING a guard silently." So state what each assertion asserts AFTER the change and why it still catches host-unattributability; do NOT delete an assertion or loosen it to make the suite green.
  - Depends on: E-01
  - Expected outcome: a runner-less host is attributable by id, and an existing run record recorded before this change still resolves to its host rather than `unknown`. State per consumer WHICH mechanism was changed and how the fallback works, and show the re-based characterization test green with its new assertions stated. PRE-CUTOVER EVIDENCE COMES FROM THE TRACKED FIXTURES, NOT FROM A RUN CORPUS (corrected round 2, PR-102): `tests/test_run_analytics_sources.py:141-155` already holds real recorded shapes for `oc_runipd.py`, `runipd.py` and `ipdrunner.py`, and `:449` holds `agy_runipd.py`, matching all four `DRIVER_GENERATIONS` keys. Round 1 cited "181 run records across four basenames (160 / 13 / 5 / 2)"; that was measured on the MAINTAINER'S MACHINE and is NOT reproducible in a lane, because `.aw/records/runs/` is gitignored (`.aw/.gitignore:14`, "box-local, ephemeral working material; never committed") and absent from this checkout entirely. Use the tracked fixtures; do not synthesize a shape, and do not go looking for the corpus.
  - Execution state: pending

- [ ] E-03 Add a third host defined ONLY by a `HostLabels` instance plus the thinnest possible entry point, with NO new runner module, and drive one real IPD execution through it end to end. Use a scripted/dry-run host so the test needs no vendor CLI, credentials or spend. Record every place the attempt required a change to shared code.
  **STOP AND RECORD RATHER THAN BUILDING A RUNNER, IF THAT IS WHAT THE ATTEMPT DEMANDS.** The review's measurement predicts you will hit three walls in this order: no argv contract, no spawn seam, and nowhere to bind the nine label sites outside a runner module. If clearing a wall requires authoring a host-specific `run_<host>_turn`, that IS the finding: record it and go to E-04. Do NOT write a third runner module to make E-03 "succeed"; doing so would answer the plan's question NO while appearing to answer it YES, and it is the one outcome that would make this experiment worse than not running it.
  BOUND THE SHARED-CODE CHANGES YOU MAY MAKE. Adding a genuinely missing seam to `runner_shared.py` is in scope and is the point. Lifting one of the five large forked functions (`execute_item`, `run_queue`, `initialize_run`, `build_parser`, `main`) is NOT: they are out of this Set by design, and if the third host is blocked on one of them, that is an E-04 structural-limit gap and a strong argument for a future Set, not licence to split it here.
  - Depends on: E-02
  - Expected outcome: either a completed execution, or a precise failure list. **The failure list is the PREDICTED outcome, not a fallback.** Each required change to shared code is recorded with the reason, because that list IS the measurement of how good the seam is. Compare the result against the review's predicted three walls and say explicitly which ones you hit and which you did not; a wall the review predicted that did NOT materialize is as interesting as one that did.
  - Execution state: pending

- [ ] E-04 Classify each gap E-03 found as (a) a missing `HostLabels` field, (b) a genuine host CAPABILITY needing a switch rather than a label, or (c) a structural limit meaning the seam is insufficient as designed. For (c), state what a sufficient seam would look like; do not paper over it. **A FOURTH CLASS IS REQUIRED AND WAS MISSING: (d) BLOCKED ON THE REMAINING FORK,** i.e. the gap exists only because one of the five large functions is still per-host. That class must be separated from (c), because (c) says the DESIGN is wrong while (d) says the design is fine and the migration is unfinished, and those two conclusions point at completely different next steps. The review predicts the argv/spawn gaps land in (d) or (b), and the label-binding-site gap in (c).
  - Depends on: E-03
  - Expected outcome: a per-gap classification with a recommendation, using all FOUR classes. An empty gap list is a valid and excellent outcome, but must be stated as a measured result rather than an assumption, and given the review's measurement an empty list should be treated as a surprise requiring extra evidence rather than a clean pass.
  - Execution state: pending

### Task group 3: Make the answer durable

- [ ] E-05 Immortalize the host contract from E-01 and the gap analysis from E-04 to `.aw/records/research/` via `aw research new`, so the codex/claude/hermes work starts from a measured contract rather than re-deriving it.
  - Depends on: E-04
  - Expected outcome: a committed research record containing the enumerated contract, the third-host result, and the gap classification.
  - Execution state: pending

- [ ] E-06 Add `tests/test_hostdedup_third_host.py` keeping the third host alive as a PERMANENT guard, so a future change that reintroduces a host-specific assumption into shared code fails a test instead of being discovered by the next host integrator. Assert the third host needs no runner module, AND pin host attribution in BOTH directions per the OQ-02 ruling: a runner-less host attributes by id, and a pre-cutover path-only record still attributes correctly.
  **IF E-03 CONCLUDED THE SEAM IS INSUFFICIENT, THIS ITEM STILL HAS A DELIVERABLE, and it is not a passing third host.** Pin the LIMIT instead, in the inverse direction, exactly as `tests/test_rununify_lift.py` pins the symbols that must never move: assert that the third host gets as far as it currently can and NO FURTHER, with each blocking gap named and cited in the test. A guard that documents "a descriptor-only host reaches X and is blocked at Y by Z" is what stops the next integrator rediscovering Y, and it FAILS LOUDLY the day someone fixes Z, which is the signal this Set wants. Do NOT delete this item because the experiment found gaps, and do NOT weaken it into asserting only what already works.
  PIN BOTH ATTRIBUTION DIRECTIONS AGAINST REAL DATA, taken from the TRACKED fixtures (corrected round 2, PR-102): `tests/test_run_analytics_sources.py:141-155` and `:449` carry real recorded driver-path shapes for all four historical basenames, so the pre-cutover half needs no hand-built record and no access to `.aw/records/runs/`, which is gitignored and absent from every lane.
  - Depends on: E-05
  - Expected outcome: a guard proving the seam still admits a runner-less host as far as it does, which is the property Orders 01-03 exist to establish. If gaps remain, the guard pins the CURRENT boundary with each gap named, and is shown to fail when a gap is closed OR when a host-specific assumption is reintroduced into shared code.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `runner_shared.HostLabels` requires every field explicitly (NO DEFAULTS) so a missing value raises at
  construction rather than reading as empty. A third host must therefore supply all eight fields, which is
  exactly the enumeration E-01 needs.
- `HostLabels` models ONE capability flag (`emits_launch_identity`) alongside its strings, establishing the
  precedent that a genuine capability may be a switch rather than a label. E-03's classification uses that
  distinction.
- THE DRIVER-IDENTITY CONTRACT IS A REAL TRAP FOR A NEW HOST: `initialize_run` writes
  `state['driver']['path']` from `__file__`, and `run_analytics_sources.driver_generation` plus
  `run_viewer` key on its BASENAME to attribute a run to a host. A host with no runner module of its own
  has no natural basename, so E-01 must state what it supplies instead. `orziju` found both consumers
  would silently return `unknown` with no test failing.
- `aw host capabilities` already exists as the surface describing what a host can guarantee; a third host
  should be legible to it rather than bypassing it. MEASURED AT REVIEW, and it is better news than the note
  implies: the host list is `host_cmd.DEFAULT_HOSTS` (`host_cmd.py:37`, exactly
  `("opencode", "antigravity")`), and `host_sandbox_profile.detect_host_capabilities` is host-NAME driven
  with a SINGLE hardcoded `opencode` branch (`:838`), so an unrecognized third host already reports
  fail-closed capabilities rather than crashing. Making it legible is a ONE-TUPLE edit plus whatever probes
  it can honestly pass; `host_cmd.py` is now in the fence for that reason.
- SPEC `25kzda` IS ALREADY N-HOST, which the spec-sync section underestimates. Assurance A4 is "host
  asymmetry" ("A current per-host capability descriptor is mandatory ... fails closed, item-locally, when
  the chosen host cannot supply them"), there is a mandatory "Per-host capability descriptor" section
  stating "`oc` may support a capability that `agy` does not, or vice versa", and every action packet
  declares `required_host_capabilities`. A third host is contemplated by the spec, so E-03 is unlikely to
  need a spec amendment; if it finds a genuinely two-host-only assumption, THAT is the finding.
- `host_runner.run_worker_process` takes an INJECTABLE `runner` and `host_launchers`'s docstring says "No
  live models are launched in tests (doubles only)", which is F-6's precedent. NOTE THE LIMIT, so E-03 does
  not over-read it: `host_runner` is a DIFFERENT subsystem from the IPD driver, whose per-turn spawn is
  each runner's own `run_opencode` / `run_agy_turn`. The doubles precedent proves a scripted host is
  acceptable practice here; it does NOT supply a seam the IPD driver already honors.
- Durable analysis belongs in `.aw/records/research/` via `aw research new`, never hand-named (AGENTS.md).
- The execution contract forbids `git add -A` and pushing; commit only declared `Scope-Paths`.
- THE SUITE BASELINE, measured at review HEAD with `env -u AW_EXECUTION_ROLE`:
  `7975 passed, 3 skipped, 2 xfailed`. Take a baseline in the SAME tree before starting and gate on NO NEW
  failures; a managed worker lane refuses a set of lifecycle tests by design (backlog `770fkp`), so an
  absolute count from a different invocation form is not comparable.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | `HostLabels` exists and carries 8 host-varying values, with both instances bound by their host's wrappers | VERIFIED AT REVIEW at `runner_shared.py:9425` (authored as `:8530`, stale): exactly 8 fields, `_field_defaults` empty, both instances constructed and bound |
| F-2 | The descriptor has never been exercised by a host WITHOUT its own runner module, which is the actual N-host use case | both instances were extracted from pre-existing runners by `rununify` 04 (`tx6q0h`) |
| F-3 | Host-specific state is not confined to labels: `options` keys split 10 shared / 7 oc-only / 6 agy-only | RE-MEASURED AT REVIEW from the two `initialize_run` `options` literals and it reproduces: oc-only `agent`, `auto`, `launch_profile`, `no_audit`, `opencode`, `validate`, `variant`; agy-only `agy_executable`, `dangerously_skip_permissions`, `effort`, `new_session`, `no_verify`, `timeout` |
| F-4 | Driver identity is derived from `__file__` by two analytics consumers, so a runner-less host has no obvious identity | VERIFIED IN BOTH (re-verified round 2), and **THEY DO NOT AGREE ON THE MECHANISM**: `run_analytics_sources.py:206-207` takes `Path(raw).name` and looks it up in `DRIVER_GENERATIONS`, while `run_viewer.py:865-871` does SUBSTRING matching (`if "oc_runipd" in driver_path`) with a `Path(driver_path).stem` fallback. So E-02 is two different edits, not one repeated. The write site is `oc_runipd.py:3642` / `agy_runipd.py:2350` |
| F-4a | A THIRD reader exists and it is a TEST that pins the current identity, so E-02 must re-base it (found round 2, PR-101) | `tests/test_rununify_initialize_run_characterization.py:230-233` (basename, "The load-bearing assertion"), `:248-252` (`path == module_file` AND `sha256 == sha256_file(module_file)`), `:292` (basename again). Green at round 2 (`35 passed`). Now the ninth declared path |
| F-4b | `driver.sha256` has NO product consumer, closing a question round 1 left open (found round 2, PR-105) | measured across `agent_workflows/` and `tests/`: the only reader is the characterization test above, so what a runner-less host records there is a test re-base decision rather than a consumer migration |
| F-5 | The cost of an insufficient seam is measured in thousands of lines per host | RE-MEASURED AT ROUND 2 and unchanged: `oc_runipd.py` 9708 lines, `agy_runipd.py` 5887 (authored 9588/5784). `runner_shared.py` is now 10178, i.e. the shared module is already LARGER than either runner |
| F-6 | A vendor CLI is NOT needed to answer the structural question | VERIFIED: `host_launchers.py:17` states "No live models are launched in tests (doubles only)" and `host_runner.run_worker_process` takes an injectable `runner`. HONEST LIMIT ADDED AT REVIEW: `host_runner` is a DIFFERENT subsystem from the IPD driver, whose per-turn spawn is each runner's own `run_opencode`/`run_agy_turn`, so this is a precedent for the METHOD, not an existing seam |

### Findings added by the 2026-09-18 plan review

| id | sev | where | finding |
|---|---|---|---|
| F-7 | BLOCKER | `- Scope-Paths:` vs the maintainer's resolved OQ-02 | **THE FENCE MAKES E-02 UNEXECUTABLE, AND THE MISSING SET IS FIVE FILES.** OQ-02 is `Blocking: yes`, `Status: resolved` by the maintainer and commits the plan to four things; carrying them requires `run_analytics_sources.py`, `run_viewer.py`, BOTH runners' `initialize_run` (where `state['driver']['path']` is written from `__file__`) and `host_cmd.py` (so `aw host capabilities` can see a third host). The plan declared only `runner_shared.py`, one new test file and the research dir, while its gate says "commit only the declared `Scope-Paths`". This is the same defect the parent's review raised as PR-002 and it was never fixed in the child. All five added. |
| F-8 | HIGH | the plan's premise; `HostLabels` vs what a turn needs | **`HostLabels` MODELS NONE OF THE THREE THINGS A HOST NEEDS TO RUN A TURN.** It carries 8 strings and 1 flag. It does not model the ARGV (`[opencode, "run", "--dir", ...]` vs `[agy_bin, "-p", prompt, "--output-format", "stream-json", ...]`, zero overlap), the SPAWN function (`run_opencode` vs `run_agy_turn`, different signatures, each called by name from its own `execute_item`), or the 13 host-only `options` keys. So "add a descriptor plus a thin entry point" understates the work, and E-03's gap list is the PREDICTED outcome rather than the fallback. |
| F-9 | HIGH | the label binding sites | **A DESCRIPTOR-ONLY HOST HAS NOWHERE TO BIND ITS LABELS.** Measured: each runner contains NINE `HOST_LABELS` references, every one a call site inside the runner module passing `labels=` into a shared function. A host with no module has no home for those nine bindings, which is a STRUCTURAL gap (E-04 class (c)) rather than a missing field, and is the most likely first wall E-03 hits. |
| F-10 | MEDIUM | E-04's classification vocabulary | **THE FOUR-WAY DISTINCTION WAS A THREE-WAY ONE, AND THE MISSING CLASS IS THE MOST LIKELY.** A gap caused by one of the five still-forked large functions is neither a missing label nor a capability nor a design flaw: it is an UNFINISHED MIGRATION, and conflating it with (c) "the seam is insufficient as designed" would condemn a design that is actually fine. Class (d) added. |
| F-11 | MEDIUM | `## Spec / documentation sync` | **THE SPEC IS ALREADY N-HOST, so the section's premise is mostly wrong in the reassuring direction.** `25kzda` assurance A4 is "host asymmetry", it mandates a per-host capability descriptor explicitly contemplating that hosts differ, and each action packet declares `required_host_capabilities`. A spec amendment is therefore unlikely to be needed; if E-03 finds a genuine two-host-only assumption, that is a real finding rather than an expected one. |
| F-12 | MEDIUM | `## Proposed changes (ordered, validatable)` | **THE ORDERED LIST DOES NOT MATCH THE CHECKLIST IT SUMMARIZES.** It has five steps for six E-items, maps E-02 onto "add a third host and drive an execution" (which is E-03), labels the gap classification E-03 (it is E-04), the research record E-04 (E-05) and the permanent guard E-05 (E-06). An executor following the summary would perform the wrong item at every step after the first. |
| F-13 | LOW | `## Required tests / validation`; the Deferred section | The suite baseline was unstated ("bare and green" with no figure), and the Deferred section's cross-references inherited F-12's off-by-one (it cites "E-02 finds ... a finding for E-03" where the items are E-03 and E-04). Measured baseline: `7975 passed, 3 skipped, 2 xfailed`. |
| F-14 | LOW | provenance | The plan carried no `- From-Backlog:` while both siblings and the orchestrator carry `- From-Backlog: dstnso`, so this child's graduation link was invisible to `aw check` and to the close-legitimacy predicate. Added. (Round 2 re-verified: present, and all three siblings carry `dstnso`.) |

### Findings added by the 2026-09-18 plan review, ROUND 2 (an audit of round 1)

| id | sev | where | finding |
|---|---|---|---|
| F-15 | HIGH | `- Scope-Paths:` vs `tests/test_rununify_initialize_run_characterization.py` | **THE NINTH FILE: round 1 widened the fence for the identity work but missed the TEST THAT PINS THE IDENTITY.** Three assertion sites (`:230-233`, `:248-252`, `:292`) pin `driver.path` to the module basename and `driver.sha256` to that module's digest, against BOTH hosts. This is the same defect class round 1 raised as PR-001, one file further out. Fenced, and E-02 now specifies a deliberate re-base under the maintainer's 2026-09-16 rule rather than leaving an executor to guess. |
| F-16 | HIGH | E-02 / E-06 / required tests / V-02 vs `.aw/.gitignore:14` | **ROUND 1 REQUIRED EVIDENCE FROM A GITIGNORED, LANE-ABSENT CORPUS.** It measured 181 run records under `.aw/records/runs/` and made them mandatory ("must be used rather than synthesized"), but that tree is never committed and does not exist in this checkout, so the requirement was unsatisfiable in exactly the way round 1's own PR-001 was. Re-pointed at tracked fixtures (`tests/test_run_analytics_sources.py:141-155`, `:449`) which cover all four historical basenames, preserving round 1's correct intent that the evidence be real. |
| F-17 | MEDIUM | the `HostLabels` line anchors | **AN ANCHOR ROUND 1 FIXED HAS DRIFTED AGAIN, 9425 -> 9509 (84 lines).** `runner_shared.py` is now 10178 lines and grows weekly, so a bare line number there is a perishable citation; this is its third recorded value. Citation form changed to name the SYMBOL as authoritative with the line as a hint. |
| F-18 | LOW | the suite baseline | Round 1's baseline `7975 passed, 3 skipped, 2 xfailed` has drifted to `7993 passed, 3 skipped, 2 xfailed` (`env -u AW_EXECUTION_ROLE`, round 2 HEAD). Round 1's NO-NEW-FAILURES gate was the right construction and is unchanged; both figures are now recorded with their HEADs so a difference of 18 is not mistaken for a regression. |
| F-19 | MEDIUM | the typed review gate, across rounds | **ADVANCING TO ROUND 2 SILENTLY RELEASED ROUND 1's BLOCKER.** The gate reads only the CURRENT round by design (`check_engine.py:3161-3162`, so a finding fixed in round 2 stops blocking). Measured: `subject_gating_blocks(repo, "xdvglg")` returned round 1's PR-001 before round 2 was appended and `()` immediately after, with nothing resolved. PR-001 is therefore RESTATED in round 2 to keep it gating. Recorded here because it is a trap for every future re-review in this repo, not a defect in this plan. |

## Proposed changes (ordered, validatable)

**RENUMBERED AT REVIEW: this list was off by one against the checklist from step 2 onward (F-12), so an
executor following it would have performed the wrong item at every step.**

1. Derive the complete host contract from code, with a consumer cited per entry and each entry marked
   modelled / not-modelled by `HostLabels` (E-01).
2. Implement the maintainer's OQ-02 identity ruling across all five files it reaches, including the
   pre-cutover fallback in both analytics consumers (E-02).
3. Add a third host as a descriptor plus a thin entry point, no runner module, and drive a real execution
   through it, recording every shared-code change it forced (E-03).
4. Classify each gap as missing-label / genuine-capability / structural-limit / blocked-on-the-remaining-fork,
   with a recommendation (E-04).
5. Immortalize the contract and the gap analysis to `.aw/records/research/` (E-05).
6. Keep the third host, or its measured LIMIT, as a permanent guard (E-06).

## Deferred / out of scope (with reason)

- Integrating a REAL codex / claude / hermes host is out of scope. This plan establishes the seam is
  sufficient; each real host is its own work with its own vendor specifics, spend and credentials.
- The five large functions remain forked; a third host that needs them will reach them through whatever
  wrappers exist. If E-03 finds that the remaining fork BLOCKS a third host, that is an E-04 class (d)
  finding and a strong argument for resolving those five, not licence to split them here. **(Item numbers
  corrected at review, F-12.) THE REVIEW PREDICTS THIS WILL HAPPEN**: the driver identity is written inside
  the forked `initialize_run` and the spawn is each host's own function, so at least two of E-03's expected
  gaps land in class (d).
- No new public `aw` verb for host registration. If E-04 concludes one is needed, it recommends it.
- CHANGING `run_analytics_sources.DRIVER_GENERATIONS` INTO A DYNAMIC REGISTRY is out of scope. The table is
  four historical basenames and the corpus depends on all four resolving (measured: 160 + 13 + 5 + 2 records);
  E-02 adds an id path with a fallback to that table, it does not replace it.

## Scope check

- Over-scope: none. Every item serves the single question of whether a host can be added without a runner.
- Under-scope: this plan does not deliver a usable third AI host, only the proof that the seam admits one.
  That is deliberate: the structural question is answerable without vendor dependencies, and coupling it to
  one would make the answer hostage to an unrelated integration.

## Required tests / validation

- `python3 -m pytest` bare with the summary line pasted, compared against a baseline taken in the SAME
  tree, gating on NO NEW failures. BASELINES, both with `env -u AW_EXECUTION_ROLE`: round 1 measured
  `7975 passed, 3 skipped, 2 xfailed`; round 2 measured `7993 passed, 3 skipped, 2 xfailed` at HEAD
  `a01c82ba`. THE PASS TOTAL DRIFTS UPWARD as the suite grows (18 between two HEADs a day apart), so it is
  NOT the invariant: the NO-NEW-FAILURES comparison against a baseline you take yourself in the same tree
  is. A managed worker lane refuses a set of lifecycle tests by design (backlog `770fkp`), so state the
  invocation form.
- `python3 -m pytest tests/test_rununify_initialize_run_characterization.py` green AFTER E-02's re-base,
  with each re-based assertion's new meaning stated (round 2, PR-101). It is `35 passed` before this work.
- Evidence the third host got as far as it got, with its run record showing correct host attribution rather
  than `unknown` (F-4's trap). **A COMPLETED EXECUTION IS NOT REQUIRED**: per E-03, a documented wall is the
  predicted and acceptable result, and the required evidence is then the wall plus its citation rather than
  a green end-to-end run.
- BOTH analytics consumers exercised SEPARATELY, since they use different mechanisms (F-4): a basename
  lookup in `run_analytics_sources` and substring matching in `run_viewer`.
- A PRE-CUTOVER record shown still attributing correctly, taken from the TRACKED fixtures that already carry
  real recorded shapes for all four historical basenames (`tests/test_run_analytics_sources.py:141-155` for
  `oc_runipd.py`/`runipd.py`/`ipdrunner.py`, `:449` for `agy_runipd.py`) rather than synthesized. CORRECTED
  AT ROUND 2: round 1 required this from `.aw/records/runs/`, which is gitignored (`.aw/.gitignore:14`) and
  absent from every lane, so that requirement could not be met by an executor.
- The explicit list of shared-code changes the third host required, or a statement that it required none,
  compared against the review's three predicted walls (argv, spawn, label-binding sites).
- `aw host capabilities` shown reporting the third host, since E-01's own convention note requires it be
  legible to that surface rather than bypassing it.
- `tests/test_hostdedup_third_host.py` green, and shown to FAIL if a host-specific assumption is
  reintroduced into shared code OR, where the guard pins a measured LIMIT instead, shown to fail when that
  limit is lifted.

## Spec / documentation sync

No `.spec.md` is declared, and VERIFIED AT REVIEW that none is needed: **spec `25kzda` is already written
for N hosts, not two.** Its assurance A4 is "host asymmetry" ("A current per-host capability descriptor is
mandatory. Each action declares required enforcement capabilities and fails closed, item-locally, when the
chosen host cannot supply them"), it carries a mandatory "Per-host capability descriptor" section whose text
says "`oc` may support a capability that `agy` does not, or vice versa; the descriptor controls the decision
for the current installation", and every action packet declares `required_host_capabilities`. So a third host
is contemplated by the contract rather than excluded by it. If E-03 finds a genuine exactly-two-hosts
assumption anywhere, record it as a finding and file a spec amendment separately rather than editing a
shipped contract inside an experiment; do NOT go looking for one on the assumption that it must exist.
Backlog `xdgorn` (open) notes the spec is silent on the per-host VERIFICATION FLAG asymmetry (`--no-verify`
means different things on the two hosts, defended in code by
`agy_runipd.assert_verification_flags_are_distinct`), which is a real documentation gap but is about FLAGS
rather than about host count, and it is `xdgorn`'s to close, not this plan's.

## Open questions

### OQ-01: Should the third host be a real vendor CLI or a scripted double?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A SCRIPTED/DRY-RUN HOST. The question this plan answers is structural
  (can a host exist without a runner module), and a scripted host exercises every seam the runners touch
  while needing no credentials, no vendor CLI and no spend. The repository already establishes this pattern:
  `host_runner` takes an injectable runner and `host_launchers`' own docstring records "No live models are
  launched in tests (doubles only)". Using a real vendor host would make a structural result hostage to an
  unrelated integration, and would not strengthen the finding.

### OQ-02: What identity does a host with no runner module report as its driver?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-17: THE DESCRIPTOR CARRIES AN
  EXPLICIT HOST ID, and a run records that identity rather than deriving it from a module filename. The
  question was put to the maintainer with three alternatives priced (explicit id; a per-host identity-only
  stub module; recording both during a transition) and this was chosen directly.

  WHY IT WAS THE MAINTAINER'S CALL, not an executor's: `state['driver']['path']` reaches PERMANENT run
  records, and `run_analytics_sources.driver_generation` plus `run_viewer` currently attribute a run to a
  host by string-matching the BASENAME of that path. Changing what the field means changes durable history
  and the analytics that read it.

  WHAT THIS COMMITS THE SET TO, and E-01/E-02 must carry all four. (1) `HostLabels` gains an explicit host
  id field, justified by named consumers exactly as every other field is. (2) The two analytics consumers
  read the ID rather than the basename, so a runner-less host is attributable. (3) HISTORICAL RECORDS STILL
  HOLD PATHS and must keep resolving: existing runs recorded `oc_runipd.py` / `agy_runipd.py` and cannot be
  rewritten, so the consumers need a documented fallback from id to basename for pre-cutover records. This
  is the part most likely to be missed and it must not be. (4) The identity must be pinned by a test in BOTH
  directions: a runner-less host attributes correctly, and a pre-cutover record still attributes correctly.
  The rejected stub-module option is recorded here so a later reader knows it was considered and why it lost:
  it would have preserved both consumers with zero migration, at the cost of conceding one module per host
  forever, which is the very shape this Set exists to eliminate.

### OQ-03: E-02's identity ruling must edit both forked `initialize_run`s. Is that in scope for this Set, or does it wait for the fork to be resolved?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-001 (dispositioned FIXED)
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-18: The premise of the fork conflict
  was superseded by the maintainer's direct instruction to unify `initialize_run` across `oc_runipd.py` and
  `agy_runipd.py` into `runner_shared.initialize_run_core` (performed and committed at `7a28ed11`). The driver
  identity write `state['driver']` now sits centrally in `runner_shared.py` (line 10433), parameterized by
  caller, so the write is unified rather than duplicated across two forked 400-line functions. Both runner
  wrappers pass their own module path as `driver_path`, and a runner-less host supplies its own identity
  directly to `initialize_run_core`. PR-001 is DISCHARGED/FIXED. Tests characterization will be re-based
  deliberately per maintainer ruling.

  ROUND 1 AND 2 CONTEXT (KEPT FOR HISTORY): RAISED AT REVIEW 2026-09-18 and originally BLOCKING, because the maintainer's own
  resolved OQ-02 commits this plan to an edit the Set's own boundary appears to forbid, and only the
  maintainer can say which of the two wins. THE FACTS, measured: `state['driver']['path']` is written as
  `str(Path(__file__).resolve())` at `oc_runipd.py:3641-3643` AND `agy_runipd.py:2349-2351`, both inside
  `initialize_run`, which is ONE OF THE FIVE LARGE FUNCTIONS this Set deliberately leaves forked (446 oc /
  353 agy raw lines; the orchestrator's OQ-01 defers their fate to a maintainer decision about five already
  approved `rununify` plans). So carrying commitment (1) of OQ-02 means editing the same identity write in
  TWO forked functions, in a plan whose Scope says it adds a host "without adding a runner module" and
  whose sibling plans explicitly do not touch those five.
  THE OPTIONS. (a) ALLOW IT, narrowly: this plan edits both `initialize_run`s at the identity write only,
  declaring both runners in its fence (which the review has now done) and changing nothing else in those
  functions. Cheapest, and the review's recommendation, since a two-line-equivalent change in each host is
  not the "split the large function" work the Set defers. (b) DEFER E-02 until the five large functions are
  resolved, which makes this plan's identity half wait on a decision the orchestrator's OQ-01 has not yet
  had, and leaves the third host unattributable in the meantime. (c) RECORD THE IDENTITY SOMEWHERE ELSE
  entirely (a sibling field written by shared code that `initialize_run` already calls), which avoids the
  forked functions but invents a second identity location and needs its own design.
  WHY I DID NOT DECIDE IT: (a) crosses a Set boundary the maintainer drew, (b) reorders the Set, and (c)
  designs a new durable field. All three are the maintainer's. What I DID do is make (a) executable if
  chosen: both runners are now in the fence, E-02 names the exact write sites, and it carries an explicit
  prohibition on lifting `initialize_run` to make the change "once".

  ROUND 2 ADDENDUM (2026-09-18), because the maintainer should decide with this in view and round 1 did not
  cite it. THERE IS AN EXISTING MAINTAINER DIRECTIVE THAT POINTS TOWARD OPTION (a) WITHOUT SETTLING IT. On
  2026-09-16 the maintainer resolved the blocking OQ-03 of `rununify` plan `orziju` (which owned
  `initialize_run`) with "ROUTE (A) AS THE OBJECTIVE ... So DO THE SPLIT", under the Set-wide directive that
  "at the end of the SET, there should be one code base shared by the two runners that contains 100% of the
  otherwise redundant code that currently is duplicated between the two runners"
  (`.aw/records/plans/executed/20260915-rununify-09-orziju-...ipd.md:280-285`). That ruling also established
  the two sub-rules this plan now relies on: TESTS ARE NOT IMMOVABLE (re-base deliberately, never weaken
  silently) and coordinated de-duplication is permitted.
  WHY THAT DOES NOT AUTOMATICALLY ANSWER THIS QUESTION, and why round 2 still left it open: the directive was
  given to the `rununify` Set about SPLITTING those five functions, whereas this question asks whether
  `hostdedup`, a Set that explicitly EXCLUDES them, may make a narrow edit INSIDE one. Those are different
  questions, and this Set's own orchestrator records the five functions' fate as STILL an open maintainer
  question with three unchosen routes (`a5wdne:237-258`, `Status: open`), marked `Blocking: no` there only
  because that Set "proceeds on the other 29 symbols either way". So the authority is genuinely unsettled and
  the boundary call remains the maintainer's.
  ROUND 2 ALSO WIDENED WHAT OPTION (a) COSTS, which is the other thing worth knowing before ruling: the
  identity is pinned by `tests/test_rununify_initialize_run_characterization.py` in three places against both
  hosts, so option (a) is "edit two forked write sites AND deliberately re-base three assertions", not a
  two-line change. That is still far short of splitting a 446-line function, so it does not change round 2's
  agreement with round 1's recommendation, but it should be priced honestly.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the enumerated host contract, each entry citing the consumer that reads it AND marked
    modelled / not-modelled by `HostLabels`, explicitly covering the 8 `HostLabels` fields, the 13
    host-specific `options` keys, the ARGV construction, the SPAWN signature, the driver-identity contract,
    and the nine per-host label BINDING SITES. A contract with an entry whose consumer is not named fails
    this item, and so does one that omits the argv/spawn rows: those are the entries that decide whether the
    plan's premise holds, and the review measured them as unmodelled.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the host-id field with its named consumers; evidence a runner-less host attributes by
    id; AND evidence a PRE-CUTOVER run record (one holding only a module path, taken from an existing run in
    the TRACKED fixtures at `tests/test_run_analytics_sources.py:141-155` and `:449`, NOT from
    `.aw/records/runs/` which is gitignored and absent from every lane) still attributes to its host rather
    than `unknown`. The historical case is the one most likely to be skipped, so a verdict without it fails
    this item. BOTH consumers must be shown SEPARATELY, because they use different mechanisms
    (`DRIVER_GENERATIONS[basename]` versus substring matching with a `stem` fallback); evidence from one does
    not cover the other. State what the runner-less host records in the `sha256` field beside `path`, since
    it has no module to digest; round 2 measured that NO product code reads that field and its only reader is
    the characterization test, so say what that test asserts about it afterwards. SHOW THE RE-BASED
    CHARACTERIZATION TEST GREEN (`tests/test_rununify_initialize_run_characterization.py`, `35 passed`
    before this work) with each of its three identity assertions' new meaning stated, and confirm none was
    deleted or loosened; a green suite achieved by removing an assertion fails this item. If OQ-03 resolved
    to option (a), show the identity write changed in BOTH forked `initialize_run`s and NOTHING ELSE in those
    functions changed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the third host's run record showing correct host attribution (NOT `unknown`), plus
    the complete list of shared-code changes the attempt required, or an explicit statement that it required
    none. Confirm no new runner module was added: that is the plan's central claim and a third
    `*_runipd.py`-shaped module would answer the question NO while appearing to answer it YES. A DOCUMENTED
    WALL SATISFIES THIS ITEM; a completed end-to-end execution is not required. Compare the result against
    the review's three predicted walls (no argv contract, no spawn seam, nowhere to bind the nine label
    sites) and state which materialized.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the per-gap classification with a recommendation for each, using all FOUR classes
    (missing label / genuine capability / structural limit / blocked on the remaining fork), or an explicit
    "no gaps found" stated as a measured result. Any structural-limit gap must say what a sufficient seam
    looks like. A class-(c) verdict on a gap that is really class (d) fails this item: the review predicts
    the argv and spawn gaps are unfinished-migration rather than design failures, and the distinction decides
    whether the recommendation is "redesign the seam" or "finish the five".
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the committed research record path, containing the contract and the gap analysis.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest tests/test_hostdedup_third_host.py` green, AND shown to fail when
    a host-specific assumption is reintroduced into shared code (make the edit, paste the failure, revert) or,
    where the guard pins a measured LIMIT, when that limit is lifted. A guard never seen red is untested.
    Where gaps remain, show the guard NAMES each one with its citation, so the next integrator meets the
    boundary in a test rather than rediscovering it. Plus `python3 -m pytest` bare with the summary line
    pasted, the invocation form stated, and a same-tree baseline beside it (review baseline
    `7975 passed, 3 skipped, 2 xfailed`), gating on NO NEW failures. Also paste `aw host capabilities`
    showing the third host, since a host the capability surface cannot see is not integrated.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (6 E-items in 3 task groups, under the 18-leaf / 5-group thresholds).

This plan requires explicit human approval before execution. OQ-02 (the driver identity of a runner-less
host) is RESOLVED by the maintainer and its four commitments are binding on E-01/E-02; an executor must not
re-open it. **BUT DO NOT EXECUTE UNTIL OQ-03 IS ANSWERED**: carrying OQ-02's first commitment requires
editing the `__file__`-derived identity write inside BOTH forked `initialize_run`s, which are two of the five
large functions this Set deliberately leaves alone, so the maintainer must say whether that narrow edit is
in scope (the review's recommendation), whether E-02 waits for the fork to be resolved, or whether the
identity belongs somewhere else entirely. That is a Set-boundary call, not an executor's.

EXECUTION CONTRACT. OQ-01 and OQ-02 are RESOLVED; execute their recorded answers. THE TWO THINGS THIS PLAN
MUST NOT DO, both stated because each is a plausible shortcut to an apparently-successful result. FIRST, do
NOT write a third runner module, or anything shaped like one, to make E-03 "pass": the plan's whole question
is whether a host can exist without one, and answering it by writing one inverts the result while hiding the
inversion. SECOND, do NOT lift `initialize_run` (or any of the five large forked functions) to make the
identity change once instead of twice: that work is deferred by the Set and by the orchestrator's OQ-01. A
gap you cannot close is a FINDING, and E-04 has a class for each kind; a plan that reports "the seam is
insufficient, here is exactly how, in four classified gaps" has SUCCEEDED.

SCOPE FENCE: this plan declares NINE paths: three authored, five added at review round 1 because the
maintainer's resolved OQ-02 reaches them, and a ninth added at round 2
(`tests/test_rununify_initialize_run_characterization.py`, which pins the very identity E-02 changes).
An out-of-scope edit that is genuinely required must be MADE and then JUSTIFIED to
`aw ipd finalize` with a `--scope-reason` per path, and a declared-but-unmodified path needs a
`--scope-ack`; do not stop over a scope question. DO stop on a genuinely unsafe condition: `nmlx47`'s
symbols absent because Order 02 has not executed, or an unresolvable concurrent edit in this SHARED
CHECKOUT (roughly 33 other pending plans declare these runner files).

HARD-MUST HONESTY RULE: paste the ACTUAL command output for every `V-*`. State the suite invocation form and
put a same-tree PRE-work baseline beside the post-work run (review baseline `7975 passed, 3 skipped, 2
xfailed`), gating on NO NEW failures rather than an absolute count. Never claim a test passed that you did
not run, and never report a wall as cleared without the evidence that cleared it.

Work in an isolated worktree. Commit path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never
push, never tag. Before every commit run `git diff --cached --name-only` and unstage anything that is not
yours with `git restore --staged <path>`; re-verify after any failed hook.

Post-gate lifecycle: the finalize obligation is unconditional, but its OWNER is conditional. Under
`aw oc run` / `aw agy run` the RUNNER owns `aw ipd begin` and `aw ipd finalize`; a hand-executed run means
the executor runs `aw ipd finalize` itself. Either way the plan reaches `.aw/records/plans/executed/` only
after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence. Never
hand-roll a `git mv` to `executed/`. A finding of "the seam is insufficient, here is how" is a SUCCESSFUL
outcome, provided E-04 classifies each gap into one of its four classes; it does not require the third host
to work.
