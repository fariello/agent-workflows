# Guiding Principles

The values that guide work in this repository, and especially the design of the
`release-review/` framework. These are the principles we actually hold and apply, not
aspirations. Where a principle is also enforced mechanically, the enforcing location
is noted.

## 1. Fix by default; justify deferral, not action

The cost of a fix (effort, time, tokens) is not a reason to skip it. Address findings
by default; defer only when the *Remediation Risk* of the fix itself is Medium-High or
higher (complexity, usability, security, or functionality). Severity is for
reporting; Remediation Risk is for deciding.
*Enforced in `release-review/fix-decision-policy.md`.*

## 2. Honest documentation over aspirational documentation

Docs describe what the software actually does today. Intent and rationale recovered
from conversation are verified or clearly marked "inferred, needs confirmation" - we
never manufacture fiction to fill a gap.

## 3. Self-documenting and learn-as-you-go

Software should teach the user as they go (clear names, helpful defaults, actionable
errors, good first-run guidance) so they need not read a manual or take a course.
Prefer making the product self-explanatory over compensating with more documentation.
Minimize user effort; an unnecessary action is a defect.

## 4. Durable knowledge for cold-start handoff

A competent engineer or an LLM with zero prior context should be able to understand a
project's intent, philosophy, architecture, and the *why* behind major decisions from
its own tracked docs. We hold ourselves to this: this repository keeps `README.md`,
`ARCHITECTURE.md`, `DECISIONS.md`, and this file for exactly that reason.

## 5. Externalize state; do not trust memory

For multi-step work, the authoritative record lives in files, not in conversational
memory or ephemeral task lists. This makes work recoverable, auditable, and robust to
context degradation.

Then prefer LOCATION over CONTENTS for state that is surveyed across many items. When
you need to see the state of many artifacts at once (which plans are pending, which
prompts are queued to run), encode that state in the filesystem itself (directory
placement and filename) rather than only in a line inside each file. A directory listing
reveals the state of every item in one cheap glance; reading a status line inside each
file requires opening every file (costly for a human, and many tokens for an agent).
Location-encoded state also resists rot: the state changes by the act of moving the
file, which cannot be half-done or forgotten the way an in-file marker can, and it is
tool-agnostic (a file tree works everywhere; parsing file contents needs a parser that
can drift). This is why the plan lifecycle uses directories for disposition.

Boundaries (when an in-file marker or a stable path is still right):
- One primary axis per tree. A file lives in exactly one directory, so encode only the
  ONE primary lifecycle axis in the path. Orthogonal or secondary attributes
  (readiness, grouping, ordering) stay as in-file fields. This is why plans keep
  disposition in the directory but `Status:`, `Set:`, and `Order:` in the file.
- Do not move artifacts that are cited by a stable PATH. Specs are referenced by path; there,
  citation stability outweighs glanceability, so keep the spec path stable and let an in-file
  `Status:` carry the rare state change (for example current vs superseded). Research is the
  EXCEPTION: research is cited by its stable `<id6>` (resolved via the tool-maintained manifest),
  not by path, so research files are freely movable between states and weekly shards without
  breaking citations. Use the `aw research` / `aw archive` verbs (never hand-move or hand-name
  research); the rename tool updates references and flags danglers.
- If the file must be opened anyway for the task, an in-file marker is fine.

## 6. KISS, and guard against scope creep

Prefer the simplest design that meets the need. Because "fix by default" invites
gold-plating, the complexity axis is the deliberate counterweight: do not add
abstraction, features, or dependencies not traceable to a real need. A new noun does
not automatically require a new model or abstraction; compare semantics, not names.
Follow the generality ladder: prefer variation as data or config first, then a shared
core with thin specialization, and only use bounded special cases when justified.
Do not build for hypothetical needs.

## 7. Solve the general case; stay project-agnostic

Generalize project-specific insight into universal concepts rather than hardcoding one
stack's checklist. The framework must work across languages, frameworks, and project
types. Prefer variation as data or config before code.

## 8. Single source of truth; no drift

