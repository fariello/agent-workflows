- Id: qph7c5
- Status: open
- Set: writestd
- Priority: high
- Work-Kind: feature
- Summary: Adopt a shipped technical-artifact writing standard (with diagram rules) for specs, backlog items, and plans, wire it into authoring and review, and sweep live artifacts

## Workflow history
- 2026-10-26 created (aw backlog): Maintainer request 2026-10-25: apply the technical-artifact writing requirements plus entity and flow diagrams to all specs, backlog items, and plans going forward

## Problem

No shared writing standard exists for specs, backlog items, and plans. Writing rules are spread across `GUIDING_PRINCIPLES.md` P13, `CONTRIBUTING.md` "Authoring conventions", `.aw/system/workflows/assess/references/prose-style.md`, and the `aw:reporting` section of `AGENTS.md`. No rule tells an author when to draw an entity diagram or a flow diagram. The proofreading prompt `wcisgc` applies only at review time (spec `k3yx72` non-goal N5), and it lives under `.aw/records/`, which the installer does not ship to target repositories.

## Requested outcome

The maintainer supplied a draft standard on 2026-10-25 (delivery copy, gitignored: `tmp/20261025-technical-artifact-writing-requirements.md`). The maintainer requires the following:

1. Every spec, backlog item, and plan follows that standard when it is written, proofread, reviewed, or revised.
2. These artifacts contain entity diagrams and flow diagrams when a diagram helps the reader.
3. The standard ships to every repository that agent-workflows manages.
4. The standard's em dash rule applies to these artifacts and covers em and en dashes. This replaces the current exemption in P13 and in the `AGENTS.md` execution contract.
5. A sweep proofreads every live artifact: specs in `draft`, `to-review`, `reviewed`, `approved`, `implementing`, and `parked`; backlog items in `open`, `blocked`, `graduated`, and `parked`; and plans in `pending/` and `reusable/`. An approved artifact keeps its status and gets a history line that records the proofread. The sweep skips a plan that is executing or queued in a live run.

## Maintainer decisions (2026-10-25, in session)

| Question | Decision |
| --- | --- |
| Scope | Ship to all managed repositories. |
| Dash rule | The standard wins. It covers em and en dashes in specs, plans, and backlog items. |
| Existing artifacts | Apply to new work and sweep live artifacts now. |
| Approved artifacts in the sweep | Proofread them and keep their approval. Skip any plan in a live run. |
| Parked backlog items | Include them in the sweep. |
| Delivery | A backlog item, a spec, and a review-ready plan Set. |

## Acceptance

This item is done when every plan graduated from it is `executed` and spec `writestd` (the spec carrying `- From-Backlog: hq2ut2`) is `implemented`.
