# Review findings: plan tb6wh7

- Subject-Id: tb6wh7
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0a4a74a3` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize` conforms after. No
pre-review snapshot was needed: the plan was committed and unmodified, and the lane-input copy at
`.aw/state/lane-inputs/rev-7/` is byte-identical to the tracked file.

THE PLAN IS WELL RESEARCHED AND ITS NUMBERS ARE RIGHT. I re-derived every one rather than trusting the
authoring measurement:

```text
MAX_TURN_TIMEOUT      = 14400.0
driver_bound(None)    = 14400.0
parse("240m")         = 14400.0
driver_bound(240m)    = 14100.0
```

so E-01's expected `14400.0` (oc) and `14100.0` (agy) are exact, and F-4's point that the agy ceiling is
14100 rather than 4h is correct and load-bearing. F-1 through F-6 all re-verify: the FOREGROUND paragraph
exists at the cited place, `initialize_run_core` freezes `stall_timeout` exactly as described, the two
supervision sites use precisely the expressions E-01 copies, `tests/test_turn_bounds.py` is indeed gone
(deleted in `19313eed`, "test: trim test suite from 9,136 to under 2,000 tests"), and
`tests/test_defect_report.py` really has no prompt-length baseline. I also confirmed the defect: driving
both hosts' `build_prompt` today produces prompts of 7833 and 7836 characters containing no timing
information at all.

WHAT I FOUND THAT THE PLAN HAD NOT, in descending order of consequence.

FIRST, A FOURTH TEST FILE RENDERS THIS PROMPT AND THE PLAN NAMED TWO. `rg -n "build_prompt" tests/`
returns four files, and the unnamed one is the dangerous one: `tests/test_attempt_lane_facts.py:456` feeds
the rendered prompt to `lane_containment.absolute_paths_outside_lane` and asserts the result is EMPTY.
That function's own docstring says it is "A PROPERTY CHECK OVER THE EMITTED TEXT" and that "a newly added
line ... fail[s] it". So a budget paragraph containing any absolute path would redden a test the plan never
mentioned. I checked the proposed wording against the real predicate and it returns `[]`, which converts a
latent break into a stated constraint: the paragraph must contain no absolute path. E-06 now enumerates all
four files and singles this one out, and V-06 requires them named in the evidence.

SECOND, THE FIXTURE THAT WOULD HAVE BROKEN IS THE ONE E-06 ALREADY CITED. `tests/test_defect_report.py:72`
calls `build_prompt` with `{"run_id": "run-x", "repo": "."}` - no `options` KEY AT ALL, not an empty one.
E-02 was written for "a resumed run whose frozen `options` has no `turn_ceiling`", which understates it: a
literal `state["options"]["turn_ceiling"]` raises `KeyError` on a state that renders fine today. E-02 now
requires reading through `state.get("options", {})`.

THIRD, A RENDERING DEFECT IN A PARAGRAPH WHOSE ENTIRE PURPOSE IS ARITHMETIC. Both values are floats
(`DEFAULT_STALL_TIMEOUT: float = 600.0`, `--stall-timeout type=float`, `driver_bound_for_host` returning
`14400.0`), so a bare interpolation tells the agent "600.0 seconds" and "14400.0 seconds". Worse, the plan's
own wording includes "(about H hours)", and `int(14100/3600)` is `3`: a truncating render would tell an
antigravity agent it has "about 3 hours" when it has 3.9, UNDERSTATING the budget by nearly an hour in the
one place an agent is being asked to do arithmetic. And E-04's assertions would NOT have caught it, because
they are substring checks and `"600" in "600.0"` is True. E-03 now mandates integer-seconds formatting and a
rounded (never truncated) hours value; V-03 requires the agy paragraph specifically, since that is the case
truncation gets wrong; and the validation section records that this is verified by reading and by V-03's
paste rather than by an assertion.

