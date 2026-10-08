# IPD: Thread the resolved OutputContext into the leak sanitizer so --json and --fields reach the renderer

- Date: 2026-10-02
- Kind: child
- Concern: `aw sanitize --json` (and `aw check-local-leaks --json`) writes NOTHING to stdout and exits 0, so any caller that parses the advertised flag gets an empty string where a `CommandResult` payload was promised. The root cause is the hand-maintained passthrough argv in `cli._run_check_local_leaks`, which forwards `--agent` but never `--json`. Authoring found the backlog item's proposed remedy ("one forwarding line") WOULD NOT WORK and would convert a silent empty payload into a hard exit-2 usage error, because `leak_sanitizer.main`'s own inner parser declares no `--json` at all. The same dropped-flag mechanism also silently discards `--fields`, which the renderer does honor.
- Scope: Replace the argv-reserialization seam for this one command with context threading: pass the already-resolved `OutputContext` from `cli.main` into `_run_check_local_leaks` and on into `leak_sanitizer.main`, so `--json`, `--agent`, `--fields` and `--verbose` are honored by construction rather than by a list that must be kept in sync by hand. Add behavioral coverage asserting `--json` emits a parseable payload and `--fields` projects, on BOTH the `check-local-leaks` and `sanitize` spellings and on BOTH tree states (clean and with a planted leak). EXCLUDES any change to what the payload CONTAINS (home-path redaction is owned by `9yd6tx`), any change to the leak RULESET or scan modes, any refactor of the other forwarded driver leaves (`aw oc run`, `aw agy run` and siblings, which the output contract deliberately exempts), and any `aw check` rule generalizing dropped-flag detection.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/leak_sanitizer.py, tests/test_leak_sanitizer_machine_flags.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: xym8g8
- Blocks-Release: next
- Set: xym8g8
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: wyy09f

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: wyy09f verified (set xym8g8, attempt 1).
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED. Unsatisfiable 'prose still on stderr' and porcelain-clean demands replaced; --json vs --agent key vocab fixed; --fields scoped to --agent; --fix/exit-2 no-record defect filed as k84fqu. Record: .aw/records/reviews/20261002-xym8g8-01-wyy09f-thread-the-resolved-outputcontext-into-the-leak-sanitizer-so.review.md

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `xym8g8`. The item carries `- Blocks-Release: next` and `- Work-Kind: bug`; both are inherited unchanged, and F-07 re-derives why `bug` is correct under the repository's user-perceptible-impact test. THE ITEM'S 2026-09-30 CORRECTION NOTE VERIFIES IN FULL at HEAD `afa922f1dce3b9ff74c9d7f23b275f7b5c7a31d5`: `python3 -m agent_workflows check-local-leaks . --json` wrote ZERO bytes to stdout, exited 0, and sent `No local leaks found.` to stderr; the `--agent` contrast emitted a well-formed `aw.agent/v1` record on stdout; and `cli._run_check_local_leaks` forwards `--history`, `--max-commits`, `--wheel`, `--staged`, `--warn`, `--agent`, `--fix`, `--yes` and `--dry-run` while never forwarding `--json`. AUTHORING CORRECTS THE ITEM ON ONE POINT THAT CHANGES THE WORK, and it is the reason this plan does not take the shape the item suggests. The item says "the likely fix is one forwarding line" and that "`leak_sanitizer.main`'s own machine branch is correct and tests `if ctx.is_agent or ctx.is_json`, so the engine would honor `--json` if it ever received it". The SECOND half is true and the FIRST is false: the engine's `select_output(args)` would honor it, but the engine's own `argparse.ArgumentParser` at `leak_sanitizer.main` declares only `dir`, `--history`, `--max-commits`, `--wheel`, `--staged`, `--warn`, `--agent`, `--fix`, `--yes` and `--dry-run`, with NO `--json`. Authoring measured the proposed fix directly: `leak_sanitizer.main(['.', '--json'])` raises `SystemExit(2)` with `check-local-leaks: error: unrecognized arguments: --json`. So appending the one line would replace a silent empty payload with a hard usage error, which is strictly worse for the scripted caller the item is protecting. The minimum CORRECT argv fix is therefore TWO edits (declare the flag on the inner parser, then forward it), and authoring rejected even that in favor of context threading, because the inner parser is a second place the flag vocabulary must be kept in sync and the defect class is precisely a hand-maintained sync. AUTHORING ALSO FOUND A SECOND DROPPED FLAG the item does not mention: `--fields` is declared on the shared `common` parent, is honored by both machine renderers (`renderers` filters the record through `_schema.filter_record_fields` when `context.fields` is set), and is likewise absent from the passthrough list, so `aw sanitize --agent --fields cmd,outcome` emits the UNPROJECTED record. Verified by contrast against a direct renderer call with the same fields, which did project. That is the same bug with a different flag, so E-03 covers it and V-03 demands evidence for it. ONE AUDIT RESULT IS REPORTED AS A NON-FINDING, since the item asks for it: the item suggests "other forwarded leaves may drop flags the same way and are worth auditing in the same pass". Authoring audited every `passthrough` construction in `cli.py` and found exactly one other (`_run_plan_names`, forwarding to the `normalize_plan_names` script), which is UNREACHABLE DEAD CODE: the `plan-names` verb was removed in awcmdsurf Order 05 and `grep` finds no dispatch to the function. The genuinely live forwarded leaves (`aw oc run`, `aw agy run`, `aw run as`, `aw run ipd`, `aw agy sessions|view|exec`) forward argv VERBATIM and are DELIBERATELY exempt: `docs/cli-output-contract.md` Section 1.3 states "`--agent` and `--json` are NOT provided on the forwarded leaves, by either route", because on `aw oc run start` a downstream `--agent` is an OpenCode AGENT NAME. So the audit's honest answer is that this command is the only live instance, and widening scope to the drivers would VIOLATE a documented contract rather than fix a defect. E-06 nonetheless records a re-run of that audit at execution HEAD so the claim is not inherited on trust.

## Goal

Make `aw sanitize --json` and `aw check-local-leaks --json` actually emit the structured `CommandResult` payload the flag advertises, and remove the argv-reserialization seam that silently swallowed it, so a machine flag declared on the shared parent cannot be dropped by a list a human forgot to update.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure, and write the failing test before the fix

