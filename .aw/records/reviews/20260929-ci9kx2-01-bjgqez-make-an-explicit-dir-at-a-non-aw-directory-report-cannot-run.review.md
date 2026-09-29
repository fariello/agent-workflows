# Review findings: plan bjgqez

- Subject-Id: bjgqez
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `e7cc662c` in a lane worktree. Structural preflight `aw ipd lint --phase author`
reported `conforming` with ZERO diagnostics; after revision `--phase review-finalize` also reports
`conforming` with ZERO diagnostics. No pre-review snapshot was owed: the plan was committed and
unmodified, and the lane-input copy under `.aw/state/lane-inputs/rev-44/` is byte-identical (verified by
`diff`). NO PRODUCTION FILE, TEST, OR SPEC WAS MODIFIED by this review. Every measurement was a read, an
in-process call, or a subprocess run against throwaway fixtures under a temp directory, with `cwd` set
OUTSIDE any AW project exactly as F-10 requires, and using `python3 -m agent_workflows` with
`PYTHONPATH=<lane>` and `AW_NO_REEXEC=1` as the plan's measurement-discipline note prescribes. One
BACKLOG ITEM was annotated (`5gmi12`, via `aw backlog note`, status and gate untouched; see PR-701).

EVERY MEASURED CLAIM IN THIS PLAN REPRODUCES, and I re-drove all of them rather than sampling. F-01: the
same command exits 0 with `0 artifacts shown` and empty stderr WITH `--dir`, and exits 3 with the full
guidance on stderr WITHOUT it. F-03: `ipd board --dir <non-project>` prints
`✓ CLEAN  no plans found (no plans under <dir>)` plus `Next  aw ipd scaffold (scaffold a new plan)` at
exit 0, and `--agent` emits `outcome:"clean","exit":0,"next":"aw ipd scaffold"`. F-07: `attention --check
--dir` prints `aw attention --check: the view is valid.` at exit 0 and `--check --agent` emits
`outcome:"clean","verified":true,"exit":0`. F-11: a nonexistent path, a regular file, and a `.aw/`
holding only `state/` all exit 0, and `is_project_dir` is `False` for each. F-09: `ipd board --format
json` is rejected by argparse at exit 2. F-02: `tests/test_awretrofit_project_root_climb.py` is absent
and `NoProjectAgentEnvelopeTests._run_from_nowhere` does pass `dir=None`, so it cannot see this bug.
F-05: `validate_agent_record` returns the unsanitized-home-path finding for a home-rooted absolute
`next` and `[]` for both a temp-rooted one and the literal `.`. F-08: the git-root offer fires for an explicit directory and is
absent for a non-git one. F-06: `--dir <root>` reports `1 artifact shown`, `--dir <root>/src/deep`
reports `0 artifacts shown`, and no `--dir` from inside that subdirectory climbs and correctly reports
`1 artifact shown`, all three at exit 0. F-12: `exit_code=3` appears only in comment prose (four hits,
all assertions about the property) and `return 3` at exactly the two sites in scope. F-13: the only
constructed `--dir` in the package is the `gemini` CLI's own flag. F-14: the bare suite reports
`3246 passed, 2 skipped, 3 warnings`.

PR-701 IS THE FINDING THAT MATTERS, and it is a case of the plan being too modest about its own reach.
E-02 replaces `not explicit_dir and not is_project_dir(x)` with a plain `not is_project_dir(x)`. I
measured `is_project_dir(<root>/src/deep)` as `False` for a subdirectory of a real project, which means
the new guard catches the F-06 input too: after this plan, `--dir <subdir>` stops printing
`0 artifacts shown` at exit 0 and starts reporting cannot-run. The plan's Deferred row says that case is
"NOT in this plan's scope" and carries it entirely to `5gmi12`, and its Scope-check repeats that it "does
NOT fix the subdirectory under-reporting". Both readings are wrong about what the code will do. The
change itself is GOOD and arguably the most valuable part of the plan, since F-06 is the worse defect
(a plausible wrong answer beats an empty one for danger), and it is precisely why E-01's no-climb
sentence is load-bearing rather than decorative: the refusal is only diagnosable if the message explains
why a directory one level below a real root is not a project. But left as written, an executor measuring
the after-state would find an input changing that the plan told them was untouched, with no case in E-05
and no row in V-02 to confirm it was expected. I split the concern: the BEHAVIOR change is now in scope
and evidenced, while the RESOLUTION question (should `--dir` climb?) stays with `5gmi12`. Because that
narrows what the item still owns, I recorded it on the item with `aw backlog note` rather than only in
this plan, so the carrier's own record is accurate.

