# Durable Conformance Probe Results Report Template

- Probe Date: YYYY-MM-DD
- Harness Version: 1.0.0
- Gating Purpose: Clean-delta and skills delivery tier release verification (D109 Phase 0)
- Execution Mode: Operator-run host probe against isolated harness fixtures

> [!IMPORTANT]
> Evidence Gate Discipline: No clean-delta or skills delivery tier (T1 out-of-repo, T2 skill, T3 global, fallback) may be shipped on documentation alone. A live per-host/version probe MUST reproduce the documented behavior. Resolved requires diagnostic/context evidence; Followed requires a verified nonce side-effect file.

## 9-Point Required Release Fixture Summary Table

| Host & Version | Tier & Variant | Nonce | Isolated Fixture Base | Environment (HOME) | Resolved? | Followed? | Side-Effect File | Verified By |
|---|---|---|---|---|---|---|---|---|
| OpenCode v1.0 | T2 (default) | 4f8a91c2 | /tmp/probe-opencode-t2 | /tmp/probe-opencode-t2/home | YES | YES | PROBE-OK-opencode-1.0-4f8a91c2.txt | operator-name |
| Claude Code v2.0 | T1 (default) | 9b2e11a4 | /tmp/probe-claude-t1 | /tmp/probe-claude-t1/home | YES | YES | PROBE-OK-claude_code-2.0-9b2e11a4.txt | operator-name |

## 9 Recipe Fields Checklist

1. **Host Identification & Version**: Full name and exact version of the host evaluated.
2. **Delivery Tier & Variant**: Tier (T1 pointer, T2 skill, T3 global) and variant (default, noninteractive, permission-denied, precedence).
3. **Isolated Fixture Base & Nonce**: Path to clean temp base directory and unique random nonce.
4. **Exact Execution Commands**: Copy-pasteable shell script executed by the operator.
5. **Environment Isolation Verification**: Confirmation that `$HOME` and `$XDG_CONFIG_HOME` pointed inside the fixture base and real home was untouched.
6. **Diagnostic Evidence (Resolved)**: Captured diagnostic logs or context dump proving the host loaded/attached the content.
7. **Nonce Side-Effect Evidence (Followed)**: Path and contents of `PROBE-OK-<host>-<version>-<nonce>.txt`.
8. **Classification Verdict**: Explicit classification of Resolved vs. Followed vs. Precedence behavior.
9. **Verification Metadata**: Operator identity, execution timestamp, and pass/fail verdict.

## Individual Host Probe Records

### Host Probe Record: <host> v<version> - <tier> [<variant>]

- **Host**: <host> v<version>
- **Tier & Variant**: <tier> (<variant>)
- **Nonce**: <nonce>
- **Operator**: <operator-name>
- **Timestamp**: <iso-timestamp>
- **Classification Verdict**: Resolved=<YES/NO>, Followed=<YES/NO>
- **Nonce Side-Effect File**: `PROBE-OK-<host>-<version>-<nonce>.txt`
- **Side-Effect Verified**: <YES/NO>
- **Diagnostic Evidence**:
```
<Paste exact un-truncated diagnostic log or context dump here>
```
- **Notes & Observations**:
<Additional notes on host behavior, permissions, prompts, or limitations>
