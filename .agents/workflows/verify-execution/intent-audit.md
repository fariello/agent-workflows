# Intent & Spirit Audit Harness (the 5-dimension verification protocol)

Treat this file as the controlling instruction for AUDITING a completed IPD or user prompt against
both its explicit requirements AND its underlying architectural intent. It is loaded by
`verify-execution.md` (Step 2) and is tool-agnostic: any auditing agent runs it against the real git
diff and real runtime logs, never against commit messages, walkthroughs, or the executor's prose.

Core discipline (inherited from `verify-execution.md`): re-open the actual `path:line` and diff;
re-run the real commands and capture their output; never trust a claim of success you did not
observe. This harness only DETECTS and RATES gaps; it never fixes code in place.

You audit along five dimensions. Every dimension yields concrete `path:line` (or pasted-output)
evidence and feeds the fidelity rubric in `rubric.md`.

## Dimension 1: Explicit Requirements Audit

Verify 100% of what was explicitly required actually landed. Build the requirement checklist from:

- every `E-*` execution item and its stated Expected outcome;
- every acceptance criterion / "Required tests / validation" item;
- every `V-*` validation item (was its Required evidence actually produced?);
- every finding the plan agreed to fix during `/plan-review` (read the plan-review record and
  `## Workflow history`) - these are part of "what was required";
- for a raw user prompt: every distinct instruction in it.

For each, re-open the diff at `path:line` and classify it done / partial / missing / diverged
(reuse the `verify-execution.md` Step 2 vocabulary). A requirement whose `V-*` evidence is empty or
was never run is NOT satisfied, regardless of the `E-*` checkbox.

## Dimension 2: Implicit Intent & Spirit Audit

Verify the change honors the architectural INTENT, not just the letter. A line can be touched while
the goal is missed. Check for:

- completeness of the real behavior (does it actually solve the stated problem, or only the happy
  path named in the example?);
- edge cases and error handling the intent implies (empty, missing, malformed, concurrent, large);
- whether an abstraction/mechanism the plan intended was actually used, or bypassed with a shortcut;
- performance or resource intent (did a change meant to reduce cost actually reduce it?);
- anti-patterns that technically pass but defeat the purpose (see the failure-signature catalog in
  `rubric.md`): swallowed exceptions, silent `try/except: pass`, empty/no-op mock returns, a test
  weakened or an assertion deleted to make it pass, a feature stubbed to "return the expected value"
  rather than computed, a guard clause that always short-circuits.

Quote the offending `path:line`. "It technically runs" is not "it honors the intent."

## Dimension 3: Empirical Runtime Validation

Do not accept any "tests pass" / "lint clean" claim as evidence. RE-RUN the repo's real validation
yourself and capture the actual output:

- run the project's own commands (reuse `/verify` if available; else the commands the plan named:
  e.g. `python3 -m unittest discover -s tests -t .`, `aw ipd lint`, formatters, `--check` gates);
- paste the real stdout/stderr tail and the real exit code into the run record;
- attribute honestly: distinguish a failure INTRODUCED by this execution from a pre-existing red
  baseline (note the baseline). Never blame the execution for a failure it did not cause; never
  excuse one it did.

A required-green result that is red (and this execution owns it) is a gap.

## Dimension 4: Scope & Boundaries Audit

Verify nothing outside the authorized scope was changed or committed:

- read the plan's scope fence; every file in the execution diff must trace to a required change;
- flag unrequested/over-scope edits (judge by complexity/risk, not raw size);
- confirm commits were path-scoped (no bare `git add -A`/`-a` that could sweep unrelated or a
  concurrent agent's files); confirm nothing was pushed and no tag/Release was created;
- confirm no protected/ownership boundary was crossed (e.g. hand-editing a generated/managed file
  that must be regenerated instead).

## Dimension 5: Artifact & Convention Compliance

Verify the surrounding artifacts and metadata conform to repo standards:

- IPD lifecycle metadata is correct (Status, Workflow history, the terminal transition done as a
  post-gate step, not as a checklist item); the plan does not falsely claim execution;
- required spec/doc sync happened (specs, README, CHANGELOG, indexes regenerated where required);
- research/walkthrough artifacts are named and filed per convention (not hand-named where a tool
  owns naming/index);
- the no-em/en-dash rule is applied only to user-facing prose (GUIDING_PRINCIPLES P13), not to
  internal artifacts;
- deterministic gates that own truth were actually run (`aw ipd lint`, `aw sanitize`,
  `--check` verbs) and their output pasted.

## Output of the harness

For each dimension, record the concrete evidence and any gaps (with `path:line` + Severity +
Remediation Risk). Pass the aggregate to `rubric.md` to assign a FIDELITY_* level, which
`verify-execution.md` maps onto its MATCHES / DIVERGES / INCOMPLETE verdict and its D65
corrective-IPD status rule. This harness does not invent gaps where the execution was faithful, and
does not excuse gaps where it was not.