PR-702 IS SMALLER BUT HAS THE SAME SHAPE: the plan fixes one false sentence and leaves two. E-01 targets
the remedy (`or pass --dir <repo>`), which is right. It does not touch the SECOND line, `Checked <dir>
and its parents for a .aw/ ... directory`, which for an explicit `--dir` asserts a search that did not
happen; that is worse than the remedy, because it actively misleads the operator whose project root IS a
parent, i.e. exactly the F-06 case E-02 now refuses. And E-02 constrains the MACHINE summary only to
stay path-free, while that summary is a hardcoded literal reading `no AW project found at the working
directory or any ancestor; cd into the repository or pass --dir <repo>` at BOTH sites (measured
identical), so both halves are false for this case. Path-free is a necessary constraint, not a
sufficient one: a sanitized sentence can still be a lie. Both now branch, and V-01/V-02 require greps
proving neither false sentence survives, because an exit-code-only assertion would pass with both still
present.

I ALSO CHECKED THE ONE THING THAT WOULD MAKE OQ-01 UNSAFE and it holds. The resolution rests on "no
in-tree caller is affected", which F-13 argues from the library side. I checked the CI side too, which
the plan does not: `.github/workflows/tests.yml` has an `attention-check` job running `python -m
agent_workflows attention --check --agent` with NO `--dir`, i.e. exactly the climb path this plan leaves
byte-identical, and no `--dir` appears in `.pre-commit-config.yaml`. So the in-repository blast radius is
measured at zero on both surfaces, which is stronger support than the plan claims for itself. Recorded as
F-18.

