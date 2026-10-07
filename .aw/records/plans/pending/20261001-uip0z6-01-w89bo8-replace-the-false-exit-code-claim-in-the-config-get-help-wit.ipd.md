# IPD: Replace the false exit-code claim in the config get help with the measured behavior

- Date: 2026-10-01
- Kind: child
- Concern: The shipped `aw config get --help` description promises a nonzero exit for an unset variable that never occurs, so a script written from the help text branches on an exit code that cannot arrive.
- Scope: Correct the one false sentence in the `config get` inline `description=` to the DRIVEN behavior, add a default-visible regression guard that fails on a re-introduced exit-code promise, and record the fix in the changelog. No handler, exit code, flag, or `help=` string changes.
- Scope-Paths: agent_workflows/cli.py, tests/test_config.py, CHANGELOG.md, .aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: uip0z6
- Blocks-Release: next
- Set: uip0z6
- Order: 1
- Highest E allocated: 06
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: w89bo8
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004, all FIXED. Reviewed in lane review-sweep-run-20261007T032752Z-4094028 at HEAD 2745954be; review record .aw/records/reviews/20261001-uip0z6-01-w89bo8-replace-the-false-exit-code-claim-in-the-config-get-help-wit.review.md. Re-drove F-01/F-03 (all match). PR-001: ypnk56 has EXECUTED, so the slow set is green (237 passed) and the bare run is 2 failed, 5219 passed, 2 skipped (unrelated live-corpus failures); E-06/V-06 now re-derive the baseline at the executing HEAD and compare failing-node sets. PR-002: OQ-01 named config show as a route to the unset/empty distinction; driven, config show aw_home prints the identical row in both states; E-02/OQ-01/F-04/V-02 corrected. PR-003: E-03 description guard made concrete (negative falsehood token plus positive authored anchor). PR-004: stale ypnk56-pending and backlog-transition wording swept from the scope fence and gate.

