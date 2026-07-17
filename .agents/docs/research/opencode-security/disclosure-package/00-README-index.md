# OpenCode shared-host security analysis: disclosure package (index)

Prepared for: OpenCode maintainers (private security channel), pending approval to submit AI-assisted material.
Prepared by: the reporting team at the University of Rhode Island, with validation help from HPC/research-computing colleagues at peer institutions.
Provenance: human-owned, AI-assisted. Findings were produced and then adversarially cross-reviewed by three independent AI agents (see 05). Nothing here should be read as independent unaided human work; it is offered as thorough assisted analysis for a human-owned report.
Date assembled: 2026-07-16.

## Status and intent

This package accompanies a request for permission to submit AI-assisted material without triggering the project's automatic-ban policy for AI-generated reports. It is provided so the maintainers can gauge depth and decide format. It is NOT published anywhere; distribution is limited to the private security channel.

We acknowledge the project's SECURITY.md position that server mode is opt-in and that "server access when opted-in" is expected behavior. We are raising this because of the practical shared-infrastructure (HPC / multi-tenant) consequences, and because a few well-contained changes appear able to reduce the risk substantially while preserving compatibility for legitimate server and IPC users. We defer entirely to the maintainers on scope.

## Contents

- `00-README-index.md` - this file.
- `01-executive-summary-and-report.md` - the human-readable report: threat model, the verified chain, affected scope, what is and is not in scope, severity, and the HPC/consortium context.
- `02-test-evidence.md` - the controlled test campaign (discovery, reachability, disclosure, shell execution as victim, network exposure, attended-TUI visibility, mitigation), labeled by verification method (runtime / source / reported).
- `03-source-validation.md` - file:line source citations for every load-bearing claim, and the four framing corrections the review process applied.
- `04-patch-proposal.md` - proposed remediations mapped to source, sequenced as reviewable PRs. DESIGN SPECIFICATION / PSEUDODIFF ONLY - not compiled, not tested.
- `05-provenance-and-cross-validation.md` - how the analysis was produced, the three-agent adversarial review, and what each review caught/corrected. Establishes rigor and honesty about limits.

## Load-bearing honesty notes (read before the rest)

1. Precondition: every finding requires a REACHABLE OpenCode HTTP listener (`opencode serve`/`web`, or a config/tool that opens one). A plain TUI opens no listening socket and is not affected via this surface. This was verified on a fresh install.
2. `/session/{id}/shell` is the DEMONSTRATED ungated command-execution path. `/session/{id}/message` (agent tool calls) IS gated by the permission system (default `ask` blocks) and must NOT be described as categorically ungated.
3. The filesystem issue is a CALLER-SELECTED confinement root (an attacker passes `?directory=/`), not a `..` path-traversal bypass; the `contains` guard is present and correct.
4. Source line numbers were read from a downstream fork's `dev` at commit `08fb47373` (`git describe` = `github-v1.2.25-1295-g08fb47373`), just past a v1.18.3-era bump. They MUST be re-pinned to the exact upstream release the maintainers wish to treat as the target before any fix work.
5. The patches in `04` are design specifications and pseudodiff. They are NOT compiled, typechecked, or tested. They locate the seams and describe intent; producing real, reviewed, tested code is a separate step.
6. Runtime testing used synthetic credentials, harmless marker files under a dedicated temp directory, and controlled test accounts. No live secrets, private keys, or third-party data are included in this package.
7. Some validation was performed by HPC/research-computing colleagues on their own controlled environments; we deliberately do not attribute specific tests to specific individuals, as we cannot precisely reconstruct who ran which subset. Treat colleague-reported items as independently corroborated but not all re-run by the primary reporter.
</content>
