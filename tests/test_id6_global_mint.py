"""id6 minting is REPOSITORY-WIDE, not per-tree (IPD sk7ggr E-01, E-02, E-07).

THE DEFECT THESE TESTS PIN. `artifact_core.generate_id6(existing)` is collision-checked against a
caller-supplied set, and every one of the eleven mint call sites used to supply only its OWN tree's
ids: backlog checked backlog ids, specs checked spec ids, research checked research filenames. id6
identity is repository-WIDE, so a fresh backlog id6 could equal an existing spec's or an executed
plan's and nothing would notice until the file was written and the id6 cited elsewhere.

WHY A FORCED COLLISION RATHER THAN A STATISTICAL ONE. A test that mints normally and asserts the
result is unique proves nothing: an id6 is one of 36**6 values, so it would pass with a completely
broken collision set. Every test here PINS the rng (`generate_id6`'s `_rng` injection point) to
return a candidate that is ALREADY TAKEN by another tree, then asserts the mint refuses it and moves
on. That is the only shape that can tell a real collision check from an absent one, and it is why
`generate_id6` must stay pure and injectable rather than fetching its own set.

THE TERMINAL CASE IS THE LOAD-BEARING ONE. An executed plan's or a done item's id6 is permanently
cited across the repository (`Item-Dependencies`, `From-Backlog`, review filenames, prose), so
re-minting it is a real collision even though the artifact is no longer live. The motivating
real-world instance (`uyeko5`) is exactly this shape: one side sits in `executed/`.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as core

PLANS_PENDING = ".aw/records/plans/pending"
PLANS_EXECUTED = ".aw/records/plans/executed"
SPECS = ".aw/records/specs"
BACKLOG_OPEN = ".aw/records/backlog/open"
BACKLOG_DONE = ".aw/records/backlog/done"
RESEARCH = ".aw/records/research"


def _plan_text(id6, status="approved"):
    return f"# IPD\n\n- Id: {id6}\n- Status: {status}\n- Set: demo\n\n## Goal\n\nx\n"


def _spec_text(id6, status="draft"):
    return f"# Spec\n\n- Id: {id6}\n- Status: {status}\n- Set: demo\n\n## Body\n\nx\n"


def _backlog_text(id6, status="open"):
    return (
        f"- Id: {id6}\n- Status: {status}\n- Set: demo\n- Priority: medium\n"
        f"- Work-Kind: feature\n- Summary: x\n\n## Detail\n\nx\n"
    )


def _research_text(id6):
    """The RESEARCH dialect: YAML front matter with a bare `id:`, not a `- Id:` bullet."""

    return f"---\nid: {id6}\nkind: research-report\n---\n\n# Report\n\nx\n"


def _tree(files):
    """Materialize `[(relative path, text)]` into a fresh temp repo and return its root."""

    root = Path(tempfile.mkdtemp())
    (root / ".git").mkdir()
    for rel, text in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def _rng_returning(*words):
    """An rng that yields the characters of each word in turn, so candidates are FORCED in order.

    `generate_id6` calls `rng(alphabet)` six times per candidate, so a word is consumed as six
    single-character draws. This is what makes "try a taken id6 first, then a free one" expressible.
    """

    chars = list("".join(words))
    it = iter(chars)

    def _rng(_alphabet):
        return next(it)

    return _rng


class GlobalMintSetTests(unittest.TestCase):
    """`global_id6s` spans EVERY tree and includes TERMINAL artifacts.

    ONE table, because every row is the same claim about a different tree or disposition: an id6
    written anywhere in the records must appear in the one set that mint sites collide against. The
    rows are grouped rather than split because the failure they guard against is a
    MISSING TREE, and a per-tree test reports that as one unrelated red line while the table reports
    which tree was dropped.

    THE TERMINAL AND THE RESEARCH-DIALECT ROWS ARE THE POINT. A helper that defaulted to excluding
    retired paths would pass every live row and still permit the measured `uyeko5` collision, and a
    helper reading only the `- Id:` bullet dialect would silently omit every research id.
    """

    #: (case, relative path, text, the id6 that must be collected, why this row exists)
    ARTIFACTS = (
        (
            "a live pending plan",
            f"{PLANS_PENDING}/20260101-demo-01-aaa111-a.ipd.md",
            _plan_text("aaa111"),
            "aaa111",
            "THE LIVE BASELINE. A set that missed this would be broken in the obvious direction and "
            "every other row would be moot",
        ),
        (
            "an EXECUTED plan",
            f"{PLANS_EXECUTED}/20260101-demo-01-bbb222-b.ipd.md",
            _plan_text("bbb222", status="executed"),
            "bbb222",
            "THE LOAD-BEARING ROW. `_iter_type_files` skips retired paths BY DEFAULT and `executed/` "
            "is retired, so a mint set built on that default would omit every executed plan's id6 - "
            "which is precisely the shape of the real `uyeko5` collision. A terminal id6 is cited "
            "forever, so re-minting it is a real defect",
        ),
        (
            "a DONE backlog item",
            f"{BACKLOG_DONE}/20260101-demo-01-ccc333-c.backlog.md",
            _backlog_text("ccc333", status="done"),
            "ccc333",
            "the same terminal claim for a SECOND tree with a different retirement spelling "
            "(`done/`), so the property is shown to be about retirement in general and not about one "
            "hard-coded directory name",
        ),
        (
            "a spec",
            f"{SPECS}/20260101-ddd444-01-ddd444-d.spec.md",
            _spec_text("ddd444"),
            "ddd444",
            "specs were a SEPARATE per-tree mint (`_existing_spec_ids`), so a spec id6 was invisible "
            "to every other tree's mint before this change",
        ),
        (
            "a live backlog item",
            f"{BACKLOG_OPEN}/20260101-demo-01-eee555-e.backlog.md",
            _backlog_text("eee555"),
            "eee555",
            "backlog was its own per-tree mint too, and it is the tree with the MOST mint sites "
            "(`backlog.run_new` plus `set_records`)",
        ),
        (
            "a RESEARCH record declaring a YAML `id:`",
            f"{RESEARCH}/20260101-demo-01-fff666-f.research-report.md",
            _research_text("fff666"),
            "fff666",
            "RESEARCH USES A DIFFERENT FRONT-MATTER DIALECT (YAML `id:`, not a `- Id:` bullet), so a "
            "set built from the bullet reader alone omits every research id. This is not hypothetical: "
            "every non-plan participant in the measured `uyeko5` collision is a research record, so "
            "research is the tree the defect most implicated",
        ),
    )

    def test_every_tree_and_disposition_is_collected(self):
        for case, rel, text, expected_id6, why in self.ARTIFACTS:
            with self.subTest(case=case):
                root = _tree([(rel, text)])
                got = core.global_id6s(root)
                self.assertIn(
                    expected_id6,
                    got,
                    f"{case}: id6 {expected_id6!r} is absent from the global mint set, so a fresh "
                    f"mint could duplicate it. WHY THIS ROW EXISTS: {why}. Collected: {sorted(got)}",
                )

    def test_a_missing_records_tree_yields_an_empty_set_rather_than_raising(self):
        """A mint must not be BLOCKED by an unscannable repository.

        Separate from the table because the claim is about the degenerate input, not about any tree.
        `mint_id6` unions the caller's own per-tree set in, so an empty global set degrades to exactly
        the per-tree check that existed before rather than to no check at all.
        """

        root = Path(tempfile.mkdtemp())
        self.assertEqual(
            core.global_id6s(root),
            set(),
            "a repository with no records tree must yield an empty set, not raise: minting has to "
            "keep working in a fresh or partially-initialized repository",
        )


class ForcedCollisionMintTests(unittest.TestCase):
    """A mint REFUSES a candidate already used by a DIFFERENT type, including a terminal one.

    ONE table over the cross-type pairs that matter. Each row plants an artifact of type A holding
    id6 X, then mints for type B with the rng PINNED to produce X first and a free id6 second, and
    asserts the mint returned the free one. The rows are one table because they are one property
    measured across the type pairs that were previously blind to each other.
    """

    #: (case, planted relative path, planted text, the taken id6, why this row exists)
    PAIRS = (
        (
            "a plan's id6 is refused when minting for another tree",
            f"{PLANS_PENDING}/20260101-demo-01-tak111-a.ipd.md",
            _plan_text("tak111"),
            "tak111",
            "the plans tree is the largest and the one most cited by other artifacts",
        ),
        (
            "an EXECUTED plan's id6 is refused",
            f"{PLANS_EXECUTED}/20260101-demo-01-tak222-b.ipd.md",
            _plan_text("tak222", status="executed"),
            "tak222",
            "THE MOTIVATING CASE, in the same shape as the real `uyeko5` instance: the other side of "
            "the collision sits in `executed/`. A mint set honoring the default liveness filter would "
            "hand out this id6 again",
        ),
        (
            "a DONE backlog item's id6 is refused",
            f"{BACKLOG_DONE}/20260101-demo-01-tak333-c.backlog.md",
            _backlog_text("tak333", status="done"),
            "tak333",
            "terminal in a second tree with a second retirement spelling",
        ),
        (
            "a spec's id6 is refused",
            f"{SPECS}/20260101-tak444-01-tak444-d.spec.md",
            _spec_text("tak444"),
            "tak444",
            "cross-tree between two trees that each had their own independent per-tree mint",
        ),
        (
            "a RESEARCH record's YAML id is refused",
            f"{RESEARCH}/20260101-demo-01-tak555-e.research-report.md",
            _research_text("tak555"),
            "tak555",
            "the dialect case again, now at MINT time rather than at collection time: a research id6 "
            "must be unmintable by a bullet-dialect tree",
        ),
    )

    def test_a_taken_id6_from_another_type_is_never_minted(self):
        free = "zzz999"
        for case, rel, text, taken, why in self.PAIRS:
            with self.subTest(case=case):
                root = _tree([(rel, text)])
                got = core.mint_id6(root, _rng=_rng_returning(taken, free))
                self.assertEqual(
                    got,
                    free,
                    f"{case}: the mint returned {got!r}. The rng offered the ALREADY-TAKEN id6 "
                    f"{taken!r} first and a free id6 {free!r} second, so returning {taken!r} proves "
                    f"the candidate was not checked against the other tree. WHY: {why}",
                )

    def test_the_callers_own_set_is_unioned_not_replaced(self):
        """`existing` must still be honored, because a caller may hold ids that are not on disk yet.

        Separate from the table because the claim is about the ARGUMENT rather than about the
        repository scan. `research_cmd` plans a whole comparison Set in one pass and adds each minted
        id6 to its own set as it goes, so an implementation that ignored `existing` in favor of the
        global scan would mint the same id6 twice inside one command.
        """

        root = _tree(
            [
                (
                    f"{PLANS_PENDING}/20260101-demo-01-aaa111-a.ipd.md",
                    _plan_text("aaa111"),
                )
            ]
        )
        got = core.mint_id6(root, {"inmem1"}, _rng=_rng_returning("inmem1", "zzz999"))
        self.assertEqual(
            got,
            "zzz999",
            "an id6 present only in the caller's in-memory `existing` set was minted anyway, so a "
            "multi-document command can produce two files with one id6",
        )


class PurityAndSubsetContractTests(unittest.TestCase):
    """The generator stays PURE, and the mint set is a documented conservative SUPERSET (E-07)."""

    def test_generate_id6_keeps_its_injectable_signature(self):
        """The property that makes every forced-collision test above possible.

        Stated as its own test because it is a claim about the API rather than about a tree: if
        `generate_id6` ever fetched its own set from the filesystem, none of the collisions above
        could be forced and this whole module would degrade into 36**6 wishful thinking.
        """

        import inspect

        params = list(inspect.signature(core.generate_id6).parameters)
        self.assertEqual(
            params,
            ["existing", "_rng"],
            "generate_id6 must keep taking the collision set as an ARGUMENT and keep its injectable "
            "_rng; the impure repository-wide fetch belongs in mint_id6",
        )

    def test_the_mint_set_over_collects_quoted_ids_and_that_is_deliberate(self):
        """E-07: the substrate's identity readers are UNBOUNDED, so the set is a SUPERSET.

        WHY THIS IS A TEST AND NOT ONLY A COMMENT. The over-collection is SAFE for minting (refusing
        one quoted candidate costs one draw out of 36**6 and the result is still collision-free) and
        WRONG for checking (treating a quotation as a declaration manufactures a false collision
        finding). A future reader who assumes the set is an EXACT census could "optimize" the mint
        path onto a checker's precise reader, or worse reuse this set to decide a collision EXISTS.
        This test pins the actual behavior so that change fails here, loudly, with the reason.

        Bounding those readers is owned by IPD `76w6mq`; this plan deliberately does not touch them.
        """

        quoted = "qut111"
        root = _tree(
            [
                (
                    f"{RESEARCH}/20260101-demo-01-own111-r.research-report.md",
                    "---\nid: own111\nkind: research-report\n---\n\n# Report\n\n"
                    "Here is an example of a plan's metadata block:\n\n"
                    f"```markdown\n- Id: {quoted}\n- Status: approved\n```\n",
                )
            ]
        )
        got = core.global_id6s(root)
        self.assertIn(
            "own111",
            got,
            "the document's OWN declared identity must be collected",
        )
        self.assertIn(
            quoted,
            got,
            "MEASURED BEHAVIOR, deliberately pinned: an id6 QUOTED inside a fenced code block is "
            "collected too, because the underlying identity readers are unbounded. That makes the set "
            "a conservative SUPERSET, which is correct for MINTING and wrong for CHECKING. If this "
            "assertion starts failing because a reader was bounded, the mint path is still correct "
            "(the set merely got tighter) - update this test and see IPD 76w6mq",
        )


if __name__ == "__main__":
    unittest.main()
