# Review findings: plan 0e41gc

- Subject-Id: 0e41gc
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `04ba026c0` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `leak_sanitizer.main(argv, *, context=None)`: the `if args.fix:` branch and both scan `except` handlers return before `ctx = context or select_output(args)` (F-06).
- `cli._run_check_local_leaks` ends `return leak_sanitizer.main(passthrough, context=context)` (F-07).
- `_prompt_stdin` uses `input(f"Rewrite leak-class paths in {rel}? [y/N] ")`; in-process probe with stdin at EOF: `--fix --agent` rc 0, stdout is the prompt; `--fix --dry-run --agent` and `--json` rc 0, stdout empty, stderr `would rewrite: a.md` (F-04, F-05).
- `CommandResult.to_agent_record`: exit 2 or `cannot-run` -> `kind: error`, `verified/complete: False`; `applied` set False for preview; `next` from `next_actions[0]`; `assert_valid_agent_record` runs, and `AgentRenderer.render` degrades a `ValueError` to an exit-2 error record.
- `agent_schema.validate_agent_record`: `preview` is not in `POSITIVE_OUTCOMES`; exit 0 with `ok`/`clean`/`preview` valid; exit 1 with `findings` valid.
- `docs/cli-output-contract.md` 11.3 (mutation feedback), 11.4 (cannot-run records), 7 (no diagnostic duplicated across streams).
- `input()` under pytest capture raises `EOFError` after writing the prompt (probe), so baseline E-02 row (e) cannot hang.
- Backlog `k84fqu` is `graduated`, `bug`, `Blocks-Release: next`; the plan inherits both.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Testing / sequencing | E-03 "with and without `--fix`" vs E-05 OQ-01 refusal | Bare `--fix` under a machine context is refused by E-05 before `fix_working_tree` runs, so the E-03 "with `--fix`" not-a-git-repo row would pass via the refusal and never exercise the fix branch's `CalledProcessError` handler (E-04). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now uses `--fix --yes` and asserts `next == "aw sanitize --help"`, which distinguishes the handler from the refusal. |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Anti-regression | Scope "HUMAN path ... byte-identical"; E-05 "Keep the human `--fix` prose ... byte-identical" | Human `--fix` byte-identity was asserted only in prose; E-03 controls cover only exit-2 branches, so an E-05 restructure could alter `would rewrite:`/`rewrote:`/`No auto-fixable` output undetected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds human `--fix` controls (dry-run, yes, clean) pinning exact stderr, empty stdout and exit; V-02/V-05 demand them. |
| PR-003 | MEDIUM | IN-SCOPE | C. Stream contract | `docs/cli-output-contract.md` Section 7 "Diagnostics are never duplicated across both streams"; scan branch emits no prose under machine ctx | Plan did not say whether machine-mode `--fix`/error paths still print the human prose to stderr; ambiguous for the executor and untested. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/E-05 state machine mode prints no human prose; E-02 asserts its absence on stderr and E-03 asserts stderr empty. |
| PR-004 | LOW | IN-SCOPE | E. Test isolation | `tests/test_release_readiness.py` `monkeypatch.setenv("GIT_CEILING_DIRECTORIES", ...)` | A "not a git repo" tmpdir is only non-repo if no enclosing repo exists above `TMPDIR`; without a ceiling the test is environment-dependent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and E-03 set `GIT_CEILING_DIRECTORIES` to the tmpdir parent, saved/restored like the `XDG_CONFIG_HOME` pin. |
| PR-005 | LOW | IN-SCOPE | B. Command safety | E-05 `next` = `aw sanitize <dir> --fix --yes` | A user-supplied `dir` with spaces would yield a non-executable `next` command. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 requires `shlex.quote(args.dir)`. Row (d) also asserts the `private-repo` rule is reported. |
| PR-006 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked scope-as-declaration (`--scope-reason`/`--scope-ack`), `aw ipd begin`, staged-set check, the do-not-claim-done rule, conditional runner/executor finalize ownership with a never-`git mv` rule, and the `Blocks-Release` handoff. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate extended with all elements; existing valid STOP on the absent `wyy09f` precondition retained (prerequisite-absent case). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Under a machine context, should `--fix`/error paths still print human prose to stderr? | No; the record is the single diagnostic | Keep stderr prose alongside the record | `docs/cli-output-contract.md` Section 7; scan branch in `leak_sanitizer.main` emits no prose under machine ctx | yes |
| D-2 | Which `--fix` variant should E-03's not-a-git-repo row use? | `--fix --yes` | Bare `--fix` (hits OQ-01 refusal); `--fix --dry-run` (also valid, but `--yes` mirrors the apply path) | E-05 (i) ordering refuses before `fix_working_tree` | yes |
| D-3 | OQ-01 (author-resolved): refuse un-attested machine `--fix`? | Accepted as authored | Silently decline (greenwash `clean`); prompt on stderr | `artifact_adopt._emit("cannot-run", 2, ...)` precedent; probe shows `input()` writes to stdout | yes |