- 2026-10-01 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `uip0z6`; inherits `Blocks-Release: next` per the live-bug gate. Authored review-ready with every claim DRIVEN rather than reasoned, as the item explicitly demands ("Any replacement must be DRIVEN, not reasoned: this defect exists because a plausible sentence was never run"). Reproduced the item's measurements at the lane HEAD and widened them: the item's three unset keys all exit 0 printing empty, two further recognized keys (`defaults.backup`, `repos.search`) exit 0 printing a value, only `no.such.key` exits 2, and `config get` is 335 characters against a 76-character help. THREE AUTHORING FINDINGS WENT BEYOND THE ITEM. First, the promised distinction is not merely unimplemented but UNREPRESENTABLE: `config.normalize` DROPS an empty string, so no config file can hold "set to an empty value" for any string key and no future exit code could expose it (F-03); this is why the fix must not promise a weaker version of the same distinction. Second, the item's suggested replacement wording ("prints an empty line and exits 0") needs one correction: the unset and set-to-empty cases are INDISTINGUISHABLE under `--json` too, which returns `null` for both, so the honest sentence must name `config show` or the file as the only route (F-04). Third, the same false claim is MIRRORED in a tracked research survey (`ffi66q`), which is in scope to correct because leaving it makes the next reader re-derive the defect (F-05). One SIBLING AUDIT was performed as the item asks: `config show`, `set`, `add`, `remove`, and `is` descriptions were each driven and are ACCURATE, so only `config get` is wrong (F-06).
- 2026-10-01 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw config get --help` state what the command actually does, so a script author reading it does
not write a branch on an exit code that never arrives.

The user-visible point is narrow and real: the help currently tells a reader that an unset variable
exits nonzero and that this lets them tell "unset" from "set to an empty value". Driven, every
recognized variable exits 0, and the second distinction cannot be made by ANY means because an empty
value is not storable. A reader who trusts the sentence writes a conditional that silently never
fires.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure at the executing HEAD before editing prose

- [ ] E-01 RE-DRIVE the defect at the HEAD you are executing on, and do not take this plan's numbers
  on trust. In-process with a THROWAWAY `XDG_CONFIG_HOME` (the convention
  `tests.test_config.ConfigCliCommandTests.setUp` already uses), call `cli.main(["config","get",K])`
  for `defaults.migrate_layout`, `color_depth`, `aw_home`, `defaults.backup`, `repos.search`, and
  `no.such.key`, capturing exit code and stdout for each. Separately confirm the empty-value state is
  UNREPRESENTABLE by handing `config.normalize` a dict holding `""` for `aw_home` and showing the key
  is dropped (F-03). Record the `config get` description length and its `help=` length from the live
  parser. THIS IS THE ITEM'S CENTRAL INSTRUCTION, not a formality: the defect exists precisely because
  a plausible sentence was never run, so an executor who reasons about the new sentence instead of
  driving it reproduces the original error.
  - Depends on: none
  - Expected outcome: The item's measurements are confirmed or corrected in writing at the executing
    HEAD: five recognized keys exit 0 (three printing an empty line, `defaults.backup` printing
    `true`, `repos.search` printing `[]`), `no.such.key` exits 2 naming the valid keys, `normalize`
    drops an empty `aw_home`, and the description is longer than the help while being false.
  - Execution state: pending

### Task group 2: correct the prose and guard it

- [ ] E-02 REWRITE the false sentence in the `config get` inline `description=` on `p_config_get` in
  `cli._build_parser`, replacing the clause "Exits nonzero when the variable is not set, so a caller
  can distinguish 'unset' from 'set to an empty value'." with the behavior E-01 measured. EDIT IN
  PLACE as an inline kwarg: the parser already carries an inline `description=`, `config get` has NO
  `_DESCRIPTIONS` table key (driven: the table holds no `config get` entry), and plan `ypnk56` OQ-01
  settled inline as the route for a leaf, so do NOT move it to the table. KEEP the first two sentences,
  which are ACCURATE and were driven (the output is the value alone, unlike `config show`). The
  replacement must state: a recognized variable always exits 0, printing its value or an empty line
  when unset; only an UNRECOGNIZED name is refused with exit 2 naming the valid keys.   It must NOT
  promise ANY route to the unset/empty distinction (no exit code, no `--json` field, and NOT
  `config show`), because F-03 shows the state does not exist and PR-002 drove `config show aw_home`
  to print the identical `aw_home = -` row for both cases. If it mentions the distinction at all it
  must say the truthful thing: an empty value is not stored, so it reads the same as unset.
  WRITE NO CLAIM YOU HAVE NOT DRIVEN IN E-01. The new string must remain longer than the 76-character
  help so the `SubcommandDescriptionTests` length contract still holds.
  - Depends on: E-01
  - Expected outcome: `aw config get --help` and `aw conf get --help` both render a description whose
    every factual claim matches E-01's measurements, with no exit-code promise the command does not
    honor, and the contract test's length condition still satisfied.
  - Execution state: pending

- [ ] E-03 ADD a behavioral regression guard to `tests/test_config.py` that would FAIL on the
  unfixed tree. It must do two things. (1) DRIVE the command and assert the real contract: every
  recognized key exits 0 (including an unset one, printing empty), and an unrecognized key exits 2.
  (2) Assert the DESCRIPTION does not re-introduce the false promise, by reading the live parser's
  `description` for `config get` (an argparse attribute, NOT production source text) and requiring
  that it does not claim a nonzero or failing exit for an unset variable. Make (2) CONCRETE with two
  limbs on the whitespace-normalized description: a NEGATIVE limb asserting the falsehood's
  distinctive token is absent (case-insensitive `"nonzero when"` / `"not set, so"`), and a POSITIVE
  content anchor asserting the authored exit-0 statement E-02 writes is present (the same
  content-anchor shape `tests/test_subparser_descriptions.py::test_alias_shows_canonical_authored_prose`
  uses for `conf unset`). The negative limb alone is weak (a reworded falsehood evades it); the
  positive limb alone does not reject a re-added false clause; together they do. Do not anchor on the
  whole sentence, so a legitimate rewording of the surrounding prose does not break it. This is
  NOT a code-pinning test under AGENTS.md: it drives `cli.main` for the behavior and reads a PARSER
  OBJECT attribute for the rendered contract, using no `inspect`, `ast`, regex over source, or
  substring search of a source file. Place it in `tests/test_config.py` beside the existing
  `config get` coverage (`InstallPolicyDefaultsConfigTests.test_clearing_and_unset_removes_keys`
  already pins the exit 0) and NOT in `tests/test_cli.py`, whose `SubcommandDescriptionTests` is
  marked `slow` (module-level `pytestmark = pytest.mark.slow`) and so is DESELECTED from the default
  run; a guard against a false help string must be default-visible or it does not guard. Do NOT edit
  `tests/test_subparser_descriptions.py` either: it is executed plan `ypnk56`'s shipped guard and is
  outside this plan's Scope-Paths.
  - Depends on: E-02
  - Expected outcome: A new test in `tests/test_config.py` that is RED on the unfixed description and
    GREEN after E-02, and that runs in the default (non-slow) suite.
  - Execution state: pending

### Task group 3: stop the same falsehood being re-derived from records

- [ ] E-04 CORRECT the MIRRORED false claim in the tracked CLI inventory survey
  `.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md`, whose
  `aw config get <var>` row reads "Exits nonzero when unset, so 'unset' differs from 'empty'." That is
  the same falsehood in a record a later reader treats as ground truth (it declares itself "the
  current ground truth" for a whole-CLI naming review). Replace the row's description with the
  measured behavior and leave every other row untouched. Do NOT hand-edit the frontmatter, the
  `status:`, or the file name, and do NOT regenerate the survey: this is a one-row factual correction
  to the body, not a re-survey. Note in the row or nearby that the correction came from `uip0z6`.
  - Depends on: E-01
  - Expected outcome: The survey's `config get` row no longer asserts a nonzero exit, so the next
    reader of the inventory cannot re-derive the false contract from a tracked record.
  - Execution state: pending

- [ ] E-05 ADD exactly one `- Fixed:` line to `CHANGELOG.md` under `## 2.0.0 (pending)`, in the style
  of the existing `- Fixed:` entries, saying that `aw config get --help` no longer claims a nonzero
  exit for an unset variable. Write NO em or en dashes: `CHANGELOG.md` is user-facing prose under the
  AGENTS.md dash rule.
  - Depends on: E-02
  - Expected outcome: One added changelog line recording the user-visible help correction, with no
    em or en dash.
  - Execution state: pending

