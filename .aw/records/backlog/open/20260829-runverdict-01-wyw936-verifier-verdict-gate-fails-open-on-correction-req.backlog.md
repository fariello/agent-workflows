- Id: wyw936
- Status: open
- Blocks-Release: next
- Set: runverdict
- Priority: high
- Work-Kind: bug
- Summary: Both runners' verifier gate fails OPEN: only BLOCKED/NOT CONFORMING downgrade, so the schema's own CORRECTION_REQUIRED verdict (and any typo/empty/garbage) is recorded 'verified' and proceeds to finalize+merge

## Workflow history
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

ROOT CAUSE (in-tree, verified): the verifier PROMPT asks for a three-value verdict, but the GATE that
consumes it can only express two outcomes, and its fallback is the permissive one. `build_verifier_prompt`
instructs the model to write `"verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED"`
(`oc_runipd.py:1614`, `agy_runipd.py:1706`). The consuming gate (`oc_runipd.py:2169-2184`, duplicated
BYTE-IDENTICALLY at `agy_runipd.py:2246-2261`) is:

    verify_verdict = str(v_data.get("verdict", "")).upper()
    if "BLOCKED" in verify_verdict or "NOT CONFORMING" in verify_verdict:
        verify_disp = "blocked"; disposition = "partial"
    else:
        verify_disp = "verified"

`CORRECTION_REQUIRED` matches neither substring, so it lands in the `else` and is recorded `verified`.
There is no third branch, and the default is to pass.

MEASURED (the branch above, replicated exactly on the real strings):
  'VERIFIED'            -> ('verified', unchanged)
  'CORRECTION_REQUIRED' -> ('verified', unchanged)   <- a schema-valid REJECTION, silently accepted
  'FAILED'              -> ('verified', unchanged)
  'REJECTED'            -> ('verified', unchanged)
  ''                    -> ('verified', unchanged)
  'garbage'             -> ('verified', unchanged)
  'BLOCKED'             -> ('blocked', 'partial')
  'NOT CONFORMING'      -> ('blocked', 'partial')

So two of the three DOCUMENTED verdicts fail open, as does any typo, any unknown value, and an empty or
missing verdict key. `except Exception: verify_disp = "verified" if v_rc == 0 else "unverified"`
(`oc_runipd.py:2181`) means unparseable JSON with a zero exit ALSO reads as verified.

