# Review findings: plan 76fgt1

- Subject-Id: 76fgt1
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `43fb3825` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --json`
conforms after revision with zero diagnostics. No pre-review snapshot was owed: the plan was committed
and unmodified. `aw sanitize --agent` clean. No production code was modified by this review; the
post-change state was measured by rebuilding the parser tree under a patched subclass rather than by
editing `cli.py`.

THE PLAN'S CODE CHANGE IS RIGHT AND ITS MEASUREMENT DISCIPLINE IS EXCELLENT. Every one of its nine
findings reproduced. F-01: instrumenting `argparse._ActionsContainer._handle_conflict_resolve` records
0 firings across `cli._build_parser()` and 0 across all seven builders. F-03: `cli` alone reports
`_handle_conflict_resolve` and is `_AwArgumentParser`; the other six are plain `argparse.ArgumentParser`
on `_handle_conflict_error`. F-04: all 174 `id()`-deduplicated parser objects report resolve today, and
rebuilding under a class with the setdefault removed yields 174 objects all on `_handle_conflict_error`
with no exception, so the conversion is total with no partial middle state. F-05 reproduces the shipped
defect exactly: under `resolve` the duplicate add succeeds silently, the shared action's
`option_strings` becomes `[]`, and the no-flag invocation then yields `agent=True`; under `error` it
raises `argument --agent: conflicting option string: --agent`. F-06: 599 `add_argument` calls, 153
`parents=[...]` usages, three two-parent chains, 9 `_add_commit_flags` and 3 `_register_run_leaf` sites.
F-08 and F-09: the four non-definition `conflict_handler` hits are exactly as described, and the sole
executable occurrence outside the definition is `tests/test_runner_shared.py`'s own plain parser. F-02's
`2935 passed, 2 skipped` matches a bare suite run on this clean tree.

WHAT REVIEW FOUND IS THAT THE PLAN'S EVIDENCE REQUIREMENTS CONTAIN ONE INSTRUCTION THAT CANNOT BE
SATISFIED AND WHOSE ONLY SATISFACTION WOULD BREAK A NORMATIVE FLAG, plus two further falsehoods in the
comment E-03 opens. The code change itself needed nothing.

**V-03 DEMANDS A STATE THAT CANNOT EXIST, AND SATISFYING IT WOULD DELETE THE REPO-WIDE MACHINE-OUTPUT
FLAG (PR-501, HIGH).** V-03 required pasting `aw oc profile add --help` "showing `--oc-agent` unchanged
and `--agent` absent". Measured: the help lists BOTH, because `p_ocp_add` is declared `parents=[common]`
and `common` is exactly where `--agent` is declared. Their coexistence with distinct dests is the whole
achievement of `p0l1to`'s rename (`--oc-agent build --yes` yields `agent=False, oc_agent='build'`). The
only way to make `--agent` absent from that help is to remove it from the shared parent, which strips
the machine-output flag from every `aw` subcommand and contradicts `docs/cli-output-contract.md`. This is
the review's most consequential finding because an executor treats the plan as authoritative at
execution time and is likelier to attempt the deletion than to question the sentence.

**THE COMMENT E-03 REWRITES CARRIES TWO MORE FALSEHOODS THAN THE PLAN NOTICED (PR-502, MEDIUM;
PR-503, MEDIUM).** The plan correctly identifies that the comment's present-tense resolve-mechanism
sentence becomes false. Review found two others in the same comment. First, its bare citation
`agent_workflows/cli.py:729` has ALREADY drifted: that line is docstring prose inside
`_ViewerOrLeafSubParsersAction`, unrelated to `--agent`. This is precisely the defect class the plan's
own Step-0 convention names, sitting in the comment the plan is opening. Second, the comment says
`--agent` is "declared once", and there are TWO declarations in `cli.py`, on `common` and on
`common_upgrade`. Measured across all 174 parser objects: 162 carry exactly one `--agent` action and 12
carry none, so nothing collides today only because no parser inherits both parents. That second
declaration is also the strongest live argument for E-02's guard, since a future
`parents=[common, common_upgrade]` becomes a build-breaking collision under the new policy.

**ONE OF F-07's THREE COUNTS DOES NOT REPRODUCE (PR-504, LOW).** Re-measured: 249 alias-expanded
subcommand paths, not 283; the 174 objects and 151 canonical leaves reproduce exactly. No conclusion
moves, and F-07's actual point (three correct counts that must not be interchanged) is reinforced. But
a plan naming three precise figures invites an executor to treat all three as verifiable constants, and
the one that drifted is the one E-02's guard must not use.

**THE QUOTED SYMPTOM NO LONGER REPRODUCES (PR-505, LOW).** The comment says
`aw oc profile add --agent` "reported 'unrecognized arguments'". Today it parses and emits an
`aw.agent/v1` error record. That is correct post-`p0l1to` behavior and the comment is describing the
pre-fix breakage, which E-03 already frames as history; this supplies the measurement making that
framing non-optional and gives the executor the observed replacement behavior to cite.

**THE REMOVED LINE WAS NEVER ARGUED FOR (PR-506, LOW).** `git log -S` places its introduction in
`ef55eadb`, a 984-line `cli.py` migration, inserted with no comment and unmentioned in the commit
subject. There is no design intent to weigh against removal, and the rationale comment should say so,
because "this was deliberate once" is what the next contributor will assume on meeting an
`ArgumentError`.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. Both authored open questions are `resolved` and both survive review (OQ-02 upheld, and
strengthened by F-12's measurement that the nearest collision is already in the tree rather than
hypothetical). OQ-03 is new, recording the inverted validation requirement.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | HIGH | IN-SCOPE | A. Correctness / E. Testing | plan V-03 ("`--agent` absent"); `p_ocp_add = oc_profile_sub.add_parser("add", parents=[common], ...)`; `common.add_argument("--agent", ...)`; `docs/cli-output-contract.md` | V-03 DEMANDS AN IMPOSSIBLE STATE WHOSE ONLY SATISFACTION IS A BREAKING CHANGE. `aw oc profile add --help` lists BOTH `--agent` and `--oc-agent`, because the verb inherits the shared `common` parent where the repo-wide machine-output flag is declared; the two have distinct dests, which is the entire point of `p0l1to`'s rename. To make `--agent` absent an executor would have to strip it from `common`, removing the normative machine-output flag from every `aw` subcommand. At execution time the plan reads as more authoritative than the tree, so the deletion is the likelier response. | C:Low; U:Low; S:Low; F:Low; Overall:Low (invert one evidence requirement and state the correct invariant) | FIXED | Added F-10 with the measured help output and the distinct-dest parse probe. V-03 now requires BOTH flags present plus the parse probe, states that `--agent` going missing is itself the defect, and records why the old wording was dangerous. Added OQ-03 with the full reasoning. Added a gate prohibition against removing `--agent` from `common`. |
| PR-502 | MEDIUM | IN-SCOPE | G. Plan executability (citation convention) | the `--oc-agent` comment's `agent_workflows/cli.py:729`; `sed -n '725,735p'` showing docstring prose | THE COMMENT BEING REWRITTEN CARRIES AN ALREADY-DRIFTED BARE LINE CITATION. Line 729 is inside `_ViewerOrLeafSubParsersAction`'s docstring, not the `--agent` declaration. This is the exact defect class the plan's own Step-0 convention forbids, in the one comment E-03 opens; a comment rewrite is the cheapest moment to fix it and the worst moment to leave a known falsehood behind. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11. E-03 now requires replacing the bare offset with a symbol or quoted-content citation, per the plan's own convention. V-03 requires confirming no bare `cli.py:<line>` citation remains in the comment. |
| PR-503 | MEDIUM | IN-SCOPE | A. Correctness | two `add_argument("--agent", ...)` sites (`common`, `common_upgrade`); per-parser count `{1: 162, 0: 12}` across 174 objects | THE COMMENT'S "DECLARED ONCE" IS FALSE OF THE FILE, and the second declaration is the live shape this policy guards. `cli.py` declares `--agent` on `common` (`store_true`) and again on `common_upgrade` (`store_true, default=SUPPRESS`). Nothing collides today only because no parser inherits both parents. Under the new policy a future `parents=[common, common_upgrade]` breaks the build - which is the guard working, but only if someone has written down that this is the expected meaning of that failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 with the per-parser measurement. E-03 must not repeat "declared once" and should say "on the shared `common` parent". E-02 must note the two-declaration shape in the test module docstring so the next reader who hits that failure does not reach for `resolve`. Scope check records both declarations must be left as they are. Gate forbids adding a parser that inherits both. OQ-02 strengthened with this measurement. |
| PR-504 | LOW | IN-SCOPE | G. Plan executability (live-artifact convention) | plan F-07 (283 / 174 / 151); re-measurement (249 / 174 / 151) | ONE OF THREE NAMED COUNTS DOES NOT REPRODUCE. The alias-expanded figure is 249 here, not 283; the object count and leaf count reproduce exactly. No conclusion changes and F-07's point is reinforced, but naming three precise figures invites treating all three as constants, and the drifted one is the figure E-02's guard must specifically avoid. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 with all three re-derived. F-07 carries the correction and labels the digits as context. E-02 and V-01 both require re-deriving rather than transcribing, with the guard's bound a floor comfortably below the measured value. |
| PR-505 | LOW | IN-SCOPE | A. Correctness (documentation honesty) | comment's "reported \"unrecognized arguments\""; `python3 -m agent_workflows oc profile add --agent` emitting an `aw.agent/v1` error record | THE QUOTED SYMPTOM NO LONGER REPRODUCES. `--agent` on that verb parses today and behaves as the machine-output flag. E-03 already asks for `p0l1to`'s evidence to be kept "as history rather than as current behavior"; without the measurement that framing is a style preference rather than a correction, and an unqualified present-tense claim is false a second time over. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 with the observed output. E-03 requires the symptom be framed as the pre-fix state; V-03 requires confirming it. |
| PR-506 | LOW | UNDER-SCOPE | C. Architecture (recorded rationale) | `git log -1 -S'kwargs.setdefault("conflict_handler", "resolve")'` -> `ef55eadb`; its diff hunk and 984-line `cli.py` change | THE REMOVED LINE'S PROVENANCE IS UNRECORDED AND IS AN ARGUMENT FOR REMOVAL. It arrived in a large migration commit with no comment and no mention in the subject, so there is no design intent to preserve. The rationale comment should say this, because a future contributor meeting an `ArgumentError` will otherwise assume the blanket `resolve` was a considered choice and restore it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14. E-01's rationale-comment requirement now includes the unargued provenance; V-01 requires the comment name it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | V-03 requires `--agent` absent from `aw oc profile add --help`, which is false. Invert the requirement, or ask the maintainer what was intended? | INVERT IT: require both flags present with a distinct-dest parse probe, and state that `--agent` going missing is the defect. | (a) Ask the maintainer - rejected: the repository answers it by running one command, and the execution contract directs resolving from evidence where it can. (b) Delete the requirement - rejected: the underlying concern (E-03 must not disturb the shipped flag surface) is legitimate and worth an evidence item; only its polarity was wrong. (c) Leave it and let the executor notice - rejected: this is the single likeliest way this plan causes damage, because the only way to satisfy the sentence is to strip a normative flag from every subcommand. | `aw oc profile add --help` lists both flags; `p_ocp_add` declares `parents=[common]`; parse probe yields `agent=False, oc_agent='build'`; `docs/cli-output-contract.md` makes `--agent` normative repo-wide. | yes |
| D-2 | `cli.py` declares `--agent` twice. Is that a defect this plan should fix, a blocker for E-01, or a fact to document? | DOCUMENT IT: not a defect, not a blocker, and explicitly out of scope, with the guard's docstring explaining what a future collision there would mean. | (a) Treat it as a blocker for E-01 - rejected: measured, no parser inherits both parents, so the build succeeds under `error` (verified by rebuilding the whole tree with the setdefault removed: 174 objects, no exception). (b) Consolidate the two declarations into one parent - rejected: `common_upgrade` deliberately uses `default=argparse.SUPPRESS` so a pre-subcommand `--json`/`--agent` is not clobbered by a subparser default, which is a recorded regression fix; merging them would reintroduce it. (c) Say nothing - rejected: it is the nearest live instance of the hazard, so it belongs in the record both as the argument for the guard and as a prohibition. | Per-parser `--agent` action counts `{1: 162, 0: 12}`; `common_upgrade`'s `default=argparse.SUPPRESS` and its "F-5 / CliTests regression" comment; patched-class rebuild succeeding. | yes |
| D-3 | F-07's alias-path count does not reproduce. Correct the digit, or mark all three counts as re-derive-at-execution? | BOTH: correct it and require re-derivation of all three. | (a) Just fix 283 to 249 - rejected: it would drift again, and the plan's own convention says a live count belongs in prose as context rather than as a bar. (b) Drop the figures entirely - rejected: F-07's value is precisely that three different correct counts exist and are confusable, which needs the numbers to illustrate. | Three walks at review HEAD: 249 alias paths, 174 objects, 151 leaves via `command_surface.discover_parser_leaves(root)`. The repository convention on live-artifact counts in acceptance criteria. | yes |
| D-4 | OQ-02 accepts a build-time failure that breaks every command at once. Does the second `--agent` declaration change that judgement? | NO, it strengthens it; uphold OQ-02 and add the measurement. | (a) Reopen OQ-02 as blocking - rejected: the tradeoff is unchanged in kind, and the finding makes the loud-failure side stronger, not weaker: the plausible edit that would trip it would previously have silently emptied a shared flag exactly as `p0l1to` measured. (b) Add a narrower handler that resolves only for known-safe pairs - rejected: argparse offers only `error` and `resolve`, and a custom handler preserving silent-overwrite semantics is the failure mode the item exists to remove. | F-12's two declarations and the 162/12 distribution; F-05's reproduction of the silent `option_strings` emptying; argparse's two-handler vocabulary. | yes |