### Task group 4: prove the change against the recorded baseline

- [ ] E-06 RUN the full regression comparison against a baseline RE-DERIVED at the executing HEAD,
  and resolve any difference before claiming done. FIRST, BEFORE E-02, record the baseline: run the
  suite BARE per AGENTS.md (`python3 -m pytest`; no `-n0`, no extra `-q`, no `-p no:randomly`) and the
  slow set (`python3 -m pytest -m slow`) on the unmodified tree and keep each run's FAILING-NODE SET.
  THEN, after E-02..E-05, run both again and compare by FAILING-NODE SET, not by count. The counts this
  plan quotes are CONTEXT ONLY, never the bar (they drift with every merge: authoring measured
  `3692 passed, 2 skipped` bare and `1 failed, 202 passed` slow; review at HEAD `2745954be` measured
  `2 failed, 5219 passed, 2 skipped` bare, the two failures being
  `tests/test_readiness_absence_invariant.py` live-corpus picks of an UNRELATED pending plan, and
  `237 passed` slow, because executed plan `ypnk56` has since cleared `SubcommandDescriptionTests`).
  The property that matters: no node fails after that did not fail before, and
  `tests/test_cli.py::SubcommandDescriptionTests` and `tests/test_subparser_descriptions.py` still pass
  (this plan's `config get` string must keep satisfying the length contract and must not disturb
  `ypnk56`'s shipped strings).
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: The post-change failing-node set of each run is a subset of the pre-change set
    recorded at the same HEAD, the only new passing nodes are the tests E-03 adds, and both
    description-contract tests pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE DESCRIPTION IS AN INLINE KWARG, NOT A TABLE ENTRY. `config get` is registered by
  `config_sub.add_parser("get", ...)` in `cli._build_parser` with an inline `description=`. Driven: no
  `config get` key exists in `cli._DESCRIPTIONS`. Plan `ypnk56` OQ-01 was REVERSED by its review onto
  the inline route for a leaf, on the measurement that inline is the majority convention (183 inline
  against 94 table keys) and is local to the `add_parser` block. This plan follows that settled route.
- ONE PARSER OBJECT SERVES BOTH `config` AND `conf`. Driven: `config get` and `conf get` both report
  `desc_len=335`, and `ypnk56` F-2 established the alias shares the parser object. So ONE edit fixes
  both spellings and no second string is needed; a table key for either would additionally override
  the inline edit.
- THE DEFAULT SUITE DOES NOT SEE `SubcommandDescriptionTests`. `tests/test_cli.py` is module-marked
  `pytestmark = pytest.mark.slow` and the configured `addopts` deselects `slow`. It FAILED under
  `-m slow` at authoring and PASSES at review HEAD `2745954be` (executed plan `ypnk56` fixed its eight
  gaps and added the default-visible `tests/test_subparser_descriptions.py`, which covers `config
  unset` and the `upgrade-test` leaves but NOT `config get`). Any guard this plan adds must therefore
  live in a default-visible test (E-03), and the slow set must be compared separately (V-06).
- TESTS ASSERT OUTCOMES, NOT SOURCE STRUCTURE (AGENTS.md, GUIDING_PRINCIPLES P16). The E-03 guard
  drives `cli.main` and reads an argparse object attribute; it must not read production source with
  `inspect`, `ast`, regex, or substring search.
- `tests/test_config.py` is stdlib `unittest` only, driving the CLI through `cli.main(...)` with
  `redirect_stdout` and a throwaway `XDG_CONFIG_HOME` set in `setUp`
  (`tests.test_config.ConfigCliCommandTests`). E-03 follows that shape.

## Findings

| Id | Severity | Where | What | Evidence |
|---|---|---|---|---|
| F-01 | MEDIUM | `cli._build_parser`, the `config get` inline `description=` | THE SHIPPED HELP STATES SOMETHING FALSE. It reads "Exits nonzero when the variable is not set, so a caller can distinguish 'unset' from 'set to an empty value'." Driven, NO recognized variable exits nonzero. This is the defect `uip0z6` records. | driven in-process, throwaway `XDG_CONFIG_HOME`: `defaults.migrate_layout` -> `exit=0 stdout='\n'`; `color_depth` -> `exit=0 stdout='\n'`; `aw_home` -> `exit=0 stdout='\n'`; `defaults.backup` -> `exit=0 stdout='true\n'`; `repos.search` -> `exit=0 stdout='[]\n'`; `no.such.key` -> `exit=2` "Unknown config key 'no.such.key'. Valid keys: aw_home, color_depth, config_version, defaults, ..." |
| F-02 | LOW | `cli._run_config_get` | EXIT 0 IS THE CORRECT BEHAVIOR, so the fix belongs in the TEXT and not the code. The handler ends `elif val is None: print("")` then `return 0`, and the repository's own test pins it: `tests/test_config.py::InstallPolicyDefaultsConfigTests::test_clearing_and_unset_removes_keys` asserts `cli.main(["config","get","defaults.migrate_layout"]) == 0` with empty output under the comment "Verify config get outputs empty (unset)". Changing the exit code would break a shipped, tested contract. | read `cli._run_config_get` (every recognized path reaches `return 0`; the only `return 2` paths are a missing varname and a `config.ConfigError`); read the asserting test |
| F-03 | MEDIUM | `config.normalize`, `config.get_config_value` | THE PROMISED DISTINCTION IS UNREPRESENTABLE, NOT MERELY UNIMPLEMENTED. This goes beyond the item and CONSTRAINS the fix: no exit code could ever expose "set to an empty value" because that state cannot be stored. Driven, `aw config set aw_home ""` reports `aw_home = None` and writes NO `aw_home` key, and hand-writing `"aw_home": ""` into the config file is DROPPED by `normalize` on load, after which `get_config_value` returns `None` exactly as for unset. Same for `defaults.leftovers` and `color_depth`. So the replacement must not offer a weaker version of the same distinction. | driven: `config set aw_home ''` -> `OK aw_home = None`, resulting file contains no `aw_home`; hand-written `{"aw_home": ""}` -> `normalize` yields `null` and `'aw_home' in normalized` is `False`; `get_config_value('aw_home')` -> `('aw_home', None)` |
| F-04 | LOW | `cli._run_config_get` `--json` and `--agent` branches | THE ITEM'S SUGGESTED WORDING NEEDS ONE CORRECTION: the unset/empty cases are indistinguishable under `--json` TOO, so the honest sentence cannot imply a structured-output escape hatch. Both an unset `aw_home` and a hand-written empty one return `{"aw_home": null}`. CORRECTED AT REVIEW (PR-002): `config show` is NOT a route either; driven, `config show aw_home` prints `aw_home              = -` both when unset and after hand-writing `""` into the file (only the `File:` line differs, `none yet` vs `present`, which reflects other keys and not `aw_home`). Reading the raw file is the only place a hand-written `""` is visible, and the toolkit ignores it, so the replacement must say an empty value reads the same as unset rather than point at any route. | driven: `config get aw_home --json` -> `exit=0 {"aw_home": null}` both when unset and after writing `""` into the file; review: `config show aw_home` -> identical `aw_home = -` row in both states |
| F-05 | LOW | `.aw/records/research/...-ffi66q-aw-cli-command-inventory.survey.md` | THE SAME FALSEHOOD IS MIRRORED IN A TRACKED RECORD that calls itself the current ground truth for a CLI naming review. Its `aw config get <var>` row reads "Exits nonzero when unset, so 'unset' differs from 'empty'." Fixing only the help leaves a record from which the next reader re-derives the wrong contract, which is why E-04 is in scope rather than deferred. | the survey row quoted above; its header states "This supersedes the 2026-08-26 inventory `sk94i0` as the current ground truth" |
| F-06 | INFO | the sibling `config *` descriptions | THE SIBLING AUDIT THE ITEM ASKS FOR CAME BACK CLEAN, so this plan's scope stays at one string. Each sibling claim was driven and holds: `config show` modifies nothing (no config file created by a `show` on a fresh dir); `config set` replaces a whole list (`["/a","/b"]` -> `["/c","/d"]`); `config add` is a no-op on a duplicate (`Already present`, exit 0, list unchanged); `config remove` REPORTS an absent item rather than silently succeeding (exit 1 `No entry matching`); `config is` answers through the exit code (`0` present, `1` absent). | driven in-process per claim, outputs as quoted |
| F-07 | INFO | `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description` | WHY NO TEST CAUGHT IT, and the limit worth recording: the contract measures LENGTH and DISTINCTNESS, never ACCURACY. `config get` is 335 characters against a 76-character help, so it passes comfortably while being false. A length contract cannot catch a false sentence, which is why E-03 adds a content guard. | read the test (it appends a problem only for an empty description, `len(desc) <= len(hlp)`, or `desc == hlp`); driven lengths `desc_len=335`, `help_len=76` |
| F-08 | INFO | the test baseline at the lane HEAD | SUPERSEDED AT REVIEW (PR-001): `ypnk56` has since EXECUTED, so at review HEAD `2745954be` the slow set is `237 passed` (green) and the bare run is `2 failed, 5219 passed, 2 skipped`, the two failures being `tests/test_readiness_absence_invariant.py` live-corpus tests that pick an unrelated pending plan. E-06/V-06 therefore re-derive the baseline at the executing HEAD. AUTHORING TEXT RETAINED FOR HISTORY: THE SLOW-SET BASELINE IS ALREADY RED, and for a DIFFERENT defect, so the executor must compare failing-node SETS and not counts. `-m slow` reports `1 failed, 202 passed`, the single failure being `SubcommandDescriptionTests`, whose eight reported gaps are `config unset`/`conf unset` (too short) and six `upgrade-test` leaves (empty). `config get` is NOT among them, confirming F-07. Those eight are owned by APPROVED pending plan `ypnk56`, not by this plan. Note this DIFFERS from `ypnk56`'s cited `3 failed, 199 passed`, so that number is stale as a baseline. | `python3 -m pytest -m slow` -> `1 failed, 202 passed in 94.26s`; bare `python3 -m pytest` -> `3692 passed, 2 skipped, 3 warnings in 224.25s` |
| F-09 | MEDIUM | interaction with plan `ypnk56` (EXECUTED since authoring; PR-001) | UPDATED AT REVIEW: `ypnk56` is now in `executed/` with `- Status: executed`, so the live hazard is no longer a concurrent diff but REGRESSING its shipped strings and its shipped guard `tests/test_subparser_descriptions.py`; the fence below still holds, now enforced by that default-visible test. AUTHORING TEXT RETAINED: TWO PENDING PLANS EDIT THE SAME FUNCTION, AND THE FENCE IS DELIBERATE AND MUTUAL. `ypnk56` is `- Status: approved` with `- Scope-Paths: agent_workflows/cli.py, tests/test_subparser_descriptions.py, CHANGELOG.md`; its E-03 instructs "Do NOT touch the SIBLING `config get` description while you are in this block", its deferred section carries `- Carrier: uip0z6`, and its V-03/V-06 require confirming `config get` was left ALONE. So that plan will not do this work and this plan must not do its work: this plan edits ONLY the `config get` description and must leave `config unset` and the six `upgrade-test` leaves untouched. Each runs in its own isolated worktree with a merge-and-revalidate gate, so the shared file is not a run hazard; the real hazard is an executor "helpfully" fixing the neighbour and invalidating the other plan's diff-based validation. | `ypnk56` front matter and the quoted E-03, deferred `- Carrier: uip0z6`, and V-03 "NO change to the neighbouring `config get` description (F-10 is carried by `uip0z6`, not fixed here)" |

## Proposed changes (ordered, validatable)

1. Re-drive the defect and the unrepresentability of the empty value at the executing HEAD (E-01), so
   the sentence that replaces it is grounded in output rather than plausibility.
2. Rewrite the false clause in the `config get` inline `description=` to the measured contract, keeping
   the two accurate sentences and adding no exit-code promise (E-02).
3. Add a default-visible regression guard that drives the exit codes and rejects a re-introduced
   exit-code promise in the rendered description (E-03).
4. Correct the mirrored false row in the tracked CLI inventory survey `ffi66q` (E-04).
5. Record the user-visible help correction as one `- Fixed:` changelog line (E-05).
6. Prove the result against bare and slow-set baselines RE-DERIVED at the executing HEAD, comparing
   by failing-node SET, and show both description-contract tests still pass (E-06).

## Deferred / out of scope (with reason)

- The EIGHT description gaps that made `SubcommandDescriptionTests` fail (`config unset`, `conf unset`,
  and six `upgrade-test` leaves).
  - Carrier: `ypnk56` (EXECUTED since authoring; the gaps are fixed at review HEAD `2745954be`)
  - Carrier-Declined: A DIFFERENT DEFECT WITH A DIFFERENT SHAPE, owned and now delivered by `ypnk56`.
    Those strings were too SHORT or ABSENT; this one is long enough and WRONG. This plan must not
    touch those strings, and must leave `SubcommandDescriptionTests` and
    `tests/test_subparser_descriptions.py` passing.
- Changing `config get` to actually exit nonzero for an unset variable.
  - Carrier: none (declined on the merits, not handed off)
  - Carrier-Declined: It would break a SHIPPED, TESTED contract (F-02) and, per F-03, still could not
    deliver the distinction the false sentence promises, because the empty-value state is not
    storable. The item reaches the same conclusion: "the help text is what is wrong."
- Making "set to an empty value" representable so the original distinction could exist.
  - Carrier: none (no item filed; not a defect)
  - Carrier-Declined: That is a FEATURE request about the config data model (F-03), far outside a
    help-text correction, and nothing observed suggests a user wants it. Documenting the real
    behavior is the fix; if someone later wants the distinction, it needs its own item.
- The `aw config --agent` `ImportError` in neighbouring code.
  - Carrier: `dtq6jr`
  - Carrier-Declined: Pre-existing and unrelated to the description; `ypnk56` already fences it to the
    same carrier.
- Strengthening `SubcommandDescriptionTests` to check ACCURACY generally rather than length (F-07).
  - Carrier: none (no item filed; would need a design)
  - Carrier-Declined: There is no general mechanical test for "this sentence is true", so this would
    be research rather than a fix. E-03 instead guards the ONE falsehood known to have shipped.

## Scope check

- Over-scope: none. Each of the four declared paths is touched by exactly one E-item that writes a
  file: `agent_workflows/cli.py` (E-02), `tests/test_config.py` (E-03), the `ffi66q` survey (E-04), and
  `CHANGELOG.md` (E-05). E-01 is measurement only and writes nothing. The survey edit is the one that
  could look opportunistic, so its justification is explicit: F-05 shows the same falsehood mirrored in
  a record that declares itself current ground truth, so leaving it lets the next reader re-derive the
  defect this plan is fixing. It is a ONE-ROW factual correction, not a re-survey.
- Scope-Paths justification: `agent_workflows/cli.py` holds the single `description=` correction (E-02);
  `tests/test_config.py` holds the new default-visible guard (E-03, home chosen in OQ-02);
  `.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md` holds the mirrored
  false row (E-04); `CHANGELOG.md` holds the one `- Fixed:` line (E-05).
- Under-scope: This plan does NOT touch the eight description gaps `ypnk56` fixed (F-08, F-09); it
  must merely keep `SubcommandDescriptionTests` and `tests/test_subparser_descriptions.py` passing. It also does not change any exit code,
  handler, flag, or `help=` string, so no command's BEHAVIOR changes; the only user-visible difference
  is what `--help` prints for `aw config get` and `aw conf get`.

## Required tests / validation

Driven, not reasoned. Every item below requires PASTED actual output.

- The new E-03 guard, shown RED on the unfixed description and GREEN after the fix.
- `tests/test_config.py` in full, proving the existing `config get` exit-0 contract
  (`InstallPolicyDefaultsConfigTests::test_clearing_and_unset_removes_keys`) still passes unchanged.
- The rendered `--help` for BOTH `aw config get` and `aw conf get`, ANSI-stripped and
  whitespace-normalized (argparse WRAPS a description, so an unnormalized comparison is unreliable;
  `ypnk56` PR-403 measured exactly this).
- The bare default suite and the `-m slow` set, each compared by FAILING-NODE SET against a baseline
  RE-DERIVED on the unmodified tree at the executing HEAD (E-06); authored counts are context only.

## Spec / documentation sync

No `.spec.md` file is amended, and none is in `- Scope-Paths:`. This plan corrects a false factual
claim in help text to match behavior the code already has and a shipped test already pins (F-02); it
changes no contract, so there is no spec to keep in step. The documentation sync it DOES owe is
non-spec and is carried as real work rather than a note: `CHANGELOG.md` (E-05) for the user-visible
help change, and the tracked CLI inventory survey `ffi66q` (E-04), which mirrors the same falsehood
and would otherwise keep propagating it (F-05).

## Open questions

### OQ-01: Should the replacement sentence mention the unset/empty distinction at all, or simply drop the claim?

- Blocking: no
- Status: resolved
- Owner: plan author (revised by reviewer; D-1 in the review record)
- Resolution or deferral rationale: REVISED AT REVIEW (PR-002): option (c) as authored named
  `config show` as a route, and review DROVE `config show aw_home` to print the identical
  `aw_home = -` row whether unset or hand-written `""`, so (c) would itself have shipped a second
  false claim, the exact failure this item exists to stop. The chosen wording is now (c'): state the
  real exit contract and say an empty value is not stored and so reads the same as unset, naming NO
  route. AUTHORING RATIONALE RETAINED BELOW, its `config show` clause superseded: RESOLVED FROM DRIVEN
  EVIDENCE; it is MENTIONED, with the honest route. Three options were considered. (a) Delete the clause silently: smallest diff, but a reader
  who previously relied on the promise is left with no answer to "how DO I tell unset from empty?",
  and the question is natural enough that the original author wrote a sentence about it. (b) Promise
  the distinction through some other channel: REFUTED by F-04, since `--json` returns `null` for both
  cases, so this would ship a second false claim. (c) State the real contract and name the only
  routes that exist: chosen. F-03 shows the distinction is unrepresentable (an empty string is dropped
  by `normalize`), so the truthful statement is that a recognized variable always exits 0 and that
  `config show` or the config file is where to look; per the item, "A caller needing that distinction
  has to read `config show` or the config file." This also explains WHY no exit code will ever provide
  it, which is what stops the same plausible sentence being written again.

### OQ-02: Where should the regression guard live, given the existing contract test is marked `slow`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED BY MEASUREMENT; it goes in `tests/test_config.py`. The
  obvious home looks like `tests/test_cli.py::SubcommandDescriptionTests`, which already walks every
  subparser description, but driving the suite showed that class is marked `slow` and the configured
  `addopts` deselects `slow`: at authoring a bare run passed while `-m slow` reported the failure. A guard against a false help string that is invisible to the default suite would not have
  caught this defect and will not catch its recurrence, so it must be default-visible.
  `tests/test_config.py` is also where the `config get` exit-0 contract is already pinned, which keeps
  the behavior and its documentation asserted side by side. `tests/test_subparser_descriptions.py` was
  rejected as a home because it is `ypnk56`'s shipped guard (that plan has since executed) and is
  outside this plan's Scope-Paths (F-09).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the actual per-key table from the re-drive at the executing HEAD, showing
    exit code and stdout for all six keys, and state explicitly whether it MATCHES F-01 or differs.
    Paste the `normalize` probe showing an empty `aw_home` dropped (key absent, value `None`). Paste
    the measured `config get` description length and `help=` length. If any measurement differs from
    F-01 or F-03, say so and STOP to reconsider the replacement wording before editing it: the whole
    point of this item is that the sentence must follow the measurement.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/cli.py` showing ONLY the `config get`
    `description=` changed, with the false clause gone, no `help=` string touched, no
    `_DESCRIPTIONS` key added for `config get` or `conf get`, and NO change to the neighbouring
    `config unset` description or any `upgrade-test` parser (F-09: `ypnk56` owns those and requires
    them untouched by this plan). Paste the ANSI-stripped, WHITESPACE-NORMALIZED `--help` output for
    BOTH `aw config get` and `aw conf get`, showing identical prose from the one shared string. Quote
    the new sentence and, for EACH factual claim in it, name the V-01 measurement that grounds it;
    confirm in writing that it promises no exit code the command does not return and no route to the
    unset/empty distinction (in particular, it must NOT name `config show` or `--json` as one: PR-002). State the new description length and confirm it exceeds 76.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the new test passing via `python3 -m pytest tests/test_config.py -o
    addopts="" -q`, and paste the test body showing BOTH limbs of E-03 (2): the negative
    falsehood-token assertion and the positive authored exit-0 content anchor. Prove it is a REAL guard by pasting it FAILING against the unfixed description:
    temporarily restore the old clause, run the test, paste the failure, then revert and paste
    `git diff --stat agent_workflows/cli.py` proving the probe is gone and the fix intact. Paste the
    test body and confirm it uses no `inspect`, `ast`, regex over source, or substring search of a
    source FILE (reading the parser object's `description` attribute is permitted and is the point),
    per the AGENTS.md outcomes-not-structure rule. Confirm the test is NOT marked `slow` by showing it
    selected in a bare run.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `git diff` of the `ffi66q` survey file showing EXACTLY the one
    `aw config get <var>` row changed, with no frontmatter, `status:`, filename, or other row
    modified. Quote the new row text and confirm every claim in it matches V-01's measurements. Paste
    a repository-wide search for the false phrase ("Exits nonzero when" near config get) and show the
    only remaining hits are historical records that MUST NOT be rewritten (the backlog item itself,
    the executed `ypnk56` plan, its review record, and this plan), naming why each is left alone.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste `git diff CHANGELOG.md` showing exactly ONE added `- Fixed:` line under
    `## 2.0.0 (pending)`. Paste a grep over that line for em and en dashes returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the PRE-CHANGE bare and `-m slow` summary lines and their failing-node
    lists, recorded on the unmodified tree at the executing HEAD, and the POST-CHANGE ones. Show the
    post-change failing-node set of each run is a subset of the pre-change set (name any node that
    differs and explain it), and that the new E-03 tests appear as passing. Paste
    `python3 -m pytest -o addopts="" tests/test_subparser_descriptions.py
    "tests/test_cli.py::SubcommandDescriptionTests"` passing, proving `config get` still meets the
    length contract and `ypnk56`'s shipped strings were not disturbed. Run the suite BARE per AGENTS.md: no `-n0`, no
    extra `-q`, no `-p no:randomly`. State in writing that neither `tests/test_cli.py` nor
    `tests/test_subparser_descriptions.py` was modified.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. One `description=` string in
`agent_workflows/cli.py`, one new test in `tests/test_config.py`, one corrected table row in a tracked
research survey, and one `CHANGELOG.md` line. NO handler, flag, exit code, or `help=` string changes,
so no command's BEHAVIOR changes; the only user-visible difference is what `--help` prints for
`aw config get` and `aw conf get`. The judgement worth scrutinising is the REPLACEMENT WORDING, and
the single most important thing to check is that it was DRIVEN: this defect exists because a plausible
sentence was never run, and the plan therefore requires the executor to re-measure first (E-01, V-01)
and to ground each clause in a specific measurement (V-02). The one finding that goes beyond the filed
item is F-03, that an empty value is UNREPRESENTABLE because `config.normalize` drops it, which is why
the fix must not offer a weaker version of the promised distinction. Fully reversible by editing one
string. Two things this plan deliberately does NOT do: it does not change the exit code (that would
break a shipped, tested contract and still could not deliver the promised distinction), and it does not
touch the eight description strings executed plan `ypnk56` authored.

Execution contract: commit only the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`,
never `git add -A`, never `git add .`, never `git commit -a`, never `--no-verify`, and never
`git push`. SCOPE FENCE (a DECLARATION for the runner to reconcile against, not an instruction to
stop). Modify exactly `agent_workflows/cli.py`, `tests/test_config.py`, `CHANGELOG.md`, and the one
`ffi66q` survey row. Specifically DO NOT: edit the neighbouring `config unset` description or any
`upgrade-test` parser, which executed plan `ypnk56` authored (F-09); edit
`tests/test_subparser_descriptions.py`, `ypnk56`'s shipped guard; edit `tests/test_cli.py`, whose
`SubcommandDescriptionTests` must keep passing unmodified; add a `_DESCRIPTIONS` table key for `config get` or `conf get`,
since the route is inline and a key would override the prose just written; change
`cli._run_config_get`, any exit code, or any `help=` string; fix the `aw config --agent` `ImportError`
(carrier `dtq6jr`); rewrite the backlog item, the `ypnk56` plan, or its review record, which are
HISTORICAL records of the defect and must keep quoting the false sentence; or write any test that reads
production source with `inspect`, `ast`, regex, or substring search. An out-of-scope edit that proves
NECESSARY is to be MADE and then JUSTIFIED with `aw ipd finalize --scope-reason`, and a declared path
you end up not modifying needs a `--scope-ack`; neither is a reason to stop. Paste ACTUAL runner output
for every validation item; do not claim a test run that did not happen. LIFECYCLE TRANSITION: after
every `E-*` is performed and every `V-*` is verified with pasted evidence, run
`aw ipd lint --phase pre-transition` and require conforming. The terminal transition is then owed
UNCONDITIONALLY but its OWNER is CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER performs it
and the executor must NOT (a worker-role process is refused with `AW-LIFECYCLE-ROLE-001`); executed by
hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`.
Never hand-roll the move with `git mv` and never hand-edit `- Status: executed`. Backlog `uip0z6` is
ALREADY `graduated` (it lives in `.aw/records/backlog/graduated/`); do not set it `done` from this plan:
closing it is a separate act via the HANDOFF route once this carrier is executed. The
`- Blocks-Release: next` gate is inherited from that item and must travel with this plan.
