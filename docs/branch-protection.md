# Branch protection: the authoritative repository boundary

This document describes the required-CI + protected-branch policy that makes the agent-workflows
policy engine an authoritative, non-bypassable repository boundary (agentadhere Phase 5, IPD
r2ks4k; findings `bu9yij` section 7.8). It is the layer the local git hooks (Phase 4) deliberately
defer to.

## Why this layer exists

The local git hooks (`aw precommit-scope-gate`, `aw prepush-authorization-gate`, and the other
`aw ...-gate` hooks) are honest LOCAL feedback: they are not cloned by default, are skippable with
`--no-verify`, and run in an environment the agent controls. They cannot be an authority boundary.
The only non-bypassable control for a repository invariant is a REQUIRED check that runs in a clean,
remote environment on a PROTECTED branch, plus protection of the policy and CI definitions
themselves so they cannot be quietly weakened.

## What CI enforces (fail-closed, already in the repo)

The `attention-check` job in `.github/workflows/tests.yml` runs the SAME shipped policy engine that
`aw check` runs locally (`python -m agent_workflows check ...`), so CI and local results cannot
diverge. It fails the job (blocks the merge) on any finding for:

- `aw specs check` - the spec status/gate/history contract;
- `aw attention --check` - the cross-tree attention view;
- `aw check plans` - plan (IPD) conformance;
- `aw check releases` - release-record conformance.

`aw check backlog` also runs in the same job but is currently ADVISORY (report-only): the backlog
tree carries pre-existing name/summary debt that a fail-closed gate would fail `main` on. It joins
the fail-closed set above once that baseline is cleaned by a separate migration (see the run
decision `18-r2ks4k-D1`). Until then CI still prints the backlog findings as a warning so they stay
visible.

No second test-run step was added: the `unittest` job already runs the full suite.

## What a repo admin MUST enable (this is a remote action the toolkit cannot self-enforce)

Enabling GitHub branch protection is a repo-ADMIN action on the remote. The local toolkit and this
repository cannot enable it for you; it must be configured in the GitHub repository settings. To make
the boundary authoritative, a maintainer should, on the default branch:

1. REQUIRE the status checks from `.github/workflows/tests.yml` (at least the `unittest`,
   `attention-check`, `wheel`, and `output-conformance` jobs) as required checks before merge.
2. DISALLOW ordinary bypass: do not allow force-pushes, do not allow the required checks to be
   skipped, and restrict who (if anyone) may bypass the rules to a minimal admin set.
3. REQUIRE review from Code Owners so the policy/CI/hook definitions cannot be weakened without an
   owner review. This needs the `.github/CODEOWNERS` file (present in this repo) AND the "Require
   review from Code Owners" setting enabled; edit `CODEOWNERS` to name the real maintainer handle or
   team (it ships with an `@OWNER` placeholder so no maintainer identity is committed to this public
   repo).

## Honest limits

- Branch protection is a REMOTE control. Nothing in this repository or the local toolkit enforces it;
  a maintainer must enable it in GitHub settings. A CODEOWNERS file by itself enforces nothing until
  "Require review from Code Owners" is turned on.
- CI on a protected branch is the authoritative boundary for REPOSITORY invariants (conformance,
  scope, release gates). It does NOT provide AUTHORITY-invariant guarantees such as non-forgeable
  provenance, an external signing service, or a brokered push credential - those are a deferred,
  separately-tracked external-authority effort. Do not present this CI/branch-protection layer as if
  it provided non-forgeable attestation.
