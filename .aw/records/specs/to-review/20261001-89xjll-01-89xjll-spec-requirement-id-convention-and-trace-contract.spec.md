# Spec: Spec Requirement ID Convention and the SPEC-PLAN-TRACE Contract

- Date: 2026-10-01
- Status: to-review
- Id: 89xjll
- Author: opencode / antigravity (IPD jjh4aj)
- From-Backlog: vy20et
- From-Spec: 25kzda
- Scope: Requirement-ID convention for new specs, acceptance-criterion namespace, declaration-site rule, retrofit policy via stamped cutover, and SPEC-PLAN-TRACE verification contract (scope, severity, grandfathering behavior, and citation-not-implementation limit).

## Workflow history

- 2026-10-01 to-review (aw specs): Authored review-ready by IPD jjh4aj graduating backlog vy20et: defines requirement and acceptance namespaces, declaration-site rule, stamped cutover retrofit policy, and SPEC-PLAN-TRACE contract
- 2026-10-01 created (aw specs): Spec Requirement ID Convention and the SPEC-PLAN-TRACE Contract

## 1. Why this exists

Approved spec `25kzda` 4.8 declares `SPEC-PLAN-TRACE` with a mandatory pass criterion:
"Every mandatory spec requirement maps to at least one E item; every acceptance criterion maps to at least one V item; there are no unknown references."
Its action is `RETRY, then FAIL ITEM`, and its message template is:
`[SPEC-PLAN-TRACE] Generated IPD <plan-id> does not cover spec items: <ids>. Re-read spec <source-id> and update plan checklist, then: aw <host> run <selector>`

While its three sibling verification codes shipped in `production_checks.py` (`spec_plan_count`, `spec_plan_conformance`, and `spec_plan_gate_carry`), `SPEC-PLAN-TRACE` was deferred by spec `z7nbn1` 4.4 to backlog `vy20et` because requirements carried no machine-readable identifiers by any agreed convention. `z7nbn1` 4.4 additionally bound the repository to the restriction that "a produced plan MUST NOT be described as trace-verified" until this contract exists.

Earlier research `vkub9o` (2026-09-20) surveyed the 36-spec corpus and recommended against building a corpus-wide requirement parser or coverage view, primarily because the plan-to-spec join edge (`- From-Spec:`) was missing across historical specs. However, that survey's objection does not apply to `SPEC-PLAN-TRACE` at the point of spec production: as measured in `runner_shared.py`, the production dispatcher computes newly produced plans directly (`new_produced_paths` against `baseline_plan_ids`) and passes them immediately into the verifiers. The join edge is in hand.

Furthermore, `vkub9o` Section 3 measured that three of five observed harm cases were ADDRESSING failures that a stable requirement-ID convention resolves, independent of any whole-corpus coverage tracking:
1. In `25kzda`, the 0..10 retry budget bound appeared across four different sections (§1.4, §2.1, §4.1, §5.5) without a canonical identifier, resulting in 2 backlog items (`trjfyy`, `eh91an`) and a pending plan (`xipfy1`) being filed over 15 days for a single requirement.
2. An author cited `25kzda` §2.1 line 211, their reviewer mistakenly "corrected" it to §1.1 line 586, and a code comment cited "spec 2.1's 0..10 bound" while the bound appeared in four places—three parties disagreeing about where one requirement lives.
3. Code comments drifted from spec citations because there was no stable symbol or identifier to reference.

This specification resolves the convention, the namespaces, the declaration rule, the retrofit boundary, and the verification contract so that Order 02 (`rtvdak`) implements a specified check rather than guessing.

## 2. Measured corpus evidence (HEAD census)

At execution HEAD `f279e326`, recursive census of `.aw/records/specs/` demonstrates:
- Total specs: 39 (12 `approved`, 2 `deferred`, 2 `draft`, 15 `implemented`, 2 `implementing`, 1 `reviewed`, 3 `superseded`, 2 `to-review`).
- Live specs: 21; Terminal specs: 18 (`implemented`, `superseded`, `parked`).
- Specs without `- Id:`: 19 total, but only 2 live specs lack `- Id:`, both of which are `deferred` legacy specs (`20260725-0957-01` and `20260726-1239-01`).
- Requirement ID availability across live specs: exactly 2 live specs carry no requirement ID of any form (`25kzda`, which is section-addressed, and `kw5y2s`). The other 19 live specs already carry addressable requirement IDs or section handles.
- Approved specs requirement status: 10 of 12 `approved` specs already carry requirement IDs (`5tapom`, `7ckptx`, `6m4kow`, `77tr3o`, `2vev8j`, `2lcqno`, `6kwd2e`, `w15vzb`, `uonrjg`, `r07vma`). Only 2 lack them: `25kzda` (section-addressed) and `kw5y2s`.
- Approved specs acceptance status: 7 of 12 `approved` specs carry acceptance-criterion IDs (`7ckptx` 36, `6kwd2e` 49, `uonrjg` 25, `w15vzb` 12, `6m4kow` 11, `2vev8j` 11, and `25kzda` 4 table rows). 4 carry an acceptance heading with no IDs (`5tapom`, `kw5y2s`, `2lcqno`, `r07vma`), and 1 carries no acceptance heading (`77tr3o`).
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

