---
name: assess-local-leaks
description: Use when the user asks to assess-local-leaks (Detect maintainer/machine identifying info that must not be in a public artifact (home paths, usernames, other local accounts, private repo names, hostnames, session ids) across the working tree, git history, and the built wheel (via `aw check-local-leaks`, consuming its `--agent` record stream); enumerate emails/usernames and ask which are intended-public; propose a scrub/allowlist IPD. The class ordinary secret scanners miss (D92/D93)). Do not use for unrelated requests or when no assess-local-leaks action was requested.
semantic-digest: c54d2634c61aa4dd24b8ef3791381c74ad4dcbd0f819b2ce0a191b50aaadf62b
---

# Skill: assess-local-leaks

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `c54d2634c61aa4dd24b8ef3791381c74ad4dcbd0f819b2ce0a191b50aaadf62b`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
