# Review: Accept --repo as an alias of --dir on aw runs so the run footer's hints compose

- Subject-Id: 8y13kn
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `47c0e0ca`. The target plan was committed and unchanged, so the pre-review
snapshot was correctly skipped per Step 1. Structural preflight reported `conforming` at
`--phase author` before review and `clean` with ZERO findings at `--phase review-finalize` after.

EVERY ONE OF THE PLAN'S FOUR FINDINGS HOLDS, and the diagnosis is precise. `aw runs run-x --repo /tmp`
fails with `unrecognized arguments: --repo /tmp` at exit 2, and `aw runs show run-x --repo /tmp` fails
the same way through the top-level parser. I walked `cli._build_parser()` myself and confirmed F-3
exactly, including its count: 13 `runs` leaves plus the `runs` root accept `--dir`, the four `run`
writing leaves (`start`, `record`, `cancel`, `finalize`) accept it too, and `run`, `run as` and
`run ipd` accept neither. F-2's footer quotation is verbatim on both lines. F-4 is right that only
`runs list` declares `--dir`, which I confirmed by enumerating `get_all_declarations()` (the other
seven are `normalize-lanes`, `ipd execute-set`, `ipd recheck-readiness`, `ipd begin`, `ipd finalize`,
`work begin`, `finish`, none in scope). Both cited artifacts resolve: backlog `tqaxjw` is `graduated`
and research `ffi66q` is a live `todo` survey, so OQ-01's deferral names a real carrier.

I DID NOT STOP AT VERIFYING THE DIAGNOSIS; I APPLIED THE FIX AND MEASURED IT. All six sites edited to
`"--dir", "--repo", dest="dir"`, then: the parser re-walk returned an EMPTY set of `runs`/`run` parsers
accepting `--dir` but not `--repo`; ten argv shapes (the plan's eight, plus `runs submit` and
`run start`) all parsed to `args.dir == R`; the three `--dir` controls still parsed; the end-to-end
`python3 -m agent_workflows runs --repo <tmp>` exited 0 printing `no matching runs found`, byte-identical
to the `--dir` spelling; `tests/test_command_surface_declarations.py` passed; and the bare suite stayed
at `2436 passed, 1 skipped`. The probe is reverted and `agent_workflows/cli.py` is byte-unchanged. So the
approach is not merely plausible, it is demonstrated, and that is recorded as F-5 so the executor does
not re-derive it.

PR-901 IS THE FINDING THAT MATTERS, AND IT IS ABOUT THE PLAN'S OWN PURPOSE. The concern is
discoverability: an operator copies `--repo` from the footer and hits an error. But the plan never
checks that `--repo` becomes VISIBLE, and an alias absent from `--help` is only half a fix - nobody
learns it exists except by guessing. The good news, which I verified rather than assumed, is that
argparse renders multiple option strings on one line automatically, and the precedent sits in the very
parser being changed: `_runs_viewer_flags` already declares `--last`, `--latest`, `-l` on one argument
and `--ipd`, `--id6` on another, rendering as `--last, --latest, -l [N]`. With the probe applied the new
line reads `--dir, --repo DIR`. So nothing extra is needed, but the plan had no item that would notice
if it were, hence E-06 with a stop condition forbidding hand-edited help strings.

PR-903 IS A MEASUREMENT TRAP I FELL INTO MYSELF, which is why it is worth an item. After applying the
probe in-tree, `aw runs --help` still showed a bare `--dir DIR`. That reads exactly like "the alias does
not render" and I spent a cycle chasing the wrong cause, inspecting `_AwArgumentParser`'s
`conflict_handler="resolve"` and `_AlphaHelpFormatter` before noticing the banner `aw` prints on every
invocation here: `aw: invoked in checkout <this worktree> but imported agent_workflows from <another
checkout>`. The `aw` wrapper was running a different checkout's code. Driving `cli._build_parser()`
in-process showed `--dir, --repo DIR` at that same moment. E-01 and E-06 now require the in-tree route
and an explicit banner check, because an executor measuring through `aw` would draw exactly my wrong
conclusion and might "fix" it by editing help strings that were never broken.

PR-904 is the same class of problem as the declaration finding in sibling plan `6vozur`, and here it is
doubled. E-04's evidence is `tests/test_command_surface_declarations.py` passing, which asserts only
`find_undeclared_leaves(...) == set()` - LEAVES, not flags. E-05's declaration case is the `prompts new`
shape, `declared - accepted == set()`, which is satisfied whether or not `--repo` is declared, since a
declared subset of an accepted set always passes. I measured that set difference as empty BEFORE any
declaration change, with `--repo` accepted by the parser and absent from `legacy_flags`. So E-04 could
have been skipped entirely with both named checks green. V-04 now rests on a direct print of the tuple,
and E-05's declaration case asserts both directions.

