# Review findings: plan lhjsu0

- Subject-Id: lhjsu0
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a631a1f6` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review; `--phase review-finalize` conforms after
revision. Nothing below is structural.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests
entirely on RUNNING the claims rather than re-reading them. It found one BLOCKER the author did not know
existed and two authored claims that are FALSE.

### What re-measured TRUE

F-1, F-2 and F-4 all hold. The `.pth` is a single line naming the main checkout, and the resolution flip
is real:

```text
cwd = lane ROOT        python3 -c  'import agent_workflows' -> LANE
cwd = lane tests/      python3 -c                           -> MAIN
cwd = lane ROOT        python3 -P -c   (no cwd path entry)  -> MAIN
console-script shape   (sys.path[0] = <venv>/bin)           -> MAIN
```

F-4 was UPGRADED from "to be confirmed by E-01" to measured, by reproducing the unpinned fixture shape
exactly (spawn with `cwd` = a temp repo, no `PYTHONPATH`):

```text
UNPINNED fixture shape (cwd=tmp repo, no PYTHONPATH) -> MAIN | <main>/agent_workflows/__init__.py
PINNED   fixture shape (PYTHONPATH=tree root)        -> LANE | <lane>/agent_workflows/__init__.py
```

and by quantifying the population: **59** `-m agent_workflows` subprocess launches across **26** test
files, **15** of which never mention `PYTHONPATH` at all. Also measured, and material to E-03's size:
there is **no shared spawn helper today** (`tests/support.py` spawns `git`, the installer and arbitrary
tools, but never `-m agent_workflows`), while **four** files already implement the correct pattern
(`test_awnaming_grammar_and_producers._run_cli` even documents the reasoning), so E-03's real work is
INTRODUCING the helper and migrating, not fixing one.

### THE BLOCKER: the plan is unaware of the shipped pin it would fight

Executed plan `af7i6p` (`lanetruth` Order 01) pins nested control-plane `aw` to the DRIVER's tree ON
PURPOSE. Its scope says so in terms: "Excludes the host-agent `Popen` (the agent turn SHOULD run in the
lane)". That pin is why THIS turn's environment carries:

```text
AW_PIN_KEEP_ROOT=<main checkout>
PYTHONPATH=<main checkout>:<...>
```

The plan cites `af7i6p` nowhere, and its RECOMMENDED OQ-01 candidate (a) reintroduces it. Measured with
the SHIPPED `_AW_PIN_PROBE`, under the env candidate (a) would produce (lane prepended to `PYTHONPATH`,
`AW_PIN_KEEP_ROOT` = the driver's own root):

```text
cwd = lane ROOT   (== the PYTHONPATH entry) -> MAIN (pin held)
cwd = lane SUBDIR (!= the entry)           -> LANE  <-- af7i6p REINTRODUCED
```

And the shipped guard cannot see it, because it is a membership test with no ORDER component:

```text
tests/test_lane_permission_posture.py
  assert oc_runipd.runner_package_root() in env["PYTHONPATH"].split(":")
# with PYTHONPATH = <lane>:<main>, this PASSES while the pin is defeated.
```

So the two properties are in TENSION and both are wanted: a CONTROL-PLANE `aw` must resolve the driver's
tree (or an unreviewed mid-edit lane executes the lifecycle meant to gate it, `af7i6p` F4), while an
EVIDENCE `aw` must resolve the lane's. Approved spec `7ckptx` A8 pins the control-plane half
("inherited PATH and the import pin survive"). `tests/test_lane_tool_identity.py`: `23 passed in 3.56s`.

### TWO AUTHORED CLAIMS ARE FALSE

```text
# F-9: the "fixed interpreter shebang" is not a mechanism
head -1 "$(command -v aw)"  ->  #!<venv>/bin/python3
command -v python3          ->  <venv>/bin/python3        # THE SAME INTERPRETER
# The real variable is the ABSENCE of a cwd sys.path entry, which -P reproduces.

