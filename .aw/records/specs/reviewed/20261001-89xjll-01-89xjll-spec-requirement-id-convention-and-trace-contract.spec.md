# Spec: Spec Requirement ID Convention and the SPEC-PLAN-TRACE Contract

- Date: 2026-10-01
- Status: reviewed
- Id: 89xjll
- Author: opencode / antigravity (IPD jjh4aj)
- From-Backlog: vy20et
- From-Spec: 25kzda
- Scope: Requirement-ID convention for new specs, acceptance-criterion namespace, declaration-site rule, retrofit policy via stamped cutover, and SPEC-PLAN-TRACE verification contract (scope, severity, grandfathering behavior, and citation-not-implementation limit).

## Workflow history

- 2026-10-02 note (aw specs): /spec-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; SR-001..SR-010 (SR-002, SR-003 OPEN, gate approval)
- 2026-10-03 reviewed (aw set): REVIEWED - OPEN QUESTIONS; SR-001,SR-004..SR-010 FIXED; SR-002,SR-003 OPEN as blocking OQ-05,OQ-04

- 2026-10-01 to-review (aw specs): Authored review-ready by IPD jjh4aj graduating backlog vy20et: defines requirement and acceptance namespaces, declaration-site rule, stamped cutover retrofit policy, and SPEC-PLAN-TRACE contract
- 2026-10-01 created (aw specs): Spec Requirement ID Convention and the SPEC-PLAN-TRACE Contract

## 1. Why this exists

Approved spec `25kzda` 4.8 ("IPD authoring from an approved spec" table, row `SPEC-PLAN-TRACE`) declares the check with this pass criterion, quoted verbatim:
"Every mandatory spec requirement maps to at least one E item and every acceptance criterion maps to at least one V item; there are no unknown references"
Its action is `RETRY, then FAIL ITEM`, and its message template, quoted verbatim, is:
`[SPEC-PLAN-TRACE] Generated IPD <plan-id> does not cover spec items: <ids>. Correct and sync the IPD, then: aw <host> run resume <run-id>`

While its three sibling verification codes shipped in `production_checks.py` (`spec_plan_count`, `spec_plan_conformance`, and `spec_plan_gate_carry`), `SPEC-PLAN-TRACE` was deferred by spec `z7nbn1` 4.4 to backlog `vy20et` because requirements carried no machine-readable identifiers by any agreed convention. `z7nbn1` 4.4 additionally bound the repository to the restriction that "a produced plan MUST NOT be described as trace-verified" until this contract exists.

Earlier research `vkub9o` (2026-09-20) surveyed the 36-spec corpus and recommended option B-minus: a convention for new specs, and explicitly "Do NOT build: a requirement parser, a plan-side requirement declaration field, a partial spec status, a requirements-outstanding attention view, or `implemented` computed from coverage" (`vkub9o` Section 5, item 3). THIS SPEC DEPARTS FROM THAT RECOMMENDATION IN ONE RESPECT, deliberately: it specifies a requirement parser, scoped to the single producing spec at production time. The basis is the maintainer's 2026-09-26 ruling recorded in backlog `vy20et` (the convention AND parser are to be decided as their own spec, with TRACE waiting on it), plus the fact that `vkub9o`'s decisive objection (Section 3.2: "The blocker is the missing plan-to-spec edge, not the missing requirement parser") does not hold at production time: the production dispatcher in `runner_shared.py` computes the newly produced plans directly (`new_produced_paths`, every plan whose id is not in `baseline_plan_ids`) and passes them to the sibling verifiers, so the join edge is in hand. Every other item on `vkub9o`'s do-not-build list remains a non-goal of this spec (Section 1a).

Furthermore, `vkub9o` Section 3 measured that three of five observed harm cases were ADDRESSING failures that a stable requirement-ID convention resolves, independent of any whole-corpus coverage tracking:
1. In `25kzda`, the 0..10 retry budget bound appeared across four different sections (§1.4, §2.1, §4.1, §5.5) without a canonical identifier; the one requirement was tracked by two backlog items (`trjfyy`, `eh91an`) and a plan (`xipfy1`, since executed).
2. An author cited `25kzda` §2.1 line 211, their reviewer mistakenly "corrected" it to §1.1 line 586, and a code comment cited "spec 2.1's 0..10 bound" while the bound appeared in four places: three parties disagreeing about where one requirement lives.
3. Code comments drifted from spec citations because there was no stable symbol or identifier to reference.