Each policy, table, or rule lives in exactly one canonical place and is referenced
elsewhere. Duplicated normative content is a maintenance and correctness hazard.

## 9. Design instructions for the model that will run them

Instructions for LLMs are engineered for reliable execution: forcing functions,
exit-gate checklists, MUST/SHOULD tiering, and context-assembly ordering that respects
how attention degrades. Reliability comes from structure, not from writing more prose.

## 10. Safety and reversibility

Default to non-destructive action. Do not push, publish, deploy, expose secrets, or
change public contracts without explicit permission and analysis. Prefer staged,
reversible changes and a clear record of what was done.

## 11. Deterministic checks belong in scripts, not in LLM workflows

Work that needs NO model judgment (pattern matches, structural validation, config or
lockfile checks, deterministic transforms) belongs in a robust, tested script with a
precise agent-consumable output mode (`--agent`/`--llm`: one machine-parseable record per
finding, no prose). LLM workflows DELEGATE to that script and consume its output instead
of re-deriving the result, which is cheaper, more reliable, and identical across runs. The
leak-sanitizer (DECISIONS D96) is the reference: one engine, an `--agent` mode, and lenses
that call it rather than eyeballing files.

## 12. Ask self-contained questions

When user input is needed, ALWAYS prefer the interactive question tool if available.

Within the question interface, provide clear, concise, self-contained context so the user can answer without rereading earlier messages or opening referenced files.

Include things like:

- The relevant facts.
- What changed or was discovered, if applicable.
- The general reason a decision or clarification is needed.
- Any constraint, dependency, consequence, or tradeoff essential to the answer.
- Your recommendation and its main factual basis, when you have one.

Use your judgement. Use plain English. Prefer a compact synthesis. Do not include chronology, investigation details, quotations, filenames, or exhaustive evidence unless important to decision making.

Do not repeat, preview, or separately summarize the choices that the interactive tool will display. The context should explain the situation; the tool options should present the possible answers.

Keep the context short enough to fit comfortably on a terminal screen. If it is too long, reduce it to the minimum facts needed to make an informed choice. If additional detail is imperative, provide it in the chat (last resort) and say so clearly in the question tool's main text.

