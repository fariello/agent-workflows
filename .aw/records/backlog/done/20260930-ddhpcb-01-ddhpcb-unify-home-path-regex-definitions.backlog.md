- Id: ddhpcb
- Status: done
- Graduated-To: ddhpcb
- Set: ddhpcb
- Priority: medium
- Work-Kind: chore
- Summary: The three home-path regexes are duplicated character-for-character between agent_schema and leak_sanitizer with no shared constant and no test asserting they agree

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD 1xthrh executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-ddhpcb-01-1xthrh-hold-the-three-home-path-regexes-as-one-datum-shared-by-agen.ipd.md); evidence .aw/records/plans/executed/20261001-ddhpcb-01-1xthrh-hold-the-three-home-path-regexes-as-one-datum-shared-by-agen.ipd.md
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: 1xthrh
- 2026-09-30 created (aw backlog): Found authoring plan 9yd6tx (backlog 7tixnq) as its F-07. Measured: agent_schema._HOME_PATH_RE is one fused alternation covering POSIX /home/<user>, macOS /Users/<user>, and Windows <drive>:\Users\<user>; leak_sanitizer._FAIL_PATTERNS carries the same three bodies as three separately named rules (home-path, users-path, windows-home). The regex bodies are character-identical, neither module imports the other (agent_schema is stdlib-only; leak_sanitizer defers its renderers/result_types import into main to avoid a cycle), and NO test asserts the two definitions agree. So a fix to one silently leaves the other stale. tests/test_leak_sanitizer.py already gestures at the shared-pattern concern in its BinaryAndStagedScanTests prose but tests only the sanitizer's own rules. Not unified in 9yd6tx because the sanitizer side carries a config-gated per-rule severity model plus allowlists that have nothing to do with the --json leak posture that plan addresses; 9yd6tx only pins its new redaction helper against _HOME_PATH_RE so it adds no third definition. The open question is whether to extract one shared constant or add a cross-module agreement test, which trades a refactor against a cheaper pin.
