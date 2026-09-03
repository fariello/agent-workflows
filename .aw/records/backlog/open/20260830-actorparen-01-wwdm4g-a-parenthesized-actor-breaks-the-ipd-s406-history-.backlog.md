- Id: wwdm4g
- Status: open
- Blocks-Release: next
- Set: actorparen
- Priority: medium
- Work-Kind: bug
- Summary: A parenthesized actor breaks the IPD-S406 history regex, so finalize commits the lifecycle transition then refuses post-transition validation

## Workflow history
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

OBSERVED TWICE ON 2026-08-30, independently, by two different agents. That is what makes it worth
filing rather than shrugging at: it is not one agent's typo, it is a shape the tooling invites and the
linter rejects.

THE MECHANISM. `ipd_lint._HISTORY_ATTRIB_RE` captures a history line's actor with
`\((?P<actor>[^)]*)\)`. The `[^)]*` stops at the FIRST closing paren, so an actor that itself
contains parens never matches the pattern at all. `_newest_executed_history` then falls through to its
bare-line branch and returns `("", "")`, and `_check_terminal_attribution` (IPD-S406) reports that the
newest `executed` entry has an EMPTY actor AND an empty summary, even though both are plainly present
in the file.

WHY IT IS WORSE THAN A LINT NUISANCE. IPD-S406 runs as POST-TRANSITION validation inside `aw ipd
finalize`. By the time it fires, the lifecycle COMMIT ALREADY EXISTS. The transaction therefore lands
in the COMMITTED-INCOMPLETE state and reports:

    refused: finalize is COMMITTED-INCOMPLETE for <id6>: the lifecycle commit <sha> exists but
    post-transition validation failed. Re-run the SAME command to resume

Re-running does NOT help, because the offending text is now in the file and the regex still cannot
parse it. The operator is told to resume an operation that cannot succeed. The only way out is to edit
the history line, which is hand-editing a plan that is already in `executed/` and therefore also trips
the executed-transition gate (backlog `gjadwm`), requiring `--no-verify` on top. One bad character
class cascades into two gate bypasses.

THE TWO SIGHTINGS.
1. Me, finalizing `af7i6p`. I passed `--actor "opencode (its_direct/pt3-claude-opus-5-1m-us)"`.
   Lifecycle commit 3b1df90f landed, post-transition validation refused, and completing the
   transaction required editing the executed plan's history line to
   `opencode/its_direct/pt3-claude-opus-5-1m-us` and committing that with `--no-verify`.
2. The `2ouj70` lane agent, independently. Its worktree held a ONE-LINE UNCOMMITTED fix changing
   exactly the same string from the parenthesized form to `opencode/its_direct/...`. It hit the same
   wall, diagnosed it, and fixed it in-flight; the fix was never committed, so merging the lane would
   have REINTRODUCED the broken form. It survived only because the lane's dirty state was harvested
   before cleanup.

WHY AGENTS KEEP WRITING THE PARENTHESIZED FORM. It is the shape the tooling itself teaches. `aw ipd
scaffold --author` accepts and preserves it, and a large number of plans carry
`- Author: opencode (its_direct/...)` in their frontmatter. An agent that copies its own Author string
into `--actor` produces an unparseable history line. So the two conventions diverge silently, and the
divergence is only detected AFTER a commit has been made.

WHAT TO SOLVE FOR, not a prescribed fix.
1. Should the REGEX accept a parenthesized actor (for example a greedy capture anchored on the
   trailing `):` rather than `[^)]*`)? Cheap and fixes both sightings at once, but needs care not to
   swallow a `):` occurring inside a summary.
2. Should the SETTER normalize the actor on the way in, so an unparseable form can never be written?
   Fail-fast at `aw ipd finalize --actor` beats fail-after-commit, and it is the only option that
   prevents the committed-incomplete state rather than merely tolerating it.
3. Should IPD-S406 run BEFORE the lifecycle commit rather than after? The deeper issue is that a
   formatting rule about text the transaction itself writes is enforced post-commit, which is what
   converts a typo into a wedged transaction.
4. Should `Author` and `actor` share ONE documented spelling, with `aw ipd scaffold` emitting the form
   the linter accepts? The two surfaces currently disagree and nothing detects that.
5. Is there other tooling that reads the actor and would break on either form? Worth a sweep before
   choosing, so the fix does not just move the incompatibility.

INTERIM GUIDANCE for anyone finalizing by hand: pass the SLASH form,
`--actor "opencode/its_direct/<model>"`. Verified to parse (`IPD-S406 parses actor:
'opencode/its_direct/pt3-claude-opus-5-1m-us'`), and `z2isfg` was finalized with it cleanly with no
committed-incomplete state and no `--no-verify` needed for the transition itself.

RELATED. Backlog `gjadwm` (the executed-transition gate cannot see a consumed finalize journal) is the
defect that makes RECOVERING from this require a second bypass. Backlog `xmqv5l` (begin freezes a
whole-file digest) was also hit during the same `af7i6p` finalize. Backlog `v880xk` (a stale frozen
base makes scope-drift emit ~1000 findings) is a fourth. FOUR independent defects in the
receipt/journal/attribution layer surfaced in a single session, which argues for one coherent review of
the finalize-evidence model rather than four separate patches.

DISCOVERED while hand-merging lane branches after an overnight run in which validation was disabled,
so plans self-finalized inside their lanes without integrating.