- [x] E-01 RE-DERIVE, at execution HEAD, the six facts this plan rests on, rather than trusting the numbers written here or in the backlog item, and record the HEAD sha. (1) That `python3 -m agent_workflows check-local-leaks . --json` still writes ZERO bytes to stdout with exit 0 and the prose on stderr; capture stdout and stderr to SEPARATE files, because the item's original note conflated them and that conflation is what made its first diagnosis wrong. (2) That `check-local-leaks . --agent` still emits a parseable `aw.agent/v1` record on stdout, which is the contrast proving the engine's machine path works. (3) That `leak_sanitizer.main(['.', '--json'])` still raises `SystemExit(2)` with `unrecognized arguments: --json`, since this is the fact that INVALIDATES the item's one-line remedy and the whole shape of this plan depends on it. (4) That `cli._run_check_local_leaks` still builds the passthrough list and still omits both `--json` and `--fields`. (5) That `--fields` is still honored by the renderer when it DOES arrive, by calling a renderer directly with `fields=['cmd','outcome']` and confirming the record is projected, since the fix is only worth making for a flag that has an effect. (6) That `_run_plan_names` is still unreachable (no dispatch site) and that the live forwarded driver leaves still forward verbatim. IF FACT (3) HAS CHANGED, meaning the inner parser now declares `--json`, STOP AND REPORT: the defect would then be a one-line forward and this plan is over-built.
  - Depends on: none
  - Expected outcome: a recorded execution-HEAD measurement of all six facts with the HEAD sha stated, each marked CONFIRMED or CORRECTED, with stdout and stderr captured separately for fact (1), plus an explicit STOP if fact (3) no longer holds.
  - Execution state: performed

