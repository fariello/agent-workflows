# IPD: Advertise the verifier verdict tokens the runner actually accepts, and correct the falsified 'nothing emits NOT CONFORMING' claim

- Date: 2026-09-30
- Kind: child
- Concern: The verifier prompt's schema line asks a model for one of THREE tokens (`"verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED"`, written twice in `runner_shared.build_verifier_prompt` and `runner_shared._build_audit_prompt`) while its consumer `runner_shared._VERDICT_TABLE` recognizes FOUR, the fourth being `NOT CONFORMING`. A reader of either side cannot derive the other, which is the producer/consumer drift that let the original fail-open defect exist. AND THE PREMISE THE ITEM WAS FILED ON IS FALSIFIED BY THE TREE: the item and the code comment beside `VERDICT_NOT_CONFORMING` both assert the token "appears nowhere in this repository except the gate that used to test for it, so nothing is known to emit it", but `tools/awphysical/agy-self-audit-prompt.md` and `tools/awphysical/agy-spec-audit-prompt.md` each contain the line ``- Verdict: `CONFORMING`, `CONFORMING AFTER CORRECTIONS`, or `NOT CONFORMING` ``, which is a PROMPT INSTRUCTING A MODEL TO EMIT EXACTLY THAT TOKEN. Both prompts were added 2026-08-10 (`b629defc`) and the claim was written 2026-09-22 (`0fbb7498`), so the claim was already false when written.
- Scope: Derive BOTH renderings of the schema line from the same constants the consumer is keyed on, so the advertised set and the accepted set cannot disagree; correct the two falsified provenance claims in the code comments so they name the two prompts that DO ask for `NOT CONFORMING`; and pin the agreement with a test that fails if a token is added to the table without reaching the prompt or vice versa. Does NOT add, remove, or re-map any table entry, so no verdict's behavior changes: `CONFORMING` stays absent and fail-closed (the resolution executed plan `1bfppy` recorded as OQ-02, whose reasoning this plan strengthens rather than revisits). Does NOT touch the two `tools/awphysical/` audit prompts, whose `CONFORMING`/`CONFORMING AFTER CORRECTIONS` vocabulary belongs to `agy_run`'s prose-report path that writes no outcome JSON and reaches no verdict table. Does NOT implement the `correction_required -> runnable` requeue (`1bfppy` OQ-01).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: jerb7j
- Set: runverdict
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 3x5wx9

## Workflow history

- 2026-09-30 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `jerb7j`. The item frames the fix as a binary SCHEMA DECISION (advertise the fourth token, or drop it and let it fail closed) and defers the choice to whoever owns the prompt schema. THE REPOSITORY ANSWERS IT: the item's deciding measurement ("`NOT CONFORMING` appears NOWHERE in the repository except the gate that tested for it, so nothing is known to emit it") is FALSE at HEAD, and two tracked prompt files refute it by instructing a model to emit that exact token. Dropping the entry would therefore remove the mapping for a token this repository's own prompts still ask for, so the item's second option is eliminated on evidence and the first is taken. The residual genuinely-maintainer question is narrower and is preserved as `OQ-01`: whether advertising a fourth token in the in-run prompt is wanted at all, given that nothing on THAT path is known to emit it.

## Goal

Make the verifier prompt's advertised verdict set and `map_verdict`'s accepted verdict set ONE derived
fact instead of two hand-maintained spellings, and replace the falsified provenance claim beside
`VERDICT_NOT_CONFORMING` with what the tree actually contains. No verdict changes meaning; what changes
is that a future edit to the table cannot leave the prompt stale, and a reader of the comment is no
longer told something measurably untrue.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the advertised set derived rather than spelled

