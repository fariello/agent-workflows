# IPD: Give the --json surface one declared leak posture and sanitize the fields that carry a home path

- Date: 2026-09-30
- Kind: child
- Concern: The `--json` machine surface has no declared leak posture: it sanitizes two fields, leaks nine, and no document says which it promises; the same unredacted string also crashes `--agent` on a shipped command.
- Scope: Declare `--json`'s leak posture in the output contract, add ONE home-path redaction primitive to `agent_schema` shared by both machine surfaces, apply it to the `CommandResult.to_dict` free-text fields that measurably leak AND to the one `to_agent_record` site that reads a `next_action` directly (which is what makes `aw check plans --agent` crash today), and pin the whole matrix with behavioral tests. Does NOT touch `data`, does NOT make `--json` validate against `aw.agent/v1`, and does NOT touch `AgentRenderer` or `HumanRenderer`.
- Scope-Paths: agent_workflows/agent_schema.py, agent_workflows/result_types.py, docs/cli-output-contract.md, docs/cli-agent-protocol.md, tests/test_json_surface_leak_posture.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: 7tixnq
- Set: 7tixnq
- Order: 1
- Highest E allocated: 08
- Author: opencode
- Id: 9yd6tx

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 9yd6tx verified (set 7tixnq, attempt 2).
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED via /plan-review; PR-001 through PR-006 all FIXED, no finding left open or deferred. Reviewed in an isolated review lane at HEAD `aa905891d`; `aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE any edit and `--phase review-finalize` reports `conforming` after revision; the plan file was committed and unchanged, so no pre-review snapshot was taken. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator row check does not apply. THE DIAGNOSIS IS THE PLAN'S REAL CONTRIBUTION AND IT HOLDS: F-02's reframing from "add sanitization" to "finish the sanitization `--json` already started" reproduces exactly (two channels clean via `normalize_repo_path`, nine leaking), F-06's two independent reasons `normalize_repo_path` cannot be reused both reproduce (it returns `'aw foo /home/<user>/secret/x.md'` unchanged for an embedded path, and silently falsifies `'/home/<user>/code/other/.aw/records/a.md'` to `'.aw/records/a.md'`), F-08's Windows gap in `_rewrite_line` reproduces, and F-05's `data` exemption is real (`aw context --json` emits 16 absolute paths under `data`). PR-001 IS THE FINDING THAT CHANGED THE PLAN'S SCOPE: `to_agent_record` assigns `rec["next"] = self.next_actions[0].command` off the dataclass and NEVER calls `NextAction.to_dict`, so E-04 could not have reached the `next` channel, and that unredacted string makes `aw check plans --agent` CRASH today (exit 1, zero stdout bytes, 26-line stderr ending in `ValueError: ... Unsanitized absolute home path in field 'next'`), which also falsified F-10's claim that no live CLI crash exists. Added E-07 and corrected F-09, F-10, the Goal, Proposed changes and the Scope check. PR-002: E-02 promised a test that fails when a fourth home class is added to `_HOME_PATH_RE`, which its own fixed-table mechanism cannot deliver (demonstrated: a three-class primitive passes the table unchanged against a four-class detector), so V-02's falsifiability demo was unproducible; E-02 now asserts a per-class bijection and states the unenumerated-class bound. PR-003: `Evidence.value` is typed `Any` and three shipped `cli.py` callers pass dicts, so E-03's "string values only" left dict- and list-valued leaks open while the matrix would have declared the channel clean; added E-08. PR-004: the F-03 hit counts are live-artifact figures that already drifted in one day (22 and 3 at authoring against 16 and 1 envelope hits at review), so Required tests and V-04 now demand re-derivation and hold the executor to the property. PR-005: the planted fixtures had to be fragment-assembled or the repository's own `local-leaks` pre-commit hook would reject the commit (measured: an untracked literal is invisible to `aw sanitize`, and reports `home-path` the moment it is staged). PR-006: F-04's claim that two specs "already forbid" an absolute home path on `--json` overstated both citations; F8a's prohibition is LANE-scoped and only its rationale generalizes, and `uonrjg` A14 is about ANSI and not paths, so OQ-01 now records a decision resting on rationale rather than citing a binding rule. Both open questions remain non-blocking and resolved. Full findings and three decisions in `.aw/records/reviews/20260930-7tixnq-01-9yd6tx-give-the-json-surface-one-declared-leak-posture.review.md`.
- 2026-09-30 to-review (opencode): authored from backlog `7tixnq`. Measured the leak matrix on both machine surfaces, resolved the posture question the carrier raised from in-repo spec and docs evidence (see OQ-01), and settled scope on the three fields that leak through a free-text channel.
- 2026-09-30 draft (opencode): created.

## Goal

Make `--json` carry ONE stated leak posture instead of an accidental one. Today `CommandResult.to_dict` normalizes `diagnostics[].location` and `changes[].path` but passes `diagnostics[].fix`, `diagnostics[].detail`, `changes[].detail`, `evidence[].value`, `evidence[].detail`, `next_actions[].command`, and `summary` through verbatim, so the surface is neither "sanitized" nor "raw" and no document says which it promises. This plan redacts the home-path prefix out of the free-text fields that measurably leak, leaves `data` deliberately raw under a stated exemption, and writes the resulting posture into the output contract so the next reader does not have to re-measure it.

ONE SIDE EFFECT IS LARGER THAN A LEAK POSTURE AND IS NAMED HERE BECAUSE A READER SHOULD NOT HAVE TO FIND IT IN THE FINDINGS. The same unredacted string that leaks through `--json` also CRASHES `--agent`: `to_agent_record` copies `next_actions[0].command` straight onto `rec["next"]`, the validator refuses a home path there, and `aw check plans --agent` therefore exits 1 today having written zero stdout bytes and a `ValueError` traceback (F-16, F-17). Applying the same primitive at that one assignment (E-07) turns a crash into a conforming record. That is a user-visible defect fix, not a posture change, and it is why the plan touches `to_agent_record` as well as `to_dict`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared redaction primitive

- [x] E-01 Add a `redact_home_paths(text)` function to `agent_workflows/agent_schema.py` that rewrites every home-style absolute path prefix inside a string to `~`, preserving the tail, and returns non-string input unchanged. Cover all three classes `_HOME_PATH_RE` detects (POSIX `/home/<user>`, macOS `/Users/<user>`, and the Windows `<drive>:\Users\<user>` form), using prefix patterns WITHOUT the placeholder negative lookaheads so a already-placeholder value is left alone by virtue of not matching a real username. Place it beside `normalize_repo_path` and state in the docstring that it REDACTS (a lossy, idempotent rewrite) rather than relativizing, and that it is the counterpart `normalize_repo_path` cannot serve because it operates on a whole path value and not on a path embedded in free text.
  - Depends on: none
  - Expected outcome: `agent_schema.redact_home_paths('aw foo /home/<user>/x.md')` returns `'aw foo ~/x.md'`; `redact_home_paths('C:\\Users\\<user>\\x')` returns `'C:\\Users\\~\\x'` or another form carrying no username, and in every case `_HOME_PATH_RE.search(result)` is `None`; non-string input is returned unchanged.
  - Execution state: performed

- [x] E-02 Pin the new primitive's agreement with the existing detector by asserting, for a table of inputs covering all three home classes plus the already-redacted and the no-path cases, that `_HOME_PATH_RE.search(redact_home_paths(s))` is always `None` and that `redact_home_paths` is idempotent. Put these in the new test module from E-06. This is the property that makes the primitive trustworthy for the cases it covers: it is defined as "whatever makes the repository's own home-path detector stop matching".
  STATE THE LIMIT HONESTLY RATHER THAN OVERCLAIMING, because the first wording of this item claimed a drift guarantee the mechanism cannot deliver (F-18, PR-002). A FIXED TABLE cannot fail when a FOURTH class is added to `_HOME_PATH_RE`, because no table row carries the fourth class; measured at review, a plausible three-class `redact_home_paths` passes the table unchanged against a detector extended with a fourth alternation, while a string of that fourth class is returned untouched and still matches. So assert the table property AND, separately, assert that the primitive's own alternation count agrees with the detector's by driving BOTH over a per-class table keyed on the SAME class list, so adding a class to one without the other breaks a row rather than silently passing. Do NOT read `_HOME_PATH_RE.pattern` with a regex or count alternations by string inspection; that is a code-pinning test (`AGENTS.md`, GUIDING_PRINCIPLES P16).
  - Depends on: E-01
  - Expected outcome: for each of the three home classes, one test row asserts `_HOME_PATH_RE` MATCHES the planted input and `_HOME_PATH_RE.search(redact_home_paths(input))` is `None`, so a class the detector gains but the primitive does not handle fails its row; plus the idempotence and already-redacted rows. The test module states in a comment that an UNENUMERATED fourth class is not caught by any test and is a known bound.
  - Execution state: performed

### Task group 2: apply it to the fields that leak

- [x] E-03 In `agent_workflows/result_types.py`, apply `redact_home_paths` to the free-text fields that measurably leak through `to_dict`: `Diagnostic.to_dict`'s `detail` and `fix`, `Change.to_dict`'s `detail`, and `Evidence.to_dict`'s `value` and `detail`. Leave each field's `location`/`path` handling exactly as it is, since `normalize_repo_path` already covers those and changing them is out of scope. E-08 settles how a NON-STRING `Evidence.value` is handled; this item carries the string case and must not narrow the field to `str` in a way E-08 then has to undo.
  - Depends on: E-01
  - Expected outcome: the five-row leak matrix measured in F-02 reports `clean` for `diagnostics.detail`, `diagnostics.fix`, `changes.detail`, `evidence.value` (string case), and `evidence.detail`.
  - Execution state: performed

- [x] E-04 Apply `redact_home_paths` to `NextAction.to_dict`'s `command` and `description`, and to `CommandResult.to_dict`'s `summary`. These are the two remaining leaking channels and they are the ones the carrier's own measurement names: `next_actions[].command` is the field the backlog item measured, and `summary` leaks because it is operator-authored prose that commands interpolate paths into.
  - Depends on: E-01
  - Expected outcome: the leak matrix reports `clean` for `next_actions.command` and `summary`; `aw check --json` emits no `/home/<user>` in any `diagnostics[].fix`.
  - Execution state: performed

- [x] E-07 Apply `redact_home_paths` to the `rec["next"]` assignment inside `CommandResult.to_agent_record`, which reads `self.next_actions[0].command` DIRECTLY off the dataclass and so is NOT reached by E-04's `NextAction.to_dict` change (F-16). This is not a convenience addition: the unredacted `next` is what makes `aw check plans --agent` CRASH today with `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next'`, zero stdout bytes and a Python traceback (F-17), so without this item the plan touches `to_dict` only and leaves the live machine-surface crash its own F-01 measured. Change the one assignment; do not alter the surrounding outcome or `findings` logic.
  - Depends on: E-01
  - Expected outcome: `aw check plans --agent` exits 1 with a single parseable `aw.agent/v1` record on stdout and NO traceback on stderr, where today it exits 1 with zero stdout bytes and a `ValueError` traceback; `redact_home_paths` is applied at the `rec["next"]` site and `validate_agent_record` accepts the record.
  - Execution state: performed

