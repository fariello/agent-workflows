# Review findings: plan dmjp0u

- Subject-Id: dmjp0u
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-401 (BLOCKER, fixed), PR-402 (HIGH, fixed), PR-403 (MEDIUM, fixed), PR-404 (MEDIUM, fixed), PR-405 (MEDIUM, fixed), PR-406 (LOW, fixed), PR-407 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and byte-identical to the lane input
(`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
`--phase review-finalize --agent` reports `clean` with zero findings after revision. The plan's own first
`- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator row check does not apply.

THE PLAN'S CENTRAL JUDGEMENT IS RIGHT AND ITS HARDEST PART IS ALREADY DONE. The genuinely difficult thing
about applying P15 to a comment sweep is knowing what NOT to touch, and this plan gets that right before
review touches it: it identifies that the anti-malice vocabulary is densest in the COMPLIANT sites, it
fences off the three disclaimers by name, and it refuses to add a test on the correct grounds that a
docstring pin is what P16 forbids. All three fenced sites are real and all three are P15's own cited model:

- `runner_shared`'s baseline banner, four numbered reasons ending "THE TARGET IS SLOPPINESS, NOT MALICE",
  whose reason 3 is "A GENUINELY MALICIOUS AGENT WOULD REWRITE THE GATE. It has write access to this file."
- `host_sandbox_profile`'s docstring: "it is explicitly NOT a boundary against a MALICIOUS same-user
  worker".
- `attention_contract`'s `--by-human` note: "a conscious speed bump recording attributed human approval;
  NOT anti-malicious crypto".

Both target sites also reproduce verbatim. `ipd_lifecycle:4383` reads "hard enforcement against a
determined same-user agent requires an OS sandbox or separate principal", and `orchestrate_isolation`'s
module docstring reads "E-04: Seeded orchestration adversarial protections against role collisions, leaked
prose, unauthorized mutations, shared-worktree conflicts, stale branches, lane timeouts, and unsafe
background completions". F-4's claim that the module already models the P15-correct voice reproduces too:
"CRUCIAL: Per-lane green NEVER implies integrated green!" at line 1159.

THE DOMINANT FINDING IS THAT THE PLAN WAS UNEXECUTABLE AS WRITTEN (PR-401), and it is the same class of
defect that review found in both siblings: a declared mechanical step that does not produce the input the
next step consumes. E-01 declared the census family `malicious`, `determined same-user`, `hostile`,
`adversarial`. The F-2 site is three comment lines reading:

```
# HONEST LIMIT: this is an environment SELECTOR, i.e. the operational-default guidance layer, not a
# hardened boundary. A same-user worker with shell access can unset the variable. Hard enforcement is
# an OS sandbox / separate principal (x03wgn, Phase 6 `1o4eif`).
```

Grepping those three lines for the declared family returns ZERO matches. So an executor who ran exactly
the authored census would produce a target list from which one of the plan's own two named `ipd_lifecycle`
subjects is ABSENT, and would then reach E-03, which instructs them to edit it. Measured across
`agent_workflows/*.py`, `determined same-user` matches exactly ONE line in the entire package
(`ipd_lifecycle:4383`), which is F-1. The plan's own fact 2 even quotes F-2's text, so the gap is between
the plan's prose and its mechanical step, not in its understanding. Fixed by adding a FRAMING family
(`hard enforcement`, `hardened boundary`, `real fix`, `separate principal`, pointers at `1o4eif` or
`host_sandbox_profile`) beside the vocabulary one, and by making V-01 fail the item outright if the pasted
census does not contain F-2. That last part matters more than the family list: it converts the fix from a
better grep, which the next executor could still get wrong, into a property the validation checks.

THE SECOND FINDING RESHAPES THE PLAN'S SEQUENCING (PR-402). E-02 and OQ-02 are both written as "check
whether backlog `dvonrn` has landed", but `dvonrn` is `- Status: graduated` with `- Graduated-To: lifegate`
and its D1/D7 work now lives in four pending plans. The one that matters is `e25iy9`, whose E-04 reads, in
as many words: "Also remove the honest-limit comment block that names the token and points at `1o4eif` as
the fix for a 'determined same-user agent'". That is the F-1 site, so F-1 has TWO declared owners, and
`e25iy9` carries `- Blocks-Release: next` with `- Work-Kind: bug` and `- Priority: high` against this
plan's `chore`/`low`. The authored E-02 would have had the executor check for the token and then reframe a
comment that a higher-priority sibling intends to delete. Fixed by rewriting E-02 to read the state from
the four plans rather than the item and to resolve F-1 to a definite disposition in BOTH states: if the
token symbols are gone, record F-1 as closed by `e25iy9` and do not re-add a comment where the code no
longer exists; if present, reframe it WITHOUT naming the token so the later deletion removes it cleanly.
Also established, and worth recording because it bounds the collision: F-2 and F-3 are unambiguously this
plan's. No sibling declares the role-gate selector block, `e25iy9`'s E-09 keeps spec `7ckptx` R4.5's
matching honest-limit sentence VERBATIM, and no plan in either Set touches `orchestrate_isolation` at all.

THE THIRD FINDING IS THAT THE CLASSIFICATION SCHEME COULD NOT CLASSIFY ITS OWN CENSUS (PR-403). E-01
offered exactly three classes and required the counts to sum to the total. Measured over
`agent_workflows/*.py`, the vocabulary family returns 30 hits and 25 of them fit none of the three:

| Class | Hits | What they are |
|---|---|---|
| benchmark taxonomy | 14 | `benchmark_scorer`/`benchmark_metrics` `ADVERSARIAL_CLASSES`, a corpus of seeded false-completion cases |
| hostile INPUT data | 8 | `run_analytics_*` on a malformed JSON value, a manifest path, an undecodable byte |
| dangling test filename | 3 | `wtiso_gate` citing `tests/test_wtiso_adversarial.py`, which Order 02 deletes |
| DISCLAIMER | 3 | the three fenced sites |
| JUSTIFICATION | 2 | F-1 and F-3, this plan's actual subject |
| TOTAL | 30 | |

So the defect-to-noise ratio is 2 in 30, which strengthens the plan's own fact 4 rather than contradicting
it, but the three-class scheme would have forced 25 hits into a wrong class or silently dropped them from
the sum. Note also that `tamper` and `forge`, the words the INTEGRITY-OR-CLAIM class exists to catch, are
not in the declared family at all, so that class was unreachable by the declared search. Fixed by adding
HOSTILE-INPUT and VOCABULARY-ONLY classes and by widening the vocabulary family to include `malice`,
`adversary`, `tamper`, `forge` and `deception`.

TWO SMALLER CORRECTIONS. F-10 asserted that `orchestrate_isolation` "exports exception classes" carrying
the vocabulary; an AST walk of the module finds NO symbol carrying any of it, and its twelve exception
classes are named for the CONDITION (`StaleBaseError`, `LaneExecutionTimeoutError`,
`CombinedRevalidationFailedError`), which is already the P15-correct style. The real instances are
`benchmark_scorer`'s `ADVERSARIAL_CLASSES` and `adversary_class`, correctly out of scope as a data
taxonomy. The row now reports the measurement, and E-04 hands the executor the census result instead of
implying a hunt that finds nothing. Separately, `tests/test_orchestrate_isolation.py` carries the
near-identical line "E-04 / V-04: Seeded orchestration adversarial suite" while sitting OUTSIDE
`- Scope-Paths:`, so an executor sweeping the phrase will find it; E-04 now forbids the edit and states why
the word is accurate there (the suite genuinely does seed adversarial cases) while being a misnomer in the
production module, which claims the protections THEMSELVES are adversarial.

WHAT I CHECKED AND FOUND SOUND, recorded so a later reader knows it was tested rather than assumed. The
no-test decision is correct: P16 forbids asserting "that exact phrases, warning banners, or docstrings
exist in production files", so there is no conforming test for a reworded comment, and the plan's diffs
plus an unchanged suite are the right evidence. The no-spec claim holds: searching the specs tree for both
changed phrases returns nothing normative, and spec `7ckptx` R4.5's "an environment selector and not a
hardened boundary" is a DISCLAIMER that `dvonrn` D8 measured as already P15-conforming. The P13 reasoning
holds: every edited site is a code comment or docstring, which P13 lists explicitly as not user-facing. The
`kcc71f` fence is real (`20260929-aced01-01-kcc71f-...` exists in `pending/`), so the baseline-banner
correction genuinely has its own carrier. And the `chore`/`low` classification is right under the
AGENTS.md perceptibility test: nothing a user perceives changes and no operator waits on anything.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | BLOCKER | IN-SCOPE | G (plan executability) | plan E-01; `agent_workflows/ipd_lifecycle.py:66` (the F-2 comment block) | E-01's declared census family (`malicious`, `determined same-user`, `hostile`, `adversarial`) matches NOTHING in the F-2 site, whose words are "not a hardened boundary" / "can unset the variable" / "Hard enforcement is an OS sandbox / separate principal". An executor running the authored census builds a target list missing one of the plan's own two named subjects, then E-03 tells them to edit it. `determined same-user` matches exactly one line package-wide, which is F-1 | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now searches a VOCABULARY family plus a FRAMING family (`hard enforcement`, `hardened boundary`, `real fix`, `separate principal`, `1o4eif` pointers); V-01 FAILS the item if the pasted census does not contain F-2; fact 2 records why |
| PR-402 | HIGH | IN-SCOPE | C (architecture/ownership) | plan E-02, OQ-02, F-8; `.aw/records/backlog/graduated/20260926-lifegate-01-dvonrn-...backlog.md:2`; `.aw/records/plans/pending/20260930-lifegate-02-e25iy9-...ipd.md:116` | E-02 and OQ-02 treat `dvonrn` as a live backlog item to check, but it is `graduated` into Set `lifegate`, and its child `e25iy9` E-04 explicitly declares the F-1 comment ("Also remove the honest-limit comment block that names the token and points at `1o4eif` as the fix for a 'determined same-user agent'"). F-1 is double-declared, and `e25iy9` is `bug`/`high`/`Blocks-Release: next` against this plan's `chore`/`low` | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 rewritten to read state from the four `lifegate` plans and to resolve F-1 in BOTH states (closed by `e25iy9` if the token is gone, reframed token-free if present); V-02 requires the disposition be stated; F-8 and F-12 record the overlap; the deferred section names `e25iy9` as carrier |
| PR-403 | MEDIUM | IN-SCOPE | G (plan executability) | plan E-01, V-01 | The three-class scheme cannot classify its own census: 25 of 30 vocabulary hits are neither JUSTIFICATION, DISCLAIMER nor INTEGRITY-OR-CLAIM (14 benchmark taxonomy, 8 hostile input data, 3 dangling test filenames), yet E-01 requires the counts to sum to the total. `tamper`/`forge`, the words INTEGRITY-OR-CLAIM exists for, were not even in the declared family | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added HOSTILE-INPUT and VOCABULARY-ONLY classes (five total), widened the vocabulary family to include `malice`, `adversary`, `tamper`, `forge`, `deception`, and recorded the measured distribution in fact 4 and the scope check |
| PR-404 | MEDIUM | IN-SCOPE | D (anti-regression) | plan E-04; `tests/test_orchestrate_isolation.py:16` | The test module's docstring carries the near-identical "Seeded orchestration adversarial suite" line while the file is NOT in `- Scope-Paths:`, so a phrase sweep finds it and an executor may edit an undeclared path | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 forbids the edit, explains why the word is ACCURATE in a test that really does seed adversarial cases, and requires the sighting be recorded; V-04 requires the diff show the test file absent; F-13 records it |
| PR-405 | MEDIUM | IN-SCOPE | B (evidence accuracy) | plan F-10; AST walk of `agent_workflows/orchestrate_isolation.py` | F-10 implies `orchestrate_isolation` exports vocabulary-carrying exception classes. It exports NONE; all twelve are named for the condition (`StaleBaseError`, `LaneExecutionTimeoutError`). The real instances are `benchmark_scorer`'s `ADVERSARIAL_CLASSES`/`adversary_class` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 now reports the measured census; E-04 hands the executor the result and asks for confirmation rather than implying a hunt that finds nothing |
| PR-406 | LOW | IN-SCOPE | F (KISS/principles) | plan OQ-01 | OQ-01 was left `open` with `Owner: reviewer`, so it would have stranded, and it treats the two sandbox pointers as one case when they are not symmetric | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved: DROP the pointer from F-2 entirely (pure inference bait in a neighbourhood that has nothing to do with isolation; the sandbox's position is stated at its own home in `host_sandbox_profile`), keep a reframed one at F-1 if that site survives. E-03 and V-03 carry the constraint |
| PR-407 | LOW | IN-SCOPE | G (plan executability) | plan OQ-02 | OQ-02 was left `open` with `Owner: reviewer` and rests on a stale premise (an edge on a backlog item that has graduated) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved: declare NO edge, on three measured grounds (different Sets so no runner ordering applies; an edge would gate a `chore`/`low` fix on a `bug`/`high` release blocker; E-02 now makes both orders safe), with the merge-collision risk named and accepted |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the reframed `ipd_lifecycle` note keep pointing at the hardened sandbox? (OQ-01) | Drop the pointer from the F-2 site entirely; a reframed pointer may stay at F-1 if that site survives | Keep a reframed pointer at both sites (D7 permits it); drop it at both | `dvonrn` D7 permits a reframed pointer, so both answers conform; the deciding asymmetry is that F-2's neighbourhood (`agent_workflows/ipd_lifecycle.py:66`, the role-gate selector) concerns lifecycle ownership and not isolation at all, so the mention only invites the "weak version of a real defense" reading P15 forbids, while the sandbox's position is already stated at its own home (`agent_workflows/host_sandbox_profile.py:31`). No true statement is lost because the genuine limitation is a separate sentence E-03 keeps | yes |
| D-2 | Should this plan declare a dependency edge on the `lifegate` work? (OQ-02) | No edge; E-02 makes both orders safe | Declare `- Item-Dependencies:` on `e25iy9`; wait for the whole `lifegate` Set | The two plans are in DIFFERENT Sets, so no runner ordering exists to lean on either way; `e25iy9` is `- Work-Kind: bug`, `- Priority: high`, `- Blocks-Release: next` while this plan is `chore`/`low`, so an edge inverts the urgency; and the revised E-02 resolves F-1 to a definite disposition in both states, so neither order leaves work unbuilt or double-done. Residual merge-collision risk is handled by the runner's isolated-worktree and merge-revalidate path (AGENTS.md: do not raise file overlap as a runtime hazard) | yes |
| D-3 | The authored census family cannot reach the F-2 site. Widen the search, or narrow the plan to the one site the family does find? | Widen, and make V-01 fail if the census misses F-2 | Narrow the plan to F-1 and F-3 and file F-2 separately; leave the family and rely on the executor noticing fact 2 quotes F-2 | Narrowing would drop a site the plan's own Concern and fact 2 both name, and filing it separately splits one three-line comment edit across two plans for no benefit (P6). Relying on the executor contradicts P9 (design instructions for the model that will run them): the authored step produces a list, and an agent following it has no signal that the list is incomplete. Pinning the property in V-01 is what makes the fix durable rather than a better grep | yes |
| D-4 | Should the plan add a deterministic rule flagging new anti-malice justifications, now that review measured the vocabulary distribution? | No; keep the plan's own refusal | Add a lint rule; file a backlog item for one | The plan already refuses this under P11 and its own F-5, and review's measurement STRENGTHENS the refusal rather than weakening it: 2 of 30 vocabulary hits are defects, so a word-keyed rule would fire on 28 correct sites. The JUSTIFICATION-versus-DISCLAIMER distinction is a judgement made by reading, and PR-401 shows the defect can be stated in words a pattern would not catch at all | yes |

### Verification run in this lane

```
3527 passed, 2 skipped, 3 warnings in 64.58s (0:01:04)
NOTE: 208 tests were deselected by -m/-k and did not run
```

`aw check`: `✗ FINDINGS  70 finding(s) detected across 2628 all`, with ZERO findings attributable to this
plan (`aw check --agent | grep dmjp0u` returns nothing). `aw ipd lint --phase review-finalize --agent`:
`{"outcome":"clean","exit":0,"findings":0}`.