- [ ] E-01 Add a single module-level source of the ADVERTISED verdict set to `agent_workflows/runner_shared.py`, derived from the recognized entries of `_VERDICT_TABLE` rather than from a literal, plus a helper that renders it in the prompt's `A|B|C` shape. Place both immediately after `_VERDICT_TABLE` (it is the input) and before `map_verdict`. The renderer must emit the three currently-advertised tokens FIRST and in their present order (`VERIFIED`, `CORRECTION_REQUIRED`, `BLOCKED`) so the rendered string is a pure EXTENSION of today's `VERIFIED|CORRECTION_REQUIRED|BLOCKED` and not a reordering of it; a set iteration order is not acceptable because the rendered text is operator-facing and must be stable across runs.
  - Depends on: none
  - Expected outcome: `runner_shared` exposes a name whose value is computed from `_VERDICT_TABLE` and renders exactly `VERIFIED|CORRECTION_REQUIRED|BLOCKED|NOT CONFORMING` at HEAD's table, with no literal token list written beside it.
  - Execution state: pending

- [ ] E-02 Replace the hand-spelled `"verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED"` line in BOTH prompt renderings with the E-01 renderer: the in-run one in `runner_shared.build_verifier_prompt` and the audit one in `runner_shared._build_audit_prompt`. Both are f-strings already, so this is an interpolation and not a restructure. Leave every other byte of both prompts unchanged, including `_build_audit_prompt`'s additional `diff_basis` and `findings_filed` keys.
  - Depends on: E-01
  - Expected outcome: neither prompt composer contains the literal `VERIFIED|CORRECTION_REQUIRED|BLOCKED`; both interpolate the derived renderer; a rendered prompt's schema line reads `"verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED|NOT CONFORMING"`.
  - Execution state: pending

### Task group 2: correct the falsified claim and pin the agreement

- [ ] E-03 Rewrite the docstring comment block on `VERDICT_NOT_CONFORMING` in `runner_shared.py` so it no longer asserts the token "appears nowhere in this repository except the gate that used to test for it" and no longer concludes "nothing is known to emit it". State instead what is measurable: two tracked prompts (`tools/awphysical/agy-self-audit-prompt.md` and `tools/awphysical/agy-spec-audit-prompt.md`) instruct a model to report exactly this token; they drive `agy_run`'s prose-report path (`agy_run.build_turn2_prompt`, whose result is printed by `agy_run.main` and parsed by nothing), so no verdict from them reaches this table TODAY, and that is why the entry is kept as cheap insurance rather than as a live wiring. Also correct the adjacent `VERDICT_CONFORMING` block's closing sentence, which recommends a future fix "on the strength of a plausible story about a model echoing `aw ipd lint`'s vocabulary" and ends "Nothing in the corpus has ever written it": the vocabulary is not `aw ipd lint`'s but those two prompts', which is a stronger and checkable provenance. Do NOT change either constant's VALUE and do NOT change the table, so the OQ-02 resolution stands exactly as executed.
  - Depends on: none
  - Expected outcome: neither comment block asserts the falsified nonexistence claim; both name the two prompt files and the `agy_run` path; `_VERDICT_TABLE` and both constants are byte-identical in value to HEAD.
  - Execution state: pending

- [ ] E-04 Add a test to the existing verdict test home, `tests/test_oc_runipd.py`, asserting the AGREEMENT as a behavioral property rather than as a text match: render both prompts through the real composers and assert that every token `map_verdict` reports `recognized` appears in the rendered schema line, and that every token in that rendered line maps to a `recognized` mapping. Place it beside `VerdictTruthTableTests` so the two are read together. It must be a BIJECTION assertion in both directions, because a one-way check passes vacuously if the renderer emits a superset. Additionally assert that `CONFORMING` is NOT advertised (it is not recognized, so advertising it would invite the very widening `1bfppy` refused) and update the existing `test_verifier_prompt_contents_and_paths` assertion, which pins the old three-token literal via `assertIn("VERIFIED|CORRECTION_REQUIRED|BLOCKED", prompt)`; note that this assertion still passes on the extended string because the new value has it as a PREFIX, so it must be tightened deliberately rather than left to pass by accident.
  - Depends on: E-01, E-02
  - Expected outcome: a new test fails if a token is added to `_VERDICT_TABLE` without reaching either prompt, fails if a prompt advertises an unrecognized token, and fails if `CONFORMING` becomes advertised; the pre-existing prompt test no longer passes on a stale prefix.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A verdict is a TOKEN matched EXACTLY on a normalized form, never by substring: `runner_shared.normalize_verdict` upper-cases, strips, and collapses internal whitespace, and `runner_shared.map_verdict` does a dict lookup. The comment above `_VERDICT_TABLE` records why (`"CONFORMING" in "NOT CONFORMING"` is True, so substring semantics make an arm's behavior depend on another arm's position). This plan must therefore not introduce any prefix or containment test when rendering or checking the advertised set.
