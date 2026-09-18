- Id: b0dcyp
- Status: open
- Blocks-Release: next
- Set: b0dcyp
- Priority: medium
- Work-Kind: bug
- Summary: There is no way to record a bug's release-gate EXEMPTION: a literal Blocks-Release dash trades one error rule for another

## Workflow history
- 2026-09-18 created (aw backlog): There is no way to record a bug's release-gate EXEMPTION: a literal Blocks-Release dash trades one error rule for another

FOUND 2026-09-18 while executing nobugship rgaasb E-04, which instructs that a bug which genuinely should not gate the release 'needs an explicit - Blocks-Release: - plus a reason in its history, not silent omission'. That mechanism DOES NOT WORK.

MEASURED, two ways.

(1) THE LITERAL MARKER TRADES ONE ERROR FOR ANOTHER. A fixture item carrying '- Blocks-Release: -':
check.live-bug-ungated is correctly silent, but the full sweep then reports
check.blocks-release-dangling (also ERROR, also I-07), because '-' does not resolve to a release
record. So the prescribed exemption is not expressible: an item is either ungated (flagged by the new
rule) or dash-gated (flagged by the dangling rule).

(2) THE SETTER WRITES NO RECORD FOR A NO-OP DE-GATE. Running
'aw backlog set graduated cnwy8g --blocks-release - --message <a long recorded rationale>' on an
already-ungated item returned outcome clean, exit 0, applied FALSE, changes [{kind: noop}], and wrote
NOTHING to the file: no gate line, and critically no history entry carrying the rationale. Verified
with git status immediately afterwards (no modification). This is the shipped defect x6tk1u
('same-status set discards message') showing up on the gate path, so the reason for an exemption
cannot be recorded through the tool at all.

WHY IT MATTERS. Without an expressible exemption, every ungated live bug looks identical to the
checker: a genuine deliberate exemption is indistinguishable from an oversight. That is precisely the
distinction rgaasb's E-04 was told to preserve ('DO NOT BLANKET-APPLY'), and it pushes a future
executor toward the wrong fix: re-gating an item whose de-gate was a recorded decision, just to
silence the sweep. The live instance is cnwy8g, de-gated on 2026-09-09 with a documented reason,
which rgaasb therefore had to leave as a standing finding.

SUGGESTED FIX, needing a decision rather than only code: introduce a typed exemption the checker
understands (for example a '- Gate-Exempt: <reason-ref>' field, or teaching check.live-bug-ungated to
accept an item whose history carries an attributed de-gate record), so an exemption is a positive
assertion with an author and a reason rather than an absence. Whichever shape is chosen must also fix
the no-op-discards-message behavior, or the reason still cannot be written.
