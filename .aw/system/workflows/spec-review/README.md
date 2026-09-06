# spec-review

Pre-approval SPEC reviewer: review a specification at `to-review`, record typed findings and a
verdict, and advance it to `reviewed` through the setter. The spec-time sibling of `plan-review`.
Run `/spec-review [path]`, or from any agent: "read and execute
`.aw/system/workflows/spec-review/spec-review.md`".

`spec` PRODUCES a spec, `/advise spec-editor` COACHES one interactively, and this workflow REVIEWS
one and produces the attestation the lifecycle now requires. Reviewing is the only one of the three
that yields a verdict, a record, and a status transition.

## Why this is a separate package and not a generalization of `plan-review`

MAINTAINER RULING, 2026-09-04 (IPD `5slbpi` OQ-01, spec `6m4kow` R-10): the spec reviewer is a
SEPARATE `spec-review/` package, NOT a conditional generalization of `plan-review/`. Spec `6m4kow`
Section 5 deliberately left the shape to the graduating plan; the maintainer decided it. This
section RECORDS that decision and the evidence behind it so the next reader inherits the reasoning
instead of re-deriving it, and so the choice is not silently re-litigated.

THE MEASURED COST OF THE REJECTED OPTION. Generalizing meant making `plan-review`'s plan-only
obligations conditional on the subject's type. Those obligations are mandatory REQUIREMENTS, not
optional prose, and there are three of them in a 601-line body:

| Site | Obligation | Why it cannot apply to a spec |
|---|---|---|
| `plan-review/plan-review.md:113-133` | The `aw ipd lint --phase author` structural preflight, run as a GATE | `aw ipd lint` is IPD-only. Worse, the preflight is GUARDED ("For each eligible plan that is an agent-executable IPD"), so handed a spec it would SKIP rather than fail, and a gate that passes by not running is worse than no gate. |
| `plan-review/plan-review.md:377-398` | The REQUIRED `- Readiness:` front-matter write | `Readiness` is a plan field. Spec `25kzda` Section 3.3 stops a reviewed spec at an unconditional human approval gate even under `--full-auto`, so a spec has no automated readiness to record. The section's own text warns that "a consumer that finds no field FAILS CLOSED", so writing the field onto a spec would manufacture a machine signal no consumer may act on. |
| `plan-review/plan-review.md:487-496` | The E/V-bijection and per-E-item right-sizing rubric | A spec has no `E-*`/`V-*` checklists at all. Applying the rubric to a spec produces findings about a structure the artifact does not have. |

`plan-review` and `plan-review-long` are held in DELIBERATE PARITY (`plan-review.md:17`), so three
conditionals would have become SIX sites, in two long bodies, each read by an agent under load. A
mis-taken branch there does not merely produce a bad report: it writes a wrong lifecycle value onto
a real artifact. That is the cost that decided the ruling.

THE COST WE ACCEPTED INSTEAD is drift: two review bodies whose shared rubric can diverge over time.
See "Keeping this from drifting" below, which is the mitigation, not a hope.

## The constraint the ruling does NOT relax

The findings/verdict/record machinery is shared EXACTLY ONCE. A separate BODY is authorized; a
separate RECORD FORMAT is not, and a design that forks the record is rejected (spec `6m4kow`
Section 5, restated in `5slbpi` E-01). Concretely, and verifiably by grep:

- `agent_workflows/review_findings.py` remains the SINGLE writer and parser of a `.review.md`. This
  workflow writes the same columns, through the same module, into the same flat
  `.aw/records/reviews/` tree. It defines no record shape of its own.
- The verdict vocabulary remains `agent_workflows/plan_readiness.VERDICTS`, the same four values.
  This workflow does not invent a spec-flavoured verdict.
- The severity comparison remains `review_findings.is_gating`, and the gating predicate remains
  `review_findings.subject_gating_blocks`, which is already artifact-neutral (it matches the
  record's `- Subject-Id:` and never consults the type).

What the fork owns is exactly one thing: the RUBRIC AND THE QUESTIONS, because a plan rubric applied
to a spec produces findings about the wrong artifact.

## Keeping this from drifting

Drift is the acknowledged cost of a fork, so the mitigation is stated here rather than left to
discipline:

1. THE SHARED HALVES ARE SHARED IN CODE, not in prose. Severity, scope, Remediation Risk, the Fix
   Bar, the verdict vocabulary, and the record format all live in `review_findings` and
   `plan_readiness`. This body REFERENCES `../plan-review/plan-review.md` for them rather than
   restating them, so improving them once improves both reviewers. A copy is the thing that drifts;
   a pointer is not.
2. WHAT IS FORKED IS BOUNDED AND NAMED. Only the rubric (Section "Spec rubric" below) and the
   spec-specific prohibitions are local to this package. Anything else appearing here in duplicate
   is a defect to fix by deleting the copy.
3. A CHANGE TO THE SHARED HALVES MUST NOT BE MADE HERE. If a future change needs a different
   severity vocabulary, a different verdict set, or a different record shape, it belongs in the
   shared module and applies to both reviewers by construction. Editing it in one body is the
   divergence this note exists to prevent.
4. THE ANTI-FORK GUARD IS A TEST, not a convention. `tests/test_spec_review_workflow.py` asserts
   that this body does not restate the closed vocabularies and that it names the shared module, so
   a future copy-paste fails the suite rather than being noticed in review.
