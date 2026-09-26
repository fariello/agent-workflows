- Id: vy20et
- Status: open
- Set: reqids
- Priority: medium
- Work-Kind: feature
- Summary: Specs have no machine-readable requirement-ID convention, so SPEC-PLAN-TRACE (every spec requirement covered by a plan E item, every acceptance criterion by a V item) cannot be built: specify a convention and parser

## Workflow history
- 2026-09-26 created (aw backlog): Filed during /spec-review of z7nbn1 per maintainer ruling 2026-09-26: SPEC-PLAN-TRACE deferred out of z7nbn1 until a requirement-ID convention and parser exist as their own spec.

WHY THIS EXISTS. Spec 25kzda 4.8 declares SPEC-PLAN-TRACE: after the runner authors plans from an approved spec, verify every mandatory spec requirement maps to at least one E item and every acceptance criterion to at least one V item. Spec z7nbn1 OQ-02 (ruled 2026-09-16) put it in scope; its 2026-09-26 spec review found it cannot be built deterministically because specs carry no consistent machine-readable requirement id. Research vkub9o (2026-09-20) measured three incompatible forms across 36 specs (letter-prefixed ids, bare dotted paragraph numbers such as z7nbn1's own 1.1, and section headings) and recommended against a parser; the maintainer ruled on 2026-09-26 that the convention and parser should be decided as a SEPARATE spec rather than inside z7nbn1, with TRACE waiting on it.

WHAT GRADUATING THIS NEEDS. A spec that defines: the requirement-id convention for new specs, whether live specs are retrofitted (vkub9o counts 6 live specs needing ids or reconciliation), the parser, and SPEC-PLAN-TRACE's severity. Honest limit to carry: a trace check proves a plan step CITES a requirement, not that it implements it. Related: backlog 1zknu7 (plans omit the From-Spec edge), research vkub9o, spec z7nbn1 OQ-02, spec 25kzda 4.8.