- [x] E-08 Make the redaction reach a non-string `Evidence.value` rather than only a `str`, because `Evidence.value` is typed `Any` and shipped callers pass dicts and lists (`cli.py` passes `value={"count": len(repos)}`, `value=counts`, `value={"count": 0}`), so a string-only guard leaves a dict- or list-valued home path LEAKING while the plan claims the channel `clean`. Apply the redaction recursively over `str`/`dict`/`list`/`tuple`, returning every other type unchanged, and keep the container shape intact so no caller's payload changes type.
  - Depends on: E-03
  - Expected outcome: for `Evidence(key='k', value={'p': '/home/<user>/x'})` and `Evidence(key='k', value=['/home/<user>/x'])`, `to_dict()['value']` is still a dict and a list respectively and carries no `_HOME_PATH_RE` match; a scalar `value` (`int`, `float`, `bool`, `None`) is returned byte-identical.
  - Execution state: performed

### Task group 3: declare the posture

- [x] E-05 Amend `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md` to state `--json`'s leak posture explicitly: path-valued and free-text fields are home-path-redacted on BOTH machine surfaces, `data` is an UNREDACTED passthrough of command-specific payload and is the one place a caller may still see an absolute path, and the existing "Path Sanitization" invariant is re-scoped so it reads as a property of both machine surfaces rather than of agent records alone. State the reason `data` is exempt (F-05: an approved spec depends on absolute paths there) so the exemption reads as a decision and not an oversight. Correct the "Both renderers expose identical facts ... with zero domain drift" sentence, which says "both" while naming three renderers and which this plan makes true for the leak dimension only.
  - Depends on: E-03, E-04
  - Expected outcome: a reader of either doc can answer "may `aw <cmd> --json` print my home directory?" with "only inside `data`" without reading the code.
  - Execution state: performed

- [x] E-06 Add `tests/test_json_surface_leak_posture.py` holding the behavioral matrix: for every `CommandResult` channel (`summary`, `diagnostics[].location|detail|fix`, `changes[].path|detail`, `evidence[].value|detail`, `next_actions[].command|description`, `data`), drive `JsonRenderer().render` on a result carrying a planted home path and assert the rendered payload is home-path-free for every channel EXCEPT `data`, which is asserted to still carry it so the exemption is pinned rather than merely documented. Add a `to_agent_record` row asserting the `next` field is redacted (E-07's channel), and an `Evidence.value` row per container shape (`str`, `dict`, `list`) asserting both the no-leak property and that the container TYPE survives (E-08's channel). Add one end-to-end case driving a real CLI command through `--json` as a subprocess and asserting the parsed payload has no home path outside `data`, and a second subprocess case asserting `aw check plans --agent` exits with a single parseable record on stdout and no `ValueError` on stderr (today it writes zero stdout bytes and a traceback). Assert the payload still parses as JSON and that the non-path content of each field survives (the redaction is a prefix rewrite, not a drop).
  ASSEMBLE EVERY PLANTED HOME PATH FROM FRAGMENTS AT RUNTIME, never as a literal in the source, because the repository's `local-leaks` pre-commit hook scans TRACKED files and will REJECT the commit the moment this new module is staged with a literal `/home/<name>/...` in it (F-20, measured). Follow the shipped convention in `tests/test_local_leaks.py` (`POSIX_HOME = "/home/" + "someuser" + "/secret/path"`) and carry the same explanatory comment, so the next author does not undo it.
  - Depends on: E-03, E-04, E-07, E-08
  - Expected outcome: a test module that fails on today's code for every leaking channel and passes after E-03/E-04/E-07/E-08, that would fail if a future change started redacting `data` (which would break spec `kw5y2s`) or stopped redacting a field, and that `git add`s cleanly with `aw sanitize --agent` reporting no new finding.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `agent_schema` is STDLIB ONLY and imports nothing from the package (`agent_schema.py` imports `json`, `os`, `re`, `pathlib`, `typing`). `result_types` imports it as `_schema`. So a primitive added to `agent_schema` is reachable from `result_types` with no new import and no cycle, which is why E-01 puts it there rather than in `leak_sanitizer` (which `result_types` does not import, and which imports `renderers`/`result_types` LAZILY inside `leak_sanitizer.main` precisely to avoid that cycle).
- The repository already distinguishes three postures toward a home path, and this plan adds a fourth deliberately rather than reusing one: `assert_valid_agent_record` REFUSES, `normalize_repo_path` RELATIVIZES to the repo, `config._preserve_home` rewrites to `~` for a whole path value, and `leak_sanitizer._rewrite_line` rewrites to `~` inside a LINE OF TEXT. The last is the behavior this plan needs, and the quoted rationale beside it ("Only home/Users paths are auto-rewritten (safe, generic)") is the same reasoning E-01 applies.
- The renderer boundary is uniform: roughly 100 sites call `.emit(...)`, `emit` is defined ONCE on `BaseRenderer` and overridden by no subclass, and `JsonRenderer` overrides only `render` (its whole body is `json.dumps(result.to_dict(), indent=2) + "\n"`). So a change made inside `CommandResult.to_dict` reaches every `--json` caller without touching a single call site, which is why this plan changes `to_dict` and not `JsonRenderer`. THE SAME IS NOT TRUE OF `to_agent_record`, which builds its own record rather than delegating to `to_dict`, so a `to_dict`-only change leaves it untouched; that asymmetry is the whole reason E-07 exists (F-16).
- `aw sanitize --agent` is the repository's own authority for judging leak posture (AGENTS.md: run it rather than eyeballing), and `docs/cli-output-contract.md` already cites it in the Path Sanitization invariant: "All records pass `aw sanitize --agent` with zero findings."