The pre-flight self-check list that used to sit here (can the user answer without reopening other material, is every included fact necessary, is the reason for asking clear, have I avoided repeating the tool's choices) MOVED on 2026-09-09 into the `askme` memory kernel, which is where composition actually happens. It is not duplicated here (P8); read it there. It moved because a mandated re-read of this principle was measured to prevent nothing: it was performed on 2026-09-08 and the prompt composed immediately afterwards was still unintelligible to the maintainer, because a checklist stated one indirection away from the composition step does not get applied at the composition step.

The `askme` workflow is the invocable entry point that applies this principle to a repository's open questions: it sorts them into what the repository can answer, what only the human can decide, and what can wait, then asks and records the answers. It references this principle rather than restating it (P8). It exists because this principle alone was measured insufficient: agents that have it loaded still finish work with the human's questions unasked, so `aw ipd lint` refuses a question marked blocking that is still open, and names that workflow as the remedy (see DECISIONS D151).

## 13. Style rules for prose apply to user-facing text, not internal artifacts

Prose style rules whose whole purpose is to keep human-facing text from reading as machine-written apply ONLY to user-facing text you author: READMEs, the CHANGELOG, and documentation meant for end users. The specific rule here is the no em/en dash convention (use hyphens or parenthetical dashes), but the principle is general: the goal is that user-facing prose not feel auto-generated.

These rules do NOT apply to internal or AI-facing artifacts: IPDs and plans, research findings and prompts, specs, walkthroughs, commit messages, and code comments. Spending effort to strip dashes (or otherwise groom the style) of those artifacts wastes time and tokens for no reader benefit, because no end user consumes them as polished prose. Deterministic tooling MUST reflect this scope: a gate that mechanically enforces a user-facing style rule must not fail an internal artifact for it (see P11; the IPD linter does not check dashes).

When in doubt about whether an artifact is user-facing, ask who reads it as finished prose. If the answer is an end user, apply the style rule; if the answer is a maintainer, an executing agent, or a reviewer of internal process, do not.

## 14. Severity labels: bracketed, fixed-width, bold-colored word

User-facing tool output SHOULD tag severity lines with a bracketed, fixed-width label whose WORD is bold-colored and whose brackets are left uncolored: `[ERROR]` (bold red), `[WARN ]` (bold yellow), `[INFO ]` (bold green). The label words are padded to a common width so the brackets align in a column (`ERROR` is 5 chars; `WARN`/`INFO` get a trailing space). The word is always present so meaning survives monochrome, piped, and `NO_COLOR` output; color is a redundant cue, never the only signal (P-accessibility, and consistent with the honest-in-monochrome rule the `Term` helper already follows).

This is a preference for the SEVERITY class of messages, not a mandate that every line of every tool be tagged: plain informational body text, tables, boards, and prompts stay untagged. Apply it where a line is specifically reporting an error, a warning, or a notable informational status.

Enforced/implemented in `agent_workflows/term.py` (the shared `Term` label helper); all `aw` verbs render severity through it rather than hand-rolling ANSI, so the convention stays consistent and honors the `should_color` policy (TTY / `FORCE_COLOR` / `NO_COLOR`). When updating a tool's output to this convention, route it through the `Term` helper; do not emit raw escape codes.

## 15. Guard against honest mistakes, never against a malicious agent

We mitigate SLOPPINESS, not MALICE. Every check, gate, and refusal exists to catch an honest actor (a human or an agent acting in good faith) who is about to make a mistake. None of them exists to stop an agent that is deliberately evading the rules.

WHY. An agent runs as the same user with the same access we have. It can edit the tool, the gate, the test, the instructions, or the record the gate reads. Any defense against a deliberately hostile agent is therefore futile by construction, and each one we build becomes brittle machinery (secret tokens, location guesses, forgery checks) that trips up honest work and costs real recovery time. Measured examples: the per-run driver token (plan `u27oh3`) blocked a human's own feature worktree under `.aw/worktrees/` while its own honest-limits note conceded a same-user agent could read the token file; a proposed baseline gate for suite failures was rejected because "a gate cannot detect deception" and "a genuinely malicious agent would rewrite the gate" (maintainer ruling 2026-09-08, `daexj1` OQ-02, reaffirmed 2026-09-20).

WHAT TO BUILD INSTEAD:
- Tell the actor early and plainly whose step something is (for example the runner's turn-start notice and the `AW-LIFECYCLE-ROLE-001` message).
- Refuse with a clear message that names the cause and the remedy, and offer a deliberate, recorded override where a human may legitimately need one.
- Key checks on the real condition (is a live run working on this plan?) rather than on a proxy (does this folder look like a lane?).
- Make recovery easy: tolerate work finished by someone else, and never strand it.
- Keep honest records and speed bumps: attributions, history lines, and attestations such as `--by-human` are a conscious pause and an honest record, not a lock (spec `honest-human-approval-attestation`).

WHAT NOT TO BUILD: secrets or tokens meant to be hidden from an agent, forgery or tamper detection aimed at an agent, and any mechanism whose justification is "in case the agent lies". If real isolation is ever required, it comes from the operating system (a separate user, a sandbox such as the opt-in hardened profile), never from checks in our own code.

When a review touches an existing gate, apply this principle to it: keep it, simplify it into a clear refusal, or delete it.

## 16. Test outcomes and behavior, never code structure or text

Tests exist to prove that the software behaves correctly when executed. They do NOT exist to freeze source code, prevent refactoring, or verify that text in a script remains unchanged.

### What is prohibited:
- **No production source inspection**: Never use `inspect.getsource`, `inspect.getsourcelines`, `ast.parse`, `read_text()`, or substring/regex searches against production code (`agent_workflows/*.py`) to verify implementation details, wiring, or syntax.
- **No count or census pins**: Never assert on the number of callers, call-site counts, definition counts, or closure sizes as a proxy for an invariant.
- **No text, banner, or docstring pins**: Never assert that exact phrases, warning banners, or docstrings exist in production files. Comments and docstrings are for humans and models reading the code, not test assertions.
- **No architectural placement pins**: Do not assert which module holds a `def` by inspecting ASTs or module dictionaries. Test the behavioral contract of the modules instead.

### What to do instead:
- **Exercise the code**: Call the function, invoke the CLI, run the subprocess, supply inputs, and assert observable outputs (return values, stdout/stderr, exit codes, created files, state mutations).
- **Verify test sensitivity with mutation**: A test is only valid if breaking the underlying behavior makes the test fail. If reorganizing working code or editing a docstring breaks the test, the test is broken.
- **The one narrow exception**: Content verification is permissible only where the text or file itself is the artifact under test (for example, verifying published documentation does not cite deleted test files, or checking that test modules do not attempt network installations in offline suites). Production code is never subject to text or AST structure pins.

### When tests depend on the live checkout or environment:
- **First, synthesize the input (the default)**: Whenever the property does not actually depend on the live checkout, synthesize or anchor the input so the assertion executes everywhere. The live repository root is usually a convenient source of an input rather than the subject of the assertion, so anchoring paths (or generating fixture data) eliminates the dependency entirely.
- **Second, deselect at collection time with a marker**: When the property genuinely requires the live tree, use a collection-time marker (such as `livecorpus`). This is preferred over a runtime skip for two measured reasons: a marker deselect is announced in every run by `tests/deselect_notice.py`, and `make test-all` restores it at the release gate mandated by `.aw/system/workflows/release-review/08-final-ship-review.md`. However, recognize option two's own cost: a marker in the default deselect set removes the test from the default local run and from CI (since `.github/workflows/tests.yml` runs `python -m pytest tests/ -n auto -rfEs` with no `-m ''`), leaving it to execute only under `make test-all` and at release-review. That is the right trade for a test whose redness would block unrelated concurrent lanes (the documented `livecorpus` rationale) and the wrong trade for a test that should simply be made location-independent; choose option two for blast-radius isolation, never merely to quiet a location problem option one can eliminate.
- **Third, a runtime skip**: Use a runtime skip only when the condition cannot be known until the test body runs. The skip MUST carry a stated reason, and the author must verify that no sibling assertion in the same class degrades to a vacuous pass under that same condition. Note the measured caveat: a skip reason is visible in CI, which passes `-rfEs` in `.github/workflows/tests.yml`; the objection is to the default local run (where skips are silent without `-rs`) and to the absence of any gate that re-runs a runtime skip, not to skips being unprintable.
- **Never weaken an assertion so it passes everywhere**: Under no circumstances should an assertion be relaxed, made conditional, or hollowed out so that a test passes vacuously across environments. A test that asserts nothing proves nothing. Adhere to P16's own "Verify test sensitivity with mutation" bullet ("A test is only valid if breaking the underlying behavior makes the test fail") and live precedent in `DECISIONS.md` D78, which resolved a test that "had started passing vacuously" by restoring the real execution path rather than relaxing the assertion.

### Tabulated and table-driven tests (accumulate versus subTest):

Table-driven tests group related test cases differing primarily in data into a single table. When authoring or reviewing table-driven tests in this repository, follow these conventions:

- **The row shape**: A module- or class-level table of tuples, with the human-readable case identifier first and a trailing `why` column. The canonical in-repository shape is stated in `tests/test_ipd_lint.py`'s `RULES` table comment: `(case, the plan text, codes that MUST all be reported, message substrings that must appear on those codes' diagnostics, codes that must NOT be reported, why this row exists)`. The middle columns vary by table (such as inputs, expected value, required `needles`, and `forbidden` substrings; seen across `test_check_engine.py`, `test_completion.py`, `test_executed_transition_gate_e2e.py`, `test_installer.py`, `test_ipd_lint.py`, `test_ipd_schema.py`, and `test_run_selection_policy.py`). Do not prescribe a rigid arity for middle columns.
- **The case-first rule**: The first column serves as the row's human-readable identity in diagnostics and failure messages. While `case` is the most common variable name in loop bindings, the rule requires identity rather than a specific parameter name. Clear contextual names such as `index`, `name`, or `value` are fully conforming when they identify the row.
- **The mandatory `why` column**: Every row carries the rule or invariant it encodes in a trailing `why` column, rendered in failure diagnostics as `this row exists because: <why>`. This column is required because tabulating eliminates the individual test method name that previously documented the test's intent. Without `why`, a failing row reports an unexplained data mismatch; with it, the diagnostic states exactly which invariant failed.
- **The aggregate failure message**: A table test must report all failing rows at once rather than aborting on the first bad row. Use the accumulate pattern: collect failure diagnostics into a list across the loop, then assert the list is empty at the end. The aggregate assertion message should report the fraction of failing rows and explain what the pattern of failures means. See `tests/test_runner_profiles.py` (`ProfileNameGrammarTests.test_every_name_is_accepted_or_refused_by_the_grammar`), whose aggregate message distinguishes between over-reservation and under-reservation defects.
- **When to tabulate**: Tabulate clusters of tests that differ only in data. As recorded in commit `75b90271`: "clusters differing only in DATA become one table whose rows each carry the rule they encode and which reports every failing row at once. What was a CLASS per mode is now a COLUMN" (such as host, lint phase, entry point, cutover marker, queue shape, git state, or resolver). See also the `tests/test_runner_profiles.py` module docstring, which explains using mode columns (HOST, TIER, ROUTE) where testing level-by-level ensures that precedence chains cannot hide inversions.
- **When NOT to tabulate**: Do not merge tests where a tabular structure obscures the underlying property. Keep tests separate when:
  - The property is sequence or rollback order (where recoverability is the reverse execution order and cannot be expressed in an isolated row).
  - The behavior is an idempotence pair.
  - The scenario is a multi-step consent transcript.
  - An explicit ordering constraint exists between phases (such as preflight and apply).
  - The assertion is an `assertRaises` checking an immediate exception.
  - The claim is structural rather than behavioral.
  - The subject compares two dynamic results to each other rather than to a fixed expectation.
  - The test demonstrates a contrast between outcomes (such as absent-yields-empty versus malformed-raises).
  Tests that are deliberately not rows should carry a one-line docstring stating why, following the convention in `tests/test_runner_profiles.py`.
- **Safety gate and constant traps**:
  - Keep refusals individually detectable: Pin the specific refusal code or diagnostic rather than asserting generic refusal, ensuring distinct refusal reasons cannot collapse into an ambiguous failure.
  - Use literal strings for published interfaces: In expected columns, use string literals rather than referencing production constants that define the published interface under test. Referencing constants allows breaking renames to pass silently because constant and code move together (as documented in `tests/test_ipd_lint.py`'s `RULES` table comment).
  - Preserve tri-states: When a field has three semantic states (such as `None` meaning absent/fall-through versus `False` meaning explicit refusal), keep the column three-valued rather than coercing to a boolean.
- **Runner behavior and row verdicts (accumulate versus subTest)**:
  - In default pytest runs (where `pytest-subtests` is not installed), an in-context failure inside `with self.subTest()` aborts test execution immediately: pytest reports only the first failing row, skips all subsequent rows in the loop, and never reaches the aggregate assertion message.
  - In contrast, under `python3 -m unittest`, `subTest` captures individual row failures and proceeds to the aggregate check.
  - An in-loop bare `assert` (outside any subtest context) aborts the loop on the first failure, truncating execution so that later rows never run at all. The accumulate pattern avoids this by collecting issues and asserting once after the loop.
  - Because default pytest runs do not produce per-row outcomes for accumulate tables, a per-row `PASS` list cannot be claimed as valid test evidence today. Valid evidence consists of the enclosing test verdict accompanied by the row's inputs and expected values. Plan `t5txjk` addresses opt-in row-level evidence tooling, while `vtup6x` defines evidence-substitution rules.
