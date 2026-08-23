# Skill selection

A host discovers a workflow through a generated skill package and dispatches it. This document
describes how discovery and dispatch work and where precedence is decided.

## The skill package

For each workflow the compiler generates a portable skill package
(`agent_workflows/host_adapters.build_skill_package`) rooted at `.agents/skills/<name>/`:

- `SKILL.md`: the router. It carries a trigger description (an affirmative "Use when" clause and
  a negative "Do not use" clause), the canonical semantic digest, and an explicit runtime
  invocation. The router POINTS at the canonical body via the digest; it never inlines the
  authoritative steps.
- `reference/canonical-body.md`: a pointer to the authoritative instruction.
- `scripts/verify_digest.py`: a deterministic script that recomputes the parity digest.

`validate_skill_package` fails a package that is missing frontmatter, lacks the use/non-use
clauses, references a missing resource, exceeds the entry-point byte budget, or does not carry
the canonical digest. `check_authority_not_inlined` fails a router that copied the canonical
body into its own prose.

## Precedence

A workspace-local skill (under `.agents/skills/`) deterministically supersedes a global skill
(under a host config directory). The host capability registry proves this with the
`path_precedence` negative probe (see [host-adapters.md](host-adapters.md)).

## Least privilege (security boundary)

The router is a least-privilege pointer, not an authority. The security check
`security_hardening.check_skill_least_privilege` refuses a package whose entry point inlines the
canonical body or fails package validation. See [security.md](security.md).

## Limitations

- A host advertises a discovery feature as supported only where the capability registry promoted
  it from a live probe; otherwise the feature is "unverified".
- A malformed skill frontmatter is rejected fail-closed rather than executed (the
  `malformed_frontmatter` negative probe).