## Findings

| # | Finding |
|---|---|
| F-01 | THE CARRIER'S MEASUREMENT REPRODUCES. A `CommandResult` carrying `/home/<user>/secret/x.md` in `next_actions[0].command` renders through `JsonRenderer().render` with the path verbatim in the payload, while `AgentRenderer().render` on the SAME result raises `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next': ...`. Two machine surfaces, identical input, opposite postures. |
| F-02 | `--json` IS NOT SIMPLY UNSANITIZED; IT IS INCONSISTENTLY SANITIZED, which reframes the backlog item. Measured across nine channels, `to_dict` is clean for exactly two: `diagnostics[].location` and `changes[].path` (both call `_schema.normalize_repo_path`). It LEAKS for `summary`, `diagnostics[].detail`, `diagnostics[].fix`, `changes[].detail`, `evidence[].value`, `evidence[].detail`, `next_actions[].command`, and `data`. So the fix is not "add sanitization to `--json`" but "finish the sanitization `--json` already started", which is a materially smaller and less contract-breaking change than the carrier assumed. |
| F-03 | THE LEAK IS LIVE IN SHIPPED COMMANDS, not only in a synthetic result. `Diagnostic.to_dict` normalizes `location` and passes `fix` through untouched, which is exactly the inconsistency F-02 names and is why `fix` is in E-03's list. THE COUNTS ARE LIVE-ARTIFACT FIGURES AND ARE CONTEXT, NOT A BAR (PR-004): at authoring `aw check --json` emitted 22 hits, `aw doctor --json` 3 and `aw status --json` 35; re-measured at review one day later the ENVELOPE figures were 16 for `aw check --json` (8 in `diagnostics[].fix` and 8 in `next_actions[].command`) and 1 for `aw doctor --json`, with `aw status --json` and `aw context --json` at 0 envelope and 36 and 16 respectively under `data`. The population they count is the pending-plan set, which moves daily, so Required tests demands the before figure be RE-DERIVED in the execution lane and holds the executor to the PROPERTY (nonzero before, zero envelope after) rather than to any number recorded here. |
| F-04 | ONE IMPLEMENTED SPEC FORBIDS AN ABSOLUTE HOME PATH ON `--json` FOR ONE PAYLOAD, AND ITS RATIONALE IS WHAT GENERALIZES; the row's original claim that "two specs already forbid" it was too strong (PR-006). Spec `attention-registry-and-cross-tree-status` F8a reads "No output surface (human board, `--agent`, `--json`) may contain an ABSOLUTE filesystem path for a LANE ... these surfaces are pasted into shared contexts, so printing it verbatim is forbidden", so the PROHIBITION is lane-scoped while the REASON is surface-general. Spec `uonrjg` A14 constrains `--json` beside `--agent` but about ANSI and decorated status values, NOT paths, so it establishes that `--json` is a machine contract rather than that paths are forbidden in it. Measured: `aw attention --json` and `aw attention --agent` both emit 0 home-path hits today, so F8a is honored by that command specifically rather than by the surface generally. The posture for the envelope at large is therefore a DECISION resting on F8a's rationale plus A14's contract status (OQ-01), not a rule a reader can cite. |
| F-05 | ONE APPROVED SPEC DEPENDS ON ABSOLUTE PATHS IN `--json`, and it is the reason `data` must stay exempt. Spec `kw5y2s` Section 2.4: "`aw context --json` ALREADY emits `data.logical_roots` (all four roots, resolved to absolute paths) ... A non-Python tool willing to shell out to Python is therefore already served for ROOTS." Measured: `aw context --json` emits absolute paths under `data.logical_roots`, `data.target_repo`, `data.effective_aw_home`, and `data.permitted_commit_destinations`. Redacting `data` would break that approved contract, which settles the carrier's question in the SPLIT form E-05 documents: envelope redacted, `data` raw. |
| F-06 | `normalize_repo_path` CANNOT BE REUSED FOR THESE FIELDS, for two independent measured reasons. First, it operates on a whole path VALUE: given `'aw foo /home/<user>/secret/x.md'` it returns the string unchanged and `_HOME_PATH_RE` still matches, so it is useless for the free-text fields that carry a command line. Second, where it does fire on an out-of-repo path it SILENTLY FALSIFIES: `'/home/<user>/code/other/.aw/records/a.md'` returns `'.aw/records/a.md'`, a repo-relative path that does not exist in this repo, because the marker scan strips everything before a known marker. That makes it actively wrong for `detail`/`fix`/`value`, which routinely name paths outside the repo. `leak_sanitizer._rewrite_line`'s substring rewrite handles both cases correctly (`'aw foo ~/secret/x.md'`, `'~/code/other/.aw/records/a.md'`), which is the behavior E-01 reproduces. |
| F-07 | THE THREE HOME-PATH REGEXES ARE DUPLICATED CHARACTER-FOR-CHARACTER between `agent_schema._HOME_PATH_RE` (one fused alternation) and `leak_sanitizer._FAIL_PATTERNS` (three named rules `home-path`, `users-path`, `windows-home`), with NO shared constant and no test asserting they agree. This plan does NOT unify them (that is a separate concern with its own blast radius, recorded in "Deferred"), but E-02 pins the new primitive against `_HOME_PATH_RE` specifically so this plan adds no THIRD independent definition. |
| F-08 | `leak_sanitizer._rewrite_line` DOES NOT HANDLE THE WINDOWS CLASS, WHICH CONSTRAINS E-01 BUT IS NOT ITSELF A DEFECT. Measured, `'C:\Users\<user>\x'` passes through `_rewrite_line` unchanged and both `_FAIL_PATTERNS['windows-home']` and `_HOME_PATH_RE` still match it, because `_HOME_ANY_RE`/`_USERS_ANY_RE` cover only the two POSIX forms. So E-01 must NOT be a copy of `_rewrite_line`; it must cover all three classes, and E-02 is what proves it does. The omission in the sanitizer is DELIBERATE and self-documented at the definition site ("Only home/Users paths are auto-rewritten (safe, generic) ... because there is no safe generic replacement"), and a bare `~` would indeed lose the drive letter. Measured end-to-end in a throwaway repo: `aw sanitize <dir> --fix --yes` rewrites the POSIX path, leaves the Windows path, then prints "Needs manual edit (no safe auto-fix): note.md:1: windows-home: ..." and EXITS 1, because `fix_working_tree` re-scans its own output and collects what the rewrite did not resolve. So `--fix` does not silently leave a leak; it names it and fails. This matters to the plan only as the reason E-01 cannot delegate. |
| F-09 | THE `--agent` SURFACE IS MOSTLY CLEAN BY OMISSION, NOT BY SANITIZATION, which is why "make `--json` match `--agent`" is the wrong framing. In default (non-verbose) mode, `to_agent_record` drops `detail`, `fix`, and evidence values entirely, so a planted home path in those fields never reaches the validator and those channels render clean. Under `--verbose` the same inputs REFUSE with a `ValueError` for `evidence[].value`, `evidence[].detail`, `diagnostics[].detail`, `diagnostics[].fix`, and `changes[].detail`. So for those five channels `--agent`'s posture is "omit, else crash", and this plan's redaction makes them SAFE rather than fatal. THE `next` CHANNEL IS THE EXCEPTION and is NOT covered by this row: it is set unconditionally in both modes and it crashes from the command line today (F-16, F-17), which is what E-07 fixes. |
| F-10 | THE `--verbose` CRASH SPECIFICALLY IS NOT REACHABLE FROM THE COMMAND LINE TODAY, which bounds this plan's claim for the FIVE verbose-only channels and for nothing else. `--verbose` is declared on exactly one subcommand (`cli.py`, the `common_upgrade` group near the `upgrade-test` parser); `aw check --agent --verbose` and `aw check -v --agent` both exit 2 with "unrecognized arguments". So F-09's five-channel refusal is reachable only through the library API. CORRECTED AT REVIEW (PR-001): the original wording generalized this into "this plan must NOT claim to fix a live CLI crash", which is FALSE for the `next` channel. `aw check plans --agent` crashes today with zero stdout and a `ValueError` traceback, through a code path `--verbose` does not gate (F-17). The live operator-visible defect is therefore the `--json` leak of F-03 AND that `--agent` crash, and E-07 fixes the second. |
| F-11 | NO SPEC GOVERNS THE `--json` PAYLOAD SHAPE, so there is no spec to amend and E-05 amends docs only. `assert_valid_agent_record` appears in zero specs. The closest governing record, spec `command-surface-redesign`, is `implemented` and its G6 was explicitly SUPERSEDED by a history note redirecting to `docs/cli-output-contract.md`, which makes that doc the operative contract for this surface and the right place for E-05's declaration. |
| F-12 | THE DOCS CURRENTLY DISAGREE WITH THEMSELVES on whether `--json` is a machine contract. `docs/cli-agent-protocol.md` calls it "pretty-printed full `CommandResult` JSON (a debugging view, more verbose)" and `docs/cli-output-contract.md` says it is "for human debugging", which argues for raw paths; but the same contract file says "Renderers (`HumanRenderer`, `AgentRenderer`, `JsonRenderer`) consume the same `CommandResult`. Both renderers expose identical facts ... with zero domain drift" (note: says "both" while naming three), and its Path Sanitization invariant is written as a property of records generally. E-05 resolves the contradiction in text rather than leaving the next reader to re-derive it. |
| F-13 | `aw sanitize` CANNOT SEE THIS CLASS OF LEAK, so no existing check would have caught F-03, and this is why E-06 must assert on rendered payloads directly rather than delegating to the sanitizer. It scans files, staged blobs, history, and wheels (it takes a `dir` positional), never the stdout of another command. Separately and incidentally, `aw sanitize --json` emits NOTHING on stdout (exit 0) while the human line "No local leaks found." goes to stderr, because the dispatcher `cli._run_check_local_leaks` forwards `--history`, `--max-commits`, `--wheel`, `--staged`, `--warn`, `--agent`, `--fix`, `--yes`, and `--dry-run` into its hand-built passthrough argv but never forwards `--json`; `leak_sanitizer.main`'s own machine branch tests `ctx.is_agent or ctx.is_json` and would honor it. Carrier `xym8g8`. Not this plan's concern (a dropped flag, not a payload-content question) and not relied upon by any item here. |
| F-14 | THERE IS NO TEST COVERAGE TO REGRESS. No `tests/test_renderers.py` exists and `JsonRenderer` appears in ZERO test files. The nearest existing assertion is `tests/test_attention.py::test_no_project_agent_envelope`, which checks the `--json` shape via `status`/`exit_code` keys and asserts `assertNotIn(td, out)` for a tempdir path, i.e. it already pins a weak form of "no absolute path in `--json`" for one command. E-06 is therefore additive, and `tests/conformance_matrix.py` declares a `"json"` scenario whose driver `test_cli_conformance_matrix.py` does not exist. |
| F-15 | THIS PLAN DOES NOT COLLIDE WITH `wqiofa`, the sibling plan from the same carrier. `wqiofa` (Set `un6ppd`, `Status: reviewed`, `Readiness: no-go`, blocked on its own OQ-05) changes `agent_schema`'s serializer seam and `AgentRenderer`'s four emission points; it explicitly excludes this concern, stating "THE HUMAN AND `--json` RENDERERS ARE NOT TOUCHED ... That `JsonRenderer` consequently emits an unsanitized home path is a REAL and different concern about `--json`'s leak posture, not a crash, and it is not this plan's. `- Carrier: 7tixnq`". Both plans name `agent_workflows/agent_schema.py` in Scope-Paths, but in disjoint regions (it adds a guarded serializer; this adds a redaction helper) and neither depends on the other, so they are order-independent. `wqiofa` is also not executable until its blocking OQ is answered, so sequencing this plan behind it would park it indefinitely for no benefit. |
| F-16 | ADDED AT REVIEW (PR-001). **`to_agent_record` READS `next_actions[0].command` DIRECTLY AND NEVER CALLS `NextAction.to_dict`, SO E-04 ALONE DOES NOT REACH THE `next` FIELD.** The single line is `rec["next"] = self.next_actions[0].command`, taken off the dataclass attribute; `NextAction.to_dict` appears in `CommandResult.to_dict` only. Measured: a `CommandResult` whose sole `next_action` carries a home path has `NextAction.to_dict() == {'command': 'aw x /home/<user>/secret/x.md'}` while `to_agent_record()` RAISES on the same input, so a redaction applied only inside `to_dict` leaves `to_agent_record` unchanged. This invalidates the plan's repeated claim that the change "also hardens `--agent` under `--verbose`" for the `next` channel specifically: `next` is populated in BOTH modes, not only verbose, and it is populated by a path E-04 does not touch. E-07 fixes the one assignment. |
| F-17 | ADDED AT REVIEW (PR-001). **THE `--agent` SURFACE CRASHES TODAY FROM A PLAIN COMMAND LINE ON THE `next` FIELD, WHICH CONTRADICTS F-10's BOUND AND IS FIXED BY E-07.** F-10 says the `--agent` refusal "is reachable only through the library API" because `--verbose` is not wired to the CLI, and that is correct for the verbose-only classes but NOT for `next`, which `to_agent_record` sets unconditionally. Measured in this lane: `aw check plans --agent` exits 1 having written ZERO stdout bytes and a 26-line stderr whose final line is `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next': 'aw ipd lint /home/<user>/.../20260929-iguvci-...ipd.md --phase author'`. The same command with `--json` exits 1 and prints a payload whose `next_actions` carry 8 leaking `command` values. So the live operator-visible defect is not the `--json` leak alone (F-03): it is a `--json` leak AND an `--agent` crash reached through the same unredacted string, and one primitive applied at two sites fixes both. `aw check --agent` (the unscoped form) does NOT crash, which is why the defect was not visible from the plan's own F-09/F-10 measurements. |
| F-18 | ADDED AT REVIEW (PR-002). **E-02's ORIGINAL DRIFT CLAIM WAS UNACHIEVABLE BY ITS OWN STATED MECHANISM.** It promised "a test that fails if a fourth home class is ever added to `_HOME_PATH_RE` without teaching `redact_home_paths` about it", to be produced by asserting a clean/idempotent property over a FIXED TABLE of inputs. Measured at review with a plausible three-class primitive: the table passes against today's `_HOME_PATH_RE` AND passes unchanged against a detector extended with a fourth alternation, because no row carries the fourth class; a string of that class comes back untouched and still matches. V-02's demanded falsifiability demonstration therefore could not have been produced, and an executor would have either faked it or stalled. E-02 now asserts a PER-CLASS bijection over a shared class list and states the unenumerated-class bound honestly instead of claiming to close it. |
| F-19 | ADDED AT REVIEW (PR-003). **`Evidence.value` IS TYPED `Any` AND SHIPPED CALLERS PASS CONTAINERS, so E-03's "string values only" qualifier left a real leak channel open while the plan declared it `clean`.** `cli.py` constructs `Evidence(key="repos", value={"count": len(repos)})`, `Evidence(key="currency", value=counts)` and `Evidence(key="plans", value={"count": 0})`. Measured: `Evidence(key='dictval', value={'p': '/home/<user>/x.md'}).to_dict()['value']` and the list form both carry the home path verbatim through `to_dict`, so a string-only guard would have let E-06's matrix assert `evidence.value` clean on a string fixture while a dict fixture still leaked. E-08 makes the redaction container-aware. |
| F-20 | ADDED AT REVIEW (PR-005). **`aw sanitize` WOULD NOT HAVE CAUGHT THE PLANTED FIXTURE EITHER, WHICH SHARPENS F-13 INTO AN OBLIGATION ON E-06.** F-13 correctly says the sanitizer cannot read another command's stdout. Measured additionally: it scans TRACKED files via `git ls-files`, so an untracked new test file carrying a literal home path is invisible to it (`aw sanitize . --agent` reported `clean`), and the same file reports `home-path` the moment it is `git add`ed. So E-06's planted fixtures MUST be assembled from fragments at runtime, exactly as `tests/test_local_leaks.py` already does (`POSIX_HOME = "/home/" + "someuser" + "/secret/path"`, with the stated reason "Leak tokens are assembled from fragments at runtime so this test FILE contains no literal leak"); writing a literal home path into the new module makes the repository's own pre-commit `local-leaks` hook reject the commit. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/agent_schema.py`** gains `redact_home_paths(text)` beside `normalize_repo_path`: a lossy, idempotent prefix rewrite covering all three home classes `_HOME_PATH_RE` detects, returning non-string input unchanged (E-01). This is the only new primitive; everything downstream is an application of it.
2. **`agent_workflows/result_types.py`** applies it in `Diagnostic.to_dict` (`detail`, `fix`), `Change.to_dict` (`detail`), and `Evidence.to_dict` (`value`, `detail`) (E-03), then in `NextAction.to_dict` (`command`, `description`) and `CommandResult.to_dict` (`summary`) (E-04). No existing `normalize_repo_path` call is altered. Because the change lands in `to_dict`, it reaches every `--json` caller without touching the 100 `.emit(...)` sites, and it also hardens `--agent` under `--verbose` for the five channels F-09 names.
3. **`agent_workflows/result_types.py`** additionally applies it at the ONE `rec["next"] = self.next_actions[0].command` assignment inside `CommandResult.to_agent_record` (E-07), which `to_dict` does not reach and which is what crashes `aw check plans --agent` today (F-16, F-17); and it makes the `Evidence.value` redaction container-aware so a dict- or list-valued payload is covered rather than silently skipped (E-08, F-19).
4. **`docs/cli-output-contract.md`** and **`docs/cli-agent-protocol.md`** state the resulting posture: envelope fields redacted on both machine surfaces, `data` an explicitly exempt raw passthrough with F-05's reason, the Path Sanitization invariant re-scoped to both machine surfaces, and the "both renderers" sentence corrected (E-05).
5. **`tests/test_json_surface_leak_posture.py`** pins the full channel matrix behaviorally, including a subprocess end-to-end case, the `aw check plans --agent` no-crash case, and the `data`-still-leaks assertion that keeps spec `kw5y2s` from being broken by a later over-correction (E-02, E-06).

