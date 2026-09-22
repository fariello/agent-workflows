- Id: 7q9ycn
- Status: open
- Set: 7q9ycn
- Priority: high
- Work-Kind: chore
- Summary: Update the four documented setter examples that now refuse without --yes

## Workflow history
- 2026-09-22 created (aw backlog): Update the four documented setter examples that now refuse without --yes

FOUND BY: executing IPD 4bc1nd (Set setterguard), which recorded this as finding F-13 and deferred it with a required carrier. OQ-02 recommended it land as a follow-up rather than in 4bc1nd, at HIGH priority because it is the only one of that plan's deferrals a user meets directly.

WHAT IS WRONG. IPD 4bc1nd extended the shipped confirmation refusal to every FLAGLESS caller of the status setters, so a mutating `aw set` / `aw ipd set` / `aw specs set` / `aw backlog set` now exits 2 with 'confirmation required (--yes needed to execute mutation)' unless it is passed `--yes` or `--dry-run`. That is the intended fix (it closed a defect that silently reverted seven executed plans). The side effect is that documented examples written before it are now commands that REFUSE as written.

THE MEASURED OCCURRENCES (line numbers as of this filing):

  - README.md:53                       aw ipd set approved <id> # transition plan status (or aw set approved <id>)
  - .aw/records/plans/README.md:63     aw ipd set <status> <id6|setid|fname>...  (e.g. aw ipd set approved pl0001, aw ipd set to-review my-set)
  - .aw/records/plans/README.md:64     aw set approved <id6|setid|fname>...
  - .aw/records/backlog/README.md:70   aw backlog set <status> <id6|setid|fname>...
  - .aw/records/specs/README.md:24     aw spec set <status> <id6|setid|fname>...

WHY IT MATTERS. GUIDING_PRINCIPLES principle 2 (honest over aspirational documentation) forbids leaving a documented command that does not work. A reader who copies any of these gets an exit 2 and no explanation of why the published form is incomplete.

WHY NOT IN 4bc1nd. Four README files across four record trees is a documentation sweep with its own reviewable surface; bundling it into a two-guard code change would have widened that change into a docs migration. The maintainer may still prefer them folded in.

SUGGESTED FIX. Add `--yes` to each example, or better, say once near each that a mutating setter requires `--yes` (and that `--dry-run` previews) and keep the examples canonical. Check for further occurrences in `.aw/system/workflows/` prose at the same time; the 4bc1nd survey found only prose ABOUT the forbidden `aw set executed` bypass there, not live invocations, but that survey was scoped to the setter verbs.
