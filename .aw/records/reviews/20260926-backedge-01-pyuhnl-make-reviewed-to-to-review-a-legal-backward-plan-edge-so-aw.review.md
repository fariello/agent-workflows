# Review findings: plan pyuhnl

- Subject-Id: pyuhnl
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5a6b144e`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision. No pre-review snapshot was needed: the plan was committed and
unmodified, and the lane-input copy is byte-identical to the tracked file.

THIS IS AN UNUSUALLY WELL-EVIDENCED PLAN AND EVERY AUTHORED CLAIM REPRODUCED. I re-ran the whole F-1
reproduction on a scratch repo through the real CLI and got the defect verbatim:

```text
=== STEP 1: aw ipd set to-review on a REVIEWED plan ===
  exit=0
  -    plan        20260828-wk-01-wk0001  [medium]  reviewed -> to-review
  history now:
    - 2026-09-26 to-review (aw set): revise
    - 2026-08-28 reviewed (aw set): reviewed

=== STEP 2: check_engine findings for plans ===
    rule=check.lifecycle-transition-invalid sev=error detail=recorded lifecycle transition
    'reviewed' -> 'to-review' is invalid: missing predecessor: backwards transition
    'reviewed' -> 'to-review'

=== STEP 3: aw commit <plan> -- src/f.py ===
  exit=1
  aw commit: refusing - 1 finding(s) on 20260828-wk-01-wk0001-demo.ipd.md:
    check.lifecycle-transition-invalid: ...
