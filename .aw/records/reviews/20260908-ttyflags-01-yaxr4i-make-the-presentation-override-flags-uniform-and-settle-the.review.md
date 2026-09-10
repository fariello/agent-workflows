# Review: make the presentation override flags uniform and settle the documented non-TTY mode rule, child yaxr4i (Set ttyflags)

- Subject-Id: yaxr4i
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `5075613e` (suite baseline taken at `781d70ae`). Every claim was re-measured
independently by walking the built parser tree, driving `select_output` with fake pipe and TTY streams,
running real CLI commands, and running the bare suite in an isolated worktree.

THE PLAN'S TECHNICAL DIAGNOSIS IS ACCURATE IN EVERY PARTICULAR, which is unusual enough to state first.
Re-measured rather than trusted: 25 of 219 nested subcommands lack `--no-color`, and the 25 NAMES are
exactly the ones the plan lists; `--color` and `--tty` are both at 0 of 219; a piped `select_output`
returns `mode=OutputMode.HUMAN color=False` while a TTY returns `HUMAN color=True`; and
`result_types.py` contains exactly TWO `isatty` mentions, both inside the docstring that makes the false
claim. The published contract at `docs/cli-output-contract.md:18` and `:161` really does promise
non-TTY AGENT mode that the code has never implemented. The plan's central judgement, that this
divergence must be settled before `--tty` can be specified at all, is correct and well argued.

THE HEADLINE FINDING IS THAT THE STRUCTURAL LINTER ALREADY FAILED THIS PLAN AND THE REVIEW COULD NOT
CLEAR IT. `aw ipd lint --phase author` exits 1 on `IPD-Q501`: OQ-01 is `Blocking: yes` and still `open`,
which blocks `aw ipd begin` at every checkpoint. So the plan was not executable as it stood. I did NOT
resolve the question. It is not the kind repository evidence can settle: Option A knowingly breaks every
existing consumer that pipes `aw` and parses prose, and Option B retracts a decision the contract
records as a maintainer decision adopted "immediately upon release". Choosing between a compatibility
break and a retraction of a published promise is a maintainer's call about risk appetite, and this run
had no interactive channel through which to ask. Per the workflow's non-interactive rule the question
stays explicitly OPEN, the verdict is REVIEWED - OPEN QUESTIONS, and readiness is NO-GO.

WHAT I COULD DO WAS MAKE THE RULING CHEAPER TO MAKE, and I added three measurements toward that. The
divergence is TOTAL rather than half-built, so Option A is a new feature and not the completion of a
bug fix. The shipped behavior was confirmed on real commands rather than only on `select_output`:
`aw check reviews` piped emits human text and only `--agent` emits JSONL. And Option A's in-repo blast
radius is small but NOT zero: `docs/cli-migration.md:50` documents `aw status | grep -i current` and
`docs/cli-human-guide.md:103` documents `aw doctor | head`, both of which assume human piped output and
would need rewriting; those two paths are now named in Deferred with the condition attached, since
neither is in `Scope-Paths` under the recommended Option B.

THE MOST USEFUL MECHANICAL FINDING SHRINKS THE WORK BY MORE THAN HALF. The 25 missing NAMES are only TEN
DISTINCT PARSER OBJECTS, verified by `id()`: the four `oc`/`opencode` run leaves are ONE object and the
six `agy`/`antigravity` run leaves are ONE object. E-01 is therefore NINE registration edits, not 25 and
not the plan's "roughly half" estimate, and editing per NAME would touch the same object repeatedly. I
also found a latent hazard the plan missed entirely: `conflict_handler="resolve"` is set on every parser,
so adding `parents=[common]` to a parser that already declared one of the three flags would SILENTLY
replace a definition rather than error. No collision exists today, and E-01 now carries the re-check.

Two smaller items are worth noting as strengths preserved rather than problems found. E-02's mechanism
was verified rather than assumed: a mutually-exclusive group declared on an `add_help=False` parent DOES
propagate through `parents=[...]`, and passing both flags raises `SystemExit(2)`, so OQ-02's structural
refusal is satisfiable exactly as specified. And E-07's byte-identity property already HOLDS today,
which makes it a regression guard rather than a fix; that is now stated so a passing V-07 is not
mistaken for having fixed something.