Grounding in census evidence: Mandating a single prefix letter such as `R` would invalidate 5 of the 10 currently conforming `approved` specs (`2vev8j` using `C*`/`N*`, `2lcqno` using `N*`, `5tapom` using `B*`/`H*`/`F*`), as well as pending/draft specs (`pqsx96`, `llbr2b`, `wy9aru`, `4sd62s`). Admitting the established prefixed families aligns the normative contract with repository practice and requires zero retrofit across live specs.

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

Any occurrence of an identifier that fails this structural test—such as an identifier appearing mid-sentence, inside a parenthetical note, within running paragraph prose, or as a reference to another specification (e.g., "referencing `77tr3o` R-5" or "(spec 2.1's 0..10 bound)")—is a MENTION, not a declaration. A mention conveys no obligation and MUST NOT be extracted by the requirement parser or counted by `SPEC-PLAN-TRACE`.

### 4.2 Addressing Rationale

A formal addressing convention is established to eliminate citation ambiguity. In-tree research `vkub9o` Section 3 measured five concrete cases of drift and waste:
1. Three of the five cases were addressing failures where authors, reviewers, and code comments could not agree on how to reference a requirement because no stable identifier existed.
2. In `25kzda`, the retry-budget bound was duplicated across four sections without an ID, causing confusion between implementers and reviewers (finding PR-305 in `vkub9o`).
3. In `runner_shared.py:6636`, comments had to cite §2.1 by section number and line offset rather than a stable symbol.

A stable declaration-site identifier provides a singular, durable handle for specifications, plans, code comments, and automated gates.

## 5. Retrofit and Grandfathering Policy

### 5.1 Cutover Registration via KNOWN_FEATURE_CUTOVERS

The retrofit boundary is governed by the repository's single existing cutover registry, `config.KNOWN_FEATURE_CUTOVERS`, rather than inventing a secondary mechanism.

1. **Feature Key**: The feature key registered in `config.KNOWN_FEATURE_CUTOVERS` is `spec_requirement_ids`.
2. **Stamped Boundary**: The cutover date is STAMPED per repository in `.aw/config/project.json` under `cutovers.spec_requirement_ids` (synchronized during installation via `sync_cutovers_on_install`). It is not hardcoded into source logic. Order 02 (`rtvdak`) registers the key and introduction date in `config.KNOWN_FEATURE_CUTOVERS`.
3. **Per-Spec Grandfathering**: Grandfathering is evaluated PER SPEC against the stamped boundary by comparing the spec file's date (from front matter or filename `YYYYMMDD`) to the cutover date. Specifications predating the cutover date remain valid indefinitely and are not required to adopt requirement IDs.
4. **Going-Forward Rule**: New specifications authored on or after the cutover date must conform to the requirement and acceptance namespaces and declaration-site rules. Existing prose-only live specifications (`kw5y2s` and section-addressed `25kzda`) are grandfathered as policy, in accordance with `vkub9o` Q5.

### 5.2 Accepted Cost of Grandfathering

As documented in `vkub9o` Option B, the accepted cost of per-spec grandfathering is that an external reader or naive automated tool cannot distinguish an exempt legacy specification from a non-conforming specification without consulting the repository's cutover timestamp. This trade-off is accepted to avoid rewriting approved historical records, retrofitting completed specifications, or causing breaking check failures on existing code.

## 6. The SPEC-PLAN-TRACE Verification Contract

### 6.1 Check Scope

`SPEC-PLAN-TRACE` runs exclusively as a post-generation gate during the spec production action (`aw <host> run <spec-id6>`). As measured in `run_selection_policy._SPEC_ACTIONS`, only specifications with status `approved` map to `ACTION_PLAN`.

The check inspects the newly produced plans against the SINGLE producing specification that was dispatched. It does NOT inspect the entire repository corpus. The produced plans are in hand at execution time: as measured in `runner_shared.py`, the dispatcher identifies `new_produced_paths` by comparing the target tree's plans against `baseline_plan_ids` before invoking verifiers.

### 6.2 Severity, Action, and Message Template (Adopting 25kzda 4.8)

This specification ADOPTS the `SPEC-PLAN-TRACE` row from `25kzda` 4.8 verbatim, without amendment:
- **Action**: `RETRY, then FAIL ITEM`.
- **Pass Criterion**: "Every mandatory spec requirement maps to at least one E item; every acceptance criterion maps to at least one V item; there are no unknown references."
- **Message Template**:
  `[SPEC-PLAN-TRACE] Generated IPD <plan-id> does not cover spec items: <ids>. Re-read spec <source-id> and update plan checklist, then: aw <host> run <selector>`