This specification resolves the convention, the namespaces, the declaration rule, the retrofit boundary, and the verification contract so that Order 02 (`rtvdak`) implements a specified check rather than guessing. Its normative requirements are indexed with stable ids in Section 1b.

## 1a. Non-goals

- NOT a retrofit of any existing spec's requirement text or ids (Section 5; `vkub9o` Q5).
- NOT a corpus-wide `aw check` rule over requirement ids. Going-forward conformance of a NEW spec's ids is enforced by spec review, not by a check rule (`vkub9o` Option B records why a corpus rule either exempts most specs or reds every run).
- NOT a requirements-outstanding `aw attention` view, a partial spec status, a plan-side requirement declaration field, or `implemented` computed from coverage (`vkub9o` Section 5, item 3).
- NOT an amendment to `25kzda` (OQ-02).
- NOT a semantic coverage judgement: TRACE is a citation gate only (Section 6.4).

## 1b. Requirements index (canonical declaration site)

This table is the single canonical declaration of this spec's requirements; the cited sections elaborate them and do not restate them as separate obligations.

| ID | Requirement | Detail |
| --- | --- | --- |
| R-1 | Requirement ids in a post-cutover spec are drawn from the admitted families; acceptance ids from the distinct `A`/`AC` namespace. | 3.1, 3.2 |
| R-2 | An id is extracted only at a declaration site; a mention is never extracted. | 4.1 |
| R-3 | Grandfathering is per spec against the stamped `spec_requirement_ids` cutover, via `config.KNOWN_FEATURE_CUTOVERS`, with a non-`None` fallback. | 5.1 |
| R-4 | TRACE runs only at spec production, against the single producing spec and its newly produced plans, evaluated across the produced plan set. | 6.1 |
| R-5 | TRACE renders `25kzda` 4.8's action and message template verbatim and implements all three conjuncts of its pass criterion. | 6.2, 6.2a |
| R-6 | TRACE passes a grandfathered spec and a spec with no traceable ids. | 6.3 |
| R-7 | TRACE is described only as a citation gate, never as proof of implementation; a plan from a grandfathered or zero-id spec is not described as trace-verified. | 6.4 |

## 2. Measured corpus evidence (HEAD census)

At execution HEAD `f279e326`, recursive census of `.aw/records/specs/` demonstrates:
- Total specs: 39 (12 `approved`, 2 `deferred`, 2 `draft`, 15 `implemented`, 2 `implementing`, 1 `reviewed`, 3 `superseded`, 2 `to-review`).
- Live specs: 21; Terminal specs: 18 (`implemented`, `superseded`, `parked`).
- Specs without `- Id:`: 19 total, but only 2 live specs lack `- Id:`, both of which are `deferred` legacy specs (`20260725-0957-01` and `20260726-1239-01`).
- Requirement ID availability across live specs: exactly 2 live specs carry no requirement ID of any form (`25kzda`, which is section-addressed, and `kw5y2s`). The other 19 live specs already carry addressable requirement IDs or section handles.
- Approved specs requirement status: 10 of 12 `approved` specs already carry requirement IDs (`5tapom`, `7ckptx`, `6m4kow`, `77tr3o`, `2vev8j`, `2lcqno`, `6kwd2e`, `w15vzb`, `uonrjg`, `r07vma`). Only 2 lack them: `25kzda` (section-addressed) and `kw5y2s`.
- Approved specs acceptance status (corrected at review, SR-006): 6 of 12 `approved` specs carry acceptance-criterion IDs (`7ckptx` 36, `6kwd2e` 49, `uonrjg` 25, `w15vzb` 12, `6m4kow` 11, `2vev8j` 11). 4 carry an acceptance heading with no IDs (`5tapom`, `kw5y2s`, `2lcqno`, `r07vma`), and 2 carry no acceptance heading (`25kzda`, `77tr3o`). `25kzda`'s `| A1:` .. `| A4:` rows are NOT acceptance criteria: they sit in `### 1.4 Resolution of the required revisions` and label resolved revisions. They are nonetheless matched by the declaration-site rule of Section 4.1 as written, which is harmless only because `25kzda` is grandfathered (Section 5); it is recorded here as evidence that the rule is section-blind (see OQ-04).
- Prefix-letter semantics are NOT uniform across the corpus (measured at review): `N` declares NORMATIVE items in `2lcqno` (`- **N1 (setid is a grouping label ...)**`, under `## 3. The normative model`) but NON-GOALS in `2vev8j` (`- N1 NOT a rewrite ...`, under `## 3a. Non-goals`). `2vev8j` also declares `E1`..`E4` evidence items and `uonrjg`/`6m4kow` declare `D*` decisions; `E` and `D` are not admitted families, so those are correctly not requirements.
- Census re-measured at review HEAD `81cb4f85`: 40 specs (this spec is the 40th; `to-review` now holds 3). Every other figure above reproduced.
- Verification entry point: `run_selection_policy._SPEC_ACTIONS` maps strictly `approved` to `ACTION_PLAN` (all other statuses map to `skip` or `review`). Thus, spec production and `SPEC-PLAN-TRACE` judge exclusively the `approved` spec population and the plans newly produced from it.

