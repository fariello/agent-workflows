# Review: stop install --to-aw leaving a permanent split-brain, child z1yefm (Set migleftover)

- Subject-Id: z1yefm
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `bba372a8`. Structural preflight `aw ipd lint --phase author` CONFORMED with zero findings
before semantic review, and `--phase review-finalize` CONFORMED after the revisions. No product code was
modified by this review.

DISCLOSURE: I AUTHORED THIS PLAN in the same session, so this is a self-review and worth less than an
independent one. Its value rests on what was EXECUTED. Eight things were run: every cited line range
opened; a grep for ALL `leftover_disposition=` literals in `cli.py`; `_split_brain_guard` read in full;
`engine.detect_split_brain_layout` read in full; that detector executed against a fixture holding the
EXACT measured residue shape; `doctor.probe_environment` executed against the same fixture; the detector
executed against a GENUINE split-brain fixture to check for a masked true positive; and the enclosing
function of each call site identified by name.

THE MOST CONSEQUENTIAL FINDING IS THAT THE PLAN'S ROOT-CAUSE STORY FOR THE USER-VISIBLE SYMPTOM WAS WRONG.
The plan asserted, as a discovered convention, that "the dual-layout detector keys off directory EXISTENCE,
not live content" and that this detector is consumed by BOTH `aw doctor` and `cli._split_brain_guard`. That
is false, and the error mattered in two directions. There are TWO detectors. `engine.detect_split_brain_layout`
(engine.py:119-142) is already content-aware: it walks `.agents/workflows` and returns True only for a
non-empty, non-cruft file. `doctor.probe_environment` is not: it tests bare `.is_dir()` on `.aw` and
`.agents` (doctor.py:323-326). Measured side by side on a residue-only fixture, engine returns `False`
while doctor returns `.aw + .agents (dual layout / split-brain)`. Consequences: first, the plan's claim
that the residue can affect LATER INSTALLS is unfounded, because `_split_brain_guard` consumes the engine
detector (cli.py:4977) and that detector is already correct, so the plan was overstating the blast radius;
second and worse, the plan DEFERRED the detector fix on the explicit premise that "once the residue is gone
the false report is gone", and that premise is false.

WHY THE DEFERRAL WAS THE REAL DEFECT. `.agents/skills` is the intended permanent skills location for BOTH
layouts (engine.py:171, engine.py:174-183), a fact this plan itself established in order to protect those
92 files from deletion. It follows that `.agents/` exists FOREVER on a correctly migrated repo. Doctor's
bare-existence test therefore reports split-brain forever, no matter how perfect the cleanup. Cleanup alone
could never close the defect the plan was written to close, so the plan as authored would have shipped,
passed all its own validation, and left the user still reading `Dual layouts detected`. PR-002 brings the
detector fix IN scope as E-06, pointed at the existing content-aware predicate rather than a second walk.

I CHECKED THAT E-06 CANNOT MASK A REAL PROBLEM, since making a warning quieter is exactly the kind of fix
that hides bugs. Against a genuine split-brain fixture (a non-empty file under `.agents/workflows`) the
engine detector returns `True`; against the residue shape plus a populated `.agents/skills` it returns
`False`. So adopting it preserves true positives while dropping the false one. V-06 requires both fixtures
to be pasted, precisely so a future change cannot quietly weaken this.

THE THIRD FINDING IS AN INCOMPLETE FIX INSTRUCTION. The plan named TWO hardcoded `leftover_disposition="defer"`
sites and told the executor to change "both". A grep finds THREE: cli.py:5240 (`--to-aw`), cli.py:5265-5267
(interactive confirm), and cli.py:4998, inside `_split_brain_guard`'s own migrate-now branch. The third is
the path a split-brain repo actually takes, so an executor following the plan literally would have left the
consolidation path unable to clean up and would have reasonably believed the work complete. E-01 now names
all three and requires a grep proving no hardcoded literal remains.

WHAT I VERIFIED AND KEPT. F-04's root cause is exact, and F-05's reading of `defer` is correct: only the
`remove` branch deletes (layout_migration.py:527-541, :568+). The conservative `_is_removable_leftover`
predicate (layout_migration.py:495-521) is correctly identified as a contract not to weaken, and the gate
still says so. The deliberate refusal to change the DEFAULT to `remove` is right and stays deferred to the
maintainer as OQ-01: making a migration destructive by default is a risk-appetite call, not an agent's. The
conditional shape of E-03 (change nothing if `remove` already prunes) is good discipline and V-03 forces
the evidence either way. F-06's correction of the skills claim is the single most important thing in the
plan and is untouched.