The new verifier `production_checks.spec_plan_trace` implements this exact template and returns `list[tuple[str, str, str]]` matching the signature of `spec_plan_conformance(repo, spec_id6, produced_paths, *, host, run_id)`.

### 6.3 Grandfathered-Spec and No-IDs Behavior

When the producing specification predates the cutover date or declares zero requirement/acceptance IDs (such as legacy grandfathered specs), `SPEC-PLAN-TRACE` evaluates to a PASS with no findings. It must not fail or refuse plan production on specifications that were never required to adopt requirement IDs.

### 6.4 The Honest Limit (Citation vs. Implementation)

A successful `SPEC-PLAN-TRACE` check confirms that every declared mandatory requirement ID is cited by at least one `E-*` execution checklist item and every declared acceptance criterion ID is cited by at least one `V-*` validation checklist item across the produced plans.

**The Honest Limit (Verbatim Contract)**:
A trace check proves only that a plan step CITES a requirement or acceptance identifier; it does NOT prove that the plan correctly, completely, or safely implements the requirement. `SPEC-PLAN-TRACE` is a structural citation gate, never a semantic proof of implementation. A produced plan verified by this check may be described as trace-verified against declared identifiers, but MUST NOT be described as having verified the semantic correctness of the implementation.

This explicit limit satisfies and replaces the prohibition in `z7nbn1` 4.4.

## 7. Relations to Other Specifications

- **`25kzda` 4.8**: ADOPTED VERBATIM. The pass criterion, message template, and `RETRY, then FAIL ITEM` action are adopted exactly as specified. No amendment to `25kzda` is made.
- **`z7nbn1` 4.4**: Addresses the deferral of `SPEC-PLAN-TRACE` to backlog `vy20et`. Note that this deferral is addressed by this specification, but is NOT discharged until Order 02 (`rtvdak`) implements the parser and wires the check into `runner_shared.py`.
- **Research `vkub9o`**: Cites the census methodology and harm findings. Reconciles the survey's corpus-wide recommendation against the production-scoped check.

## 8. Open Questions (Recommendations for Spec Review)

The following three questions were resolved on repository evidence. These resolutions are agent recommendations awaiting human ratification via the human approval attestation (`aw spec set approved <id6> --by-human`), not maintainer determinations or approvals.

### OQ-01: How is a "mandatory" spec requirement identified, given that no marker is in general use?

- **Options Considered**:
  1. (Option A) Every declared requirement ID is mandatory unless explicitly tagged with an optional marker (e.g. `[Optional]`, `(optional)`).
  2. (Option B) Adopt the `[Must]` marker as the sole discriminator of mandatory requirements.
  3. (Option C) Require each specification to list its mandatory requirement subset in front matter or a dedicated section.
- **Recommended Answer**: Option A (fail-closed: every declared requirement ID is mandatory by default).
- **Evidence & Rationale**: Census measurements show that `[Must]` appears in only 2 of 12 `approved` specifications (`2vev8j`, `5tapom`). Under Option B, `SPEC-PLAN-TRACE` would be vacuous for 10 of 12 approved specs, passing by default and teaching authors to treat the gate as decoration. Option A fails closed, aligning with all other safety gates in this repository.

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
- **Evidence & Rationale**: Two of the repository's foundational specifications (`25kzda` with 61 sections and `z7nbn1` with 30 dotted paragraph clauses) are structured around numbered sections and clauses without letter prefixes. Requiring letter-prefixed IDs would treat these key specifications as unaddressable or demand an invasive retrofit.

## 9. Acceptance Criteria

- **AC-1**: The specification defines the requirement namespace admitting prefixed families (`R`, `F`, `G`, `I`, `N`, `C`, `P`, `T`, `B`, `H`, plus FORM B and FORM C) and establishes the acceptance-criterion namespace (`A`, `AC`) as distinct from requirements.
- **AC-2**: The declaration-site rule provides a syntactic, machine-implementable discriminator distinguishing declared requirement identifiers from prose mentions.
- **AC-3**: The retrofit policy establishes `spec_requirement_ids` as the feature key in `config.KNOWN_FEATURE_CUTOVERS`, with per-spec grandfathering based on the repository's stamped cutover date.
- **AC-4**: The `SPEC-PLAN-TRACE` contract specifies production scope, adopts `25kzda` 4.8 verbatim, defines grandfathered pass behavior, and states the honest limit that trace verifies citation presence rather than semantic implementation correctness.
- **AC-5**: Open questions OQ-01, OQ-02, and OQ-03 are documented with options, recommendations, and evidence, and are explicitly designated as agent recommendations awaiting human approval attestation.
