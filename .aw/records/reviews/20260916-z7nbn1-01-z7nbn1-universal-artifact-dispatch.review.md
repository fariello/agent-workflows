# Review findings: spec z7nbn1

- Subject-Id: z7nbn1
- Subject-Type: spec
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-001 | blocker | IN-SCOPE | D (decisions) / G (plannable) | spec 1.3/1.4/1.7 vs `25kzda` 3.1 gate 1 and `RUN-STRUCTURE-PREFLIGHT` row (FAIL ITEM); `runner_shared.edge_satisfied` (per-item `fail-depend`); spec old 2.4 "largely satisfy 1.4" | The spec required whole-run refusal while the approved contract it builds on and the shipped runner fail per item, and it misreported 1.4 as largely satisfied. A planner could not tell which contract governs. | C:Medium;U:Low;S:Low;F:High;Overall:Medium | fixed | Maintainer ruled 2026-09-26 (asked): split by when known. Added OQ-04 (resolved), 1.4a, sharpened 1.3/1.4/1.7, rewrote 2.4, added 0.2 declaring the `25kzda` amendment and ACs 5.3a/5.3b. |
| SR-002 | high | IN-SCOPE | A (measured claims) | spec old 2.2 "EXISTS and satisfies 1.2"; `runner_shared.action_for` / `determine_action` (maps every non-review status incl. `executed` to `execute`); `_action_for` is private; backlog `oc3mhb` seam 3 | A second status-to-action mapping exists and is what the runners actually use, so 1.2 is not satisfied and 5.6 would fail at HEAD. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | 2.2 rewritten to state both mappings, their disagreement, the 2026-09-10 public-reader ruling, and the `orchestrate` question; 5.6 now pins runner action equals table action. |
| SR-003 | high | IN-SCOPE | E (open questions) / D | OQ-02 ruled `SPEC-PLAN-TRACE` in scope; research `vkub9o` (no single requirement-id convention; this spec uses bare dotted ids) | TRACE cannot be built deterministically without a requirement-id convention the repo lacks; the ruling predated the survey. | C:Medium;U:Low;S:Low;F:Medium;Overall:Medium | fixed | Maintainer ruled 2026-09-26 (asked): defer TRACE to a separate spec; filed backlog `vy20et`. OQ-02 revised, 4.4 rewritten, honest limit added. |
| SR-004 | high | UNDER-SCOPE | C (coverage) | Section 3 names backlog `open -> plan` as production; no AC covered it; `25kzda` 4.9 BACKLOG-* codes grep to zero | Backlog production had no acceptance criterion and its verification codes were unscoped. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | Maintainer ruled 2026-09-26 (asked): all in scope. Added OQ-05, 4.4 in-scope list, AC 5.5c with refusal paths. |
| SR-005 | medium | IN-SCOPE | A / E | OQ-01 resolution and 3.4 cite `--follow-generated` "once implemented" (owner `x8diyb`); plan `hzdq8y` executed, `x8diyb` done; 3.4 said "does not decide" while OQ-01 decided | Stale forward reference and a self-contradiction between 3.4 and OQ-01. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 3.4 now states report-only as decided, citing `25kzda` 3.3/3.4; OQ-01 annotated as updated; opt-in moved to out of scope. |
| SR-006 | medium | IN-SCOPE | A | 4.1 "37 sites across five modules"; re-measured 44 across six (`runner_shared` 27) | Stale count after host code was lifted into `runner_shared`. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 4.1 and 5.8 carry the re-measurement and require an execution-time enumeration. |
| SR-007 | medium | UNDER-SCOPE | C | ACs 5.2/5.4/5.5 happy-path only | Refusal paths for conformance, spec review advancement and spec production were not stated as evidence. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 5.2, 5.4, 5.5 extended with refusal evidence; 5.9 added for 1.1 on runners. |
| SR-008 | medium | UNDER-SCOPE | G (plannable) / F | no relation to `25kzda`, `6m4kow` R-15, `oc3mhb`; 3.3 did not name setters or `implementing` transition | Dependencies and their direction were implicit; the source-artifact transition mechanism was unstated. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Added 0.2 relations section; 3.3 names `aw specs set`/`aw backlog set`; 3.3a adds no-requirement-edit and no-duplicate constraints. |
| SR-009 | low | UNDER-SCOPE | F (honest limits) | no limits/migration section | Missing honest limits and migration statement. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Added 5a. |
| SR-010 | low | IN-SCOPE | A | 2.1 "thirteen modules" (17 import `selectors`); 0 still described `mng63x` as live; 1.7 "undetermined" collides with `reviewed` rows | Minor stale facts and an ambiguity that would make 1.7 refuse every run containing a `reviewed` plan. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | 2.1 count and runner caveat updated; 0 notes `mng63x` superseded; 1.7 defines undetermined after runner-known inputs. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Should the first graduating plan close backlog `oc3mhb`? | Yes, recommended via `- From-Backlog: oc3mhb` (SHOULD, in 0.2). | Leave `oc3mhb` as parallel work. | `oc3mhb` body asks to be reconciled with z7nbn1 before work starts; its four seams equal 4.1/4.3. | yes |
| D-2 | Does the `approved -> implementing` transition belong here though `SPEC-IMPLEMENTING-TRANSITION` is out of scope? | Yes: the transition is performed; only its dedicated verifier stays with `25kzda`. | Leave the spec at `approved`. | `25kzda` 3.3 `approved` row requires "tool-set spec to `implementing`". | yes |
| D-3 | Is the `25kzda` amendment an irreversible commitment? | Called out as irreversible-in-practice in 0.2. | Treat as routine. | `25kzda` is the approved contract every runner plan is reviewed against (AGENTS.md "A plan may amend a spec"). | yes |
