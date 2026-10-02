# IPD: Drop the retracted non-TTY auto-switch clause from 19 cli.py help and docstring sites

- Date: 2026-10-02
- Kind: child
- Concern: `aw --help` promises a machine-readable auto-switch on piped stdout that was retracted on 2026-09-10 and never shipped, so 18 help surfaces describe behavior the CLI refutes when run exactly as described.
- Scope: Correct the false clause at all 19 source sites in `agent_workflows/cli.py` (16 epilog `OUTPUT & EXITS` lines, 2 parser `description=` strings, 1 internal docstring), and add one behavior test that fails if any help surface re-asserts the retracted auto-switch.
- Scope-Paths: agent_workflows/cli.py, tests/test_help_nontty_claim.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: qdd6ey
- Blocks-Release: next
- Set: qdd6ey
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 79piey

## Workflow history

- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `qdd6ey` (graduation). Measured the defect at lane HEAD `37ab8a287`, widened the site count from the item's 16 to 19 source sites / 18 help surfaces after finding two sibling `description=` strings and one docstring carrying the same false claim in different wording, and confirmed no test or golden pins the current bytes.

## Goal

Make every `aw` help surface describe the output-mode contract the CLI actually implements: `--agent` is the only route to `aw.agent/v1` JSONL and `--json` the only route to structured JSON, while piping or redirecting emits human-readable text. Today 18 help surfaces promise an automatic non-TTY switch that `docs/cli-output-contract.md` Section 9 records as RETRACTED and that no release ever implemented, so a user or agent who reads `--help` and pipes the command gets prose where JSONL was promised.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: correct the false claim at its source

- [ ] E-01 In `agent_workflows/cli.py`, replace the retracted clause in all 16 `OUTPUT & EXITS` epilog lines whose content string begins `  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL`, so the resulting line names `--agent` as the only JSONL route and preserves each line's existing `--json` tail verbatim. The 16 split into four shapes, measured: 12 carry the bare form ending `JSONL.\n`; 2 carry `; --json for formatted JSON.\n` (the `project` and `check` epilogs); 1 carries `; --json for structured JSON.\n` (the `storage` epilog); and 1 is the `adopt` site, bare but ending `JSONL.` with NO trailing `\n` escape because it sits inside a triple-quoted block. Use the already-corrected `renderers.py` hint (`"Agent output: --agent"`, fixed under closed item `zdjhug` / executed plan `zosxj4`) as the wording precedent, and do NOT add any new claim about piped or non-TTY behavior. One site (`adopt`) is inside a triple-quoted epilog rather than a concatenated string literal and carries no leading `"`, so a naive string-literal-only edit misses it.
  - Depends on: none
  - Expected outcome: `rg -c "non-TTY piped" agent_workflows/cli.py` reports no matches (down from 16), and `rg -c "Agent mode:" agent_workflows/cli.py` still reports 16, proving the lines were corrected rather than deleted.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/cli.py`, correct the same false claim in the two sibling parser `description=` strings that carry it in DIFFERENT wording and so are invisible to a search for the E-01 phrase: the `oc profile list` description beginning `"List your profiles. Human table on a TTY, aw.agent/v1 JSONL when piped or with "` and the `agy profile list` description beginning `"List your Antigravity profiles. Human table on a TTY, aw.agent/v1 JSONL when piped or "`. Each must stop attributing JSONL to piping while keeping its true `--agent`, `--json`, and `An empty list is a clean result, not an error.` content. Also correct the identical claim in the `cli._oc_profile_out` docstring, whose first body line reads `Human table/lines on a TTY, aw.agent/v1 JSONL when piped or `--agent`, structured JSON with`; it is internal rather than user-facing, but it is the docstring of the function that implements this very contract, and leaving it wrong reintroduces the error the next time someone copies it.
  - Depends on: E-01
  - Expected outcome: `rg -c "JSONL when piped" agent_workflows/cli.py` reports no matches (down from 3), and both profile-list help surfaces still document `--agent` and `--json`.
  - Execution state: pending

### Task group 2: pin the corrected contract against regression

- [ ] E-03 Add `tests/test_help_nontty_claim.py` asserting, across the WHOLE built parser tree, that no rendered help surface claims the retracted auto-switch. Build the tree with `cli._build_parser()`, walk every `argparse._SubParsersAction` choice recursively (deduplicating aliases by `id(parser)`, since `list`/`ls` are the same parser object), call `format_help()` on each, and NORMALIZE WHITESPACE with `re.sub(r"\s+", " ", text)` before matching. The normalization is load-bearing and not a stylistic choice: argparse re-wraps `description=` text to terminal width, so an un-normalized search for `aw.agent/v1 JSONL when piped` MISSES the `agy profile list` surface entirely (measured: 17 surfaces found un-normalized versus 18 normalized). Assert on the rendered help text, never by reading `cli.py` source, per the no-code-pinning rule in AGENTS.md.
  - Depends on: E-02
  - Expected outcome: the new test file exists and passes, failing with a message naming the offending command path if any surface re-asserts the claim.
  - Execution state: pending

- [ ] E-04 Record the fix in `CHANGELOG.md` under the existing `## 2.0.0 (pending)` heading as a `- Fixed:` bullet, following the surrounding bullet style, stating that `aw --help` no longer promises `aw.agent/v1` JSONL on piped or redirected stdout and that `--agent` is the explicit and only route. Write no em or en dashes (AGENTS.md applies this to user-facing prose, and `CHANGELOG.md` is user-facing).
  - Depends on: E-03
  - Expected outcome: `CHANGELOG.md` carries one new `- Fixed:` bullet describing the corrected help contract.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE AUTHORITATIVE RULING. `docs/cli-output-contract.md` Section 9, headed `Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19`, records maintainer ruling ttyflags `yaxr4i` OQ-01 (2026-09-10) and states: `Piping or redirecting `aw` emits HUMAN-READABLE TEXT. `--agent` is the explicit and only way to obtain `aw.agent/v1` JSONL, and `--json` the only way to obtain the full structured JSON. Non-TTY stdout affects COLOR only`. It further records that `select_output` `has never consulted `stdout.isatty()` for mode selection; the only TTY consultation is the color one`, so this is a documentation defect and NOT a behavior regression.
