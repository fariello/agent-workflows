# IPD: Mark the retracted non-TTY JSONL cutover as retracted in the user docs

- Date: 2026-09-26
- Kind: child
- Concern: Five user-facing docs still promise that piped/non-TTY `aw` output switches automatically to `aw.agent/v1` JSONL ("HARD CUTOVER"). That policy was RETRACTED by maintainer ruling ttyflags `yaxr4i` OQ-01 (2026-09-10) and never shipped: `aw status | cat` and `aw check plans | cat` print human text today. A scraper author following these docs gets the wrong mental model of the output contract.
- Scope: IN: `docs/cli-migration.md` (retitle, RETRACTED banner, reframe recipes as "`--agent` is the only way to get machine output", mark the rationale section and the 2.0.0 schedule row retracted rather than deleting them); `docs/cli-agent-protocol.md` "When you get machine output" section (drop the auto-switch claim and the false "This is the default when piped"); `README.md` "CLI output modes" paragraph; `docs/README.md` index line for the migration guide; `CHANGELOG.md` 2.0.0 (pending) entry that announces the cutover. OUT: `docs/cli-output-contract.md` and `docs/cli-human-guide.md` (already correct, they are the reference wording); any code change; the three legacy byte-form removals (TSV drift lines, find/search path lines, old status JSON), which are a separate question from the auto-switch and are not touched here.
- Scope-Paths: docs/cli-migration.md, docs/cli-agent-protocol.md, README.md, docs/README.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: sm0vgn
- Blocks-Release: next
- Set: staledocs
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3rsdbj

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog sm0vgn: Mark the retracted non-TTY JSONL cutover as retracted in five user docs.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every user-facing doc agree with the shipped behavior and with the normative contract (`docs/cli-output-contract.md` section "9. Automatic Non-TTY Migration Policy: RETRACTED"): piped output is human text, and `--agent` / `--json` are the only way to get machine output. The retracted promise is labelled RETRACTED with a pointer to the ruling, not silently deleted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm the behavior the docs must describe

- [ ] E-01 Re-measure the shipped behavior before editing: run `aw status | cat | head -3` and `aw check plans | cat | head -3` and confirm both print human text (not a line starting `{"schema":"aw.agent/v1"`), and `aw status --agent | head -1` prints an `aw.agent/v1` record.
  - Depends on: none
  - Expected outcome: piped output is human text; `--agent` output is JSONL. If piped output IS JSONL, stop and report: the docs would then be correct and this plan's premise wrong.
  - Execution state: pending

### Task group 2: Rewrite the migration guide

- [ ] E-02 In `docs/cli-migration.md`: retitle the H1 (for example `# CLI output migration guide (2.0.0 machine output)`), and directly under it add a RETRACTED banner stating that the automatic non-TTY switch to JSONL announced for 2.0.0 was retracted on 2026-09-10 (maintainer ruling, ttyflags `yaxr4i` OQ-01), that piped output stays human text, that `--agent` is the only way to get `aw.agent/v1` JSONL and `--json` the only way to get full structured JSON, and link `cli-output-contract.md` section 9.
  - Depends on: E-01
  - Expected outcome: the first screen of the guide states the true behavior; no sentence in the intro ("This is a HARD CUTOVER with NO compatibility window") asserts the retracted switch without being marked retracted.
  - Execution state: pending
- [ ] E-03 In `docs/cli-migration.md`, rewrite "The break, stated loudly" so it no longer says non-terminal stdout emits JSONL "automatic and immediate"; keep the three legacy byte-form items only as far as they are still true (the machine shapes are what `--agent` emits), phrased around `--agent`. Reframe the recipes: recipe 1 ("I just want the human text back") says nothing changed for terminals or pipes; recipe 2 says piped text is still text but is not a stable contract, so switch to `--agent`; recipes 3-5 keep their `--agent` / `--json` commands.
  - Depends on: E-02
  - Expected outcome: every recipe tells the reader to pass `--agent` or `--json` explicitly; none implies piping alone yields JSONL.
  - Execution state: pending
- [ ] E-04 In `docs/cli-migration.md`, mark the "Why a hard cutover" section RETRACTED (rename the heading, keep the original rationale as a quoted historical note, add one sentence on why it was retracted pointing at contract section 9); in "Rollback" drop "that is what hard cutover means"; in the "Compatibility schedule" table mark the 2.0.0 row's automatic switch as retracted 2026-09-10 and state the actual 2.0.0 state (piped output is human text; `--agent`/`--json` select machine output).
  - Depends on: E-03
  - Expected outcome: the rationale and schedule rows remain readable as history and are labelled retracted, not deleted.
  - Execution state: pending

### Task group 3: Fix the other four docs