PR-902 closes a smaller gap. The plan honestly declares in Scope and in its conventions that
`_register_run_leaf` gives the alias to `aw run start|record|cancel|finalize` as well, and that is the
right call - forking a helper whose documented purpose is that the two surfaces "cannot drift apart",
just to withhold a harmless alias, would be worse. But no test covered it, and a declared consequence
with no test is indistinguishable from an accident to the next person who touches the helper. E-05 now
includes a `run start` case and, more usefully, a DERIVED coverage walk asserting that every
`runs`/`run` parser accepting `--dir` also accepts `--repo`, so a leaf added later cannot regress
silently. Recorded as OQ-02.

PR-905 is a table defect I nearly propagated. F-3's cell contained `run start|record|cancel|finalize`
with unescaped pipes, which breaks the markdown row (9 cells instead of 6) and would defeat any tooling
reading these tables. While rewriting it I initially "corrected" the leaf count to fourteen and was
wrong: re-running the walk gives 14 `runs` PATHS, which is 13 leaves plus the root, exactly as the plan
wrote. I record that here because the costlier error in a review is rejecting a correct claim, and I
came one edit away from doing it; the final text restores the plan's number and cites the derivation.

Two things I checked and found correct, recorded so they are not re-derived. Adding `--repo` creates no
new ambiguous abbreviation on the `runs` parser (`--re` and `--r` both resolve to `--repo`; `--d` was
ALREADY ambiguous between `--dir` and `--detail` before this change, so that is pre-existing and not
caused here). And nothing else needs updating: the shell completions are generated from
`cli._build_parser()` rather than hardcoded, and no conformance golden or doc pins the `runs --dir` help
line. The plan carries `- Work-Kind: chore` with no `- Blocks-Release:`, correct since the gating set is
`bug` alone and this is additive friction relief rather than a defect in output.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | MEDIUM | UNDER-SCOPE | F. KISS, principles and UX / E. Testing | With the probe applied, in-tree `format_help()` renders `  --dir, --repo DIR     Target Git repository root (default: current directory).`; existing precedent in the same parser: `--last, --latest, -l [N]` and `--ipd, --id6 IPD` from `_runs_viewer_flags`. No item in the plan inspects help output | THE PLAN NEVER VERIFIES THE ALIAS IS DISCOVERABLE, which is the concern it exists to fix. An operator who cannot see `--repo` in `--help` has no reason to try it, so a parse-only change is half a fix. Argparse happens to render both spellings automatically, so nothing extra is required - but the plan had no item that would NOTICE if that were untrue, and the wrong response to a non-rendering alias (hand-editing help strings) is exactly what an executor would reach for. | C:Low; U:Medium if unfixed (an invisible feature); S:Low; F:Low; Overall:Low | FIXED | Added E-06 verifying the rendered help line for the shared parent, one `_register_run_leaf` leaf and one separately-registered leaf, with V-06 requiring the captured lines and the route used; added a stop condition forbidding hand-edited help strings; added F-6 and a conventions bullet recording the argparse behavior and the in-parser precedent. |
| PR-902 | MEDIUM | UNDER-SCOPE | D. Anti-regression / G. Plan executability | `_register_run_leaf(group, ...)` is called for both `runs_sub` and `run_sub`; probe measured `["run","start","run-x","--repo",R]` -> `args.dir == R`; the plan's E-05 argv list contains no `run` shape and omits `runs submit` | A DECLARED CROSS-NOUN CONSEQUENCE HAS NO TEST. The plan correctly states that the four `aw run` writing leaves (`start`, `record`, `cancel`, `finalize`) gain the alias because one helper registers both nouns, and correctly judges that acceptable. But prose is not a guard: nothing would tell the next person to touch that helper that the cross-noun alias was intended rather than accidental, and a leaf added later could silently miss it. `runs submit` was also absent from the tested shapes despite being one of the four leaves E-03 changes. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 gains a `["run","start","run-x","--repo",R]` case, the missing `runs submit` shape, and a DERIVED coverage walk asserting every `runs`/`run` parser accepting `--dir` also accepts `--repo` (empty violation set measured with the probe). Recorded as OQ-02 with the reasoning that forking the shared helper to withhold the alias would be worse. A stop condition covers the walk finding an uncovered site. |
| PR-903 | MEDIUM | IN-SCOPE | E. Testing and verification | `aw` prints `aw: invoked in checkout <A> but imported agent_workflows from <B>` on every invocation in this worktree; with the probe applied, `aw runs --help` showed `--dir DIR` while `python3 -m agent_workflows runs --help` showed `--dir, --repo DIR` at the same moment | THE `aw` WRAPPER CAN MEASURE A DIFFERENT CHECKOUT, AND THE FALSE READING IS INDISTINGUISHABLE FROM A REAL FAILURE. Review hit this directly and spent a cycle inspecting the parser class and help formatter before noticing the banner. An executor running E-01 or E-06 through `aw` after making the change would conclude the alias does not work or does not render, and the natural "fix" (hand-editing help strings, or adding parser sites that are already correct) makes the tree worse. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 and E-06 now require the in-tree route (`python3 -m agent_workflows` or in-process `_build_parser()`) and an explicit check for the banner before trusting any `aw` output, with the review incident named so the reason is concrete. V-06 requires the route to be stated. Added F-8 and a conventions bullet. The honesty rule names banner-carrying output as not acceptable evidence. |
| PR-904 | MEDIUM | IN-SCOPE | E. Testing and verification | `tests/test_command_surface_declarations.py` holds one test asserting `find_undeclared_leaves(parser) == set()`; measured `set(get_declaration("runs list").legacy_flags) - accepted == set()` BEFORE any declaration change, with `--repo` accepted by the parser and absent from `legacy_flags`; the suite file passes `1 passed in 0.38s` untouched | BOTH CHECKS NAMED FOR E-04 PASS WITH THE DECLARATION MISSING. The shipped test is about undeclared LEAVES, not flags, and E-05's declared-flags case asserts only `declared - accepted`, which a declared SUBSET always satisfies. So the `legacy_flags` edit could be skipped entirely and every stated validation would stay green, making E-04 unverifiable as written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now states plainly that the suite proves nothing about the flag and names the mechanism; V-04 rests on a direct `get_declaration("runs list").legacy_flags` print; E-05's declaration case asserts BOTH directions (declared-subset-of-accepted AND `--repo` present). Added F-7 and a corollary to the conventions bullet; the honesty rule names this as a non-accepted claim. |
| PR-905 | LOW | IN-SCOPE | F. Honest documentation | F-3's cell spelled the four writing leaves with bare pipe separators inside a code span, giving the row 9 cells against the table's 6 | A FINDINGS ROW WAS STRUCTURALLY BROKEN by unescaped pipes inside a code span, which defeats any tooling that parses these tables and misrenders for a human reader. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the cell as a comma-separated list with no bare pipes, and confirmed all findings rows now carry exactly 6 cells. While rewriting it review initially mis-"corrected" the leaf count to fourteen and caught the error by re-running the walk (14 PATHS = 13 leaves + root); the plan's original count was right and is restored with the derivation cited. |
| PR-906 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: `- Cohesion rationale: not required`; one honesty sentence; no stop conditions | THE GATE CARRIED NO STOP CONDITIONS AND NO COHESION RATIONALE, and did not tell the approving human that the change had been demonstrated or that it widens beyond the `runs` noun in a way worth a glance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gained a cohesion rationale, a paragraph reporting review's applied-and-reverted measurement with the numbers, an explicit note on the cross-noun widening, two non-accepted-evidence clauses in the honesty rule, and three stop conditions (help not rendering both spellings; the coverage walk finding an uncovered parser; a `--dir` control failing, which would mean the alias is not additive). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan asserts a six-site edit makes every `runs` leaf accept `--repo` with no other effect. Accept the reasoning, or apply it? | Apply it as a throwaway probe, measure parser coverage, ten argv shapes, an end-to-end invocation, help rendering and the full suite, then revert. | (a) Accept the reasoning - rejected: "add a second option string" is plausible but says nothing about help rendering, abbreviation ambiguity, or whether the six sites are exhaustive, and all three were worth knowing before approving. (b) Read the parser and reason - rejected: reading found the sites but could not have found the `aw`-versus-package measurement trap, which is the finding most likely to waste an executor's time. | Probe at HEAD `47c0e0ca`: empty violation set from the coverage walk; `args.dir == R` for ten shapes; `runs --repo <tmp>` exit 0 with output identical to `--dir`; help line `--dir, --repo DIR`; `2436 passed, 1 skipped`; reverted with `git checkout`, `cli.py` byte-unchanged | yes |
| D-2 | `_register_run_leaf` gives the alias to the `aw run` WRITING leaves too. Accept that widening, or fork the helper to confine it to `runs`? | Accept it, and require a test for it. | (a) Fork the helper so only `runs` leaves get the alias - rejected: the helper's documented purpose is that the two surfaces cannot drift apart, and forking it to withhold a harmless additive alias trades a real structural property for a cosmetic boundary. (b) Accept it and leave it as prose, as the plan did - rejected: a declared consequence with no test is indistinguishable from an accident to the next reader, and nothing would catch a later leaf missing the alias. (c) Ask the maintainer - rejected: both nouns name a repository root, the flag lands in the same `args.dir`, and the measurement shows no other behavior change, so the repository answers it. | `_register_run_leaf` called for both `runs_sub` and `run_sub`; its docstring; the `_runs_viewer_flags` "cannot drift apart" comment (runnamecollapse `0soncw` E-03); probe measured `run start --repo R` -> `args.dir == R` | yes |
| D-3 | Should review decide the help-rendering question, or leave it open for the executor? | Decide it from measurement (argparse renders both, no work needed) and convert it into a VERIFY item rather than a build item. | (a) Leave it open as a question - rejected: it is answerable by running the code, and review ran it. (b) Add an item to write help text naming the alias - rejected as over-scope and actively harmful: argparse already renders it, so a hand-written mention would duplicate and could drift from the real option strings. (c) Say nothing, as the plan did - rejected: the purpose of the change is discoverability, so the one surface that delivers it must be checked. | In-tree `format_help()` output with the probe applied; the pre-existing `--last, --latest, -l [N]` and `--ipd, --id6 IPD` renders in the same parser; plain-argparse reproduction confirming the behavior is not repo-specific | yes |