FOURTH, A FALSE PREMISE IN THE PLAN'S OWN RATIONALE. E-03 instructed "Keep `build_prompt` host-neutral: it
reads only `state["options"]`, never a host module", and OQ-02 leaned on that. `build_prompt`'s first line
is `from agent_workflows import ipd_lifecycle, lane_containment, reporting_contract`, and E-02's own
fallback to `MAX_TURN_TIMEOUT` REQUIRES that import. The actual standing rule is that `runner_shared` must
not import EITHER RUNNER. The frozen-option design is still right, on OQ-02's second argument (the agy
ceiling depends on a per-run option, so it is run state), but the import argument is withdrawn in both
places so a future reader does not derive a rule the code contradicts.

FIFTH, A HEDGE I COULD SIMPLY TEST AWAY. E-05 offered a fallback in case an agy `--prepare-only` fixture
"turns out to need host resolution that cannot run offline". I ran it: `agy_runipd.main(["appr01", "--repo",
<tmp>, "--prepare-only"])` returned `0` offline, created the run directory, and wrote `options.timeout =
240m`. The hedge is removed and the direct fixture prescribed. I also recorded that the two existing agy
`--prepare-only` cases assert NO run dir is created, so they are not a usable model for reading `state.json`.

WHAT I CHECKED AND DELIBERATELY LEFT ALONE, recorded because it is the obvious way a frozen-at-init number
could be wrong. Could the stated budget go stale for the turn the agent is in? No, on both halves, and for
different reasons: `--stall-timeout` IS accepted on `resume` (verified by parsing
`["resume","run-x","--repo",".","--stall-timeout","42"]` -> `42.0`) and both hosts write it back into
`options`, so reading it at render time reflects the override automatically; while `--timeout` lives only on
the `start` subparser, so a ceiling frozen at init cannot diverge from the one the supervision site computes.
That is now F-12 and OQ-03, with an explicit instruction NOT to "improve" it by recomputing per turn.