- [ ] E-05 In `docs/cli-agent-protocol.md` section "When you get machine output": replace the first paragraph with the true rule (machine format only when you pass `--agent`; piping or redirecting does not switch it; a one-line RETRACTED note pointing at contract section 9) and delete the false clause "This is the default when piped." from the `--agent` bullet.
  - Depends on: E-01
  - Expected outcome: the section no longer claims non-TTY stdout selects machine output.
  - Execution state: pending
- [ ] E-06 In `README.md` "CLI output modes (human and agent)": replace "when stdout is a pipe, a file, or an agent, you get the `aw.agent/v1` JSONL machine format automatically. As of 2.0.0 this is a HARD CUTOVER: piped output is machine JSONL, not the old plain text." with wording matching `docs/cli-human-guide.md` "Output mode and audience" (human text everywhere by default, `--agent` for machine JSONL, non-TTY affects color only, the auto cutover was retracted 2026-09-10). In `docs/README.md` change the migration-guide index line from "the 2.0.0 non-TTY hard cutover and how to update scrapers" to a description of what the guide now is (moving scrapers to `--agent`, with the retracted cutover noted).
  - Depends on: E-01
  - Expected outcome: neither file asserts the retracted switch.
  - Execution state: pending
- [ ] E-07 In `CHANGELOG.md` under "## 2.0.0 (pending)", edit the bullet beginning "Changed (BREAKING, LOUD): dual-audience CLI output with an automatic non-TTY HARD CUTOVER" so it no longer announces the auto-switch: state that the automatic non-TTY switch was retracted before release (2026-09-10, `yaxr4i` OQ-01), that piped output remains human text, and that machine output is obtained with `--agent`/`--json`. Keep the parts of the bullet that remain true (the `aw.agent/v1` format, the 0/1/2 exit classification, the doc links, the `Drift` supersession).
  - Depends on: E-01
  - Expected outcome: the unreleased changelog entry does not promise behavior the release will not have.
  - Execution state: pending

### Task group 4: Verify

- [ ] E-08 Grep the five files for the retracted claim and run the leak sanitizer: `git grep -n -i "hard cutover\|default when piped\|machine format automatically" -- docs/cli-migration.md docs/cli-agent-protocol.md README.md docs/README.md CHANGELOG.md`, and `aw sanitize --agent; echo rc=$?`. Also check no em or en dash was introduced: `git diff -U0 -- <the five files> | grep '^+' | grep -P '[\x{2013}\x{2014}]'`.
  - Depends on: E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: every remaining grep hit sits inside a sentence or heading that explicitly says RETRACTED; sanitizer exit 0; no dash hits.
  - Execution state: pending

## Project conventions discovered (Step 0)

- User-facing prose (README, docs, CHANGELOG) must contain no em or en dashes (AGENTS.md "Agent execution contract").
- A reversed policy is labelled RETRACTED with a pointer to the ruling and kept, never silently deleted; `docs/cli-output-contract.md` section "9. Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19" and `docs/cli-human-guide.md` "Output mode and audience" are the reference wording (plan 7p3tt8 used the same shape on `cli-human-guide.md`).
- Commits go through `aw commit 3rsdbj -- <paths>`; never push.
- Cite by quoted content string; line numbers below are at HEAD `61ef21d8` and are approximate.

## Findings

| # | Location (HEAD 61ef21d8) | Finding |
| --- | --- | --- |
| F-1 | `docs/cli-migration.md` "# CLI output migration guide (2.0.0 hard cutover)", "This is a HARD CUTOVER with NO", "## Why a hard cutover", "that is what \"hard cutover\" means", schedule row "Hard cutover. Non-terminal stdout" (~:1,5,18-19,30,41,92,104) | Title, intro, "The break", "Why a hard cutover", recipe 1, "Rollback", and the schedule row all assert the retracted auto-switch. Confirmed as the brief states. |
| F-2 | `docs/cli-agent-protocol.md` "## When you get machine output" (~:10-15) | "emits the machine format whenever stdout is not a terminal ... This is a HARD CUTOVER" and "This is the default when piped." Both false. |
| F-3 | `README.md` "### CLI output modes (human and agent)" (~:192-195) | "you get the `aw.agent/v1` JSONL machine format automatically. As of 2.0.0 this is a HARD CUTOVER". False. |
| F-4 | `docs/README.md` "[CLI output migration guide](cli-migration.md)" (~:33) | Index line describes the guide as "the 2.0.0 non-TTY hard cutover". |
| F-5 | `CHANGELOG.md` "Changed (BREAKING, LOUD): dual-audience CLI output" (~:57) | NOT IN THE BRIEF OR THE BACKLOG ITEM. The pending 2.0.0 entry announces "an automatic non-TTY HARD CUTOVER ... `aw` now emits the `aw.agent/v1` JSONL machine format instead of human plain text". It would ship as a false release note, so it is added to scope (E-07). |
| F-6 | measured at authoring | `aw status | cat` prints `agent-workflows status` / `Environment:`; `aw check plans | cat` prints `AW check  plans ... CONFORMS  24 plans checked`. Both human. The brief's claim holds. |
| F-7 | `docs/cli-output-contract.md` | Its section 9 heading says "RETRACTED 2026-09-19" while its body and `cli-human-guide.md` cite the ruling as 2026-09-10. The ruling date is 2026-09-10; 09-19 is presumably when the contract was edited. This plan cites 2026-09-10 and does not edit the contract (out of scope). |