## 3. Requirement and Acceptance Namespaces

The requirement namespace and the acceptance-criterion namespace are DISTINCT and must not be conflated.

### 3.1 Requirement Namespace for New Specs

For new specifications, requirement IDs must be drawn from the recognized prefixed families that the repository already uses, rather than mandating a single prefix letter.

1. **Admitted Prefixed Families (FORM A)**: The uppercase prefix letters `R`, `F`, `G`, `I`, `N`, `C`, `P`, `T`, `B`, `H` followed by an optional hyphen or underscore and a sequence of digits and sub-indices:
   - `R` (Requirements): e.g. `R1`, `R-1`, `R1.1`, `R1.1a`, `R-10` (used in `7ckptx`, `6m4kow`, `77tr3o`, `6kwd2e`, `w15vzb`, `r07vma`).
   - `F` (Functional requirements): e.g. `F1`, `F-01`, `F1.1` (used in `5tapom`, `4sd62s`).
   - `G` (Goals / Guarantees): e.g. `G1`, `G-1` (used across historical and implemented specs).
   - `I` (Invariants): e.g. `I-01`, `I-1` (used in `pqsx96`).
   - `N` (Normative items): e.g. `N1`, `N-1` (used in `2vev8j`, `2lcqno`).
   - `C` (Criteria / Constraints): e.g. `C1`, `C-1` (used in `2vev8j`, `llbr2b`, `wy9aru`, `4sd62s`).
   - `P` (Policy / Principles): e.g. `P1`, `P-1` (used in `4sd62s`).
   - `T` (Technical requirements): e.g. `T1`, `T-1` (used in deferred delivery specs).
   - `B` / `H` (Behavioral / Hygiene requirements): e.g. `B1`, `H1` (used in `5tapom`).
2. **Dotted Paragraph Numbers (FORM B)**: Numbered clauses formatted as `<major>.<minor>` at the start of a paragraph (e.g. `1.1`, `1.2`, `2.1` as used systematically throughout `z7nbn1` across 30 clauses).
3. **Numbered Section Handles (FORM C)**: Explicit numbered headings formatted as `## <n>.` or `### <n>.<n>` (as used in `25kzda` across 61 numbered sections).

Grounding in census evidence: Mandating a single prefix letter such as `R` would leave 3 of the 10 id-carrying `approved` specs outside the convention (`2vev8j` using `C*`/`N*`, `2lcqno` using `N*`, `5tapom` using `B*`/`H*`/`F*`), as well as pending/draft specs (`pqsx96`, `llbr2b`, `wy9aru`, `4sd62s`). (Corrected at review, SR-006: the draft said 5 while naming 3. All of these predate the cutover and are grandfathered either way, so the argument is about matching established practice for NEW specs, not about invalidating existing ones.)

WHICH ADMITTED FORMS ARE TRACE-MANDATORY IS NOT YET DECIDED (OQ-04). Admitting a form as a valid ADDRESSING handle (something a plan, comment, or reviewer may cite) is not the same as making every occurrence of it a mandatory requirement that `SPEC-PLAN-TRACE` demands an `E-*` citation for. Under OQ-01 Option A, FORM C as written makes every numbered heading of a post-cutover spec (including `## 1. Why this exists`) a mandatory requirement, and an `N`-prefixed non-goal (the `2vev8j` usage) a mandatory requirement too. Section 6 MUST NOT be implemented until OQ-04 is ratified.

### 3.2 Acceptance-Criterion Namespace (Distinct from Requirements)