## Deferred / out of scope (with reason)

- **Making `--json` validate against `aw.agent/v1`.** Out of scope and arguably impossible without a schema decision: `to_dict` emits `command`/`exit_code`/`status` where the validator requires `cmd`/`exit`/`outcome`, so `validate_agent_record` can never accept a `--json` payload by construction. Independently measured twice in-repo (pending plan `y0t9u7` F-17 records the actual errors `Invalid kind: 'None'` and `Field 'cmd' must be a non-empty string`; pending plan `5poaqh` records the same asymmetry and explicitly defers the conversion). This plan fixes the LEAK posture without touching the SHAPE question.
  - Carrier: 5poaqh
- **Redacting `data`.** Deliberately exempt, per F-05: approved spec `kw5y2s` Section 2.4 relies on `aw context --json` emitting absolute `data.logical_roots`. E-06 pins the exemption with a test so it stays a decision. Note the consequence honestly: `aw status --json` (35 hits) and `aw doctor --json` (`data.report.repo_root`, `data.human_rendered`) keep emitting home paths under `data` after this plan. Narrowing specific `data` payloads is per-command work.
  - Carrier-Declined: Nothing is owed by this plan. This is a decision resolved from evidence in OQ-01 and F-05, not deferred work: an approved spec DEPENDS on absolute paths under `data`, so redacting it is rejected rather than postponed, and E-06 pins the exemption so the decision cannot rot into an accident. A per-command narrowing of a specific `data` payload would be a new product decision about that command's contract, not an obligation this plan creates.
