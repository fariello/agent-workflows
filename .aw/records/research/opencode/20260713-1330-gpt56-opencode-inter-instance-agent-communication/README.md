<!--
Research baseline: OpenCode v1.17.18, tag commit b1fc811, released 2026-07-09.
Research date: 2026-07-13, America/New_York.
Evidence labels: VERIFIED-SOURCE, DOCUMENTED, OBSERVED-EXTERNAL-REPORT, INFERRED, PROPOSED.
No live OpenCode binary was available in the execution sandbox, so runtime claims are source-derived unless explicitly labeled otherwise.
-->
# OpenCode Inter-Instance Agent Communication Research Package

This package executes the uploaded deep-research prompt on communication between concurrent OpenCode instances.

## Read in this order

1. [20260713-occomms-03-tmylmj-executive-summary.executive-summary.md](20260713-occomms-03-tmylmj-executive-summary.executive-summary.md)
2. [20260713-occomms-04-t5xyw0-native-capabilities-and-runtime.research-report.md](20260713-occomms-04-t5xyw0-native-capabilities-and-runtime.research-report.md)
3. [20260713-occomms-05-u5wtc3-communication-methods-comparison.research-report.md](20260713-occomms-05-u5wtc3-communication-methods-comparison.research-report.md)
4. [20260713-occomms-06-fl4bfm-provenance-and-security.research-report.md](20260713-occomms-06-fl4bfm-provenance-and-security.research-report.md)
5. [20260713-occomms-07-e1majf-plugin-feasibility-and-design.research-report.md](20260713-occomms-07-e1majf-plugin-feasibility-and-design.research-report.md)
6. [20260713-occomms-08-wz8x3l-core-enhancement-proposal.research-report.md](20260713-occomms-08-wz8x3l-core-enhancement-proposal.research-report.md)
7. [20260713-occomms-09-3rpcmu-implementation-roadmap.roadmap.md](20260713-occomms-09-3rpcmu-implementation-roadmap.roadmap.md)
8. [20260713-occomms-11-8xgwvm-sources.research-report.md](20260713-occomms-11-8xgwvm-sources.research-report.md)
9. [prototype/README.md](prototype/README.md)

## Key conclusion

OpenCode's native HTTP/SDK API can send prompts to known sessions and start an idle session. It is not a secure, durable peer-agent messaging system. The recommended production design is a local durable coordinator with headless OpenCode workers and a thin plugin or MCP adapter.

## Research limitation

No OpenCode executable was available in the execution sandbox, so live two-instance experiments remain an explicit next step. Source-level findings are pinned to v1.17.18.
