# Review findings: plan mzc019

- Subject-Id: mzc019
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `7562ca6c`. The plan on disk was byte-identical to the lane input, and `git status --porcelain`
on the plan path was empty, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0.

THE DIAGNOSIS IS CORRECT, WELL-EVIDENCED, AND WORTH DOING. A file:line citation does expire silently, the
misdirection-versus-dangling distinction is the right frame, and the plan's own discipline of anchoring every
claim by symbol is both the rule it proposes and a live demonstration of it. Its natural-experiment history
entry (four symbol anchors still resolving after `216rgg` rewrote the cited region) is genuine evidence, not
rhetoric. I verified the headline drift directly: at `d445e6e6`, `check_engine.py:897-905` was indeed the
`seen_ids` initialization plus an identity-slot comment, and `doctor.py:530` was a blank line.

WHERE THIS REVIEW SPENT ITS EFFORT: the diagnosis is right and THREE OF THE FOUR MECHANISMS THE PLAN NAMES
BEHAVE DIFFERENTLY FROM HOW IT DESCRIBES THEM. Each would have stranded or silently neutered an item, and
each was measured rather than inferred.

**1. The detector as specified could not flag this plan's own headline evidence.** E-03 originally keyed on a
citation carrying "NO accompanying symbol or quoted content string on the same bullet or table cell". Measured
over the whole pending corpus through `_structural_lines`:

```text
structural citations:                                   2773
on a line that ALSO has a backticked token:             2766 (99%)
lines with NO backtick at all:                             7 (0%)
```

So the condition is satisfied almost everywhere and the rule would have emitted essentially nothing. Worse,
it fails on the exact case the plan was written from. The `216rgg` anchors are themselves backticked, and the
file path `check_engine.py` is itself a dotted token:

```text
216rgg F-1 Location cell: `check_engine.py:897-905`
  backticked token present?  True
  dotted-symbol present?     True  -> scored ANCHORED, no finding emitted
```

A rule that cannot flag the single example motivating the plan is the wrong rule, not a weak one. The fix is
to exclude from the candidate-anchor set the citation itself, a backticked bare file path, and a backticked
bare line range (the filename-less `` `:906-915` `` continuation form, of which the corpus carries 2628).
Measured with that correction: **558 of 2773 (20%)** flag, and the `216rgg` Findings cell and prose sentence
both flag while its E-01 bullet correctly does not, because that bullet names `check_engine.check_collisions`
beside the offset, which is precisely the compliant form E-01 blesses. That contrast is the rule working.

**2. An advisory is invisible in default human output, so the nudge nudged nobody.** The human render path
prints per-advisory lines only `if has_adv and detail`, where `detail` comes from `--detail`/`--long`. Measured
on `5e4sb6`, the only pending plan currently carrying advisories:

```text
$ aw ipd lint --phase author --no-color <5e4sb6>
- >  approved     plan        20260829-rununify-00-5e4sb6  [blocking]  advisory
exit=0
$ ... --detail
     ? advisory: IPD-Z602 (line 51): E-02: action text may bundle multiple concerns ...
     ? advisory: IPD-Z602 (line 56): E-03: action text may bundle multiple concerns ...
```

Default output gives the word `advisory` and nothing else: no code, no message, no line. E-02's entire premise
is that the author must MEET the rule, and an author who does not know to pass a flag they have no reason to
suspect learns nothing. Added E-05/V-05, deliberately narrow (surface the new code only, leave `IPD-Z602`
byte-unchanged) with an explicit stop boundary if that proves impossible without a wider render refactor.

**3. E-02 named the wrong module and would have broken a byte-parity pin.** `ipd_schema` owns only
`H_PROJECT_CONVENTIONS` and its place in `CHILD_H2_ORDER`; the emitted body is the
`ipd_authoring._SECTION_BODY` entry keyed by that constant. And the template is byte-pinned to the generator.
I added one convention line to `_SECTION_BODY` in memory and ran the pin:

```text
FAIL: test_child_template_matches_generator
AssertionError: ... != ... : child template drifted from build_skeleton; regenerate it
```

So the edit is three files, not one, and the template must be REGENERATED rather than hand-matched. I also
checked the adjacent trap: the new line must NOT join `_AUTHORING_PLACEHOLDERS`, or
`authoring_placeholders_resolved` would read every plan as a forever-stub and silence
`check.ipd-draft-ready-to-review`. The orchestrator template has no conventions heading at all, so its pin is
unaffected.

Three further metadata contract errors, all measured:

- The `Scope-Paths` fence declared `ipd_schema.py` (not needed) and omitted `ipd_authoring.py`, the template,
  and the template's parity test (all required). As authored the run takes three out-of-scope edits and owes a
  `--scope-ack` on a fourth.
- The Deferred row carried `- Carrier: mzc019`, the plan's OWN id6. `_resolve_carrier` returned `ok` for it,
  but only because this plan is currently `to-review`; the resolver accepts any non-terminal owner and does
  not special-case self-reference. At execution the reference turns terminal and the promotion decision
  vanishes, which is exactly what the field exists to prevent. Because the gate that would catch this
  (`check.ipd-uncarried-obligation`, `pre-transition` only) reports the row SATISFIED today, nothing will ever
  stop a run over it, so it needed an E-item rather than a gate sentence.
- V-01 required the spec's `- Status:` be "updated by a tooled verb". `SPEC_TRANSITIONS['implemented']` is
  `{superseded, deferred}` and `transition_allowed('implemented', X)` is False for every review-ish target, so
  the demand was unsatisfiable in one half and undesirable in the other (the status must NOT change here).
  `aw specs note` is the correct surface and this very spec already carries a precedent history entry.

VERIFIED CLAIMS I DID NOT CHANGE. `_structural_lines` genuinely excludes fenced, indented, front-matter and
block-quote lines (tested with a synthetic plan carrying a fenced citation and an indented traceback: both
excluded, an ordinary bullet returned). Nothing in the repo validates a citation today (`cite`/`citation`
absent from `ipd_lint`). `IPD-D701` is retired and must not be revived. The `assess` workflow does ask for
`file:line`, and leaving it alone is right. The `C_*` count is 30 as stated. The corpus shape re-derived at
this HEAD as 90 of 93 plans (96%) and 2802/2773 citations, holding the plan's ~95% claim across three
measurements while every absolute number moved.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; E. testing | corpus scan through `ipd_lint._structural_lines` (2766/2773 = 99% co-occur with a backticked token; 7 do not); `216rgg` Findings cell and prose evaluated directly under the specified condition | **THE DETECTOR AS SPECIFIED CANNOT FLAG THE PLAN'S OWN HEADLINE EVIDENCE, SO E-03 WOULD SHIP A RULE THAT SEES NOTHING.** E-03 keyed on a citation with "NO accompanying symbol or quoted content string" in the same bullet or cell. 99% of corpus citations already sit beside a backticked token, and the drifted `216rgg` anchors are themselves backticked with `check_engine.py` reading as a dotted symbol, so the test scores them ANCHORED and emits zero. The plan would have delivered a passing, well-tested, permanently silent rule, and its own F-3 warns against exactly this class of near-zero result being mistaken for health. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-03 rewritten to specify the test as "does a DURABLE anchor accompany it, where the citation itself is not evidence of one", explicitly excluding the matched citation, a backticked bare file path, and a backticked bare line range from the candidate set. I measured the corrected form at 558/2773 (20%) with the `216rgg` cell and prose flagging and its compliant E-01 bullet not, and required both numbers re-derived at execution plus the `216rgg`-shaped fixtures pinned. V-03 grew from four cases to six plus the headline fixture plus a corpus discrimination measurement; a near-zero result is now defined as a failure condition. |
| PR-002 | HIGH | UNDER-SCOPE | C. operability; F. UX (silent failure) | `ipd_lint` human render path guard `if has_adv and detail`; measured default vs `--detail` output for `5e4sb6` (pasted above) | **THE ADVISORY IS INVISIBLE BY DEFAULT, SO E-03'S NUDGE WOULD REACH NOBODY.** Without `--detail`/`--long` the entire finding collapses to the word `advisory` in the status line, with no code, no message, and no line number. E-02's stated premise is that the author must MEET the rule before writing findings; a finding that prints nothing an author can act on fails that premise while passing every test the plan proposed. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-05/V-05 to surface the new code's message in default human output, scoped narrowly: `IPD-Z602`'s default quietness must stay byte-identical, `--agent`/`--json` must not change (already unconditional, verified), and exit status and disposition must not move. Added an explicit stop boundary: if the narrow fix is impossible without reshaping the render path, record it, file a carrier, and mark the item `blocked` rather than widening scope. |
| PR-003 | HIGH | IN-SCOPE | G. executability; D. anti-regression | `H_PROJECT_CONVENTIONS` grepped across the package (2 files; the only non-declaration use is the `_SECTION_BODY` key); `tests/test_ipd_templates.py` failure reproduced with a one-line `_SECTION_BODY` edit | **E-02 NAMED THE WRONG MODULE AND WOULD HAVE BROKEN A BYTE-PARITY PIN.** The conventions BODY is in `ipd_authoring._SECTION_BODY`, not `ipd_schema` (which owns only the heading constant). And the shipped child template is asserted byte-identical to `build_skeleton` output, so any body edit fails `tests/test_ipd_templates.py` unless the template is regenerated in the same change. An executor following the item as written edits the wrong file, then hits a test failure the plan does not predict. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 corrected to name `ipd_authoring`, with the grep evidence inline, and now REQUIRES regenerating the child template from `build_skeleton` (explicitly not hand-editing it). Recorded that the orchestrator template has no conventions heading so its pin is unaffected, and added a warning NOT to add the new line to `_AUTHORING_PLACEHOLDERS` (which would make every plan read as a forever-stub and silence `check.ipd-draft-ready-to-review`). V-02 now requires the parity test pasted passing plus proof the placeholder tuple was untouched. |
| PR-004 | HIGH | IN-SCOPE | G. executability (scope fence) | `ipd_schema.parse_scope_paths` run on the declared value (4 paths, no errors, so the fence is well-formed but wrong); the three surfaces E-02 must actually touch | **THE SCOPE FENCE IS WRONG IN BOTH DIRECTIONS, SO FINALIZE WOULD REFUSE.** It declared `agent_workflows/ipd_schema.py`, which E-02 does not need to touch, and omitted `agent_workflows/ipd_authoring.py`, `.aw/system/workflows/assess/templates/ipd.md`, and `tests/test_ipd_templates.py`, all three of which E-02 must change. As authored the run takes three out-of-scope edits (each needing a `--scope-reason`) and owes a `--scope-ack` for a declared path never modified. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `Scope-Paths` corrected to the six paths actually required. Scope check section rewritten to map each declared path to its owning E-item, to record what was wrong and why, and to note that E-06 touches no declared path by design (it edits this plan and creates a backlog record, neither of which belongs in an allowlist). |
| PR-005 | HIGH | IN-SCOPE | A. correctness (a gate the plan trusts that cannot see the defect) | `check_engine._resolve_carrier(idx, 'mzc019')` returned `('ok', '')`; `_CARRIER_TERMINAL_STATUSES`; `_CARRIER_CHECKPOINTS` = `{pre-transition}`; measured `aw ipd lint --phase pre-transition` reporting the row satisfied | **THE DEFERRED ROW NAMES THE PLAN ITSELF AS ITS OWN CARRIER, WHICH PASSES THE GATE NOW AND VANISHES AT EXECUTION.** `- Carrier: mzc019` resolves only because this plan's status is non-terminal; the resolver accepts any non-terminal owner and does not special-case self-reference. Once the plan is `executed` the reference is terminal, the obligation classes `done` in `aw attention`, and the promotion-to-gating decision disappears with no record, which is precisely the failure the carrier field exists to prevent. Critically, the gate that exists to catch this reports SATISFIED today, so no checkpoint will ever stop a run over it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added E-06/V-06 requiring a real backlog item be filed for the promotion decision and the row's `- Carrier:` repointed at it before finalize, with the reasoning recorded in the Deferred row itself. Made it an E-item precisely because no gate can see it. Explicitly forbade "fixing" the resolver under this plan (out of the declared fence, and a change affecting every carrier in the tree) while allowing the executor to file it separately. |
| PR-006 | MEDIUM | IN-SCOPE | G. executability; spec sync | `attention_contract.SPEC_TRANSITIONS['implemented']` = `{superseded, deferred}`; `transition_allowed('implemented', X)` False for `reviewed`/`approved`/`to-review`/`implementing`/`implemented`; the target spec's `- Status: implemented`; its existing `2026-08-26 note (aw specs)` history entry | **V-01 DEMANDED A SPEC STATUS TRANSITION THE TOOLING REFUSES, AND WHICH WOULD BE WRONG IF IT WORKED.** It required confirming "the spec's `- Status:` and history were updated by a tooled verb". The spec is `implemented`, whose only legal onward transitions are `superseded` and `deferred`, so `aw specs set` cannot satisfy the status half at all, and the status SHOULD NOT change here: this is an amendment to an implemented contract, not a reversion. An executor would either stall or force something harmful. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Spec-sync section now records the measured transition table, prescribes `aw specs note` (status-preserving, with the in-spec precedent cited), and forbids attempting a transition. V-01 now requires the `- Status:` line pasted before and after showing it UNCHANGED at `implemented`, plus `aw specs check` and the sibling-spec-reading test. Added a caution to prefer appending a Section 10 item over renumbering, since numbered items are referenced elsewhere, and to re-derive the legal transition set if the status has moved by execution time. |
| PR-007 | MEDIUM | IN-SCOPE | A. correctness (precedent misread) | `check_engine.carrier_severity_for_plan` (returns `error` post-cutover, `info` pre-cutover; the finding is still emitted); E-03's ruling that this rule is `info` in all cases; newest pending `- Date:` measured as `2026-09-18`, this plan's own | **E-04 COPIES A PRECEDENT THAT DOWNGRADES SEVERITY, BUT THIS RULE NEEDS SUPPRESSION, AND ITS CUTOVER WOULD HAVE FIRED ON ITSELF.** The carrier precedent still EMITS for a pre-cutover artifact, merely at `info`. Since E-03 fixes this rule at `info` in both tiers, "downgrade" is a no-op and a faithful copy would report hundreds of advisories on untouchable history, the exact outcome E-04 exists to prevent. Separately, "this plan's execution date or later" is ambiguous and the newest corpus date IS this plan's `2026-09-18`, so a `20260918` cutover would fire on this plan, which carries three illustrative `foo.py:123` strings. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now states explicitly that it borrows the DATE MECHANISM and not the severity ladder, and must SUPPRESS pre-cutover rather than downgrade, with a code comment warning against later "restoring parity". Added the precedent's missing-`Date`-is-pre-cutover rule and its reasoning (`IPD-M101` owns that complaint). Required the cutover be strictly greater than the newest date present at execution time, re-measured then, with the boundary-case-is-this-plan hazard named. V-04 now requires a zero-advisory run against this plan specifically and a no-`Date` fixture. |
| PR-008 | LOW | IN-SCOPE | D. anti-regression; G. executability | `artifact_core.drift_exit_code` grepped: 0 occurrences in `ipd_lint`; `LintResult.advisories` vs `diagnostics` disposition logic; `IPD-I3xx` is the id-family block; `IPD-D701` retired | Four smaller mechanism inaccuracies, each cheap to correct and each capable of sending an executor down a wrong path: the plan cited `artifact_core.drift_exit_code` as the non-gating mechanism, but `ipd_lint` never calls it (non-gating comes from emitting into `LintResult.advisories`); it suggested allocating the new code in the `IPD-I3xx` block, which is the id-family group and unrelated to citations; it did not warn against reviving retired `IPD-D701`; and it did not record that `_structural_lines` works per LINE, so a multi-line bullet with its symbol on line 1 and its offset on a continuation line will false-positive. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All four corrected in place: E-03 now says emit into `advisories` and not `diagnostics`, open a NEW area block rather than extending `IPD-I3xx`, never revive `IPD-D701`, and records the line-granularity false positive as a KNOWN AND ACCEPTED limit that is part of why the rule must stay `info`. Conventions section updated with the measured mechanism facts (advisory channel, default quietness, spec transition refusal, self-carrier trap) so a later reader inherits the measurements rather than the original assumptions. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-03's specified detector cannot see the plan's own headline defect. Escalate as a blocking question, or re-specify the condition? | RE-SPECIFY the condition in place (exclude the citation itself, bare paths, and bare line ranges from the candidate-anchor set) and require the corrected discrimination be MEASURED at execution. Not escalated. | (a) Escalate `Blocking: yes` and stop: rejected, this is answerable from repository evidence rather than maintainer preference, since I could measure both the broken and the corrected rates directly on the corpus. (b) Leave E-03 as written and let the executor discover it: rejected, the failure mode is a silently passing rule, which is the hardest kind to notice and exactly the defect class F-3 warns about. (c) Prescribe an exact regex: rejected, over-specifying a heuristic in a plan freezes an implementation detail the executor should be free to tune, so I specified the CONDITION and the measurable outcome instead. | Measured 2766/2773 (99%) co-occurrence with a backticked token; 7 lines with no backtick; the `216rgg` cell and prose scoring anchored under the original condition and flagging under the corrected one; 558/2773 (20%) corrected flag rate; 2628 bare `:NNN` forms. | yes |
| D-2 | The advisory prints nothing without `--detail`. Add a visibility item, or accept the nudge as flag-gated? | ADD E-05, scoped narrowly to the new code only, with an explicit stop boundary. | (a) Accept flag-gated visibility: rejected, E-02's premise is that the author must meet the rule, and a finding that prints no code and no message by default cannot do that; the item would pass its tests and deliver nothing. (b) Make all advisories verbose by default: rejected, that changes output for every plan in the tree (starting with `IPD-Z602` on `5e4sb6`) and is a separate decision with its own blast radius. (c) File it as a follow-up: rejected, E-03 without it ships a nudge nobody sees, so they are not separable. | Measured default vs `--detail` output on `5e4sb6`: default prints one status line ending `advisory` and zero finding lines. The `--agent`/`--json` paths already emit advisories unconditionally with `severity: "info"` (verified on this plan's own uncarried-obligation advisory). | yes |
| D-3 | The Deferred row's `- Carrier: mzc019` is a self-reference that resolves today. Note it in the gate, or add an E-item? | ADD E-06/V-06 as a real checklist item, and forbid touching the resolver. | (a) A gate sentence or contract note: rejected, and this is the load-bearing reason: the gate that exists to catch an uncarried obligation reports this row SATISFIED today, so nothing will ever stop a run over it. An obligation invisible to every checkpoint needs a checklist item and a validation item, not prose. (b) Fix `_resolve_carrier` to reject self-reference: rejected as out-of-scope here (the plan's fence excludes `check_engine.py` and the change affects every carrier in the tree), but the executor is explicitly permitted to file it separately. (c) Drop the deferral: rejected, promoting the rule to gating is a real future decision worth keeping. | `_resolve_carrier(idx, 'mzc019')` returned `('ok', '')`; the owner list shows the single non-terminal `to-review` entry that makes it resolve; `_CARRIER_TERMINAL_STATUSES` includes `executed`; `_CARRIER_CHECKPOINTS` is `{pre-transition}` only. | yes |
| D-4 | V-01 required a tooled spec `- Status:` update that `implemented` refuses. Ask the maintainer how to record the amendment, or resolve it? | RESOLVE: use `aw specs note` and require the status be proven UNCHANGED. | (a) Ask the maintainer: rejected, the repository answers it unambiguously (the transition table, the `note` verb's documented purpose, and a precedent history entry in this very spec). (b) Transition to `deferred` or `superseded` to get a legal move: rejected outright as actively harmful; it would misrepresent an implemented, canonical contract to satisfy a validation demand. (c) Hand-append a history line: rejected, the setter owns that format and AGENTS.md requires tooled status/history writes. | `SPEC_TRANSITIONS['implemented']` = `{superseded, deferred}`; `transition_allowed` False for every review-ish target; `aw specs note --help` ("WITHOUT changing its status"); the spec's existing `2026-08-26 note (aw specs)` entry. | yes |
| D-5 | The plan's corpus counts are all stale (a third time). Re-measure and rewrite, or annotate? | ANNOTATE with a third dated snapshot and keep the shape-based criteria, rather than rewriting the plan around new absolutes. | (a) Rewrite every count to this HEAD: rejected, it would date again within hours and the plan already argues correctly that the SHAPE is what must survive; replacing one snapshot with another teaches the wrong lesson. (b) Delete the counts: rejected, they are the evidence that this is a convention-wide problem rather than one author's lapse. | Re-derived at `7562ca6c`: 90/93 plans (96%), 2802 raw / 2773 structural citations, densest 102 unchanged; provably-dead re-derived as 132/2764 (4%) under a broader resolver versus the plan's 8/2816 (0%), which is why I required the resolution rule be stated alongside the number. | yes |

### Honest limits of this review

- I did NOT write or prototype the corrected detector as shipping code. I measured candidate conditions with
  throwaway scripts over the real corpus, which is enough to prove the original condition is inert (99%) and
  that a corrected one discriminates (20%), and enough to prove the `216rgg` cases flip. It is NOT a proof that
  the implementer's chosen regex will land on the same numbers, which is exactly why V-03 now demands the
  measurement be re-derived rather than quoted.
- The 20% figure is one reasonable definition of "durable anchor", not the only one. A stricter rule (requiring
  a genuinely qualified `module.symbol` rather than any non-path backticked token) would flag more. I did not
  try to find the optimal threshold, and the plan is right to keep the rule `info` while that is unknown.
- I did not verify the plan's claim that `216rgg`'s citations were correct WHEN WRITTEN. I confirmed they are
  wrong now and that the plan's history asserts they were measured at HEAD; whether that original measurement
  was accurate is not checkable from here, and the argument does not depend on it.
- I did not run the full suite as part of this review. I ran `tests/test_ipd_templates.py` (10 passed) as the
  baseline for the parity claim, and reproduced its failure under a simulated E-02 edit. This review changed
  only a plan file and this record, so no suite run was warranted; the plan's own validation section requires
  the bare suite at execution.
- E-05's feasibility is asserted from reading the render path, not from implementing it. I could see the
  `if has_adv and detail` guard and the per-code advisory data available at that point, but I did not confirm
  that distinguishing one advisory code from another there is clean. That uncertainty is why E-05 carries an
  explicit stop boundary and why V-05 permits a `blocked` result with evidence.