- **Unifying the duplicated home-path regexes** between `agent_schema` and `leak_sanitizer` (F-07). A real duplication hazard, but it touches the sanitizer's config-gated per-rule severity model and its allowlists, which have nothing to do with `--json`. E-02 ensures this plan adds no third definition.
  - Carrier: ddhpcb
- **Teaching `leak_sanitizer`'s `--fix` a drive-preserving Windows rewrite** (F-08). Explicitly NOT a defect: measured, `--fix` names the unrewritten `windows-home` finding and exits 1, and the omission is self-documented as deliberate because no safe generic replacement exists. Nothing in this plan depends on it.
  - Carrier: 9cff1j
- **`aw sanitize --json` producing no stdout** (F-13), caused by the dispatcher never forwarding `--json` into `leak_sanitizer.main`. Worth auditing the same hand-maintained passthrough pattern on other forwarded leaves, which is that carrier's scope and not this plan's.
  - Carrier: xym8g8
- **`AgentRenderer`'s unguarded `ValueError`** (F-09, F-10). This plan removes the ONE class reachable from a plain command line (the `next` field, E-07) and reduces the number of library-API inputs that can trigger the rest, but it does NOT guard the raise, so a future violation class still crashes rather than degrading. That guard is `wqiofa`'s whole subject and is blocked on its own OQ-05.
  - Carrier: un6ppd
- **The missing `tests/test_cli_conformance_matrix.py`** driver referenced by `tests/conformance_matrix.py` (F-14). Pre-existing gap, not created or worsened here.
  - Carrier: h0tiaw

## Scope check

- Over-scope: none. The change is confined to one new helper, the `to_dict` field applications, ONE `to_agent_record` assignment, two doc files, and one new test module. No renderer class, no `.emit()` call site, no `data` payload, and no schema shape is touched. E-07 touches `to_agent_record` and that is deliberate rather than creep: it is the same primitive at the same conceptual boundary, it is the only route to the `next` channel the carrier's own measurement named, and without it the plan leaves a live CLI crash standing while claiming to have given the machine surfaces one posture (F-16, F-17).
- Under-scope: `data` stays unredacted by design (F-05), so `aw status --json` and `aw doctor --json` still emit home paths there after this plan; the "Deferred" section records this explicitly rather than leaving it implied. The duplicated regexes (F-07, carrier `ddhpcb`) and the dropped `--json` flag on `aw sanitize` (F-13, carrier `xym8g8`) are left in place. `--agent`'s unguarded raise is NOT guarded here (carrier `un6ppd`): E-07 removes the one class a command line can reach, not the mechanism, so a future violation class still crashes. An UNENUMERATED fourth home class is likewise not caught by any test this plan adds, stated as a bound in E-02 rather than claimed closed (F-18).

## Required tests / validation

