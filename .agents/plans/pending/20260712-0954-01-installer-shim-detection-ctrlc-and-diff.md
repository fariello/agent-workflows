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
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): three bugs root-caused from a real
  a-consuming-repo install log; verified against source. Complete proposal; born to-review.

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
   template-truth comparison: a shim is "customized" only if it does NOT match what the installer
   WOULD generate for that command now (compare against the freshly-rendered shim body, ignoring
   volatile fields like the description line and trivial whitespace). Concretely: render the expected
   shim for the command and compare normalized bodies; only differences beyond the generated template
   count as customization. This makes an unmodified current-format shim NEVER flagged, and it cannot
   drift from the template because it IS the template. Keep `is_shim_customized` as a thin wrapper if
   other call sites need it, but base the decision on template equality.
2. **Ctrl-C aborts the whole install cleanly (BUG 2).** At every interactive prompt, `KeyboardInterrupt`
   must ABORT the run (propagate to the `main()` guard -> print a clean "Cancelled.", exit 130), NOT
   set `choice="n"` and continue. Remove the inner swallowing of `KeyboardInterrupt` at the four sites
   (:759, :960, :1348, :1699); let it propagate. Keep EOF (`EOFError`, Ctrl-D) handling DELIBERATE and
   per-prompt (treat as "decline this prompt / use the safe default") since piped/EOF input is a
   different intent than an explicit interrupt - do NOT conflate the two. Verify the D56 `main()`
   guard (engine.py:2381) then produces the clean 130 exit.
3. **Add a diff view on conflict (BUG 3).** When a file differs and the run is interactive, offer
   `[y/N/d]` where `d` prints a colorized unified diff (current vs. what the installer would write),
   reusing the existing `difflib.unified_diff` renderer, then re-prompts. In non-interactive/`--yes`
   runs, behavior is unchanged (no prompt). This turns "has manual modifications" from an opaque
   warning into an inspectable decision - and would have exposed BUG 1 instantly.
4. **Tests.** Add the missing coverage: (a) an unmodified current-format shim for EVERY generated
   command is NOT flagged customized (guards against future template drift - this is the test that was
   missing); (b) a genuinely hand-edited shim IS flagged; (c) Ctrl-C at the overwrite prompt returns
   130 and aborts (patch `input` to raise KeyboardInterrupt; assert no further files processed); (d)
   the `[y/N/d]` diff branch prints a diff and re-prompts (patch input to feed `d` then `n`).
5. **DECISIONS + docs.** DECISIONS entry (Dnn) recording the template-truth detection, Ctrl-C-aborts
   (vs EOF-declines) semantics, and the diff-on-conflict affordance. Note in the installer's help/docs
   that Ctrl-C aborts and `d` shows a diff.

## Open questions (v1 leans for review)

1. Ctrl-C vs EOF: RESOLVED lean - Ctrl-C ABORTS the whole run (exit 130); EOF/Ctrl-D stays a
   per-prompt "decline/safe-default" (piped-input intent). Confirm both semantics.
2. #1 approach: RESOLVED lean - compare against the freshly-rendered template (template-truth), not a
   maintained allowlist, so it cannot drift. Confirm vs. simply expanding the allowlist (rejected:
   would drift again).
3. Diff prompt shape: `[y/N/d]` re-prompting after showing the diff. Confirm vs. always-show-diff
   before the y/N prompt (louder but noisier for many files).
4. Should the same diff affordance apply to the stale-delete and AGENTS-block prompts too, or just the
   overwrite prompt for v1? (Lean: overwrite prompt now; extend later if useful - KISS.)

## Approval and execution gate

`to-review`. Next: `/plan-review` (two-commit per D52), resolve OQs interactively (D60), human
approve, execute changes 1-5, validate (suite green + a real re-install of this repo showing NO false
"manual modifications" warning and a clean Ctrl-C abort), commit (never push), `git mv` to executed/.
Not auto-executed.