ON THE RELEASE GATE, which I examined but did not disturb. The plan carries `- Blocks-Release: next` while
the backlog item it graduated from says in its own text "NOT filed as a bug and NOT release-gating", and
`- Work-Kind: followup` is outside the auto-gating set. OQ-01 already resolves this honestly as an explicit
maintainer decision rather than a policy consequence, and names the real reason (it makes x7wfyx's recorded
"continues to gate the release" claim true, since nothing else carried item A with the gate). I verified
x7wfyx is `graduated`, `Work-Kind: bug`, `Blocks-Release: next` with that exact history line. No finding: the
plan's own framing is accurate. I did add a note to the gate about closing `4bhxni`, because that item carries
the gate too and `aw backlog set done` fails closed on it: the HANDOFF route applies via this plan's
`From-Backlog` plus matching gate, and an executor reaching for `--blocks-release -` would DROP the gate
rather than discharge it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing | `rg -n "build_prompt" tests/` -> four files; `tests/test_attempt_lane_facts.py:456` asserts `lane_containment.absolute_paths_outside_lane(rendered_prompt, lane_root) == []`; that function's docstring: "A PROPERTY CHECK OVER THE EMITTED TEXT ... a newly added line ... fail[s] it"; verified at review that the proposed wording returns `[]` | **THE PLAN'S LARGEST REGRESSION SURFACE WAS UNDECLARED.** E-06 named two of the four test files that render this prompt, and the unnamed `tests/test_attempt_lane_facts.py` is the one with a whole-prompt property assertion that fails on any new out-of-lane absolute path. An executor following E-06 as written would have checked the two named files, seen them pass, and been surprised by the fourth. | C:Low; U:Low; S:Low; F:Medium (a surprise red in a property test whose failure mode is non-obvious); the FIX is Low | FIXED | E-06 now enumerates all four callers with their line numbers, singles out the property test with its failure mode, and states the resulting constraint (the paragraph must contain NO absolute path, verified safe at review). V-06 requires all four named in a pasted run. Recorded as F-9 and in "Project conventions discovered". |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness | `tests/test_defect_report.py:72-78` fixture state is `{"run_id": "run-x", "repo": "."}` with no `options` key; measured: both hosts render 7833/7836 characters from it today | **E-02 GUARDED THE WRONG ABSENCE.** It was written for a state whose `options` lacks `turn_ceiling`, but the live fixture has no `options` key at all, so `state["options"]["turn_ceiling"]` would raise `KeyError` and turn a currently-green test red. | C:Low; U:Low; S:Low; F:Low | FIXED | E-02 now requires `state.get("options", {})` with the measurement, and adds that the whole paragraph must be omitted (not a bare heading) when both bounds are disabled. E-06 repeats the constraint at the test that would catch it. Recorded as F-10. |
| PR-003 | MEDIUM | IN-SCOPE | F. KISS/UX (honest output) / E. Testing | `DEFAULT_STALL_TIMEOUT: float = 600.0`; `--stall-timeout type=float`; `driver_bound_for_host` -> `14400.0`/`14100.0`; measured `int(14100/3600) == 3` vs `round(14100/3600, 1) == 3.9`; `"600" in "600.0"` is True | **THE BUDGET PARAGRAPH WOULD HAVE PRINTED FLOATS AND COULD HAVE UNDERSTATED THE AGY CEILING BY NEARLY AN HOUR, AND THE PLAN'S OWN TESTS COULD NOT CATCH EITHER.** "600.0 seconds" is sloppy; "about 3 hours" for a 3.9-hour budget is actively misleading in the one paragraph whose purpose is to let an agent decide arithmetically whether a command fits. E-04's substring assertions pass on the float form, so the tests provided no protection. | C:Low; U:Medium (the agent is the user here, and an understated budget causes exactly the premature deferral this plan exists to prevent); S:Low; F:Low; Overall:Low for the fix | FIXED | E-03 requires integer-seconds rendering (`f"{v:g}"` or `int(round(...))`, both verified) and a ROUNDED hours value, or omitting the parenthetical when it would mislead. V-03 requires the agy paragraph pasted specifically. "Required tests / validation" now states plainly that the substring assertions cannot catch this and suggests an explicit `assertNotIn(".0 seconds", prompt)`. Recorded as F-11. |
| PR-004 | MEDIUM | IN-SCOPE | C. Architecture (a rationale that contradicts the code) | `runner_shared.build_prompt` first line: `from agent_workflows import ipd_lifecycle, lane_containment, reporting_contract`; E-02's fallback requires `lane_containment.MAX_TURN_TIMEOUT` | **THE PLAN JUSTIFIED ITS DESIGN WITH A RULE THE CODE ALREADY BREAKS, AND ITS OWN NEXT ITEM BREAKS IT TOO.** E-03 said `build_prompt` reads "never a host module" and OQ-02 leaned on it. The function already imports three shared modules including the one E-02 needs. The design choice is correct; the stated reason is not, and a false invariant in a plan propagates into the code comment the executor writes next. | C:Low; U:Low; S:Low; F:Low | FIXED | E-03 now states the real invariant (`runner_shared` must not import EITHER RUNNER; `lane_containment` is host-neutral and already imported) and keeps the frozen-option design on the run-state argument alone. OQ-02 records the correction and withdraws the import argument explicitly. "Project conventions discovered" corrected. Recorded as F-8. |
| PR-005 | LOW | IN-SCOPE | E. Testing (an unnecessary hedge and a vacuity risk) | Measured: `agy_runipd.main(["appr01", "--repo", <tmp>, "--prepare-only"])` -> rc 0 offline, run dir created, `options.timeout = 240m`, `options.stall_timeout = 600.0`; the two existing agy `--prepare-only` cases assert `self.assertFalse((repo / ".aw" / "records" / "runs").is_dir())` | **E-05 CARRIED AN ESCAPE HATCH FOR A DIFFICULTY THAT DOES NOT EXIST, AND POINTED AT A MODEL THAT ASSERTS THE OPPOSITE.** The fallback ("assert via `initialize_run` with a patched model resolver") would have produced a weaker test on an untested assumption, and the cited `tests/test_agy_runipd_cli.py` pattern deliberately asserts NO run dir is created, so it cannot model reading `state.json`. | C:Low; U:Low; S:Low; F:Low | FIXED | The hedge is REMOVED and the direct fixture prescribed with the measured evidence. E-05 also records why the existing agy cases are not a usable model. V-04 separately gains a check that its `-k` pattern selects a non-zero number of tests, since a non-matching `-k` exits 0 having run nothing. |
| PR-006 | LOW | IN-SCOPE | G. Executability (an unsafe validation step and a placement ambiguity) | V-04 as written: "temporarily replacing the rendered stall value with a literal `600` in a scratch working copy (revert before commit)"; `{role_block}` immediately follows the FOREGROUND paragraph; `test_prompt_integration_and_format` compares `prompt[start:]` to `contract_text()` exactly | **THE ONE STEP THAT CAN LOSE WORK WAS AN IN-PLACE MUTATION IN A SHARED CHECKOUT, AND "DIRECTLY AFTER THE FOREGROUND PARAGRAPH" IS AMBIGUOUS.** "Scratch working copy" is undefined and invites `git stash`, which would move a co-worker's uncommitted changes. Separately, the insertion point sits next to `{role_block}`, and inserting on the wrong side of it splits the lifecycle notice from the JSON schema; inserting after the reporting contract fails an existing exact-match assertion. | C:Low; U:Low; S:Medium-High if a stash moves a peer's work, but the FIX is Low; F:Low | FIXED | V-04 prescribes a throwaway detached worktree with the gitignored paths and `git worktree remove`, permits an in-place mutation only if reverted in the next command and recorded, and forbids `git stash` with the shared-checkout reason. E-03 states the placement precisely (between the FOREGROUND text and `{role_block}`) with the reason, and V-03 requires the position pasted plus the contract test passing. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | A fourth test file property-asserts over the whole prompt. Widen scope to update it pre-emptively, or constrain the new paragraph so it cannot break it? | CONSTRAIN THE PARAGRAPH (no absolute path) and name the file in E-06, changing no test. | (a) Pre-emptively edit `tests/test_attempt_lane_facts.py`: rejected, the test is CORRECT and the proposed wording passes it (verified), so editing it would weaken a live containment guarantee for no reason. (b) Add it to `- Scope-Paths:`: rejected, the plan should not declare a path it has no reason to modify; the gate already permits a justified out-of-fence edit with `--scope-reason` if one genuinely breaks. (c) Leave E-06 naming two files: rejected, it hands the executor a surprise in the test hardest to diagnose. | `lane_containment.absolute_paths_outside_lane` docstring and `_ABS_PATH_RE`; the predicate driven at review on the proposed wording returning `[]`; `rg -n "build_prompt" tests/` | yes |
| D-2 | The hours parenthetical truncates to "about 3 hours" for the 14100s agy ceiling. Drop the parenthetical, or require rounding? | REQUIRE A ROUNDED VALUE, permitting omission when it would mislead. | (a) Keep integer truncation: rejected outright, it understates the budget by nearly an hour in the paragraph whose sole purpose is arithmetic, which causes the premature deferral this plan exists to prevent. (b) Drop the parenthetical entirely: rejected as the default, since "14400 seconds" is genuinely hard for a human or agent to feel, and the hours figure is the part that makes the number actionable; it is allowed as a fallback. (c) Render exact hours ("3.9166 hours"): rejected, false precision in prose. | `int(14100/3600) == 3` vs `round(14100/3600, 1) == 3.9`, measured; `driver_bound_for_host` returning `14100.0` on agy with the default `--timeout 240m` | yes |
| D-3 | The plan's host-neutrality rationale is factually wrong but its design choice is right. Correct the rationale, or leave it since the outcome is unaffected? | CORRECT IT in both places and withdraw the import argument explicitly. | (a) Leave it: rejected. A plan is read by the executor who then writes the code comment; a false invariant ("never a host module") propagates into the source and is then cited by the next reader, and E-02 in the same plan already violates it. (b) Change the design to match the claim (compute the ceiling outside `build_prompt` and pass it in): rejected, it would remove the frozen-option design that makes the per-run agy `--timeout` case work, for the sake of a rule that does not exist. | `build_prompt`'s first line importing `ipd_lifecycle, lane_containment, reporting_contract`; E-02's required `MAX_TURN_TIMEOUT` fallback; the module's actual standing rule (import neither runner) | yes |
| D-4 | The plan carries `Blocks-Release: next` while its source backlog item says "NOT release-gating" and its `Work-Kind: followup` is outside the auto-gating set. Raise it to the maintainer? | NO: the plan's OQ-01 already records it correctly as an explicit maintainer decision; add only a closing-mechanics note. | (a) Raise it as a finding: rejected, OQ-01 states the reasoning accurately (policy does not require the gate; the maintainer chose it; it makes x7wfyx's recorded claim true), so there is nothing to correct. (b) Ask the maintainer to reconfirm: rejected, it is recorded as decided on 2026-09-26 and re-asking spends the maintainer's time on a settled question. (c) Say nothing at all: rejected, because closing `4bhxni` (which carries the same gate) FAILS CLOSED and an executor could reach for `--blocks-release -`, dropping the gate instead of discharging it. | Backlog `4bhxni` text "NOT filed as a bug and NOT release-gating"; `x7wfyx` `graduated`/`bug`/`Blocks-Release: next` with its 2026-09-24 history line; AGENTS.md close-legitimacy rule and the HANDOFF route this plan's `From-Backlog` plus matching gate satisfies | yes |
| D-5 | Can a ceiling frozen at init go stale for the turn the agent is actually in? | NO on both bounds; record it as F-12/OQ-03 with an instruction not to recompute per turn. | (a) Recompute the ceiling every turn from `options["timeout"]`: rejected as unnecessary, since `--timeout` cannot be changed on resume, and it would add a second computation site that could drift from the supervision site. (b) Leave the question unexamined: rejected, a frozen-at-init number is exactly the shape that goes stale, and a reader who does not find the check recorded will redo it. | `--timeout` present only on the `start` subparser; `--stall-timeout` accepted on `resume` (parsed at review -> `42.0`) and written back into `options` by both hosts; `agy_runipd` supervision site reading `options.get("timeout", DEFAULT_TIMEOUT)` | yes |

