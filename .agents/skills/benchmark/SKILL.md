---
name: benchmark
description: Use when the user asks to benchmark (Guided performance benchmarking (informational, not a regression gate): author an ISOLATED benchmarks/ suite in the target repo (inert when unused), deeply capture and diagnose the machine/environment (`bench_env.py`: CPU/RAM/GPU/load/filesystem, flags NFS working sets, powersave governor, swapping, busy/login-node with suggested remedies), run with warm-up and >=2 iterations, detect HPC schedulers and (on explicit per-submission consent) generate + submit a job script, and produce a shareable, anonymizable results bundle. Read-only on system state; never publishes). Do not use for unrelated requests or when no benchmark action was requested.
semantic-digest: 3a64775cf13e5a3a894e0412a0d8eb07617e3e79448fd7a40c146f83636f0727
---

# Skill: benchmark

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/benchmark/benchmark.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `3a64775cf13e5a3a894e0412a0d8eb07617e3e79448fd7a40c146f83636f0727`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/benchmark/benchmark.md

## Package resources

- `reference/canonical-body.md` (reference)
