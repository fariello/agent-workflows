# IPD: Build the m0001 short-description validation

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.2 SAFEGUARDS require every model-generated `short_description` to be refused when it is too long, holds a newline or control character, or leaks a path, user name or host name. Plan `odeo9z` owned this as its E-05 beside five other items (6 E-items); research `nj8zdp` guidance (at most 5 E-items per plan) moves it here, split from `odeo9z` in round 3 on 2026-11-09. It is a pure function with no dependency on the journal or the model call, so it can be built first.
- Scope: `validate(text, repo) -> str | None` in `agent_workflows/migrations/m0001_describe.py` (creating the module if `odeo9z` has not yet), with its unit tests in `tests/test_m0001_describe.py`. EXCLUDES: the prompt, journal, tool-less call and regenerate-once rule (`odeo9z`); wiring, CLI options and the real trial (`ya4ee4`).
- Scope-Paths: agent_workflows/migrations/m0001_describe.py, tests/test_m0001_describe.py, .aw/records/plans/pending/20261109-metastore-106-830wku-build-the-m0001-short-description-validation.ipd.md
- Item-Dependencies: executed:dcerjg
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 106
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 830wku

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from odeo9z (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

One function decides whether a generated description is safe to store, with the same refusals the `artifact_meta` writer applies, so `odeo9z`'s regenerate-once rule has a validator to call.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: validation

- [ ] E-01 (carried verbatim from `odeo9z` E-05; create `agent_workflows/migrations/m0001_describe.py` if it does not yet exist, and add its tests to `tests/test_m0001_describe.py`) Add `validate(text, repo) -> str | None` returning the first refusal reason: `attention_contract.refuse_unsafe_descriptive("aw migrate metadata", "short_description", text)` (300-character bound, newline and control characters), then `leak_sanitizer.scan_text(text, "short_description", ruleset, include_warn=True)` over `ruleset = leak_sanitizer.build_ruleset(repo, include_warn=True)` (built once per run) with ANY finding, `fail` or `warn`, refused naming its rule, matching `tve77h` E-03 (b) so the migration's own writer cannot refuse a value this step accepted; then, because the sanitizer flags only THIS machine's home directory, user name and host name (measured at review: `see /home/alice/secret` produces no finding under either ruleset, while the machine's own home path produces `home-path` and `handle` `fail` findings and its host name a `derived:<host>` `warn`), also refuse any whitespace-separated token that is an absolute POSIX path of two or more segments or a Windows drive path, the same extra rule `tve77h` E-03 (b) applies to `message`, so a planted path from another machine is refused too. Strip one pair of surrounding quotes and surrounding whitespace before validating; never truncate, never rewrite inner text.
  - Depends on: none
  - Expected outcome: a 301-character value, a value with `\n`, a value with `\x07`, a value containing this machine's home directory (sanitizer `home-path`), a value containing another machine's home path such as `/home/alice/x` (absolute-path rule) and a value containing this machine's host name (sanitizer `warn`) are each refused with a distinct reason; a 300-character plain sentence and a sentence mentioning the slash command `/plan-review` pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Descriptive-value safety is `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN` 300; leak scanning is `leak_sanitizer.scan_text` with `leak_sanitizer.build_ruleset` (carried from `odeo9z` Step 0).
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); test values for "this machine" are computed at test time, never written into the test file.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `odeo9z` F-02: `rg -n "def (refuse_unsafe_descriptive\|scan_text\|build_ruleset)\b" agent_workflows`: each exists | No helper this part reuses is missing. |
| F-02 | `ipd_lint` IPD-Z603 on `odeo9z` (2026-11-09, cutover patched): "plan has 6 E-items (guidance: at most 5)" | Moving E-05 here brings `odeo9z` to 5. |

## Proposed changes (ordered, validatable)

1. E-01: `validate` and its tests.

## Deferred / out of scope (with reason)

- The rest of the describe module (prompt, journal, tool-less call, regenerate-once).
  - Carrier: odeo9z

## Scope check

- Over-scope: none.
- Under-scope: none for `odeo9z` E-05.

## Required tests / validation

Module: `tests/test_m0001_describe.py` (`core`), validate cases only; `odeo9z` and `ya4ee4` add the rest.

## Spec / documentation sync

No spec change; implements `4sd62s` 4.2 SAFEGUARDS (validation half).

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_describe.py -k validate -rA` all PASSED with the six refusal reasons (length, newline, control character, sanitizer `home-path`, absolute path, sanitizer `derived:<host>` warn) printed or quoted from the assertions, and the two passing cases (300-character sentence, `/plan-review` sentence) by node id.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: no model call. Never write this machine's real home path, user name or host name into a test file; compute them at test time.

Honesty rule: paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 830wku -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 830wku` itself.
