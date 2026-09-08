- Id: rbftpl
- Status: graduated
- Blocks-Release: next
- Set: runverdict
- Priority: medium
- Work-Kind: bug
- Summary: The runner reads only 'verdict' from the verification outcome: the substantive evidence/tests_run/corrections_made fields all 28 verifiers populated are written, committed, and then ignored by every gate

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan bxx9af (Set runverdict, Order 05, .aw/records/plans/pending/20260908-runverdict-05-bxx9af-...ipd.md), which carries From-Backlog: rbftpl and inherits this item's Blocks-Release: next. Status graduated (design handed off), NOT done. NOTHING IN THIS ITEM IS OBSOLETE, but EVERY LINE NUMBER HAD DRIFTED ENORMOUSLY and was re-located BY SYMBOL at HEAD 8b4e1570: the v_data read cited at oc_runipd.py:2171-2172 is now :6421-6422 (~4250 lines), agy_runipd.py:2248-2249 is now :3685-3686, and the prompt schema cited at oc_runipd.py:1610-1620 is now :4915-4919. The core claim holds exactly: v_data is read in precisely two places, one per host, and only for 'verdict'; evidence, tests_run, corrections_made and summary are consumed by no gate, aggregate or report. THIS ITEM'S ORDERING CONSTRAINT IS STILL BINDING AND ITS SIBLING IS STILL UNOWNED, so it is carried as the plan's BLOCKING open question rather than silently absorbed: wyw936 is - Status: open with no plan, and I verified the fail-open directly - the gate downgrades only on 'BLOCKED' or 'NOT CONFORMING' (oc_runipd.py:6423-6428) and the schema's own CORRECTION_REQUIRED verdict appears NOWHERE outside the prompt string (one occurrence per host, oc_runipd.py:4915 / agy_runipd.py:2575), so CORRECTION_REQUIRED is recorded 'verified' today. I also found TWO FURTHER FAIL-OPEN BRANCHES this item did not name, both defaulting to verified: the 'except Exception' around the JSON parse and the 'else' when no outcome file exists (oc_runipd.py:6430-6434); the plan closes them too, because a fix guarding only the parsed path leaves the hole one branch over. THE ONE MEASUREMENT THAT MATERIALLY RESHAPES THE WORK, and the reason this was not transcribed literally: THIS ITEM'S OWN PROPOSED BAR WOULD FAIL CLOSED ON MOST REAL VERIFICATIONS. The fix sketch says to 'require tests_run to be non-empty with at least one entry carrying a command AND an exit code', while test (c) demands that all the existing recorded outcomes still satisfy the new requirement. Those two contradict each other against the real corpus. Evaluated at HEAD 8b4e1570 over the 34 verification outcomes now recorded (this item measured 28, so the producing side is still healthy and has grown): ALL 34 populate BOTH tests_run and evidence, 0 leave either empty, but only 10 of 34 satisfy the command-AND-exit-code shape, so the sketch would reject 24 of 34 GENUINE verifications. THE CAUSE is that tests_run is not uniformly typed: of 258 total entries, 132 are dicts and 126 are BARE STRINGS carrying the same facts in prose (measured example: 'python -m unittest tests.test_release_gate_close -v -> Ran 25 tests in 0.102s OK (exit 0): ...'), and even among dicts only 110 of 126 carry an exit code. The plan therefore SURVEYS the corpus FIRST (E-01) and calibrates the predicate to accept both shapes (E-02), then pins a COMMITTED FIXTURE corpus as the regression fence (E-03) rather than reading .aw/records/runs/, which is gitignored with zero tracked files and would make the test pass on one box and fail in CI. Graduated in full: the fail-closed gate in both hosts, the execution-report.md and aw runs surfacing, and the interaction check with the integration gate. DELIBERATELY NOT GRADUATED: the verdict-vocabulary fix (wyw936's, per this item's own ordering note) and the session-log cross-check for fabricated evidence (test (e)), which this item itself says to scope separately if expensive - it is, and the plan records prose-acceptance as the acknowledged residual weakness rather than overselling the predicate as fabrication-proof. NOTED FOR THE EXECUTOR: reviewed plan r2i1b1 declares the same four modules for the same two render surfaces, so E-07 must extend its shared accessor rather than fork one. Siblings wyw936, vlf75p and t74o5q all remain open and are not mine to touch.
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

