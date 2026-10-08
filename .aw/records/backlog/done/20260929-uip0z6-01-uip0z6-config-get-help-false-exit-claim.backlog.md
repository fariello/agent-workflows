- Id: uip0z6
- Status: done
- Graduated-To: uip0z6
- Blocks-Release: next
- Set: uip0z6
- Priority: medium
- Work-Kind: bug
- Summary: aw config get --help claims a nonzero exit for an unset variable that never happens

## Workflow history
- 2026-10-08 done (aw backlog): closed by aw agy run: IPD w89bo8 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-uip0z6-01-w89bo8-replace-the-false-exit-code-claim-in-the-config-get-help-wit.ipd.md); evidence .aw/records/plans/executed/20261001-uip0z6-01-w89bo8-replace-the-false-exit-code-claim-in-the-config-get-help-wit.ipd.md
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053053Z-3200037: w89bo8
- 2026-09-29 created (aw backlog): Filed at review of plan ypnk56 (/plan-review). Measured, not inferred.

`aw config get --help` states a contract the command does not honor, so a script written from the
help text branches on an exit code that never arrives.

THE FALSE CLAIM. The inline `description=` on the `config get` parser in `cli._build_parser` reads:

  "Exits nonzero when the variable is not set, so a caller can distinguish 'unset' from
  'set to an empty value'."

MEASURED (in-process, throwaway `XDG_CONFIG_HOME`, review HEAD `ec7f0068`):

  aw config get defaults.migrate_layout  -> exit=0, stdout=''   (recognized, unset)
  aw config get color_depth              -> exit=0, stdout=''   (recognized, unset)
  aw config get aw_home                  -> exit=0, stdout=''   (recognized, unset)
  aw config get no.such.key              -> exit=2              (UNRECOGNIZED, the only nonzero case)

WHY exit 0 IS THE CORRECT BEHAVIOR, so the fix is to the TEXT and not to the code.
`cli._run_config_get` ends with `elif val is None: print("")` then `return 0`, and the repository's
own test pins that: `tests/test_config.py::InstallPolicyDefaultsConfigTests::test_clearing_and_unset_removes_keys`
asserts `cli.main(["config", "get", "defaults.migrate_layout"]) == 0` with empty output, under the
comment "Verify config get outputs empty (unset)". Changing the exit code would break a shipped
contract; the help text is what is wrong.

CONSEQUENCE. The sentence does not merely omit something, it instructs the reader to do something
that cannot work: there is no exit code that distinguishes a recognized-but-unset key from one set to
an empty value, because both print an empty line and exit 0. A caller needing that distinction has to
read `config show` or the config file.

WHY IT WAS NOT CAUGHT. `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`
checks only that a description is non-empty, longer than its `help=`, and distinct from it. This
description is 335 characters against a 76-character help, so it passes the length contract while
being false. That is a real limit of the contract worth recording: it measures LENGTH, never accuracy.

FOUND BY. Review of plan `ypnk56` (F-10). That plan's own draft made the IDENTICAL false claim about
`config unset`, caught by driving the command before shipping it (`ypnk56` F-6); this item is the
already-shipped instance of the same error on the sibling verb. `ypnk56` deliberately does NOT fix it:
it edits `config unset` only, and widening to a sibling's prose would be unrequested scope.

SUGGESTED FIX. Replace the false sentence with the measured behavior: a recognized but unset variable
prints an empty line and exits 0, and only an UNRECOGNIZED name is refused with exit 2 naming the
valid keys. Check the other `config *` descriptions for the same class of unverified claim while
there. Any replacement must be DRIVEN, not reasoned: this defect exists because a plausible sentence
was never run.
