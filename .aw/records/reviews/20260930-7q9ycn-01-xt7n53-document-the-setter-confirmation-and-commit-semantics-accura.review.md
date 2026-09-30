# Review findings: plan xt7n53

- Subject-Id: xt7n53
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803 (MEDIUM, fixed), PR-804 (MEDIUM, fixed), PR-805 (MEDIUM, fixed), PR-806 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and byte-identical to the lane input
(`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

I BUILT A REAL FIXTURE AND RE-RAN THE SETTER RATHER THAN READING THE PLAN'S MEASUREMENTS, because this
is a documentation plan whose entire deliverable is a claim about runtime behavior, and its own history
is of an accurate description falsified by a later commit. Fixture built with the real installer
(`install tmp/rev/fx1 --preset local-only --delivery-mode tracked --records-backend repository --yes`,
exit 0), then `ipd scaffold` and `specs new`. Everything the plan asserts about the mechanism holds:

- F-01: the predicate reads `if (ctx.is_agent or ctx.is_json) and not is_dry_run and not yes:` and
  `git show fcf76812` shows exactly the narrowing the plan cites (`-    if not is_dry_run and not yes:`
  to `+    if (ctx.is_agent or ctx.is_json) and not is_dry_run and not yes:`). Flagless
  `ipd set reviewed <id6>` exit 0, wrote `- Status: reviewed`, left the file ` M` with HEAD unmoved.
- F-02: `ipd set approved <id6> --agent` exit 2 with `"next":"aw set approved vnvz9e --yes"`; `--json`
  exit 2 with `"summary": "confirmation required (--yes needed to execute mutation)"`. Verbatim.
- F-03: `ipd set to-review <id6> --yes` printed `Committed 1 path(s): c5040d3c...` and moved HEAD to
  `chore(plans): set status to-review`. The plan's decisive measurement is real.
- F-06: flagless `spec set reviewed <id6>` on a `to-review` spec exit 1 with the review-record
  attestation refusal, not a confirmation refusal.
- F-05, F-09, F-10, F-11, F-12 each verified: both `aw specs set reviewed <id6> --message` invocations
  are live in the spec-review body at exactly two sites; `--yes` occurs exactly 5 times across the four
  READMEs and every hit is about `install`/`setup`/completion, none about a setter; the item carries no
  `Blocks-Release` and is `Work-Kind: chore`; `5poaqh` declares only the two code paths; and
  `artifact-lifecycles.md` carries 19 setter invocations including `aw set prompts` and
  `aw set releases shipped`. Every anchor E-01 through E-05 names resolves at HEAD.

TWO FINDINGS CAME OUT OF MEASURING WHAT THE PLAN DID NOT.

PR-801 IS THE SERIOUS ONE AND IT IS AN UNSATISFIABLE SUCCESS CRITERION SITTING ON TOP OF A CORRECT
PLAN. E-06's Expected outcome demanded that "every documented form exits 0 in human mode and exits 2 in
`--agent` mode without `--yes`". That is false for the exact invocation E-05 exists to annotate, and the
plan's OWN F-06 is the counterexample it did not follow through. `run_set_command` validates each record
with `validate_transition_allowed` in a loop that emits `rule="status.invalid_transition"` and returns 1,
and that loop sits EARLIER in the function than the confirmation predicate. Measured: the documented
`spec set reviewed <id6>` refusal is exit 1 flagless AND exit 1 under `--agent` (payload carries
`"exit":1` and `"rule":"status.invalid_transition"`), never 2. An executor holding E-06's criterion would
chase a cell that cannot be produced, and the plausible wrong move is to add `--yes` to make it "work",
which cannot satisfy a validation gate and would reintroduce F-03 on the surface the plan most wants
protected.

PR-802 IS A NEW FALSEHOOD THE PLAN WOULD HAVE PUBLISHED. E-01 clause (2) said "`--yes` writes AND
commits" flatly. Measured, that holds only in human mode: `ipd set approved <id6> --agent --yes` exits 0,
writes the status, and creates NO commit, because `_offer_self_commit`'s `assume_yes` carries
`and not (agent or json or as_agent)`. The plan KNOWS this (F-04 quotes the expression) and then states
the clause unconditionally anyway, so the finding is an internal contradiction rather than a missing
fact. It matters because the audience of these four READMEs is substantially agents, by the plan's own
argument for E-05: an agent reading the unconditional clause believes its own `--yes` committed and
either double-commits or omits a commit it thought had happened. Note that F-04 was INFERRED from the
expression rather than run; the `--agent --yes` cell was absent from E-06's mode list, which is why the
contradiction survived authoring.

PR-803: E-05's rationale for not adding `--yes` to the workflow invocations rested on a hazard that does
not exist. It argued an auto-commit there "would commit the spec transition together with whatever the
agent had staged conceptually adjacent". `git_commit_helper.offer_commit` stages ONLY the caller's
explicit paths (`git add -- <paths>`), never `-A`, and its default `on_unrelated_staged="scope"` commits
only those paths while leaving the rest staged-but-uncommitted, with a path outside `paths` NEVER staged
in either mode. The CONCLUSION is right and two real reasons support it, so this is a rationale
replacement rather than a reversal: a machine-mode caller gets no commit from `--yes` at all (F-04), and
`spec-review`'s own "Hardened-result commit" step commits the spec and the review record together, which
a setter self-commit would pre-empt and split.

PR-804: the conventions bullet describing the shared engine names "a declared-but-dead `aw prompts set`".
Measured, `prompts set` is not a subcommand at all (`invalid choice: 'set' (choose from 'new')`), while
the typed-positional `aw set prompts <status> <sel>` IS live and reaches selector resolution. This is not
pedantry: E-06's coverage list is derived from that bullet, and it omitted the typed-positional
`aw set <type> <status> <sel>` form entirely, which is a real spelling `docs/artifact-lifecycles.md`
publishes. A wrong premise produced a coverage gap.

PR-805: the gate carried the commit rule, never-push, the staged-set check, the fixture rule, the unpiped
rule and the paste-output rule, but NO scope fence and NO transition-ownership sentence. The fence matters
concretely here because sibling plan `5poaqh` is already `reviewed` and declares the two code paths this
plan must not touch, and because `artifact-lifecycles.md` is the standing temptation the plan explicitly
declines.

WHAT THE PLAN GETS RIGHT AND I DID NOT WEAKEN. The central reversal is correct and well-evidenced: the
item's premise is stale, its suggested fix would now publish auto-committing examples, and the surviving
defect is that no documentation anywhere states the contract. The one-home-per-policy shape (one paragraph
plus four pointers) follows a convention demonstrated in one of the very files being edited. E-05's
inclusion of a file outside the item's occurrence list is the strongest scope argument in the plan, not
the weakest, and it is backed by the predecessor plan's own deferral row. The three-failure-mode warning
to the executor is unusually good; I added a fourth rather than replacing it.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | IN-SCOPE | E. Testing / A. Correctness (an unsatisfiable success criterion) | `agent_workflows/status_set.py:1965` `validate_transition_allowed` loop emits `rule="status.invalid_transition"` and returns 1; the confirmation predicate is at `:2135`. Measured: documented `spec set reviewed m17qdf` exit 1 flagless AND exit 1 with `--agent` (`"exit":1`, `"rule":"status.invalid_transition"`), never 2 | **E-06's Expected outcome demanded that every documented form exit 2 in `--agent` mode without `--yes`, and an earlier validation gate makes that unachievable for the exact invocation E-05 annotates.** The plan's own F-06 is the counterexample and it was not carried into the criterion. An executor would chase an unproducible cell, and the plausible wrong repair is adding `--yes`, which cannot satisfy a validation gate and would reintroduce F-03 on the most sensitive surface | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-06 gains the measured gate-ordering rule and a PER-INVOCATION expectation (exit 0/exit 2 for a valid transition; same exit in both modes for a gate-blocked one, named as the validation gate), and instructs the executor to record which gate produced each exit and never to force a cell to 2. E-01 gains the ordering sentence, V-01 requires it quoted with its supporting row, F-14 records the mechanism |
| PR-802 | HIGH | IN-SCOPE | B. Security / F. UX (the plan would publish a new inaccuracy) | `status_set._offer_self_commit` `assume_yes` carries `and not (agent or json or as_agent)`. Measured: `ipd set to-review <id6> --yes` moved HEAD to `chore(plans): set status to-review`; `ipd set approved <id6> --agent --yes` exit 0, wrote the status, HEAD unmoved, file ` M` | **E-01 clause (2) stated "`--yes` writes AND commits" unconditionally, which is true only in human mode, and the plan's own F-04 quotes the expression that makes it false for agents.** The audience of these READMEs is substantially agents by the plan's own E-05 argument, so an agent reading it believes its own `--yes` committed and either double-commits or omits a commit it thought happened. The `--agent --yes` cell was missing from E-06's mode list, which is how the contradiction survived authoring | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Clause (2) now carries both halves of the mode split with the measured evidence for each; E-06's mode list gains a REQUIRED `--agent --yes` column with the reason it is not redundant; V-01 requires clause (2) quoted with its two supporting rows and FAILS an unconditional form; V-06 states a table lacking that column does not satisfy the item; F-04 records the direct measurement; the gate's failure-mode list gains this as its ZEROTH entry |
| PR-803 | MEDIUM | IN-SCOPE | C. Architecture (a correct conclusion resting on a non-existent hazard) | `git_commit_helper.offer_commit:518` stages only `paths` (`git add -- <paths>`), never `-A`; `on_unrelated_staged="scope"` default "commits only `paths` and leaves the rest staged-but-uncommitted", and a path outside `paths` is "NEVER staged by this helper" in either mode. `spec-review.md:305` "Hardened-result commit" commits the spec files and the review record together | **E-05 justified withholding `--yes` with a staged-file contamination hazard the shipped helper makes impossible.** A rationale that cites a non-existent mechanism invites a later reader to "correct" it and reverse a conclusion that is actually right for other reasons, and it misrepresents a helper whose whole design is path-scoping | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05's rationale replaced with the two measured reasons (a machine caller gets no commit from `--yes`; the workflow's own commit step would be pre-empted and split), explicitly forbidding the staged-file claim. V-05 requires a grep proving no such claim was written. F-15 records the contract |
| PR-804 | MEDIUM | UNDER-SCOPE | G. Plan executability (a wrong premise producing a coverage gap) | Measured: `prompts set active <sel>` exits 2, `argument prompts_command: invalid choice: 'set' (choose from 'new')`; `set prompts active <sel>` reaches selector resolution (`No prompts artifact matched`). `status_set`'s module docstring lists `aw set <type> <status> <sel>` as its second spelling; `docs/artifact-lifecycles.md` publishes `aw set prompts <status> <selector>` | **The conventions bullet calls `aw prompts set` a declared-but-dead spelling; it does not exist, while the typed-positional route that does exist was omitted from E-06's coverage list.** E-06's list is derived from that bullet, so a wrong premise produced a real gap: the typed-positional form is a documented spelling whose confirmation behavior the plan would publish a contract for without ever running it | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Conventions bullet corrected with the measured evidence and a note on why the correction matters; E-06's coverage list gains the typed-positional `aw set <type> <status> <sel>` form with its citation; V-06's row list gains it; F-16 records both measurements |
| PR-805 | MEDIUM | UNDER-SCOPE | G. Plan executability (missing execution-contract elements) | The gate carried commit/never-push/staged-set/fixture/unpiped/paste-output but no scope fence and no transition ownership. `5poaqh` is at `- Status: reviewed` declaring `agent_workflows/status_set.py, tests/test_status_set.py`; `docs/artifact-lifecycles.md` is the declined widening (F-12) | **No fence declared what this plan must not touch, beside a `reviewed` sibling plan owning the code paths and a 552-line doc the plan explicitly declines.** The runner reconciles edits against a declared fence, so an undeclared one means an out-of-scope edit is neither anticipated nor explained. The transition sentence was absent, so a runner-driven executor had no instruction against invoking the finalize the runner owns | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate gains a declaration-style fence with four named negative constraints (no code/test paths, no `artifact-lifecycles.md`, no `--yes` on any example, no live-record mutation) each with its measured reason plus make-then-justify routing, and the conditional transition-ownership paragraph including that `7q9ycn` must not be set `done` and no gate acquired |
| PR-806 | LOW | IN-SCOPE | F. UX (an asymmetry that strengthens the plan's own answer, unstated) | OQ-02 argued against `--yes` on the ground that it would commit. Measured, for an AGENT copying the same amended example it would not commit at all | **OQ-02's reasoning was one-sided where the two-sided version is stronger.** One appended flag would mean two different things to the two audiences these files serve, which is a better argument for stating a contract instead of amending examples than the one-audience version the plan gave | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02's second measurement re-stated with both audiences and the conclusion that the asymmetry sharpens rather than softens the answer |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-801: E-06's success criterion is unachievable for a gate-blocked transition. Relax the criterion, drop the affected invocation, or make the criterion per-invocation? | PER-INVOCATION, with the gate that produced each exit recorded | (a) Drop `spec set reviewed` from E-06's coverage, since it cannot produce the expected cell; (b) weaken the criterion to "exit 0 or 2"; (c) leave it and let the executor reconcile | Option (a) removes the one invocation E-05 actually annotates, so the surface the plan calls its strongest case would ship with its contract unmeasured. Option (b) destroys the check: "0 or 2" passes for a validation refusal, a confirmation refusal and a success alike, which is the unfalsifiable shape. Option (c) is the finding, and its concrete danger is that the plausible way to force a 2 is to add `--yes`, reintroducing F-03 on the most sensitive surface. Per-invocation is the only option that keeps every cell falsifiable while telling the truth about a preemptive gate, and I verified the ordering in the source (validation loop before the confirmation predicate) rather than inferring it from the exit codes | yes |
| D-2 | PR-802: clause (2) is false for agents. Split it by mode, or drop the commit claim? | SPLIT it by mode, and require the `--agent --yes` measurement | (a) State only the human behavior and say nothing about machine mode; (b) drop clause (2) entirely, leaving `--yes` described only as confirmation | Option (a) is what the plan effectively did and is the finding: on a surface whose audience is substantially agents, an unqualified human-mode claim is read by agents as applying to them. Option (b) discards the single most useful fact in the paragraph, since the auto-commit is precisely what the plan identifies as the reader's likely surprise and is its whole reason for refusing the item's suggested fix. I demonstrated the split rather than reasoning it (`--yes` committed; `--agent --yes` did not), which is the standard this workflow sets for resolving a mechanism question, and that demonstration is now a required E-06 column so the executor re-derives it rather than trusting me | yes |
| D-3 | PR-803: E-05's staged-file rationale is false but its conclusion is right. Replace the rationale, or drop the constraint? | REPLACE the rationale with the two measured reasons; keep the constraint | (a) Keep the rationale, since the conclusion it supports is correct; (b) drop the "do not add `--yes`" constraint for the workflow invocations, since its stated reason does not hold | Option (a) leaves a false claim about a helper whose entire design is path-scoping, and a later reader who checks it will reasonably conclude the constraint was unfounded and reverse it. Option (b) reverses a correct conclusion on the strength of a bad argument: measured, a machine caller gets no commit from `--yes` at all, so instructing an agent to pass it for the commit half would be false, and `spec-review`'s own Hardened-result step commits the spec and record together. Replacing the reason is the only option where both the constraint and the record are true | yes |
| D-4 | PR-804: does correcting the spelling census widen scope, since it adds a row to E-06? | CORRECT it and add the row | (a) Correct the conventions bullet but leave E-06's coverage list as authored; (b) leave both, treating the census as incidental prose | Option (b) lets a measurably false statement stand in the section whose whole purpose is recording verified conventions, and this plan's subject is documentation that drifted from code. Option (a) is worse than either: it records the correct premise and then leaves the coverage list that the wrong premise produced, so the gap survives with its cause removed and the next reader cannot see why. The added row is one more invocation in a fixture E-06 already builds, so the cost is a table row, not a new deliverable; and the form is DOCUMENTED (`aw set prompts <status> <selector>` in `artifact-lifecycles.md`), which is what makes it in-scope for a plan publishing a contract over documented setter forms | yes |