ROOT CAUSE (in-tree, verified): the verifier outcome schema requests five fields, the verifiers fill
them in substantively, and the runner reads exactly ONE. `build_verifier_prompt` asks for
`schema_version, id6, verdict, summary, evidence, tests_run, corrections_made`
(`oc_runipd.py:1610-1620`, `agy_runipd.py:1702-1712`). The only consumption is:

    grep -n "v_data" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
      oc_runipd.py:2171   v_data = json.loads(...)
      oc_runipd.py:2172   verify_verdict = str(v_data.get("verdict", "")).upper()
      agy_runipd.py:2248  v_data = json.loads(...)
      agy_runipd.py:2249  verify_verdict = str(v_data.get("verdict", "")).upper()

`evidence`, `tests_run`, `corrections_made` and `summary` are never read by any gate, aggregate, or
report. They are written to disk, committed, and ignored.

MEASURED (the producing side is HEALTHY -- this corrects an assumption made earlier in the audit):
all 28 recorded verification outcomes populate BOTH fields; 0 of 28 left either empty. The content is
not boilerplate. Example (`run-20260829T191652Z-4134000/outcomes/02-8zgybk-verification.json`)
records three commands with exit codes, including an independently reproduced phase gate
(`15 passed, 4 xfailed in 1.54s`, EXIT=0) and a MUTATION test: deleting a table row from the code under
test and confirming the suite then fails with the expected message. Evidence strings cite commits and
`git show --name-status` output. So the verifiers are doing real work whose product is discarded.

CONSEQUENCE: `verified` is currently a single opaque bit. Nothing distinguishes the mutation-testing
verifier above from one that pasted nothing and asserted success, because only `verdict` is inspected.
That makes the fleet-level 28/28 VERIFIED uninterpretable: it cannot be told apart from 28
rubber-stamps, which is why this item exists alongside wyw936. It also means the framework's own
principle -- claims require pasted evidence -- is enforced on HUMAN-facing IPD validation items but not
on the machine-readable verifier record that gates merging.

FIX SKETCH: make the gate consume what it asked for. Minimally: require `tests_run` to be non-empty
with at least one entry carrying a command AND an exit code before `verify_disp` may be `verified`; treat
a `VERIFIED` verdict with no test evidence as NOT verified (fail closed, consistent with wyw936).
Surface `tests_run`/`corrections_made` in the run's `execution-report.md` and in `aw runs` so a
maintainer can audit what a verification actually did without opening JSON. Consider recording whether
the verifier's commands were actually EXECUTED in the turn (cross-check the claimed commands against the
session log's tool calls), which would catch a fabricated evidence block; that cross-check is the
strongest version and should be scoped separately if it proves expensive.

ORDERING NOTE: this item should land AFTER or WITH wyw936. Tightening evidence requirements while the
verdict gate still fails open would add a second fail-open path (an evidence check whose failure mode is
also "record verified"), so both must fail closed together to be worth anything.

TEST: (a) a `VERIFIED` outcome with empty `tests_run` fails CLOSED and does not reach finalize; (b) a
`tests_run` entry missing an exit code does not satisfy the requirement; (c) the 28 EXISTING recorded
outcomes all still satisfy the new requirement (a regression corpus proving the bar is not set above
what good verifiers already produce); (d) `execution-report.md`/`aw runs` render the commands and exit
codes for a verified turn; (e) a fabricated `tests_run` naming a command absent from the session log is
detected (if the cross-check is in scope).

RELATION: siblings in this Set are wyw936 (the gate cannot express rejection), vlf75p (the record
cannot attribute or price) and t74o5q (the verification often never ran at all). Together: the runner asks for a rigorous verification, cannot record its
rejection, does not read its evidence, and cannot say which model produced it.
