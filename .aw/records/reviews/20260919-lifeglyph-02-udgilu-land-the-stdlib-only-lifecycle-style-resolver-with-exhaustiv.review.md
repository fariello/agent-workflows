# Review findings: plan udgilu

- Subject-Id: udgilu
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `07dabf1b`. The plan on disk was byte-identical to the sealed lane input
(`sha256 a794daec...` for rev-2's sibling; this plan's own `diff` against rev-3 was empty), and
`git status --porcelain` was clean, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0.

THIS IS THE STRONGEST PLAN IN THE SET SO FAR AND ITS ARCHITECTURE IS RIGHT. A stdlib-only semantic
module with no ANSI, a precedence resolver that returns stage/status/activity separately and mutates
neither input, self-validation that refuses duplicate keys, and an owner-enum test that fails when a
status is added without a mapping: that is the correct shape for R10.1, and the deferrals are all
genuine (rendering to `bn026f`, depth to `pow5sj`, deletion to `qdd5jq`). Every Step 0 claim held:
`lifecycle_style.py` is absent, and all four palettes plus the three-hop re-export chain are live
exactly where cited (`term.py:117`, `attention.py:1403`, `render_stream.py:51`, `oc_runipd.py:104`,
`agy_runipd.py:104`, `runner_shared.py:168`).

WHERE THIS REVIEW SPENT ITS EFFORT: I re-derived the plan's two load-bearing numbers from the spec and
the code, and both were wrong. One is cosmetic-looking but would fail its own validation; the other makes
criterion A2 unsatisfiable and needs a maintainer ruling.

**1. A sixth orphan status exists, and A2 cannot pass without a ruling on it.** The spec's own
2026-09-13 review found five status words in no mapping table and fixed them. I ran the same check
against the runner's owner enum and found a sixth:

```text
runner_shutdown.KNOWN_ITEM_STATUSES   15 members
spec Section 7.2 rows                 covers 14
>>> OWNER statuses with NO spec row:  ['integration-deferred']
$ grep -c integration-deferred <uonrjg spec>   ->  0
$ grep integration-deferred <all 9 lifeglyph plans>  ->  0 matches
```

It is live and deliberately non-terminal: `runner_shared.INTEGRATION_DEFERRED_STATUS`
(`runner_shared.py:2478`) defines it, `runner_shutdown.py:87` files it under "in-flight / recoverable"
with a comment saying it is NOT terminal, and `oc_runipd.py:6123` repeats that it is deliberately absent
from `TERMINAL_STATES`. The spec's review could not have caught it because the plan that introduced it
(`integpath-03`/`51vw4y`) landed afterwards.

This is not a documentation nit: E-06's A2 assertion over that owner enum FAILS until it is mapped, and
all three ways to make it pass without a ruling are wrong. Excluding the member guts the test. Guessing
a stage writes an unreviewed presentation decision into the canonical module every other child consumes.
Letting it fall through to `unknown` produces the gray `?` that the spec's Section 6 preamble calls a
defect in so many words. The same question was escalated to the maintainer five times in this spec's own
review (D12 to D15 plus `quarantined`), each producing a recorded ruling with rejected alternatives, so
the sixth instance should not be settled silently by an executing agent. Escalated as OQ-02
`Blocking: yes`, with the evidence and a recommendation (`recovering`, since the status is in-flight with
a pending re-attempt rather than obstructed) so the ruling is cheap to give.

**2. The stage count is 20, not 21, and the wrong number had spread to three plans.** Parsed from the
normative Section 5 table:

```text
COUNT: 20
formative, review-queued, authority-queued, ready, reviewing, executing, verifying,
integrating, recovering, active, waiting-input, blocked, failed, done, reusable,
parked, superseded, abandoned, unknown, none
```

The spec corroborates this independently and twice: D13 and the Section 7.2 commentary on `ran` both
record rejecting "a new 21st stage", which only parses if the table holds 20. The wrong count sat in this
plan's Scope and E-01, and in `7p3tt8`'s E-03 ("the 21 stages") and E-04 ("a 22nd stage"). Left alone, a
correct implementation transcribing 20 spec rows would fail an E-01 that demands 21, and `7p3tt8`'s
legend drift-guard would be built around an off-by-one. Fixed here; the two `7p3tt8` occurrences are
flagged for that plan's own review since it is not in this ledger.

**3. OQ-01 was answerable at review, and answering it changed the plan twice.** The question asked which
owner enums are authoritative for A2 and deferred it to execution. I imported every candidate and diffed
it against the spec:

```text
plans     -> plans.RECOGNIZED                  9 members, spec 6.1 total (0 uncovered)
specs     -> attention_contract.SPEC_STATUSES  9 members, spec 6.2 total
research  -> research_contract.STATUSES        4 members, spec 6.4 total
backlog   -> backlog.STATUSES                  5 members, spec 6.3 total
releases  -> releases.RELEASE_STATUSES         3 members, spec 6.6 total
set state -> set_state.ALL_SET_STATES          7 members, spec 7.3 total
runner    -> runner_shutdown.KNOWN_ITEM_STATUSES  15 members, 1 UNCOVERED (finding 1)
```

Two consequences a restatement would have missed. Six of seven mappings are ALREADY total, so most of A2
is faithful transcription rather than discovery. And the question's premise ("each records tree has an
owner module that defines its status vocabulary") is FALSE for prompts: `prompts.py` defines only
`DEFAULT_STATUS = "pending"` and `PROMPT_KINDS`, with prompt status carried by DIRECTORY (the five
anchors at `ipd_lint.py:425`, matching the live `.aw/records/prompts/` subdirs). An agent resolving this
at execution would most likely have grepped for `prompts.STATUSES`, found nothing, and silently dropped a
family Section 6.5 explicitly maps, which is exactly the "test that passes while covering nothing"
outcome the question was recorded to prevent. Resolved, with the owner list and the prompts caveat written
into E-06.

**4. A shipped precedent for this exact test existed and went uncited.**
`tests/test_attention_contract.py`'s `MappingTotalityTests` already asserts
`set(CLASS_MAPS["plans"].keys()) == set(plans.RECOGNIZED)` and three siblings, and
`attention_contract.py:283-288` documents the lazy-import trick that keeps the contract module
dependency-light, which is the same tension E-06 faces between stdlib-only and importing owners. E-06 now
points at it. This is a KISS/reuse point rather than a defect.