WHAT I DELIBERATELY DID NOT FLAG. OQ-01's resolution is sound and unusually well argued: three published
rules (Section 3's cannot-run class, Section 11.4's no-silent-failure rule, the Anti-Greenwashing
Invariant) plus the attention spec's own `--check` sentence all point the same way, and I verified each
verbatim. The correction of the item's suggested flat exit 3 to the established 3/2 pair is right and the
reasoning (the schema admits only 0/1/2 and parity forces the machine exit to 2) is correct. The decision
NOT to widen `agent_schema`, NOT to add a `--check` flag to `ipd board`, and NOT to convert the other
`resolve_verb_repo_root` callers are each correct, and the third is explicitly honoring a documented
refusal to settle that question. E-04's instruction to say honestly whether it required a code change or
was satisfied by E-02's branch, "rather than manufacturing an edit to look busy", is exactly right. F-10's
measurement discipline is correct and I followed it; it would indeed have polluted a naive test with this
repository's own stranded lanes.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | MEDIUM | IN-SCOPE | A (correctness) / F (honest documentation) / E (testing) | plan E-02, its Deferred F-06 row, and its Scope-check; measured `is_project_dir(<root>/src/deep)` -> `False`; pre-change subprocess runs giving `--dir <root>` -> `1 artifact shown` and `--dir <root>/src/deep` -> `0 artifacts shown`, both exit 0 | THE GUARD CHANGE ALSO CONVERTS THE SUBDIRECTORY CASE THE PLAN SAYS IT DOES NOT TOUCH. A plain `not is_project_dir(x)` test catches `--dir <subdir of a real project>`, so that input stops under-reporting at exit 0 and starts refusing at 3/2. The change is a strict improvement, but the plan asserted the case was untouched and carried entirely to `5gmi12`, so an executor could not distinguish an expected conversion from a regression, E-05 had no case for it, and V-02 had no row | C:Low; U:Low; S:Low; F:Medium (the behavior is right; the plan's account of it was wrong, which is how a correct change gets reverted as a suspected regression); Overall:Medium | FIXED | E-02 now states the conversion, calls it a strict improvement, and ties it to why E-01's no-climb sentence is load-bearing. The Deferred row is re-scoped to the RESOLUTION question only (climb versus refuse) with the behavior change acknowledged. Scope-check corrected. E-05 gains the subdirectory case asserting the refusal beside the root's working answer; V-02 requires the row plus a written statement that it is expected. Backlog `5gmi12` ANNOTATED with `aw backlog note` recording the narrowing, status and gate untouched. New F-15 |
| PR-702 | MEDIUM | IN-SCOPE | F (honest documentation) / B | plan E-01 (remedy sentence only) and E-02 (path-free constraint only); measured the identical hardcoded summary at `attention.py` and `cli.py`; the rendered `no_project_message` carrying `Checked <dir> and its parents` | TWO MORE STRINGS ARE FALSE FOR AN EXPLICIT `--dir` THAN THE PLAN FIXES. The human message's SECOND line claims an ancestor search that did not happen (worse than the remedy, since it misleads exactly the operator whose root IS a parent), and the MACHINE summary hardcodes both falsehoods at both sites while E-02 required only that it stay path-free. A sanitized sentence can still be a lie, so path-free is necessary and not sufficient | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now branches BOTH sentences under `explicit=True` with the measurement quoted; E-02 requires the machine summary to be branched too, staying path-free. V-01 requires greps for `--dir <repo>` AND `and its parents` both returning nothing and calls a remedy-only check a fail; V-02 requires the machine summary check and calls a merely-path-free summary a fail. Expected outcomes for both items updated. New F-16 |
| PR-703 | LOW | IN-SCOPE | E (testing) | plan E-05's case list versus F-11's own enumeration | E-05'S CASE LIST OMITS ONE SHAPE ITS OWN FINDING NAMES. F-11 measures a `.aw/` holding only `state/` as a non-project that also exits 0 today, but the coverage list stops at a nonexistent path and a file. It is the cheapest guard against a future `is_project_dir` loosening and costs one fixture | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 gains the `.aw/`-with-only-`state/` case (re-measured at review as exit 0 with `is_project_dir` False); V-05's confirmation list updated |
| PR-704 | LOW | IN-SCOPE | E (testing) | plan E-05 and V-05 asserting exit codes and stream content generally, with no content assertion on the two corrected sentences | THE TEST COULD PASS WITH BOTH FALSE SENTENCES STILL PRESENT. E-05 asserts exit codes and "stream CONTENT" but names no specific string, so a fix that changed only the exit code while leaving `and its parents` and `pass --dir` in place would be green. The two sentences are the user-visible half of this defect | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires asserting the explicit human stderr does NOT contain `and its parents` and does NOT contain `pass --dir`, and the same for the machine summary. V-01 and V-02 require the corresponding greps |
| PR-705 | LOW | UNDER-SCOPE | G (execution contract) | plan gate as authored: an execution contract and a completion paragraph, but no scope fence and an unconditional terminal-move instruction | NO SCOPE FENCE AND NO CONDITIONAL FINALIZE OWNER. The plan's many load-bearing "do not touch" decisions (do not change `is_project_dir`, do not make `--dir` climb, do not widen the schema, do not add a flag, do not convert the other callers) lived only in item prose, so finalize reconciliation had nothing declared. Separately, the gate tells the executor to move the plan to `executed/`, which a worker-role process is refused from doing (`AW-LIFECYCLE-ROLE-001`, enforced inside the finalize transaction, so `aw ipd set executed` is refused too) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A SCOPE FENCE added as a DECLARATION (not a stop directive, per the 2026-09-01 ruling) naming eleven constraints, each traceable to a finding or a Deferred row. The completion paragraph now separates the unconditional finalize obligation from the conditional owner, names the enforcement site and the hand-execution invocation, and forbids both a hand-rolled `git mv` and a hand-edited `- Status:` |
| PR-706 | LOW | UNDER-SCOPE | G (approval gate) | plan gate's behavior-change paragraph, which names only "an `X` that is not an AW project" | THE APPROVAL PARAGRAPH UNDERSTATES WHICH INPUTS CHANGE. It frames the decision as being about a non-AW directory, but the guard tests `is_project_dir` on the named path, so the new refusal also covers a nonexistent path, a regular file, a `.aw/state`-only directory, and a SUBDIRECTORY OF A REAL PROJECT. A maintainer approving this should see the last one explicitly, since it is the input most likely to be typed by accident | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gains a paragraph naming the full changed input set with the subdirectory case called out and measured, stating that approving does not settle or foreclose the climb question (`5gmi12`); a paragraph bounding the risk with F-13 plus the new F-18 CI evidence; and a recorded right-sizing judgement noting the linter reports zero advisories |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is
owed (`check.review-finding-unescalated` satisfied vacuously). No BLOCKER and no HIGH was found: the
defect is real on four surfaces, the diagnosis is accurate to the guard line, the exit-code decision is
argued from published contracts rather than invented, and both MEDIUMs are accuracy defects in items
nobody has executed.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-02 measurably converts the F-06 subdirectory case the plan says it does not touch. Narrow E-02 to preserve the old behavior there, or acknowledge the conversion? | Acknowledge it, bring it in scope for behavior and evidence, and leave only the climb-versus-refuse decision with `5gmi12` | Narrowing E-02 to keep the subdirectory case at exit 0 (for example by testing `find_project_root` instead), rejected on two grounds: it would PRESERVE the worse defect (a plausible wrong answer) to protect the plan's scope prose, and it would make the guard inconsistent with the message E-01 writes, which explains the no-climb rule precisely so this refusal is diagnosable. Leaving the prose alone and letting the executor discover it, rejected because an unannounced behavior change is how a correct fix gets reverted | measured `is_project_dir(<root>/src/deep)` -> `False`; the three-way pre-change measurement showing the root reporting 1 artifact and the subdirectory reporting 0, both exit 0; `resolve_verb_repo_root`'s documented "honored verbatim (resolved, no climb)" rule, which the refusal is consistent with and a climb would contradict | yes |
| D-2 | The narrowing changes what carrier `5gmi12` still owns. Record it only in this plan, or on the item? | On the item, with `aw backlog note` (status and gate untouched) | Recording only in this plan, rejected on the durable-carrier rationale this repository already applies: once this plan reaches `executed/` the attention view maps it to `done`, so a narrowing recorded only here becomes invisible and the item keeps claiming a symptom that is already fixed. Using `aw backlog set` to change its status, rejected because the item is NOT done: its resolution question survives intact, and demoting or closing it would drop a live release-gated decision | `ipd_schema`'s durable-carrier comment; `aw backlog note`'s own contract ("record a reason rather than transition the item"); the item re-read at review as `open` / `bug` / `Blocks-Release: next` | yes |
| D-3 | The machine summary is a hardcoded literal at both sites. Branch it, or reuse `no_project_message` sanitized? | Branch the literal, keeping it path-free | Reusing `no_project_message` and stripping the path, rejected because the stripping would have to be done at both sites and a regex over prose is exactly the fragile coupling the existing comments avoided by writing a separate summary; the two strings serve different audiences (one names the directory, one must not) and keeping them separate is why the machine one is safe today | measured the identical literal at `attention.py` and `cli.py`; `validate_agent_record` refusing a `/home` path in `next` and accepting `.`; the existing site comments explaining why the summary is written separately | yes |
| D-4 | Three live source comments cite the deleted `tests/test_awretrofit_project_root_climb.py`. Fix them here? | No; record as F-17 and fence them out | Fixing them, rejected because every conclusion they state is still true and independently re-verifiable (I re-verified the `exit_code=3` absence and the git-blindness rule directly), so nothing is unsafe; the defect is a dead citation, and editing comment prose in three files to chase it would widen an exit-code change's diff for no failing test. Filing an item, rejected as below the bar: a stale citation inside a correct comment is not user-reachable, and F-17 plus the new test file are where a reader will find the live evidence | `ls` and `grep` confirming the file and both cited test names are absent; `git log --diff-filter=D` naming `19313eed`; the conclusions re-verified independently at review | yes |
| D-5 | Should OQ-01 be re-opened for the maintainer given it changes a published exit-code contract? | No; keep it resolved, and strengthen the approval paragraph instead | Re-opening as `- Blocking: yes`, rejected because the repository ANSWERS it: three published rules and one implemented spec all require the new behavior, the old exit 0 violates the Anti-Greenwashing Invariant outright (measured: `outcome:"clean","verified":true` about an unsurveyed tree), and the in-tree blast radius is now measured at zero on BOTH the library and CI surfaces. The judgement that remains is the maintainer's to make AT APPROVAL, which is where the plan already routes it, and a blocking question would stall a correct fix for a decision the approval gate already asks | `docs/cli-output-contract.md` Section 3, Section 11.4 and the Anti-Greenwashing Invariant, each read verbatim; the attention spec's Section 8.1 `--check` sentence and A5/G3; F-13 plus the new CI evidence in F-18 | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
