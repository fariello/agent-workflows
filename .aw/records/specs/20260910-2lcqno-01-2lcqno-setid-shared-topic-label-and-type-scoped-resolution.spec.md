# Spec: Setid as a shared cross-type topic label, with type-scoped resolution

- Date: 2026-09-10
- Status: draft
- Id: 2lcqno
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Spec: 4w7d6s
- Scope: A setid is a SHARED cross-type grouping label, not a unique identity; fix the ambiguous lookup (type-scoped resolution) instead of enforcing uniqueness, and re-scope check.setid-collision to the within-type half that is still a real defect.
- Supersedes: `.aw/records/specs/20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md`
  (`4w7d6s`), whose central invariant the maintainer REVERSED on 2026-09-10. That spec is retained as the
  historical record and its surviving parts are carried forward here rather than cited across a reversal.
- Parent: `.aw/records/specs/20260817-2147-01-uniform-artifact-naming-grammar.spec.md` (the uniform naming
  grammar that defines the `<setid>` token; it is `implemented` and transition-frozen, so this spec
  CONSTRAINS the token's SEMANTICS without editing the grammar).

---

## 1. Why this spec replaces its predecessor

Spec `4w7d6s` proposed making a setid unique across every record type, preventing duplicates at
creation, hardening the collision check, and minting a fresh setid whenever a source graduated into a
plan Set. On 2026-09-10 the maintainer REVERSED that direction after the numbers were measured. This
spec records the replacement design.

THE MAINTAINER'S REASONING, preserved because it is the load-bearing part and not merely the outcome:
research, specs, prompts, backlog items and plans concerning one issue ARE naturally one set to a user,
and a shared setid makes that relationship obvious while distinct setids OBFUSCATE it. The alternative
reading was stated honestly and rejected: if a setid meant only "artifacts that run together" (a
plan-execution batch), the token would become effectively useless for most artifacts and ALWAYS useless
for specs, since no "spec set" exists.

THE FIVE MEASUREMENTS THAT DECIDED IT, all taken at HEAD before the decision and reproducible:

1. CROSS-TYPE SHARING IS THE DOMINANT PATTERN, NOT DRIFT. Of 433 distinct filename-slot setids, **117
   span more than one record type**. The widest are genuine topics: `agentadhere` covers 7 plans + 1
   backlog item + 5 research reports (13 files); `lanectn` covers 7 plans + 7 reviews + 1 walkthrough.
   The predecessor's uniqueness invariant would have forbidden all 117.
2. THE SHARING IS PARTLY AUTOMATIC AND DELIBERATE. `review_findings.build_review_name` constructs a
   review's filename from the SUBJECT's setid AND the SUBJECT's id6, documented in that function as "the
   join key ... not a fresh identifier". Plans-and-reviews sharing a setid is therefore designed
   behavior; that pair alone is 47 of the 117, plus 38 more as backlog+plans+reviews.
3. THE MOTIVATING FAILURE WAS A LOOKUP DEFECT. The predecessor's own evidence was `aw ipd set approved
   agentadhere` failing with "selector 'agentadhere' resolved to artifact(s) of type ['backlog',
   'research'] ... scoped to 'plans'". The setter held BOTH the setid and the target type and still gave
   up, when resolution by `(type, setid)` was available and unused. That is a resolution bug, not a
   naming bug, and fixing it is this spec's primary deliverable.
4. THE CHECK IS CURRENTLY MISLABELLING CORRECT BEHAVIOR. `check.setid-collision` is registered at
   severity `error` (`check_engine.py:95-97`) and reports **38 findings on the default scope and 86 with
   `--all`**. Of the 86, **78** are the backlog+plans topic sharing this spec endorses, 2 are
   plans+research, 1 is plans+walkthrough, and only **5** are within-type conflicting-descriptive cases
   that remain genuine defects.
5. THE FIELD IS BARELY USED OUTSIDE PLANS IN FRONT MATTER BUT HEAVILY USED IN FILENAMES. Body `- Set:`
   field: plans 597, backlog 176, research 2, walkthroughs 1, and ZERO in specs, prompts and reviews.
   Filename slot: plans 604/608, backlog 177/177, reviews 162/162, research 110/112, specs 10/29,
   walkthroughs 7/17, prompts 2/34. Filename-level topic discovery is where the setid earns its keep,
   which is exactly what uniqueness would have destroyed.

AN IRONY WORTH RECORDING SO IT IS NOT RE-DISCOVERED AS EVIDENCE: the predecessor's implementing plan Set
exists partly because scaffolding it under the setid `setiduniq` instantly collided with its own source
backlog item, and the plans cite that as live proof of the defect. Under this spec that collision was
CORRECT BEHAVIOR, so the demonstration proved the opposite of what it was read as proving.

## 2. What the predecessor got right, and is carried forward

Not all of `4w7d6s` is reversed, and the surviving half is restated here so no reader has to consult a
superseded document across a reversal:

- The typed, id6-keyed graduation links are correct and wanted: a child carries `- From-Backlog: <id6>`
  or `- From-Spec: <id6>` pointing at its single source (its old G2).
- A source carrying a multi-valued `- Graduated-To:` forward link is useful INDEPENDENTLY of uniqueness,
  because it answers "what did this become" without a corpus scan (its old G3).
- The link asymmetry is intentional and correct: back-link by id6 because a child has exactly one
  source; forward-link by setid because a source points at a whole generated Set (its old G4).
- Both directions should be validated, so a dangling forward link is reported the way a dangling
  `From-Backlog` already is (its old G5).
- The within-type descriptive-consistency rule is real and stays.

## 3. The normative model

- **N1 (setid is a grouping label, not an identity).** A setid is a SHARED, cross-type TOPIC label. The
  same setid token MAY appear under any number of record types, and doing so is CORRECT when the
  artifacts concern one topic. Nothing may prevent, rename, or report-as-drift a cross-type setid that
  is used this way.
- **N2 (id6 is the identity, unchanged).** Artifact identity is the id6, already hard-enforced
  (DECISIONS.md D140, `check.id6-collision`, `check.id6-identity-slot`). This spec changes nothing about
  it. Any component needing to name exactly one artifact MUST use an id6, never a setid.
- **N3 (resolution is type-scoped).** Every verb that accepts a setid MUST resolve it WITHIN the
  requested type's tree when a type is known, so `aw ipd set approved <setid>` acts on the plan Set even
  when the token also exists on a backlog item and several research reports. A verb that already knows
  its type MUST NOT fail on cross-type multiplicity.
- **N4 (honest ambiguity, never a generic failure).** Where a type genuinely cannot be inferred and the
  setid resolves into more than one type, the tool MUST report the CANDIDATES BY TYPE and how to
  disambiguate. It MUST NOT emit a generic type-mismatch error, and MUST NOT guess.
- **N5 (the collision check is re-scoped, not deleted).** A cross-type setid is NOT a finding. A setid
  used within ONE type with two different descriptives REMAINS a finding, because that is a genuine
  inconsistency in one Set's own name. The rule keeps its recovery command for the surviving case.
- **N6 (graduation preserves the source's setid by default).** Graduation MUST NOT mint a fresh setid to
  avoid a collision, because the shared name is the feature. A child Set SHOULD carry its source's setid
  when it is the same topic. Distinct setids remain permitted when the work genuinely is a different
  topic; this is a default, not a prohibition.
- **N7 (the typed links carry the relationship, and are not replaced by the name).** N6 does not make
  the links optional. `From-Backlog`/`From-Spec` and `Graduated-To` remain the machine-readable truth,
  because a shared name is a human affordance and not a resolvable reference.

## 4. Accepted costs, stated plainly

1. A BARE SETID STAYS AMBIGUOUS BY DESIGN. Every name-taking verb needs a type scope or a
   disambiguating prompt. The maintainer judged filename-level topic discovery worth more than global
   uniqueness. This is the central trade and it is deliberate.
2. THE 5 SURVIVING DESCRIPTIVE CONFLICTS STILL NEED FIXING. Re-scoping the check does not clean them.
3. NO AUTOMATED CHECK CAN TELL A DELIBERATE TOPIC SHARE FROM A CARELESS ONE. Two unrelated efforts that
   pick the same setid look exactly like one topic spanning types. That is the price of N1, and the
   mitigation is a human noticing, not a rule.

## 5. Acceptance criteria

1. `check.setid-collision` no longer reports a cross-type setid; the 78 backlog+plans findings, the 2
   plans+research and the 1 plans+walkthrough disappear WITHOUT any artifact being renamed.
2. The 5 within-type conflicting-descriptive findings still report, with their recovery command intact.
3. `aw doctor` and `aw check` report the SAME population for this rule (see Section 6).
4. `aw ipd set approved <a setid shared with other types>` succeeds against the plan Set. The
   `agentadhere` case is the regression fixture, since it is the original failure.
5. Where a type cannot be inferred and the setid spans types, the error names the candidates per type.
6. The full suite and `aw check all` are green, with no artifact renamed to achieve it.

## 6. A separate defect this spec must not inherit

`doctor.py:530` hardcodes `include_retired=True` while `check_engine.py:1760` passes a flag defaulting
to `False`, so the SAME predicate reports two different populations to two surfaces. That is the entire
38-versus-86 discrepancy in Section 1 finding 4. It is INDEPENDENT of the setid reversal and predates
it. Whoever implements the re-scope MUST settle which population is authoritative rather than inheriting
the split, because otherwise acceptance criterion 3 cannot be evaluated.

## 7. Non-goals

- The id6 identity invariant (N2): already hard, unchanged.
- The filename grammar itself: owned by the parent spec, unchanged. This spec constrains the SEMANTICS
  of the `<setid>` token, never its shape.
- The runner, its queue ordering, and its dependency handling.
- Renaming any existing artifact. This spec's whole point is that the existing names are correct.
- Per-requirement spec tracking, and any semantic "already implemented" verdict for graduation.

## 8. Open questions

### OQ-01: Should a cross-type setid be reported at `info` for discoverability, or not reported at all?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-10 AS **DO NOT REPORT IT AT ALL**, by applying this
  question's own stated decision rule once the number was measured. The rule was: under roughly a dozen
  `info` lines it is a discoverability feature, at scale it is noise restored under a new severity.
  MEASURED on the DEFAULT `aw check` scope at HEAD: **38 findings across 28 distinct setids**, every one
  of them cross-type (the 5 within-type descriptive cases appear only under `--all`). That is three times
  the threshold this question set, and it is 28 separate topics a reader would have to dismiss on every
  run, so the `info` variant fails its own test.
  A SECOND REASON, INDEPENDENT OF THE COUNT, and the stronger one: an `info` line saying "this setid
  spans three types" trains a reader (and an agent) to treat cross-type sharing as REMARKABLE, which is
  exactly the belief that produced the reversed design. Under N1 it is the NORMAL, CORRECT state, and a
  check that narrates the normal state is not discoverability, it is a standing suggestion that something
  might be wrong. The precedent cited in this question cuts the same way: `check.stale-index-missing` was
  registered at `info` for a state that is expected but ACTIONABLE (run `aw index`). A cross-type setid is
  expected and requires NO action, so it has nothing to report.
  WHAT SERVES TOPIC DISCOVERY INSTEAD, since the underlying need is real: the filename already carries the
  setid, so `ls`, `grep`, and `aw find` already answer "what else is in this topic" without a check rule.
  That is the affordance the maintainer's decision preserved; it does not need a second, noisier channel.
  CONSEQUENCE FOR THE IMPLEMENTER: the re-scoped `check.setid-collision` emits NOTHING for a cross-type
  setid. Do not add an `info` rule, and do not keep the cross-type branch behind a flag: acceptance
  criterion 1 requires those 38 findings to disappear, not to be relabelled.

## Workflow history

- 2026-09-10 note (aw specs): OQ-01 resolved from measurement, not asked: DO NOT report a cross-type setid at all. The question stated its own rule (under roughly a dozen info lines it is discoverability, at scale it is noise under a new severity); measured on the default aw check scope at HEAD it is 38 findings across 28 distinct setids, three times the threshold, so the info variant fails its own test. Added the stronger independent reason: narrating the NORMAL state trains readers to treat cross-type sharing as remarkable, which is the belief that produced the reversed design, and unlike check.stale-index-missing (expected but ACTIONABLE) a cross-type setid needs no action. Recorded that filename-level grep and aw find already serve topic discovery, and instructed the implementer to emit nothing rather than relabel or flag-guard the cross-type branch. Spec now carries zero open questions.
