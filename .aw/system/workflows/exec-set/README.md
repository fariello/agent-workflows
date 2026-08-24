# exec-set

Autonomous IPD Set execution: run every approved, runnable child of a Set with maximal safe
parallelism, route each lane to the right model role, integrate results deterministically, and ask a
human only under the exact two-part stop rule. A thin entry point over the deterministic Set
coordinator; authority stays in the runtime, never in prose. Run `/exec-set <set-id> [--plan-only]`,
or from any agent: "read and execute `.aw/system/workflows/exec-set/exec-set.md`". The explicit
`aw ipd execute-set <set-id>` is always available.