- The prompt composers are SHARED, one definition per prompt for both hosts: `oc_runipd.build_verifier_prompt` and `agy_runipd.build_verifier_prompt` both delegate to `runner_shared.build_verifier_prompt`, and the module comments in both hosts cite the (since-deleted) `tests/test_runner_refork_guard.py` as the guard against a host re-growing a private copy. Editing the shared composer is therefore the whole job; there is no per-host copy to update.
- `runner_shared._build_audit_prompt` is PRIVATE and reached only through `build_verifier_prompt(..., audit=True)`; its docstring enumerates exactly THREE intended differences from the in-run rendering and states that requirements 2 through 5 are "reused VERBATIM". Its schema line is inside requirement 5, so a divergence there would contradict that documented invariant, which is why E-02 changes both renderings and not just the in-run one.
- The one accepted V-item result token is `pass` (backlog `mc57em` records that writing the natural word `verified` produces `IPD-S402`/`IPD-S404`), so every `V-*` below terminates at `pass`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
| --- | --- | --- | --- |
| F-1 | The schema line is spelled TWICE, not once, so the drift the item names is doubled. | The literal `VERIFIED\|CORRECTION_REQUIRED\|BLOCKED` occurs three times in `agent_workflows/runner_shared.py`: once in the comment above `VERDICT_VERIFIED` describing the prompt, once in `build_verifier_prompt`'s requirement 5, and once in `_build_audit_prompt`'s requirement 5. It occurs once more in `tests/test_oc_runipd.py`. | E-02 fixes both composers; a fix to only the in-run one would leave the audit prompt stale and contradict `_build_audit_prompt`'s "reused VERBATIM" docstring. |
| F-2 | THE ITEM'S DECIDING MEASUREMENT IS FALSE AT HEAD, which eliminates one of its two options. | The item states `NOT CONFORMING` "appears NOWHERE in the repository except the gate that tested for it - not in a prompt, a test, an outcome file, or a spec". `tools/awphysical/agy-self-audit-prompt.md` and `tools/awphysical/agy-spec-audit-prompt.md` each contain ``- Verdict: `CONFORMING`, `CONFORMING AFTER CORRECTIONS`, or `NOT CONFORMING` `` under "Report back with:". These are prompts asking a model to emit the token, which is the strongest possible refutation of "nothing is known to emit it". | The item's option "drop the alias and let it fall to the fail-closed arm" is rejected on evidence, not on preference: dropping it would unmap a token this repository's own prompts still request. OQ-01 records what remains genuinely open. |
| F-3 | The false claim is not only in the backlog item; it is IN THE SHIPPED CODE COMMENT, and it was already false when written. | The `VERDICT_NOT_CONFORMING` docstring comment in `runner_shared.py` reads "It appears nowhere in this repository except the gate that used to test for it, so nothing is known to emit it". `git log --diff-filter=A` dates both prompt files to `b629defc` (2026-08-10); `git log -S'appears nowhere in this'` dates the claim to `0fbb7498` (2026-09-22). | E-03 exists. A comment asserting a measurably false fact is worse than no comment, because the next author will trust it; this one already propagated into a backlog item. |
| F-4 | The two prompts that ask for the token reach NO verdict table, so this is a documentation defect and not a live fail-open hole. | `agy_run.build_turn2_prompt` loads `_IPD_SELF_AUDIT_PROMPT_FILE` / `_SPEC_AUDIT_PROMPT_FILE`; `agy_run.main` ends the audit branch by `print(audit.response.rstrip())` and returns 0. `agy_run.py` contains zero occurrences of `CONFORMING` and zero of `verdict` outside one prose docstring, and no occurrence of `map_verdict` or `verification.json`. | Fixes the severity claim: nothing is silently passing. This is why the plan is `chore`, changes no mapping, and does not edit the two prompts. |
| F-5 | `CONFORMING` must NOT be advertised even though `NOT CONFORMING` is, so the renderer cannot naively emit "every token any prompt mentions". | `_VERDICT_TABLE` contains `VERDICT_NOT_CONFORMING` and deliberately omits `VERDICT_CONFORMING`; `tests/test_oc_runipd.py`'s `VerdictTruthTableTests.CASES` pins `("CONFORMING", "unverified", True, False)`, i.e. NOT recognized. | E-01 derives the advertised set from `_VERDICT_TABLE`'s RECOGNIZED entries, which yields the correct answer by construction, and E-04 asserts `CONFORMING` stays unadvertised. |
| F-6 | The existing prompt test will PASS VACUOUSLY after E-02 unless deliberately tightened. | `tests/test_oc_runipd.py::VerifierPromptTests::test_verifier_prompt_contents_and_paths` asserts `assertIn("VERIFIED\|CORRECTION_REQUIRED\|BLOCKED", prompt)`. The extended string `VERIFIED\|CORRECTION_REQUIRED\|BLOCKED\|NOT CONFORMING` contains that as a prefix, so the assertion holds without proving anything about the change. | E-04 explicitly updates it. Without this the plan could ship with its only pre-existing guard silently weakened. |
| F-7 | The backlog item's claim that a prompt edit is test-visible via `tests/test_reporting_contract.py` is WRONG: that file does not exist. | The item states "`tests/test_reporting_contract.py` asserts the prompt's verdict line VERBATIM". `ls tests/test_reporting_contract.py` reports no such file; the only verbatim assertion on that line in the tree is in `tests/test_oc_runipd.py` (F-6). `agent_workflows/reporting_contract.py` does exist but contains zero occurrences of `verdict`. | The plan's Scope-Paths name `tests/test_oc_runipd.py`, not the nonexistent file. An executor trusting the item would have edited a path that cannot be opened. |
| F-8 | A second test pins the two rejection tokens' states by direct table subscript, so E-03's "do not change the table" constraint is load-bearing. | `tests/test_terminal_status_vocabulary.py` asserts `runner_shared._VERDICT_TABLE["BLOCKED"].state` and `runner_shared._VERDICT_TABLE["NOT CONFORMING"].state` both equal `"fail-verify"`. | Any restructure of `_VERDICT_TABLE` into a different shape would break an out-of-scope test file. E-01 therefore READS the table and does not reshape it. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/runner_shared.py`: add the derived advertised-set value and its `A|B|C` renderer directly after `_VERDICT_TABLE`, computing from the table's recognized entries with the three historically-advertised tokens pinned first in their existing order (E-01).
2. `agent_workflows/runner_shared.py`: interpolate that renderer into the schema line of `build_verifier_prompt` and of `_build_audit_prompt`, changing nothing else in either prompt (E-02).
3. `agent_workflows/runner_shared.py`: rewrite the `VERDICT_NOT_CONFORMING` comment to state the measured provenance, and correct `VERDICT_CONFORMING`'s closing sentences, leaving both constant values and the table untouched (E-03).
4. `tests/test_oc_runipd.py`: add the two-way agreement test beside `VerdictTruthTableTests`, and tighten `VerifierPromptTests::test_verifier_prompt_contents_and_paths` so it cannot pass on a stale prefix (E-04).

## Deferred / out of scope (with reason)

- The two `tools/awphysical/` audit prompts' own vocabulary (`CONFORMING`, `CONFORMING AFTER CORRECTIONS`, `NOT CONFORMING`) is NOT changed. They drive a prose-report path that parses nothing (F-4), so aligning them with the runner's tokens would be a behavior-free edit to a human-read report format, and doing it inside a plan whose whole point is that the two sides must agree would create a NEW claim (that they now share a vocabulary) that nothing checks. If that alignment is wanted it is its own item.
- Re-mapping `CONFORMING` to a pass is explicitly out of scope. Plan `1bfppy` resolved it fail-closed on the argument that at HEAD it already mapped to `unverified`, so accepting it would WIDEN the pass set of a gate built to narrow it. This plan's F-2 strengthens that reasoning by showing real prompts DO ask for `CONFORMING`; it does not disturb the resolution.
- The `correction_required -> runnable` requeue (`1bfppy` OQ-01) remains unimplemented and untouched.
- Repairing the eight-plus stale citations of the deleted `tests/test_runner_refork_guard.py` in `oc_runipd.py` and `agy_runipd.py` is out of scope: they are already annotated in place with "deleted in `19313eed`", they are unrelated to the verdict surface, and touching them would put two 19k-line host modules in Scope-Paths for a comment sweep.

## Scope check

- Over-scope: none. Both scope paths are modified by an E-item: `agent_workflows/runner_shared.py` by E-01, E-02 and E-03, and `tests/test_oc_runipd.py` by E-04.
- Under-scope: none expected. The advertised-set derivation, both prompt renderings, and the two comment blocks are all in `runner_shared.py`; the only test files asserting on the affected surfaces are `tests/test_oc_runipd.py` (edited, E-04) and `tests/test_terminal_status_vocabulary.py` (deliberately unmodified, since E-03 changes no table entry: F-8). Should the executor find `tests/test_terminal_status_vocabulary.py` or `tools/ipdrunner/test_runagy.py` requires a change, that is a signal the table or a prompt was altered beyond this plan's scope, and the correct response is to stop and report, not to broaden scope.

## Required tests / validation

- `python3 -m pytest tests/test_oc_runipd.py tests/test_terminal_status_vocabulary.py tests/test_verifier_evidence.py tests/test_agy_runipd_cli.py -o addopts=""` for the directly affected surfaces, with per-test counts.
- `python3 -m pytest` (bare; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the fast marker scope) for regression.
- A RED-then-GREEN falsifiability proof of E-04's new test: temporarily add a recognized entry to `_VERDICT_TABLE` (or temporarily restore a hand-spelled literal in one prompt), observe the new test FAIL, revert, observe it PASS. A guard that has never been seen to fail is not evidence.
- `aw sanitize --agent` must report no `fail`, since this plan's evidence quotes file paths.

## Spec / documentation sync

No `.spec.md` file is amended, and none is in Scope-Paths. Checked: spec `25kzda` (`aw <host> run` deterministic run-and-verify) governs the verifier's ROLE and authority (Section 1.1 makes it advisory to the deterministic checker; Section 4.4 requires its findings to force "a correction or human disposition rather than being silently treated as machine truth") but nowhere enumerates the verdict TOKENS, so the accepted set is not a spec-level contract and extending the advertised set amends nothing. Draft spec `i4gpto` (standalone executed-plan audit) discusses the audit verdict's DESTINATION and its `diff_basis` field, not its token vocabulary. No user-facing document states the verdict set.

## Open questions

### OQ-01: Should the IN-RUN verifier prompt advertise a fourth token that nothing on its own path is known to emit?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: The repository answers the item's ORIGINAL binary (F-2 eliminates "drop the alias", because two tracked prompts still ask for the token), and this plan implements the surviving option. What it cannot decide from evidence is a JUDGEMENT about prompt design: the two prompts that request `NOT CONFORMING` drive `agy_run`'s prose path and reach no table (F-4), so on the IN-RUN path the fourth token is accepted-but-unrequested, and advertising it arguably invites a model to use a token the run has no reason to prefer over `BLOCKED` (they map identically: both to `blocked`/`fail-verify`). The alternative shape is to advertise only the three and add a separate machine-readable note that the table also TOLERATES `NOT CONFORMING`, which keeps the prompt minimal while still making the two sides derivable from one source. This plan takes the simpler route (advertise what is accepted) because it is the shape the item asked for and because a tolerated-but-unadvertised token is exactly the asymmetry the item filed against. NOT BLOCKING: either answer is a one-line change to E-01's renderer, the E-04 bijection test is what makes the choice checkable either way, and no verdict's MAPPING depends on the answer. If the maintainer prefers three-plus-a-note, say so at review and E-01 changes; silence is taken as accepting the advertised-set route.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python invocation that imports `runner_shared` and prints both the derived advertised set and the rendered `A|B|C` string, showing the rendered value is exactly `VERIFIED|CORRECTION_REQUIRED|BLOCKED|NOT CONFORMING`. Paste `rg -n` output over the new code showing it references `_VERDICT_TABLE` and contains no hand-written list of all four tokens. Demonstrate ORDER STABILITY by printing the rendered string on at least two separate interpreter invocations with `PYTHONHASHSEED` differing, pasting both.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered schema line from BOTH composers, obtained by calling `runner_shared.build_verifier_prompt` with `audit=False` and with `audit=True` and grepping the returned text for `"verdict"`. Paste `rg -c 'VERIFIED\|CORRECTION_REQUIRED\|BLOCKED' agent_workflows/runner_shared.py` showing the literal now occurs ONLY where a comment quotes history (state the surviving count and why each survivor is legitimate). Paste a diff stat proving no other line of either prompt changed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the rewritten comment blocks in full. Paste `rg -n 'appears nowhere in this repository|nothing is known to emit it' agent_workflows/runner_shared.py` returning no matches. Paste `git diff` over `_VERDICT_TABLE`, `VERDICT_NOT_CONFORMING`'s value and `VERDICT_CONFORMING`'s value showing the values are UNCHANGED, and paste passing output for `tests/test_terminal_status_vocabulary.py` (F-8's direct subscript assertions) as proof the table was not reshaped.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test's source. Paste its RED-then-GREEN proof: the actual failure output with the injected extra table entry (or restored literal) in place, then the actual passing output after reverting, with exit codes. Paste the tightened `test_verifier_prompt_contents_and_paths` source and show it FAILS against a prompt still carrying only the old three tokens. Paste the full bare `python3 -m pytest` summary line as regression evidence, and the per-test counts for the four named files run with `-o addopts=""`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

This plan is authored `to-review` and must not be executed before it is reviewed and explicitly approved.
The executor of this plan MUST: read this plan in full before editing; keep every change inside the
declared Scope-Paths (`agent_workflows/runner_shared.py`, `tests/test_oc_runipd.py`) and stop and report
rather than broadening them; change NO entry, key, or value of `_VERDICT_TABLE` and no constant's value,
since the plan's entire safety argument is that no verdict's behavior changes; perform the RED-then-GREEN
falsifiability proof V-04 demands rather than asserting the guard works; paste ACTUAL runner output with
exit codes for every test claim; and commit only the paths it modified through
`aw commit <plan> -- <paths>`, never `git add -A`, and never push.

LIFECYCLE OWNERSHIP IS CONDITIONAL. If this plan is executed by `aw oc run` or `aw agy run` with the
runner owning the lifecycle, the executor must NOT move this file or set its terminal status: the runner
performs the atomic finalize after its own checks. If it is executed by an agent directly, that agent
performs the terminal transition itself, and only after `aw ipd lint --phase pre-transition` reports
conforming and every `V-*` above carries concrete pasted evidence with `- Result: pass`.
