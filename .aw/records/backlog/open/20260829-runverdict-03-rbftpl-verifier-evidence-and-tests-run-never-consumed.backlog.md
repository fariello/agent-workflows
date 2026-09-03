- Id: rbftpl
- Status: open
- Blocks-Release: next
- Set: runverdict
- Priority: medium
- Work-Kind: bug
- Summary: The runner reads only 'verdict' from the verification outcome: the substantive evidence/tests_run/corrections_made fields all 28 verifiers populated are written, committed, and then ignored by every gate

## Workflow history
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
