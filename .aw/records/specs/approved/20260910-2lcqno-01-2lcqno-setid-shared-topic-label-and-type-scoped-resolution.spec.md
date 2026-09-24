# Spec: Setid as a shared cross-type topic label, with type-scoped resolution

- Date: 2026-09-10
- Status: approved
- Id: 2lcqno
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Spec: 4w7d6s
- Scope: A setid is a SHARED cross-type grouping label, not a unique identity; fix the ambiguous lookup (type-scoped resolution) instead of enforcing uniqueness, and re-scope check.setid-collision to the within-type half that is still a real defect.
- Supersedes: `.aw/records/specs/superseded/20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md`
  (`4w7d6s`), whose central invariant the maintainer REVERSED on 2026-09-10. That spec is retained as the
  historical record and its surviving parts are carried forward here rather than cited across a reversal.
- Parent: `.aw/records/specs/implemented/20260817-2147-01-uniform-artifact-naming-grammar.spec.md` (the uniform naming
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

THE FIVE MEASUREMENTS THAT DECIDED IT, all taken at HEAD before the decision and reproducible. EVERY
COUNT BELOW IS A DATED SNAPSHOT, NOT A LIVE INVARIANT: this corpus grows every day, so a re-measurement
that returns a different number CONFIRMS the argument rather than falsifying it. What must survive
re-measurement is the SHAPE (cross-type sharing dominates; the surviving within-type cases are few and
fixable), and Section 5 states the acceptance criteria in shape terms for exactly that reason.

1. CROSS-TYPE SHARING IS THE DOMINANT PATTERN, NOT DRIFT. Of 433 distinct filename-slot setids, **117
   span more than one record type**. The widest are genuine topics: `agentadhere` covers 7 plans + 1
   backlog item + 5 research reports (13 files); `lanectn` covers 7 plans + 7 reviews + 1 walkthrough.
   The predecessor's uniqueness invariant would have forbidden all 117.
   RE-MEASURED 2026-09-13 at HEAD `9697856e`: 431 distinct setids, **130 spanning more than one type**,
   with both named topics unchanged in shape (`agentadhere` 13 files across backlog+plans+research,
   `lanectn` 15 across plans+reviews+walkthroughs). The dominance grew; the conclusion is unchanged.
2. THE SHARING IS PARTLY AUTOMATIC AND DELIBERATE. `review_findings.build_review_name` constructs a
   review's filename from the SUBJECT's setid AND the SUBJECT's id6, documented in that function as "the
   join key ... not a fresh identifier". Plans-and-reviews sharing a setid is therefore designed
   behavior; that pair alone is 47 of the 117, plus 38 more as backlog+plans+reviews.
3. THE MOTIVATING FAILURE WAS A LOOKUP DEFECT. The predecessor's own evidence was `aw ipd set approved
   agentadhere` failing with "selector 'agentadhere' resolved to artifact(s) of type ['backlog',
   'research'] ... scoped to 'plans'". The setter held BOTH the setid and the target type and still gave
   up, when resolution by `(type, setid)` was available and unused. That is a resolution bug, not a
   naming bug, and fixing it is this spec's primary deliverable.
   THIS QUOTED FAILURE NO LONGER REPRODUCES ON THE TYPED PATH, AND THE CORRECTION MATTERS BECAUSE IT
   MOVES THE DELIVERABLE. Re-measured 2026-09-13: `match_selector` accepts `scoped_type` and narrows
   `record_types` to it (`status_set.py:315-317`), so `aw ipd set approved agentadhere` now resolves 7
   plans and acts on them, and the `Type mismatch` refusal (`status_set.py:1290-1299`) is unreachable for
   a SETID. The fix landed in commit `91077905` (2026-08-27), BEFORE this spec was authored, so the
   defect was already closed when the spec quoted it as live. WHAT REMAINS BROKEN is the UNTYPED path:
   `aw set approved agentadhere` still fans out across types and dies on the first artifact whose
   vocabulary rejects the status, naming a backlog item the operator never meant. So N3's typed half is
   ALREADY SATISFIED and needs pinning, not building; N4's untyped half is the live work. This
   correction, and the measurements behind it, come from the graduated child plan `w2y5ac`, whose review
   found it by executing rather than reading (its F-1, F-2). A reader must not treat the quoted error as
   a reproducible symptom.
   ONE FURTHER WARNING, EARNED THE HARD WAY TWICE: `aw ipd set` WRITES BY DEFAULT with no confirmation.
   Reproducing the historical error with a bare `aw ipd set approved agentadhere` reverts all 7 executed
   `agentadhere` plans out of `executed/`. This happened during `w2y5ac`'s authoring (filed as backlog
   `f5pttg`) and AGAIN during this spec's review on 2026-09-13, both times reverted uncommitted. Use
   `--dry-run` for every reproduction.
4. THE CHECK IS CURRENTLY MISLABELLING CORRECT BEHAVIOR. `check.setid-collision` is registered at
   severity `error` (`check_engine.py:95-97`) and reports **38 findings on the default scope and 86 with
   `--all`**. Of the 86, **78** are the backlog+plans topic sharing this spec endorses, 2 are
   plans+research, 1 is plans+walkthrough, and only **5** are within-type conflicting-descriptive cases
   that remain genuine defects.
   RE-MEASURED 2026-09-13 at HEAD `9697856e`, AND THE WITHIN-TYPE HALF IS NOW **ZERO**, which changes what
   an implementer must expect. `aw check` reports **35** (all cross-type, all backlog+plans, 26 distinct
   setids) and `aw check --all` reports **81** (78 backlog+plans, 2 plans+research, 1 plans+walkthrough,
   and **0** descriptive conflicts). The 5 descriptive cases were RESOLVED BY RENAME, not by this spec:
   commit `4f1ca199` (2026-09-11) regrouped six executed plans that shared three setids
   (`release-review` -> `relrev01`/`relrev02`/`relrev03`, `leak-sanitizer` -> `leaksan01`,
   `assess-documentation` -> `assessdoc01`, `assess-bugs` -> `assessbug01`), at the maintainer's own
   suggestion and chosen over widening the rule. CONSEQUENCE FOR THE IMPLEMENTER, stated because it
   inverts an obvious reading: the surviving within-type branch this spec insists on keeping (N5) now has
   an EMPTY population, so it is LATENT BY DESIGN, guarding future cases rather than reporting present
   ones. It must be pinned by a FIXTURE, and a zero count on the real tree is the CORRECT result rather
   than evidence the branch was lost. See Section 4 cost 2, which this measurement supersedes.
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
  ALREADY SATISFIED FOR A SETID as of commit `91077905` (Section 1 finding 3), so the work N3 authorizes
  is a REGRESSION PIN, not a build. It is worth pinning precisely because nothing currently tests it.
  ONE DOCUMENTED HOLE THAT N3 MUST NOT BE READ AS CLOSING: scoped resolution is type-safe for every
  selector kind EXCEPT a direct PATH, because `selectors.resolve`'s path precedence matches an existing
  file regardless of the type requested. The `Type mismatch` refusal is the ONLY guard on that case, and
  plan `w2y5ac`'s review measured that deleting it lets `aw specs set approved <a plan path> --by-human`
  rewrite a PLAN and append a forged human attestation to it, with the suite still green. That refusal
  must be PINNED, never retired as dead code.
- **N4 (honest ambiguity, never a generic failure).** Where a type genuinely cannot be inferred and the
  setid resolves into more than one type, the tool MUST report the CANDIDATES BY TYPE and how to
  disambiguate. It MUST NOT emit a generic type-mismatch error, and MUST NOT guess.
- **N5 (the collision check is re-scoped, not deleted).** A cross-type setid is NOT a finding. A setid
  used within ONE type with two different descriptives REMAINS a finding, because that is a genuine
  inconsistency in one Set's own name. The rule keeps its recovery command for the surviving case.
  THE SURVIVING BRANCH IS LATENT, NOT ACTIVE, and an implementer must expect a ZERO count: the 5 cases
  that motivated keeping it were renamed away in `4f1ca199` (Section 1 finding 4). It is therefore pinned
  by a FIXTURE, and reporting nothing on the real tree satisfies this item rather than violating it.
  THE BRANCH ALSO NEEDS A KEYING FIX, WITHOUT WHICH KEEPING IT IS ILLUSORY. `check_engine`'s `seen_sets`
  is keyed on the setid ALONE and stores the FIRST file seen, and `SUPPORTED` iterates `plans` first, so
  a foreign-type predecessor occupies the slot a within-type comparison needs. Measured by plan `216rgg`'s
  review with one plan plus two conflicting specs: HEAD emits 2 cross-type findings and NEVER the genuine
  spec-vs-spec conflict, and removing the cross-type branch alone emits ZERO. Deleting the cross-type
  emission therefore converts a noisy miss into a SILENT one unless the slot is keyed per type. Both
  halves are required.
- **N6 (graduation preserves the source's setid by default).** Graduation MUST NOT mint a fresh setid to
  avoid a collision, because the shared name is the feature. A child Set SHOULD carry its source's setid
  when it is the same topic. Distinct setids remain permitted when the work genuinely is a different
  topic; this is a default, not a prohibition.
- **N7 (the typed links carry the relationship, and are not replaced by the name).** N6 does not make
  the links optional. `From-Backlog`/`From-Spec` and `Graduated-To` remain the machine-readable truth,
  because a shared name is a human affordance and not a resolvable reference.
- **N8 (a setid's LENGTH is bounded, in two tiers, with a per-repository cutover).** Added 2026-09-23 by
  plan `x75obw`, catalog invariant I-17. A setid of **14 characters or fewer** is strongly PREFERRED; a
  setid of **15 to 24** characters is a WARNING; a setid of **more than 24** characters is REFUSED. The
  thresholds are repository policy, read from the optional `setids` object in `.aw/config/project.json`
  (`warn_length`, `max_length`, `strict`) through the one accessor `config.get_setid_policy`, and MUST
  NOT be re-spelled by any consumer.
  LENGTH IS NOT PART OF THE FILENAME GRAMMAR, DELIBERATELY. The setid group in both naming regexes
  (`artifact_naming.parse_clustered`, `_UNIFORM_RE`) stays UNBOUNDED, because a grammar match is binary
  and could express neither the two tiers nor the cutover below. A length violation is therefore a
  POLICY finding (`check.setid-length-warn` / `check.setid-length-error`, `IPD-M109` on a plan), never a
  nonconformant NAME, and `check.name-nonconformant` must not start reporting it.
  GRANDFATHERING IS PER ARTIFACT, NOT PER SETID, and this follows directly from N1. Because a setid is a
  SHARED label, "the setid's date" is not a quantity that exists: measured 2026-09-23,
  `backlog-medhigh-260819` (22 characters) spans 8 artifacts, `assess-documentation` (20) spans 6, and
  `agent-comms-broker` (18) spans 3, with different dates. Each finding is located AT A FILE, so the
  ARTIFACT'S OWN date is compared against the `cutovers.setid_length` boundary that
  `sync_cutovers_on_install` stamps per repository. An absent boundary FAILS OPEN (everything is
  grandfathered); `strict` removes the grandfathering entirely.
  THE INTENDED CONSEQUENCE, STATED SO AN AUTHOR DOES NOT DISCOVER IT: one long setid can be
  simultaneously grandfathered on an old artifact and refused on a new one, so a NEW artifact may NOT
  join an existing long-setid topic after the cutover. That is the whole mechanism by which the corpus
  stays green while new long setids stop appearing, and it is an accepted usability cost (see Section 4
  item 5), not a defect.
  AUTHORING REFUSES BEFORE THE FACT, through one shared validator
  (`config.validate_setid_length_for_authoring`) called by the four `--set`-taking verbs: `aw ipd
  scaffold`, `aw backlog new`, `aw research new`, `aw group`. `aw specs new` is EXCLUDED because it takes
  no `--set` at all (`specs.run_new` passes `set_id=id6`, so a standalone spec's setid is always its own
  6-character id6); a guard there would be unreachable code. The authoring guard deliberately consults NO
  cutover: a setid being chosen now is post-cutover whatever the boundary says.

## 4. Accepted costs, stated plainly

1. A BARE SETID STAYS AMBIGUOUS BY DESIGN. Every name-taking verb needs a type scope or a
   disambiguating prompt. The maintainer judged filename-level topic discovery worth more than global
   uniqueness. This is the central trade and it is deliberate.
2. THE SURVIVING DESCRIPTIVE-CONFLICT BRANCH GUARDS AN EMPTY POPULATION. As authored this cost read "the
   5 surviving descriptive conflicts still need fixing"; they were fixed on 2026-09-11 by rename
   (`4f1ca199`), so the residual cost is different and smaller: the repository now carries a rule that
   reports nothing, whose correctness rests entirely on a fixture. A latent rule is cheap to keep and
   easy to lose in a refactor, which is why N5 requires the pin.
3. NO AUTOMATED CHECK CAN TELL A DELIBERATE TOPIC SHARE FROM A CARELESS ONE. Two unrelated efforts that
   pick the same setid look exactly like one topic spanning types. That is the price of N1, and the
   mitigation is a human noticing, not a rule.
5. THE `> 24` REFUSAL (N8) HAS ZERO MARGIN, AND A NEW ARTIFACT CANNOT JOIN A LONG-SETID TOPIC. Measured
   2026-09-23 over 749 unique declared setids: 713 at 14 or fewer, 36 in the 15-to-24 band, and 0 over
   24, with the longest being `research-prompt-pipeline` at EXACTLY 24 characters. So 24 was chosen to
   sit AT the existing maximum rather than above it, which has two consequences worth stating. FIRST, the
   comparison must be strictly `> max_length`: an off-by-one would hard-fail a live record, which is why
   the tests pin 24-conforms and 25-errors rather than testing a comfortable 26. SECOND, the 36 setids in
   the warn band are permanently grandfathered on their existing artifacts but are CLOSED to new members
   once the repository's boundary is stamped, so continuing one of those topics means regrouping it under
   a shorter setid. Both are accepted, not defects.
6. EVERY COUNT IN THIS SPEC IS A DATED SNAPSHOT OF A GROWING CORPUS. The numbers in Section 1 were true
   when measured and are re-measured inline where they moved; none of them is a live invariant, and an
   implementer must re-derive rather than assert them (see Section 5, which is written in shape terms for
   this reason).

## 5. Acceptance criteria

EACH CRITERION STATES A SHAPE PLUS THE EVIDENCE THAT SATISFIES IT, and none is an equality against a
literal count. That is deliberate and is the lesson of Section 1: the counts moved between authoring and
review, so a criterion phrased as "the 78 findings disappear" would fail for a reason unrelated to the
change. Every criterion below requires the implementer to RE-DERIVE the number at execution time and to
report the denominator alongside it, so a zero is corroborated rather than assumed.

1. `check.setid-collision` reports NO cross-type finding, on either surface and on every population, and
   NO artifact was renamed to achieve it. Evidence: the cross-type count before and after (re-derived, not
   quoted from this spec), plus a `git status` proving no tracked record moved or changed.
2. The within-type conflicting-descriptive emission SURVIVES and is proven by a FIXTURE, because its
   real-tree population is now empty (Section 1 finding 4). Evidence: a fixture case that fires, plus a
   mutation check (break the descriptive comparison, show the pin FAILS, restore, show it passes). A zero
   count on the real tree is expected and is NOT evidence of loss; a zero count with no fixture is.
3. The fixture of criterion 2 includes the SHARED-SLOT case (one plan plus two same-type records with
   conflicting descriptives) and reports the genuine same-type conflict, which neither HEAD nor a
   same-type-guard-alone fix does. This is what proves N5's keying fix rather than only its guard.
4. `aw doctor` and `aw check` report the SAME population for this rule, on BOTH axes: `include_retired`
   AND doctor's independent demotion of findings under `executed/`. Evidence: the two surfaces' counts
   printed side by side and equal. See Section 6, which the review corrected from a two-way to a
   three-way split.
5. `aw ipd set approved <a setid shared with other types>` acts on the plan Set only. Already true
   (Section 1 finding 3), so the evidence is a REGRESSION TEST that fails when `match_selector`'s type
   narrowing is reverted, not a demonstration that the command works.
6. The direct-PATH cross-type write remains REFUSED. Evidence: `aw specs set approved <a plan path>
   --by-human` exits nonzero and writes nothing, and a test pins it (nothing does today).
7. Where a type cannot be inferred and the setid spans types, the untyped setter reports the candidates
   GROUPED BY TYPE with a runnable disambiguating command, exits nonzero, and WRITES NOTHING. Evidence:
   the `agentadhere` case's output plus a clean `git status` after it.
8. The full suite passes and `aw check all` is NO WORSE than its pre-change baseline, with both counts
   pasted. Not "green": the tree carries known unrelated findings, so an absolute-green criterion would be
   unsatisfiable and would invite editing the number instead of the code.

## 6. A separate defect this spec must not inherit

`doctor.py:538` hardcodes `include_retired=True` while `check_engine.py:1763` passes a flag defaulting
to `False`, so the SAME predicate reports two different populations to two surfaces. That is most of the
38-versus-86 discrepancy in Section 1 finding 4. It is INDEPENDENT of the setid reversal and predates
it. Whoever implements the re-scope MUST settle which population is authoritative rather than inheriting
the split, because otherwise acceptance criterion 4 cannot be evaluated.

THE SPLIT IS THREE-WAY, NOT TWO-WAY, and this correction is load-bearing because reconciling
`include_retired` alone CANNOT make the surfaces agree. `doctor.py:519-528` independently demotes any
finding located under `executed/` into `executed_warnings` unless `include_executed` is set, which is a
second axis. Measured 2026-09-13 at HEAD `9697856e`: the predicate returns 81 with retired records
included, `aw doctor --agent` surfaces 81, and `aw check` surfaces 35. (At authoring the same three
numbers were 86 / 81 / 38, the difference being the 5 descriptive cases since renamed away.) Both axes
must be settled, and criterion 4 requires the two surfaces' counts pasted side by side and EQUAL.

THIS SPEC DOES NOT DECIDE WHICH POPULATION WINS, and that is a deliberate boundary rather than an
omission: the choice is a `aw check` product decision about whether a retired record is in scope for any
rule, which reaches far past this rule. Plan `216rgg` carries it as its own open question. What this spec
requires is only that the two surfaces AGREE and that the choice be stated.

## 7. Non-goals

- The id6 identity invariant (N2): already hard, unchanged.
- The filename grammar itself: owned by the parent spec, unchanged. This spec constrains the SEMANTICS
  of the `<setid>` token, never its shape.
- The runner, its queue ordering, and its dependency handling.
- Renaming any existing artifact TO SATISFY THE CROSS-TYPE RULE. This spec's whole point is that a
  cross-type name is correct, so achieving the rule's silence by renaming would defeat it, and criterion 1
  requires proving no record moved.
  THE EXCEPTION, RECORDED BECAUSE IT ALREADY HAPPENED: renaming to resolve a WITHIN-TYPE descriptive
  conflict is legitimate and is not what this non-goal forbids. On 2026-09-11 the maintainer renamed six
  executed plans for exactly that reason (`4f1ca199`), choosing it over widening the rule. That is
  consistent with N5, which calls a within-type conflict a genuine defect; the two cases must not be
  conflated.
- Deciding whether `aw check` scans retired records at all (Section 6). This spec requires only that the
  two surfaces agree.
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
  criterion 1 requires the cross-type findings to disappear, not to be relabelled. (The count was 38 at
  resolution and 35 when re-measured 2026-09-13; the decision rests on the order of magnitude, which is
  unchanged, so nothing here turns on the exact figure.)

## Workflow history
- 2026-09-13 approved (aw set, --by-human): status set to approved
- 2026-09-13 reviewed (aw set): spec-review round 1 (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; SR-001..SR-009, all nine FIXED, none deferred, none open. Re-measured every count at HEAD 9697856e and four of six acceptance criteria were falsified by drift while the ARGUMENT strengthened (cross-type sharing grew 117 -> 130 topics), so Section 5 was rewritten in SHAPE terms with a re-derive-and-report-the-denominator rule. THE FINDING THAT CHANGES AN IMPLEMENTER'S EXPECTATION: the 5 within-type descriptive conflicts N5 exists to preserve were RENAMED AWAY on 2026-09-11 (4f1ca199), so that branch now returns ZERO on every population and is LATENT BY DESIGN, pinned by a fixture. The motivating failure also no longer reproduces: the typed path was fixed in 91077905 BEFORE this spec was authored, so N3 needs PINNING not building and the live defect is the UNTYPED path. Added the keying fix N5 requires (seen_sets is setid-keyed, so deleting the cross-type branch turns a noisy miss silent), the three-way doctor/check population split, and the direct-PATH forged-attestation hole N3 must not be read as closing. DISCLOSED: verifying the quoted failure with a bare 'aw ipd set approved agentadhere' reverted 7 executed plans out of executed/; reverted path-scoped, verified byte-identical, nothing committed, and the warning is now in the spec.

- 2026-09-10 to-review (aw specs): Ready for critique: seven normative items, five measurements, three accepted costs, six acceptance criteria, and zero open questions (OQ-01 resolved from measurement).
