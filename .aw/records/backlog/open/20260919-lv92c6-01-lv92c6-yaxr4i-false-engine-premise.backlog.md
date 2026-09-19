- Id: lv92c6
- Status: open
- Blocks-Release: next
- Set: lv92c6
- Priority: medium
- Work-Kind: bug
- Summary: Plan yaxr4i asserts the color engine is already correct and complete, which measurement falsifies

## Workflow history
- 2026-09-19 created (aw backlog): Found while converting nyz8dt into lifeglyph child z8ddk0. yaxr4i is approved, so an executor would trust the claim and leave the engine alone.

## The false statement

`.aw/records/plans/pending/20260908-ttyflags-01-yaxr4i-...ipd.md` line 97, in its "Project conventions
discovered" section:

> The color ENGINE is already correct and complete: `should_color` (`term.py:74-98`) implements
> `NO_COLOR` unless `FORCE_COLOR`, then `TERM` capability, then `isatty()`. This item adds a flag
> SURFACE over a working engine; it does not need new color logic.

Measured by EXECUTION 2026-09-19, the engine is neither correct nor singular:

- There are THREE `should_color` implementations, not one. `term.py:90` checks `TERM` and tests by
  presence; `runner_shared.py:276` IGNORES `TERM` and tests by truthiness; `pwatch.py:951` ignores
  `FORCE_COLOR` entirely.
- `FORCE_COLOR=0` FORCES COLOR ON, even to a pipe, because `"0"` is truthy in Python. That is the
  opposite of what the value means.
- `FORCE_COLOR=''` is read by PRESENCE on `term.py:100` and by TRUTHINESS on line 103, so it cancels
  `NO_COLOR` without forcing: one variable, two tests, four lines apart.

The line's DESCRIPTION of the precedence is accurate for `term.py` alone. What is false is the
generalization ("the engine", singular) and the conclusion ("already correct and complete").

## Why it matters

`yaxr4i` is `- Status: approved`, so an executing agent is entitled to trust its Step 0 findings. An
agent reading line 97 would conclude no engine work is needed, add the flag surface over a broken and
triplicated engine, and record a conforming run. The plan would pass its own validation while leaving
every defect above in place.

The immediate hazard is now covered: the engine is owned by lifeglyph child `z8ddk0`, which has its own
E-items and its own pins. So this item is about the STALE CLAIM rather than about unowned work.

## What to do

Not obvious, which is why this is filed rather than fixed. Options, in rough order of preference:

1. Amend line 97 when `yaxr4i` next changes for another reason, noting the measurement and pointing at
   `z8ddk0`. Cheapest, and avoids touching an approved plan solely for a comment.
2. If `z8ddk0` lands FIRST, line 97 becomes retrospectively true (one definition, correct semantics), so
   the amendment could be a one-line note recording that it was false when written. Verify before
   assuming: `yaxr4i` also claims `term.py:74-98` as the line range, which has already drifted to
   `term.py:90` in the shipped file.
3. Leave it and rely on `z8ddk0` owning the work. Weakest, because the false claim stays readable in an
   approved plan.

## The general defect this is an instance of

A plan's Step 0 "conventions discovered" section is UNVERIFIED PROSE that later readers treat as
established fact, and nothing re-checks it when the tree moves underneath. `yaxr4i` was authored
2026-09-08 and its line range was already stale by 2026-09-19. This is worth considering separately from
the specific claim; it is not filed as its own item because the remedy is not obvious and a checker for
prose accuracy may not be feasible.