No BLOCKER finding. Eight findings, all FIXED. The one thing standing between this plan and execution is
a decision only the maintainer can make. Everything in task group 1 (E-01 through E-04 plus the new
E-08) is independent of OQ-01, fully measured, and mechanically clear; the gate section now says so, in
case the maintainer wants that value before ruling.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Executability (the plan is not executable as it stands) | `aw ipd lint --phase author --agent` -> exit 1, 3 findings, `IPD-Q501` at line 132 | **THE STRUCTURAL GATE ALREADY FAILS THIS PLAN.** OQ-01 is `Blocking: yes` and `open`, which `IPD-Q501` refuses at every checkpoint from `author` onward, so `aw ipd begin` cannot start. The plan's gate section described OQ-01 as blocking but did not record that the linter therefore REFUSES the plan, so a reader could reasonably have thought approval was the only missing step. | C:Low; U:Low; S:Low; F:High; Overall:High (no safe fix from available evidence: the question is the maintainer's) | OPEN | NOT fixable by the reviewer. OQ-01 left explicitly OPEN with the required decision stated, the lint refusal recorded in the gate section, and an explicit prohibition on clearing it by flipping `- Blocking:` to `no` (E-05 cannot implement a ruling that does not exist, and E-06/E-07 depend on E-05). Verdict set to REVIEWED - OPEN QUESTIONS and readiness to `no-go` accordingly. F-19 records the lint result. |
| PR-002 | MEDIUM | IN-SCOPE | G. Executability (a materially wrong work estimate) | grouped the 25 missing parsers by `id()`: 10 distinct objects; `oc run`/`oc runipd`/`opencode run`/`opencode runipd` share ONE; the six `agy`/`antigravity` run leaves share ONE | **THE 25 NAMES ARE ONLY TEN PARSER OBJECTS, SO E-01 IS NINE EDITS, NOT 25.** The plan guessed "roughly half the reported names" and told the executor to fix once per parser "if they share a builder", leaving the grouping unmeasured. Worse, editing per NAME would touch the same object repeatedly and could double-add the flag. The exact grouping is cheap to measure and turns a vague instruction into nine specific edits. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now lists all ten groups explicitly, states NINE edits, and requires the `id()` grouping be verified before editing. F-13 records it. V-01 requires the grouping and the nine-edit count be pasted. |
| PR-003 | MEDIUM | UNDER-SCOPE | A. Correctness (a silent-overwrite hazard in the prescribed change) | `_AwArgumentParser.__init__` sets `kwargs.setdefault("conflict_handler", "resolve")`; checked all 25 targets for `--agent`/`--json` -> none present | **`conflict_handler="resolve"` MAKES A DUPLICATE FLAG DEFINITION SILENTLY REPLACE RATHER THAN ERROR, AND THE PLAN NEVER MENTIONS IT.** Adding `parents=[common]` to a parser that already declared `--no-color`, `--agent` or `--json` would quietly drop one definition instead of failing loudly. No collision exists today, so this is latent rather than live, but the plan's own evidence is that this command set MOVES (18 -> 25), so a future target may well carry its own flag. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now names the hazard and requires a per-parser collision re-check at execution time. F-14 records it. V-01 requires the re-check be pasted. A new Deferred entry records that changing `conflict_handler` repo-wide is its own item. |
| PR-004 | MEDIUM | IN-SCOPE | D. Anti-regression (a stale baseline plus an open-ended failure allowance) | bare `python3 -m pytest` in an isolated worktree at `781d70ae` -> `5959 passed, 3 skipped, 2 xfailed`, ZERO failures | **THE BASELINE IS STALE AND ITS ALLOWANCE IS THE DANGEROUS PART.** The plan records `1 failed, 5648 passed` with a known `test_orchestrator_retirement` failure AND tells the executor to "expect additional environmental failures inside a lane worktree". The suite is clean. A stale known-failure baseline combined with an open-ended environmental allowance gives an executor two independent excuses for a regression this plan caused. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required tests rewritten with the re-measured clean baseline, an explicit statement that the old figure is stale, and an instruction NOT to carry forward the environmental allowance. F-16 records it. V-07 now compares against the corrected baseline by name. |
| PR-005 | MEDIUM | UNDER-SCOPE | E. Testing (an exemption that could become a hole) | `IPD-Z602` fired on E-04; the plan's exemption instruction was one clause inside a four-clause E-item | **THE EXEMPTION LIST WAS A SUB-CLAUSE OF ANOTHER E-ITEM AND HAD NO SHAPE CONSTRAINT OR MUTATION TEST.** The durable value of this plan is a test that stops the gap regrowing, and the exemption list is the part of that test most able to silently defeat it: a predicate like "skip anything hidden" would absorb the next flagless subcommand, which is exactly the regrowth (18 -> 25) the plan documents. Buried in E-04 alongside three other clauses, it was also the item the density linter flagged. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split out as new E-08 requiring a CLOSED NAMED SET containing only `__complete`, a comment stating why, and a MUTATION adding an unlisted flagless subcommand that must FAIL and name it. New V-08 demands the mutation; a V-08 without it has not validated the item. E-04 trimmed, which also cleared both `IPD-Z602` advisories. |
| PR-006 | LOW | IN-SCOPE | E. Testing (an unverified mechanism in a load-bearing E-item) | built a minimal parent/subparser reproduction: `SystemExit(2)` with `argument --no-color: not allowed with argument --color`; `_AwArgumentParser.error` ends in `self.exit(2)` | E-02 asserts that an argparse mutually-exclusive group gives a structural refusal with exit 2, and OQ-02 depends on that being true, but neither verified it. Propagation of a mutually-exclusive group through `parents=[...]` is not obvious and would have been discovered only at implementation time. It DOES work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now records the verified mechanism and its exit code, so the executor implements rather than re-derives. F-15 records it. |
| PR-007 | LOW | IN-SCOPE | E. Testing (a guard mistakable for a fix) | `aw check reviews --agent` and `--agent --no-color` are byte-identical with zero `\x1b` bytes | E-07 requires machine output be byte-identical under presentation flags, but does not say that this property ALREADY HOLDS. Without that, a passing V-07 reads as having fixed a leak, when its real value is catching a leak `--color` might newly introduce. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07's V-item now states the property holds today, names it a REGRESSION GUARD, and says a difference means `--color` leaked into a machine surface. F-17 records the measurement. |
| PR-008 | LOW | IN-SCOPE | G. Executability (stale coordinates) | `--no-color` is declared at `cli.py:804-808`, not `:789-794`; `isatty` refs are 51 package-wide, not 49 (the `cli.py` 18 is exact) | Two cited coordinates are stale. The plan already mandates re-measuring the subcommand set, which is the right instinct, but it points the executor at a specific line for the `common` parent that no longer holds. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now says to locate `common` by symbol inside `_build_parser` and gives the corrected line; F-18 records both corrections. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 (should non-TTY stdout select AGENT mode as documented, or should the docs be corrected?) blocks the lint. Resolve it from evidence to unblock the plan, flip `Blocking` to `no`, or leave it OPEN and report NO-GO? | LEAVE IT OPEN, report `REVIEWED - OPEN QUESTIONS` and readiness `no-go`, and add measurements that make the maintainer's ruling cheaper. | (a) Resolve it from evidence toward the plan's recommended Option B; rejected because the repository cannot settle it: Option A knowingly breaks unknown external consumers and Option B retracts a decision the contract records as a maintainer decision adopted "immediately upon release", so the choice is about risk appetite and published promises, which is the definition of a human decision. (b) Flip `- Blocking:` to `no` to clear `IPD-Q501`; rejected as defeating a gate rather than satisfying it, and false besides, since E-05 cannot implement a nonexistent ruling and E-06/E-07 depend on E-05. (c) Split task group 1 into its own executable plan; rejected as a scope decision belonging to the maintainer, but recorded in the gate section as an option. | `aw ipd lint --phase author` exits 1 on `IPD-Q501`; `result_types.py` has exactly two `isatty` mentions, both in the docstring, so no branch exists to finish; `aw check reviews` piped emits human text, confirming the shipped behavior; `docs/cli-output-contract.md:161` records the decision as adopted immediately upon release; the workflow's own non-interactive rule prescribes leaving questions OPEN with `REVIEWED - OPEN QUESTIONS` and `NO-GO` when there is no channel to ask. | yes |
| D-2 | E-04 bundled the parser walk and the exemption list, and the density linter flagged it. Dismiss the advisory since it is advisory-only, or split the item? | SPLIT: the exemption list becomes E-08 with its own mutation test. | Dismissing it; rejected because the plan-review rubric states explicitly that a passing count-based size lint does NOT clear conceptual density, and because the exemption list is independently the highest-risk part of the durable deliverable: written as a predicate it silently absorbs the next flagless subcommand and the test stops catching the regrowth it exists to catch. Also rejected: keeping it in E-04 but adding the mutation requirement there, which would have left a five-clause item and a still-firing advisory. | `IPD-Z602` fired on E-04 naming four clauses; the plan's own history documents the gap growing 18 -> 25 precisely because new leaves inherited nothing and nobody was forced to notice; splitting cleared both advisories, so the linter agrees the density was real. | yes |
| D-3 | The 25 missing subcommand names collapse to 10 parser objects. Correct E-01's estimate, or leave the executor to discover the grouping as the plan instructed? | CORRECT it: enumerate all ten groups, state nine edits, and require `id()` verification before editing. | Leaving it to the executor as authored ("roughly half the reported names ... if they share a builder"); rejected because the grouping is cheap to measure and the vague version carries a real hazard: iterating the 25 NAMES would touch the same parser object repeatedly, and with `conflict_handler="resolve"` a repeat add is silent rather than loud. A guess that happens to be wrong in the safe direction is still a guess an executor must redo. | Grouped all 25 missing parsers by `id()` -> 10 distinct objects, with the `oc`/`opencode` four sharing one and the `agy`/`antigravity` six sharing one; `_AwArgumentParser.__init__` sets `conflict_handler="resolve"`, so duplicate adds do not error. | yes |
| D-4 | Option A would invalidate two in-repo docs that document piping `aw` and reading prose. Add those paths to `Scope-Paths` now, or record them conditionally? | RECORD them conditionally in Deferred, with the instruction to add both paths if Option A is ruled. | (a) Adding them to `Scope-Paths` now; rejected because a declared path that is not modified must carry a `--scope-ack` at finalize, and under the RECOMMENDED Option B both files stay correct, so declaring them would create a false signal for the runners' pre-run spec/scope announcement. (b) Saying nothing; rejected because it hides part of Option A's true cost from the very decision that is blocking the plan, and the maintainer is being asked to weigh exactly that cost. | `docs/cli-migration.md:50` documents `aw status \| grep -i current`; `docs/cli-human-guide.md:103` documents `aw doctor \| head`; both assume human piped output and would be wrong under Option A and remain correct under Option B. | yes |
