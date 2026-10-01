- Id: o53joz
- Status: open
- Set: o53joz
- Priority: low
- Work-Kind: chore
- Summary: Add a mechanical guard so a future lifecycle renderer cannot silently re-collapse the 256/16/none color-depth ladder

## Workflow history
- 2026-09-30 created (aw backlog): Add a mechanical guard so a future lifecycle renderer cannot silently re-collapse the 256/16/none color-depth ladder

RAISED BY plan nw088c (backlog p5qx91) while fixing a measured instance of exactly this.

WHAT HAPPENED, which is the argument for a guard. term.Term.lifecycle_depth ended 'return DEPTH_16 if depth == DEPTH_16 else DEPTH_256', rewriting a resolved 'none' into '256', so a user who pinned 'aw config set color_depth none' still received 256-color ANSI. Meanwhile render_stream.Palette.lifecycle honored the same pin correctly. Two consumers of one pin disagreed and nothing noticed for as long as the pin has existed.

WHAT IS NOT ENOUGH. Plan nw088c closes the two consumer paths that exist today by asserting observable output (ANSI bytes from real commands at each tier). That is the right coverage for those two, but it does not cover 'every future renderer': a third consumer added later could re-collapse the ladder in its own way and no existing behavioral test would see it.

WHY THIS IS NOT SIMPLY A STRUCTURAL PIN. The obvious guard walks the consumers and asserts none of them rewrites a tier, which is precisely the code-structure pin GUIDING_PRINCIPLES P16 prohibits and which the maintainer ruling on p5qx91 forbids for this axis specifically. So the cheap answer is unavailable by policy, which is why this is filed rather than bundled.

ONE DIRECTION WORTH EVALUATING. Give Term no way to express the coercion at all: resolve the tier only in term.resolve_color_depth and have consumers receive it rather than re-deriving it. That removes the defect class by construction instead of policing it. It is an API change to a widely used class, so it needs its own design decision, and it was explicitly out of scope for a release-gating one-line bug fix.
