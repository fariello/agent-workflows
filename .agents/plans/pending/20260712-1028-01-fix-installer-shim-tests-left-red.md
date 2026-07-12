# IPD: Fix two red tests left by the installer-shim execution (cross-check of Gemini's work)

- Date: 2026-07-12
- Concern: correctness / test integrity. Cross-checking Gemini's execution of
  `20260712-0954-01-installer-shim-detection-ctrlc-and-diff` (commit 6971756) found the ENGINE work
  is sound but the SUITE was left RED: 2 of the newly-added interactive tests fail. A plan is not
  "executed" while its own new tests fail. This IPD fixes the two tests (and one small scope note).
- Scope: `tests/test_installer.py` only (the two failing tests + assertions). No engine.py change is
  required - the implementation is correct. Plus a DECISIONS note.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): created while cross-checking Gemini's
  execution of 0954-01. Root-caused 2 red tests. Complete proposal; born to-review.

## What Gemini did well (do NOT re-do)

Verified against commit 6971756:
- BUG-1 fixed correctly: `is_shim_customized_vs_expected(content, expected)` compares the on-disk
  shim to the freshly-generated `expected` (template-truth), replacing the drifted allowlist.
- PL-1 handled: a separate `is_stale_shim_customized` (structural allowlist) covers the prune path
  where no expected shim is renderable. Correct fallback.
- BUG-2: the four `except (KeyboardInterrupt, EOFError)` sites narrowed to `except EOFError` (decline);
  Ctrl-C now propagates to the `main()` guard (verified: `main` catches KeyboardInterrupt -> 130).
- BUG-3: `[y/N/d]` loop with `print_shim_diff` reusing `difflib.unified_diff`. Correct.
- The KEY drift-guard test `test_shim_expected_does_not_warn` (generates every manifest shim and
  asserts none is flagged) PASSES - this is the test that would have caught the original bug.
- `test_eof_declines_install` and `test_hand_edited_and_legacy_shims` PASS.

## The problem: 2 red tests (VERIFIED by running the suite)

`python3 -m unittest discover -s tests -t .` -> `Ran 201 tests ... FAILED (failures=2)`:

1. `test_ctrl_c_aborts_install` -> `AssertionError: 0 != 130`. ROOT CAUSE: the test writes a modified
   `.opencode/commands/assess.md` and expects the overwrite prompt to fire so a mocked
   `KeyboardInterrupt` aborts with 130. The prompt never fires in that setup (the modified content
   does not reach the shim-overwrite prompt path as the test assumes), so `input()` is never called,
   Ctrl-C is never raised, and `main()` returns 0. The ENGINE is correct; the TEST setup does not
   reach the prompt.
2. `test_diff_option_re_prompts` -> `AssertionError: 'Diff:' not found`. ROOT CAUSE: the test does
   `@mock.patch("builtins.input")` with `side_effect=["d","n"]`, then invokes the installer via
   `run_installer(...)` which runs a SUBPROCESS. `builtins.input` is patched only in the parent
   process, so the subprocess prompt never sees the mock; `d` is never sent and no diff prints.

## Proposed changes (ordered, validatable)

1. **Fix `test_ctrl_c_aborts_install`.** Make the test reliably reach the shim-overwrite prompt, then
   assert `main()` (in-process) returns 130 on `KeyboardInterrupt`. Concretely: install once and
   commit; then make the on-disk shim genuinely DIFFER from its generated expected content in a way
   the overwrite path detects (so `is_shim_customized_vs_expected` is True and the interactive prompt
   is reached), while keeping the working tree clean so the run proceeds to that file. Patch the
   in-process `builtins.input` (the test already calls `INS.main(argv)` in-process, which is correct)
   to raise `KeyboardInterrupt`. Assert `INS.main(argv) == 130` and that the shim was NOT overwritten.
2. **Fix `test_diff_option_re_prompts`.** It must run the installer IN-PROCESS (call `INS.main(argv)`
   with `builtins.input` mocked to `["d","n"]` and capture stdout), NOT via `run_installer` (a
   subprocess the mock cannot reach). Assert the diff output (`Diff:` header and a `+`/`-` line)
   appears and that after `n` the file is left unchanged. Mirror the working in-process pattern used
   by `test_ctrl_c_aborts_install`/`test_eof_declines_install`.
3. **Scope note (no code change).** Gemini also added an unrequested `--diff` flag + `test_diff_mode`
   (a whole-repo diff preview). It is harmless and passes; KEEP it but record that it was beyond the
   0954-01 scope, so the addition is tracked rather than silent. If undesired, retire separately.
4. **Validate.** `python3 -m unittest discover -s tests -t .` is fully GREEN. Also re-run the two
   fixed tests in isolation to confirm they now genuinely exercise the prompt (not vacuously pass).
5. **DECISIONS.** A short entry (D62) recording that 0954-01 was executed by Gemini, cross-checked
   here, engine sound, two interactive tests were left red due to prompt-not-reached and
   mock-vs-subprocess setup errors, now fixed. Cross-reference 0954-01.

## Deferred / out of scope

- Any engine.py behavior change (not needed; the implementation is correct).
- Re-litigating the 0954-01 design (already reviewed twice and sound).

## Open questions

1. Keep or retire Gemini's unrequested `--diff` whole-repo preview flag? (Lean: KEEP - it is small,
   passing, and useful; just record it. Confirm.)

## Approval and execution gate

`to-review`. Next: `/plan-review`, resolve OQ, human approve, execute changes 1-5, validate (suite
fully green), commit (never push), `git mv` to executed/. Not auto-executed. Either agent may execute;
it touches only `tests/test_installer.py` + DECISIONS, so it will not collide with engine work.
