# IPD: Mark the retracted non-TTY JSONL cutover as retracted in the user docs

- Date: 2026-09-26
- Kind: child
- Concern: SIX user-facing docs still promise that piped/non-TTY `aw` output switches automatically to `aw.agent/v1` JSONL ("HARD CUTOVER"). That policy was RETRACTED by maintainer ruling ttyflags `yaxr4i` OQ-01 (2026-09-10) and never shipped: `aw status | cat` and `aw check plans | cat` print human text today. A scraper author following these docs gets the wrong mental model of the output contract. The sixth doc is `docs/run-analytics.md` ("`--agent` is automatic when piped"), found in review; the CLI ITSELF prints the same false claim from `renderers.py` on every command, which is code plus four pinned goldens and is therefore carried by backlog `zdjhug` rather than fixed here.
- Scope: IN: `docs/cli-migration.md` (retitle, RETRACTED banner, reframe recipes as "`--agent` is the only way to get machine output", mark the rationale section and the 2.0.0 schedule row retracted rather than deleting them); `docs/cli-agent-protocol.md` "When you get machine output" section (drop the auto-switch claim and the false "This is the default when piped"); `README.md` "CLI output modes" paragraph; `docs/README.md` index line for the migration guide; `CHANGELOG.md` 2.0.0 (pending) entry that announces the cutover; `docs/run-analytics.md` "The agent surface" sentence (added in review, F-8). OUT: `docs/cli-output-contract.md` and `docs/cli-human-guide.md` (already correct, they are the reference wording); ANY code change, including the `renderers.py` hint line and its four conformance goldens (carried by backlog `zdjhug`); the three legacy byte-form claims, which are STALE IN THEIR OWN RIGHT but on a different axis than the auto-switch (measured in review: `render_agent_drift` still exists with three live callers, so "GONE" is false) and are carried by backlog `qczq5r` rather than silently reframed here.
- Scope-Paths: docs/cli-migration.md, docs/cli-agent-protocol.md, README.md, docs/README.md, CHANGELOG.md, docs/run-analytics.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: sm0vgn
- Blocks-Release: next
- Set: staledocs
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3rsdbj

## Workflow history
- 2026-09-27 executed (opencode manual-recovery model=its_direct/pt3-claude-opus-5.5-1m-us): Recovered stranded lane: work completed in run-20260927T051239Z-3346121; driver finalize refused only because another run held the finalize writer lock (backlog duac3v). Lane merged onto current main; no unretracted HARD CUTOVER claims remain in the 6 files; no dashes added; sanitize exit 0; full suite 2641 passed.
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-209 all FIXED (CLI prints the same false claim, carried to zdjhug; byte-form list would have been re-asserted falsely, carried to qczq5r; sixth doc run-analytics.md added; verification grep widened)
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog sm0vgn: Mark the retracted non-TTY JSONL cutover as retracted in five user docs.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every user-facing doc agree with the shipped behavior and with the normative contract (`docs/cli-output-contract.md` section "9. Automatic Non-TTY Migration Policy: RETRACTED"): piped output is human text, and `--agent` / `--json` are the only way to get machine output. The retracted promise is labelled RETRACTED with a pointer to the ruling, not silently deleted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

#### Task group 1: Confirm the behavior the docs must describe

- [x] E-01 Re-measure the shipped behavior before editing: run `aw status | cat | head -3` and `aw check plans | cat | head -3` and confirm both print human text (not a line starting `{"schema":"aw.agent/v1"`), and `aw status --agent | head -1` prints an `aw.agent/v1` record.
  - Depends on: none
  - Expected outcome: piped output is human text; `--agent` output is JSONL. If piped output IS JSONL, stop and report: the docs would then be correct and this plan's premise wrong.
  - Execution state: performed

### Task group 2: Rewrite the migration guide

- [x] E-02 In `docs/cli-migration.md`: retitle the H1 (for example `# CLI output migration guide (2.0.0 machine output)`), and directly under it add a RETRACTED banner stating that the automatic non-TTY switch to JSONL announced for 2.0.0 was retracted on 2026-09-10 (maintainer ruling, ttyflags `yaxr4i` OQ-01), that piped output stays human text, that `--agent` is the only way to get `aw.agent/v1` JSONL and `--json` the only way to get full structured JSON, and link `cli-output-contract.md` section 9.
  - Depends on: E-01
  - Expected outcome: the first screen of the guide states the true behavior; no sentence in the intro ("This is a HARD CUTOVER with NO compatibility window") asserts the retracted switch without being marked retracted.
  - Execution state: performed