CONSEQUENCE: `verify_disp == "verified"` is the gate precondition for self-finalize and lane
integration (`oc_runipd.py:673-674`: "verify_disp == 'verified' is the gate precondition for reaching
integration"). A verifier that does its job and reports `CORRECTION_REQUIRED` therefore has its
rejection discarded, and the lane proceeds to `aw ipd finalize` and merges to main. This inverts the
framework's stated fail-closed posture for the one gate whose entire purpose is to catch bad work.

THE FIX ALREADY EXISTS AND IS NOT WIRED UP: `verify_roles.py` defines the correct state authority,
including `"verifying -> correction_required"` (`verify_roles.py:369`, `:511`) and
`"correction_required -> runnable"` (`verify_roles.py:422`, `:512`), i.e. a rejected turn returns to
runnable rather than completing. `run_state.py:34` defines `STATE_CORRECTION_REQUIRED` and
`agy_verifier.py:204` uses `FINAL_CORRECTION_REQUIRED` properly. But NEITHER runner imports any of it:
`grep -n "run_state\|verify_roles\|run_recovery" agent_workflows/oc_runipd.py` returns ZERO matches.
Importers are `agy_verifier`, `host_runner`, `migration_complex`, `orchestrate_isolation`,
`security_hardening` -- not `oc_runipd`/`agy_runipd`. This is a WIRING GAP between two of the repo's own
components, not a missing concept.

CORROBORATING FLEET EVIDENCE (why this went unnoticed): across 63 runs there are 28 recorded
verification outcomes and the verdict distribution is 28x VERIFIED, 0 CORRECTION_REQUIRED, 0 BLOCKED.
A 100% pass rate is consistent with a gate that cannot record a failure. By contrast the DETERMINISTIC
gates in the same runs refused 27 times (7 `ipd-finalize-refused` for stale/missing begin receipts and
an unacknowledged Scope-Paths discrepancy, 1 `ipd-begin-refused` for a dirty Scope-Path, 19
`orchestrator-deferred` for unfinished children). The deterministic checks catch things; this one never
has. NOTE the 28/28 is NOT proof the verifiers were wrong -- their evidence bodies are substantive (one
even ran mutation tests) -- but the gate could not have recorded a rejection had one been made.

SEVERITY (REVISED DOWN after measurement -- read this before acting): the original filing said "it can
silently merge work an independent verifier rejected". That OVERSTATED the active risk, and the
correction matters for prioritisation.

1. AUTO-MERGE IS SEPARATELY GATED ON THE SAME VARIABLE. Self-finalize requires
   `verify_disp == "verified"` (`oc_runipd.py:2309-2314`: `disposition in ("executed",
   "substantially-complete") and verify_disp == "verified"`). This bug corrupts what gets WRITTEN into
   that variable, but does not bypass the gate. Measured: 23 turns recorded `unverified` and none was
   auto-merged by the runner; the 5 spot-checked plans reached `executed/` through SEPARATE
   human-driven finalize commits (`08e22b1` g69y23, `71724de` iw793a).
2. THE FAIL-OPEN PATH HAS NEVER FIRED. Every one of the 34 recorded verification outcomes carries the
   exact string `'VERIFIED'`; there is not one `CORRECTION_REQUIRED`, typo, empty, or malformed verdict
   in the corpus. So this is a LATENT trap, not an active leak.
3. THEREFORE THERE IS NO BEHAVIOR CHANGE TO NEGOTIATE. The earlier "failing closed will start blocking
   lanes that currently merge" warning is FALSIFIED by (2): a correct gate would have changed the
   outcome of ZERO historical turns. That removes the argument for escalating this to a spec; it is a
   small mapping fix with a 34-case regression corpus that must all still pass.

It remains a real bug worth fixing BEFORE the verifier population becomes more willing to reject, since
`self_finalize` defaults to True (`oc_runipd.py:1427`) and the first genuine rejection would be
converted to `verified` and auto-merged. But it is not an emergency and, on this evidence, not a release
blocker. Sibling t74o5q (verification skipped entirely, fired 23 times) is the more urgent defect and
should probably be fixed first.

FIX SKETCH: delete the private two-way substring test from BOTH runners and consume the shared state
machine (`verify_roles`/`run_state`), exactly as sibling items resolve duplicated logic. Map the three
documented verdicts explicitly; treat ANY unrecognized/absent/unparseable verdict as NOT verified
(fail closed) rather than as verified; and on `correction_required` follow the declared transition back
to runnable instead of finalizing. Deduplicate the gate so the two runners cannot diverge again.

BEHAVIOR-CHANGE WARNING (deliberate, needs a human decision): making this fail closed WILL start
blocking lanes that currently merge, including on a garbled verdict from an otherwise-good turn. That
is the point, but it is an operational cost and may warrant a spec rather than a direct fix.

REPRO: run any `execute` item to a successful turn, have the verifier write
`{"verdict": "CORRECTION_REQUIRED", ...}` to
`.aw/records/runs/<run>/outcomes/<NN>-<id6>-verification.json`, and observe the run state record
`verification_status: verified` and proceed to finalize/integration.

TEST: (a) a `CORRECTION_REQUIRED` verdict yields NOT-verified and does not reach finalize; (b) an
unknown verdict (`FAILED`, `REJECTED`, `''`, absent key, malformed JSON) fails CLOSED; (c) `BLOCKED`
still downgrades as today (no regression); (d) `VERIFIED` still passes; (e) an AST/import guard
asserting neither runner defines its own verdict-substring test, so the two copies cannot diverge again.

RELATION: same class as y9lcem (runner reimplements a parser the schema already owns) -- a runner
carrying private logic that duplicates and contradicts a shared, correct implementation. Siblings in
this Set: t74o5q (verifier turn dies on a stale plan path, so verification is SKIPPED -- fired 23
times, fix first), vlf75p (model + rate card not recorded) and rbftpl (verifier evidence never
consumed).