**5. Smaller fixes.** V-01 said to diff the stage table "by eye", which for 20 rows times 4 fields is a
transcription slip waiting to happen; it now demands a mechanical comparison, the asserted row count, a
grep proving the emoji forms are absent (the code points alone do not prove absence), and greps proving
stdlib-only and no-ANSI. The Required-tests section gained a measured baseline. The gate gained a scope
fence, the honesty rule, OQ-02's disposition, and conditional finalize ownership in place of the
hand-rolled `git mv`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | A. correctness; D. anti-regression | Section 5 table parsed -> 20 rows; `uonrjg` D13 and Section 7.2 commentary both reject "a new 21st stage"; wrong count in this plan's Scope and E-01, and in `7p3tt8` E-03/E-04 | The plan asserts 21 semantic stages where the normative table holds 20. A correct implementation transcribing the spec would fail an E-01 demanding 21, and the error had propagated to four places across three plans | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Corrected to 20 in Scope and E-01, with the full stage list and both corroborating spec citations recorded; V-01 now asserts the count. `7p3tt8`'s two occurrences flagged for that plan's review (not in this ledger) |
| PR-202 | MEDIUM | IN-SCOPE | E. testing; F. do not ask what the repo answers | Imported all seven owners and diffed against the spec: six already total; `prompts.py:45,49` has no status enum; `ipd_lint.py:425` directory anchors | OQ-01 deferred to execution a question answerable by reading the repository, and its premise was false for prompts, so an executing agent would plausibly have dropped a mapped family and shipped a green test covering nothing | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Resolved at review; the seven owners and member counts written into E-06 with the prompts directory-derived caveat; OQ-01 `Status: open` -> `resolved`; V-06 now demands a per-family assertion |
| PR-203 | BLOCKER | UNDER-SCOPE | A. correctness; D. domain invariants | `runner_shutdown.py:87`; `runner_shared.py:2478`; `oc_runipd.py:6123`; `grep -c integration-deferred` on the spec -> 0, and on all nine Set plans -> 0 | A sixth orphan status exists that the spec's own review missed (it postdates that review). `runner_shutdown.KNOWN_ITEM_STATUSES` has 15 members and Section 7.2 covers 14, so criterion A2 and this plan's E-06 are unsatisfiable, and the three workarounds each gut the test, write an unreviewed decision into the canonical module, or produce the gray fallthrough Section 6 calls a defect | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | Escalated as OQ-02 `Blocking: yes` / `Finding: PR-203`, with the evidence, the two defensible candidates, and a recommendation (`recovering`). E-03, V-03 and the Spec-sync section carry the conditional one-row Section 7.2 amendment and the `Scope-Paths` declaration it would require |
| PR-204 | MEDIUM | IN-SCOPE | E. testing and verification | V-01 as authored ("diff it against spec Section 5's table by eye"); criterion A5 requires the emoji forms be ABSENT; R10.1 forbids ANSI and non-stdlib imports | V-01 relied on eyeball comparison of 80 values, and proved the text-presentation code points without proving the emoji forms absent, so A5 could pass while `⚠️` sat elsewhere in the module. The stdlib-only and no-ANSI constraints had no evidence demand at all | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-01 now demands a mechanical spec-table comparison, the row count, a grep proving the emoji forms absent, and greps proving stdlib-only imports and no `\033`/`\x1b` |
| PR-205 | LOW | UNDER-SCOPE | E. testing; evidence accuracy | Bare suite in this lane at `07dabf1b` -> `8369 passed, 3 skipped, 2 xfailed in 100.98s` | The plan required a bare suite run but recorded no baseline, so an executor meeting a pre-existing failure could not distinguish it from one it caused | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline recorded in Required tests with a compare-node-ids-not-totals rule and a note that this child ADDS tests so the total is expected to rise |
| PR-206 | LOW | UNDER-SCOPE | G. executability; execution contract | plan gate (original final paragraph): no scope fence, no honesty rule, hand-rolled `git mv` beside `aw ipd finalize` | The gate lacked a scope fence, the paste-the-actual-output honesty rule, and a statement of the open questions' disposition, and prescribed a hand-rolled `git mv` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries the fence (naming the consumers this child must not touch, plus the conditional spec path), the honesty MUST, both questions' disposition, one legitimate stop condition, and conditional runner/executor finalize ownership |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `integration-deferred` has no spec row, so A2 cannot pass. Pick a stage myself, or escalate? | ESCALATE as OQ-02 `Blocking: yes` with the evidence, the two defensible candidates, and a recommendation of `recovering`. Do not write a mapping. | (a) Map it to `recovering` on my own authority: rejected, this is a presentation-semantics decision on an `approved`, `Blocks-Release: next` spec, and the identical question was escalated to the maintainer five times in this spec's own review (D12 to D15 plus `quarantined`), each producing a recorded ruling; deciding the sixth silently would be inconsistent and would put an unreviewed decision into the module every other child consumes. (b) Exclude the member from the A2 assertion: rejected, that guts the one test whose purpose is to fail when a status lacks a mapping. (c) Let it fall through to `unknown`: rejected, the spec's Section 6 preamble calls a silent gray fallthrough for a known status a defect in exactly those words. (d) Amend Section 7.2 myself: rejected, reviewers do not author spec requirements, and the amendment needs a `Scope-Paths` declaration the plan does not yet carry. | `runner_shutdown.KNOWN_ITEM_STATUSES` 15 members vs 14 Section 7.2 rows; `grep -c` on the spec -> 0 and on all nine Set plans -> 0; `runner_shutdown.py:87` and `oc_runipd.py:6123` both state it is deliberately non-terminal; `runner_shared.py:2478`. | yes |
| D-2 | OQ-01 defers the owner-enum question to execution. Leave it, or resolve it from the repository? | RESOLVE at review: import every candidate, diff against the spec, and write the seven owners plus their member counts into E-06. | (a) Leave it for execution as authored: rejected, the workflow forbids asking (or deferring) what the repository answers, and resolving it surfaced two things execution would likely have gotten wrong (the prompts non-enum, and that six mappings are already total). (b) Name only the modules without the diff: rejected, the diff is what turned a vague instruction into a finding, since it is how `integration-deferred` surfaced at all. (c) Resolve it and delete the question: rejected, a resolved question with its rationale is the durable record; deleting it would hide that the premise was false. | Imports on 2026-09-19 of `plans.RECOGNIZED` (9), `attention_contract.SPEC_STATUSES` (9), `research_contract.STATUSES` (4), `backlog.STATUSES` (5), `releases.RELEASE_STATUSES` (3), `runner_shutdown.KNOWN_ITEM_STATUSES` (15), `set_state.ALL_SET_STATES` (7); `prompts.py:45,49`; `ipd_lint.py:425`. | yes |
| D-3 | The stage count is wrong in this plan and in `7p3tt8`. Fix both, or only the one under review? | FIX ONLY THIS PLAN and record the `7p3tt8` occurrences in the finding and the final report for that plan's own review. | (a) Fix `7p3tt8` too: rejected, it is not in this review's Step 0 ledger and the scope rule forbids expanding it; editing a plan I am not reviewing also leaves no review record attached to the change. (b) Say nothing about `7p3tt8`: rejected, the error is propagated rather than local, and its E-04 builds a legend drift-guard around the wrong number, so a reviewer of that plan needs to know. | Section 5 parsed to 20 rows; `uonrjg` D13 and the Section 7.2 `ran` commentary both reject "a new 21st stage"; `7p3tt8` E-03 "the 21 stages" and E-04 "a 22nd stage". | yes |