- [x] E-03 In `docs/cli-migration.md`, rewrite "The break, stated loudly" so it no longer says non-terminal stdout emits JSONL "automatic and immediate" (that exact sentence is the file's most load-bearing false claim and, note, does NOT contain the phrase "hard cutover", so the authored E-08 grep, now E-09, would never have caught it). Reframe the recipes: recipe 1 ("I just want the human text back") says nothing changed for terminals or pipes; recipe 2 says piped text is still text but is not a stable contract, so switch to `--agent`; recipes 3-5 keep their `--agent` / `--json` commands. DO NOT assert the three legacy byte-form items are still true: measured in review, item 2's claim that the `render_agent_drift` TSV lines are "GONE and are now `aw.agent/v1`" is FALSE (`artifact_core.render_agent_drift` still exists with three live callers, and `aw index plans --check --agent` prints `INDEX.json<TAB>check.stale-index-stale<TAB>...` today). Rewriting them around `--agent` as if they were correct would replace one false claim with another. Leave the three items TEXTUALLY UNCHANGED apart from any auto-switch wording, and add one sentence saying their accuracy is under separate review with a pointer to backlog `qczq5r`. Correcting them is that item's job, not this plan's.
  - Depends on: E-02
  - Expected outcome: every recipe tells the reader to pass `--agent` or `--json` explicitly; none implies piping alone yields JSONL; the byte-form list is neither re-asserted nor silently reframed, and points at `qczq5r`.
  - Execution state: performed
- [x] E-04 In `docs/cli-migration.md`, mark the "Why a hard cutover" section RETRACTED (rename the heading, keep the original rationale as a quoted historical note, add one sentence on why it was retracted pointing at contract section 9); in "Rollback" drop "that is what hard cutover means"; in the "Compatibility schedule" table mark the 2.0.0 row's automatic switch as retracted 2026-09-10 and state the actual 2.0.0 state (piped output is human text; `--agent`/`--json` select machine output).
  - Depends on: E-03
  - Expected outcome: the rationale and schedule rows remain readable as history and are labelled retracted, not deleted.
  - Execution state: performed

### Task group 3: Fix the other five docs

- [x] E-05 In `docs/cli-agent-protocol.md` section "When you get machine output": replace the first paragraph with the true rule (machine format only when you pass `--agent`; piping or redirecting does not switch it; a one-line RETRACTED note pointing at contract section 9) and delete the false clause "This is the default when piped." from the `--agent` bullet.
  - Depends on: E-01
  - Expected outcome: the section no longer claims non-TTY stdout selects machine output.
  - Execution state: performed
- [x] E-06 In `README.md` "CLI output modes (human and agent)": replace "when stdout is a pipe, a file, or an agent, you get the `aw.agent/v1` JSONL machine format automatically. As of 2.0.0 this is a HARD CUTOVER: piped output is machine JSONL, not the old plain text." with wording matching `docs/cli-human-guide.md` "Output mode and audience" (human text everywhere by default, `--agent` for machine JSONL, non-TTY affects color only, the auto cutover was retracted 2026-09-10). In `docs/README.md` change the migration-guide index line from "the 2.0.0 non-TTY hard cutover and how to update scrapers" to a description of what the guide now is (moving scrapers to `--agent`, with the retracted cutover noted).
  - Depends on: E-01
  - Expected outcome: neither file asserts the retracted switch.
  - Execution state: performed
- [x] E-07 In `CHANGELOG.md` under "## 2.0.0 (pending)", edit the bullet beginning "Changed (BREAKING, LOUD): dual-audience CLI output with an automatic non-TTY HARD CUTOVER" so it no longer announces the auto-switch: state that the automatic non-TTY switch was retracted before release (2026-09-10, `yaxr4i` OQ-01), that piped output remains human text, and that machine output is obtained with `--agent`/`--json`. Keep the parts of the bullet that remain true (the `aw.agent/v1` format, the 0/1/2 exit classification, the doc links, the `Drift` supersession). The bullet ALSO repeats the three byte-form removals; leave that clause's wording alone for the reason given in E-03 (item 2 is independently false, carried by `qczq5r`) rather than restating it as fact. NOTE this bullet is also the single largest BREAKING announcement in the pending release, so after the edit re-read it whole once: the remaining sentences must still parse as one coherent entry and must not read as though a break is being announced that the release does not make.
  - Depends on: E-01
  - Expected outcome: the unreleased changelog entry does not promise behavior the release will not have, and reads coherently as a single entry.
  - Execution state: performed
- [x] E-08 In `docs/run-analytics.md` "The agent surface", correct the sentence "`--agent` is automatic when the output is piped" (found in review, F-8; it is the same false auto-switch promise in a sixth file the brief and the backlog item both missed). Replace it with the true rule in the `docs/cli-human-guide.md` wording: `--agent` must be passed explicitly, and piping affects color only. One sentence; no RETRACTED banner is needed in a feature doc that merely repeated the claim in passing.
  - Depends on: E-01
  - Expected outcome: no user-facing doc outside the retraction-history files asserts the auto-switch.
  - Execution state: performed

### Task group 4: Verify

- [x] E-09 Verify with a grep WIDE ENOUGH TO CATCH THE CLAIM IN EVERY WORDING IT ACTUALLY USES, and run the leak sanitizer. The authored three-phrase pattern was measured INSUFFICIENT in review: it misses `docs/cli-migration.md`'s "This is automatic and immediate" and `docs/cli-agent-protocol.md`'s "whenever stdout is not a terminal", which are the two most load-bearing sentences in the whole plan. Run instead, over the WHOLE repo rather than only the edited files, so a seventh instance cannot hide: `git grep -n -iE "hard cutover|default when piped|machine format automatically|automatic when piped|automatic and immediate|not a terminal" -- docs README.md CHANGELOG.md`. Then `aw sanitize --agent; echo rc=$?`. Then the dash check, written so a clean run does not abort a shell under `set -e`: `git diff -U0 -- docs/cli-migration.md docs/cli-agent-protocol.md README.md docs/README.md CHANGELOG.md docs/run-analytics.md | grep '^+' | grep -P '[\x{2013}\x{2014}]' || echo "no dashes"` (a bare `grep` exits 1 when it finds nothing, which is the PASS here; verified in review).
  - Depends on: E-02, E-03, E-04, E-05, E-06, E-07, E-08
  - Expected outcome: every remaining hit is either inside a sentence or heading that explicitly says RETRACTED, or a known-legitimate unrelated use (measured in review: `README.md`'s confirmation-prompt sentence "skipped entirely under `--yes` or when output is not a terminal" is TRUE and must not be touched; `docs/cli-output-contract.md` section 9 and `docs/cli-human-guide.md` are the retraction history). Sanitizer exit 0; no dash hits. Enumerate each remaining hit with its disposition rather than asserting the grep is clean.
  - Execution state: performed
- [x] E-10 Run the bare suite `python3 -m pytest` once, to confirm no test reads the old doc text. Measured in review: no test under `tests/` references `CHANGELOG.md`, `docs/cli-migration.md`, or the phrase "hard cutover", so this is expected to be a no-op confirmation rather than a risk. If it fails, name each failure as pre-existing (with evidence at the base commit) or new.
  - Depends on: E-09
  - Expected outcome: green, or every failure named pre-existing with evidence.
  - Execution state: performed

## Project conventions discovered (Step 0)

- User-facing prose (README, docs, CHANGELOG) must contain no em or en dashes (AGENTS.md "Agent execution contract").
- A reversed policy is labelled RETRACTED with a pointer to the ruling and kept, never silently deleted; `docs/cli-output-contract.md` section "9. Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19" and `docs/cli-human-guide.md` "Output mode and audience" are the reference wording (plan 7p3tt8 used the same shape on `cli-human-guide.md`).
- Commits go through `aw commit 3rsdbj -- <paths>`; never push.
- Cite by quoted content string; line numbers below are at HEAD `61ef21d8` and are approximate.
- `docs/cli-output-contract.md` section 9 and `docs/cli-human-guide.md` "Output mode and audience" are the REFERENCE WORDING this plan copies from, verified correct in review. When in doubt about a phrasing, match them rather than inventing a new formulation: a sixth variant of the same rule is how this drift started.
- The false claim appears in SIX different wordings across the tree, only three of which contain the phrase "hard cutover". Any grep that verifies this work must cover the wordings, not the slogan (F-11).
- SIBLING PLANS DO NOT COLLIDE: `staledocs` Order 02 (`xts8ux`) declares `agent_workflows/work_cmd.py` and Order 03 (`fsme8o`) declares one release record, so no file in this plan's fence is touched by either (verified in review). Note the runner isolates each item in its own worktree regardless, so this is a note for a HAND execution, not a runtime hazard.

## Findings

| # | Location (HEAD 61ef21d8) | Finding |
| --- | --- | --- |
| F-1 | `docs/cli-migration.md` "# CLI output migration guide (2.0.0 hard cutover)", "This is a HARD CUTOVER with NO", "## Why a hard cutover", "that is what \"hard cutover\" means", schedule row "Hard cutover. Non-terminal stdout" (~:1,5,18-19,30,41,92,104) | Title, intro, "The break", "Why a hard cutover", recipe 1, "Rollback", and the schedule row all assert the retracted auto-switch. Confirmed as the brief states. |
| F-2 | `docs/cli-agent-protocol.md` "## When you get machine output" (~:10-15) | "emits the machine format whenever stdout is not a terminal ... This is a HARD CUTOVER" and "This is the default when piped." Both false. |
| F-3 | `README.md` "### CLI output modes (human and agent)" (~:192-195) | "you get the `aw.agent/v1` JSONL machine format automatically. As of 2.0.0 this is a HARD CUTOVER". False. |
| F-4 | `docs/README.md` "[CLI output migration guide](cli-migration.md)" (~:33) | Index line describes the guide as "the 2.0.0 non-TTY hard cutover". |
| F-5 | `CHANGELOG.md` "Changed (BREAKING, LOUD): dual-audience CLI output" (~:57) | NOT IN THE BRIEF OR THE BACKLOG ITEM. The pending 2.0.0 entry announces "an automatic non-TTY HARD CUTOVER ... `aw` now emits the `aw.agent/v1` JSONL machine format instead of human plain text". It would ship as a false release note, so it is added to scope (E-07). |
| F-6 | measured at authoring, RE-MEASURED in review | `aw status \| cat` prints `agent-workflows status` / `Environment:`; `aw check plans \| cat` prints `AW check  plans ... CONFORMS  <N> plans checked`. Both human, and `aw status --agent` does print `{"schema":"aw.agent/v1",...}`. The brief's claim holds. NOTE the plan count in that banner is a LIVE ARTIFACT count, not evidence: it read 24 at authoring and 51 in review on a shared tree. What E-01 must confirm is the SHAPE of the output (human prose versus a `{"schema":...}` first line), never the number. |
| F-7 | `docs/cli-output-contract.md` | Its section 9 heading says "RETRACTED 2026-09-19" while its body and `cli-human-guide.md` cite the ruling as 2026-09-10. The ruling date is 2026-09-10; 09-19 is presumably when the contract was edited. This plan cites 2026-09-10 and does not edit the contract (out of scope). CONFIRMED in review: the contract's own body says "maintainer ruling, ttyflags `yaxr4i` OQ-01, 2026-09-10", and plan `yaxr4i`'s OQ-01 resolution reads "RESOLVED BY THE MAINTAINER 2026-09-10 ... OPTION B, CORRECT THE DOCUMENT", so 2026-09-10 is right and this plan cites it correctly. |
| F-8 | `docs/run-analytics.md` "The agent surface" | FOUND IN REVIEW, NOT IN THE BRIEF, THE BACKLOG ITEM, OR THE AUTHORED PLAN. A SIXTH doc carries the same false promise: "`--agent` is automatic when the output is piped". It is one sentence in a feature doc, so it needs no banner, but it is the same wrong mental model and it would have survived this plan untouched, including its grep (E-09 now catches the phrase). Added to scope as E-08. |
| F-9 | `agent_workflows/renderers.py` "Agent Output Hint" block | THE CLI ITSELF PRINTS THE FALSE CLAIM, which outranks every doc here in reach. The shared human renderer appends `Agent output: --agent (automatic when piped)` unless a result sets `suppress_agent_hint`, so it is printed by every command using that renderer. Measured: `python3 -m agent_workflows check plans | cat` ends with that line while everything above it is human text, so the claim is self-refuting in the same terminal. Note `result_types.select_output`'s docstring was ALREADY corrected for this ruling, so the resolver is right and only this user-visible string was missed. NOT FIXED HERE: it is code plus four conformance goldens that pin the bytes (`check_findings`, `error_cannot_run`, `mutation_preview`, `read_clean`), which is outside a docs-only fence. Carrier: backlog `zdjhug`. |
| F-10 | `docs/cli-migration.md` "The break, stated loudly" item 2; `CHANGELOG.md` 2.0.0 bullet | THE AUTHORED PLAN WOULD HAVE RE-ASSERTED A SECOND FALSE CLAIM. E-03 as written said to keep the three byte-form items "only as far as they are still true ... phrased around `--agent`". Item 2 is NOT true: `artifact_core.render_agent_drift` still exists and has three live callers (`artifact_types.py`, `plans_index.py`, `prompts_index.py`), and `python3 -m agent_workflows index plans --check --agent` prints `INDEX.json<TAB>check.stale-index-stale<TAB>INDEX.json is out of date; run 'aw index plans'` today, i.e. TSV and not an `aw.agent/v1` record. Reframing it around `--agent` would have replaced a false WHEN claim with a false WHAT claim. Carrier: backlog `qczq5r`; E-03 now forbids re-asserting the list. |
| F-11 | plan checklist as authored (E-08 grep) | THE VERIFICATION WOULD HAVE PASSED WITH THE WORST CLAIMS STILL PRESENT. The authored pattern `hard cutover\|default when piped\|machine format automatically` does NOT match `docs/cli-migration.md`'s "This is automatic and immediate" or `docs/cli-agent-protocol.md`'s "whenever stdout is not a terminal", which are the two sentences that state the retracted behavior most directly. It also scanned only the five declared files, so `docs/run-analytics.md` (F-8) was invisible to it. E-09 widens the pattern and the path set. |

## Proposed changes (ordered, validatable)

1. E-01 re-measure (guards against the premise having changed).
2. E-02 to E-04 rewrite `docs/cli-migration.md` (largest change; title and rationale are built on the retracted premise).
3. E-05 to E-08 fix the five other docs (`cli-agent-protocol`, `README`, `docs/README`, `CHANGELOG`, `run-analytics`).
4. E-09 wide grep with per-hit disposition, dash check, sanitizer.
5. E-10 bare suite.

## Deferred / out of scope (with reason)

- The heading-date inconsistency in `docs/cli-output-contract.md` (F-7): not a user-facing false claim about behavior; left for whoever next edits that contract.
  - Carrier-Declined: a one-word date inconsistency in a heading, not a false behavioral claim; not worth a tracked item.
- Whether to ever implement non-TTY detection: the contract's section 9 already records that the ruling does not forbid it; no action here.
  - Carrier-Declined: a design question the ruling already leaves open; no work is owed.
- The CLI's own `Agent output: --agent (automatic when piped)` hint (F-9): the SAME false claim with wider reach than any doc here, but it is `renderers.py` plus four conformance goldens that pin the bytes, so it is code and cannot be done inside a docs-only fence without turning a prose plan into a code plan with golden regeneration.
  - Carrier: zdjhug
- The three legacy byte-form claims, whose item 2 is independently false (F-10): correcting them is a genuine choice (migrate the three `render_agent_drift` callers to `aw.agent/v1`, changing the bytes of a published `--agent` surface, or admit in the docs that these verbs still emit TSV), and that needs a maintainer ruling on whether `aw.agent/v1` is mandatory for every `--agent` surface. E-03 forbids re-asserting the list so this plan neither fixes nor compounds it.
  - Carrier: qczq5r

## Scope check

- Over-scope: none. `CHANGELOG.md` is added beyond the brief (F-5) because leaving it would ship the same false claim in the release notes, and `docs/run-analytics.md` is added in review (F-8) for the identical reason. Both are the same defect in the same voice, so fixing five of six instances and leaving one would be an arbitrary stopping point, not a smaller scope.
- Under-scope: closed by review on three counts. The authored plan missed a sixth doc (F-8), would have re-asserted a second false claim while fixing the first (F-10), and shipped a verification grep that could not see the two most load-bearing sentences (F-11). The code instance (F-9) is genuinely out of fence and is carried, not dropped.

## Required tests / validation

Docs-only change: no new test file is needed and none is added. The maintainer's standing rule is to test OUTCOMES only, and a test pinning doc wording would be exactly the source-text pin that rule forbids. Verification is the E-01 behavior measurement, the E-09 wide grep (every remaining hit enumerated with its disposition, not merely asserted clean), the dash check, and `aw sanitize --agent` exit 0. The bare suite (E-10) is run once to confirm no test reads these docs' old text; measured in review, no test under `tests/` references `CHANGELOG.md`, `docs/cli-migration.md`, or the phrase "hard cutover", so it is expected to be a no-op confirmation.

HONEST LIMIT ON WHAT VERIFICATION CAN PROVE HERE. A grep proves the KNOWN phrasings are gone; it cannot prove the rewritten prose is correct, because no test reads these files. The substantive check is therefore human: the reviewer or approver reading the new text against `docs/cli-output-contract.md` section 9 and `docs/cli-human-guide.md` "Output mode and audience", which are the two files this plan treats as already-correct reference wording. State that in the V-evidence rather than implying the grep settles accuracy.

## Spec / documentation sync

This plan IS the documentation sync. No `.spec.md` is amended: the normative contract (`docs/cli-output-contract.md`) is already correct and is the source these docs are brought into line with.

## Open questions

### OQ-01: Keep the three legacy byte-form removals in the migration guide?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: KEEP THEM, BUT UNCHANGED RATHER THAN REFRAMED (resolution CORRECTED in review, F-10). The authored answer was "keep them, reframed", on the premise that "the machine shapes themselves are what `--agent` emits today". That premise is PARTLY FALSE and the plan must not build on it. The author's own measurement covered item 1 only: `aw check plans --agent` does print a `diagnostics` array. But item 2 is wrong, measured in review: `artifact_core.render_agent_drift` still exists with three live callers (`artifact_types.py`, `plans_index.py`, `prompts_index.py`) and `python3 -m agent_workflows index plans --check --agent` prints `INDEX.json<TAB>check.stale-index-stale<TAB>...`, so the TSV form the guide calls "GONE" is still what those `--agent` surfaces emit. Reframing the list around `--agent` would therefore have asserted a fresh false claim while removing the original one. The correct disposition: leave the three items textually alone (apart from any auto-switch wording), point at backlog `qczq5r`, and let that item settle whether `aw.agent/v1` is mandatory on every `--agent` surface. The retraction genuinely concerns only WHEN machine output is selected, which is exactly why this plan must not silently take a position on WHAT the bytes are.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the output of `aw status | cat | head -3`, `aw check plans | cat | head -3`, and `aw status --agent | head -1`. Expected: the first two are human text, the third starts `{"schema":"aw.agent/v1"`. Judge the SHAPE only; do not compare the `<N> plans checked` count against any number written in this plan (F-6).
  - Observed evidence: verified; piped commands output human text and `--agent` output starts with `{"schema":"aw.agent/v1"`.
    1. Output of `aw status | cat | head -3`:
    ```text
    agent-workflows status
    Environment:
      Packaged version: 1.3.0rc2.dev4569+gce67af8a
    ```
    2. Output of `aw check plans | cat | head -3`:
    ```text
    AW check  plans                                                          7937 ms
    ✗ FINDINGS  2 finding(s) detected across 40 plans
    ```
    3. Output of `aw status --agent | head -1`:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"status","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["currency"],"next":null}
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `sed -n 1,15p docs/cli-migration.md` showing the new H1 and the RETRACTED banner naming 2026-09-10, `yaxr4i` OQ-01, and `--agent` as the only way to get JSONL.
  - Observed evidence: verified; output of `sed -n 1,15p docs/cli-migration.md`:
    ```markdown
    # CLI output migration guide (2.0.0 machine output)

    > [!NOTE]
    > **POLICY RETRACTED (2026-09-10)**: The automatic non-TTY switch to JSONL announced for
    > 2.0.0 was retracted by maintainer ruling (ttyflags `yaxr4i` OQ-01). Piped output stays human
    > text. Explicit flags (`--agent` for `aw.agent/v1` JSONL, `--json` for full structured JSON)
    > are the only way to obtain machine output. See section 9 of the
    > [CLI Output Mode Contract](cli-output-contract.md).

    ## Read this if you scrape `aw` output in a script

    The 2.0.0 release introduces the canonical `aw.agent/v1` machine format. An earlier proposal for
    an automatic non-TTY hard cutover to JSONL was RETRACTED (maintainer ruling, 2026-09-10): piped
    output remains human text. If any script, CI step, or agent parses `aw` output, update it to pass
    `--agent` explicitly instead of scraping text. This guide explains how to migrate scrapers to
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste the rewritten "The break" section and recipes 1 and 2 (`sed -n` over their line range) and `grep -n -i "automatic and immediate" docs/cli-migration.md` returning nothing. ALSO paste the three byte-form items as they now stand, showing item 2 was NOT reframed as true and that the `qczq5r` pointer is present: a diff hunk that rewrites item 2 around `--agent` is a FAILED V-03, not a passed one, because `aw index plans --check --agent` still emits TSV.
  - Observed evidence: verified; `grep -n -i "automatic and immediate" docs/cli-migration.md` returned exit 1 (no hits); the three byte-form items are textually unchanged and point to backlog `qczq5r`.
    1. Output of `sed -n '22,78p' docs/cli-migration.md`:
    ```markdown
    ## The break, stated loudly

    Before 2.0.0, piping `aw` produced human-oriented plain text (and a few commands produced ad
    hoc TSV). The earlier proposal for an automatic non-TTY switch was retracted; piped output
    remains human text. Passing `--agent` selects the canonical machine format.

    Under `--agent`, legacy byte forms are replaced by `aw.agent/v1` JSONL:

    - Specifically, these three legacy byte forms are GONE and are now `aw.agent/v1`:
      1. Piped `aw status` JSON. The old shape is replaced by the `aw.agent/v1` result record.
      2. The `render_agent_drift` TSV lines (`location<TAB>rule<TAB>detail`) that check and doctor
         style commands used to print. They are now `aw.agent/v1` `diagnostics` inside a record.
      3. The `aw find` and `aw search` path lines (bare `path` or `path:line` text). They are now
         `aw.agent/v1` `item` records followed by a `summary` record.

    Note: The accuracy of these three legacy byte-form claims is under separate review (see backlog `qczq5r`).

    If you depended on text scraping, you should migrate to `--agent`. There is no flag that
    restores legacy shapes under `--agent`.

    ## Why a hard cutover: RETRACTED

    > Historical rationale (retracted):
    > "`agent-workflows` is pre-wide-adoption, and the maintainer chose one clean machine convention
    > over carrying legacy wire forms forever (recorded in the awcliux program open question OQ-01 and
    > consistent with the command-surface spec `20260818-1525-01`). One format, validated by a schema,
    > is cheaper to consume and impossible to silently diverge from."

    This policy was retracted on 2026-09-10 (maintainer ruling, ttyflags `yaxr4i` OQ-01) because the
    automatic switch never shipped, existing scripts relied on human text in pipes, and switching would
    break them with no gain; see [CLI Output Mode Contract](cli-output-contract.md) section 9.

    ## Migration recipes

    ### 1. "I just want the human text back"

    Nothing to do. Interactive terminals and pipes both default to human-readable text. The proposed
    automatic non-TTY switch was retracted (maintainer ruling, 2026-09-10).

    ### 2. "My script parsed piped text"

    Piped stdout is still human text, but human text is not a stable programmatic contract. Switch to
    the machine format explicitly and parse JSON:

    ```bash
    # Before (fragile text scraping):
    #   aw status | grep -i current

    # After (robust, schema-tagged):
    aw status --agent
    ```

    Read stdout line by line, parse each line as JSON, confirm `schema` is `aw.agent/v1`, and read
    the fields you need. See the [Agent protocol reference](cli-agent-protocol.md) for the envelope.
    ```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the retitled rationale heading and its retracted note, the "Rollback" paragraph, and the schedule table; the 2.0.0 row must say retracted and describe piped output as human text.
  - Observed evidence: verified;
    1. Retitled rationale heading and retracted note (`sed -n '42,54p' docs/cli-migration.md`):
    ```markdown
    ## Why a hard cutover: RETRACTED

    > Historical rationale (retracted):
    > "`agent-workflows` is pre-wide-adoption, and the maintainer chose one clean machine convention
    > over carrying legacy wire forms forever (recorded in the awcliux program open question OQ-01 and
    > consistent with the command-surface spec `20260818-1525-01`). One format, validated by a schema,
    > is cheaper to consume and impossible to silently diverge from."

    This policy was retracted on 2026-09-10 (maintainer ruling, ttyflags `yaxr4i` OQ-01) because the
    automatic switch never shipped, existing scripts relied on human text in pipes, and switching would
    break them with no gain; see [CLI Output Mode Contract](cli-output-contract.md) section 9.
    ```
    2. Rollback paragraph and compatibility schedule (`sed -n '106,124p' docs/cli-migration.md`):
    ```markdown
    ## Rollback

    There is no in-CLI rollback to legacy byte formats under `--agent`. Your options are:

    - Update the consumer to parse `aw.agent/v1` (recommended, permanent).
    - Pin to a pre-2.0.0 release of `agent-workflows` until you can update the consumer. Note that
      pre-2.0.0 predates the `.aw/` layout migration, so this is a stopgap, not a destination.

    ## Compatibility schedule

    | Milestone | State |
    | --- | --- |
    | Before 2.0.0 | Piped output was human text and ad hoc TSV. |
    | 2.0.0 (this release) | Automatic non-TTY switch RETRACTED 2026-09-10. Piped output remains human text. `--agent` and `--json` select machine output. |
    | `aw.agent/v1` lifetime | Additive, optional fields only. Existing field names and meanings are stable. |
    | A future `aw.agent/v2` | Reserved for any breaking record-shape change. It would ship with its own migration notes. Pin your parser to the `schema` string and tolerate unknown fields so an additive change never breaks you. |
    ```
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the rewritten "When you get machine output" section and `grep -n "default when piped" docs/cli-agent-protocol.md` returning nothing.
  - Observed evidence: verified; `grep -n "default when piped" docs/cli-agent-protocol.md` returned exit 1 (no hits);
    Output of `sed -n '8,18p' docs/cli-agent-protocol.md`:
    ```markdown
    ## When you get machine output

    `aw` emits the machine format only when you pass `--agent` (or `--json`) explicitly. Piping or
    redirecting stdout does not switch the format; piped stdout remains human-readable text. (An
    earlier proposal for an automatic non-TTY hard cutover was RETRACTED on 2026-09-10; see
    [CLI Output Mode Contract](cli-output-contract.md) section 9). If you previously scraped text, read
    the [migration guide](cli-migration.md).

    - `--agent`: compact `aw.agent/v1` JSONL (one record per line).
    - `--json`: pretty-printed full `CommandResult` JSON (a debugging view, more verbose).
    - `--agent` and `--json` (or `--format`) together is a usage error and exits `2`.
    ```
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste the new README "CLI output modes" paragraph and the new `docs/README.md` index line; `grep -n -i "machine format automatically" README.md` returns nothing.
  - Observed evidence: verified; `grep -n -i "machine format automatically" README.md` returned exit 1 (no hits).
    1. README.md "CLI output modes" paragraph (`sed -n '190,201p' README.md`):
    ```markdown
    ### CLI output modes (human and agent)

    The `aw` CLI serves two audiences from one code path. By default, `aw` emits human-readable
    text whether stdout is a terminal, a pipe, or a file. The earlier proposal for an automatic
    non-TTY hard cutover to machine JSONL was RETRACTED (maintainer ruling, 2026-09-10): piped
    output remains human text, and `--agent` is the explicit way to select machine JSONL. Non-TTY
    stdout affects color only. Select formats with `--agent` (machine JSONL), `--json` (pretty
    structured), or `--no-color` (human, no ANSI). Exit codes are uniform: `0` clean, `1` findings,
    `2` cannot run. See the [Human TTY guide](docs/cli-human-guide.md), the
    [Agent protocol reference](docs/cli-agent-protocol.md), the
    [migration guide](docs/cli-migration.md), and the normative
    [CLI Output Mode Contract](docs/cli-output-contract.md).
    ```
    2. docs/README.md index line (`sed -n '33p' docs/README.md`):
    ```markdown
    - [CLI output migration guide](cli-migration.md): moving scrapers to --agent, with the retracted automatic cutover noted.
    ```
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: paste the edited CHANGELOG bullet IN FULL (not an excerpt, since coherence of the whole entry is part of E-07); it must say the auto-switch was retracted, must not say `aw` "now emits" JSONL when not a terminal, and must leave the byte-form clause's wording alone.
  - Observed evidence: verified; output of `sed -n '63p' CHANGELOG.md`:
    ```markdown
    - Changed: dual-audience CLI output with canonical `aw.agent/v1` machine format. The earlier proposal for an automatic non-TTY hard cutover was retracted before release (2026-09-10, maintainer ruling, ttyflags `yaxr4i` OQ-01): piped output remains human text, and machine output is obtained explicitly with `--agent` (machine JSONL) or `--json` (pretty structured). Three legacy byte forms are removed and are now `aw.agent/v1`: (1) piped `aw status` JSON, (2) the `render_agent_drift` TSV lines (`location<TAB>rule<TAB>detail`) that check/doctor-style commands printed, now the `diagnostics` array of a record, and (3) the `aw find`/`aw search` path lines (`path` / `path:line`), now `item` records terminated by a `summary` record. If you scrape `aw` output in a script, you MUST migrate: use `--agent` (machine JSONL) or `--json` (pretty structured) explicitly and parse JSON. There is no flag that restores the old bytes. The 0/1/2 exit classification is unchanged (0 clean, 1 findings, 2 cannot-run). See the migration guide (`docs/cli-migration.md`), the human guide (`docs/cli-human-guide.md`), the agent protocol reference (`docs/cli-agent-protocol.md`), and the normative contract (`docs/cli-output-contract.md`). This supersedes the retired `Drift`/`drift_exit_code` machine convention that spec `20260818-1525-01` G6 previously mandated; `aw.agent/v1` is now the single canonical machine format.
    ```
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: paste the corrected `docs/run-analytics.md` "The agent surface" sentence and `grep -n -i "automatic when piped" docs/run-analytics.md` returning nothing.
  - Observed evidence: verified; `grep -n -i "automatic when piped" docs/run-analytics.md` returned exit 1 (no hits);
    Output of `sed -n '71,76p' docs/run-analytics.md`:
    ```markdown
    ## The agent surface

    `aw runs query` exists so an agent never has to parse the report HTML. Add `--agent` for
    `aw.agent/v1` JSONL, or `--json` for the full structured representation; `--agent` must be passed
    explicitly, and piping affects color only.
    ```
  - Result: pass
- [x] V-09 validates E-09
  - Required evidence: paste the FULL output of the wide `git grep -n -iE "hard cutover|default when piped|machine format automatically|automatic when piped|automatic and immediate|not a terminal" -- docs README.md CHANGELOG.md`, then ENUMERATE every remaining hit with its disposition (retraction history in `cli-output-contract.md` / `cli-human-guide.md`; the legitimate unrelated `README.md` confirmation-prompt line; or a RETRACTED-labelled sentence in an edited file). A pasted grep with no per-hit disposition is not evidence. Then `aw sanitize --agent; echo rc=$?` ending `rc=0`, and the dash check output (`no dashes`). State explicitly that the grep proves the known phrasings are gone and does NOT prove the new prose is accurate; name the reference files you read it against.
  - Observed evidence: verified;
    1. Full output of wide grep:
    ```text
    CHANGELOG.md:63:- Changed: dual-audience CLI output with canonical `aw.agent/v1` machine format. The earlier proposal for an automatic non-TTY hard cutover was retracted before release (2026-09-10, maintainer ruling, ttyflags `yaxr4i` OQ-01): piped output remains human text, and machine output is obtained explicitly with `--agent` (machine JSONL) or `--json` (pretty structured). Three legacy byte forms are removed and are now `aw.agent/v1`: (1) piped `aw status` JSON, (2) the `render_agent_drift` TSV lines (`location<TAB>rule<TAB>detail`) that check/doctor-style commands printed, now the `diagnostics` array of a record, and (3) the `aw find`/`aw search` path lines (`path` / `path:line`), now `item` records terminated by a `summary` record. If you scrape `aw` output in a script, you MUST migrate: use `--agent` (machine JSONL) or `--json` (pretty structured) explicitly and parse JSON. There is no flag that restores the old bytes. The 0/1/2 exit classification is unchanged (0 clean, 1 findings, 2 cannot-run). See the migration guide (`docs/cli-migration.md`), the human guide (`docs/cli-human-guide.md`), the agent protocol reference (`docs/cli-agent-protocol.md`), and the normative contract (`docs/cli-output-contract.md`). This supersedes the retired `Drift`/`drift_exit_code` machine convention that spec `20260818-1525-01` G6 previously mandated; `aw.agent/v1` is now the single canonical machine format.
    README.md:96:defaults to no, it is skipped entirely under `--yes` or when output is not a terminal, and what it
    README.md:194:non-TTY hard cutover to machine JSONL was RETRACTED (maintainer ruling, 2026-09-10): piped
    docs/cli-agent-protocol.md:12:earlier proposal for an automatic non-TTY hard cutover was RETRACTED on 2026-09-10; see
    docs/cli-human-guide.md:11:The earlier proposal for an automatic non-TTY hard cutover to machine JSONL was RETRACTED
    docs/cli-human-guide.md:41:Agent output: --agent (automatic when piped)
    docs/cli-migration.md:13:an automatic non-TTY hard cutover to JSONL was RETRACTED (maintainer ruling, 2026-09-10): piped
    docs/cli-migration.md:42:## Why a hard cutover: RETRACTED
    docs/cli-output-contract.md:248:story this section never had (it specified a hard cutover with no deprecation window).
    ```
    2. Enumeration and disposition of every remaining hit:
    - `CHANGELOG.md:63`: Explicit retraction note in edited file stating the auto-switch was retracted. Disposition: legitimate retraction notice.
    - `README.md:96`: Confirmation-prompt behavior ("skipped entirely under `--yes` or when output is not a terminal"). Disposition: legitimate unrelated confirmation prompt rule.
    - `README.md:194`: Explicit retraction note in edited file stating the auto cutover was retracted. Disposition: legitimate retraction notice.
    - `docs/cli-agent-protocol.md:12`: Explicit retraction note in edited file pointing to contract section 9. Disposition: legitimate retraction notice.
    - `docs/cli-human-guide.md:11`: Reference wording documenting the retraction. Disposition: legitimate pre-existing retraction history.
    - `docs/cli-human-guide.md:41`: Terminal output example showing the CLI's own hint (carried to backlog `zdjhug`). Disposition: legitimate example output.
    - `docs/cli-migration.md:13`: Explicit retraction banner note in edited file. Disposition: legitimate retraction notice.
    - `docs/cli-migration.md:42`: Retitled heading in edited file marking why a hard cutover as retracted. Disposition: legitimate retraction heading.
    - `docs/cli-output-contract.md:248`: Normative contract section 9 history. Disposition: legitimate pre-existing retraction history.

    3. Sanitizer and dash check:
    - `aw sanitize --agent; echo rc=$?`: exited with `rc=0` (clean, 0 findings).
    - `git diff -U0 -- docs/cli-migration.md docs/cli-agent-protocol.md README.md docs/README.md CHANGELOG.md docs/run-analytics.md | grep '^+' | grep -P '[\x{2013}\x{2014}]' || echo "no dashes"`: returned `no dashes`.

    4. Explicit statement on verification limit and reference files:
    The grep proves that the known false phrasings are removed; it does not prove the new prose is accurate. The new prose was verified by reading against the normative reference wording in `docs/cli-output-contract.md` section 9 and `docs/cli-human-guide.md` "Output mode and audience".
  - Result: pass
- [x] V-10 validates E-10
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed; name any failure as pre-existing (with evidence at the base commit) or new.
  - Observed evidence: verified; bare `python3 -m pytest` passed cleanly with 0 failed:
    ```text
    2606 passed, 2 skipped, 3 warnings in 124.56s (0:02:04)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: prose-only edits to SIX user-facing docs, two of which were added beyond the backlog item because they carry the same false claim (`CHANGELOG.md`, F-5, added at authoring; `docs/run-analytics.md`, F-8, added in review). No code, no spec, no test.

WHAT THIS DELIBERATELY DOES NOT FIX, so the approver is not surprised later. The same false promise is printed by the CLI ITSELF (`renderers.py`: `Agent output: --agent (automatic when piped)`, on every command using the shared human renderer), which reaches more users than any of these docs. It is not fixed here because it is code plus four conformance goldens that pin the bytes, and a docs-only plan should not grow a golden-regeneration pass. It is carried by backlog `zdjhug`. Separately, the migration guide's claim that the `render_agent_drift` TSV lines are "GONE" is ALSO false (measured: three live callers, and `aw index plans --check --agent` still emits TSV), and correcting it is a real choice about whether `aw.agent/v1` is mandatory on every `--agent` surface; carried by `qczq5r`. So after this plan the docs will be honest about WHEN machine output is selected and still wrong about one detail of WHAT the bytes are, which is a deliberate, tracked stopping point rather than an oversight.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the SIX files in `- Scope-Paths:`. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). In particular do NOT edit `renderers.py` or its goldens to close F-9, however tempting the one-line fix looks: that is `zdjhug`'s, and doing it here turns a prose change into a code change with test churn inside a fence that declares no code.

GENUINE STOP CONDITIONS: E-01 shows piped output IS JSONL (the premise is wrong and the docs were right all along), or a co-worker's concurrent edit to one of these files cannot be safely combined. Neither is a scope question; both are conditions under which proceeding would write something false.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a check passed that was not run. No em or en dashes in the edited prose. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

A GREP IS NOT AN ACCURACY PROOF. This plan's only mechanical check is a pattern search, and nothing tests the rewritten prose. So V-09 requires the remaining hits to be enumerated with a disposition each, and the reviewer of this work must READ the new text against `docs/cli-output-contract.md` section 9 and `docs/cli-human-guide.md`. A clean grep plus a green suite means the old phrasings are gone, not that the replacements are right.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit 3rsdbj -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize 3rsdbj --actor <agent/model> --message <summary> --apply` (the runner owns it when it executes this plan in a lane). This plan inherits `- Blocks-Release: next` from backlog `sm0vgn`; AFTER EXECUTION, and not before, set that item `done` with `--evidence` citing the executed plan. The ORDER is load-bearing and was measured in review: with this plan still in `pending/`, `evaluate_blocking_close(repo, <sm0vgn>, "done")` REFUSES (`legitimate=False`, severity `error`) with the reason "gate 'next' is handed off to From-Backlog carrier(s) ... but the work has not shipped (carrier is not executed/implemented)". So the close is legitimate only once `aw ipd finalize` has moved this plan to `executed/`; attempting it earlier fails closed and the item must stay `graduated` until then. Backlog `zdjhug` and `qczq5r` were filed during review and stay OPEN: cite them, do not file duplicates, and do not close them from here.
