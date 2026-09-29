# Review findings: plan 4taj2e

- Subject-Id: 4taj2e
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `9d322249` in an isolated worktree. Structural preflight `aw ipd lint --phase author`
reported `clean` (`findings: 0`) before any edit; re-run at `--phase review-finalize` after revisions, also
clean. No pre-review snapshot was owed: the plan was committed and unmodified. Bare suite at review HEAD:
`3246 passed, 2 skipped, 3 warnings in 47.63s`, matching the plan's own F-06 baseline count exactly. NO
PRODUCTION FILE OR TEST WAS MODIFIED by this review; every fix-side measurement was staged IN MEMORY via a
synthetic module, `git status --short` was empty before and after, and the plan's own mutation-discipline rule
was followed by the review itself.

THE DIAGNOSIS IS CORRECT, THE FIX DIRECTION IS MANDATED BY AN APPROVED SPEC, AND I REPRODUCED THE DEFECT AND
THE REPAIR END TO END. The cell case (a `setid` containing `⚠︎`) renders a two-element width set, the banner
case (a table-widening `exit_reason` containing NFD `cafe\u0301`) likewise, and both become single-element
under the conversion while an all-ASCII table stays BYTE-IDENTICAL in both styling modes. Spec `uonrjg`
Section 9.4's fourth bullet is verbatim "no use of `len(styled_text)` to compute a visible column", so the
plan brings a renderer into compliance with an approved contract rather than proposing a new one; no spec
amendment is owed, as the plan says. F-01, F-03, F-04, F-05, F-07, F-08, F-09, F-10 and F-11 all reproduce,
including the measured facts that both runners set `exit_reason=f"FAILED ({exc})"` on their exception paths,
that `unicodedata.category('\u0301') == 'Mn'`, that all eleven box-drawing characters plus `█`/`▍`/`•` are
East Asian Width `A`, that `_strip_ansi` is re-exported through both drivers' `__all__` and called by two
test modules, and that no existing test measures the width of any summary-table line.

FOUR DEFECTS WERE FOUND. The most serious is that the plan's own prescribed locator grep is BLIND to
`max_banner_w`, the very site the plan singles out as the one the backlog item missed. That is not a cosmetic
slip: the plan promotes that grep to "the durable locator" in E-01 and to the "falsifiable check that no site
was skipped" in V-01, so an executor who trusts it converts the sites it matches, observes zero residual
matches, and ships an incomplete fix having passed the plan's own completeness gate. I proved this by
construction rather than arguing it.

I ALSO CORRECTED A CLAIM IN THE PLAN'S FAVOUR THAT WAS NONETHELESS OVERSTATED. The plan describes
`max_banner_w` as "the site that misaligns a banner case". Measured four ways, both partial fixes yield a
RECTANGULAR box; what `max_banner_w` actually decides is the WIDTH the box settles on, so a box can be
rectangular at the wrong width. This matters because it means E-02's width-cardinality property cannot
distinguish a complete fix from an almost-complete one, which is precisely why the per-line accounting in
V-01 has to be the completeness evidence. Recorded as F-12 and reflected in both items.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | HIGH | IN-SCOPE | G (executability) / D (anti-regression) | plan E-01 locator, V-01 reconciliation, F-02; `render_stream.render_run_summary_table`'s `max_banner_w = max((len(t) for t in banner_plain), default=0) + 4` | The prescribed locator `grep -n "len(_strip_ansi\|len(tot_\|len(h)\|len(tot_str)"` does NOT match `max_banner_w`, because its measurement is spelled `len(t)`. The plan promotes that grep to "the durable locator" (E-01) and to "the falsifiable check that no site was skipped" (V-01), while separately naming `max_banner_w` as the site the backlog item missed and the one that "decides the whole table width". PROVED NON-FALSIFIABLE BY CONSTRUCTION at review: converting the 14 lines the grep matches and deliberately leaving `max_banner_w` alone yields ZERO residual grep matches while the banner fixture still measures a two-element width set on the unfixed tree. The plan's site arithmetic is also off by one for the same reason ("14 matches, 13 convert" describes 14 matches that all convert, plus an unseen fifteenth line) | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-01 now carries a locator that sees every site (`len(` narrowed to the function, 19 lines: 14 convert, 5 do not) and explicitly names the two `len()` calls that MUST survive (`touched` over files, `len(col_widths)` over columns), so neither is converted by mistake. F-02 rewritten with the counting correction measured. V-01 now requires per-line accounting and explicitly forbids offering the old grep as the completeness check. E-01's Expected outcome no longer says "no `len(` remains", which was false by design |
| PR-502 | MEDIUM | IN-SCOPE | E (testing) / G | plan E-02 mutation bullet, gate MUTATION DISCIPLINE; `render_stream`'s `@dataclass(frozen=True)`; `dataclasses._is_type` | The prescribed in-memory mutation mechanism ("an out-of-tree pytest plugin that re-execs the patched source as a module and rebinds the one function"), called "verified to work and the recommended route", CRASHES in its natural spelling: `render_stream` defines a frozen dataclass, `dataclasses` resolves annotations through `sys.modules.get(cls.__module__).__dict__`, and a module not yet registered in `sys.modules` raises `AttributeError: 'NoneType' object has no attribute '__dict__'` during the exec. Reproduced at review, then made to work by registering BEFORE the exec. The risk is specific: an executor hitting this crash concludes the in-memory route is unworkable and falls back to editing the tracked file, which is exactly what the plan's own shared-checkout rule forbids | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now states the ordering requirement with the measured traceback and the working shape, warns against the tracked-file fallback, and offers the simpler `mock.patch.object` route (sufficient here, since the tests call the function directly) as preferred when a whole-module patch is not needed |
| PR-503 | MEDIUM | IN-SCOPE | F (honest documentation) / D | plan Deferred, `format_statusline_lines` entry; commit `19313eed` | The deferral of `format_statusline_lines` rested on a test that does not exist: it cites `test_format_statusline_user_example_box_layout` as pinning that box "byte-for-byte", making conversion "a wider change than it looks". That test was deleted in `19313eed`, and NO test file mentions `format_statusline_lines` or `statusline` at all. The stated reason was therefore backwards: the surface is not protected by a risky byte-pin, it is protected by NOTHING, which makes it more exposed rather than less and changes what the carrier owes | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The deferral entry now records the deleted test and the zero-coverage measurement, keeps the deferral on the honest reason (separate surface, outside the filed scope, needs coverage authored first), and the carrier note now requires the filed item to record that the surface has no coverage so the work is scoped as "author coverage, then convert" |
| PR-504 | LOW | IN-SCOPE | F / E | plan Required tests width-measurement bullet, V-01 | The pasted before/after width baselines (`{120, 121}` -> `{120}`, `{234, 235}` -> `{234}`) are presented as figures to "reproduce or refute", but they depend entirely on the fixture's column contents and on nothing the plan changes. Review reproduced the same PROPERTY with different fixtures and measured `{119, 120}` -> `{120}` and `{263, 264}` -> `{263}`. An executor comparing absolute numbers against the plan's would mis-read a correct run as a discrepancy | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bar is now stated as the CARDINALITY (two distinct widths before, exactly one after), with both the authoring and the review measurements recorded and an explicit note that a differing absolute number is not a finding while a two-member set after the fix is |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is owed
(`check.review-finding-unescalated` satisfied vacuously). No BLOCKER was found. The single HIGH is FIXED in
place and is a defect in the plan's verification apparatus rather than in its design.

