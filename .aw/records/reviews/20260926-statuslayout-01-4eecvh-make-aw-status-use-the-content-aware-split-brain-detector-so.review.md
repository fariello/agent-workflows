# Review findings: plan 4eecvh

- Subject-Id: 4eecvh
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `8b64b198` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize` conforms after. No
pre-review snapshot was needed: the plan was committed and unmodified, and the lane-input copy is
byte-identical to the tracked file.

THE PLAN'S CORE CLAIM IS TRUE AND I RE-DERIVED IT RATHER THAN TRUSTING THE BRIEF. Driving the three
real functions across six shapes:

```text
clean      collector=('.aw + .agents', True) engine=False doctor='.aw'
res        collector=('.aw + .agents', True) engine=False doctor='.aw'
gen        collector=('.aw + .agents', True) engine=True  doctor='.aw + .agents (dual layout / split-brain)'
legacy     collector=('.agents', False)      engine=False doctor='.agents'
empty      collector=('none', False)         engine=False doctor='unconfigured'
partialaw  collector=('.aw + .agents', True) engine=False doctor='.aw'
```

Note what that table shows beyond the plan's own statement: the collector returns the IDENTICAL verdict
for `clean`, `res` and `gen`, so its output carries no information about content at all. F-5's partial-`.aw`
edge reproduces exactly as the plan records it.

THE USER-VISIBLE SYMPTOM REPRODUCES THROUGH THE REAL COMMAND, which the plan asserted but had not shown.
Driving `cli.main(["status"])` against a residue fixture:

```text
Layout:    .aw + .agents [dual layout / split-brain - run aw migrate-layout]
contains dual layout? True
```

and the GENUINE fixture renders the same line, confirming the warning is uninformative in both directions.

Every other material claim checks out. F-3's negative `check_engine` audit is correct (`rg 'split.brain|detect_split_brain'`
on that module returns nothing; its only layout rules are the two `check.system-layout-*` ids keyed on
`.aw/system/VERSION` and `.aw/system/layout.json`). F-4 is correct: the sole `_collect_repo_status_details`
caller in `tests/` is `tests/test_doctor.py::...test_status_and_doctor_report_the_same_preset_and_backend`,
which reads `preset`/`backend` only. `engine.SKILLS_DIR = ".agents/skills"` is confirmed, as is
`DoctorLayoutClassificationIsContentAwareTests.setUp` already building the RESIDUE shape including
`.agents/skills`, so E-03's chosen home is right. The spec-sync claim is verifiable: no `.spec.md` mentions
split-brain or dual layout, and no doc names the `layout`/`split_brain` keys.

WHAT I FIXED. All three findings concern the plan's EVIDENCE AND METHOD, not its approach, which is the
right one (reuse the one shared detector, mirror doctor's labels, change nothing else). The highest-value
one is PR-002: E-03's render assertion carried an escape hatch ("if driving the full `status` command
cannot be pointed at a temp repo without touching global config, assert on the collector only") that would
have dropped the ONLY assertion covering the user-visible symptom, on a difficulty the executor had no
reason to test. I executed both candidate mechanisms against the unfixed code, confirmed both reproduce the
false warning, and prescribed them, so the hedge is gone. While doing so I found the trap that would have
made the obvious placement silently useless: `tests/test_cli.py` is `pytestmark = pytest.mark.slow`
(`tests/test_cli.py:29`), so a render case added beside `test_status_shows_environment_readout` would NOT
run in the bare suite E-04 uses as its gate. That is now stated in E-03, in the Scope check, and in the
validation section.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | C. architecture / G. executability (a Goal claim wider than the work) | Goal as written: "Make `aw status`, `aw doctor` and the install guard give ONE answer"; measured at review with `.aw/system/VERSION` present: a `__pycache__/x.pyc` under `.agents/workflows` -> `engine.detect_split_brain_layout` `False`, `upgrade_rehearsal.detect_layout` `'dual'`; a ZERO-BYTE `assess/empty.md` -> `False` vs `'dual'`; `upgrade_rehearsal.has_files` counts any file, where `engine.detect_split_brain_layout` requires `st_size > 0` and non-cruft | **A FOURTH LAYOUT CLASSIFIER DISAGREES AND THE PLAN DID NOT KNOW ABOUT IT.** The plan's own Concern frames this defect as the class "two detectors disagreeing", and its Goal promises ONE answer. `upgrade_rehearsal.detect_layout` is a fifth-vocabulary classifier (`aw`/`legacy`/`dual`/`aw+litter`/`none`) that does not consume the shared detector and returns `dual` on shapes the shared detector calls clean. Left unstated, the plan would have shipped claiming a unification it does not deliver, and a future reader auditing "is the split-brain question unified?" would find a live counterexample and re-open a settled question. | C:Low; U:Low; S:Low; F:Low (the FIX is prose plus a recorded decline; actually unifying it would be a real change and is correctly NOT proposed) | FIXED | Goal now states the scope of its claim explicitly and names the fourth classifier as a recorded, unfixed divergence. Added F-6 with all three measured shapes, a reasoned `Carrier-Declined` row under "Deferred / out of scope", and OQ-03 resolved from the harness's OWN documentation (`derive_observations` tells its reader the state is "Directory litter, not a split-brain layout, though 'aw doctor' may still call it dual", and its docstring says the output is "Descriptive, never a pass/fail verdict"), which is what makes the divergence deliberate rather than a second instance of this bug. |
| PR-002 | MEDIUM | UNDER-SCOPE | E. testing (an escape hatch that drops the only test of the reported symptom) | E-03 as written: "If driving the full `status` command cannot be pointed at a temp repo without touching global config, assert on the collector only and say so in V-03"; `tests/test_cli.py:29` `pytestmark = pytest.mark.slow`; `pyproject.toml` `addopts` carries `-m 'not slow'`; verified at review that BOTH `mock.patch.object(cli, "_repos_for_report", return_value=[repo])` and the `XDG_CONFIG_HOME`+`config.save` route drive `cli.main(["status"])` against a temp repo and print the false warning | **THE RENDER ASSERTION WAS OPTIONAL, AND ITS SUGGESTED HOME WOULD NOT HAVE RUN.** The user-visible defect IS a line of rendered text and nothing asserts on it today (the plan's own F-4), so the escape hatch let the executor skip the only coverage of the actual symptom, on a difficulty nobody had tested. Worse, E-03 pointed at `tests/test_cli.py::test_status_shows_environment_readout` as the model: that module is `slow`-marked and excluded from the bare run, so a case placed there would be written and then never executed by E-04's own gate - a vacuous pass of exactly the kind this plan exists to prevent. A third hazard was unstated: the warning is emitted through `term.color256(..., 208, bold=True)`, so a substring assertion on unstripped output is brittle. | C:Low; U:Low; S:Low; F:Medium (a symptom-level test that can be skipped, or written where it never runs, proves nothing) | FIXED | The hedge is REMOVED. E-03 now prescribes both proven mechanisms (each executed at review against unfixed code), requires `NO_COLOR=1` plus ANSI stripping with the regex, forbids placing the case in `tests/test_cli.py` WITH the slow-mark reason, requires environment restoration in `tearDown`, and records the measured pre-fix render output so the assertion is demonstrably non-vacuous. Scope check and "Required tests / validation" updated to match; the stale note about importing a helper from `tests/test_cli.py` is replaced (no such helper is needed). |
| PR-003 | LOW | IN-SCOPE | A. correctness / E. testing (an irreversible step and two unreliable instructions) | V-03 as written: "the same run with the E-02 hunk temporarily reverted ... then passing again after restoring"; E-01 as written: "Build three scratch dirs under `/tmp/`"; measured at review: a bare `/tmp/<name>` write was REFUSED by the sandbox while `tempfile.TemporaryDirectory()` inside the interpreter worked; `.gitignore:73` (`.aw/worktrees/`), `.gitignore:42` (`tmp/`) | **THE ONLY IRREVERSIBLE STEP WAS AN UNGUARDED HAND-REVERT, AND E-01'S FIXTURE PATH MAY SIMPLY BE REFUSED.** V-03 told the executor to revert the fix in place and restore it, with no instruction on what to do if interrupted; in an otherwise one-block plan that is the single action that can lose the work, and in a SHARED CHECKOUT it invites reaching for `git stash`, which would move a co-worker's uncommitted changes. Separately, E-01's `/tmp/` instruction is environment-dependent: it was refused during this very review, which would cost the executor a cycle on the plan's FIRST step. Also missing: what it means if a CONTROL case fails before the fix. | C:Low; U:Low; S:Low; F:Medium-High if the revert is interrupted, but the FIX is Low (prescribe a throwaway worktree and in-process temp dirs, which risk nothing) | FIXED | V-03 now prescribes a throwaway detached worktree as the preferred before-fix mechanism with its gitignored path and teardown command, permits the in-place revert as an explicit alternative on condition it is restored in the next command and that fact is recorded, forbids `git stash` with the shared-checkout reason, and states that a control case failing before the fix means the TEST is broken and must be reported rather than adjusted. E-01 now mandates `tempfile.TemporaryDirectory()` in one throwaway script, citing the measured refusal, and its Expected outcome is corrected to show the collector's verdict is identical on all three shapes. E-04 gains the bare-run prohibition list and a re-derive instruction on the `2501 passed, 2 skipped` baseline. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | A fourth classifier (`upgrade_rehearsal.detect_layout`) disagrees with the shared detector. Widen the plan to fix it, file a carrier for it, or record it as deliberate? | RECORD IT AS A DELIBERATE DIVERGENCE: narrow the Goal's claim to the three health surfaces, add F-6 with measurements, and decline a carrier with a reason. | (a) Widen the plan to repoint it: rejected, `upgrade_rehearsal.py` is outside `- Scope-Paths:`, it answers a different question with a different five-value vocabulary, and turning a one-block status fix into a harness change multiplies blast radius for no user-visible gain. (b) File a backlog carrier: rejected, the carrier rules oblige a durable handoff for an unfixed DEFECT, and the harness DOCUMENTS this behavior as intended, so filing one would assert a defect the code denies. (c) Say nothing: rejected outright, it leaves the Goal's "ONE answer" claim false and hands the next auditor a live counterexample. | `upgrade_rehearsal.derive_observations` `aw+litter` branch: "Directory litter, not a split-brain layout, though 'aw doctor' may still call it dual"; its docstring "Descriptive, never a pass/fail verdict"; `upgrade_rehearsal.has_files` docstring vs the `st_size > 0` + `is_ignored_source_path` filters in `engine.detect_split_brain_layout`; three measured shapes in F-6. | yes |
| D-2 | E-03's render assertion was optional and its modelled home is slow-marked. Prove a mechanism, or let the executor decide? | PROVE BOTH CANDIDATE MECHANISMS AT REVIEW and prescribe them, deleting the escape hatch. | (a) Keep the hedge: rejected, it permits skipping the only test of the reported symptom (the plan's own F-4 says nothing covers it), which is precisely the vacuous-coverage shape the plan exists to remove. (b) Prescribe one mechanism only: rejected, both work and they fail differently (the mock route needs no config at all; the config route matches existing suite convention), so naming both leaves the executor a fallback that is still proven. (c) Move the render case to `tests/test_cli.py` beside the cited sibling: rejected and now explicitly forbidden, that module is `slow`-marked so the case would never run in E-04's bare gate. | Both mechanisms executed at review against unfixed code, each rendering `Layout:    .aw + .agents [dual layout / split-brain - run aw migrate-layout]`; `tests/test_cli.py:29`; `pyproject.toml` `addopts` `-m 'not slow'`; `tests/test_doctor.py` carries no `pytestmark`. | yes |
| D-3 | Repointing adds a filesystem walk to `aw status`. Does the repo's "inefficiency a user can notice is a defect" bar make that a concern worth raising to the maintainer? | NO: measure it, record the numbers as F-7 (INFO), and do not raise it. | (a) Raise it as a finding to fix: rejected on measurement, the realistic cost is 17-120 us and the command already runs `attention.scan(repo)` per repo, which is orders of magnitude more work; filing it would be the unmeasured-hunch filing AGENTS.md explicitly says is not a bug. (b) Say nothing: rejected, the plan adds I/O to a user-facing command and a reader deserves the number rather than having to re-derive it; recording costs one row. (c) Ask the maintainer: rejected, this is answerable by measurement, which is what "do not ask the human what the repository already answers" means. | Measured at review: clean migrated repo 17 us/call, realistic residue shape 120 us/call, pathological 1200-file non-short-circuiting tree 23.7 ms/call; `cli._collect_repo_status_details` already calls `attention.scan(repo)`; AGENTS.md "inefficiency a user can notice is a defect ... An unmeasured hunch that something feels slow is not a bug". | yes |

### Deferred and open

- (none). All three findings were FIXED in place. No finding reached the repository's gate threshold
  (`HIGH`), so nothing is owed an escalated `- Blocking: yes` question. Every question was resolvable from
  repository evidence; the plan's three open questions are all `resolved` and all non-blocking. No
  `Reversible: no` decision was taken, so no escalation is owed.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECT on six shapes, the
rendered symptom through the real command, both prescribed render mechanisms, the negative `check_engine`
audit, the absent test coverage, the spec and doc silence, and the performance cost. I did NOT apply E-02
or write the tests, so that the shipped test asserts correctly, that the before-fix run is genuinely red,
and that the suite stays green remain E-02/E-03/E-04's work and V-02/V-03/V-04's evidence. I ran the bare
suite once for the `2501 passed, 2 skipped in 59.95s` baseline and did NOT run the slow set (`make
test-all`); for a change confined to one function whose only in-repo caller reads different keys that is
proportionate, but it is a hole and not a clearance - and note the slow-marked `tests/test_installer.py`
carries 21 `split_brain` references, none of which touch the status collector, so I judged the risk low by
READING rather than by running. A consumer of `aw status --agent` OUTSIDE this repository cannot be
surveyed from here; what covers that case is that the key names and types are unchanged and that `aw
doctor` has already reported the corrected value for the same repo since `z1yefm`, not any measurement I
made. The `2501` baseline is a live population and will drift; E-04/V-04 are instructed to re-derive it.
