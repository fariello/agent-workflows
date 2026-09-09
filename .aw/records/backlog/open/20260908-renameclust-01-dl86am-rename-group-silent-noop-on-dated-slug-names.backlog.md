- Id: dl86am
- Status: open
- Set: renameclust
- Priority: medium
- Work-Kind: bug
- Summary: aw rename and aw group silently no-op on a legacy dated-slug name: compute_target_name's _DATED_SLUG_FACET_RE branch discards to-id6/set/order and returns the input with err None, so a re-cluster reports success having changed nothing

## Workflow history
- 2026-09-08 created (aw backlog): aw rename and aw group silently no-op on a legacy dated-slug name: compute_target_name's _DATED_SLUG_FACET_RE branch discards to-id6/set/order and returns the input with err None, so a re-cluster reports success having changed nothing

FOUND 2026-09-08 while fixing `check.name-nonconformant` findings. Three legacy-named records cannot
be brought onto the naming grammar by ANY shipped verb, and the verbs report success while doing
nothing, so the condition is invisible unless someone diffs the result.

THE THREE FILES, all currently reported by `aw doctor` as `check.name-nonconformant`:

    .aw/records/walkthroughs/20260823-highpbacklog0822-execution-decisions.walkthrough.md
    .aw/records/walkthroughs/20260821-awoptimize-rescope-walkthrough.walkthrough.md
    .aw/records/roadmaps/20260712-1426-agent-workflows-bounded-iteration-skills-roadmap-for-consideration.roadmap.md

THE DEFECT, measured. `artifact_rename.compute_target_name` tries its shape regexes in order and the
LAST-BUT-ONE branch, `_DATED_SLUG_FACET_RE` (`artifact_rename.py:172-178`), matches all three. That
branch rebuilds the name from ONLY `date` + `slug` + `facet` and silently DISCARDS `new_set`,
`new_order` and `to_id6`:

    m_dated = _DATED_SLUG_FACET_RE.match(src_name)
    if m_dated:
        date_str = m_dated.group("date")
        slug = _core.kebab(new_slug) if new_slug else m_dated.group("slug")
        facet = m_dated.group("facet")
        ext = f".{facet}.md" if facet else ".md"
        return f"{date_str}-{slug}{ext}", None          # <- no set, no NN, no id6

Its pattern is `\A(?P<date>\d{8})-(?P<slug>[a-z0-9-]+)(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z`, which is
broad enough to swallow any dated non-clustered name.

REPRODUCTION (asking for a full re-cluster; note `err` is None, i.e. SUCCESS):

    >>> from agent_workflows import artifact_rename as ar
    >>> ar.compute_target_name('20260823-highpbacklog0822-execution-decisions.walkthrough.md',
    ...     'walkthroughs', new_set='demoset', new_order=1, to_id6=True, mint_id6='abc123')
    ('20260823-highpbacklog0822-execution-decisions.walkthrough.md', None)

Identical no-op for the other two. At the CLI both surfaces confirm it:

    $ aw rename walkthroughs .aw/records/walkthroughs/20260823-highpbacklog0822-execution-decisions.walkthrough.md --set highpbacklog0822 --order 1 --to-id6
    --- would rename ... -> 20260823-highpbacklog0822-execution-decisions.walkthrough.md ---
    --- would inject '- Id: d765tp' into ... ---

    $ aw group walkthroughs .aw/records/walkthroughs/20260821-awoptimize-rescope-walkthrough.walkthrough.md --set awoptimize --order 1 --rename
    --- would set metadata Set: awoptimize in ... ---

The first prints a rename whose source and destination are THE SAME STRING, and would still inject an
`- Id:` -- so `--apply` there mints an identity into a file whose name keeps no id6 slot to hold it.
The second drops the `--rename` half entirely and only writes metadata.

TWO DISTINCT DEFECTS, worth separating because the second is the load-bearing one:

D1. `_DATED_SLUG_FACET_RE` is reached for names the caller explicitly asked to CLUSTER. When
    `to_id6`/`new_set`/`new_order` are supplied, a match on a non-clustered shape should build the
    clustered name (the target IS constructible: `npn.is_conformant('20260823-highpbacklog0822-01-d765tp-execution-decisions.walkthrough.md', expected_type='walkthrough')` returns True, verified).
D2. A no-op is returned as `(name, None)`, i.e. SUCCESS with err None. Any branch that cannot honor
    the requested mutation must return an ERROR naming what it could not apply. This is why the
    condition is invisible: the verb exits 0 and prints a would-rename line. Compare the explicit
    fallback at `artifact_rename.py:187`, which DOES return `(None, "unable to parse and compute new
    name for ...")`; these three never reach it.

D2 IS THE PRIORITY even if D1 is deferred, because a silent success is what lets an agent report the
name fixed when it was not. Same class as the `aw rename` remediation defect filed alongside this
(`9yf5u9`), and the two will be read together.

CARE REQUIRED, do not just widen the regex. `_DATED_SLUG_FACET_RE` is documented at
`artifact_naming.py:17` as "the ONE dated-slug form", and there is a deliberate `--to-id6` ordering
comment at `artifact_rename.py:110-114` explaining that the legacy TIMESTAMP branch is tried FIRST
precisely because a 4-digit HHMM would otherwise be captured as a setid. The roadmap file here IS a
`YYYYMMDD-HHMM-...` name, so check why it does not take the legacy-timestamp branch: its `NN` segment
is missing (`20260712-1426-agent-workflows-...`, no `-NN-`), so `_LEGACY_TIMESTAMP_RE` does not match
and it falls through to the dated-slug branch. A fix must keep every currently-accepted name behaving
identically; the existing rename/group suites pin that.

WHETHER TO RENAME THESE THREE FILES AT ALL IS A SEPARATE, HUMAN CALL, and this item does NOT assume
the answer. Executed plan `o6b8l3` V-06 records the two walkthroughs as "PRE-EXISTING legacy
non-clustered names (no id6), reported non-conformant identically before AND after this refactor - NOT
in this IPD's scope", and executed plan `30jug9` records the roadmap the same way ("`roadmaps` exits 1
on a pre-existing NAME finding"). So the corpus decision has been deferred twice on purpose. This item
is about the TOOL LYING when asked to do it, which is true regardless of whether the three files are
ever renamed. If the tool is fixed and the files are then renamed, note both walkthroughs are cited by
executed plans (`o6b8l3`, `wot0nc`, `53yczi`) and the roadmap by `30jug9`, so citation rewriting
matters; and per D140 a walkthrough must get its OWN minted id6 rather than reusing its source plan's.
