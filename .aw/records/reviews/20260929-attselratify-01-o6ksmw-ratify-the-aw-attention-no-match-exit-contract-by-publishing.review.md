# Review findings: plan o6ksmw

- Subject-Id: o6ksmw
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-901 (HIGH, fixed), PR-902 (HIGH, fixed), PR-903 (MEDIUM, fixed), PR-904 (MEDIUM, fixed), PR-905 (LOW, fixed)

## Round 1

Reviewed at HEAD `c1cacc29` in an isolated review lane. The plan file was already committed and identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming`, exit 0, with ZERO findings before semantic review, and `--phase
review-finalize --agent` still reports `conforming` with zero findings after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

THE PLAN'S CENTRAL CLAIM VERIFIES BYTE FOR BYTE AND ITS DOCUMENTATION FINDINGS ARE ITS BEST WORK, so I record
that before the findings. Driving all nine surfaces with a non-vocabulary token returned exit 2 on every one,
with the diagnostic on STDERR for the board, `--check` and the three list modes, on STDOUT for the three
machine modes, and a MEASURED 0 bytes of STDOUT for `-id`, `--paths` and `--filenames`, which is the
pipe-safety property the plan refuses to publish unchecked. The record carries exactly the shape F-01
describes: `kind: error`, `outcome: cannot-run`, `verified: false`, `complete: false`, `findings: 1`, both
`unresolved_selectors` and `unresolved_targets`, and NO `diagnostics` and NO `valid` key, so the refusal
genuinely does not travel the drift path. F-02 and F-03 quote their document correctly: Section 11.1 really
does mandate `outcome: "clean"`, `exit: 0`, `findings: 0`, `verified: true`, `complete: true` for "a query,
find, search, or list verb" matching zero records, Section 11.4 really does say invalid selectors MUST exit
`2`, and Section 12 really does claim `aw find` exits `1` on a zero-match selector while the verb measurably
exits 0 on both its human and `--agent` surfaces. F-04 is exact and is the strongest argument in the plan: all
five named symbols (`selector_vocabulary`, `refusable`, `selector_match_facts`,
`format_unresolved_selector_message`, `unresolved_selector_agent_record`) return ZERO hits across `tests/`.
F-05 is exact (74). F-06 is exact (`rg EXIT_UNRESOLVED_SELECTOR docs/ AGENTS.md README.md CHANGELOG.md`
returns nothing). F-07's spec quotes are real and the `aw runs` sibling really does exit 2. F-09 reproduces
(`ahlgnm --status done` and `ahlgnm -t plans` both exit 0). All five deferred-row carriers resolve. The
judgement to leave Section 12 to `hd5bkk` rather than replacing one wrong sentence with another is right, and
the plan's self-description as ratification rather than design is accurate.

PR-901 IS THE FINDING THAT WOULD HAVE STOPPED A CORRECT EXECUTION, AND IT IS AN INTERNAL CONTRADICTION THE
PLAN ALREADY CONTAINED. F-01 closes by asserting "Both exemptions hold: a bare invocation exits 0". In THIS
repository a bare `python3 -m agent_workflows attention` exits **1**, with `outcome: findings`, `findings: 5`,
from five pre-existing lane diagnostics (one `attention.lane-superseded`, four `attention.lane-stranded`). The
exemption is real, but what it exempts is the REFUSAL predicate; the ordinary drift exit code still applies
afterwards. I confirmed both halves: in the shipped drift-free fixture (`tests/test_attention.py::_attsel_repo`,
the same builder the existing pin uses) bare, bare `--agent`, bare `--check` and bare `--check --agent` all
exit 0, while in the live tree they exit 1. The plan's own F-08 measured exactly this and recorded `1` for the
same invocation class, so the two findings contradicted each other and nothing in the plan reconciled them.
This matters operationally rather than cosmetically: E-01 instructs the executor to drive the bare case and
V-01 states the bare exit code "must be 0", with the item's Expected outcome making any disagreement with F-01
a STOP. So an executor running this plan in this repository would have measured 1, found a documented stop
condition, and halted a correct plan against correct code, concluding the ratification question had changed
when nothing had moved. Worse, E-02 was instructed to PUBLISH the exempt side as "exits 0", which would have
minted a third falsifiable statement into the very document whose contradictions F-02 and F-03 exist to fix.

PR-902 IS A GAP BETWEEN THE PLAN'S STATED PROPERTY AND WHAT ITS TEST WOULD ACTUALLY COVER. E-03(1) enumerates
FOUR derivation sources; `selector_vocabulary` uses SIX, the two omitted being `_RUN_STATUS_ALIASES` (keys and
values) and `run_viewer.ABANDONED`. Measured: the four named sources cover 39 of the 74 tokens, adding
E-03(2)'s `TYPE_ALIASES` reaches 55, and the remaining 19 are all run-status words (`abandoned`, `completed`,
`dependency-blocked`, six `fail-*`, `failed`, `failed-safely`, `integration-blocked`, `interrupted`, three
`merge-*`, `not-run`, `partial`, `substantially-complete`). Two concrete consequences. First, E-03's stated
property, that "a value added to any of them joins the assertion automatically", would be FALSE for a new run
status, which is exactly the regression class the plan is written to prevent. Second, `abandoned` is one of
the four probe tokens E-01 uses to prove the exemption works across sources, so the plan would test a token
its own pin does not protect. I also noted a detail an implementer would trip on: `run_viewer.ABANDONED` is
the string `'abandoned?'` and production strips the trailing `?`, so a test must assert the stripped token and
read it through the symbol.

PR-903 IS A BITE TEST THAT DOES NOT BITE, WHICH IS WORSE THAN NO BITE TEST BECAUSE IT CERTIFIES FALSELY. V-03
instructs the executor to prove the source-coverage assertion bites by removing one derivation source and
showing a failure. Measured deltas from the 74-token baseline, by patching each source empty in memory:
`TRACKED_TREES` **0**, `ATTENTION_CLASSES` 1, `PRIORITIES` 3, `TYPE_ALIASES` 16, `CLASS_MAPS` 22. Emptying
`TRACKED_TREES` changes NOTHING, because every tree name is independently contributed by `TYPE_ALIASES`, so a
reviewer or executor who picks that source (the first one E-03 lists) watches the assertion pass against a
subject they just broke and records it as proof. Only `ATTENTION_CLASSES` contributes a unique token at all
(`ready`). I also folded in a smaller but related correction: V-03 as written invited a temporary EDIT of
`agent_workflows/attention.py`, a file deliberately outside `- Scope-Paths:` and forbidden by the plan's own
gate, with restoration afterwards. In-memory `patch.object` proves the identical property with no window in
which an interrupted turn leaves a modified production file behind, so the gate and the validation no longer
pull against each other.

PR-904 is that E-03(5)'s case-insensitivity assertion, taken literally, pins the wrong thing. The returned set
is lowercase-only, so `'REUSABLE' in attention.selector_vocabulary()` is False, while driving the verb with
`REUSABLE`, `Reusable` or `SHIPPED` exits 0. A membership-style assertion would either fail against correct
code or, written the other way, assert a property the set does not have; the exemption must be driven through
the call path.

PR-905 is a batch of stale live-state claims. Four deferred rows and the history line call carriers "open"
that are `graduated` at review (`hd5bkk`, `fyeg6a`, `rtbcok`, and `ahlgnm` itself, which this plan's own
authoring pass moved, its history reading "graduated by run run-20260928T235941Z-1396311: o6ksmw"); only
`5gmi12` is still `open`. F-07's description of spec `25kzda` Section 2.4a is also slightly broader than the
text, whose subject is `aw reviews` specifically and which generalizes to status selectors only in its closing
clause, so citing it as an existing rule for a 74-token derived vocabulary would overstate a narrow exception.
None of these changes a decision; all five are the kind of drift the plan's own conventions section warns
about, and the plan deserves credit for correcting the item's stale "63" the same way.

WHAT I CHECKED THAT PRODUCED NO FINDING. E-06's dash grep works as written (`grep -nP '[\x{2013}\x{2014}]'`
matches a real en dash and exits 1 on an empty diff). The `--check` premise E-04 rests on is true: the
`aw attention --check: the view is valid.` sentence is measurably absent from a refusing `--check`. `DECISIONS.md`
ends at D156 as E-05 says, and E-05 correctly instructs reading the next integer rather than assuming 157. The
CI step really does pass no selector, so F-08's conclusion that CI is unaffected stands even though its
mechanism is the drift path rather than the exemption. The `- Blocks-Release:` absence is correct: `ahlgnm`
carries none, and the plan rightly declines to invent one. OQ-02's resolution to amend Section 11.1 rather
than add a parallel section is well argued from the document's own mandate wording and I left it resolved.
OQ-01 is genuinely the maintainer's and is correctly non-blocking, since every deliverable here is needed on
either branch.

Bare suite at review HEAD: `3371 passed, 2 skipped, 3 warnings in 60.83s`. This review changed only the plan
and this review record; no production file was modified at any point, and every probe was an in-memory patch
or a throwaway repository under a gitignored `tmp/` path inside the lane.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | Rubric A (correctness), E (verification), G (live-artifact criteria) | Live tree: bare `python3 -m agent_workflows attention` exits 1, `outcome: findings`, `findings: 5` (one `attention.lane-superseded`, four `attention.lane-stranded`). Drift-free `tests/test_attention.py::_attsel_repo`: bare, `--agent`, `--check`, `--check --agent` all exit 0. F-08 independently measured 1 for the same class | F-01'S "A BARE INVOCATION EXITS 0" IS FALSE IN THIS REPOSITORY AND CONTRADICTS F-08. The exemption skips the REFUSAL, after which the ordinary drift exit code still applies, so the claim holds only in a drift-free tree. Because E-01's Expected outcome makes any disagreement with F-01 a STOP and V-01 says the bare code "must be 0", an executor would halt a correct plan against correct code. E-02 was also told to PUBLISH the exempt side as "exits 0", minting a third falsifiable claim into the document whose contradictions this plan exists to fix. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-01b with both measurements and the F-08 reconciliation; trimmed F-01's claim. E-01 now tests the exemption as "no refusal" (judge on `outcome` never `cannot-run` and `unresolved_selectors` absent), records both a live-tree and a drift-free-repo column, and its Expected outcome distinguishes a refusal-row divergence (STOP) from an exemption row at exit 1 (expected, do not stop). V-01 rewritten to match. E-02 must word the exempt side as NOT REFUSED with a drift-still-applies sentence; V-02 requires that sentence quoted. E-06/V-06 compare refusal rows only. |
| PR-902 | HIGH | IN-SCOPE | Rubric D (anti-regression), E (testing) | `selector_vocabulary` unions six sources. Measured coverage: four named sources 39/74; plus `TYPE_ALIASES` 55/74; the 19 uncovered are all run-status words. `run_viewer.ABANDONED == 'abandoned?'`, stripped in production | E-03 NAMES FOUR DERIVATION SOURCES WHERE THE FUNCTION USES SIX, leaving 19 of 74 tokens unpinned, every one a run-status word. So E-03's stated property that a value added to any source joins the assertion automatically would be FALSE for a new run status, the precise regression class the plan exists to prevent; and `abandoned`, one of E-01's four cross-source probe tokens, falls in the unpinned set, so the plan tests a token its own pin would not protect. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03(1) now enumerates all SIX sources with the measured coverage numbers and names the 19 uncovered tokens, requires asserting the STRIPPED `ABANDONED` token read through the symbol, and requires the `run_viewer` import guard to fail loudly rather than silently narrow the assertion. E-03's Expected outcome, the Proposed-changes list and Required-tests updated to six sources. |
| PR-903 | MEDIUM | IN-SCOPE | Rubric E (verification quality) | Measured per-source deltas from a 74 baseline by in-memory patching: `TRACKED_TREES` 0, `ATTENTION_CLASSES` 1, `PRIORITIES` 3, `TYPE_ALIASES` 16, `CLASS_MAPS` 22; only `ready` is unique to `ATTENTION_CLASSES` | V-03'S PRESCRIBED BITE TEST CAN CERTIFY FALSELY. Emptying `TRACKED_TREES`, the first source E-03 lists, changes the vocabulary by ZERO tokens because `TYPE_ALIASES` independently covers every tree name, so the assertion passes against a deliberately broken subject and the executor records that as proof it bites. Separately, V-03 invited a temporary EDIT of `agent_workflows/attention.py`, which the plan's own gate forbids and which leaves a window where an interrupted turn strands a modified production file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now requires in-memory `patch.object` instead of any file edit, names the measured deltas, directs the bite test at `CLASS_MAPS` or `TYPE_ALIASES`, and requires stating explicitly when a per-source assertion is coverage rather than a bite. The gate now says the production file is never edited even temporarily, and `git diff --stat` must be empty at every point. E-03's Expected outcome carries the same distinction. |
| PR-904 | MEDIUM | IN-SCOPE | Rubric E (testing), D | `'REUSABLE' in attention.selector_vocabulary()` is False (the set is lowercase-only); driving the verb with `REUSABLE`, `Reusable`, `SHIPPED` each exits 0 | E-03(5)'S CASE-INSENSITIVITY ASSERTION PINS THE WRONG SUBJECT. Taken as set membership it fails against correct code; written the other way it would assert a property the returned set does not have. The case-folding lives on the comparison path, not in the set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03(5) now requires driving the verb rather than testing membership, with both measurements recorded so the distinction is unmistakable; Required-tests restates it. |
| PR-905 | LOW | IN-SCOPE | Rubric G (live-artifact criteria), evidence accuracy | `aw find backlog` at review: `hd5bkk`, `fyeg6a`, `rtbcok` and `ahlgnm` are all `graduated`, not `open`; only `5gmi12` is `open`. `ahlgnm`'s history reads "graduated by run run-20260928T235941Z-1396311: o6ksmw". Spec `25kzda` 2.4a's subject sentence is about `aw reviews` | STALE LIVE-STATE CLAIMS. Four deferred rows and the history line call carriers "open" that are `graduated` (one of them moved by this plan's own authoring). F-07 also describes 2.4a as carving out status selectors generally, where the text is written about `aw reviews` and generalizes only in its closing clause, so citing it as an existing rule for a 74-token vocabulary overstates a narrow exception. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All five carrier references now state the status measured at review and flag where the earlier word was wrong. F-07 now requires E-02 to cite 2.4a as reasoning this verb ADOPTS and extends, naming its `reviews`-specific subject, and E-02's Expected outcome requires the subject not be overstated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-901: should the exemption be restated as "no refusal", or should E-01 simply be told to expect exit 1 in this tree? | RESTATE IT AS "NO REFUSAL" and test on `outcome`. | Tell E-01 to expect 1: rejected, because the correct expectation depends on tree drift at execution time, so a hardcoded 1 is exactly as wrong as the hardcoded 0 it replaces and would break the moment the lanes are cleaned up. Drop the bare case from E-01: rejected, it is half the contract being ratified. | Measured 1 in the live tree and 0 in `_attsel_repo`; `core.drift_exit_code` composing above the exemption as `attention.py`'s own preamble records ("2 dominates `core.drift_exit_code`'s 0/1"); the plan's own F-08 measuring 1 | yes |
| D-2 | PR-901: should E-02 publish an exit code for the exempt side at all? | PUBLISH "NOT REFUSED", plus a sentence saying a concurrent drift finding still reports itself. | Publish "exits 0" as originally instructed: rejected, a drifty repository falsifies it, and adding a fourth wrong statement to the document whose three contradictions this plan is fixing would be self-defeating. Say nothing about the exempt side: rejected, the discriminator is the whole deliverable and one side of it cannot be left unstated. | Section 11.1's existing mandate wording; the measured live-tree exit 1 for an exempt invocation; F-02 and F-03 establishing that this document's failure mode is precisely over-flat claims | yes |
| D-3 | PR-903: which derivation source should V-03's bite test target? | `CLASS_MAPS` or `TYPE_ALIASES`, with the redundancy of `TRACKED_TREES` stated. | Keep `TRACKED_TREES` as written: rejected, measured to be a zero-token no-op, so it certifies falsely. Require a bite test on every source: rejected, three of the six contribute 0, 1 and 3 unique tokens, so per-source bites are partly meaningless; naming which assertions are coverage versus bite is the honest shape. | Measured per-source deltas (0/1/3/16/22 from a 74 baseline); `ready` being the only token unique to `ATTENTION_CLASSES` | yes |
| D-4 | PR-903: is an in-memory patch an adequate substitute for a temporary source edit? | YES, and it is strictly better. | Temporary edit-and-restore as written: rejected, the file is outside `- Scope-Paths:` and forbidden by the plan's own gate, and an interrupted turn would strand a modified production file in a shared checkout. | The plan's own gate excluding `agent_workflows/attention.py`; `patch.object` demonstrated at review to produce the measured per-source deltas without touching the file; AGENTS.md's shared-checkout rule | yes |
| D-5 | Should OQ-01 (ratify or relax) be escalated to blocking, given the review found three execution-stopping defects? | NO; leave it non-blocking and `open`, owned by the maintainer. | Escalate to `- Blocking: yes`: rejected. All three defects were in HOW the plan measures and publishes, not in WHETHER the contract should be ratified, and all three are fixed. The plan's own argument that every deliverable is needed on either branch survives the review intact, so blocking would hold a plan that is executable either way. | The 2026-09-10 maintainer ruling that a non-blocking open question does not make a plan `NO-GO`; every finding carrying Decision `FIXED`; `ahlgnm` existing precisely to carry this question | yes |
| D-6 | Should this review itself resolve OQ-01 from the evidence it gathered, since it measured no harm from the fail-closed form? | NO. | Resolve it as ratified: rejected, and this is the clearest case in the review for not deciding. The question is a judgement about an interactive verb's exit code affecting a maintainer's own daily shell usage, the plan explicitly routes it to them, and `fqnj8k`'s execution contract already refused to guess it. A reviewer resolving it would substitute its preference for a maintainer's on exactly the axis AGENTS.md reserves to humans. | `fqnj8k`'s recorded refusal to guess a relaxation; AGENTS.md reserving scope, priority and risk-appetite calls to the human; the plan's OQ-01 `- Owner: maintainer` | yes |