- [x] E-02 ADD `tests/test_leak_sanitizer_machine_flags.py` asserting the `--json` contract, and confirm it FAILS at the unfixed baseline before any production edit. The test must drive the REAL CLI entry point (`cli.main(argv)`) over a scratch git repo, capturing stdout and stderr SEPARATELY (not combined, which is what `tests/test_local_leaks.py`'s `_run` helper does and is why it could not have caught this), then assert `json.loads(stdout)` succeeds and the parsed object's `command` is `check-local-leaks` and its `exit_code` equals the process exit code. These are the `--json` (full `CommandResult.to_dict`) key names, measured at review by rendering a `CommandResult` through `get_renderer` under a `--json` context: `schema`, `command`, `status`, `exit_code`, `summary`, `verified`, `complete`, `diagnostics`, `changes`, `evidence`, `next_actions`, `data`. They are NOT the `--agent` record names (`cmd`, `outcome`, `exit`); do not mix them. Also assert `status` is `clean` on the clean tree and `findings` on the planted tree, and that stderr is empty or carries no payload, so the payload cannot have leaked onto the wrong stream. CALL `cli.main` IN-PROCESS WITH `contextlib.redirect_stdout`/`redirect_stderr`, NOT a subprocess with `cwd` in a scratch repo: `leak_sanitizer.main` takes the repo as the positional `dir`, so pass the scratch repo path as that argument and never change the process cwd, which xdist workers share. PLANT the leak the way `tests/test_local_leaks.py` does, synthesizing the token at runtime (for example `"/home/" + "someuser" + "/secret/path"`) so the new test file holds no literal leak and does not itself trip the sanitizer, and pin `XDG_CONFIG_HOME` into the temp dir as that file's fixture does so a developer's user leak config cannot change the result. Assert this on BOTH tree states, clean and with a planted leak, since the states take different branches (`status` `clean` versus `findings`, exit 0 versus 1) and a fix that only serves the clean path would pass a one-state test. Assert it on BOTH spellings, `check-local-leaks` and the `sanitize` alias, because the alias is the spelling `AGENTS.md` tells agents to use. Follow the local fixture convention rather than inventing one: `tests/test_local_leaks.py` already builds scratch repos and plants leaks, and `tests/test_leak_sanitizer.py` has the tree-state matrix pattern; reuse whichever fits and state in the module docstring which was reused and why stdout/stderr had to be split. RUN IT NOW, BEFORE FIXING, and record the verbatim failure: a test authored after the fix proves nothing about whether it detects the defect.
  - Depends on: E-01
  - Expected outcome: the new test file exists, drives `cli.main` with separated streams, covers two tree states times two command spellings, and FAILS at the unfixed baseline with the verbatim failure message recorded.
  - Execution state: performed

- [x] E-03 EXTEND that file with the `--fields` assertion, which is the second dropped flag and the one the backlog item does not name. Assert that `--agent --fields cmd,outcome` emits a record whose keys are the projection (the envelope keys the renderer preserves, plus `cmd` and `outcome`, and NOT the unrequested domain keys such as `findings` and `evidence`), and that the same invocation WITHOUT `--fields` emits those keys. Scope this to `--agent`: measured at review, `--json --fields cmd,outcome` through the same renderer returns the FULL `CommandResult` unprojected (the `--fields` help text says "field projection for --agent output", and `renderers` applies `_schema.filter_record_fields` only in its agent paths), so a `--json --fields` assertion would be wrong and must not be added. Measured projected key set for this command: `schema, kind, cmd, outcome, exit, verified, complete, next` (the `next` key is preserved per `docs/cli-output-contract.md` "Projections also preserve `next` whenever present"). Assert the presence case and the absence case in the same test so the assertion cannot be satisfied by a projection that drops everything, which is the vacuous-pass failure mode `GUIDING_PRINCIPLES.md` P16 warns about. Read the actual projection semantics from `renderers` and `_schema.filter_record_fields` rather than assuming which envelope keys survive; assert what the function documents, not what seems natural. RUN IT at the unfixed baseline too and record that it fails for the same dropped-flag reason.
  - Depends on: E-02
  - Expected outcome: `--fields` coverage in the same file, asserting projection present-and-absent, failing at the unfixed baseline with its message recorded, and a stated derivation of which envelope keys the projection preserves.
  - Execution state: performed

### Task group 2: Remove the seam rather than patching the list

- [x] E-04 THREAD THE RESOLVED `OutputContext` into the engine, replacing the dropped-flag mechanism instead of appending to the list. `cli.main` already resolves `context = select_output(args)` once and passes it into many handlers by keyword (the established local signature is `def handler(args, term, context: Optional[Any] = None)`, used by `_run_context`, `_run_status`, `_run_find` and others). Give `_run_check_local_leaks` that same third parameter, pass `context` at its dispatch site (the `if args.command in ("check-local-leaks", "sanitize"):` branch of `cli._dispatch`), and give `leak_sanitizer.main` a keyword-only `context=None` parameter so it uses that instead of calling `select_output` on its own re-parsed namespace. KEEP FORWARDING `--agent` in the passthrough list: the inner parser declares it, and the no-context argv path still needs it; the context simply takes precedence when supplied. Do NOT forward `--json` or `--fields` in the list (the inner parser rejects `--json`, F-02). The only behavior the threaded context changes is which `OutputContext` the existing `if ctx.is_agent or ctx.is_json` branch sees; the `--fix` branch and the exit-2 handlers, which return before `select_output` is reached and emit nothing on stdout even under `--agent` today, are a SEPARATE pre-existing defect filed as backlog `k84fqu` and must NOT be changed here. PRESERVE `leak_sanitizer.main`'s EXISTING argv signature and behavior exactly: it is a public surface that `tests/test_leak_sanitizer.py` calls directly as `ls.main(argv)`, and `python3 -m agent_workflows.leak_sanitizer` must keep working, so the new parameter must be OPTIONAL and the argv path must behave identically when it is absent. Do NOT delete the inner parser. Honor the ordinary flag precedence: a resolved context already encodes the `--agent` versus `--json` decision made by `select_output`, so do not re-derive it. State in a comment WHY the context is threaded rather than reserialized, naming this defect, so a later reader does not helpfully "simplify" it back into an argv list.
  - Depends on: E-03
  - Expected outcome: `--json` and `--fields` reach the engine's renderer through the threaded context; the new tests from E-02 and E-03 pass; `leak_sanitizer.main(argv)` with no context behaves exactly as before; and a comment records why the seam was removed.
  - Execution state: performed

- [x] E-05 PROVE THE FIX IS COMPLETE AND THE GUARD IS SENSITIVE, at the surface a human and a script actually use. FIRST, re-run the exact E-01 fact (1) command and show stdout now carries exactly one parseable JSON payload and NO human prose (prose on stdout would be a NEW defect: it would corrupt the payload for the same parsing caller). Expect stderr to be EMPTY: the engine's machine branch (`if ctx.is_agent or ctx.is_json`) returns through `emit` before any of the human `print(..., file=sys.stderr)` calls, exactly as the `--agent` path does today, so the `No local leaks found.` line that appears on stderr at baseline comes from the HUMAN fallthrough and its disappearance is the evidence the machine branch was taken. SECOND, confirm the flag-conflict path is UNCHANGED: `--agent --json` together must still exit 2 with the `conflicting output format flags` message from `select_output`, since threading a context must not route around the conflict check. THIRD, confirm the non-machine path is unchanged: a bare invocation must still print the human prose to stderr and exit 0, and `--fix`, `--dry-run`, `--staged`, `--warn`, `--history` and `--wheel` must still reach the engine (the fix must not drop a flag the old list DID forward, which is the obvious regression shape here). FOURTH, prove sensitivity by MUTATION: temporarily revert the threading so the dropped-flag behavior returns, confirm the new test file FAILS, then restore and confirm the restored bytes equal the post-E-04 bytes (compare a `sha256` of each production file taken before the mutation with one taken after restoration; do NOT use `git status --porcelain`, which is non-empty for these paths until the fix is committed, and is non-empty in a shared checkout for reasons unrelated to this plan). Use a restoring wrapper whose `finally` branch rewrites the original bytes; never hand-edit and remember to undo.
  - Depends on: E-04
  - Expected outcome: pasted end-to-end evidence that `--json` emits a payload on stdout, that `--agent --json` still exits 2, that the human path and every previously-forwarded flag still work, and that the new tests fail under a reverted fix and pass after restoration with matching before/after hashes.
  - Execution state: performed

- [x] E-06 RE-RUN THE DROPPED-FLAG AUDIT the backlog item asks for, record its result in the plan's evidence, and run the full fast suite. Search `cli.py` for every remaining argv-reserialization site (the `passthrough` constructions) and for each one state whether it is live, dead, or deliberately verbatim-forwarding, with the evidence for that classification; authoring measured exactly one other (`_run_plan_names`, dead since the `plan-names` verb was removed) and found the live driver leaves exempt by `docs/cli-output-contract.md` Section 1.3. DO NOT widen this plan to change a driver leaf: if the audit finds a NEW live non-driver instance, FILE IT as a backlog item and name the id in the evidence rather than fixing it here. THEN run the full fast suite BARE as `python3 -m pytest` with no added flags, since `pyproject.toml`'s `addopts` already supplies `-q -n auto --dist=worksteal`; pay particular attention to `tests/test_leak_sanitizer.py`, `tests/test_local_leaks.py`, `tests/test_flag_surface_uniformity.py` and `tests/test_json_surface_leak_posture.py`, which are the four files whose contracts this change touches. If any failure appears, re-run the same selection at the base commit before attributing it to this change, and report the comparison either way.
  - Depends on: E-05
  - Expected outcome: a written audit naming every remaining reserialization site with its live/dead/exempt classification and evidence, a filed backlog id for any new live instance rather than a scope widening, and a bare full-suite `N passed` summary with a pre-existing-versus-caused determination for any failure.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `GUIDING_PRINCIPLES.md` P16 forbids tests that read production source with `inspect`, `ast`, regex, or substring search, and forbids assertions on symbol censuses or caller counts. Every assertion this plan adds invokes `cli.main` and parses real stdout, so none of it is a code-structure pin. P16's mutation-sensitivity bullet is what E-05's fourth step discharges.
- The established handler signature for passing a resolved output context is `def handler(args, term, context: Optional[Any] = None)`, resolved ONCE in `cli.main` as `context = select_output(args)` and passed by keyword at the dispatch site. `_run_context`, `_run_status` and `_run_find` all follow it; this plan extends the same pattern to `_run_check_local_leaks` rather than inventing a mechanism.
- `--agent`, `--json`, `--fields` and `--verbose` are declared ONCE on the shared `common` argparse parent and inherited by every subcommand `aw` itself handles (`docs/cli-output-contract.md` Section 1.3, "By declaration"). That is why the flags appear in this command's `--help` while being silently discarded, and it is what makes the defect invisible to a reader of the help text.
- The forwarded host-driver leaves are DELIBERATELY exempt from carrying `--agent`/`--json`: Section 1.3 states they are "NOT provided on the forwarded leaves, by either route", because on `aw oc run start` a downstream `--agent` is an OpenCode agent NAME. Any audit of dropped flags must not treat those leaves as defects.
- `tests/test_local_leaks.py`'s CLI helper captures stdout and stderr COMBINED ("return (exit code, combined text)"). That is precisely why the existing suite could not catch this defect, and it is why E-02 requires separated streams. A new test that reuses the combined helper would reproduce the blind spot.
- `leak_sanitizer.main` is a public surface with direct callers: `tests/test_leak_sanitizer.py` invokes `ls.main(argv)`, and the module has an `if __name__ == "__main__"` entry. Its argv behavior must be preserved, so any new parameter is additive and optional.
- Assert on the flag's OBSERVABLE EFFECT (a parseable payload on stdout, a projected key set), never by inspecting the passthrough list. A test that asserted "`--json` appears in the forwarded argv" would be a code-structure pin and would also pass for the broken one-line fix that exits 2.

## Findings

| Id | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | The defect reproduces exactly as the item's correction note describes: stdout empty, exit 0, prose on stderr. | `python3 -m agent_workflows check-local-leaks . --json` with streams captured separately: stdout 0 bytes, `exit=0`, stderr `No local leaks found.` at HEAD `afa922f1d`. | The bug is real and the item's corrected symptom is accurate. The work proceeds. |
| F-02 | The item's proposed remedy is WRONG and would make things worse. `leak_sanitizer.main`'s inner parser declares no `--json`. | `leak_sanitizer.main(['.', '--json'])` -> `SystemExit(2)`, `check-local-leaks: error: unrecognized arguments: --json`. The parser's own usage line lists only `[--history] [--max-commits] [--wheel] [--staged] [--warn] [--agent] [--fix] [--yes] [--dry-run] [dir]`. | Appending one forwarding line converts a silent empty payload into a hard exit-2 usage error. This is why the plan threads a context instead, and why E-01 fact (3) must stop the plan if it ever becomes false. |
| F-03 | The engine's machine BRANCH is correct, so the defect is purely the delivery of the flag. | `leak_sanitizer.main` tests `if ctx.is_agent or ctx.is_json` and builds a full `CommandResult` routed through `get_renderer(ctx).emit`; `check-local-leaks . --agent` emits `{"schema":"aw.agent/v1",...,"outcome":"clean","exit":0,...}` on stdout. | No change is needed to the result construction. The fix is confined to how the context reaches it. |
| F-04 | A SECOND flag is dropped the same way, which the item does not mention: `--fields`. | `check-local-leaks . --agent --fields cmd,outcome` emits the FULL record (with `findings`, `evidence`, `next`), while a direct renderer call with `fields=['cmd','outcome']` emits the projected `{"schema","kind","cmd","outcome","exit","verified","complete"}`. `renderers` applies `_schema.filter_record_fields(rec, context.fields)` when `context.fields` is set. | E-03 covers it and V-03 demands its evidence. A fix that only forwards `--json` would leave half the defect in place. |
| F-05 | The audit the item requests finds NO other live instance. The one other `passthrough` site is dead code and the driver leaves are contract-exempt. | `grep -n "passthrough" agent_workflows/cli.py` returns two constructions: `_run_check_local_leaks` and `_run_plan_names`. `grep -rn "_run_plan_names"` finds only its own `def`, with a comment recording that "the old `plan-names` verb was REMOVED" in awcmdsurf Order 05. `docs/cli-output-contract.md` Section 1.3 exempts the driver leaves. | Scope stays at this one command. E-06 re-runs the audit and files rather than fixes any new instance. |
| F-06 | The existing suite structurally cannot catch this class of defect, which explains why a documented flag shipped broken. | `tests/test_local_leaks.py`'s CLI helper returns "(exit code, combined text)", merging the streams, so an empty stdout beside prose on stderr is indistinguishable from a payload. `tests/test_flag_surface_uniformity.py` tests only the color and interactivity pairs plus non-consumption of `--agent`/`--json` on forwarded leaves; it asserts nothing about a machine flag reaching a parsed command's engine. | E-02 must separate the streams, and the new coverage is a genuinely new assertion rather than a duplicate. |
| F-07 | `bug` and the `next` gate are both correct under this repository's test. | The flag is ADVERTISED in the command's own `--help` and `docs/cli-output-contract.md` documents `--json` as "full structured JSON representation"; a caller that trusts it receives an empty string, so `json.loads` raises. That is user-perceptible breakage, not mere inefficiency, so `AGENTS.md`'s every-live-bug-gates-the-next-release policy applies. | Inherit `- Work-Kind: bug` and `- Blocks-Release: next` from the item; invent nothing and relax nothing. |
| F-08 | The flag-conflict path must be preserved by the fix, and it currently works. | `check-local-leaks . --json --agent` exits 2 with `agent-workflows: error: conflicting output format flags: cannot combine --agent and --json`, raised by `select_output` and caught in `cli.main`. | E-05's second step asserts this is unchanged. Threading a pre-resolved context must not bypass the conflict check. |
| F-09 | Re-measured at review HEAD `3c97bba81`: F-01, F-02, F-03, F-04 and F-08 all reproduce, and `--fields` is honored ONLY on the `--agent` path. | `check-local-leaks . --json`: rc 0, stdout 0 bytes, stderr `No local leaks found.`; `ls.main(['.','--json'])` -> `SystemExit 2`, `check-local-leaks: error: unrecognized arguments: --json`; `sanitize . --agent --fields cmd,outcome` -> full record (unprojected); `--agent --json` -> rc 2 `conflicting output format flags`. A `CommandResult` rendered via `get_renderer` with `select_output(Namespace(json=True, fields='cmd,outcome'))` emits the full `to_dict` (keys `schema, command, status, exit_code, summary, verified, complete, diagnostics, changes, evidence, next_actions, data`); with `agent=True, fields='cmd,outcome'` it emits `schema, kind, cmd, outcome, exit, verified, complete, next`. | E-02 asserts `--json` key names (`command`, `exit_code`, `status`), not `--agent` ones; E-03 scopes `--fields` to `--agent`. |
| F-10 | A SEPARATE no-record defect exists on the `--fix` and exit-2 branches, which the threaded context does not reach. | `sanitize . --fix --dry-run --agent`: rc 0, stdout 0 bytes; `sanitize <non-git dir> --agent`: rc 2, stdout 0 bytes, stderr `check-local-leaks: not a git repository or git unavailable`. Both branches return in `leak_sanitizer.main` before `ctx = select_output(args)`. | Out of scope; filed as backlog `k84fqu` (`bug`, `Blocks-Release: next`). E-04 must not change those branches. |

## Proposed changes (ordered, validatable)

1. Re-derive the six load-bearing facts at execution HEAD, with an explicit stop if the inner parser has gained `--json` (E-01).
2. Add `tests/test_leak_sanitizer_machine_flags.py` driving `cli.main` with SEPARATED streams, covering two tree states times two command spellings, and record it failing at the unfixed baseline (E-02).
3. Extend it with `--fields` projection coverage, present-and-absent, also failing at the baseline (E-03).
4. Thread the resolved `OutputContext` from `cli.main` through `_run_check_local_leaks` into `leak_sanitizer.main` as an optional parameter, preserving the argv path exactly (E-04).
5. Prove the fix end-to-end at the CLI surface, prove the conflict path and every previously-forwarded flag are unchanged, and prove the new tests fail under a reverted fix (E-05).
6. Re-run the dropped-flag audit, file rather than fix any new instance, and run the bare full suite (E-06).

## Deferred / out of scope (with reason)

- WHAT THE `--json` PAYLOAD CONTAINS, specifically home-path redaction in `CommandResult.to_dict`. Backlog `7tixnq` and plan `9yd6tx` own that, and the item records that `9yd6tx`'s scope is "what the --json payload CONTAINS ... not which code paths reach a renderer at all". This plan makes the payload ARRIVE; its redaction posture is the sibling's concern, and `tests/test_json_surface_leak_posture.py` already asserts it at the renderer level.
  - Carrier-Evidence: .aw/records/plans/executed/20260930-7tixnq-01-9yd6tx-give-the-json-surface-one-declared-leak-posture-and-sanitize.ipd.md
- ANY CHANGE TO THE LIVE FORWARDED DRIVER LEAVES (`aw oc run`, `aw agy run`, the `review`/`integrate` aliases, `aw run as`, `aw run ipd`, `aw agy sessions|view|exec`). `docs/cli-output-contract.md` Section 1.3 states `--agent` and `--json` are deliberately NOT provided there, because a downstream `--agent` on `aw oc run start` is an OpenCode agent NAME. Changing them would break a documented contract rather than fix a defect.
  - Carrier-Declined: NOTHING IS OWED, because this is not deferred work at all: it is a documented design decision that already holds. Section 1.3 states the exemption affirmatively ("`--agent` and `--json` are NOT provided on the forwarded leaves, by either route") and gives the reason, and `tests/test_flag_surface_uniformity.py` already pins that those leaves consume the color and interactivity pairs while leaving `--agent`/`--json` alone. Filing a carrier would record a satisfied contract as an outstanding obligation, which is the inverse of the truth. F-05 records the audit result so a future reader is not left guessing why the drivers were skipped.
- REMOVING THE DEAD `_run_plan_names` FUNCTION. It is the only other reserialization site and it is unreachable (the `plan-names` verb was removed in awcmdsurf Order 05), so it cannot drop a flag for any caller. Deleting dead code is a legitimate `chore` but it is not this bug, and bundling it would put an unrelated deletion inside a release-gated bug fix.
  - Carrier: mz9id3
- A GENERALIZED `aw check` RULE detecting that a `common`-parent flag is unreachable on some subcommand. That is the defect CLASS behind this instance and it is worth having, but it needs its own design (it must encode the Section 1.3 driver-leaf exemption or it will fire on every exempt leaf). File it separately; do not improvise it inside a release blocker.
  - Carrier: uxq5mg
- THE `--fix` BRANCH AND THE EXIT-2 ERROR HANDLERS OF `leak_sanitizer.main` EMIT NOTHING ON STDOUT EVEN UNDER `--agent`. Measured at review (HEAD `3c97bba81`): `sanitize . --fix --dry-run --agent` exits 0 with 0 stdout bytes and `No auto-fixable local leaks found.` on stderr; `sanitize <non-git dir> --agent` exits 2 with 0 stdout bytes and `check-local-leaks: not a git repository or git unavailable` on stderr. Both return before `select_output` is consulted, so this is a different mechanism from the dropped flag and the threaded context alone does not fix it. Routing them through the renderer is a Section 11.3/11.4 shape change for three branches, which would widen a focused release-blocker.
  - Carrier: k84fqu
- THE LEAK RULESET, SCAN MODES, AND CONFIG RESOLUTION. Untouched. This plan changes only how an output context reaches the renderer; `run`, `scan_text`, `fix_working_tree` and the config loaders are read-only here.
  - Carrier-Declined: No obligation is created, because nothing is deferred: these surfaces are simply not in scope and no defect in them was measured during authoring. This row exists to tell a reviewer that the engine's detection logic was read and left alone, which is a statement about what this plan does NOT touch rather than about work owed to anyone. Reserving a carrier for untouched healthy code would be designing for a hypothetical need (GUIDING_PRINCIPLES P6).

## Scope check

- Over-scope: none. All three `Scope-Paths` entries are required: `agent_workflows/cli.py` holds the dropping passthrough list and the dispatch site, `agent_workflows/leak_sanitizer.py` holds `main` which must accept the threaded context, and `tests/test_leak_sanitizer_machine_flags.py` is the new guard. No spec file is named because no spec is amended (see Spec / documentation sync).
- Under-scope: The defect CLASS stays open. After this plan, a future `common`-parent flag added to the shared parent can still be silently unreachable on some other command, because nothing checks that mechanically; the deferred `aw check` rule would close it and is filed rather than fixed here. `_run_plan_names` also keeps its stale list, harmlessly, since nothing dispatches to it. Finally, this plan asserts the payload PARSES and projects; it does not assert the payload's redaction posture, which `9yd6tx` owns.

## Required tests / validation

- The new `tests/test_leak_sanitizer_machine_flags.py`, run bare and passing after the fix, asserting a parseable stdout payload for `--json` across two tree states and both command spellings (E-02) and `--fields` projection present-and-absent (E-03).
- Recorded baseline runs of that file FAILING before the production edit, with verbatim messages, so the guard is known to detect the defect rather than merely to pass (E-02, E-03).
- A mutation run proving the file fails again under a reverted fix, with `git status --porcelain` clean for both production paths afterwards (E-05).
- End-to-end CLI evidence that `--json` now emits a payload on stdout and the human-path prose no longer appears, that `--agent --json` still exits 2 with the conflict message, that the bare human path is unchanged, and that `--fix`, `--dry-run`, `--staged`, `--warn`, `--history` and `--wheel` still reach the engine (E-05).
- Evidence that `leak_sanitizer.main(argv)` called with no context behaves exactly as before, since it is a public surface with direct test callers (E-04).
- A bare `python3 -m pytest` full fast-suite run with its `N passed` summary pasted, plus a pre-existing-versus-caused determination for any failure (E-06).

## Spec / documentation sync

N/A with reason, on the SPEC axis: no `.spec.md` is amended and none is named in `Scope-Paths`. This plan makes a DOCUMENTED contract true rather than changing it. `docs/cli-output-contract.md` already specifies that `--json` yields a "full structured JSON representation" and that it is declared on the shared `common` parent for every subcommand `aw` handles; the code did not honor that, and this plan fixes the code to match the document. Section 1.3's exemption for the forwarded driver leaves is likewise already correct and is relied upon by F-05 rather than modified. If E-06's audit finds the document's Section 1.3 claim no longer matches the code, the executor must REPORT that divergence rather than silently editing either side, since a contract edit changes what every other plan is reviewed against.

`CHANGELOG.md` is deliberately not in `Scope-Paths`. This is a release-gated user-visible bug fix, so it merits a changelog line, but authoring leaves that to the release process rather than asserting a version heading this plan cannot know; the executor should raise it if the repository's convention requires the line in the fixing commit.

## Open questions

### OQ-01: Should `leak_sanitizer.main` accept an `OutputContext` parameter, or should the CLI call a non-argv engine entry point directly?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE toward an OPTIONAL context parameter on the existing `main`, for two reasons. FIRST, `main` is a public surface with live direct callers: `tests/test_leak_sanitizer.py` invokes `ls.main(argv)` and the module carries an `if __name__ == "__main__"` entry, so introducing a parallel entry point and leaving `main` behind would create two code paths where the argv one keeps the defect. An optional parameter keeps ONE path. SECOND, the repository already has exactly this pattern for exactly this purpose: `cli.main` resolves `context = select_output(args)` once and passes it into handlers as `context: Optional[Any] = None`, which `_run_context`, `_run_status` and `_run_find` all accept. Following the local pattern is cheaper to review than inventing a seam. E-04 requires the argv path to behave identically when no context is supplied, which is what makes this non-blocking either way.

### OQ-02: Should `--verbose` be covered by the new tests alongside `--json` and `--fields`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED toward NOT adding a dedicated `--verbose` assertion, while still fixing it. `--verbose` is declared on the same `common` parent and is therefore dropped by the same mechanism, so the E-04 fix delivers it for free; the reason it gets no test is that authoring did not MEASURE a user-visible difference for this command's result shape (its `CommandResult` carries no nested diagnostic detail on a clean tree), and asserting a difference that may not exist would either fail for an unrelated reason or be weakened into a vacuous pass. The executor MAY add the assertion if E-01 fact (5)'s renderer inspection shows `--verbose` changes this command's payload; if so, record it as an additional observation under V-03 rather than silently expanding the test's claims. This is non-blocking because the fix is identical either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: The execution HEAD sha, plus pasted command output for each of the six facts. Fact (1) must show stdout and stderr captured to SEPARATE sinks, with the stdout byte count and the exit code stated explicitly. Fact (3) must show the verbatim `SystemExit` / `unrecognized arguments: --json` text. Fact (5) must show the projected versus unprojected key sets side by side. Each fact must be explicitly marked CONFIRMED or CORRECTED, and if fact (3) no longer holds the evidence must show the plan STOPPED and reported.
  - Observed evidence:
    Execution HEAD sha: `3ed1764ecb1f9a9b01f5b4f1119b5777e1c01d34`
    Fact (1): `python3 -m agent_workflows check-local-leaks . --json`
      Separate sinks: stdout byte count = 0, stderr byte count = 22, exit code = 0.
      stdout: `''`
      stderr: `'No local leaks found.\n'`
      [CONFIRMED]
    Fact (2): `python3 -m agent_workflows check-local-leaks . --agent`
      exit = 0, schema = aw.agent/v1, outcome = clean.
      [CONFIRMED]
    Fact (3): `leak_sanitizer.main(['.', '--json'])`
      Raised SystemExit(2) with:
      `usage: check-local-leaks [-h] [--history] [--max-commits MAX_COMMITS] [--wheel WHEEL] [--staged] [--warn] [--agent] [--fix] [--yes] [--dry-run] [dir]`
      `check-local-leaks: error: unrecognized arguments: --json`
      [CONFIRMED - inner parser has not gained --json; plan proceeds]
    Fact (4): `cli._run_check_local_leaks` passthrough inspection
      passthrough has --json: False, has --fields: False.
      [CONFIRMED]
    Fact (5): Renderer direct call with `fields=['cmd','outcome']` vs plain:
      Projected keys: `['cmd', 'complete', 'exit', 'kind', 'next', 'outcome', 'schema', 'verified']`
      Plain keys: `['cmd', 'complete', 'exit', 'findings', 'kind', 'next', 'outcome', 'schema', 'verified']`
      [CONFIRMED]
    Fact (6): `_run_plan_names` has 1 occurrence in `cli.py` (definition only, no callers or dispatch site). Live forwarded driver leaves (`aw oc run`, `aw agy run`, `aw run as`, `aw run ipd`, `review`, `integrate`) forward argv verbatim prior to `parse_args`.
      [CONFIRMED]
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: The new file's path and module docstring, showing which existing fixture was reused and the stated reason stdout and stderr are captured separately. Pasted output of the file FAILING at the unfixed baseline, with the verbatim failure message, taken BEFORE any production edit (the evidence must make the ordering visible, for example by including the `git status --porcelain` of the production paths showing them unmodified at that moment). Pasted output of it PASSING after E-04. The evidence must show all four cases present: clean and planted-leak tree states, each under both `check-local-leaks` and `sanitize`.
  - Observed evidence:
    New test file: `tests/test_leak_sanitizer_machine_flags.py`
    Module docstring:
    ```python
    """Tests for leak-sanitizer machine-readable CLI flags (--json and --fields).

    Reuses the scratch git repository fixture (_init_repo and _commit) and runtime
    leak token synthesis pattern from tests/test_local_leaks.py.

    Stdout and stderr are captured into separate streams rather than combined via
    tests/test_local_leaks.py's _run helper. The combined helper masked the defect:
    `check-local-leaks --json` wrote 0 bytes to stdout while printing human prose to
    stderr, which merged into non-empty output and hid that the machine payload was
    completely missing on stdout. By capturing stdout and stderr separately, these
    tests verify that stdout carries the parseable JSON payload and stderr carries
    no payload.

    CLI invocations drive cli.main in-process using contextlib.redirect_stdout and
    contextlib.redirect_stderr with scratch repo paths passed as positional `dir`
    arguments, preserving process working directory across parallel pytest-xdist
    workers. XDG_CONFIG_HOME is pinned to the temporary test directory to isolate
    against ambient user configuration.
    """
    ```
    Production paths status before edit:
    `git status --porcelain`:
    ```
    ?? tests/test_leak_sanitizer_machine_flags.py
    ```
    Baseline run failing output before any production edit:
    ```
    FAILED tests/test_leak_sanitizer_machine_flags.py::LeakSanitizerMachineFlagsTests::test_json_flag_emits_parseable_payload_across_spellings_and_states
    E   AssertionError: '' is not true : Expected non-empty JSON stdout for clean tree with check-local-leaks, but stdout was empty. stderr='No local leaks found.\n'
    ```
    Post-E-04 passing run:
    ```
    tests/test_leak_sanitizer_machine_flags.py .. [100%]
    2 passed in 14.23s
    ```
    All 4 cases present and passing: clean and planted-leak states under both `check-local-leaks` and `sanitize`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted passing output of the `--fields` test, plus the two key sets it asserts: the projected record under `--agent --fields cmd,outcome` and the fuller record without `--fields`. The absence case must be visibly present, since it is what rules out a vacuous pass. Evidence must also state WHICH envelope keys the projection preserves and cite where that was read from (`renderers` / `_schema.filter_record_fields`) rather than asserting a guessed set. Plus the baseline failure message for this test. If OQ-02's optional `--verbose` observation was taken, record it here.
  - Observed evidence:
    Baseline failure output before fix:
    ```
    FAILED tests/test_leak_sanitizer_machine_flags.py::LeakSanitizerMachineFlagsTests::test_fields_projection_scopes_to_agent_output
    E   AssertionError: Items in the first set but not the second:
    E   'evidence'
    E   'findings' : Projected keys mismatch for check-local-leaks under --agent --fields cmd,outcome
    ```
    Passing output after fix:
    ```
    tests/test_leak_sanitizer_machine_flags.py::LeakSanitizerMachineFlagsTests::test_fields_projection_scopes_to_agent_output PASSED
    ```
    Projected record key set asserted (`--agent --fields cmd,outcome`):
    `{'schema', 'kind', 'cmd', 'outcome', 'exit', 'verified', 'complete', 'next'}`
    Unprojected record key set asserted (`--agent` without `--fields`):
    `{'schema', 'kind', 'cmd', 'outcome', 'exit', 'verified', 'complete', 'findings', 'evidence', 'next'}`
    Envelope preservation derivation: read from `agent_schema.filter_record_fields`, which preserves `_PRESERVED_FIELDS` (`_MANDATORY_FIELDS` `{"schema", "kind", "cmd", "exit", "outcome", "complete", "verified"}` + `{"next"}`). Fields `'findings'` and `'evidence'` are omitted from projection and verified present when `--fields` is omitted.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: The diff of both production paths, showing the `context` parameter added to `_run_check_local_leaks` with the keyword passed at its dispatch site, the optional context parameter on `leak_sanitizer.main`, and the comment recording why the seam was removed. Evidence that the argv path is UNCHANGED when no context is supplied: a pasted run of `python3 -m agent_workflows.leak_sanitizer .` (or the module's own entry) plus a pasted run of the existing `tests/test_leak_sanitizer.py` showing its direct `ls.main(argv)` callers still pass. Evidence must show the inner parser was NOT deleted.
  - Observed evidence:
    `git diff agent_workflows/cli.py agent_workflows/leak_sanitizer.py`:
    ```diff
    diff --git a/agent_workflows/cli.py b/agent_workflows/cli.py
    index 1cfd6b081..988163cb5 100644
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -10569,7 +10569,9 @@ def _run_leaks_configure(args: argparse.Namespace, term: Term) -> int:
         return 0


    -def _run_check_local_leaks(args: argparse.Namespace, term: Term) -> int:
    +def _run_check_local_leaks(
    +    args: argparse.Namespace, term: Term, context: Optional[Any] = None
    +) -> int:
         """Detect local leaks (D92/D93). Delegates to the unified agent_workflows.leak_sanitizer
         engine (local_leaks re-exports it). With --configure, launches the config wizard instead."""
         if getattr(args, "configure", False):
    @@ -10577,6 +10579,10 @@ def _run_check_local_leaks(args: argparse.Namespace, term: Term) -> int:

         from . import leak_sanitizer

    +    # Context is threaded directly into leak_sanitizer.main rather than reserialized into argv
    +    # (IPD wyy09f). Reserializing via a hand-maintained list dropped --json and --fields, and
    +    # adding them to the list would crash against leak_sanitizer's inner parser which does not
    +    # declare --json. The resolved OutputContext takes precedence while preserving argv fallback.
         passthrough = [getattr(args, "dir", None) or "."]
         if getattr(args, "history", False):
             passthrough.append("--history")
    @@ -10596,7 +10602,8 @@ def _run_check_local_leaks(args: argparse.Namespace, term: Term) -> int:
             passthrough.append("--yes")
         if getattr(args, "dry_run", False):
             passthrough.append("--dry-run")
    -    return leak_sanitizer.main(passthrough)
    +    return leak_sanitizer.main(passthrough, context=context)
    +


     def _run_context(
    @@ -16368,7 +16375,7 @@ def _dispatch(argv: Optional[Sequence[str]]) -> int:
         if args.command == "archive":
             return _run_archive(args, term)
         if args.command in ("check-local-leaks", "sanitize"):
    -        return _run_check_local_leaks(args, term)
    +        return _run_check_local_leaks(args, term, context=context)

         if args.command == "ipd-executed-gate":
             from agent_workflows.hooks import executed_transition_gate as _gate
    diff --git a/agent_workflows/leak_sanitizer.py b/agent_workflows/leak_sanitizer.py
    index 319054327..e9814f576 100644
    --- a/agent_workflows/leak_sanitizer.py
    +++ b/agent_workflows/leak_sanitizer.py
    @@ -44,6 +44,7 @@ import sys
     import zipfile
     from dataclasses import dataclass, field
     from pathlib import Path
    +from typing import Any, Optional

     from agent_workflows import agent_schema
     from agent_workflows.artifact_core import replacement_mode
    @@ -966,7 +967,11 @@ def run(
         return fails, warns


    -def main(argv: list[str] | None = None) -> int:
    +def main(
    +    argv: list[str] | None = None,
    +    *,
    +    context: Optional[Any] = None,
    +) -> int:
         import argparse

         argv = list(sys.argv[1:] if argv is None else argv)
    @@ -1076,7 +1081,10 @@ def main(argv: list[str] | None = None) -> int:
             select_output,
         )

    -    ctx = select_output(args)
    +    # Threaded OutputContext (IPD wyy09f) avoids dropping machine flags (--json, --fields)
    +    # between CLI dispatch and the engine. If context was not provided (e.g. direct argv
    # invocation), resolve it from parsed args as before.
    +    ctx = context or select_output(args)
         if ctx.is_agent or ctx.is_json:
             findings = (*fails, *warns)
             exit_code = 1 if fails else 0
    ```
    Inner parser preserved: `parser = argparse.ArgumentParser(...)` retained.
    Argv-only path unchanged:
    `python3 -m agent_workflows.leak_sanitizer .` output:
    `No local leaks found.` (exit 0).
    Existing `tests/test_leak_sanitizer.py` direct `ls.main(argv)` callers:
    `16 passed in 17.94s`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Four pasted blocks. (1) The re-run of E-01 fact (1) showing `json.loads` of the whole stdout succeeding, the stdout and stderr byte counts, and stderr NOT carrying the baseline `No local leaks found.` line (prose on stdout, or the human-path line still on stderr, is a FAIL: either means the machine branch was not taken). (2) `--agent --json` still exiting 2 with the verbatim `conflicting output format flags` message. (3) A bare invocation still printing human prose to stderr with exit 0, and evidence that `--fix`, `--dry-run`, `--staged`, `--warn`, `--history` and `--wheel` each still reach the engine. (4) The new test file FAILING under a reverted fix, then PASSING after restoration, with `sha256sum agent_workflows/cli.py agent_workflows/leak_sanitizer.py` taken before the mutation and after restoration showing identical hashes, and evidence that the restoring wrapper's `finally` branch ran rather than a hand-undo.
  - Observed evidence:
    Block (1): E-01 fact (1) re-run:
    ```
    Part 1: exit=0, stdout_len=457, stderr_len=0
    Part 1 stderr: ''
    Part 1 json.loads SUCCESS: command=check-local-leaks, status=clean, exit_code=0
    ```
    Block (2): Flag conflict:
    ```
    Part 2: exit=2
    Part 2 stdout: ''
    Part 2 stderr: 'agent-workflows: error: conflicting output format flags: cannot combine --agent and --json\nNext  aw --help\n'
    ```
    Block (3): Non-machine and forwarded flags:
    ```
    3a bare: exit=0, stdout='', stderr='No local leaks found.\n'
    3b fix+dry-run: exit=0, stderr='No auto-fixable local leaks found.\n'
    3c staged: exit=0, stderr='No local leaks found.\n'
    3d warn: exit=0, stderr='  [warn] tests/test_release_readiness.py:132: derived:Gabriele Fariello: ...\nNo local leaks found.\n'
    3e history: exit=0, stderr='No local leaks found.\n'
    3f wheel: exit=0, stderr='No local leaks found.\n'
    ```
    Block (4): Mutation sensitivity and restoration:
    ```
    BEFORE MUTATION sha256(cli.py): cb7c69772016e843ec77f3562d311ec6cba62eb73fde1e0210411340f62d6d59
    BEFORE MUTATION sha256(leak_sanitizer.py): c42b595aa67aa00aec01cef4baf054419890477c3591dd0417198ec81e82824b
    Running pytest under mutation...
    Mutation run exit code: 1
    MUTATION CONFIRMED: tests failed as expected when threading is reverted.
    FINALLY BLOCK: original file bytes restored.
    AFTER RESTORATION sha256(cli.py): cb7c69772016e843ec77f3562d311ec6cba62eb73fde1e0210411340f62d6d59
    AFTER RESTORATION sha256(leak_sanitizer.py): c42b595aa67aa00aec01cef4baf054419890477c3591dd0417198ec81e82824b
    SHA256 MATCH CONFIRMED for both production files.
    Re-running pytest on restored tree...
    Restored run exit code: 0
    ALL MUTATION AND RESTORATION CHECKS PASSED.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: The written audit, listing every remaining `passthrough` reserialization site in `cli.py` with its live/dead/exempt classification and the command output supporting each classification (including the dispatch-site search that proves `_run_plan_names` unreachable, and the citation of `docs/cli-output-contract.md` Section 1.3 for the driver leaves). If a NEW live non-driver instance was found, the filed backlog item's id6 must appear here and the evidence must show it was NOT fixed in this plan. Plus the bare `python3 -m pytest` summary line with its `N passed` count, explicit confirmation that `tests/test_leak_sanitizer.py`, `tests/test_local_leaks.py`, `tests/test_flag_surface_uniformity.py` and `tests/test_json_surface_leak_posture.py` all pass, and for any failure a comparison run at the base commit attributing it as pre-existing or caused.
  - Observed evidence:
    Written audit of `passthrough` in `cli.py`:
    - `_run_plan_names` (lines 10515-10534): DEAD CODE. `_run_plan_names` has no dispatch site in `_dispatch` (only 1 occurrence in `cli.py` at its own definition; `plan-names` verb removed in awcmdsurf Order 05). Tracked by backlog `mz9id3`.
    - `_run_check_local_leaks` (lines 10586-10605): LIVE, FIXED in this plan (wyy09f) by threading `context` into `leak_sanitizer.main(passthrough, context=context)`.
    - Forwarded driver leaves (`aw oc run`, `aw agy run`, `aw run as`, `aw run ipd`, `review`, `integrate`): EXEMPT verbatim forwarding. `docs/cli-output-contract.md` Section 1.3: "--agent and --json are NOT provided on the forwarded leaves, by either route" because downstream `--agent` on `aw oc run start` is an OpenCode agent name.
    - No new live non-driver instances found; zero new backlog items needed.
    Bare full fast suite runner output:
    ```
    6588 passed, 2 skipped, 3 warnings in 380.59s (0:06:20)
    ```
    Targeted contract suites all confirmed passing:
    - `tests/test_leak_sanitizer.py`: 16 passed
    - `tests/test_local_leaks.py`: passed
    - `tests/test_flag_surface_uniformity.py`: passed
    - `tests/test_json_surface_leak_posture.py`: passed
    - `tests/test_leak_sanitizer_machine_flags.py`: 2 passed
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. All open questions (OQ-01, OQ-02) are resolved.

The executing agent must: commit ONLY the three declared `Scope-Paths` entries, through `aw commit <plan> -- <paths>`, never `git add -A` and never `--no-verify`; paste ACTUAL runner output for every suite claim rather than asserting success; and run the suite BARE as `python3 -m pytest`, since `pyproject.toml`'s `addopts` already supplies `-q -n auto --dist=worksteal` and added flags such as `-n0` or a second `-q` would slow the run or suppress the summary line V-06 requires.

TWO EXECUTION-SPECIFIC HAZARDS, stated because each has a tempting wrong shortcut.

FIRST, DO NOT TAKE THE BACKLOG ITEM'S SUGGESTED ONE-LINE FIX. The item says "the likely fix is one forwarding line"; F-02 measured that `leak_sanitizer.main(['.', '--json'])` raises `SystemExit(2)` with `unrecognized arguments: --json`, so that line alone converts a silent empty payload into a hard usage error for the very scripted caller this plan protects. If the inner parser has gained `--json` by execution time, E-01 fact (3) catches it and the plan STOPS for re-scoping rather than quietly shrinking.

SECOND, THE REGRESSION SHAPE HERE IS A DROPPED FLAG, NOT A BROKEN PAYLOAD. The old passthrough list did correctly forward nine flags. A rewrite that threads the context but stops forwarding `--staged` would break the pre-commit hook (`.pre-commit-config.yaml` invokes `python3 -m agent_workflows check-local-leaks`) and a rewrite that stops forwarding `--history` would break the release-time history scan. E-05's third step and V-05's third block exist to prove each previously-working flag still works; do not treat them as ceremony.

After every `E-*` is `performed` and every `V-*` is `pass` with concrete pasted evidence, run `aw ipd lint --phase pre-transition`. Under `aw oc run`/`aw agy run` the runner owns begin/finalize and the move to `.aw/records/plans/executed/`; when executing by hand, complete the terminal transition with `aw ipd finalize`. Do not hand-edit the terminal state or the plan's directory. `- Scope-Paths:` is a declaration the finalize scope gate reconciles: a genuinely needed out-of-scope edit is made and justified with `--scope-reason`, never silently.
