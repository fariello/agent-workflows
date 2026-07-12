# IPD: Fix installer shim false-positive, Ctrl-C abort, and add a diff view on conflict

- Date: 2026-07-12
- Concern: installer correctness + UX. Three bugs observed installing into `a consuming repo clone`:
  (1) the installer flagged its OWN freshly-generated `plan-review` command shims as having "manual
  modifications" (false positive); (2) Ctrl-C at the overwrite prompt was swallowed and the install
  CONTINUED instead of aborting; (3) there is no way to SEE what differs when a file is flagged, which
  would have immediately revealed that bug #1 was a false positive.
- Scope: `agent_workflows/engine.py` (the `is_shim_customized` heuristic; the four interactive
  `input()` prompt sites; a diff renderer reused from the existing `difflib` usage at ~engine.py:1512)
  + tests + DECISIONS. Behavior change to Ctrl-C semantics and the conflict prompt.
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): three bugs root-caused from a real
  a-consuming-repo install log; verified against source. Complete proposal; born to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED;
  PR-1 (reconcile EOF vs Ctrl-C with the existing main() guard - dedicated per-prompt EOF decline,
  Ctrl-C propagates to abort), PR-2 (base BUG-1 fix on the existing `shim_body` generator, verified
  at engine.py:392, per command+tool), PR-3 (the drift-guard test must GENERATE shims from the
  manifest, not hardcode them). All 4 OQs resolved interactively. No BLOCKER/HIGH. Status -> reviewed.

## Plan-review record (2026-07-12)

Reviewed by `/plan-review` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: APPROVE WITH REVISIONS
APPLIED (pending human sign-off). Evidence re-verified against source: the 4 inner
KeyboardInterrupt-swallowing sites (:759/:960/:1348/:1699), `is_shim_customized` returns True on the
generated plan-review shim (the false positive), the `difflib` renderer (:1461/:1515), the D56 main()
guard treating EOF and Ctrl-C alike (:2380), and `shim_body` as the canonical generator (:392).
Findings PR-1/PR-2/PR-3 fixed in place; no BLOCKER/HIGH; no over-scope (diff limited to the overwrite
prompt for v1). Rubric B-security/C-scale/F-UI justified Not Applicable (local file-op installer).
Does not self-approve.

## Project conventions discovered (Step 0, VERIFIED against source)

- Observed log (a-consuming-repo, via the deprecated `install-workflows.py` shim -> engine): two
  `Warning: .claude/.opencode/commands/plan-review.md has manual modifications.` prompts, each
  answered by Ctrl-C, after which the install printed COMPLETE (staged, not committed). It did NOT
  overwrite the flagged files (correct no-clobber), but the warning was FALSE and Ctrl-C did not
  abort.
