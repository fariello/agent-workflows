# Review: Make run_cli's module docstring agree with its own module, by pointing at the constants

- Subject-Id: arhzce
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged at lane HEAD `cd69009f0`, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified:

- The `EXIT_*` constants are exactly 0..7, and `re.findall(r'exit (\d+)', run_cli.__doc__)` gives `[0, 1, 2, 5, 7]` (F-01).
- Through `tests/test_run_recovery_cli.py` `TestRunCliSubcommands._materialize`:
  - The `bad-evidence` seed gives `run finalize` rc=4, printing `EV-FAILED-EXIT` (F-02).
  - The `root-performed` seed gives `run record S-01 performed` rc=6, printing `Illegal transition from 'performed' to 'performed'` (F-03).
- The backlog items `94op6l` and `2cqs11` exist and are open, and `h9kgjp` is `graduated`.
- `u28vqb` is `approved`, and its Scope-Paths exclude `run_cli.py` (F-06).
- `aw runs --help` does not carry the docstring (F-08).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Project rule P16 (E) | GUIDING_PRINCIPLES.md:174 "No text, banner, or docstring pins"; :179 "If ... editing a docstring breaks the test, the test is broken"; plan E-04(b), OQ-02 | E-04(b)'s guard asserts that `run_cli.__doc__` contains no `exit <digit>`. Only a docstring edit can turn it red, so it is exactly the docstring pin P16 forbids. Reading `__doc__` instead of the file does not change what is asserted, and the narrow exception covers published artifacts, while F-08 shows nothing consumes this docstring. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 is resolved: the guard is deleted rather than weakened, as OQ-02 itself prescribed. E-03's anchor comment is now the re-transcription defence. V-04 requires the new file not to exist. |
| PR-002 | MEDIUM | OVER-SCOPE | Duplicate coverage (C, P8) | tests/test_run_recovery_cli.py `TestRunCliSubcommands.INVOCATIONS` rows "finalize with a tool_event that exited nonzero" (`EXIT_INVALID_EVIDENCE`), "finalize refuses an incomplete run" (`EXIT_INCOMPLETE`), "cancel/finalize authored by the executor" (`EXIT_OPERATIONAL`) | E-04(a) would add a new file whose assertions already exist in the canonical exit-class table. The only unpinned path is `_run_record`'s `except run_state.RunStateError` arm, because `illegal/unauthorized transition` appears nowhere in `tests/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now adds one `INVOCATIONS` row for that arm. Its sensitivity was demonstrated: patching `EXIT_OPERATIONAL` to 99 in memory gives rc=99, against rc=6 unmutated. Scope-Paths now names `tests/test_run_recovery_cli.py` instead of the new file. F-09 was added. |
| PR-003 | MEDIUM | IN-SCOPE | Honest documentation (F) | agent_workflows/run_cli.py `write_index` (`out.parent.mkdir`, `out.write_text`); review probe of six `aw runs` leaves, `fs changed: False` x6 | E-02 left the corrected read-only wording unbounded. A natural rewrite ("only `aw run` writes") would be a fresh falsehood, because the module also exports `write_index`, which writes files. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now bounds the sentence to the measured `aw runs` leaves and names `write_index`. F-10 was added. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract (G) | plan "Approval and execution gate" | The gate was missing four things: a scope fence with the `--scope-reason`/`--scope-ack` reconciliation, `aw ipd begin`, the conditional ownership of the terminal transition (runner versus `aw ipd finalize`), and the post-execution `h9kgjp` close path. It also named `aw commit <plan>` instead of the id6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all four in place, and `aw commit arhzce -- <paths>` is now used. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the `__doc__` absence guard admissible under P16 (OQ-02)? | No. Delete it. | Keep it on the reading that `__doc__` is not "source"; weaken it to a narrower regex | GUIDING_PRINCIPLES.md:174, :179; plan OQ-02's own prescribed remedy | yes |
| D-2 | Where should the behavioral exit pins live? | One new row in the existing `INVOCATIONS` table | A new `tests/test_run_cli_exit_docstring.py` duplicating existing rows | tests/test_run_recovery_cli.py `INVOCATIONS`; P8 | yes |
| D-3 | How wide may the corrected read-only sentence be? | Only the measured `aw runs` leaves, with `write_index` named | "Only `aw run` writes" | `run_cli.write_index`; six-leaf mtime probe | yes |
