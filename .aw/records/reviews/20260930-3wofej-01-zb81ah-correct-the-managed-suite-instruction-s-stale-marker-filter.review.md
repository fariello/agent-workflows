# Review findings: plan zb81ah

- Subject-Id: zb81ah
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `37402c39`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `clean` with zero findings after revision (two advisory
`IPD-C801` citation hints that MY OWN first revision introduced were caught by that re-run and repaired,
which is a small argument for running the finalize lint rather than assuming a reviewer's edits are clean).
The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. `aw check` reports
no finding on this plan before or after.

THE PLAN IS GOOD AND ITS DIAGNOSIS IS RIGHT. Every claim I could re-measure reproduced: F-1's core drift
(`engine.py` emits `-m 'not slow'` while `addopts` configures `-m 'not slow and not livecorpus'`), F-3's
self-contradicting `pyproject.toml` comment, F-4's second `Makefile` phrasing, F-6's hardcoded notice
string, F-7's clean merge no-op, F-8's falsifiability proof, and F-10's targeted regression set. The
Carrier-Declined reasoning is substantive throughout, OQ-01 is correctly non-blocking and correctly left
to the maintainer, and E-01's insistence on re-deriving rather than quoting is the single best feature of
the plan: both its deselection figures and its suite baseline had ALREADY drifted by review (207 to 208,
202 to 203, and 3387 to 3506 passed), so a plan that had treated them as bars would have sent an executor
chasing phantom regressions. Four findings nonetheless go to real defects that would have shipped.

PR-001 IS THE ONE THAT MATTERS MOST, because the plan's title asserts completeness it did not have. The
census is EIGHT live sites, not four. Three `tests/test_*.py` module headers (`test_installer.py`,
`test_cli.py`, `test_leak_sanitizer.py`) each carry `excluded from the fast default run (see pyproject
addopts -m "not slow")`, and `Makefile`'s `test-all` comment is the fourth (see PR-002). The ROOT CAUSE is
diagnosable and repeatable, which is why I made E-01 mandate the fix rather than just adding the files:
the authoring sweep searched the SINGLE-quoted `-m 'not slow'`, and these three use the DOUBLE-quoted
`-m "not slow"`. Both spellings are live in this repository, and `pyproject.toml` itself uses the
double-quoted form in its comment while using the single-quoted form inside the `addopts` value, so a
one-spelling sweep is not a near miss but a guaranteed miss. Had this shipped as authored, the repository
would have corrected four of eight instances under a plan titled "and the three other sites repeating it",
which is a worse state than before in one specific way: a future reader finds an executed plan claiming
the class was swept.

PR-002 is the sharpest single error, because the plan FOUND the defect and then wrote a condition that
guaranteed it would not be fixed. E-04 said to correct `Makefile`'s `test-all` phrasing "if and only if it
is in the same comment block being edited". It is not: the two comments are separated by the `test:` target
and its tab-indented recipe. So F-4 was recorded as a finding and then fenced out by its own remedy. A
finding the plan raises and silently declines to fix is worse than one it never noticed, because the
record then claims coverage.

PR-003 and PR-004 are both about E-05, and together they mean the plan's one durable guard would have
shipped unable to do the job claimed for it. PR-003: the prescribed assertion "assert the two category
names appear as well, so E-02's naming requirement is what is pinned" is VACUOUS, and I measured it. The
corrected quoted expression is `not slow and not livecorpus`, which CONTAINS both category names as
substrings, so `'livecorpus' in prose` becomes True the instant the quoted string is corrected, whether or
not the categories are named as categories. The assertion can never distinguish the two outcomes it was
written to distinguish, which is exactly what GUIDING_PRINCIPLES forbids under "Never weaken an assertion
so it passes everywhere" and its citation of D78. V-02 compounded it by demanding the test prove naming.
The fix splits the two: the test asserts what a test can assert (the configured expression appears
verbatim, the stale fragment does not, and the expression is the one READ FROM `pyproject.toml` so that
changing `addopts` turns it red), and V-02 now requires a human to read the quoted clause and judge the
naming, which is where a prose-quality requirement belongs.

PR-004: E-05 sits in direct tension with the P16 paragraph the plan's own conventions section cites. P16's
first prohibition names `read_text()` and regex searches, and E-05 prescribes both. The exception is
AVAILABLE and the plan is in the right: `pyproject.toml` is configuration rather than `agent_workflows/*.py`,
and P16's narrow exception admits content verification "where the text or file itself is the artifact under
test", which is precisely a plan whose deliverable is instruction text. But the plan never makes that
argument, so the test ships looking like a violation to the next reader, who is entitled to delete it. The
argument now lives in E-05 and is required in the test's own docstring.

PR-005 is an API error that would have crashed the executor. E-03 says `merge_aw_block` "returns `action:
refreshed`", which invites `res.action`; the function returns a 2-TUPLE `(text, action)` and that attribute
access raises `AttributeError`. Worse, the consent warning E-03 makes its stop condition is neither printed
nor returned: `merge_aw_block` appends it to a list passed as the keyword-only `warnings=` parameter, which
the plan never mentions. So an executor following the plan literally would crash, and after fixing the
crash would be structurally unable to observe the one condition the item tells them to stop on. The fix
states the real signature, requires the tuple unpacked, requires an explicit `warnings=` list passed and
inspected, and cites `tests/test_section_consent.py::test_merge_aw_block_case_3_warning_forwarded` as the
test that pins the forwarding being relied on.

PR-006 closes a validation hole the new scope creates. The three test modules E-04 now edits are all
`slow`-marked, so they are absent from the bare run that every other validation item uses. A comment edit
that disturbed an import or a `pytestmark` line would therefore pass every check the plan specified. A
targeted `-o addopts=""` run over those three files is now required, and V-04 additionally requires each
`pytestmark` line pasted byte-identical, since changing one would alter selection, which this plan forbids
itself.

TWO FURTHER CORRECTIONS AND TWO SMALL ONES. PR-007: F-9's contention census named two pending plans and
missed the two that actually matter (`n9ua3b`, which declares BOTH `engine.py` and `AGENTS.md`, and
`b24o3q`, which declares `AGENTS.md`). The CONCLUSION survives, because neither contains any occurrence of
`HOW TO RUN THE SUITE` or `not slow`, but the evidence was thin for a claim about contention. PR-008
records a design tension the plan half-identified: the managed paragraph asserts a fact about THIS
repository's `addopts` while installing verbatim into targets whose `addopts` differ or are absent, so
correcting the quoted string makes the sentence true here and leaves it equally false in every target. The
plan's Deferred section rejects deriving at render time for exactly the right reason; what it never says is
that a residual inaccuracy remains, which is the strongest argument for naming the categories as a property
rather than only quoting a string. I recorded it as F-12 and as an under-scope note rather than expanding
the plan, because the same class of this-repo-specific claim already pervades the paragraph (the "4x to 6x
slower here" measurement, the `-q` compounding claim), so it predates this plan and is not one it can fix.
PR-009 adds the missing open-questions statement to the gate. PR-010 fixes the stale authoring figures that
survived into the gate's own honesty rule, and both E-01 and E-05 now assert over BOTH `target_layout`
values, since I measured the stale fragment present in `aw` AND `legacy` and a single-layout check would
leave half the installed surface unpinned.

NOTHING ELSE WAS FOUND WRONG. `Work-Kind: chore` with no `Blocks-Release` is correct and well argued: no
shipped behavior is wrong and no user waits, so it fails the user-perceptible-impact test for `bug`, and
the item it graduates from carries no gate to inherit. `From-Backlog: 3wofej` resolves to a `graduated`
item whose text I read and whose three asks (correct the literal, consider naming the categories, check for
other sites) the plan addresses in full. The AGENTS.md-is-generated convention is correctly identified and
correctly handled through the installer path. The refusal to edit terminal records under `.aw/records/` is
right. The refusal to derive the expression at render time is right and well reasoned. `AGENTS.md` is
additionally the ONLY markdown site in the repository (a repo-wide `--include='*.md'` grep excluding `.aw/`
returns it alone), so no README, CONTRIBUTING or `docs/` page is missing from scope. E-06's
`Carrier-Declined` reasoning (a carrier id6 cannot be cited before `aw backlog new` mints it, and V-06
refuses to pass without the created item's front matter) is the correct handling of that constraint.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric D (invariants), G (executability) | `tests/test_installer.py`, `tests/test_cli.py`, `tests/test_leak_sanitizer.py` module headers reading `excluded from the fast default run (see pyproject addopts -m "not slow")`; the two greps in F-2b | THE SITE CENSUS IS INCOMPLETE BY FOUR WHILE THE PLAN'S TITLE CLAIMS COMPLETENESS. Three test-module headers carry the same stale claim and were missed because the authoring sweep searched only the SINGLE-quoted `-m 'not slow'` while these use the DOUBLE-quoted form. As authored the plan would fix four of eight live sites under a title naming "the three other sites", leaving a future reader an executed plan that claims the class was swept. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Three files added to `- Scope-Paths:`; title and Concern corrected to seven other sites; E-04 extended to seven lettered sub-sites; E-01 now MANDATES a both-spellings sweep with the count reported and names the single-spelling error as the reason. New F-2 and F-2b record the census and its root cause. |
| PR-002 | HIGH | IN-SCOPE | Rubric G (executability) | plan E-04's "if and only if it is in the same comment block being edited" against `Makefile` lines 20 to 31 | THE PLAN FOUND F-4 AND THEN WROTE A CONDITION GUARANTEEING IT WOULD NOT BE FIXED. `Makefile`'s `test-all` comment describes `-m ""` as clearing "the default `not slow` filter" when it clears both categories. E-04 gated the fix on being in the same comment block as the `test` comment; measured, the two are separated by the `test:` target and its tab-indented recipe, so the condition is false and the recorded finding would have shipped unfixed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 sub-site (d) now corrects it UNCONDITIONALLY, with the false condition and its measurement named so the executor does not reinstate it. F-4 upgraded LOW to MEDIUM and rewritten to record that the plan's own condition was measurably false. V-04 requires the corrected comment pasted. |
| PR-003 | HIGH | IN-SCOPE | Rubric E (testing), P16 / GUIDING_PRINCIPLES | plan E-05's "assert the two category names appear as well"; measured substring behavior | THE PRESCRIBED NAMING ASSERTION IS VACUOUS AND CANNOT FAIL ON THE PROPERTY IT CLAIMS TO PIN. The corrected quoted expression `not slow and not livecorpus` CONTAINS both category names, so `'livecorpus' in prose` is True the instant the string is corrected, whether or not the categories are named as categories. Measured: for a quoted-string-only fix, both `expr in text` and `'livecorpus' in text` are True. This is the "never weaken an assertion so it passes everywhere" failure GUIDING_PRINCIPLES names via D78. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 now forbids that assertion explicitly, with the measurement, and prescribes three that can fail: the expression verbatim, the stale fragment ABSENT (verified a genuine flip), and a mutation-sensitivity property tying the assertion to the value read from `pyproject.toml`. V-02 takes over the naming check as a human reading of the quoted clause; V-05 requires a mutation demonstration and explicit confirmation the vacuous check is absent. New F-8b. |
| PR-004 | HIGH | IN-SCOPE | Rubric E (testing), project rule P16 | plan E-05 against `GUIDING_PRINCIPLES.md` section 16 ("Never use ... `read_text()`, or substring/regex searches against production code") and its narrow exception | E-05 COLLIDES WITH THE P16 PARAGRAPH THE PLAN'S OWN CONVENTIONS SECTION CITES, AND NEVER ARGUES THE EXCEPTION. The prescribed test does both prohibited things (reads a file, regexes it). The exception is available and the plan is substantively right (`pyproject.toml` is not `agent_workflows/*.py`, and the instruction TEXT is the artifact under test), but unargued the test ships looking like a violation and a later reader is entitled to delete it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now states the narrow-exception argument explicitly, names what remains forbidden (reading `engine.py` by any means), and REQUIRES the reasoning in the test's own docstring. V-05 requires that docstring pasted. New F-8c. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric A (correctness), G | `inspect.signature(engine.merge_aw_block)` returning `-> 'tuple[str, str]'` with keyword-only `warnings: Optional[list[str]] = None`; `tests/test_section_consent.py::test_merge_aw_block_case_3_warning_forwarded` | E-03 CITES THE API WRONG TWICE AND EITHER ERROR BREAKS IT. The function returns a 2-tuple, not an object with `.action`, so the plan's phrasing invites an `AttributeError`. And the consent warning E-03 makes its stop condition is neither printed nor returned: it is appended to a list passed as `warnings=`, which the plan never mentions, so a literal executor cannot observe the condition they are told to stop on. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now gives the real signature, requires `out, action = ...` unpacking, requires an explicit `warnings=` list passed AND inspected, and cites the consent test pinning the forwarding. V-03 refuses evidence that never passed a `warnings=` list. New F-7b. A fifth honesty trap warns the executor to trust observed signatures over this plan's prose. |
| PR-006 | MEDIUM | UNDER-SCOPE | Rubric E (testing) | `tests/test_installer.py`, `test_cli.py`, `test_leak_sanitizer.py` each carrying `pytestmark = pytest.mark.slow` | THE NEW SCOPE OPENS A VALIDATION HOLE. All three files E-04 now edits are `slow`-marked and therefore absent from the bare run every other validation item uses, so a comment edit that disturbed an import or a `pytestmark` line would pass every check the plan specified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a required `python3 -m pytest tests/test_installer.py tests/test_cli.py tests/test_leak_sanitizer.py -o addopts=""` run with its rationale; V-04 requires it pasted plus each `pytestmark` line byte-identical; the scope fence gains a fifth negative constraint forbidding any non-comment change in those files. |
| PR-007 | MEDIUM | IN-SCOPE | Step 1 evidence | pending plans `n9ua3b` (`- Status: reviewed`, declaring `agent_workflows/engine.py` AND `AGENTS.md`) and `b24o3q` (declaring `AGENTS.md`) | F-9's CONTENTION CENSUS MISSED THE TWO PLANS THAT ACTUALLY MATTER. It named `ypnk56`, `mvcwsd` and `kcc71f` and omitted the only two pending plans declaring this plan's two most sensitive paths. The conclusion survives, since neither contains `HOW TO RUN THE SUITE` or `not slow`, but the evidence did not support the claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-9 rewritten with the full sweep, naming both plans, their statuses, and the measured absence of the paragraph from each, with the unchanged conclusion stated as following from that measurement. |
| PR-008 | MEDIUM | IN-SCOPE | Rubric A (correctness), architecture | `agents_pointer_prose` being a pure function over a static literal with two in-`engine.py` callers; the paragraph's existing "4x to 6x slower here" and `-q` compounding claims | A REAL DESIGN TENSION IS HALF-IDENTIFIED AND ITS RESIDUE UNSTATED. The managed paragraph asserts a fact about THIS repository's `addopts` while installing verbatim into targets whose `addopts` differ or are absent, so correcting the quoted string makes it true here and leaves it equally false in every target. The plan rejects deriving at render time for the right reason but never says a residual inaccuracy remains, which is the strongest argument for naming the categories as a PROPERTY rather than only quoting a string. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | Recorded as new F-12 with the measurement that the same class of this-repo-specific claim already pervades the paragraph (so it predates this plan and is not one it can fix), and as an explicit under-scope note stating the residue is knowingly left and why E-02's naming requirement is therefore not cosmetic. |
| PR-009 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan gate as authored | THE GATE OMITTED THE OPEN-QUESTIONS STATEMENT, so a reader could not tell from the gate whether OQ-01 holds execution. It does not (`Blocking: no`, maintainer-owned, and every item is coherent under either answer), but the gate did not say so. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added an OPEN QUESTIONS paragraph to the gate stating OQ-01's state, its owner, and why no question gates execution. The path count in the scope fence was also corrected from six to nine. |
| PR-010 | LOW | IN-SCOPE | Rubric G (live-artifact criteria) | bare `python3 -m pytest` at review HEAD; `--collect-only` splits | THE AUTHORED FIGURES SURVIVED INTO THE GATE'S OWN HONESTY RULE, which told the executor not to match "this plan's `3387 passed` figure" while still printing it as the reference point, and F-5's deselection split had drifted too. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 and F-10 re-measured (`208` deselected, `203` slow, `5` livecorpus, `3506 passed, 2 skipped, 3 warnings in 132.98s`), the honesty rule now cites BOTH figures days apart to make the drift the argument, and E-01 and E-05 now assert over both `target_layout` values since review measured the stale fragment in each. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Three further sites were found. Add them to this plan's scope, or file them separately? | ADD them to this plan. | (a) File a follow-up item: rejected, because the plan's deliverable IS the completeness of the sweep (its title and its Concern both claim it), so splitting would ship a plan asserting a class was swept when it was not, which is the specific harm a half-fix causes here. (b) Narrow the title and leave them: rejected for the same reason plus the cost asymmetry, since they are three one-line comment edits in files already understood. | The backlog item's own closing ask ("Check whether any other managed text repeats the stale filter before assuming a single site"); the two greps in F-2b; the three files' identical header text. | yes |
| D-2 | E-05's naming assertion is vacuous. Strengthen the test, or move the naming check to human review? | MOVE it to V-02 (human reading of the quoted clause) and give the test three assertions that CAN fail. | (a) Write a cleverer substring test (for example requiring the word `livecorpus` outside the quoted span): rejected, it would pin prose SHAPE rather than behavior, is brittle against any rewording, and drifts toward the text-pinning P16 forbids. (b) Drop the naming requirement: rejected, it is the backlog item's own suggested fix and the part carrying the actual value (F-11, F-12). | Measured substring behavior on a simulated quoted-string-only fix; GUIDING_PRINCIPLES "Never weaken an assertion so it passes everywhere" and its D78 citation; P16's prohibition on text pins. | yes |
| D-3 | E-05 reads and regexes a file, which P16's first prohibition names. Permit it with an argument, or redesign the test? | PERMIT it, and require the argument in the test's docstring. | (a) Redesign to avoid reading `pyproject.toml` (for example hardcoding the expected expression): rejected, that destroys the only property worth testing, since a hardcoded constant cannot detect `addopts` drift, which is the entire defect class. (b) Mark the test `livecorpus`: rejected, P16's own guidance says to choose a marker for blast-radius isolation and never merely to quiet a location problem option one can eliminate, and `REPO_ROOT` anchoring eliminates it. | `GUIDING_PRINCIPLES.md` section 16's narrow exception ("where the text or file itself is the artifact under test") and its scoping of the prohibition to `agent_workflows/*.py`; the `leak_sanitizer.py` 3.9-safe reader precedent. | yes |
| D-4 | The managed paragraph is this-repo-specific but installs into every target (F-12). Expand scope to address it, or record it? | RECORD it as a finding and an under-scope note. | (a) Make the paragraph target-aware (derive or parameterize): rejected on the plan's own correct reasoning plus a measurement, since the paragraph ALREADY carries several this-repo-specific claims (the "4x to 6x slower here" figure, the `-q` compounding behavior), so the class predates this plan and fixing it properly is a redesign of what the managed block asserts, which is a maintainer's call. (b) Say nothing: rejected, a knowingly-left inaccuracy belongs in the record. | `agents_pointer_prose` signature and its two callers; the paragraph's own existing repo-specific sentences; the plan's Deferred row rejecting render-time derivation. | yes |
| D-5 | My own first revision introduced two advisory `IPD-C801` bare-offset citations. Repair or leave advisory? | REPAIR, by replacing the two `engine.py:NNNN` offsets with a described-symbol citation. | Leaving them: rejected, the plan's own `Project conventions` section states the rule and every other citation in the plan obeys it, so leaving reviewer-introduced violations in a plan that documents the convention would be incoherent. | `aw ipd lint --phase review-finalize` naming both, at line 111, after my first revision; spec `ipd-structure-and-linting` Section 10.2. | yes |

No `Reversible: no` decision was taken in this round. OQ-01 remains `open`, `Blocking: no`,
`Owner: maintainer`; it is not a finding left unfixed and so requires no escalation. Every finding is
`FIXED`.
