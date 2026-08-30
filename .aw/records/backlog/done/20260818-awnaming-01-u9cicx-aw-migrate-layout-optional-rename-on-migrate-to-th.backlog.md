- Id: u9cicx
- Status: done
- Set: awnaming
- Priority: low
- Work-Kind: chore
- Summary: aw migrate-layout: optional rename-on-migrate to the .type.md grammar

## Workflow history
- 2026-08-18 created (aw backlog): aw migrate-layout: optional rename-on-migrate to the .type.md grammar
- 2026-08-18 set (aw backlog): Implemented by IPD awmigrename-01 (0qp7u8, executed dfa9efc): aw migrate-layout --rename-to-grammar flag + config key + interactive ask + class-correct facet transform (comms/research excepted).

OQ-02 (awnaming Set, resolved ask-then-offer). Because the record readers are front-matter-driven, a legacy repo's bare-.md records keep working after migration (permanent dual-read), so renaming them to the uniform .type.md grammar is an optional nicety, not a correctness requirement. Implement: aw migrate-layout leaves existing records bare by default (gentle); when INTERACTIVE, ASK the human whether to also rename migrated records to the grammar; when NON-INTERACTIVE, default OFF with an opt-in --rename-to-grammar flag. Not a release blocker.