```

That is exactly the two-step trap the Concern describes: the setter SUCCEEDS and records the history
line, and the checker then refuses every subsequent tooled commit on that plan, leaving only
`aw commit --no-plan`, which skips Scope-Paths enforcement. F-2's four predicate results, F-3's wrong
doc example, F-4's three plans now in `executed/` with a clean `aw check plans`, and F-5's absence of
any test naming `_LEGAL_BACKWARD_EDGES` all reproduced. The two spec citations are accurate and load
bearing: `2vev8j` 4.8 point 3 does delegate the enumeration to the IPD spec and does require fail-closed
treatment of un-enumerated edges, and point 2 does warn that removing the rank comparison "would permit
EVERY backward edge, which is NOT what was decided" -- which is precisely why the plan's refusal to touch
it is correct. The maintainer ruling in OQ-01 is recorded on backlog `qzo6dn`'s own history, so it is
attributed rather than asserted.

I WENT FURTHER THAN THE PLAN AND MEASURED THAT ITS FIX IS SUFFICIENT, because a one-line change to a
frozenset consulted by a gate is cheap to verify and expensive to get wrong. Applying
`("reviewed", "to-review")` in-process and re-running the reproduction: the
`check.lifecycle-transition-invalid` error disappears (only the pre-existing `info` lint diagnostic
remains) and `aw commit wk0001 -- src/f.py` exits 0 and commits. Then the blast radius, which is the
half that matters for a contract change: five un-enumerated backward edges stay REFUSED after the patch
(`approved -> to-review`, `reviewed -> draft`, `approved -> draft`, `executed -> reviewed`,
`to-review -> draft`), and both pre-existing edges stay ok. So the fix is surgical, the rank comparison
is provably still load-bearing, and E-03 needs no companion change. Recorded as F-6, and E-03's expected
outcome now says so, with the instruction that a needed companion change is a signal to report rather
than absorb.

**E-04 NAMED THE WRONG SECTION OF THE SPEC, AND THE MISTAKE IS THE KIND THAT DAMAGES A RECORD.** It says
the sentence to amend is "in the `## Workflow history` bullet". The sentence is in a bullet that
DESCRIBES `## Workflow history`, sitting inside `## What an IPD MUST contain`. The spec ALSO has a real
`## Workflow history` section further down, holding its own amendment log. An executor following the
authored wording searches that log, does not find the sentence, and in the worst case edits the history
section -- rewriting a prior line, which the very bullet under discussion forbids ("never rewrite prior
lines"). Fixed by locating the target by CONTENT instead of by section, with the distinction stated.
While there I measured two adjacent claims in the same item: `specs.run_note` reads no status at all, so
the hedge that `aw specs note` "may refuse on an `implemented` spec" is unfounded (harmless, but it
invites an executor to skip the tooled history record on a refusal that will not come); and the tool
writes a `note (aw specs)` label where this spec's one prior amendment reads `amended (tgop8e)`, so the
item now says not to hand-edit the label to match. Recorded as F-7.

**V-04's EVIDENCE BAR WOULD HAVE READ AS A REGRESSION.** It asks for "`aw check specs` output showing no
new finding for the spec". Measured today, that command reports `20 specs checked, errors 1, warnings 0`,
and the single error is the generic `cross-tree collisions NOT checked by a per-type run` notice, which
names `<collisions>` and no spec file. An executor who expects zero sees one and cannot tell whether it
caused it. V-04 now carries the baseline explicitly and states the bar as "does not rise, and no finding
names the IPD spec". Recorded as F-8. This is small, but an evidence bar that cannot be met cleanly is how
a validation item gets waved through.

I ALSO CHECKED WHETHER E-05 IS COMPLETE OR A SAMPLE, since a docs fix that repairs one of several wrong
statements leaves the lesson half-taught. It is complete: `rg` over `docs/`, the root Markdown files and
`.aw/system/` finds the wrong `approved -> to-review` example ONLY in the paragraph E-05 targets, and
`AGENTS.md`, `CONTRIBUTING.md` and the plans README name no backward edges at all. Recorded in the Scope
check. And I confirmed `_LEGAL_BACKWARD_EDGES` has exactly one consumer, so the Under-scope claim about
`check_engine.py` and `work_cmd.py` is right; `run_state.validate_transition` and `set_state` are
unrelated same-named symbols in a different lifecycle.

**WHAT I DID NOT CHANGE.** The one-edge scope, the refusal to touch the rank comparison, the declared
spec amendment and its rationale (AGENTS.md requires exactly this mechanism and the plan follows it), both
Carrier-Declined deferrals (the first is particularly well reasoned: weakening a fail-closed commit gate
for a finding that will no longer arise trades a real invariant for nothing), OQ-01 and OQ-02, and the
GENUINE STOP CONDITION in the gate, which is correctly framed as a real unsafe-to-proceed case rather than
a scope stop. E-02's test design is good: it pins the repro end to end, the absent check finding, the
direct predicate, the still-refused controls THROUGH `aw commit` as well as through the predicate, and the
pre-existing edges. Requiring the control at both layers is what stops a future change from legalizing
everything and still passing.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | E. testing; A. correctness (an unmeasured sufficiency claim) | in-process patch of `_LEGAL_BACKWARD_EDGES` + re-run of the reproduction: finding cleared, `aw commit` exit 0; five un-enumerated edges still refused | **THE FIX'S SUFFICIENCY AND BLAST RADIUS WERE ARGUED BUT NOT MEASURED.** For a one-line change to a frozenset that a fail-closed gate consults, both halves are cheap to verify: that the error clears and the commit succeeds, and that no OTHER backward edge becomes legal. I measured both. Without this, E-03's expected outcome rests on reading. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-6 with the measured results; E-03's expected outcome now records that sufficiency is proven and that a needed companion change is a signal to report, not absorb; the Under-scope claim is now backed by measurement rather than reading. |
| PR-002 | MEDIUM | IN-SCOPE | A. correctness (a wrong edit location, with record-damage risk) | the target sentence located in the bullet describing `## Workflow history`, inside `## What an IPD MUST contain`; the spec's own `## Workflow history` section is separate and holds its amendment log | **E-04 NAMES THE WRONG SECTION.** An executor following the authored wording searches the spec's history log, where the sentence is not, and could edit that log instead -- rewriting a prior history line, which the bullet under amendment explicitly forbids. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-7; E-04 now locates the target by CONTENT, states the two-sections distinction explicitly, and warns why the confusion is harmful. |
| PR-003 | LOW | IN-SCOPE | A. correctness (an unfounded hedge; a label mismatch) | `specs.run_note` body: reads `path`, date and message, no status; writes `- <date> note (aw specs): <msg>`. The spec's prior amendment line reads `amended (tgop8e)` | **E-04's HEDGE THAT `aw specs note` MAY REFUSE ON AN `implemented` SPEC IS UNFOUNDED,** and it matters because the item tells the executor to skip the tooled history record on that refusal -- an escape hatch for a refusal that cannot occur. Separately the tool's `note` label differs from this spec's prior `amended` label, which invites a hand-edit to "match". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-7; E-04 now states the verified fact (it will not refuse), keeps a paste-the-output fallback for a genuine error, and forbids hand-editing the tool's label. |
| PR-004 | LOW | IN-SCOPE | E. testing (an unmeetable evidence bar) | `aw check specs` at review HEAD: `20 specs checked, errors 1, warnings 0`; the error names `<collisions>`, not any spec | **V-04 ASKS FOR "no new finding" AGAINST A NON-ZERO BASELINE IT DOES NOT STATE.** The standing error is a generic cross-tree-collisions notice unrelated to this change; an executor expecting zero cannot tell whether it caused the one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-8; V-04 now records the baseline verbatim and restates the bar as "the count does not rise and no finding names the IPD spec", with an explicit instruction not to read the standing 1 as self-inflicted. |
| PR-005 | LOW | UNDER-SCOPE | F. honest documentation (completeness of a docs fix) | `rg` over `docs/`, root Markdown and `.aw/system/`: the wrong example appears only in the E-05 paragraph; `AGENTS.md`/`CONTRIBUTING.md`/plans README name no backward edges | **E-05 FIXES ONE PARAGRAPH WITHOUT ESTABLISHING THAT IT IS THE ONLY WRONG ONE.** A docs correction that turns out to be a sample leaves the wrong lesson elsewhere. Measured: it is the only one, so the item is complete -- but that was unverified as authored. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded in the Scope check as a docs sweep with the search surface named, so a reader can see the fix is exhaustive rather than illustrative. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan asserts a one-line frozenset addition fixes the defect. Accept the reasoning, or apply it and measure? | APPLY AND MEASURE, both the fix and the blast radius. | (a) Accept the reasoning: rejected, because the change amends a public contract a fail-closed gate enforces, and the specific failure spec `2vev8j` 4.8 point 2 warns about (permitting EVERY backward edge) is invisible to a reading that only checks the intended edge. (b) Measure only the intended edge: rejected for the same reason; the controls are the half that bounds the risk. | In-process patch of `_LEGAL_BACKWARD_EDGES` plus a re-run of the scratch-repo reproduction: finding cleared, `aw commit` exit 0, and five un-enumerated edges (`approved -> to-review`, `reviewed -> draft`, `approved -> draft`, `executed -> reviewed`, `to-review -> draft`) still refused. | yes |
| D-2 | E-04 misidentifies which section holds the sentence. Correct the location, or raise it as a question? | CORRECT IT, by locating the target by content rather than by section. | (a) Raise as an open question: rejected, there is no judgement involved -- the sentence is demonstrably in one place and not the other. (b) Note it in findings only: rejected, this is the one edit instruction whose misreading can DAMAGE a record (rewriting a history line the same bullet forbids rewriting), so the item itself must be unambiguous. | The two sections located by content in the spec file; the bullet's own rule "never rewrite prior lines". | yes |
| D-3 | The plan hedges that `aw specs note` may refuse on an `implemented` spec, with an escape hatch. Leave the hedge, or verify? | VERIFY, and remove the escape hatch's premise while keeping a fallback for a genuine error. | (a) Leave it: rejected, an unfounded hedge that authorizes skipping the tooled history record is exactly how an untooled hand-edit gets justified later. (b) Delete the fallback entirely: rejected, a real I/O error is still possible and pasting the output is the honest response to one. | `specs.run_note` read in full: it reads the file, date and message and appends; no status is consulted, so an `implemented` spec cannot be refused on that ground. | yes |
| D-4 | Is E-05's single-paragraph docs fix complete, or a sample? | COMPLETE, and now stated as such with the search surface recorded. | (a) Assume complete: rejected, the plan's own F-3 found the error by inspection rather than by a sweep, so completeness was unestablished. (b) Widen E-05 to a docs audit: rejected as unnecessary once measured -- there is nothing else to fix, and inventing scope would be over-scope. | `rg` for the wrong edge across `docs/`, root Markdown and `.aw/system/` returned only the E-05 paragraph (plus an unrelated DECISIONS.md line about the SPEC lifecycle, which legitimately permits the edge). | yes |

### Deferred and open

- (none). All five findings were FIXED in place. None reached the Medium-High or High Remediation Risk
  the Fix Bar requires for a deferral, and no question needed the human: OQ-01 was already settled by a
  maintainer ruling I verified on backlog `qzo6dn`'s history, OQ-02 is correctly resolved against
  AGENTS.md's spec-amendment rule, and each finding above was settled by a measurement recorded with the
  command that produced it.

HONEST LIMIT, stated because it bounds what this round proves. My sufficiency measurement (F-6) patched
`_LEGAL_BACKWARD_EDGES` IN PROCESS rather than on disk, so it proves the predicate and the two gates that
consume it behave as intended; it does not prove the edited source file will be byte-correct, which is
E-03's and V-03's job. I did NOT run the bare suite against a patched tree, so the plan's E-06
before/after comparison remains a real obligation and not a formality. I did narrow that risk: beyond
F-5's finding that no test names `_LEGAL_BACKWARD_EDGES`, I searched for a test asserting on the refusal
MESSAGE without naming the symbol (`rg 'backwards transition|lifecycle-transition-invalid' tests/`) and
found exactly one hit, a DOCSTRING in `tests/test_status_set.py` describing the separate
`--allow-terminal-reopen` guard for reopening an `executed` plan, which this change does not touch (I
confirmed `executed -> reviewed` stays refused after the patch). So no test is expected to flip, but
"expected" is not "measured" and E-06 is what measures it. I also did not verify the spec amendment's
wording against every other plan reviewed under the current contract; the plan's argument that adding one
edge to an enumeration changes no other plan's meaning is sound, but it is an argument rather than a
measurement.
