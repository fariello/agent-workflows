# Review findings: plan pow5sj

- Subject-Id: pow5sj
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `a5ab0515`. The plan on disk was byte-identical to the sealed lane input (`diff`
empty), and `git status --porcelain` was clean, so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS OWN F-03 IS THE BEST FINDING IN THE SET SO FAR. I verified
both headline claims: `grep -rn "COLORTERM\|256color" --include=*.py agent_workflows/` returns ZERO, and
`term.should_color` (`term.py:90-114`) returns a plain bool consulting only `NO_COLOR`, `FORCE_COLOR`,
`TERM` and `isatty()`. So the D42 ladder genuinely has no implementation. F-03 is also right and is the
kind of finding that saves an executor a mid-flight surprise: `ConfigKeySpec` carries only
`key`/`type_name`/`description`/`read_only` (`config.py:83-87`), so the spec's claim that configurability
is "a schema entry rather than a new mechanism" is half true, and A12c's "refused with a message naming
the accepted set" needs a constraint mechanism that does not exist. The plan pulled that INTO scope rather
than deferring it, which is the right call.

WHERE THIS REVIEW SPENT ITS EFFORT: the spec specifies this plan's single most important line twice, in
two adjacent sections, incompatibly, and the plan inherited one wording without noticing the other.

**1. R9.3a.2 and Section 9.3 contradict each other, and E-01 cannot be written until a human rules.**
R9.3a.2's top rung reads `NO_COLOR / --no-color / TERM=dumb / non-TTY -> none` and calls it "unchanged,
and unconditional", with commentary that `NO_COLOR` "is an accessibility convention and a preference may
not defeat it". Section 9.3, four lines earlier, requires the system "MUST preserve current `NO_COLOR`,
`FORCE_COLOR`, `TERM=dumb`, TTY ... behavior". Those are not compatible, because I measured the current
behavior by execution rather than by reading:

```text
NO_COLOR=1 AND FORCE_COLOR=1 on a fake TTY -> term.should_color(...) == True
```

implemented at `term.py:100-104` ("NO_COLOR: any value (even empty) disables, UNLESS FORCE_COLOR is set")
and PINNED by a shipped test, `tests/test_term.py:48-52::test_force_color_overrides_no_color`. So the word
"unchanged" in R9.3a.2 is false as written. Reading it literally changes documented behavior and deletes a
passing test; reading it as "unconditional with respect to the depth pin" preserves everything and still
delivers the accessibility promise the spec actually argues for. A12a's own text only ever contrasts
`NO_COLOR` with the PIN, never with `FORCE_COLOR`, which is weak evidence for the second reading, and that
is my recommendation. But it is a user-visible behavior question on an `approved`, `Blocks-Release: next`
spec, so it is escalated as OQ-02 `Blocking: yes` rather than decided here.

**2. The resolver's top rung spans two layers, and E-01 as authored invited putting it in the wrong
one.** E-01 said only "beside `should_color`", listing `--no-color` among the inputs. But `should_color`
cannot see that flag: it reads env and `isatty()` only, and the flag is applied one layer up, in
`result_types.select_output`, which computes color `if not getattr(args, "no_color", False)`
(`result_types.py:158-160`). An agent implementing E-01 literally would either add argparse awareness to
`term.py` (wrong layer, and it fights the flag-above-env layering that `yaxr4i` E-03 exists to establish)
or quietly drop the flag from the chain. E-01 now records both facts, plus that `should_color` has 38 call
sites across 7 modules so the new signature must not force a change at any of them.

**3. Two counted quantities were taken from prose and are wrong.** The plan says "21 stages" twice;
Section 5's table holds 20, and the spec's own D13 rejects "a new 21st stage", which only parses at 20.
Separately, R9.3a.3 says "the four grays" and then lists SIX names, which I settled by measuring the 256
tier:

```text
DISTINCT 256 indices: 11
   220: reviewing, executing, verifying, integrating, recovering, active
   244: parked, superseded, abandoned, unknown, none
   245: formative
```

