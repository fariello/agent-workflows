<!--
Research baseline: OpenCode v1.17.18, tag commit b1fc811, released 2026-07-09.
Research date: 2026-07-13, America/New_York.
Evidence labels: VERIFIED-SOURCE, DOCUMENTED, OBSERVED-EXTERNAL-REPORT, INFERRED, PROPOSED.
No live OpenCode binary was available in the execution sandbox, so runtime claims are source-derived unless explicitly labeled otherwise.
-->
# OpenCode Inter-Instance Agent Communication Research Package

This package executes the uploaded deep-research prompt on communication between concurrent OpenCode instances.

## Read in this order

1. [00-executive-summary.md](00-executive-summary.md)
2. [01-native-capabilities-and-runtime.md](01-native-capabilities-and-runtime.md)
3. [02-communication-methods-comparison.md](02-communication-methods-comparison.md)
4. [03-provenance-and-security.md](03-provenance-and-security.md)
5. [04-plugin-feasibility-and-design.md](04-plugin-feasibility-and-design.md)
6. [05-core-enhancement-proposal.md](05-core-enhancement-proposal.md)
7. [06-implementation-roadmap.md](06-implementation-roadmap.md)
8. [sources.md](sources.md)
9. [prototype/README.md](prototype/README.md)

## Key conclusion

OpenCode's native HTTP/SDK API can send prompts to known sessions and start an idle session. It is not a secure, durable peer-agent messaging system. The recommended production design is a local durable coordinator with headless OpenCode workers and a thin plugin or MCP adapter.

## Research limitation

No OpenCode executable was available in the execution sandbox, so live two-instance experiments remain an explicit next step. Source-level findings are pinned to v1.17.18.