Acceptance criteria represent verifiable conditions demonstrating that requirements have been satisfied. They occupy a separate namespace:
- **Admitted Prefixes**: `A` and `AC`, formatted as `A<n>`, `A-<n>`, `A<n>.<n>`, `A<n><letter>`, `AC<n>`, `AC-<n>`, or `A<n>:` in markdown lists or tables (e.g., `A1`, `A-01`, `AC-1`, `A1.`, `A1a`, `A1:`).
- **Separation from Requirements**: Acceptance criteria are strictly distinct from requirement IDs. As measured in `vkub9o` 1.2, treating `A*` identifiers as requirements would inflate the requirement population while conflating obligations with validation conditions. Under `SPEC-PLAN-TRACE`, requirements map to plan `E-*` checklist items, whereas acceptance criteria map to plan `V-*` validation checklist items. The two namespaces must never collide.

Census figures cited: Across the 12 `approved` specs, 7 carry acceptance-criterion IDs (`7ckptx`: 36 IDs; `6kwd2e`: 49 IDs; `uonrjg`: 25 IDs; `w15vzb`: 12 IDs; `6m4kow`: 11 IDs; `2vev8j`: 11 IDs; `25kzda`: 4 table rows), while 4 specs have an acceptance heading without IDs and 1 lacks an acceptance heading.

## 4. Declaration-Site Rule and Addressing Rationale

### 4.1 The Declaration-Site Rule

To enable deterministic parsing, an identifier is binding as a declared requirement or acceptance criterion if and only if it occurs at a valid declaration site.

