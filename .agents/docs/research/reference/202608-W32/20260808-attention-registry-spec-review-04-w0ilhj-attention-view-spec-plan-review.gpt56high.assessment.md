---
id: w0ilhj
created: 20260808
set: attention-registry-spec-review
order: 04
topic: [attention-registry, spec-review, plan-review, external-review]
model: gpt56high
kind: assessment
status: reference
outcome: none-yet
summary: gpt-5.6-high plan-review of the revised attention-view spec (REVIEWED - OPEN QUESTIONS; PR-001..PR-005)
consumed-by: []
---

# Plan review: attention view and cross-tree status model

Verdict: `REVIEWED - OPEN QUESTIONS`

The revised architecture substantially conforms to the consolidated expectations. Material corrections are still needed before human approval or Implementation Plan Document authoring.

## Review scope

ELIGIBLE:

- `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`
- Repository evidence from GitHub `main` at commit `0afa17a40f11efc9235b1159af0fd1d4b9890243`

NOT REVIEWED:

- (none)

Structural IPD lint: not applicable. The target is a design specification, not an agent-executable IPD.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | HIGH | UNDER-SCOPE | Correctness, dependencies, honest documentation | Spec:7, 33, 45-47, 108, 114, 215, 230, 238, 244; [`cli.py:148-174`](https://github.com/fariello/agent-workflows/blob/0afa17a40f11efc9235b1159af0fd1d4b9890243/agent_workflows/cli.py#L148-L174); [research README](https://github.com/fariello/agent-workflows/blob/0afa17a40f11efc9235b1159af0fd1d4b9890243/.agents/docs/research/README.md) | The dependency baseline does not match GitHub `main`. `artifact_core.py`, `aw research`, and the cited `aw plans index --check` and `aw research index --check` commands are absent. Research tooling remains represented by pending plans. The spec therefore relies on unverified prerequisites and contains acceptance criteria that cannot run against the named repository baseline. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | Identify the exact prerequisite commit or branch containing D123/D124 and the research tooling. Otherwise, make those capabilities explicit prerequisite work and replace the nonexistent commands with the real or planned interfaces. |
| PR-002 | HIGH | IN-SCOPE | Lifecycle correctness and authorization | Spec:4, 18, 91-106, 122-133, 205-207, 278 | The proposed spec enum omits `to-review`, even though the reviewed spec itself uses `Status: to-review`. It also does not define who may perform lifecycle transitions, especially `reviewed -> approved` and `implementing -> implemented`. An agent could otherwise mark a spec approved or implemented without the required human decision or execution evidence. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | Add `to-review` and map it to `ready`. Define a transition and authority table. Human approval must be required for `approved`; `implemented` must require verified implementation evidence. |
| PR-003 | HIGH | UNDER-SCOPE | Schema, data contract, executability | Spec:91-107, 137-181, 201-210, 244-260, 278 | Load-bearing contracts remain Phase 0 decisions: mappings, history grammar, v1 tree scope, JSON schema, serialization, rule identifiers, escaping, and gate validators. Phase 0 is described as an implementation phase after spec approval, so an IPD author would still need to invent product behavior. The metadata examples are also inconsistent: the normative status is `- Status:`, while the gate example uses unbulleted `Status:` and `Gate-*` fields. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | Close OQ1-OQ4 and OQ6 before approval. Close OQ7-OQ9 as adopted decisions. Make Phase 0 implement and test finalized contracts rather than decide them. Define one exact metadata grammar, including whether trailing prose after an enum is forbidden. |
| PR-004 | MEDIUM | UNDER-SCOPE | Security, agent safety, deterministic rendering | Spec:116-120, 137-161, 165-181, 190-196 | The output contract does not sufficiently constrain descriptive text. `Gate-Summary`, paths, URLs, and future tree metadata can introduce Markdown breakage, terminal control characters, excessive output, or instruction-like content consumed by an agent. JSON canonicalization alone does not address the Markdown and agent trust boundary. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | OPEN | Require single-line bounded metadata, JSON escaping, deterministic Markdown escaping, rejection of control characters, and `http`/`https` restrictions for issue URLs. State that `/whatnext` treats descriptive fields as untrusted data, never instructions. Add hostile-string fixtures. |
| PR-005 | MEDIUM | OVER-SCOPE | KISS and specification boundaries | Spec:85, 114, 130, 181, 215, 238; [`spec.md:68-74`](https://github.com/fariello/agent-workflows/blob/0afa17a40f11efc9235b1159af0fd1d4b9890243/.agents/workflows/spec/spec.md#L68-L74) | The repository's spec workflow requires WHAT and WHY, leaving implementation HOW to the plan. The updated spec appropriately defines behavior and output contracts, but it also fixes module names, `run(args)` signatures, CLI edit points, and physical code placement. These details duplicate IPD responsibilities and may become stale before implementation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | OPEN | Keep externally observable behavior, compatibility constraints, and required reuse. Move module names, parser/dispatch edit points, and other code-placement instructions into the follow-on IPD. |

## Edits required

1. Ground all dependency and CLI claims in the actual target branch or make the missing capabilities explicit prerequisites.
2. Add `to-review` to the spec lifecycle and define a transition and authority matrix.
3. Finalize all v1 mappings, metadata grammar, history grammar, JSON schema, validation rule identifiers, escaping, and gate validators before spec approval.
4. Add output safety constraints for human and agent renderings.
5. Move code-placement details into the follow-on IPD.

No edits were applied during this review. The repository instruction for review requests says to report and wait rather than modify or commit files. See [`AGENTS.md:28-29`](https://github.com/fariello/agent-workflows/blob/0afa17a40f11efc9235b1159af0fd1d4b9890243/AGENTS.md#L28-L29).

## Deferred and open

- `PR-001` - OPEN:
  - Reason: The authoritative implementation baseline is unresolved.
  - Remediation Risk: Medium
  - Axis: functionality and complexity
  - Required decision or evidence: Identify the commit or branch containing `artifact_core`, research tooling, and the intended index commands.
  - Consequence if unresolved: The IPD will target APIs and dependencies that do not exist on `main`.

- `PR-002` - OPEN:
  - Reason: The lifecycle is internally inconsistent and lacks transition authority.
  - Remediation Risk: Medium
  - Axis: functionality
  - Required decision or evidence: Adopt `to-review` and define who may enter each state.
  - Consequence if unresolved: The new validator would reject this spec or permit unsupported approval and completion claims.

- `PR-003` - OPEN:
  - Reason: Core product contracts remain undecided.
  - Remediation Risk: Medium
  - Axis: complexity and functionality
  - Required decision or evidence: Final mapping tables, schemas, history grammar, validators, and v1 scope.
  - Consequence if unresolved: The implementation plan must invent architecture and cannot produce complete acceptance tests.

- `PR-004` - OPEN:
  - Reason: Output safety and trust handling are incomplete.
  - Remediation Risk: Medium
  - Axis: security
  - Required decision or evidence: Define escaping, bounds, URL validation, and agent treatment of descriptive fields.
  - Consequence if unresolved: Malformed or adversarial metadata could corrupt output or influence an agent.

- `PR-005` - OPEN:
  - Reason: Implementation details exceed the repository's specification boundary.
  - Remediation Risk: Low
  - Axis: complexity
  - Required decision or evidence: Move code-placement details to the IPD.
  - Consequence if unresolved: The spec and IPD will duplicate implementation instructions and may drift.

## Commit result

- Pre-review snapshot: not applicable, review-only request with no local repository checkout
- Hardened result: not applicable, no edits authorized
- Push: not performed

## Plans reviewed and not reviewed

REVIEWED:

- `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`: NO-GO. The revised architecture is sound, but five material findings remain open, including dependency mismatch, lifecycle inconsistency, and unresolved machine contracts.
  - Verdict: `REVIEWED - OPEN QUESTIONS`.
  - Open questions: 5 open, blocks GO.
  - Required next step: Revise the specification, close the load-bearing contracts, identify the correct dependency baseline, then repeat review before human approval or IPD authoring.

NOT REVIEWED:

- (none)
