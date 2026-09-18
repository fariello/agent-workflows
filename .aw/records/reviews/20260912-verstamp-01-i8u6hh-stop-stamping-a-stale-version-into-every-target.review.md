# Review: stop stamping a stale VERSION into every target, child i8u6hh (Set verstamp)

- Subject-Id: i8u6hh
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `bba372a8`. Structural preflight `aw ipd lint --phase author` CONFORMED with zero findings
before semantic review, and `--phase review-finalize` CONFORMED after the revision. No product code was
modified by this review.

DISCLOSURE: I AUTHORED THIS PLAN in the same session, so this is a self-review. Its value rests on what was
EXECUTED: every cited line range opened and compared to the claim; `read_version` read in full; the VERSION
member emission read at engine.py:733-741; `_member_source_path`'s VERSION special case read at
engine.py:296-308; the manifest assignment read at engine.py:5885; and `RELEASING.md` grepped for the
version-baking step.

THE ROOT CAUSE IS CORRECTLY IDENTIFIED AND IS THE STRONGEST PART OF THE PLAN. VERSION is emitted as an
ordinary install member (engine.py:734-740) and its bytes are read from disk via `_member_source_path`
(engine.py:296-308), so the resolver in `read_version` (engine.py:311-330) never runs on the write path.
That is a precise, verifiable explanation for a symptom measured across nine real repos, and the fix
location follows from it directly rather than being guessed.

THE ONE FINDING IS AN OVERSTATED WORK ITEM, WHICH MATTERS BECAUSE OF WHAT AN OVERSTATEMENT INVITES. E-03
told the executor to "ensure the manifest's `installed_version` records the SAME resolved value" and to
"make the two agree", phrasing that implies the manifest derives its version independently and needs its
own fix. It does not: engine.py:5885 assigns `read_installed_version(repo_root) or ""`, which READS BACK
the file just written into the target. So fixing E-02 fixes the manifest with no further code, and an
executor acting on the original wording could add a second derivation path, which is precisely the
duplicate-authority defect this Set exists to eliminate. E-03 is now a VERIFICATION item that adds no code
unless the read-back inference turns out to be wrong, and it must record which it was.

WHAT I VERIFIED AND KEPT. F-05's severity reasoning is correct and is what keeps this plan off the release
gate: `RELEASING.md:46` bakes the intended version before tagging, so a released wheel stamps correctly and
the defect is dev-checkout-only. F-06 is right that no existing test covers a DIVERGENCE between the baked
file and the resolved value, which is exactly why the defect survived; E-04's instruction to construct the
divergence deliberately rather than rely on ambient state is the correct shape and is what makes the test
non-vacuous. The deferral of re-baking this repo's own VERSION is correct and important: `make version-file`
is a release-time action under a human GO gate, and the gate text forbids the executor from running it.
OQ-01's evidence-based lean toward the resolved value is sound (the resolver exists precisely so a dirty
checkout reports an unmistakable `.devN` string, engine.py:315-317, and `versioning.status` already has a
`dev` class), and requiring the decision to be RECORDED before implementation prevents a retrofit.

WHAT I DID NOT DO: I did not verify the trailing-newline preservation requirement empirically, so it remains
an instruction to the executor rather than a measured fact. It is called out in E-02 because getting it
wrong would make every re-install report a spurious modification, and V-02's byte-comparison evidence would
catch it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-006 | MEDIUM | OVER-SCOPE | C. Architecture; G. Plan executability | agent_workflows/engine.py:5885 | E-03 implied the manifest's `installed_version` needs its own fix to "make the two agree". It is assigned `read_installed_version(repo_root) or ""`, i.e. it reads back the file just written, so E-02 fixes it automatically. The original wording invites an executor to add a second independent derivation, which is the duplicate-authority defect this Set exists to remove. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote E-03 as a VERIFICATION item that adds no code if the read-back holds, requires the outcome to be recorded, and updated the corresponding proposed-changes line and expected outcome. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should E-03 remain a code-change item or become a verification item? | Verification item, adding code only if the read-back inference fails. | Keep it as a change item and let the executor discover the redundancy. | engine.py:5885 reads the stamped file back rather than deriving the version separately, so no manifest-specific change is needed. Leaving the change framing would invite exactly the second derivation path this Set removes elsewhere. Made it verify-and-record rather than deleting it outright, because the inference is mine and should be proven against a real install. | yes |
| D-2 | Should this plan carry `Blocks-Release: f33nrj` like its two siblings? | No. | Gate it too, on the grounds that all 31 repos currently report STALE. | `RELEASING.md:46` bakes the intended version before tagging (bake-then-tag), so a RELEASED artifact stamps correctly and the defect cannot reach a released install; it is dev-checkout-only. Gating 2.0.0 on a defect that a release itself resolves would block the release on nothing. Recorded rather than assumed because the maintainer explicitly asked whether all three bugs were blocking, and the honest answer is two of three. | yes |