- BUG 1 (false positive): `is_shim_customized()` (engine.py:1375) decides "hand-edited" via a
  hardcoded ALLOWLIST of standard shim line-prefixes/keywords. The current `plan-review` shim template
  emits two lines NOT in that allowlist - "If the user provided arguments, treat them as the target
  path(s)..." and "Treat the referenced file as the controlling instruction..." - so the function
  returns True on the installer's OWN output. VERIFIED: `is_shim_customized(<generated plan-review
  shim>) == True`. The detector has drifted from the shim template and has NO unit test.
- BUG 2 (Ctrl-C continues): the overwrite prompt (engine.py:753-761) and three sibling prompts
  (delete-stale :956-962, select-option :1347-1348, commit :1693-1699) catch
  `except (KeyboardInterrupt, EOFError)` and set `choice="n"` then CONTINUE. The clean-exit guard added
  in D56 wraps `main()` (engine.py:2381) but is UNREACHABLE because these inner handlers swallow the
  interrupt first. Net effect: Ctrl-C means "decline this one and proceed", not "abort".
- BUG 3 (no diff): when a file differs, the installer prints only "has manual modifications". A
  colorized `difflib.unified_diff` renderer ALREADY EXISTS in the repo (engine.py:1512+, the
  AGENTS/preview diff path) and can be reused; no new dependency.
- Constraints: no-clobber is correct and must stay; stage-never-commit; `--yes`/non-interactive must
  stay non-interactive; house rule no em dashes.

## Proposed changes (ordered, validatable)

1. **Fix the shim false-positive (BUG 1).** Replace the fragile allowlist heuristic with a
   template-truth comparison against the EXISTING generator: a shim is "customized" only if it does
   NOT match what `shim_body(command, workflow, tool)` (engine.py:392, the same function that
   GENERATES shims) would produce now. PR-2 (VERIFIED): `shim_body` is the single source, and it
   already handles every command type (plain workflow, concern lens, persona) - so "expected" is
   definitionally correct per command and per tool, and the check cannot drift from the template
   because it reuses the template. Comparison normalizes trivial whitespace and ignores the
   description/front-matter fields that legitimately track the manifest; only body differences beyond
   the generated output count as customization. Callers pass the command + workflow + tool so the
   right expected shim is rendered. Keep `is_shim_customized` as a thin back-compat wrapper only if a
   call site cannot supply that context; prefer the context-aware comparison everywhere it is reachable.
2. **Ctrl-C aborts the whole install cleanly (BUG 2).** At every interactive prompt, `KeyboardInterrupt`
   must ABORT the run (propagate to the `main()` guard -> clean "Cancelled.", exit 130), NOT set
   `choice="n"` and continue. At the four sites (:759, :960, :1348, :1699), STOP catching
   `KeyboardInterrupt`; let it propagate.
   - PR-1 (reconcile with the existing guard): the D56 `main()` guard (engine.py:2380-2386) currently
     treats BOTH `KeyboardInterrupt` AND `EOFError` as `return 130` (abort). The plan wants EOF to be
     a per-prompt "decline / safe default", NOT a whole-run abort. To make these consistent, each
     prompt site keeps a DEDICATED `except EOFError` that returns the safe default for that prompt
     (decline), while `KeyboardInterrupt` is NOT caught locally and propagates to the guard. The guard
     keeps its `KeyboardInterrupt -> 130`; whether the guard should still also catch `EOFError` (as a
     last-resort) is OQ2. Net intended behavior: Ctrl-C aborts the run; Ctrl-D/EOF declines the
     current prompt and continues.
3. **Add a diff view on conflict (BUG 3).** When a file differs and the run is interactive, offer
   `[y/N/d]` where `d` prints a colorized unified diff (current vs. what the installer would write),
   reusing the existing `difflib.unified_diff` renderer, then re-prompts. In non-interactive/`--yes`
   runs, behavior is unchanged (no prompt). This turns "has manual modifications" from an opaque
   warning into an inspectable decision - and would have exposed BUG 1 instantly.
4. **Tests.** Add the missing coverage: (a) for EVERY command in the manifest, GENERATE its shim via
   `shim_body(...)` and assert the detector does NOT flag that generated shim as customized (PR-3:
   generate from the manifest, do NOT hardcode sample shims, so the test cannot drift either - this is
   the loop-closing test that was missing and would have caught this bug); (b) a genuinely hand-edited
   shim IS flagged; (c) Ctrl-C at the overwrite prompt aborts with 130 (patch `input` to raise
   KeyboardInterrupt; assert the run returns 130 and does NOT process further files); (d) EOF at a
   prompt DECLINES that prompt and continues (patch `input` to raise EOFError; assert the file is
   skipped and the run proceeds) - locking in the PR-1 Ctrl-C-vs-EOF distinction; (e) the `[y/N/d]`
   diff branch prints a diff and re-prompts (patch input to feed `d` then `n`).
5. **DECISIONS + docs.** DECISIONS entry (Dnn) recording the template-truth detection, Ctrl-C-aborts
   (vs EOF-declines) semantics, and the diff-on-conflict affordance. Note in the installer's help/docs
   that Ctrl-C aborts and `d` shows a diff.

## Open questions (ALL RESOLVED with maintainer 2026-07-12 via /plan-review)

1. Ctrl-C vs EOF: RESOLVED - Ctrl-C ABORTS the whole run (exit 130, via the main() guard); Ctrl-D/EOF
   DECLINES the current prompt and continues (each site keeps a dedicated `except EOFError -> safe
   default`). The main() guard keeps its `EOFError -> 130` only as a last-resort for an EOF not caught
   at a prompt; prompts handle EOF locally so it does not reach the guard in normal flow.
2. #1 approach: RESOLVED (evidence, not preference) - compare the on-disk shim against
   `shim_body(command, workflow, tool)` (engine.py:392), the SAME generator, per command + tool.
   Template-truth cannot drift. Expanding the allowlist was rejected (it would drift again).
3. Diff prompt shape: RESOLVED - `[y/N/d]`; `d` prints the colorized unified diff then RE-PROMPTS.
   On-demand (quiet by default), not always-shown.
4. Diff scope: RESOLVED - the overwrite prompt for v1; extend the same affordance to the stale-delete
   and AGENTS-block prompts in a follow-on if useful (KISS).

## Approval and execution gate

`to-review`. Next: `/plan-review` (two-commit per D52), resolve OQs interactively (D60), human
approve, execute changes 1-5, validate (suite green + a real re-install of this repo showing NO false
"manual modifications" warning and a clean Ctrl-C abort), commit (never push), `git mv` to executed/.
Not auto-executed.