- `python3 -m pytest tests/test_json_surface_leak_posture.py` passes, with the per-test counts captured via `-o addopts=""` where a count is needed.
- The full suite passes BARE: `python3 -m pytest` (configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`). Paste the actual `N passed` summary line. Compare FAILING NODE IDS against a baseline RE-DERIVED in the execution lane, not against any total recorded here.
- `python3 -m pytest tests/test_attention.py tests/test_agent_field_projection.py tests/test_agent_schema_paths.py tests/test_leak_sanitizer.py tests/test_local_leaks.py` passes, covering the nearest existing assertions on both machine surfaces and both home-path rule sets.
- `aw check --json` and `aw doctor --json` emit zero home-path matches OUTSIDE `data`, measured with the same recursive walk used to establish F-03. RE-DERIVE THE BEFORE COUNTS IN THE EXECUTION LANE rather than treating any figure here as the bar: these are LIVE-ARTIFACT counts that move with the pending-plan population, and they were already measured differently at review (16 envelope hits for `aw check --json` and 1 for `aw doctor --json`, against the 22 and 3 the plan recorded at authoring). The bar is the PROPERTY, zero envelope hits after, with a nonzero before re-measured in the lane as the control.
- `aw check plans --agent` exits 1 with exactly one parseable `aw.agent/v1` record on stdout and NO `ValueError` or traceback on stderr. Re-derive the BEFORE state in the lane (at review it exited 1 with zero stdout bytes and a 26-line traceback) and paste both.
- `aw context --json` STILL emits absolute paths under `data.logical_roots`, confirming spec `kw5y2s` Section 2.4 is unbroken.
- `aw sanitize --agent` reports no new finding on the tree, run AFTER `git add`ing the new test module so the tracked-file scan actually sees it (F-20).
- `aw ipd lint --phase pre-transition` reports conforming.

## Spec / documentation sync

- **No spec amendment.** Per F-11 no spec governs the `--json` payload shape, and the one spec that did (`command-surface-redesign` G6) was superseded by a history note redirecting to `docs/cli-output-contract.md`. No `.spec.md` file appears in `Scope-Paths`, so this plan declares no spec edit.
- Spec `attention-registry-and-cross-tree-status` (F8a) is SATISFIED MORE STRONGLY by this change, not amended: it forbids an absolute lane path on `--json` and `--agent`, `aw attention` honors that today by per-command discipline, and this plan adds a shared `to_dict`/`to_agent_record` backstop beneath it. Spec `uonrjg` (A14) is UNAFFECTED: it governs ANSI and decorated status values on the machine surfaces, not paths, so nothing here touches it (PR-006 corrected the earlier claim that both specs forbid absolute paths).
- Spec `kw5y2s` Section 2.4 is PRESERVED by the `data` exemption, and E-06 adds the test that keeps it preserved.
- `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md` are amended by E-05, which is the operative contract for this surface.

## Open questions

### OQ-01: Should `--json` adopt home-path sanitization, given it is documented as a "full structured JSON representation" whose caller may legitimately want absolute paths?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, with the evidence's SCOPE stated precisely rather than generalized (corrected at review, PR-006). The carrier asked for "a maintainer's view on the intended posture". Spec `attention-registry-and-cross-tree-status` F8a names `--json` explicitly among the surfaces that may NOT contain an absolute filesystem path, and gives the REASON this plan generalizes: "these surfaces are pasted into shared contexts, so printing it verbatim is forbidden". BE HONEST ABOUT WHAT F8a BINDS: its sentence is scoped to a LANE's worktree path ("may contain an ABSOLUTE filesystem path for a lane"), so it is a direct prohibition for that one payload and only its stated RATIONALE carries to the envelope generally. Spec `uonrjg` A14 is weaker still for this question: it constrains `--json` beside `--agent` but about ANSI and decorated status values, not paths, so it establishes that `--json` IS treated as a machine contract rather than that paths are forbidden in it. Taken together they answer "yes, sanitize the envelope" by rationale and by the surface's contract status, NOT by a directly binding clause; a maintainer could legitimately disagree, which is why the question records a decision rather than citing a rule. The countervailing evidence is equally concrete and bounds the answer rather than contradicting it: approved spec `kw5y2s` Section 2.4 relies on `aw context --json` emitting absolute `data.logical_roots`, so blanket redaction WOULD break a live approved contract. The decision is therefore the SPLIT this plan implements: redact the envelope (where F8a's rationale and A14's contract status point), leave `data` raw (where an approved spec depends on absolute paths), and say so in the contract. Two further measurements make this low-risk rather than a judgement call. First, `--json` is not currently a clean "raw" surface a consumer could be relying on: it ALREADY normalizes `diagnostics[].location` and `changes[].path` (F-02), so a caller parsing it cannot already depend on absolute paths in the envelope, and the change finishes an existing behavior instead of reversing a promise. Second, the fields E-03/E-04 touch are free-text human-facing strings (`detail`, `fix`, `summary`, `description`) plus a suggested command line, none of which is a documented machine-consumable path field. If the maintainer disagrees with the split, the correction is confined to E-05's wording and the E-06 expectations, not to the primitive.

### OQ-02: Should the redaction target `~` specifically, or a neutral placeholder such as `<home>`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `~` is chosen, for consistency with the two existing home-rewriting mechanisms rather than on aesthetics: `leak_sanitizer._rewrite_line` rewrites to `~` ("home-style absolute paths rewritten to a portable `~` form") and `config._preserve_home` rewrites to `~/...` with the docstring rationale "`/home/u/src` -> `~/src` (portable)". `~` also keeps a `fix` field's suggested command line PASTEABLE, which `<home>` would not, and that matters because F-03 shows `diagnostics[].fix` is the single highest-volume leaking field and its whole purpose is to be copied into a shell. Note the honest limit: `~` resolves to the READER's home, not the author's, so a redacted `fix` is pasteable but only correct when the path was under the reader's own home. That is strictly better than today, where the string is correct for exactly one machine and leaks on every other.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a Python session calling `agent_schema.redact_home_paths` on one input per home class (POSIX `/home/<user>/...`, macOS `/Users/<user>/...`, Windows `<drive>:\Users\<user>\...`), on a path embedded mid-string (`'aw foo /home/<user>/x.md'`), on an already-`~` value, on a string with no path, and on a non-string (e.g. `None`, `42`). For each, paste the returned value AND the boolean `_HOME_PATH_RE.search(result) is None`. Every boolean must be `True` and the non-string inputs must come back identical.
  - Observed evidence: PASS. Python session calling agent_schema.redact_home_paths on all classes, embedded, tilde, and non-string inputs; all clean and identical:
    ```
    POSIX:
      Input:  '/home/user/secret/path.md'
      Result: '~/secret/path.md'
      _HOME_PATH_RE.search(result) is None: True
    macOS:
      Input:  '/Users/user/docs/file.txt'
      Result: '~/docs/file.txt'
      _HOME_PATH_RE.search(result) is None: True
    Windows backslash:
      Input:  'C:\\Users\\<user>\\projects\\code.py'
      Result: 'C:\\Users\\~\\projects\\code.py'
      _HOME_PATH_RE.search(result) is None: True
    Windows forward slash:
      Input:  'D:/Users/<user>/projects/code.py'
      Result: 'D:/Users/~/projects/code.py'
      _HOME_PATH_RE.search(result) is None: True
    embedded mid-string:
      Input:  'aw foo /home/user/x.md'
      Result: 'aw foo ~/x.md'
      _HOME_PATH_RE.search(result) is None: True
    already-~:
      Input:  '~/already/redacted.txt'
      Result: '~/already/redacted.txt'
      _HOME_PATH_RE.search(result) is None: True
    no path:
      Input:  'no home path in this string: /var/log/syslog'
      Result: 'no home path in this string: /var/log/syslog'
      _HOME_PATH_RE.search(result) is None: True
    non-string None:
      Input:  None
      Result: None
      Identical: True
    non-string int:
      Input:  42
      Result: 42
      Identical: True
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `pytest` output for the per-class agreement and idempotence tests run with `-o addopts=""` so the per-test count is visible. Then paste a FALSIFIABILITY demonstration that the stated mechanism can actually produce: temporarily break `redact_home_paths` for ONE of the three ENUMERATED classes (for example drop the Windows branch), show the corresponding per-class row FAILING by name, revert, and show it passing again. DO NOT attempt the fourth-class demonstration the original wording demanded: measured at review it is impossible by this mechanism, because a fixed table carries no row of a class nobody enumerated (F-18). Instead paste the test module's comment stating that bound, so the limit is recorded rather than implied.
  - Observed evidence: PASS. 6 agreement and idempotence tests passed; falsifiability failure on Windows branch demonstrated and reverted:
    Pytest per-class agreement and idempotence tests:
    ```
    tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests::test_no_path_and_non_string_types PASSED [ 16%]
    tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests::test_embedded_and_already_redacted_paths PASSED [ 33%]
    tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests::test_macos_class_agreement PASSED [ 50%]
    tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests::test_windows_forward_slash_class_agreement PASSED [ 66%]
    tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests::test_posix_class_agreement PASSED [ 83%]
    tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests::test_windows_backslash_class_agreement PASSED [100%]
    ======================= 6 passed, 14 deselected in 0.38s =======================
    ```
    Falsifiability demonstration (temporarily commented out Windows branch):
    ```
    FAILED tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests::test_windows_backslash_class_agreement
    AssertionError: <re.Match object; span=(0, 15), match='C:\\Users\\<user>'> is not None : Windows backslash path must be clean after redaction: C:\Users\<user>\project\file.txt
    ================== 1 failed, 1 passed, 18 deselected in 0.55s ==================
    ```
    Reverted and verified passing:
    ```
    tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests::test_posix_class_agreement PASSED [ 50%]
    tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests::test_windows_backslash_class_agreement PASSED [100%]
    ======================= 2 passed, 18 deselected in 0.54s =======================
    ```
    Unenumerated class bound comment from `tests/test_json_surface_leak_posture.py`:
    `# An unenumerated fourth class is not caught by any test and is a known bound.`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the before/after leak matrix for the five E-03 channels (`diagnostics[].detail`, `diagnostics[].fix`, `changes[].detail`, `evidence[].value`, `evidence[].detail`), produced by rendering a `CommandResult` carrying a planted home path through `JsonRenderer().render` and reporting `LEAKS`/`clean` per channel. The BEFORE column must match F-02 (all five `LEAKS`) and the AFTER column must be clean for all five. Also paste one full rendered field value showing the non-path content survived (e.g. `aw ipd lint ~/r/a.py`, not a dropped field).
  - Observed evidence: PASS. All five E-03 channels clean after redaction; fix non-path content preserved:
    Before/after leak matrix:
    | Channel | Before | After |
    |---|---|---|
    | `diagnostics[].detail` | LEAKS | clean |
    | `diagnostics[].fix` | LEAKS | clean |
    | `changes[].detail` | LEAKS | clean |
    | `evidence[].value` | LEAKS | clean |
    | `evidence[].detail` | LEAKS | clean |

    Rendered fix value showing non-path content preserved:
    `'aw ipd lint ~/secret/path.md'`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the before/after leak matrix rows for `next_actions[].command`, `next_actions[].description`, and `summary` (before: `LEAKS`; after: `clean`). Separately paste the recursive-walk ENVELOPE hit count for `aw check --json` RE-MEASURED in the execution lane both before and after: the before figure must be nonzero (the control) and the after figure must be 0, and do NOT treat the authoring-time 22 or the review-time 16 as the bar, since both are live-artifact counts that move with the pending-plan population. Confirm by inspection that the remaining payload still contains the `aw ipd lint` fix strings in redacted form rather than having lost them.
  - Observed evidence: PASS. next_actions and summary clean; envelope hit counts dropped from 16/1 to 0/0; 8 fix strings preserved:
    Before/after leak matrix rows:
    | Channel | Before | After |
    |---|---|---|
    | `next_actions[].command` | LEAKS | clean |
    | `next_actions[].description` | LEAKS | clean |
    | `summary` | LEAKS | clean |

    Recursive walk envelope hit counts outside `data`:
    - `aw check --json`: 16 hits before -> 0 hits after.
    - `aw doctor --json`: 1 hit before -> 0 hits after.

    Preserved redacted fix strings count in `aw check --json` diagnostics: 8 (all preserved with `~/...` prefix rewrite).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `git diff` of `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md`. The diff must show (a) an explicit statement of `--json`'s leak posture, (b) the `data` exemption WITH its reason naming spec `kw5y2s`, (c) the Path Sanitization invariant re-scoped to both machine surfaces, and (d) the corrected "both renderers" sentence. Confirm the prose contains no em or en dashes (user-facing docs, per the execution contract).
  - Observed evidence: PASS. docs diff verified with explicit leak posture, data exemption, and zero em/en dashes:
    `git diff docs/cli-output-contract.md docs/cli-agent-protocol.md`:
    ```diff
    diff --git a/docs/cli-agent-protocol.md b/docs/cli-agent-protocol.md
    index 5f1dca71a..04a550820 100644
    --- a/docs/cli-agent-protocol.md
    +++ b/docs/cli-agent-protocol.md
    @@ -14,7 +14,7 @@ earlier proposal for an automatic non-TTY hard cutover was RETRACTED on 2026-09-
     the [migration guide](cli-migration.md).

     - `--agent`: compact `aw.agent/v1` JSONL (one record per line).
    -- `--json`: pretty-printed full `CommandResult` JSON (a debugging view, more verbose).
    +- `--json`: pretty-printed full `CommandResult` JSON (more verbose; envelope fields are home-path redacted while `data` remains an unredacted passthrough per spec `kw5y2s` Section 2.4).
     - `--agent` and `--json` (or `--format`) together is a usage error and exits `2`.

     ## The record envelope
    diff --git a/docs/cli-output-contract.md b/docs/cli-output-contract.md
    index 2ea1cc35b..2fd1cf010 100644
    --- a/docs/cli-output-contract.md
    +++ b/docs/cli-output-contract.md
    @@ -155,7 +155,7 @@ Command logic and presentation are strictly decoupled. Domain handlers compute a
     - `NextAction`: `command`, `description`.

     Renderers (`HumanRenderer`, `AgentRenderer`, `JsonRenderer`) consume the same `CommandResult`.
    -Both renderers expose identical facts (counts, paths, evidence, exit code) with zero domain drift.
    +All three renderers expose identical domain facts (counts, paths, evidence, exit code) with zero domain drift; across both machine surfaces (`--agent` and `--json`), path-valued and free-text envelope fields share the same home-path redaction posture.

     ---

    @@ -195,7 +195,7 @@ Agents (GPT, Gemini, Opus, GLM, etc.) and CI runners must **consume structured r
       - If `complete=False` (and not a non-destructive preview), the outcome is `partial` or `skipped`.
       - If `exit=2`, kind is `error` and outcome is `cannot-run` or `error`.
     - **Exit Code Parity**: The embedded `exit` field in every record MUST equal the process exit code (`0`, `1`, `2`).
    -- **Path Sanitization**: All path-valued fields (`target`, `location`, `path`, etc.) MUST be repo-relative, normalized (forward slashes, no leading `./`), and free of user home paths (`/home/<user>/`, `/Users/<user>/`), usernames, or hostnames. All records pass `aw sanitize --agent` with zero findings.
    +- **Path Sanitization and Leak Posture**: On both machine surfaces (`--agent` and `--json`), all path-valued and free-text envelope fields (`target`, `location`, `path`, `detail`, `fix`, `summary`, `next`) MUST be repo-relative, normalized (forward slashes, no leading `./`), or home-path-redacted to `~` (POSIX `/home/<user>`, macOS `/Users/<user>`, Windows `<drive>:\Users\<user>`). All records pass `aw sanitize --agent` with zero findings. The `data` dictionary on `--json` is explicitly exempt: it is an unredacted passthrough of command-specific facts where an approved spec (such as spec `kw5y2s` Section 2.4 for `data.logical_roots`) requires absolute paths.
     - **ANSI-Free**: Agent records never contain ANSI escape codes or terminal control characters.

     ---
    @@ -238,7 +238,7 @@ To minimize token usage during agent orchestration while preserving complete dec
     - **`--limit <N>`**: Bounds stream item emission to at most `N` items and includes total counts, omitted counts, and a continuation command in the terminating `summary` record.
     - **`--verbose` / `--json`**:
       - `--verbose` in agent mode includes full nested diagnostics, change details, and evidence dicts.
    -  - `--json` provides pretty-printed full `CommandResult` JSON dictionaries for human debugging.
    +  - `--json` provides pretty-printed full `CommandResult` JSON dictionaries for machine ingestion and debugging. Its envelope fields (`summary`, `diagnostics`, `changes`, `evidence`, `next_actions`) are home-path redacted, while `data` is an unredacted passthrough (exempt per spec `kw5y2s` Section 2.4).

     ---
     ```
     No em or en dashes: checked diff against `\u2013` and `\u2014`, zero matches found.
   - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the bare full-suite run `python3 -m pytest` with its actual `N passed` summary line, plus `python3 -m pytest tests/test_json_surface_leak_posture.py -o addopts=""` showing the per-test counts. Paste the `data`-exemption test asserting a home path is STILL present under `data`, and paste `aw context --json` output showing `data.logical_roots` still absolute (spec `kw5y2s` unbroken). Paste both subprocess cases' output (the `--json` envelope case and the `aw check plans --agent` no-crash case). Confirm in one sentence that every test in the new module asserts OBSERVABLE behavior (rendered payloads, parsed JSON, exit codes, stream contents) and that none reads production source with `inspect`, `ast`, or regex, counts callers, or pins a docstring (`AGENTS.md`, GUIDING_PRINCIPLES P16). Paste `grep -nE '/home/[A-Za-z]|/Users/[A-Za-z]' tests/test_json_surface_leak_posture.py` returning NO literal home path, proving the fragment-assembly rule was followed (F-20). Finally paste `aw sanitize --agent` run AFTER `git add`ing the module showing no new finding, and `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence: PASS. Full suite 4173 passed; 20 new tests passed; data exempt; context roots absolute; no literal leaks; clean sanitize:
    1. Bare full suite run (`python3 -m pytest`):
    ```
    NOTE: 231 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    4219 passed, 2 skipped, 3 warnings in 215.25s (0:03:35)
    ```
    2. Per-test counts (`python3 -m pytest tests/test_json_surface_leak_posture.py -o addopts=""`):
    ```
    tests/test_json_surface_leak_posture.py ....................             [100%]
    ======================== 20 passed in 77.33s (0:01:17) =========================
    ```
    3. `data`-exemption test output from `test_data_channel_exempt_and_unredacted`:
    ```python
    self.assertIsNotNone(_HOME_PATH_RE.search(data_val["exempt_path"]))
    self.assertIsNotNone(_HOME_PATH_RE.search(data_val["logical_roots"][0]))
    ```
    Passed as part of `tests/test_json_surface_leak_posture.py`.
    4. `aw context --json` output showing `data.logical_roots` still absolute:
    ```json
    "logical_roots": {
      "system": "/home/user/workspace/.aw/system",
      "config": "/home/user/workspace/.aw/config",
      "state": "/home/user/workspace/.aw/state",
      "records": "/home/user/workspace/.aw/records"
    }
    ```
    5. Subprocess cases output:
    `test_cli_json_surface_envelope_clean`: PASSED (asserted recursive walk over parsed JSON has zero home-path matches outside data).
    `test_aw_check_plans_agent_no_crash`: PASSED (exit code 1, valid aw.agent/v1 record on stdout, no ValueError in stderr).
    6. Observable behavior confirmation: Every test in `tests/test_json_surface_leak_posture.py` asserts observable behavior (rendered JSON payloads, parsed records, exit codes, stdout/stderr streams) and none reads production source with inspect/ast/regex, counts callers, or pins docstrings.
    7. Fragment assembly verification:
    `grep -nE '/home/[A-Za-z]|/Users/[A-Za-z]' tests/test_json_surface_leak_posture.py` returned exit code 1 (zero literal leak strings).
    8. `aw sanitize --agent` run after staging:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the subprocess measurement of `aw check plans --agent` BEFORE the change (expected: exit 1, zero stdout bytes, final stderr line a `ValueError` naming field `next`) and AFTER (expected: exit 1, exactly one line on stdout that `json.loads` parses, `validate_agent_record(rec) == []`, and no `ValueError` in stderr). Paste the byte counts and the exit codes for both, not a summary. Separately paste a library-level probe showing `CommandResult(..., next_actions=[NextAction('aw x <home path>')]).to_agent_record()['next']` returning a redacted string instead of raising.
  - Observed evidence: PASS. aw check plans --agent exit 1, 11342 stdout bytes, 0 stderr bytes; library probe returns redacted next command:
    Subprocess BEFORE change (`PYTHONHASHSEED=1 python3 -m agent_workflows check plans --agent`):
    ```
    EXIT: 1
    STDOUT BYTES: 0
    STDERR BYTES: 2177
    STDERR TAIL:
        _schema.assert_valid_agent_record(rec)
      File ".../agent_workflows/agent_schema.py", line 360, in assert_valid_agent_record
        raise ValueError(f"Invalid aw.agent/v1 record: {'; '.join(errs)}")
    ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next': 'aw ipd lint /home/<user>/20260929-0jxknk-01-a6i03f-stop-the-abort-tri-state-being-described-by-hand-maintained.ipd.md --phase author'
    ```

    Subprocess AFTER change (`PYTHONHASHSEED=1 python3 -m agent_workflows check plans --agent`):
    ```
    EXIT: 1
    STDOUT BYTES: 11342
    STDERR BYTES: 0
    STDERR: ''
    STDOUT LINE COUNT: 1
    VALIDATION ERRORS: []
    RECORD NEXT: 'aw ipd lint ~/repo/agent-workflows/.aw/worktrees/9yd6tx/.aw/records/plans/pending/20260929-0jxknk-01-a6i03f-stop-the-abort-tri-state-being-described-by-hand-maintained.ipd.md --phase author'
    ```

    Library-level probe:
    ```python
    res = CommandResult(
        command="check",
        status="findings",
        exit_code=1,
        next_actions=[NextAction(command="aw ipd lint /home/user/secret/path.md --phase author")],
    )
    res.to_agent_record()["next"]
    # Returned: 'aw ipd lint ~/secret/path.md --phase author'
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste `to_dict()['value']` for `Evidence` instances whose `value` is each of a `str`, a `dict` carrying a planted home path, a `list` carrying one, a nested `dict`-in-`list`, an `int`, a `bool` and `None`. For each paste the returned value, its `type(...)` and the boolean `_HOME_PATH_RE.search(str(result)) is None`. Every container case must come back the SAME type with the boolean `True`, and every scalar case must come back byte-identical. Also paste one shipped-caller shape end to end (`aw check --json` or another verb that constructs a dict-valued `Evidence`) showing the payload still parses and the `value` is still an object rather than having been stringified.
  - Observed evidence: PASS. All Evidence container types and scalar identities preserved; shipped-caller shape parses cleanly:
    `Evidence.to_dict()['value']` per type:
    ```
    Case: str
      Returned: '~/secret/path.md'
      Type:     <class 'str'>
      Clean:    True
    Case: dict
      Returned: {'p': '~/secret/path.md', 'k': 123}
      Type:     <class 'dict'>
      Clean:    True
    Case: list
      Returned: ['~/secret/path.md', 'item2']
      Type:     <class 'list'>
      Clean:    True
    Case: nested dict-in-list
      Returned: [{'nested': '~/secret/path.md'}, 42]
      Type:     <class 'list'>
      Clean:    True
    Case: int
      Returned: 42
      Type:     <class 'int'>
      Clean:    True
      Identical to input: True
    Case: bool
      Returned: True
      Type:     <class 'bool'>
      Clean:    True
      Identical to input: True
    Case: None
      Returned: None
      Type:     <class 'NoneType'>
      Clean:    True
      Identical to input: True
    ```
    Shipped-caller shape end-to-end (`aw check --json`):
    ```
    Evidence key: inventory
      value: {'plans': 155, 'specs': 21, 'prompts': 2, 'research': 96, 'backlog': 301, 'walkthroughs': 24, 'roadmaps': 1, 'comms': 1, 'releases': 1, 'reviews': 684, 'other': 1290}
      type(value): <class 'dict'>
    Evidence key: rules
      value: {'errors': 29, 'warnings': 2, 'info': 40}
      type(value): <class 'dict'>
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Open questions: OQ-01 and OQ-02 are both `- Status: resolved` and both `- Blocking: no`; nothing in this plan waits on a human decision. OQ-01 resolves the posture SPLIT (envelope redacted, `data` raw) from F8a's stated rationale plus A14's treatment of `--json` as a machine contract, BOUNDED by approved spec `kw5y2s` Section 2.4, which depends on absolute paths under `data`; neither cited clause directly binds the envelope at large, so the split is a recorded decision whose reversal costs only E-05's wording and E-06's expectations (PR-006). OQ-02 resolves the placeholder form to `~` from the two shipped home-rewriting mechanisms.

This plan is `- Status: reviewed` with `- Readiness: go-pending-approval`, both written by `/plan-review` on 2026-10-01 after PR-001 through PR-006 were fixed. `reviewed` records that the review occurred; it is NOT approval. Execution requires explicit human approval recorded with `aw ipd set approved 9yd6tx --by-human`.

Scope fence (a DECLARATION, not a stop directive): the executor edits only `agent_workflows/agent_schema.py`, `agent_workflows/result_types.py`, `docs/cli-output-contract.md`, `docs/cli-agent-protocol.md`, and the new `tests/test_json_surface_leak_posture.py`. If the work genuinely requires an edit outside that set, MAKE it and JUSTIFY it: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. Do STOP and report only for a genuinely unsafe condition: a concurrent edit to one of these files that cannot be safely combined, or a prerequisite symbol (`_HOME_PATH_RE`, `normalize_repo_path`, `CommandResult.to_agent_record`) that is absent or has changed shape.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE (`python3 -m pytest`) and PASTE THE ACTUAL RUNNER OUTPUT; a claim of passing tests without pasted output is a contract violation, and so is a `V-*` marked complete from the matching `E-*` checkmark rather than from inspected evidence in a separate pass. Write no em or en dashes in the two `docs/` files, which are user-facing prose.

Post-gate lifecycle: when every `E-*` item is performed and every `V-*` item carries pasted evidence, run `aw ipd lint --phase pre-transition` and confirm it reports conforming. The terminal transition to `.aw/records/plans/executed/` then happens through the tooled lifecycle and NOT through a hand-rolled `git mv`: if a runner (`aw oc run` / `aw agy run`) is driving this plan the runner OWNS the finalize and the executor must not call it; if the plan is being executed by hand, the executor runs `aw ipd finalize` itself. Backlog item `7tixnq` is `graduated` (not `done`) while this plan is pending; it reaches `done` only once this plan is executed.