# F-3: the selectors crash does NOT show "two trees in one interpreter"
# control 1: force ONE tree (PYTHONPATH=<lane>), cwd=<lane>/agent_workflows -> SAME crash
# control 2: temp dir containing ONLY a 3-line decoy selectors.py, `import subprocess`,
#            no agent_workflows import at all                               -> SAME crash
AttributeError: module 'selectors' has no attribute 'SelectSelector'
```

F-7 is a reading, not a measurement, and it is decisive: the installed console script's entire body is
`from agent_workflows.cli import main`, so the package is fully imported before any in-package line runs.
OQ-01 candidate (b) ("tree-relative resolution inside the console entry point") cannot be implemented as
described.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | C (architecture); D (anti-regression) | `af7i6p` Scope ("Excludes the host-agent `Popen`"); live turn env `PYTHONPATH`/`AW_PIN_KEEP_ROOT` = main; `_AW_PIN_PROBE` with the lane prepended -> LANE from a subdir, MAIN from the root; `tests/test_lane_permission_posture.py` `... in env["PYTHONPATH"].split(":")` passing meanwhile | THE PLAN NEVER MENTIONS `af7i6p`, WHOSE PIN IT WOULD REGRESS, AND ITS RECOMMENDED CANDIDATE DOES REGRESS IT. Control-plane `aw` is deliberately pinned to the driver's tree (spec `7ckptx` A8, guard `test_lane_tool_identity.py`). OQ-01 candidate (a) prepends the lane to `PYTHONPATH`, which measurably flips a nested control-plane launch from a lane SUBDIRECTORY to the LANE, while the order-blind shipped assertion stays green. A fix that does not distinguish the two callers by name either regresses `af7i6p` or leaves this defect live. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as plan F-6 and F-10. Concern, Goal and Scope rewritten around the two-caller distinction; `af7i6p` non-regression made a HARD GATE in E-02 requiring BOTH the shipped tests and a BEHAVIORAL subdirectory probe (because membership is not order); E-01 must read `af7i6p` and produce a caller list before E-02 is executable; E-04 must assert BOTH directions and must not assert `PYTHONPATH` membership; relaxing the pin added to Scope OUT, the scope check as a STOP, Deferred, and the gate. |
| PR-002 | HIGH | IN-SCOPE | F (honest documentation); G (plan executability) | `head -1 "$(command -v aw)"` == `command -v python3`; `python3 -P -c` from the lane root -> MAIN while plain `python3 -c` -> LANE | THE AUTHORED "TWO MECHANISMS" ARE ONE, AND THE SECOND IS A FICTION. The plan instructs E-01 to "RECORD THE TWO MECHANISMS SEPARATELY, because they need different fixes", naming the console script's "FIXED interpreter shebang". The shebang names the SAME interpreter `python3` already resolves to, so it explains nothing. The real second variable is the ABSENCE of a cwd `sys.path` entry. An executor would hunt a mechanism that does not exist and could conclude the fix must change the interpreter. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as plan F-9. Concern corrected to state ONE selecting mechanism with two exposure shapes; E-01 now requires the shebang story be actively DISPROVED with pasted output (or shown to hold if the executor's environment genuinely differs); the four-case table's "neutral cwd" leg replaced by the `-P` cwd-suppressed leg, which is the one that actually discriminates. |
| PR-003 | HIGH | IN-SCOPE | A (correctness of the plan's own evidence) | control with `PYTHONPATH=<lane>` (one tree) -> same crash; control with a temp dir holding only a decoy `selectors.py` and no `agent_workflows` import -> same crash | THE STDLIB-SHADOW CRASH IS NOT EVIDENCE OF THE PLAN'S THESIS. The plan calls it "a stronger statement than 'the wrong tree wins'" and E-01 requires reproducing it "since it proves two trees can execute in one interpreter". It proves nothing of the kind: it is a single-tree shadow, reproducible with one tree and with no `agent_workflows` involved. Leaving it as HIGH supporting evidence invites an executor to "confirm" the thesis with an observation that is true whether or not the thesis is. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as plan F-3, DOWNGRADED HIGH -> LOW and reclassified as a real but separate single-tree hazard. E-01 now forbids citing it as two-tree evidence and requires the single-tree CONTROL if it is mentioned at all. Renaming `selectors.py` added to Scope OUT and Deferred with its reason (wider blast radius, own item). Conventions bullet corrected. |
| PR-004 | HIGH | IN-SCOPE | C (architecture); G (plan executability) | the installed `aw` script body: 4 lines, `from agent_workflows.cli import main` | OQ-01'S CANDIDATE (b) IS IMPOSSIBLE AS AUTHORED, AND IT IS THE ONE THE PLAN RECOMMENDS MEASURING FIRST. "A tree-relative resolution inside the console entry point" cannot exist: the package is fully imported by the script's only import statement before any of our code can run. Any fix at that layer must live OUTSIDE the package (`sitecustomize`, a `.pth`, or a wrapper script), which is a materially riskier packaging change than the plan implies. So the plan's primary recommendation would burn the turn discovering it is unbuildable. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as plan F-7. OQ-01 rewritten: (a) REJECTED as authored on the PR-001 measurement (with the narrower separate-variable variant left open), (b) marked IMPOSSIBLE as authored with the outside-the-package variants named, (c) re-assessed as the STRONGEST of the three on the non-regression criterion, and a NEW candidate (d) (lane-local wrapper on `PATH`) added because it cannot touch the pin by construction. Recommendation changed to evaluate (c) and (d) first. E-02 names both known-bad candidates so the turn is not spent rediscovering them. |
| PR-005 | HIGH | UNDER-SCOPE | G (plan executability); F (honest documentation) | plan `- Scope-Paths:` (three test-side files); E-02's "from ANY cwd within it" | THE DECLARED SCOPE CANNOT HOLD THE STATED FIX, AND THE PLAN TREATS THIS AS A LATENT RISK RATHER THAN A CERTAINTY. `- Scope-Paths:` names only `tests/test_lane_import_root.py`, `tests/support.py`, `conftest.py`, while E-02 promises `aw` resolves the invoking tree "from ANY cwd within it" - which no test-side file can deliver for any of candidates (b), (c) or (d). The author recorded this as a deliberate deferral pending OQ-01, but left a promise no declared path can keep, so the plan cannot terminate honestly. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as plan F-8. E-02 now states the two honest exits explicitly (declare the production/packaging path, or NARROW the promise and record that) and forbids choosing neither; the scope check names this as a certainty rather than a risk and adds `runner_shared.py` to the candidate widening list; V-02 requires either the added path with its reason or the recorded narrowing. |
| PR-006 | MEDIUM | UNDER-SCOPE | E (testing); C (architecture) | no `-m agent_workflows` spawn in `tests/support.py`; 59 launches / 26 files / 15 unpinned; `test_awnaming_grammar_and_producers._run_cli` and three siblings already pinning | E-03 IS MIS-SIZED BECAUSE THE HELPER IT ASSUMES DOES NOT EXIST. E-03 says "FIND THE SHARED SPAWN HELPER FIRST and fix it once. `tests/support.py` is the likely home". There is no such helper: every one of the 26 files builds its own `subprocess.run`, so the work is INTRODUCING a helper plus migrating up to 15 files, which may exceed one focused pass. The plan also does not notice that four files already solve this correctly and are the pattern to lift, nor that `test_lane_tool_identity.py` must NOT be migrated (its whole subject is that a child must not resolve the cwd's tree, so a blanket pin would invert the property it guards). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 rewritten: states no helper exists, names the four existing correct implementations and `support.REPO_ROOT` as the seam to lift, permits landing the helper plus a NAMED subset with a carrier for the remainder (while forbidding silent partial migration), and explicitly excludes `test_lane_tool_identity.py` with the reason. V-03 requires the helper symbol, the migrated and deferred lists, the carrier id, and that exclusion. |
| PR-007 | MEDIUM | UNDER-SCOPE | E (testing); D (anti-regression) | `af7i6p` E-01's floor measurement (`PYTHONSAFEPATH=1` SILENTLY IGNORED on CPython 3.9); `pyproject.toml` `requires-python = ">=3.9"`; CI matrix 3.9-3.14 | THE DECLARED PYTHON FLOOR IS NEVER MENTIONED, THOUGH IT ALREADY INVALIDATED ONE FIX FOR THIS EXACT PROBLEM. The suppressing half of any `sys.path` fix has no pre-3.11 spelling: `-P` and `PYTHONSAFEPATH` are both 3.11 features, and `af7i6p`'s review measured `PYTHONSAFEPATH=1` silently ignored on a real 3.9. A flag-based mechanism would be green on this machine and INERT on 3.9/3.10 - the same false-evidence shape this plan exists to remove - and no validation item would have caught it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required tests now demand the mechanism's floor behavior be stated when it touches interpreter flags, citing `af7i6p`'s 3.9 measurement; the conventions section records the floor and names the runner's `-P`-plus-`-c`-bootstrap as the in-tree reference for a version-uniform suppression. |
| PR-008 | MEDIUM | UNDER-SCOPE | E (testing); G (plan executability) | `af7i6p` review PR-207 (the live lane set grew from two to three mid-review, forcing a synthetic fixture); `test_lane_tool_identity.py`'s three-package fixture | E-04's GUARD WOULD LIKELY BE WRITTEN AGAINST LIVE LANES, WHICH ARE UNSTABLE, AND ITS COUNTS WERE STATED AS AUTHORED FACTS. `af7i6p` hit exactly this: its live lane set changed during review and the plan had to forbid asserting on live lanes. The plan also stated its resolution table and call-site figures as authored measurements without requiring re-derivation, though both are properties of a drifting environment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires a SYNTHETIC two-copy fixture (citing the three-copy precedent) and forbids asserting against `.aw/worktrees/`; E-01 and V-01 require the four-case table and the call-site counts be RE-DERIVED rather than copied, with the review numbers kept only as context. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is PR-001 a finding against THIS plan, or a separate item? | Against this plan. The two-caller distinction is written into the Concern, Goal, Scope, E-01, E-02, E-04, the scope check, Deferred and the gate, and `af7i6p` non-regression is made a hard gate on E-02. | Filing a separate backlog item: rejected because the plan's RECOMMENDED mechanism is the thing that regresses `af7i6p`, so a reader could execute the plan as written and re-open an executed release-blocking defect before any separate item was ever read. A finding that only lands somewhere else does not protect this plan's executor. | `af7i6p` Scope and F4; spec `7ckptx` A8; the `_AW_PIN_PROBE` subdirectory measurement | yes |
| D-2 | Should OQ-01 be RESOLVED at review, as the sibling `hv9gar` review resolved its OQ-01 from an audit? | No. Left OPEN and `Blocking: no`, but re-scoped: two candidates rejected/impossible by measurement, a fourth added, and the recommendation reversed to (c)/(d). | RESOLVING it here: rejected because the repository does NOT answer it. `hv9gar`'s OQ-01 was resolvable because an exhaustive call-site audit settled the one precondition; here the remaining candidates each need a judgement the repo cannot supply - (c) accepts per-lane install state the runner creates constantly, (d) adds a `PATH` shim, and any outside-the-package variant of (b) is a packaging change. Those are cost/risk-appetite calls the maintainer owns. Eliminating the bad options is what evidence CAN do, so that is what was done. | `plan-review.md` Step 3.1 (resolve from evidence, never guess a human decision); the measurements rejecting (a) and (b) | yes |
| D-3 | Does leaving OQ-01 open make the plan `NO-GO`? | No. It is `Blocking: no`, so per the 2026-09-10 maintainer ruling it does not gate readiness. | Marking it `Blocking: yes`: rejected because E-03 (the whole test-harness half, covering `ccbe60`) is independently executable and independently valuable with OQ-01 unanswered, and E-02 now carries a hard non-regression gate that makes a wrong mechanism fail loudly rather than ship. Flipping it would hold a plan whose author correctly judged it non-stopping, which is exactly what the ruling corrected. | `plan-review.md` "Verdict and readiness" (2026-09-10 ruling, plan `qhy3i3` OQ-01); the plan's own `- Blocking: no` | yes |
| D-4 | Should F-3 be RETRACTED rather than downgraded, since it does not support the thesis? | Downgraded to LOW and kept, reclassified as a genuine single-tree hazard, with citation-as-evidence explicitly barred. | Deleting it: rejected because the crash is REAL and will bite any fix that puts `agent_workflows/` at the head of `sys.path`, so an executor manipulating `sys.path` needs the warning. Keeping it HIGH: rejected because its severity came entirely from the false two-tree reading. | the two single-tree controls (one-tree `PYTHONPATH` forcing; decoy-only temp dir); `plan-review.md` 2.4 ("preserve valid content", "replace ambiguity") | yes |
| D-5 | Is `- Blocks-Release: next` still earned? | Yes, left in place. | Clearing it: rejected. All three carrier items are live `high` `bug`s with the gate, F-4 was upgraded from unconfirmed to MEASURED, and the defect's harm is falsified E/V evidence, which is the integrity of every release claim. PR-001 widens rather than narrows the problem. | the three graduated backlog items (each `- Blocks-Release: next`, `Work-Kind: bug`); AGENTS.md live-bug policy | yes |
| D-6 | E-03 may not fit one pass (up to 15 files). Split it into its own child plan? | No. Kept as one E-item, but authorized to land the helper plus a NAMED subset with a carrier id for the remainder, and forbidden to migrate silently-partially. | Splitting into a second child IPD: rejected because the helper and its first migrations are one deliverable in one file (`tests/support.py`) with one test surface, and the residual migration is mechanical repetition rather than a distinct concern; a child plan would add lifecycle overhead for a `sed`-shaped remainder. Requiring all 15 in one pass: rejected as the right-sizing hazard the rubric names. | `plan-review.md` rubric G right-sizing diagnostics (a)-(d); the measured absence of any shared helper | yes |

### Deferred and open

No finding is DEFERRED or REPLAN. Every finding above is FIXED, so no escalation to a `- Blocking: yes`
question is owed under the `review_findings_gate` rule (default `block_at: HIGH`; no
`review_findings_gate` key is configured in `.aw/config/project.json`).

OQ-01 remains OPEN by design (D-2, D-3): it is `- Blocking: no`, the repository does not answer it, and
the remaining candidates need a maintainer cost judgement. A non-blocking open question does not make a
plan `NO-GO`.

### Notes on what was NOT changed, and why

- No code or test file was touched by this review. Only the plan under review and this record. Every
  reproduction ran either read-only or in throwaway temp directories under the lane's own `.aw/state/`,
  each removed afterwards; the lane tree was verified clean before and after.
- F-1, F-2 and F-4 were NOT retracted or downgraded. All three re-measured TRUE and F-4 was STRENGTHENED
  from "to be confirmed by E-01" to a direct measurement with a quantified population.
- The `af7i6p` pin was NOT touched, and protecting it is now written into the plan at five places. The
  order-blind shipped assertion in `test_lane_permission_posture.py` was NOT "fixed" here either: it is a
  test-hardening change outside this plan's fence, and E-02/E-04 now route around it by requiring a
  behavioral probe instead. Whoever executes E-04 should consider whether that assertion deserves its own
  item; this review did not file one, and says so rather than implying it is covered.
- `E-01`..`E-04` were NOT renumbered or added to; `- Highest E allocated: 04` is unchanged and the E/V
  bijection stays 4/4. The revisions harden existing items rather than growing the plan.
- The plan's `- Status:` is left at `to-review` in the file; the transition to `reviewed` is applied
  through `aw ipd set reviewed` so it carries an attributed history line, per the untooled-status gate.
