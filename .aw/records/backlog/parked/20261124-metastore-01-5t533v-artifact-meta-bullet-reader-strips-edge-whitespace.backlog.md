- Id: 5t533v
- Status: parked
- Release-Exempt-Kind: artifact
- Release-Exempt-Ref: cxxmyv
- Set: metastore
- Work-Kind: bug
- Priority: low
- Summary: artifact_meta bullet reader strips edge whitespace-class control chars (FF, VT, FS-US, NEL) from values, hiding them from is_safe_descriptive checks in backlog.validate_item and specs.validate_spec
- Short-Description: artifact_meta bullet reader strips edge whitespace-class control chars (FF, VT, FS-US, NEL) from values, hiding them from is_safe_descriptive checks in backlog.validate_item and specs.validate_spec

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 parked (aw set): Moot after metastore cutover (cxxmyv): post-cutover backlog.py (fljn9b) and specs.py (szykgd) validate JSONL log fields directly instead of the legacy bullet parser.
- 2026-11-24 created (aw backlog): artifact_meta bullet reader strips edge whitespace-class control chars (FF, VT, FS-US, NEL) from values, hiding them from is_safe_descriptive checks in backlog.validate_item and specs.validate_spec