**The Declaration-Site Rule (Verbatim Contract)**:
An identifier is a DECLARED spec requirement or acceptance criterion if and only if:
1. It appears at the beginning of a line outside of code blocks (fenced blocks with ```` or ```` ``` ````), preceded by at most one structural marker:
   - A markdown bullet marker: `- `, `* `, or `+ `;
   - A table row pipe marker: `|` followed by whitespace;
   - A markdown heading marker: `## `, `### `, `#### `, etc.;
   - Or bare text at the start of a paragraph (preceded by a blank line or start of section);
2. Its initial token matches an admitted requirement ID or acceptance criterion ID grammar, optionally wrapped in markdown bold (`**...**`) or backticks (`\`...\``);
3. It is immediately followed by a delimiter (such as a colon `:`, period `.`, hyphen `-`, whitespace, closing formatting markers, or a table delimiter `|`) and the accompanying normative statement.

Any occurrence of an identifier that fails this structural test, such as an identifier appearing mid-sentence, inside a parenthetical note, within running paragraph prose, or as a reference to another specification (e.g., "referencing `77tr3o` R-5" or "(spec 2.1's 0..10 bound)"), is a MENTION, not a declaration. A mention conveys no obligation and MUST NOT be extracted by the requirement parser or counted by `SPEC-PLAN-TRACE`.

### 4.2 Addressing Rationale

A formal addressing convention is established to eliminate citation ambiguity. In-tree research `vkub9o` Section 3 measured five concrete cases of drift and waste:
1. Three of the five cases were addressing failures where authors, reviewers, and code comments could not agree on how to reference a requirement because no stable identifier existed.
2. In `25kzda`, the retry-budget bound was duplicated across four sections without an ID, causing confusion between implementers and reviewers (the plan-review finding PR-305 that `vkub9o` 3.3 shows was itself a wrong correction).
3. A code comment cited "spec 2.1's 0..10 bound" by section number while the bound is stated in four sections (`vkub9o` 3.3). (Corrected at review: the draft cited `runner_shared.py:6636` as a comment; `vkub9o` records that line as the code call `run_recovery.validate_retry_budget(cli_value)`, and the line has since moved.)

A stable declaration-site identifier provides a singular, durable handle for specifications, plans, code comments, and automated gates.

## 5. Retrofit and Grandfathering Policy

### 5.1 Cutover Registration via KNOWN_FEATURE_CUTOVERS

The retrofit boundary is governed by the repository's single existing cutover registry, `config.KNOWN_FEATURE_CUTOVERS`, rather than inventing a secondary mechanism.

1. **Feature Key**: The feature key registered in `config.KNOWN_FEATURE_CUTOVERS` is `spec_requirement_ids`.
2. **Stamped Boundary**: The enforcement boundary is STAMPED per repository in `.aw/config/project.json` under `cutovers.spec_requirement_ids` (synchronized during installation via `sync_cutovers_on_install`) and resolved with `config.resolve_cutover_date(repo, "spec_requirement_ids")`. Order 02 (`rtvdak`) registers the key with its FEATURE INTRODUCTION date in `config.KNOWN_FEATURE_CUTOVERS`. Because `resolve_cutover_date` fails open to `None` where neither the stamped key nor install history exists (a fresh clone or CI checkout), the consumer MUST also carry a non-`None` module fallback constant, exactly as `check_engine.PROMPT_ID6_CUTOVER_DATE` and `WALKTHROUGH_ID6_CUTOVER_DATE` do; without it every spec is grandfathered forever and TRACE ships as decoration. (Sharpened at review, SR-007: the draft's "not hardcoded into source logic" contradicted that precedent.)
3. **Per-Spec Grandfathering**: Grandfathering is evaluated PER SPEC by comparing the spec FILENAME's leading `YYYYMMDD` date to the resolved boundary: a spec whose filename date is at or after the boundary is bound; earlier is grandfathered. This is the comparand every shipped cutover uses (`check_engine._spec_requires_id6`), and a filename with no parseable leading date is treated as grandfathered, as there. Front-matter `- Date:` is NOT consulted, so there is one comparand, not two. Consequence, accepted: a pre-cutover spec stays grandfathered even if its body is later rewritten. Grandfathered specifications remain valid indefinitely and are not required to adopt requirement IDs.
4. **Going-Forward Rule**: New specifications authored on or after the cutover date must conform to the requirement and acceptance namespaces and declaration-site rules. Existing prose-only live specifications (`kw5y2s` and section-addressed `25kzda`) are grandfathered as policy, in accordance with `vkub9o` Q5.

### 5.2 Accepted Cost of Grandfathering

As documented in `vkub9o` Option B, the accepted cost of per-spec grandfathering is that an external reader or naive automated tool cannot distinguish an exempt legacy specification from a non-conforming specification without consulting the repository's cutover timestamp. This trade-off is accepted to avoid rewriting approved historical records, retrofitting completed specifications, or causing breaking check failures on existing code.

## 6. The SPEC-PLAN-TRACE Verification Contract

### 6.1 Check Scope

`SPEC-PLAN-TRACE` runs exclusively as a post-generation gate during the spec production action (`aw <host> run <spec-id6>`). As measured in `run_selection_policy._SPEC_ACTIONS`, only specifications with status `approved` map to `ACTION_PLAN`.

The check inspects the newly produced plans against the SINGLE producing specification that was dispatched. It does NOT inspect the entire repository corpus. The produced plans are in hand at execution time: as measured in `runner_shared.py`, the dispatcher identifies `new_produced_paths` by comparing the target tree's plans against `baseline_plan_ids` before invoking verifiers. It is wired at the SPEC production block only, not the near-identical backlog production block.

COVERAGE IS EVALUATED ACROSS THE PRODUCED PLAN SET, not per plan (added at review, SR-004): a requirement cited by an `E-*` item of ANY produced plan is covered, and an acceptance criterion cited by a `V-*` item of any produced plan is covered. An Order-0 orchestrator's typed child-tracking rows (`ipd_lint._ORCH_ROW_RE`, `CONFIRM <child-id6> REACHED <status>`) cite no requirement by construction and contribute nothing; they are not a violation. A per-plan reading would fail every produced Set that has an orchestrator for a reason unrelated to coverage. Basis: `SPEC-PLAN-COUNT`'s existing set-level reading ("At least one new IPD links to the spec") and plan `rtvdak`'s resolved open question on the same point. Which text of an `E-*`/`V-*` item counts as citing (the item's first line only, or its sub-fields too) is an implementation choice the implementing plan MUST state and pin with a test; this spec does not fix it.

### 6.2 Severity, Action, and Message Template (Adopting 25kzda 4.8)

This specification ADOPTS the `SPEC-PLAN-TRACE` row from `25kzda` 4.8 verbatim, without amendment. The row is reproduced here exactly as it reads in `25kzda` 4.8. (Corrected at review, SR-001: the draft's quotation altered both the pass criterion and the message template while claiming to quote them verbatim; the decision to adopt verbatim is unchanged.)
- **Action**: `RETRY, then FAIL ITEM`.
- **Pass Criterion**: "Every mandatory spec requirement maps to at least one E item and every acceptance criterion maps to at least one V item; there are no unknown references"
- **Message Template**:
  `[SPEC-PLAN-TRACE] Generated IPD <plan-id> does not cover spec items: <ids>. Correct and sync the IPD, then: aw <host> run resume <run-id>`

The new verifier `production_checks.spec_plan_trace` renders this exact template and returns `list[tuple[str, str, str]]` of `(code, plan_id, message)`, taking the argument shape of `spec_plan_conformance(repo, spec_id6, produced_paths, *, host, run_id)` specifically, because it is the only sibling that takes `run_id` and the template contains `<run-id>`. Because coverage is set-level, `<plan-id>` names a produced plan the finding is reported against; the implementing plan states which.

### 6.2a The third conjunct: "there are no unknown references"

The adopted pass criterion has THREE conjuncts and all three are in scope (added at review, SR-002). The third is the reverse direction: a produced plan that cites, as an id of THIS producing spec, an identifier the spec does not declare (a typo such as `R-99`, or a stale citation) fails. It is reported with the same template, the unknown ids carried in `<ids>`. A produced plan routinely mentions OTHER specs' ids (for example "`77tr3o` R-5"), so a rule that treats every id-shaped token in a plan as a citation of the producing spec would fire constantly. HOW a plan-side token is attributed to the producing spec is NOT decided by this spec and is OPEN (OQ-05, blocking).

### 6.3 Grandfathered-Spec and No-IDs Behavior

When the producing specification predates the cutover date or declares zero requirement/acceptance IDs (such as legacy grandfathered specs), `SPEC-PLAN-TRACE` evaluates to a PASS with no findings. It must not fail or refuse plan production on specifications that were never required to adopt requirement IDs. Likewise a spec that declares requirement ids but no acceptance ids cannot fail the acceptance half, and vice versa.

Honest consequence: at review HEAD every one of the 12 `approved` specs predates any plausible cutover, so on the current approved population TRACE passes vacuously. It begins to bind only on specs authored after the stamped boundary.

### 6.4 The Honest Limit (Citation vs. Implementation)

A successful `SPEC-PLAN-TRACE` check confirms that every declared mandatory requirement ID is cited by at least one `E-*` execution checklist item and every declared acceptance criterion ID is cited by at least one `V-*` validation checklist item across the produced plans.

**The Honest Limit (Verbatim Contract)**:
A trace check proves only that a plan step CITES a requirement or acceptance identifier; it does NOT prove that the plan correctly, completely, or safely implements the requirement. `SPEC-PLAN-TRACE` is a structural citation gate, never a semantic proof of implementation. A produced plan verified by this check may be described as trace-verified against declared identifiers, but MUST NOT be described as having verified the semantic correctness of the implementation. A PASS produced by the grandfathered or zero-id path of Section 6.3 is VACUOUS and MUST NOT be described as trace-verified at all; the verifier's result must make the vacuous case distinguishable from a real pass.

Further limits: the check does not prove the spec's ids are the RIGHT decomposition of its obligations, does not detect an obligation written in prose without an id, and does not detect a post-cutover spec whose author used an unadmitted shape (such ids are simply not extracted; going-forward conformance is enforced by spec review, Section 1a).

This explicit limit, once Order 02 (`rtvdak`) ships the check, replaces the prohibition in `z7nbn1` 4.4 for non-vacuous passes; until then the prohibition stands (Section 7).

## 7. Relations to Other Specifications

- **`25kzda` 4.8**: ADOPTED VERBATIM. The pass criterion, message template, and `RETRY, then FAIL ITEM` action are adopted exactly as specified. No amendment to `25kzda` is made.
- **`z7nbn1` 4.4**: Addresses the deferral of `SPEC-PLAN-TRACE` to backlog `vy20et`. Note that this deferral is addressed by this specification, but is NOT discharged until Order 02 (`rtvdak`) implements the parser and wires the check into `runner_shared.py`.
- **Research `vkub9o`**: Cites the census methodology and harm findings. DEPARTS from its Section 5 "do not build a requirement parser" recommendation, scoped to production time, on the basis stated in Section 1; every other item on its do-not-build list is kept as a non-goal (Section 1a).
- **Plan `rtvdak`** (Order 02, depends on this spec): implements R-1 through R-7. Direction: `rtvdak` depends on this spec reaching `approved`; this spec does not depend on `rtvdak`.
- **Backlog `vy20et`**: the item this spec graduates. It carries no `- Blocks-Release:`, so there is no release gate to inherit.

## 8. Open Questions (Recommendations for Spec Review)

OQ-01 through OQ-03 were resolved on repository evidence by the author. These resolutions are agent recommendations awaiting human ratification via the human approval attestation (`aw spec set approved <id6> --by-human`), not maintainer determinations or approvals. OQ-04 and OQ-05 were raised at review and are OPEN and BLOCKING: each changes what the implementing plan must build, and neither is answered by the repository. Owner: maintainer. Each closes by a recorded decision in this section before approval.

### OQ-01: How is a "mandatory" spec requirement identified, given that no marker is in general use?

- **Options Considered**:
  1. (Option A) Every declared requirement ID is mandatory unless explicitly tagged with an optional marker (e.g. `[Optional]`, `(optional)`).
  2. (Option B) Adopt the `[Must]` marker as the sole discriminator of mandatory requirements.
  3. (Option C) Require each specification to list its mandatory requirement subset in front matter or a dedicated section.
- **Recommended Answer**: Option A (fail-closed: every declared requirement ID is mandatory by default).
- **Evidence & Rationale**: Census measurements show that `[Must]` appears in only 2 of 12 `approved` specifications (`2vev8j`, `5tapom`). Under Option B, `SPEC-PLAN-TRACE` would be vacuous for 10 of 12 approved specs, passing by default and teaching authors to treat the gate as decoration. Option A fails closed, aligning with all other safety gates in this repository.
- **Marker grammar, made exact at review (SR-005)**: under Option A a declared requirement is NON-mandatory if and only if the declaration-site line carries the token `[Should]` or `[Optional]`, in backticks or not, immediately after the id. These are the only non-mandatory markers already in the corpus (`[Should]` 5 occurrences, all in pre-cutover specs). `(optional)` in running prose is NOT a marker. Acceptance criteria have no optional form: every declared acceptance criterion must map to a `V-*` item.
- **Cost recorded (SR-008)**: OQ-01 Option A interacts with OQ-03 Option A. Together they make every FORM C numbered heading in a post-cutover spec mandatory, including non-normative ones. That interaction is OQ-04.

### OQ-02: Does the spec ADOPT 25kzda 4.8's TRACE row verbatim, or AMEND it?

- **Options Considered**:
  1. (Option A) Adopt `25kzda` 4.8's TRACE row verbatim.
  2. (Option B) Amend `25kzda` 4.8 to change the severity, action, or message template.
- **Recommended Answer**: Option A (Adopt verbatim).
- **Evidence & Rationale**: The three sibling verification codes (`spec_plan_count`, `spec_plan_conformance`, `spec_plan_gate_carry`) adopted their rows from `25kzda` 4.8 verbatim. Adopting verbatim requires no modifications to `25kzda`, which is a highly contended contract file with multiple pending plans declaring edits.

### OQ-03: Does the convention bind FORM C (section-addressed) specs, or only id-declaring ones?

- **Options Considered**:
  1. (Option A) Admit bare dotted paragraph IDs (FORM B) and numbered section handles (FORM C) as valid requirement handles.
  2. (Option B) Restrict valid requirement IDs strictly to letter-prefixed identifiers (FORM A).
- **Recommended Answer**: Option A (Admit FORM B and FORM C).
- **Evidence & Rationale**: Two of the repository's foundational specifications (`25kzda` with 61 sections and `z7nbn1` with 30 dotted paragraph clauses) are structured around numbered sections and clauses without letter prefixes. Requiring letter-prefixed IDs would treat these key specifications as unaddressable or demand an invasive retrofit. Note (review): both are pre-cutover and grandfathered, so the evidence supports FORM B/C as ADDRESSING handles; whether they are TRACE-MANDATORY in a new spec is OQ-04.

### OQ-04 (OPEN, BLOCKING, raised at review SR-003): Which admitted forms does TRACE treat as mandatory requirements?

- **Why it blocks**: with OQ-01 A and OQ-03 A as written, a post-cutover spec's every `## <n>.` heading (including "Why this exists", "Open Questions", "Acceptance Criteria") is a mandatory requirement needing an `E-*` citation, `25kzda`-style `| A1:` revision-resolution rows anywhere in a spec are acceptance criteria needing a `V-*` citation, and `N` means "normative" in `2lcqno` but "non-goal" in `2vev8j`, so an `N`-prefixed non-goal would be mandatory. This spec itself would declare non-normative headings as requirements under the rule it defines. The implementing plan cannot resolve this without choosing a design.
- **Options**:
  1. (A) FORM A only is TRACE-mandatory in post-cutover specs; FORM B and FORM C remain valid addressing handles but are not extracted for TRACE. Simplest; a new spec must use letter-prefixed ids to be traced.
  2. (B) All forms are extracted, but only inside sections whose heading names requirements (and acceptance ids only inside an acceptance-criteria section); requires a section-heading grammar.
  3. (C) As written: all forms everywhere, mandatory unless marked `[Should]`/`[Optional]`.
- **Reviewer recommendation**: (A), plus excluding `N` from the TRACE-mandatory families because its corpus meaning is inconsistent. Not adopted unilaterally because it narrows OQ-03's recorded recommendation, which is the maintainer's to ratify.

### OQ-05 (OPEN, BLOCKING, raised at review SR-002): How is a plan-side id attributed to the producing spec for the "no unknown references" conjunct?

- **Why it blocks**: the adopted pass criterion requires it (Section 6.2a), but a produced plan legitimately mentions other specs' ids, so the attribution rule decides whether the conjunct is implementable without false refusals.
- **Options**:
  1. (A) An id-shaped token in a produced plan's `E-*`/`V-*` item counts as a citation of the producing spec unless it is immediately preceded by another spec's id6 (for example "`77tr3o` R-5"); an unqualified token not declared by the producing spec is unknown.
  2. (B) Only tokens explicitly qualified with the producing spec's id6 (for example "`89xjll` R-3") count; anything else is ignored. Precise, but adds an authoring burden and makes the forward conjuncts depend on the same qualification.
  3. (C) Defer the third conjunct to a carrier and state that TRACE implements two of three conjuncts, which makes `z7nbn1` 4.4 only partly discharged and requires amending the "adopt verbatim" decision (OQ-02).
- **Reviewer recommendation**: (A).

## 9. Acceptance Criteria

Each criterion names the requirement it covers and the evidence that satisfies it. (Rewritten at review, SR-005: the draft's criteria asserted properties of this document rather than observable behavior of the shipped check, and covered no failure path.)

| ID | Covers | Criterion | Evidence |
| --- | --- | --- | --- |
| AC-1 | R-1, R-2 | The parser returns the declared requirement and acceptance id sets of a post-cutover fixture spec using each admitted family and both acceptance prefixes, and returns them as DISJOINT sets. | Test output asserting the returned sets. |
| AC-2 | R-2 | An id appearing mid-sentence, in a parenthetical, inside a fenced code block, or qualified by another spec's id6 is NOT returned. | Test output for each negative case. |
| AC-3 | R-3 | A fixture spec whose filename date is before the resolved boundary is grandfathered and one on or after it is bound; with no stamped key and no install history, the module fallback is used (the boundary is non-`None`). | Test output for all three cases. |
| AC-4 | R-4, R-5 | A production run whose produced plan set cites every mandatory requirement in some `E-*` item and every acceptance criterion in some `V-*` item PASSES; an orchestrator in the set contributes no failure. | Run disposition and events pasted. |
| AC-5 | R-5 | A produced set omitting one mandatory requirement FAILS with code `SPEC-PLAN-TRACE`, the omitted id in `<ids>`, the message byte-identical to the 25kzda 4.8 template, and the item dispositioned per `RETRY, then FAIL ITEM`. Likewise for an uncovered acceptance criterion against `V-*` items, and for an unknown reference per the OQ-05 ruling. | Message text and disposition pasted for each failing case. |
| AC-6 | R-6 | A grandfathered spec with uncovered ids, and a post-cutover spec with zero declared ids, both PASS with no findings, and the result marks the pass as vacuous. | Test output. |
| AC-7 | R-7 | The verifier's docstring and user-visible result state the citation-not-implementation limit, and no output labels a vacuous pass as trace-verified. | Pasted docstring and output. |
| AC-8 | R-4 | The three existing siblings (`SPEC-PLAN-COUNT`, `SPEC-PLAN-CONFORMANCE`, `SPEC-PLAN-GATE-CARRY`) behave exactly as before, and the backlog production block is untouched. | Their existing tests passing unedited. |