### Deferred and open

- (none DEFERRED among findings). All six findings were FIXED in place. PR-001 is `HIGH` and is FIXED, so no
  finding at or above the repository's gate threshold (no `review_findings_gate` configured in
  `.aw/config/project.json`, so the default `HIGH` applies) is left unfixed, and nothing is owed an escalated
  `- Blocking: yes` question.
- No `Reversible: no` decision was taken, so no escalation to the maintainer is owed.
- The plan's three open questions (OQ-01 pre-existing, OQ-02 corrected, OQ-03 added) are all `resolved` and
  all `Blocking: no`. The plan's two Deferred entries (a true remaining budget; the verifier/review prompts)
  both carry reasoned `Carrier-Declined` values and I did not overturn either: a live remaining figure
  genuinely needs a mid-turn channel that does not exist, and the verifier/review prompts are separate
  builders that were not the reported failure.

HONEST LIMITS, stated because they bound what this round proves. I verified the NUMBERS and the REGRESSION
SURFACE by driving real code, but I applied no product edit and wrote no test, so that the shipped paragraph
renders integer seconds, that it sits where E-03 says, and that all four prompt-caller test files stay green
are still E-02/E-03/E-06's work and V-03/V-06's evidence. I did NOT run the bare suite for this plan; I ran
targeted probes and read the four affected test files, which for a prompt-text addition is proportionate but
is a hole rather than a clearance. My agy `--prepare-only` measurement used a synthetic conforming plan in a
temp repo and asserted on `options.timeout`, NOT on `options.turn_ceiling`, which does not exist yet; it
proves the fixture mechanism works offline and nothing about the value E-05 will assert. Most importantly,
NOTHING I did tests the end-to-end property the plan actually wants, that the budget the prompt STATES is the
budget the driver ENFORCES: the two sites compute the same expression from the same frozen input and I
verified they cannot diverge on either host (F-12), but that is an argument from reading, and a real
end-to-end check would need a turn that actually hits a 4-hour ceiling. I also did not evaluate whether
stating a budget changes agent behavior for the better, which is this plan's whole premise and is not
measurable from here.