The list is right and the word is wrong: six stages collapse into the one neutral, not four. The 11-index
count R9.3a.3 asserts is exactly right, which is worth stating because it is the number that justifies
forbidding a derived palette. Left uncorrected, V-02's dump would have asserted a stage count that cannot
hold and the neutral collapse would have been built for four of six stages.

**4. Smaller additions.** Required tests now points at the shipped harness rather than leaving an executor
to invent one: `tests/test_term.py:38-65` already has `_FakeTTY()`/`_FakePipe()` doubles and a `_clear()`
env helper exercising exactly the `NO_COLOR`/`FORCE_COLOR`/`TERM=dumb`/isatty matrix the per-rung A12a
tests need. A measured baseline was added, with `test_force_color_overrides_no_color` called out as the
node id to watch since OQ-02 decides its fate. The gate gained a scope fence (including that this child
must not delete `term.py`'s `STATUS_COLOR_256`, which is `qdd5jq`'s work), the honesty rule, both
questions' disposition, and conditional finalize ownership. I also re-verified the plan's claim that the
accessibility lens was already corrected: it holds at `accessibility.md:56-65`, including the sentence
"`NO_COLOR` still wins over any such setting", which is itself evidence for OQ-02's recommended reading.

I left OQ-01 OPEN and non-blocking as authored. It is a genuine implementation choice between extending
`ConfigKeySpec` declaratively and validating at the setter, both routes satisfy A12c, and E-03/V-03
already require the chosen route be named in evidence. Resolving it for the executor would be
over-prescribing an internal shape the code should decide.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | BLOCKER | IN-SCOPE | A. correctness; B. accessibility convention | Measured by execution: `NO_COLOR=1`+`FORCE_COLOR=1` on a fake TTY -> `should_color` True; `term.py:100-104`; `tests/test_term.py:48-52`; spec R9.3a.2 versus Section 9.3 | The spec specifies E-01's top rung twice and incompatibly: R9.3a.2 calls `NO_COLOR -> none` "unchanged, and unconditional" while Section 9.3 requires preserving current `FORCE_COLOR` behavior, and current behavior lets `FORCE_COLOR` defeat `NO_COLOR`. The literal reading changes documented behavior and breaks a shipped test; the plan inherited one wording without reconciling the other | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | FIXED | RESOLVED 2026-09-19 by maintainer ruling as READING A: `FORCE_COLOR` keeps its escape hatch over `NO_COLOR`, `tests/test_term.py:48` keeps passing, and no behavior changes. The ruling went wider than the finding: `NO_COLOR` is presence-only (any setting disables, empty included) for CONSISTENCY WITH `rg`/`bat`/`fd`, which are unanimous that any non-empty value disables; `FORCE_COLOR` interprets falsey values per the Node convention, so `FORCE_COLOR=0` falls through to TTY detection instead of forcing. Those two, plus the three divergent `should_color` implementations, are filed as backlog `nyz8dt` (`Work-Kind: bug`, `Blocks-Release: next`) because they are a pre-existing defect in files this Set does not own |
| PR-302 | MEDIUM | IN-SCOPE | C. architecture; G. executability | `term.py:90-114` (no flag awareness); `result_types.py:158-160` (flag applied here); `grep -c should_color` -> 38 sites in 7 modules | E-01 listed `--no-color` in a resolver placed "beside `should_color`", but that function cannot see the flag. Implemented literally it would either add argparse awareness to `term.py` or silently drop the flag from the precedence chain | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now records the two-layer seam, forbids argparse awareness in `term.py`, and notes the 38 call sites must not change; V-01 demands a grep proving both |
| PR-303 | MEDIUM | IN-SCOPE | A. correctness; E. verification | Section 5 parsed -> 20 rows and 11 distinct indices; `uonrjg` D13; spec line 484 "the four grays (`parked`, `superseded`, `abandoned`, `unknown`, `none`, `formative`)" | Two counts inherited from prose are wrong: "21 stages" (twice; the table holds 20) and R9.3a.3's "four grays" beside its own six-name list. V-02 would have asserted an impossible count and the neutral collapse would cover four of six stages | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Corrected to 20 and to six gray-family stages throughout, with the measured 256-tier grouping recorded in E-02 and V-02 asserting both |
| PR-304 | LOW | UNDER-SCOPE | E. testing; reuse | `tests/test_term.py:38-65` (`_FakeTTY`/`_FakePipe`/`_clear` harness); baseline `8369 passed, 3 skipped, 2 xfailed` at `a5ab0515` | The plan required per-rung tests without pointing at the shipped harness that already exercises this exact matrix, and recorded no suite baseline, so an executor could invent a second stream-double pattern and could not distinguish a pre-existing failure | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests now cites the harness by path and line, carries the baseline with a compare-node-ids rule, and names the one test whose fate OQ-02 decides |
| PR-305 | LOW | UNDER-SCOPE | G. executability; execution contract | plan gate (original final paragraph) | The gate lacked a scope fence, the paste-the-actual-output honesty rule, and the open questions' disposition, and prescribed a hand-rolled `git mv` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries the fence (naming the `STATUS_COLOR_256` deletion as `qdd5jq`'s), the honesty MUST, both questions' disposition, one legitimate stop condition, conditional finalize ownership, and the measured reason both dependency edges are load-bearing |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The spec contradicts itself on whether `FORCE_COLOR` still beats `NO_COLOR`. Pick the reading myself, or escalate? | ESCALATE as OQ-02 `Blocking: yes`, with the measurement, both readings, and a recommendation to preserve current behavior. Do not write the rung. | (a) Implement the conservative reading (preserve `FORCE_COLOR`) silently: rejected even though it is my recommendation, because R9.3a.2 says "unconditional" in as many words, and quietly choosing the other reading would leave the canonical resolver contradicting the spec text with no record of why. (b) Implement the literal reading: rejected, it changes documented user-visible behavior and deletes a shipped passing test, which is a decision no reviewer should take on an `approved`, release-gating spec. (c) Amend the spec myself to remove the contradiction: rejected, reviewers do not author spec requirements, and the amendment needs a `Scope-Paths` declaration the plan does not carry. (d) Treat it as non-blocking and let the executor choose: rejected, the two readings produce different code, different tests, and different shipped behavior, which is the definition of a decision that must not be made mid-execution. | Measured `NO_COLOR=1`+`FORCE_COLOR=1` -> `should_color` True; `term.py:100-104`; `tests/test_term.py:48-52::test_force_color_overrides_no_color`; spec R9.3a.2 ("unchanged, and unconditional") versus Section 9.3 ("MUST preserve current ... `FORCE_COLOR` ... behavior"); A12a contrasts `NO_COLOR` only with the pin; `accessibility.md:64-65` ("`NO_COLOR` still wins over any such setting"). | yes |
| D-2 | R9.3a.3 says "four grays" but lists six names. Follow the word or the list? | FOLLOW THE LIST (six), and record the measurement that settles it plus a conditional spec correction. | (a) Follow the word "four": rejected, it would leave two stages uncollapsed and the measurement disproves it. (b) Leave the ambiguity for the executor: rejected, the collapse assertions are what pin the 16-color table against later re-expansion, so an off-by-two there defeats the test's purpose. (c) Amend the spec now: rejected as not the reviewer's to author, but recorded as a conditional edit with its `Scope-Paths` obligation. | Section 5 parsed: 244 holds `parked`/`superseded`/`abandoned`/`unknown`/`none` and 245 holds `formative`, so six stages share one neutral; 11 distinct indices total, matching R9.3a.3's own count. | yes |
| D-3 | OQ-01 (extend `ConfigKeySpec` versus validate at the setter) is left open. Resolve it from the code, or leave it? | LEAVE OPEN and non-blocking, as authored. | (a) Resolve it to the declarative route: rejected, both routes satisfy A12c, the choice is an internal-shape judgement better made against the code being written, and E-03/V-03 already force the chosen route to be named in evidence. Prescribing it would be over-specifying an implementation detail, which is the failure the plan-review rubric warns about under KISS. (b) Make it blocking: rejected, nothing user-visible or irreversible turns on it and the plan cannot stall on an implementation preference. | `config.py:83-87` (`ConfigKeySpec` has no allowed-values field); `_ALLOWED_REPOS_KEYS` at `config.py:652,973` is the shipped bespoke-check precedent; A12c requires only that the refusal NAME the accepted set. | yes |