## Proposed changes (ordered, validatable)

1. E-01 re-measure (guards against the premise having changed).
2. E-02 to E-04 rewrite `docs/cli-migration.md` (largest change; title and rationale are built on the retracted premise).
3. E-05 to E-07 fix the four other docs.
4. E-08 grep, dash check, sanitizer.

## Deferred / out of scope (with reason)

- The heading-date inconsistency in `docs/cli-output-contract.md` (F-7): not a user-facing false claim about behavior; left for whoever next edits that contract.
  - Carrier-Declined: a one-word date inconsistency in a heading, not a false behavioral claim; not worth a tracked item.
- Whether to ever implement non-TTY detection: the contract's section 9 already records that the ruling does not forbid it; no action here.
  - Carrier-Declined: a design question the ruling already leaves open; no work is owed.

## Scope check

- Over-scope: none. `CHANGELOG.md` is added beyond the brief (F-5) because leaving it would ship the same false claim in the release notes.
- Under-scope: none known; E-08's grep across the repo's docs (not only these five) can be widened by the executor with `git grep -n -i "hard cutover" -- docs README.md CHANGELOG.md` to confirm no other doc carries the claim.

## Required tests / validation

Docs-only change: no new test file is needed and none is added. The maintainer's standing rule is to test OUTCOMES only, and a test pinning doc wording would be exactly the source-text pin that rule forbids. Verification is the E-01 behavior measurement, the E-08 grep (every hit in a retracted context), the dash check, and `aw sanitize --agent` exit 0. The bare suite (`python3 -m pytest`) is run once to confirm no test reads these docs' old text.

## Spec / documentation sync

This plan IS the documentation sync. No `.spec.md` is amended: the normative contract (`docs/cli-output-contract.md`) is already correct and is the source these docs are brought into line with.

## Open questions

### OQ-01: Keep the three legacy byte-form removals in the migration guide?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: Keep them, reframed. The retraction concerns only WHEN machine output is selected; the machine shapes themselves (`diagnostics` array, `item`/`summary` records) are what `--agent` emits today (`aw check plans --agent` prints a `diagnostics` array, measured), so the recipes remain useful as "how to read `--agent` output".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of `aw status | cat | head -3`, `aw check plans | cat | head -3`, and `aw status --agent | head -1`. Expected: the first two are human text, the third starts `{"schema":"aw.agent/v1"`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `sed -n 1,15p docs/cli-migration.md` showing the new H1 and the RETRACTED banner naming 2026-09-10, `yaxr4i` OQ-01, and `--agent` as the only way to get JSONL.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the rewritten "The break" section and recipes 1 and 2 (`sed -n` over their line range) and `grep -n -i "automatic and immediate" docs/cli-migration.md` returning nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the retitled rationale heading and its retracted note, the "Rollback" paragraph, and the schedule table; the 2.0.0 row must say retracted and describe piped output as human text.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the rewritten "When you get machine output" section and `grep -n "default when piped" docs/cli-agent-protocol.md` returning nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the new README "CLI output modes" paragraph and the new `docs/README.md` index line; `grep -n -i "machine format automatically" README.md` returns nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the edited CHANGELOG bullet; it must say the auto-switch was retracted and must not say `aw` "now emits" JSONL when not a terminal.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste the full `git grep` output (every hit must be in a RETRACTED sentence or heading), the empty dash-check output, `aw sanitize --agent; echo rc=$?` ending `rc=0`, and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: prose-only edits to five user-facing docs, one of which (`CHANGELOG.md`) was added beyond the backlog item because it carries the same false claim (F-5). No code, no spec.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the five files in `- Scope-Paths:`. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Genuine stop condition: E-01 shows piped output IS JSONL (premise wrong), or a co-worker's concurrent edit to one of these files cannot be safely combined.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a check passed that was not run. No em or en dashes in the edited prose.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit 3rsdbj -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize 3rsdbj --actor <agent/model> --message <summary> --apply` (the runner owns it when it executes this plan in a lane). This plan inherits `- Blocks-Release: next` from backlog `sm0vgn`; after execution set that item `done` with `--evidence` citing the executed plan.