WHAT I DELIBERATELY DID NOT FLAG. The plan is unusually careful in several places that a reviewer might be
tempted to second-guess. Its refusal to delete `_strip_ansi` is correct and measured (F-07 reproduces: two
driver re-exports plus two calling test modules). Its refusal to convert `format_event_prefix` is correctly
DECLINED on measurement rather than deferred, since no glyph in that table carries an `Mn`/`Me`/`Cf` code
point. Its bounding of the claim to the deterministic zero-width half is right and important, and F-09's
measurement that the box-drawing characters are THEMSELVES Ambiguous is the strongest possible support for
E-03's required honesty comment. The `banner_plain` simplification is safe: I verified
`visible_width(strip_ansi(x)) == visible_width(x)` holds, so dropping the nested strip is genuinely dead-weight
removal. F-04's reasoning that `visible_width(s) <= len(s)` makes the unguarded subtraction safe is sound, and
adding the `max(0, ...)` guard for consistency is the right call. The byte-identity guard comparing two
renders rather than a stored blob is exactly what P16 requires. OQ-01 is correctly non-blocking and correctly
the maintainer's, and it is carried to a backlog item rather than left in a retiring plan's prose.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | PR-501: the prescribed grep is blind to `max_banner_w`. Replace the grep, or drop the grep-based completeness check entirely in favour of the width property? | Replace the locator AND keep a per-line accounting check, while demoting the property to necessary-but-not-sufficient | Dropping the grep and relying on the width property alone, rejected because review measured that the property CANNOT distinguish a full fix from an all-but-`max_banner_w` fix (both are rectangular); relying on the grep alone, rejected because it was proved non-falsifiable. Only the two together are sound | Measured: converting all-but-`max_banner_w` yields `{264}` (rectangular, wrong width) while full conversion yields `{263}`; the narrow grep reports zero residual on that same broken tree | yes |
| D-2 | PR-503: the deferral's cited pin does not exist, and the surface has zero coverage. Pull `format_statusline_lines` into scope, or keep it deferred? | Keep it deferred, correct the reason, and strengthen what the carrier must record | Pulling it in, rejected on two grounds: backlog `8xcsjr` names `render_run_summary_table` and nothing else, and an untested renderer needs coverage authored BEFORE conversion, which would roughly double this plan and mix two evidence sets. The repository's execution contract also forbids opportunistic widening | `19313eed` deleted the cited test; no test file mentions `format_statusline_lines`; the plan's own scope statement and the filed backlog item's wording | yes |
| D-3 | PR-502: should the plan keep prescribing the module re-exec mechanism at all, given it crashes in its natural spelling? | Keep it, document the `sys.modules` ordering requirement, and add the simpler `mock.patch.object` route as preferred | Replacing it outright with `mock.patch.object`, rejected because the plan's gate also mandates in-memory staging for the whole-module case and a future executor may need it; removing the mechanism would leave that case unaddressed. Leaving it as "verified to work", rejected because it demonstrably does not work as spelled | Measured traceback in `dataclasses._is_type` on the unregistered-module spelling, and a working run once registration precedes the exec; the tests call the target function directly, so the simpler route suffices for this plan's own needs | yes |
| D-4 | F-12 shows a rectangular box can settle at the wrong width. Does that warrant an absolute-width assertion in E-02? | No. Record the limit and rely on V-01's per-line accounting | Adding a width-value assertion, rejected because it would pin fixture contents and rot on any unrelated column change, which is the byte-pinning this repository forbids (P16) and which the plan's own byte-identity design deliberately avoids | `GUIDING_PRINCIPLES` P16; the plan's own stated reason for comparing two renders rather than a stored blob | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