- THE RETRACTION IS NARROW, which bounds the fix. The same section states it `does not rule that non-TTY detection is unwanted, and it does not foreclose a future proposal`. So the correct edit DELETES a false promise; it must not editorialize that piped machine output is undesirable.
- NO CODE-PINNING TESTS. AGENTS.md forbids a test that reads production source with `inspect`, `ast`, regex, or substring search, which is why E-03 asserts on `format_help()` output (the user-visible surface) rather than on `cli.py` bytes. Searching source with `rg` is fine as EXECUTION evidence (E-01, E-02) but must not become the test.
- AN ALREADY-CORRECTED PRECEDENT EXISTS. `renderers.py` emits `lines.append("Agent output: --agent")`, and `tests/test_human_renderer_agent_hint.py` asserts `lines[-1] == "Agent output: --agent"` plus `"automatic when piped" not in rendered` at three call sites. That is backlog item `zdjhug`, which the item's own history calls graduated but which is now `done` with its plan `zosxj4` `executed`; it is a DIFFERENT string in a different file reached by a rendered result rather than by `--help`. It supplies the wording precedent and the test shape, and it is already fixed, so it is not re-done here.
- ALIAS DEDUPLICATION IS REQUIRED when walking the parser tree. `oc profile list` is registered with `aliases=["ls"]`, so `_SubParsersAction.choices` maps two names to ONE parser object; a walker that does not deduplicate by `id(parser)` double-counts every aliased leaf.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE CLAIM IS REFUTED BY THE EXACT INVOCATION IT DESCRIBES. The epilog promises JSONL on piped stdout; redirecting the command emits prose. | Measured at lane HEAD `37ab8a287`: `python3 -m agent_workflows config show > file` exits 0 and the file begins `agent-workflows configuration` / `  File:    ~/.config/agent-workflows/config.json (present)`; feeding its first line to `json.loads` raises `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`. The same redirect of `oc profile list` emits a `NAME RUNNER MODEL VARIANT AGENT` text table, and of `agy profile list` emits `✓ CLEAN  no runner profiles configured`. |
| F-02 | THE ITEM'S COUNT OF 16 IS A FLOOR, NOT THE TOTAL. There are 19 source sites across 3 wordings, so an executor who fixes only the item's quoted phrase leaves 3 sites lying. | `rg -c "non-TTY piped" agent_workflows/cli.py` = 16 (the item's phrase); `rg -c "JSONL when piped" agent_workflows/cli.py` = 3 (two `description=` strings plus the `cli._oc_profile_out` docstring). Total 19, all in `cli.py`; `rg -ln "Agent mode: --agent" --glob '!.aw/**' .` matches `agent_workflows/cli.py` only. |
| F-03 | THE USER-VISIBLE BLAST RADIUS IS 18 HELP SURFACES, spanning 16 commands plus 2 profile leaves. | Walking `cli._build_parser()` and rendering `format_help()` with whitespace normalized finds the claim on: `aw runs analyze`, `aw runs query`, `aw runs export`, `aw runs submit`, `aw research`, `aw reviews`, `aw host`, `aw project`, `aw storage`, `aw config`, `aw check`, `aw oc profile list`, `aw agy profile list`, `aw backlog`, `aw releases`, `aw specs`, `aw prompts`, `aw adopt`. |
| F-04 | WHITESPACE NORMALIZATION IS LOAD-BEARING FOR DETECTION, so a naive regression test under-reports. | The same walk WITHOUT `re.sub(r"\s+", " ", ...)` reports 17 surfaces and omits `aw agy profile list`, because argparse re-wraps its `description=` mid-phrase, rendering `piped or with --agent, structured JSON with --json. An empty list is a clean` across a line break. |
| F-05 | NOTHING PINS THE CURRENT BYTES, so this is a text fix plus a new test, with no golden churn. The item asked for this to be checked before assuming text-only. | `ls tests/fixtures/conformance_goldens` holds 12 files, all `check_findings` / `error_cannot_run` / `mutation_preview` / `read_clean` in `.agent`/`.human`/`.json` form, none a help snapshot; `rg -rn "non-TTY piped" tests/ docs/` matches nothing outside `.aw/` records. The two test files matching `Agent mode` use it only in a comment (`tests/test_status_set.py`: `# Agent mode without --yes refuses`) and in fixture body text (`tests/test_artifact_adopt.py`: `"# Agent mode\n\nBody.\n"`). `tests/test_command_surface_declarations.py` asserts only `find_undeclared_leaves(parser) == set()` and reads no help text. |
| F-06 | THE REPLACEMENT WORDING WILL BE TRUE AT EVERY SITE, so the fix cannot trade one false claim for another. | Each of the 18 surfaces genuinely accepts both flags: walking the parser tree and inspecting `option_strings` per leaf reports `--agent=True --json=True` for all 18, so naming `--agent` for JSONL and `--json` for structured JSON is accurate everywhere, including the two `storage`/`project` variants whose tails differ. |
| F-07 | THE DOCS ARE ALREADY CORRECT, so only the CLI drifted and no doc rewrite is needed. | `rg -ln "non-TTY piped|JSONL when piped" docs/ README.md` matches nothing. `docs/cli-output-contract.md` Section 1.1 already states the piped case `DOES NOT AFFECT THE MODE`, and Section 9 carries the retraction with its reasoning. |

## Proposed changes (ordered, validatable)

1. E-01 corrects the 16 `Agent mode:` epilog lines in `agent_workflows/cli.py`, preserving each one's existing `--json` tail (13 bare, of which 12 end `JSONL.\n` and 1 is the `adopt` site with no `\n` escape; 2 `formatted JSON`; 1 `structured JSON`) and reaching the triple-quoted `adopt` epilog as well as the 15 concatenated-string-literal sites.
2. E-02 corrects the 2 profile-list `description=` strings and the `cli._oc_profile_out` docstring, which carry the same falsehood in wording that E-01's search does not match.
3. E-03 adds `tests/test_help_nontty_claim.py`, a whitespace-normalized walk of the whole parser tree that fails if any rendered help surface re-asserts the auto-switch.
4. E-04 records the user-visible correction in `CHANGELOG.md`.

## Deferred / out of scope (with reason)

- THE RENDERER HINT AND ITS GOLDENS (`agent_workflows/renderers.py`, `tests/fixtures/conformance_goldens`). Already fixed and closed under backlog item `zdjhug`, executed as plan `zosxj4`: `renderers.py` now emits `"Agent output: --agent"` and `tests/test_human_renderer_agent_hint.py` guards it at three call sites. Nothing is outstanding, and this plan must not re-open it.
  - Carrier-Evidence: .aw/records/plans/executed/20260929-zdjhug-01-zosxj4-stop-the-cli-printing-the-retracted-non-tty-auto-switch-prom.ipd.md
- IMPLEMENTING A NON-TTY AUTO-SWITCH. Explicitly forbidden as a reading of this plan. The ruling retracted the promise BECAUSE it never shipped and an unknown number of consumers depend on the prose that actually ships; making the epilog true by changing behavior would break them. This plan changes text only, and the executor must NOT write a test asserting the piped case emits JSONL.
  - Carrier-Declined: Not a defect to carry. Maintainer ruling ttyflags `yaxr4i` OQ-01 (2026-09-10), recorded in `docs/cli-output-contract.md` Section 9, retracted this promise deliberately; building it would be new work against a standing decision, not an outstanding obligation. Section 9 keeps the door open to a future proposal, which would need its own decision and migration story.
- A `--tty` FLAG. `docs/cli-output-contract.md` Section 9.1 records that no such flag exists deliberately, because a single undifferentiated boolean would conflate the presentation axis (`stdout`, color) with the interactivity axis (`stdin`, prompting) and could silently re-enable prompting in an unattended runner.
  - Carrier-Declined: Not a defect to carry. Section 9.1 records the absence as a DESIGN CONSTRAINT with its analysis preserved for a successor, and states the two requirements it raised are `both now fulfilled` by the shipped flag pair, so nothing is outstanding.
- THE THREE PRE-EXISTING SUITE FAILURES named in the validation section. They fail at lane HEAD before any edit here and belong to spec attestation, run-finding reachability, and selector containment; none reads CLI help text. Fixing them is separate work, and V-04 exists so they are not silently absorbed into this plan's evidence. Each already has an open backlog carrier, and open item `wc5c5e` tracks the load-sensitivity question across all three.
  - Carrier: 6bolin, 8jeh4x, bxnhdj, wc5c5e
- `aw next`'s `piped list stays clean` help text. It is a TRUE statement about stderr routing on an error path, not an output-mode claim, so it is correct as written and is left alone.
  - Carrier-Declined: Nothing to carry: the text is accurate. It describes an error message going to stderr so a piped stdout list stays clean, which is routing, and it makes no claim about output MODE, so the retraction does not touch it.

## Scope check

- Over-scope: none. `CHANGELOG.md` is included only for the one-line user-visible record E-04 writes; no behavior, no renderer, and no golden is touched.
- Under-scope: the `cli._oc_profile_out` docstring (E-02) is internal rather than user-facing, so it is strictly outside the backlog item's user-visible defect. It is included deliberately because it is the docstring of the function implementing this contract, and leaving it wrong is how the claim propagates back into user-facing text. The three pre-existing suite failures are left failing, with V-04 pinning them so the gap is explicit rather than hidden.

## Required tests / validation

- `python3 -m pytest` run BARE (per AGENTS.md: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; do not add `-n0`, a second `-q`, or `-p no:randomly`). MEASURED BASELINE at lane HEAD `37ab8a287`, before any edit: `3 failed, 4624 passed, 2 skipped, 3 warnings in 263.22s (0:04:23)`, the failures being `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, and `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`. The executor must compare against this baseline and not report those three as caused by this plan.
- `python3 -m pytest tests/test_help_nontty_claim.py` for the new gate, plus `tests/test_human_renderer_agent_hint.py`, `tests/test_command_surface_declarations.py`, and `tests/test_exit_contract_conformance.py` as the neighbouring help/surface contracts most likely to notice a parser-text edit.
- A live redirect of a corrected command, re-running the F-01 measurement, to confirm the help text and the shipped behavior finally agree.

## Spec / documentation sync

- NO SPEC AMENDMENT, and no `.spec.md` file is in `- Scope-Paths:`. This plan makes the CLI agree with an ALREADY-CORRECT normative document: `docs/cli-output-contract.md` Section 9 records the retraction and Section 1.1 states the piped case affects color only. Amending a spec here would be the wrong direction of fit, since the contract is right and the help text drifted from it.
- `CHANGELOG.md` gets one `- Fixed:` bullet (E-04) because the corrected text is user-visible.
- `docs/cli-output-contract.md` needs NO edit: F-07 measured that it carries none of the three false wordings.

## Open questions

### OQ-01: Should the corrected epilog line say anything POSITIVE about what piping does emit?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO; delete the false clause without adding a replacement claim about piping. Three reasons from repository evidence. First, the already-shipped precedent for exactly this correction is subtractive: `renderers.py` emits the bare `"Agent output: --agent"`, and `tests/test_human_renderer_agent_hint.py` asserts that line EXACTLY while also asserting `"automatic when piped" not in rendered`, so the fixed sibling says nothing positive about piping. Second, `docs/cli-output-contract.md` Section 9 notes the retraction `does not foreclose a future proposal to make piped output machine-readable`, so stamping `piping emits human-readable text` into 18 help surfaces would re-pin, in 18 places, a behavior the ruling deliberately left open to revisit. Third, the plain `--agent` form is shorter, which matters in an epilog. A reviewer who prefers the positive form can say so; the resolution is a wording default, not a claim no alternative is defensible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual output of `rg -c "non-TTY piped" agent_workflows/cli.py` (must report no match; `rg` exits 1) AND of `rg -c "Agent mode:" agent_workflows/cli.py` (must still report `16`, proving correction rather than deletion). Then paste the three distinct corrected lines (a bare one, the `storage` `structured JSON` one, and the `project` or `check` `formatted JSON` one) showing each `--json` tail preserved, plus the corrected `adopt` triple-quoted epilog line to prove the non-string-literal site was reached.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the actual output of `rg -c "JSONL when piped" agent_workflows/cli.py` (must report no match) and the three corrected passages (the `oc profile list` description, the `agy profile list` description, and the `cli._oc_profile_out` docstring line), each still naming `--agent` and `--json` and the two descriptions still ending `An empty list is a clean result, not an error.`
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the actual `python3 -m pytest tests/test_help_nontty_claim.py` output showing the passed count. Then paste a NEGATIVE CONTROL proving the gate can fail: temporarily reintroduce the clause at ONE site, paste the resulting failure output showing the test names the offending command path, revert, and paste a clean re-run. Separately paste the count from a whitespace-normalized walk of `cli._build_parser()` showing `0` surfaces carry the claim (was 18), and state explicitly that the test asserts on `format_help()` output and reads no production source, per the no-code-pinning rule.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new `CHANGELOG.md` bullet and confirm it contains no em or en dash. Paste the full `python3 -m pytest` summary line and compare it against the recorded baseline `3 failed, 4624 passed, 2 skipped`: passed must rise by the number of tests E-03 added, and the failed set must be EXACTLY the same three named pre-existing failures (spec attestation, run-finding reachability, selector containment), with any change in that set reported rather than absorbed. Also paste a live redirect of one corrected command (for example `python3 -m agent_workflows config show > /tmp/x` then the first line of `/tmp/x`) showing human prose, confirming the help text now matches shipped behavior.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; the executor must not self-approve. On approval, execute the E-items in order (E-01 through E-04 are sequentially dependent), then verify each `V-*` in a separate pass with the concrete evidence each one demands, pasting ACTUAL command output and never a claim of success that was not run.

Commit through the tooled path, `aw commit <plan> -- agent_workflows/cli.py tests/test_help_nontty_claim.py CHANGELOG.md`, never `git add -A` or a bare commit, and never push. Verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and `cli.py` is a high-traffic file; unstage anything you did not change with `git restore --staged <path>`.

Two execution-time prohibitions follow from the retraction. Do NOT make the epilog true by implementing a non-TTY auto-switch, and do NOT write any test asserting that a piped invocation emits JSONL: the promise was retracted precisely because it never shipped and consumers depend on the prose that does. Do not broaden the edit beyond the 19 sites to other `piped` mentions in `cli.py` that are true as written.

On a conforming `aw ipd lint --phase pre-transition` with every `V-*` at `pass`, move this plan to `.aw/records/plans/executed/` through the lifecycle tooling. Backlog item `qdd6ey` carries `- Blocks-Release: next`, which this plan inherits; the gate is satisfied by this plan reaching `executed`, so the item must not be closed `done` before then.
