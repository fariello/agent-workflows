- Id: 5gmi12
- Status: open
- Blocks-Release: next
- Set: ci9kx2
- Priority: medium
- Work-Kind: bug
- Summary: aw attention --dir <a SUBDIRECTORY of a real AW project> silently under-reports: 0 artifacts shown and exit 0 where the project root reports its real items

## Workflow history
- 2026-09-29 note (aw backlog): NARROWED at review of plan bjgqez (/plan-review, PR-701). Plan bjgqez drops the 'not explicit_dir' guard at attention.run and cli._run_plans, and because is_project_dir(<root>/src/deep) is False (measured at review), that change ALSO catches this item's input: once bjgqez executes, 'aw attention --dir <subdir>' stops printing '0 artifacts shown' at exit 0 and reports cannot-run at 3 (human) / 2 (machine). So the SILENT WRONG ANSWER half of this item is fixed by bjgqez, not by this item, and bjgqez now covers the input in its regression matrix (E-05) and its V-02 evidence. WHAT REMAINS OWED HERE is the resolution-semantics decision this item was really about: whether a refusal is the right final answer, or whether an explicit --dir should CLIMB to the project root the way a bare invocation does. That contradicts resolve_verb_repo_root's documented 'honored verbatim (resolved, no climb)' rule and affects every call site, so it stays a separate decision. Re-measured at review before any change: --dir <root> reports '1 artifact shown', --dir <root>/src/deep reports '0 artifacts shown', and no --dir from inside <root>/src/deep climbs and correctly reports '1 artifact shown', all three at exit 0. Status left 'open' and the release gate untouched; only the scope description is narrowed.
- 2026-09-29 created (aw backlog): aw attention --dir <a SUBDIRECTORY of a real AW project> silently under-reports: 0 artifacts shown and exit 0 where the project root reports its real items

MEASURED at HEAD e4108abf while authoring IPD bjgqez (its finding F-06), and deliberately NOT fixed there.

REPRODUCTION: in a project holding ONE open backlog item, with cwd OUTSIDE any AW project:
  aw attention --dir <root>              -> '## ready (1)' / '1 artifact shown', exit 0
  aw attention --dir <root>/src/deep     -> '0 artifacts shown',                 exit 0
  cd <root>/src/deep && aw attention     -> '1 artifact shown',                  exit 0  (the climb works)

So an explicit --dir one level BELOW a real project root silently under-reports. is_project_dir(<root>/src/deep) is False while find_project_root(<root>/src/deep) correctly returns <root>.

WHY THIS IS WORSE THAN THE NON-PROJECT CASE (backlog ci9kx2): the output is PLAUSIBLE. A non-project directory printing nothing at least looks odd; a project subdirectory printing '0 artifacts shown' at exit 0 looks like a genuinely clean board, so neither a human nor a CI step has any signal that the answer is wrong.

WHY IPD bjgqez DID NOT FIX IT: bjgqez removes the 'not explicit_dir' guard so a NON-PROJECT --dir reports cannot-run. That does not help here, because this directory IS inside a project; the remedy is different in kind. Fixing this means deciding whether an explicit --dir should CLIMB to the project root, which directly contradicts the documented resolve_verb_repo_root rule that an explicit --dir is 'honored verbatim (resolved, no climb) - the operator asked for it'. That rule governs every one of the resolver's ~64 call sites, so the decision is resolution semantics across the package, not a guard change at two sites.

LIKELY OPTIONS, none yet chosen: (a) climb from an explicit --dir exactly as cwd does, changing the verbatim rule; (b) keep verbatim but DETECT the case (is_project_dir false AND find_project_root non-None) and report it, naming the root that was found and the command that would use it; (c) leave it and document the rule harder. Option (b) preserves the published resolution rule while removing the silent wrong answer, and is the cheapest to validate.

SCOPE NOTE: the same question applies to aw ipd board, whose --dir <subdir> prints a green 'CLEAN no plans found (no plans under <subdir>)'.
