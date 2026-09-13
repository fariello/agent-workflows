- Id: 0htqmm
- Status: open
- Set: 0htqmm
- Priority: medium
- Work-Kind: feature
- Summary: Make the release-gating work-kind set configurable per repository, defaulting to bug alone, mirroring the shipped review_findings_gate key

## Workflow history
- 2026-09-12 created (aw backlog): Make the release-gating work-kind set configurable per repository, defaulting to bug alone, mirroring the shipped review_findings_gate key

## Where this came from

Maintainer ruling 2026-09-12, answering `qmgn12` OQ-01 ("should `security` also gate the next release
automatically?"). They declined a global answer in either direction and asked instead: "Should this (and
basically all of these auto-gates) be configurable?"

## The problem a global answer cannot solve

A `security` designation is only as good as the judgement behind it. The maintainer has MEASURED agent
security classifications in THIS repository to be overstated, because an agent defaults to assuming an
adversarial actor, and as they put it "an adversarial agent can in fact overcome ANY 'security' we put in
place". For MOST of their other projects the opposite holds and every security finding genuinely must
block a release.

That is a PROJECT-DEPENDENT property. Hardcoding either answer is wrong for one side of the same
maintainer's estate, which is why the fix is configuration rather than a rule change.

## The shape, and the precedent it copies

A `.aw/config/project.json` key naming the work-kinds that auto-gate the next release, DEFAULTING TO
`bug` ALONE.

Follow `review_findings_gate` (`config.py:1085-1104`), which solved this exact problem shape once
already:
- takes an object (`{"block_at": "high"}`) and tolerates a bare string for convenience;
- is DELIBERATELY NOT registered in `CONFIG_SCHEMA`, because `project_schema.parse_portable_policy`
  preserves unknown keys in `unknown_fields` and writes them back on serialization, so the key
  round-trips safely;
- documents its default and the direction it fails.

## Why the default is `bug` only, and not `bug` + `security`

Strict fail-closed argues for including `security`, and that was OFFERED AND DECLINED. Including it would
be wrong for the very repository doing the configuring, forcing an immediate opt-out of a label the
maintainer does not trust here. A default the reference repo must override is a bad default. `bug` alone
is also exactly the standing rule ("we don't ship known bugs"), so a repo that configures nothing behaves
as the rule already says, and no existing repo changes behavior when this lands.

## Deliberately NOT in scope

A broader "all auto-gates" config object was offered and DECLINED: it would design a surface before a
second real case exists. Specifically, the inefficiency perceptibility test (maintainer ruling
2026-09-12: inefficiency that impacts the user experience is a defect, inefficiency users cannot notice
is not) stays PROSE in the written rule and does not become config.

## Relationship to qmgn12

`qmgn12` OQ-01 is resolved by this decision and the Set does NOT implement the key: child 01 states that
the gating work-kinds are configurable and default to `bug`, without shipping the reader. If an executor
finds that sentence cannot be written honestly before the key exists, they are instructed to RAISE it
rather than expand scope. One live `security` item exists today (`754txs`, graduated, ungated: the
auto-approve predicate trusts a `- Readiness:` field without verifying a review produced it), and it is
already carried by a plan, so gating the LABEL was never what protected it.