WHAT REMAINS GENUINELY DEFERRED: auditing `check_engine`'s own layout rules for the same existence-versus-content
confusion. That is a separate surface with separate tests and is not what a user reads in `aw doctor`, so it
does not gate this fix. It is now stated as the deferral, replacing the false one.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-002 | HIGH | UNDER-SCOPE | D. Anti-regression; G. Plan executability | agent_workflows/doctor.py:323-326; agent_workflows/engine.py:119-142 | The plan described ONE existence-based detector shared by doctor and the install guard. There are two, and they disagree: engine's is already content-aware (returns `False` on the residue), doctor's tests bare `.is_dir()` (returns split-brain). The plan therefore DEFERRED the detector fix on the false premise that cleanup alone removes the false report. Because `.agents/skills` is a permanent resident (engine.py:171), `.agents/` always exists and doctor would report split-brain forever, so the plan could not have achieved its stated goal. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Corrected the conventions section with the measured engine-versus-doctor comparison; added E-06 repointing doctor at the existing content-aware predicate; added V-06 requiring BOTH a residue fixture and a genuine-split-brain fixture so true positives are provably retained; added `doctor.py`/`tests/test_doctor.py` to `Scope-Paths`; replaced the false deferral with the real one; recorded as F-08 and F-10. |
| PR-003 | HIGH | UNDER-SCOPE | G. Plan executability | agent_workflows/cli.py:4998 | E-01 named two hardcoded `leftover_disposition="defer"` sites and said "both". A grep finds three; the missed one is in `_split_brain_guard`'s migrate-now branch, which is the path a split-brain repo actually takes. An executor following the plan literally would leave the consolidation path unable to clean up and believe the work done. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now names all three sites (cli.py:5240, :5265-5267, :4998) and requires `grep -n 'leftover_disposition="' agent_workflows/cli.py` to return no hardcoded literal before the item may be marked complete; recorded as F-09. |
| PR-005 | LOW | IN-SCOPE | C. Architecture | agent_workflows/cli.py:4977 | The plan claimed the residue "can also affect later installs" via the split-brain guard. Since that guard consumes the already-correct engine detector, the claim overstates the blast radius; an executor could waste effort defending against a condition that cannot occur. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in the conventions section, which now states explicitly that the guard consumes the engine detector and that the false report comes from doctor alone. |

MAINTAINER RULING RECEIVED DURING THIS REVIEW, AND IT REFRAMED THE QUESTION. I asked whether `--to-aw`
should default to `remove` or keep `defer`. The maintainer rejected the framing: for 2.0.0 the intent is to
strongly encourage everyone onto the new layout, and behavior we WANT must not sit behind a flag a user has
to read `--help` to discover, so a policy question like this should ASK and default the prompt to the
encouraged action. They further required that the answer be SAVEABLE so nobody is prompted on every install.
That mechanism does not exist, so it is filed as blocking backlog item `kapm7y` (`Blocks-Release: next`).
Two further defects surfaced while grounding that item, and both are recorded in this plan as F-11 and F-12
and assigned to `kapm7y` rather than fixed here: the interactive migrate prompt currently defaults to NO
(`_confirm(..., False)` rendering `[y/N]`, cli.py:5256-5259 and cli.py:4799), and `--yes` does NOT migrate
at all but keeps the deprecated layout with a warning (cli.py:5277-5282), meaning an automated fleet update
silently leaves every repo on the layout 2.0.0 is retiring. This plan keeps `defer` as the non-interactive
default deliberately: adding a prompt before the save-my-answer mechanism exists would nag on every install,
which the maintainer explicitly rejected.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should doctor's layout classification be fixed in this plan, or deferred as originally written? | Fix it here as E-06. | (a) Keep the deferral and file a separate item; (b) make cleanup so complete that `.agents/` is removed entirely. | Rejected (a) because the deferral's stated premise is provably false: `.agents/skills` is the intended permanent location for both layouts (engine.py:171, :174-183), so `.agents/` never disappears and doctor's existence test misreports a migrated repo forever; the plan's own goal would go unmet. Rejected (b) because deleting `.agents/skills` would break host skill discovery, which this very plan establishes as a regression to guard against (F-06). | yes |
| D-2 | Should E-06 write a new content-aware check for doctor, or reuse `engine.detect_split_brain_layout`? | Reuse the existing predicate. | Write a doctor-local content walk. | A second implementation of the same predicate is the duplicate-authority pattern the sibling plan `h90ij1` exists to remove, and the existing detector is already correct and already consumed by `cli._split_brain_guard` (cli.py:4977). Verified it keeps true positives: `True` on a genuine split-brain fixture, `False` on the residue shape. | yes |
| D-3 | Is it safe to make a user-facing warning stop firing, given that could mask a real problem? | Yes, and V-06 is written to prove it per-run rather than trusting this judgement. | Leave the warning firing and document the false positive instead. | Executed both cases before deciding: genuine split-brain (non-empty file under `.agents/workflows`) still detected `True`; residue plus populated `.agents/skills` detected `False`. The warning is not being weakened, it is being made accurate. Rejected documenting-the-false-positive because an always-on warning with unactionable advice trains users to ignore warnings. | yes |
| D-4 | Should the `--to-aw` default become `remove`? | ASKED the maintainer; ruling received and recorded. The answer was neither offered option: policy questions should PROMPT, defaulting to the encouraged action, and the answer must be SAVEABLE. This plan keeps `defer` non-interactively and defers the prompt to new blocking item `kapm7y`. | Decide `remove` now unilaterally; or keep `defer` silently and never raise it. | Correctly escalated rather than self-resolved: making a migration destructive by default is a risk-appetite call. The maintainer's answer reframed the question and produced a new release blocker, which a silent decision would have missed entirely. `kapm7y` needs a reachable non-default disposition to prompt for, so this plan is its prerequisite. | yes |
