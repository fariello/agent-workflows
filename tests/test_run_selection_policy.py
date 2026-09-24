"""Tests for the mixed-type confirmation gate and the runner-facing selection policy.

IPD 6lu3rq E-05, covering spec `25kzda` 2.5. The gate is demonstrated in BOTH directions (a
one-sided test does not demonstrate a gate), the verbatim refusal is asserted against the spec's own
text rather than a paraphrase, and the classification is proven to DEFER to the shipped resolver
rather than duplicating it.

TWO KINDS OF TABLE LIVE HERE, and they are not interchangeable. Where the varying input is a SCALAR
and each case is genuinely independent, `@pytest.mark.parametrize` is right and is already used: the
20-case status->action dispatch table, its 8-case undeterminable counterpart, the 12-case
confirmation-phrase rejection table, the 3-case accepted-phrase table, and the `host` parameter that
runs the sweep property on BOTH runners. Those are not touched, and should not be: a parametrized
case is individually named and individually reported, which is what you want when the cases are
unrelated points in a large input space.

Where instead a CLUSTER OF ROWS is really one property observed under several input combinations, the
rows live in a module-level tuple and ONE test accumulates failures and reports them together. That
shape is used for `needs_review`'s four interacting inputs, `classify_paths`' selections, the
per-artifact disposition line, the public vocabulary strings, and the renderer conventions. The
difference is deliberate: in each of those the interesting information is WHICH COMBINATIONS moved
together (completeness only matters on `draft`; a terminal directory overrides an otherwise
review-worthy status; an untyped record raises the item count without making a selection mixed), and
N independently-reported failures actively hide that.

MODES ARE COLUMNS in the accumulating tables: `spec_type`, the three-valued `authoring_complete`, the
file's DIRECTORY, and the queue entry's shape all vary within one table rather than across several.

WHAT IS DELIBERATELY NOT TABULATED, so the next reader does not redo the analysis. Tests that read
the SPEC FILE and compare character-for-character stay apart (their subject is a document, not an
input). So do the purity/no-mutation proofs, the AST import guard, the `inspect.signature` guards on
what the predicates deliberately do NOT accept, and `test_membership_derives_from_the_action_table...`
plus `test_every_legal_edge_in_table_is_accepted`, which already iterate the product's own tables and
so extend themselves when a row is added - restating those as literal rows would freeze a copy that a
newly added status could not fail.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_workflows import run_selection_policy as pol
from agent_workflows import selectors as sel

# --------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------


def _item(spec_type: str, action: str, n: int = 1, tag: str = "") -> list:
    return [
        pol.ClassifiedItem(
            path=Path("/repo/{0}{1}{2}.md".format(spec_type, tag, i)),
            spec_type=spec_type,
            resolver_type=None,
            status=None,
            action=action,
        )
        for i in range(n)
    ]


def _classify(items: list) -> pol.Classification:
    """Build a Classification from hand-made items (no filesystem), mirroring classify_paths."""
    return pol.Classification(
        items=tuple(items),
        counts=pol._counts_for(items),
        untyped=tuple(i.path for i in items if i.spec_type is None),
    )


def _spec_example() -> pol.Classification:
    """Spec 2.5's own example selection: IPDs 4 (2 review, 2 execute), Specs 2 (1 review, 1 plan),
    Prompts 1 (1 execute)."""
    return _classify(
        _item("ipd", pol.ACTION_REVIEW, 2, "r")
        + _item("ipd", pol.ACTION_EXECUTE, 2, "x")
        + _item("spec", pol.ACTION_REVIEW, 1, "r")
        + _item("spec", pol.ACTION_PLAN, 1, "p")
        + _item("prompt", pol.ACTION_EXECUTE, 1)
    )


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A minimal records tree with one plan, one spec, and one backlog item, all sharing a selector
    so a single token genuinely spans three types."""
    (tmp_path / ".git").mkdir()
    recs = tmp_path / ".aw" / "records"
    _write(
        recs / "plans" / "pending" / "20260101-mixdemo-01-aaa111-demo.ipd.md",
        "# IPD: demo\n\n- Id: aaa111\n- Set: mixdemo\n- Status: approved\n",
    )
    _write(
        recs / "specs" / "20260101-bbb222-01-bbb222-demo.spec.md",
        "# Spec: demo\n\n- Id: bbb222\n- Set: mixdemo\n- Status: approved\n",
    )
    _write(
        recs / "backlog" / "20260101-ccc333-01-ccc333-demo.backlog.md",
        "# Backlog: demo\n\n- Id: ccc333\n- Set: mixdemo\n- Status: open\n",
    )
    return tmp_path


# --------------------------------------------------------------------------------------------------
# E-01: classification, and that it CONSUMES the shipped resolver
# --------------------------------------------------------------------------------------------------


def test_type_mapping_is_one_data_table_covering_the_resolver_vocabulary():
    # Every resolver type the shipped resolver knows has an explicit entry (a spec type, or an
    # explicit None), so a new type cannot be silently mistyped.
    assert set(pol.SPEC_TYPE_BY_RESOLVER_TYPE) == set(sel.KNOWN_PRIMARY_TYPES)
    # Spec 2.2's seven runnable types are exactly the non-None values.
    assert set(pol.RESOLVER_TYPE_BY_SPEC_TYPE) == set(pol.SPEC_TYPE_ORDER)
    assert len(pol.SPEC_TYPE_ORDER) == 7
    # comms/roadmaps have no spec 2.2 type.
    assert pol.SPEC_TYPE_BY_RESOLVER_TYPE["comms"] is None
    assert pol.SPEC_TYPE_BY_RESOLVER_TYPE["roadmaps"] is None
    # The mapping round-trips.
    for spec_type, resolver_type in pol.RESOLVER_TYPE_BY_SPEC_TYPE.items():
        assert pol.SPEC_TYPE_BY_RESOLVER_TYPE[resolver_type] == spec_type


#: (case, which seeded records to select, expected `spec_types`, expected `is_mixed`, expected item
#: count, expected untyped count, expected (spec_type, status, action) per item, why this row exists)
#:
#: ONE table replaces three tests (`single_type_selection_reports_exactly_one_type`,
#: `mixed_selection_counts_each_type`,
#: `untyped_files_are_reported_not_dropped_and_do_not_make_a_selection_mixed`) and folds in a fourth
#: (`reviewed_ipd_is_undetermined_end_to_end_through_classify_paths`). Every one of them called
#: `classify_paths` on one selection and asserted a few of the same fields.
#:
#: WHY THE TABLE BEATS THE FOUR. `is_mixed` is the input to the CONFIRMATION GATE, so what matters is
#: not any one selection but the BOUNDARY: which selections are mixed and which are not. That boundary
#: is subtle in exactly one place - an UNTYPED record raises the item count without making the
#: selection mixed, because an unrunnable record is not a KIND OF WORK - and seeing the one-type,
#: three-type and untyped rows together is the only way to state it. Separated, a change that made
#: untyped records count as a type would break one test and read as a bug in that test's fixture.
#:
#: THE ORDER OF `spec_types` IS PART OF THE CONTRACT and is asserted as a tuple, not a set: it is
#: `SPEC_TYPE_ORDER`, deliberately NOT input order, which is what makes the preview and the queue
#: digest stable across shuffled inputs.
#:
#: THE ACTION COLUMN carries this end to end. Three of the old tests stopped at the counts, so the
#: per-item action - the thing dispatch actually consumes - was only checked by a fourth test on one
#: status. Every row now pins it, which is strictly more coverage.
_CLASSIFICATIONS = (
    (
        "one approved plan",
        ("plan",),
        ("ipd",),
        False,
        1,
        0,
        (("ipd", "approved", pol.ACTION_EXECUTE),),
        "THE SINGLE-TYPE BASELINE: one type is never mixed, so the gate never applies. This is the "
        "row that would break if `is_mixed` were derived from the ITEM count rather than the TYPE "
        "count, which would gate every multi-item run and make the flag mandatory",
    ),
    (
        "one approved spec",
        ("spec",),
        ("spec",),
        False,
        1,
        0,
        (("spec", "approved", pol.ACTION_PLAN),),
        "the same claim for a DIFFERENT type, and its action differs: an approved spec routes to "
        "`plan`, not `execute`. Without this row the classifier could be plan-shaped and the table "
        "would still pass",
    ),
    (
        "one open backlog item",
        ("backlog",),
        ("backlog",),
        False,
        1,
        0,
        (("backlog", "open", pol.ACTION_PLAN),),
        "the third runnable type. `open` also routes to `plan`, which is what makes the pairing with "
        "the spec row meaningful: two different (type, status) inputs reaching the SAME action is "
        "real behavior, not a copy",
    ),
    (
        "all three types under one selector",
        ("plan", "spec", "backlog"),
        ("ipd", "spec", "backlog"),
        True,
        3,
        0,
        (
            ("ipd", "approved", pol.ACTION_EXECUTE),
            ("spec", "approved", pol.ACTION_PLAN),
            ("backlog", "open", pol.ACTION_PLAN),
        ),
        "THE MIXED ROW, and the one the gate exists for. `spec_types` is asserted as an ORDERED "
        "tuple in `SPEC_TYPE_ORDER` rather than input order, which is the property the stable "
        "preview and the order-independent queue digest are built on",
    ),
    (
        "a plan plus an UNTYPED comms record",
        ("plan", "comm"),
        ("ipd",),
        False,
        2,
        1,
        (
            ("ipd", "approved", pol.ACTION_EXECUTE),
            (None, None, pol.ACTION_SKIP),
        ),
        "THE SUBTLE BOUNDARY, and the reason these rows must sit together: the untyped record IS "
        "REPORTED (two items, one untyped) and is NOT silently dropped, yet the selection is NOT "
        "mixed - an unrunnable record is not a KIND OF WORK, so it must not trigger a confirmation "
        "prompt. Its action is `skip`, which is how it reaches the preview without reaching dispatch",
    ),
    (
        "ONLY an untyped comms record",
        ("comm",),
        (),
        False,
        1,
        1,
        ((None, None, pol.ACTION_SKIP),),
        "the degenerate case of the row above: NO typed work at all. `spec_types` must be empty and "
        "the selection still not mixed, so a selection of nothing-runnable neither gates nor "
        "pretends to have found work",
    ),
    (
        "a REVIEWED plan, classified end to end",
        ("reviewed-plan",),
        ("ipd",),
        False,
        1,
        0,
        (("ipd", "reviewed", pol.ACTION_UNDETERMINED),),
        "THE END-TO-END UNDETERMINED ROW: `reviewed` branches on `--full-auto`, a flag the classifier "
        "cannot see, so it must reach `classify_paths`' output as UNDETERMINED rather than being "
        "guessed into a real action. Proven through the FILE-READING path, not by calling "
        "`_action_for` directly, so the status is parsed out of a real record",
    ),
)


def test_every_selection_classifies_to_the_types_and_actions_it_should(repo: Path):
    available = {
        "plan": next((repo / ".aw" / "records" / "plans").rglob("*-demo.ipd.md")),
        "spec": next((repo / ".aw" / "records" / "specs").rglob("*.spec.md")),
        "backlog": next((repo / ".aw" / "records" / "backlog").rglob("*.backlog.md")),
        "comm": _write(
            repo / ".aw" / "records" / "comms" / "shared" / "note.md",
            "# note\n\n- Id: ddd444\n",
        ),
        "reviewed-plan": _write(
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260101-mixdemo-03-eee555-rev.ipd.md",
            "# IPD: rev\n\n- Id: eee555\n- Set: mixdemo\n- Status: reviewed\n",
        ),
    }
    wrong = []
    single_type_rows_broken = 0
    for (
        case,
        keys,
        expect_types,
        expect_mixed,
        expect_items,
        expect_untyped,
        expect_triples,
        why,
    ) in _CLASSIFICATIONS:
        c = pol.classify_paths(repo, [available[k] for k in keys])
        problems = []
        if c.spec_types != expect_types:
            problems.append(
                "spec_types is {0!r}, expected {1!r} (SPEC_TYPE_ORDER, not input order)".format(
                    c.spec_types, expect_types
                )
            )
        if c.type_count != len(expect_types):
            problems.append(
                "type_count is {0!r}, expected {1!r}".format(
                    c.type_count, len(expect_types)
                )
            )
        if c.is_mixed is not expect_mixed:
            problems.append(
                "is_mixed is {0!r}, expected {1!r}; this is the CONFIRMATION GATE's input, so a "
                "wrong value either prompts for a single-type run or lets a mixed one through "
                "unconfirmed".format(c.is_mixed, expect_mixed)
            )
            if not expect_mixed:
                single_type_rows_broken += 1
        if len(c.items) != expect_items:
            problems.append(
                "{0} item(s) reported, expected {1}; an item silently DROPPED is worse than one "
                "misclassified, because nothing downstream can see it went missing".format(
                    len(c.items), expect_items
                )
            )
        if len(c.untyped) != expect_untyped:
            problems.append(
                "{0} untyped path(s) reported, expected {1}".format(
                    len(c.untyped), expect_untyped
                )
            )
        got_triples = tuple((i.spec_type, i.status, i.action) for i in c.items)
        if got_triples != expect_triples:
            problems.append(
                "the per-item (type, status, action) triples are {0!r}, expected {1!r}".format(
                    got_triples, expect_triples
                )
            )
        counts = {tc.spec_type: tc.total for tc in c.counts}
        expected_counts = {t: expect_types.count(t) for t in expect_types}
        if counts != expected_counts:
            problems.append(
                "the per-type counts are {0!r}, expected {1!r}".format(
                    counts, expected_counts
                )
            )
        if problems:
            wrong.append(
                "  {0}\n    selected: {1!r}\n".format(case, keys)
                + "".join("    - {0}\n".format(p) for p in problems)
                + "    this row exists because: {0}".format(why)
            )
    extra = ""
    if single_type_rows_broken:
        extra = (
            " {0} row(s) that must NOT be mixed are among the failures, which is the direction that "
            "costs an operator a prompt on every ordinary single-type run.".format(
                single_type_rows_broken
            )
        )
    assert not wrong, (
        "classify_paths answered wrongly for {0} of {1} selections.{2} `is_mixed` is the input to "
        "the confirmation gate, so read the grouping: the UNTYPED rows failing on `is_mixed` means "
        "an unrunnable record is now counted as a kind of work, so a comms note beside a plan would "
        "demand a confirmation phrase; the MIXED row failing alone means the type count collapsed; a "
        "wrong `spec_types` ORDER breaks the stable preview and the order-independent queue digest "
        "even when the membership is right. FIX: a row reporting too FEW items is the severe case - "
        "a dropped path is invisible downstream, whereas a misclassified one at least appears.\n"
        "{3}".format(len(wrong), len(_CLASSIFICATIONS), extra, "\n".join(wrong))
    )


def test_resolution_defers_to_selectors_resolve(repo: Path, monkeypatch):
    """The policy must CALL selectors.resolve rather than reimplementing precedence/ambiguity."""
    calls = []
    real = sel.resolve

    def spy(repo_root, record_type, selector, **kw):
        calls.append((record_type, selector))
        return real(repo_root, record_type, selector, **kw)

    monkeypatch.setattr(pol._sel, "resolve", spy)
    c, errors = pol.resolve_selection(
        repo, "mixdemo", spec_types=("ipd", "spec", "backlog")
    )
    assert errors == ()
    # One delegation per type; the policy contributed no matching logic of its own.
    assert calls == [("plans", "mixdemo"), ("specs", "mixdemo"), ("backlog", "mixdemo")]
    assert c.spec_types == ("ipd", "spec", "backlog")
    assert c.is_mixed is True


def test_unique_kind_collision_is_reported_using_the_shipped_policy(repo: Path):
    """spec 2.3 step 4: an id6 matching several files is corruption, not a multi-item selection.
    The policy applies selectors' own UNIQUE_KINDS rather than a second ambiguity policy."""
    _write(
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20260101-mixdemo-02-aaa111-dupe.ipd.md",
        "# IPD: dupe\n\n- Id: aaa111\n- Set: mixdemo\n- Status: approved\n",
    )
    c, errors = pol.resolve_selection(repo, "aaa111", spec_types=("ipd",))
    assert errors and "collision" in errors[0]
    assert c.items == ()


def test_the_untyped_path_itself_is_named_in_untyped(repo: Path):
    """Kept separate: identity of the PATH OBJECT, which the classification table cannot assert.

    That table counts untyped paths, because a count is what its uniform shape can express. This
    asserts the specific path is the one reported, so `untyped` names WHICH record could not be typed
    rather than merely how many. Without it, a classifier that reported the wrong path would satisfy
    every count in the table.
    """
    comm = _write(
        repo / ".aw" / "records" / "comms" / "shared" / "note.md",
        "# note\n\n- Id: ddd444\n",
    )
    plan = next((repo / ".aw" / "records" / "plans").rglob("*-demo.ipd.md"))
    c = pol.classify_paths(repo, [plan, comm])
    assert comm in c.untyped


# --------------------------------------------------------------------------------------------------
# E-02: the action preview
# --------------------------------------------------------------------------------------------------


def test_preview_matches_spec_2_5_example_exactly():
    expected = (
        "Mixed work-item selection:\n"
        "  IPDs:    4 (2 review, 2 execute)\n"
        "  Specs:   2 (1 review, 1 plan)\n"
        "  Prompts: 1 (1 execute)"
    )
    assert pol.render_action_preview(_spec_example()) == expected


def test_preview_is_stable_across_runs_and_input_order():
    a = _spec_example()
    shuffled = list(a.items)[::-1]
    b = _classify(shuffled)
    assert pol.render_action_preview(a) == pol.render_action_preview(b)
    assert pol.render_action_preview(a) == pol.render_action_preview(a)
    assert pol.queue_digest(a) == pol.queue_digest(b)  # digest is order-independent


@pytest.mark.parametrize(
    "spec_type,status,expected",
    [
        ("ipd", "approved", pol.ACTION_EXECUTE),
        ("ipd", "auto-approved", pol.ACTION_EXECUTE),
        ("ipd", "reusable", pol.ACTION_EXECUTE),
        ("ipd", "to-review", pol.ACTION_REVIEW),
        ("ipd", "executed", pol.ACTION_SKIP),
        ("ipd", "superseded", pol.ACTION_SKIP),
        ("ipd", "not-executed", pol.ACTION_SKIP),
        ("spec", "to-review", pol.ACTION_REVIEW),
        ("spec", "approved", pol.ACTION_PLAN),
        ("spec", "implemented", pol.ACTION_SKIP),
        ("spec", "deferred", pol.ACTION_SKIP),
        ("backlog", "open", pol.ACTION_PLAN),
        ("backlog", "blocked", pol.ACTION_SKIP),
        ("backlog", "graduated", pol.ACTION_SKIP),
        ("backlog", "done", pol.ACTION_SKIP),
        ("prompt", None, pol.ACTION_EXECUTE),
        ("prompt", "executed", pol.ACTION_SKIP),
        (
            "research",
            "active",
            pol.ACTION_SKIP,
        ),  # spec 3.6 gray skip, from the type alone
        ("release", "planned", pol.ACTION_SKIP),
        ("walkthrough", None, pol.ACTION_SKIP),
    ],
)
def test_action_derives_from_status_per_spec_dispatch_tables(
    spec_type, status, expected
):
    assert pol._action_for(spec_type, status) == expected


@pytest.mark.parametrize(
    "spec_type,status",
    [
        (
            "ipd",
            "draft",
        ),  # spec 3.2 splits draft on a completeness check (content, not status)
        (
            "ipd",
            "reviewed",
        ),  # spec 3.2 dispatches reviewed on --full-auto (a flag we cannot see)
        ("ipd", None),
        ("ipd", "banana"),  # unknown status: spec 3.2 red-aborts; we must not guess
        ("spec", "draft"),
        ("spec", "reviewed"),
        ("spec", "implementing"),
        ("backlog", "wat"),
    ],
)
def test_undeterminable_action_is_reported_not_bucketed(spec_type, status):
    assert pol._action_for(spec_type, status) == pol.ACTION_UNDETERMINED


def test_undetermined_appears_in_the_preview_rather_than_silently_counting_as_an_action():
    c = _classify(
        _item("ipd", pol.ACTION_EXECUTE, 1, "x")
        + _item("ipd", pol.ACTION_UNDETERMINED, 2, "u")
    )
    preview = pol.render_action_preview(c)
    assert "1 execute" in preview and "2 undetermined" in preview
    assert pol.ACTION_UNDETERMINED not in {
        pol.ACTION_REVIEW,
        pol.ACTION_PLAN,
        pol.ACTION_EXECUTE,
    }


# --------------------------------------------------------------------------------------------------
# E-03: the decision predicate
# --------------------------------------------------------------------------------------------------


def test_single_type_selection_is_never_gated():
    c = _classify(_item("ipd", pol.ACTION_EXECUTE, 3))
    for interactive in (True, False):
        v = pol.decide(c, interactive=interactive)
        assert v.proceed is True
        assert v.gate_applied is False  # ungated, not "passed"
        assert v.code is None and v.message is None


def test_unattended_mixed_is_refused_without_the_flag_and_proceeds_with_it():
    """Both directions on the SAME selection, differing only in the flag (the falsifiable pair)."""
    c = _spec_example()
    refused = pol.decide(c, interactive=False, allow_mixed=False)
    allowed = pol.decide(c, interactive=False, allow_mixed=True)
    assert refused.proceed is False
    assert refused.code == pol.RUN_MIXED_TYPES
    assert allowed.proceed is True
    assert allowed.code is None and allowed.message is None
    assert allowed.record.response_or_flag == "--allow-mixed"


@pytest.mark.parametrize("response", ["run mixed", "  run mixed  ", "run mixed\n"])
def test_interactive_accepts_exactly_the_spec_phrase(response):
    v = pol.decide(_spec_example(), interactive=True, response=response)
    assert v.proceed is True
    assert v.gate_applied is True


@pytest.mark.parametrize(
    "response",
    [
        "y",  # spec 2.5 rejects `y` explicitly
        "",  # spec 2.5 rejects an empty response explicitly
        None,  # no answer at all
        "yes",  # a generic confirmation
        "Y",
        "YES",
        "ok",
        "Run Mixed",  # case is not folded
        "run",
        "run mixed types",
        "runmixed",
        "run  mixed",  # internal whitespace is not normalized
    ],
)
def test_interactive_rejects_near_misses_and_generic_confirmations(response):
    v = pol.decide(_spec_example(), interactive=True, response=response)
    assert v.proceed is False
    assert v.code == pol.RUN_MIXED_TYPES


def test_no_branch_requires_a_tty():
    """Every branch is reachable as a pure call: no TTY, no host, no filesystem, no ledger."""
    c = _spec_example()
    verdicts = [
        pol.decide(_classify(_item("ipd", pol.ACTION_EXECUTE, 1)), interactive=False),
        pol.decide(c, interactive=False, allow_mixed=False),
        pol.decide(c, interactive=False, allow_mixed=True),
        pol.decide(c, interactive=True, response="run mixed"),
        pol.decide(c, interactive=True, response="y"),
    ]
    assert [v.proceed for v in verdicts] == [True, False, True, True, False]


def test_allow_mixed_waives_only_type_mixing():
    """spec 2.5 third bullet: the flag acknowledges type mixing ONLY. This predicate must never be a
    place another gate can be waived, so its waiver set is exhaustive and singular."""
    assert pol.Verdict.WAIVES == ("type-mixing",)
    # The predicate's ONLY override parameter is allow_mixed; there is no approval/scope/safety knob.
    import inspect

    params = set(inspect.signature(pol.decide).parameters)
    assert params == {
        "classification",
        "interactive",
        "allow_mixed",
        "response",
        "host",
        "selector",
    }
    for forbidden in (
        "allow_unapproved",
        "skip_gates",
        "force",
        "allow_unverifiable",
        "no_verify",
    ):
        assert forbidden not in params
    # The flag does not alter the previewed actions: what dispatch would do is unchanged.
    c = _spec_example()
    assert pol.decide(
        c, interactive=False, allow_mixed=True
    ).record.action_preview == pol.render_action_preview(c)


def test_verdict_carries_all_four_spec_2_5_bullet_4_facts():
    c = _spec_example()
    for v in (
        pol.decide(c, interactive=False, allow_mixed=True),
        pol.decide(c, interactive=True, response="run mixed"),
        pol.decide(c, interactive=False),
    ):
        rec = v.record
        assert rec.type_counts == {
            "ipd": 4,
            "spec": 2,
            "prompt": 1,
        }  # 1: confirmed type counts
        assert rec.action_preview == pol.render_action_preview(c)  # 2: action preview
        assert len(rec.queue_digest) == 64  # 4: queue digest (sha256)
        assert set(rec.as_dict()) == {
            "type_counts",
            "action_preview",
            "response_or_flag",
            "queue_digest",
        }
    # 3: the response OR the flag actually used, distinguishably.
    assert pol.decide(
        c, interactive=False, allow_mixed=True
    ).record.response_or_flag == ("--allow-mixed")
    assert (
        pol.decide(c, interactive=True, response="run mixed").record.response_or_flag
        == "run mixed"
    )
    assert pol.decide(c, interactive=False).record.response_or_flag is None


def test_queue_digest_changes_with_the_queue():
    a = _spec_example()
    b = _classify(list(a.items) + _item("ipd", pol.ACTION_EXECUTE, 1, "extra"))
    assert pol.queue_digest(a) != pol.queue_digest(b)


# --------------------------------------------------------------------------------------------------
# E-04: the verbatim refusal
# --------------------------------------------------------------------------------------------------


#: (constant name, the constant, its exact required value, why this row exists) - ONE table replacing
#: two tests (`finding_code_string_is_exactly_run_mixed_types`,
#: `confirm_phrase_constant_is_the_spec_phrase`) and pinning the two phrases beside them.
#:
#: WHY THE TABLE BEATS THE TWO. These four strings are a PUBLIC VOCABULARY fixed by spec `25kzda`:
#: the finding codes appear in refusal output that operators grep and agents match on, and the
#: confirmation phrases are what a human must type EXACTLY. Nothing in the code will break if one is
#: reworded - the gate still gates, the refusal still refuses - so a drifted constant is silent, and
#: for the phrases it is silent in the worst direction: an operator who types the documented phrase is
#: refused, with the run reporting that they declined.
#:
#: THE VALUES ARE LITERAL STRINGS, NOT REFERENCES, AND THAT IS DELIBERATE. Asserting
#: `pol.CONFIRM_PHRASE == pol.CONFIRM_PHRASE` is vacuous, and that is exactly what a
#: constant-referencing version of this table would be. The literals are transcribed from the spec.
_PUBLIC_VOCABULARY = (
    (
        "RUN_MIXED_TYPES",
        pol.RUN_MIXED_TYPES,
        "RUN-MIXED-TYPES",
        "the finding code the mixed-type refusal is reported under. It is printed in the refusal, "
        "recorded in the ledger, and matched by agents, so renaming it breaks every consumer while "
        "the gate itself keeps working - a silent break",
    ),
    (
        "RUN_DRAFTS_EXCLUDED",
        pol.RUN_DRAFTS_EXCLUDED,
        "RUN-DRAFTS-EXCLUDED",
        "the second finding code, and the pairing matters: the two gates have DIFFERENT codes "
        "because their outcomes differ (a mixed selection refuses the run, an ungated draft is merely "
        "excluded while the run proceeds). One code for both would tell a consumer the wrong thing "
        "happened",
    ),
    (
        "CONFIRM_PHRASE",
        pol.CONFIRM_PHRASE,
        "run mixed",
        "THE PHRASE A HUMAN MUST TYPE EXACTLY. This is the row whose drift is worst: the phrase is "
        "documented and printed, so changing it means an operator typing the documented words is "
        "refused and the run reports that they declined - a wrong answer to a question they answered "
        "correctly",
    ),
    (
        "DRAFTS_CONFIRM_PHRASE",
        pol.DRAFTS_CONFIRM_PHRASE,
        "run drafts",
        "the draft gate's phrase, which must be DISTINCT from the mixed gate's: spec 2.5a bullet 5 "
        "has both gates collected in one interaction, so a shared phrase would let one answer waive "
        "both - which is precisely what `test_the_combined_case...` proves it does not",
    ),
)


def test_every_public_vocabulary_string_is_exactly_the_spec_text():
    wrong = []
    for name, actual, expected, why in _PUBLIC_VOCABULARY:
        if actual != expected:
            wrong.append(
                "  {0}\n    - expected {1!r}, got {2!r}\n"
                "    this row exists because: {3}".format(name, expected, actual, why)
            )
    assert not wrong, (
        "{0} of {1} public vocabulary strings have drifted from spec `25kzda`. NOTHING IN THE CODE "
        "BREAKS WHEN ONE OF THESE MOVES, which is why they are pinned: the gate still gates and the "
        "refusal still refuses, so the damage is entirely to consumers. Read the grouping: both "
        "FINDING CODES moving together means a renaming pass, and every agent matching on them stops "
        "matching; a CONFIRM PHRASE moving is the severe case, because an operator typing the "
        "documented words is then refused and the run records that they declined. FIX: these are "
        "literal strings ON PURPOSE - do not 'tidy' them into references to the constants they check, "
        "which would make the assertions vacuous.\n{2}".format(
            len(wrong), len(_PUBLIC_VOCABULARY), "\n".join(wrong)
        )
    )


def test_refusal_template_is_character_identical_to_the_spec():
    """Asserted against spec 25kzda 2.5's exact refusal block. Rewording the message FAILS this."""
    spec_exact = (
        "[RUN-MIXED-TYPES] Selection contains <counts>. No work started. Review the selection, "
        "then run: aw <host> run <selector> --type <type> ... --allow-mixed"
    )
    assert pol.REFUSAL_TEMPLATE == spec_exact
    # With placeholders left literal, a rendered refusal differs from the spec ONLY at <counts>.
    rendered = pol.render_refusal(_spec_example())
    assert rendered == spec_exact.replace("<counts>", "IPDs: 4, Specs: 2, Prompts: 1")
    # The load-bearing clauses survive substitution.
    assert rendered.startswith("[RUN-MIXED-TYPES] Selection contains ")
    assert "No work started." in rendered
    assert rendered.endswith("--type <type> ... --allow-mixed")


def test_refusal_message_names_the_counts_and_the_recovery_command():
    v = pol.decide(_spec_example(), interactive=False, host="oc", selector="mixdemo")
    assert v.message is not None
    assert "IPDs: 4, Specs: 2, Prompts: 1" in v.message
    assert "aw oc run mixdemo --type <type> ... --allow-mixed" in v.message


def test_the_matcher_defaults_to_the_mixed_phrase_and_rejects_a_reflex_answer():
    """Kept separate: the MATCHER's default-argument behavior, not a constant's value.

    The vocabulary table pins what `CONFIRM_PHRASE` IS. This pins that
    `is_confirmation_accepted` uses it when called with no `phrase=`, which is a different claim: a
    matcher whose default drifted to something else would leave every constant above correct while
    accepting the wrong word at the prompt.
    """
    assert pol.is_confirmation_accepted("run mixed") is True
    assert pol.is_confirmation_accepted("y") is False


def test_refusal_path_starts_nothing_and_writes_nothing(repo: Path, monkeypatch):
    """The `No work started.` clause is a BEHAVIORAL guarantee. Prove the refusal path performs no
    mutation: no subprocess (no host session), and a byte-identical records tree afterwards."""
    import subprocess

    def boom(*a, **k):  # pragma: no cover - must never run
        raise AssertionError("refusal path spawned a process")

    monkeypatch.setattr(subprocess, "Popen", boom)
    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(subprocess, "check_output", boom)

    def snapshot():
        return {
            str(p.relative_to(repo)): p.read_bytes()
            for p in sorted(repo.rglob("*"))
            if p.is_file()
        }

    before = snapshot()
    c, _ = pol.resolve_selection(repo, "mixdemo", spec_types=("ipd", "spec", "backlog"))
    assert c.is_mixed is True
    v = pol.decide(c, interactive=False, allow_mixed=False)
    assert v.proceed is False and v.code == pol.RUN_MIXED_TYPES
    assert snapshot() == before  # nothing created, deleted, or modified


def test_gate_is_pure_and_leaves_no_module_state():
    """A second identical decision returns an identical verdict (no caching, no accumulation)."""
    c = _spec_example()
    first = pol.decide(c, interactive=False)
    second = pol.decide(c, interactive=False)
    assert first == second


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-01: THE DIVERGENCE PROPERTY - sweep membership == dispatch-table routing
# --------------------------------------------------------------------------------------------------
#
# THIS IS THE LOAD-BEARING TEST OF THAT PLAN, and it is worth more than the refactor it guards. Spec
# `25kzda` 2.4a property 2 makes the rule normative: an item is in `reviews` IF AND ONLY IF the Section
# 3 dispatch table gives it a review action at its current status, implemented ONCE. Before `6ypimw`
# the two disagreed and the disagreement was INVISIBLE: each runner's `expand_selectors` carried its
# own closure testing `status == "to-review"` while `determine_action` routed `to-review` AND `draft`
# to `review`, so a complete draft named EXPLICITLY was reviewed while the SAME draft was silently
# absent from the sweep.
#
# DRIVEN FROM THE ROUTING, NEVER FROM A HAND-WRITTEN STATUS LIST. A test enumerating the statuses it
# expects has to be edited whenever a status is added, and whoever edits it will edit it to match
# whatever the code then does - which is how the original divergence survived review. Asking the
# ROUTER what it routes makes a future status addition FAIL here until the predicate agrees.
#
# BOTH HOSTS, because the deleted closure was duplicated verbatim in both: a property proven on one
# runner would have left `aw agy run reviews` free to diverge again.

_HOSTS = ("oc", "agy")

#: A COMPLETE plan body (no anchored scaffold placeholder), parameterized by id6 and status. Complete
#: on purpose: spec 2.5a splits a draft on authoring completeness, and this property is about what the
#: table routes, so the completeness variable is held at "complete" here and varied in its own test.
_COMPLETE_PLAN = """\
# IPD: sweep property fixture

- Date: 2026-09-05
- Kind: child
- Concern: a real concern sentence, so no anchored placeholder remains.
- Scope: a real scope sentence.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: {status}
- Set: s1
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history

- 2026-09-05 draft (test): created.

## Goal

A real goal sentence for the fixture.

## Detailed Implementation Checklist (TODO)

### Task group 1: fixture

- [ ] E-01 Do one observable thing.
  - Depends on: none
  - Expected outcome: the observable thing happened.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: the observable thing, pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: small
- Cohesion rationale: one concern.

Real gate prose: commit path-scoped, never push.
"""


def _host_module(host: str):
    from agent_workflows import agy_runipd, oc_runipd

    return {"oc": oc_runipd, "agy": agy_runipd}[host]


def _sweep_members(driver, plans_by_id: dict, repo: Path) -> set:
    """The ids `driver.expand_selectors` sweeps for `reviews`, as a set (empty when none)."""
    manifest = {
        "schema_version": 1,
        "plans": plans_by_id,
        "sets": {"s1": {"order": sorted(plans_by_id)}},
    }
    try:
        return set(driver.expand_selectors(manifest, ["reviews"], repo=repo))
    except driver.EmptyStatusSelection:
        return set()


@pytest.mark.parametrize("host", _HOSTS)
def test_sweep_membership_equals_dispatch_routing_for_every_status(
    host: str, tmp_path: Path
):
    """E-01, spec 2.4a property 2. FAILS AT PRE-CHANGE HEAD ON THE `draft` CASE, for both hosts."""
    from agent_workflows import plans as _plans

    driver = _host_module(host)
    plans_by_id: dict = {}
    routed_to_review: set = set()
    for n, status in enumerate(sorted(_plans.RECOGNIZED), start=1):
        id6 = "st{0:04d}".format(n)
        bucket = "pending"
        if status in ("executed", "superseded", "not-executed", "reusable"):
            # A terminal STATUS lives in its terminal DIRECTORY; putting it under pending/ would test
            # a directory/status mismatch, which spec 3.2 makes a red abort rather than a review.
            bucket = status
        rel = ".aw/records/plans/{0}/20260101-s1-{1:02d}-{2}-x.ipd.md".format(
            bucket, n, id6
        )
        _write(tmp_path / rel, _COMPLETE_PLAN.format(id6=id6, status=status, order=n))
        plans_by_id[id6] = {
            "set": "s1",
            "file": rel,
            "status": status,
            "order": n,
            "dependencies": [],
        }
        if driver.determine_action(status) == "review" and bucket == "pending":
            routed_to_review.add(id6)

    swept = _sweep_members(driver, plans_by_id, tmp_path)
    # Report by STATUS, not by id6: a failure that says `st0003` sends the reader to a fixture loop to
    # decode it, while one that says `draft` names the defect.
    status_of = {id6: info["status"] for id6, info in plans_by_id.items()}
    assert swept == routed_to_review, (
        "spec 25kzda 2.4a property 2 violated on host {0!r}: the `reviews` sweep and the dispatch "
        "table disagree. swept-but-not-routed={1}, ROUTED-BUT-NOT-SWEPT={2}".format(
            host,
            sorted(status_of[i] for i in swept - routed_to_review),
            sorted(status_of[i] for i in routed_to_review - swept),
        )
    )


@pytest.mark.parametrize("host", _HOSTS)
def test_a_complete_draft_is_swept_and_an_incomplete_one_is_not(
    host: str, tmp_path: Path
):
    """The draft split spec 2.5a/3.2 requires, at the SWEEP, on both hosts.

    The incomplete fixture is a real `aw ipd scaffold` body, so completeness is decided by the shipped
    anchored check and not by a heuristic invented for the test.
    """
    from agent_workflows import ipd_authoring

    driver = _host_module(host)
    stub_text = ipd_authoring.build_skeleton(
        kind="child",
        title="stub",
        author="test",
        when="2026-09-05",
        set_name="s1",
        order=2,
        plan_id="dr0002",
    )
    assert ipd_authoring.authoring_placeholders_resolved(stub_text) is False
    assert (
        ipd_authoring.authoring_placeholders_resolved(
            _COMPLETE_PLAN.format(id6="dr0001", status="draft", order=1)
        )
        is True
    )

    complete_rel = ".aw/records/plans/pending/20260101-s1-01-dr0001-complete.ipd.md"
    stub_rel = ".aw/records/plans/pending/20260101-s1-02-dr0002-stub.ipd.md"
    _write(
        tmp_path / complete_rel,
        _COMPLETE_PLAN.format(id6="dr0001", status="draft", order=1),
    )
    _write(tmp_path / stub_rel, stub_text)
    plans_by_id = {
        "dr0001": {
            "set": "s1",
            "file": complete_rel,
            "status": "draft",
            "order": 1,
            "dependencies": [],
        },
        "dr0002": {
            "set": "s1",
            "file": stub_rel,
            "status": "draft",
            "order": 2,
            "dependencies": [],
        },
    }
    assert _sweep_members(driver, plans_by_id, tmp_path) == {"dr0001"}


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-02: the ONE predicate, and what it deliberately does NOT decide
# --------------------------------------------------------------------------------------------------


def test_membership_derives_from_the_action_table_not_a_status_comparison():
    """Already property-driven over the product's own tables, so kept as it is.

    Spec 2.4a property 2: `ACTION_REVIEW` is the single source of truth. Asserted as a PROPERTY over
    the tables rather than by re-listing statuses: for every row the table actually carries, the
    predicate agrees with `_action_for`. A corrected copy of the old `status == "to-review"`
    comparison would pass a to-review test and fail this one. Restating those rows as literal data
    would freeze a copy that a newly added status could not fail.
    """
    for spec_type, table in pol._ACTION_TABLES.items():
        for status, action in table.items():
            assert pol.needs_review(spec_type, status) is (
                action == pol.ACTION_REVIEW
            ), "{0}/{1} disagrees with the table".format(spec_type, status)


#: (case, spec_type, status, authoring_complete, file_path, expected `needs_review`, why this row
#: exists) - ONE table replacing four tests (`undetermined_is_not_treated_as_needs_review`,
#: `only_the_draft_row_consults_completeness`, `the_terminal_directory_exclusion_survives`,
#: `the_predicate_answers_for_a_spec_handed_to_it_directly`). Every one of them called
#: `needs_review` with a different combination of the same four inputs and asserted a bool.
#:
#: WHY THE TABLE BEATS THE FOUR. `needs_review` is the ONE predicate `reviews`-sweep membership is
#: derived from (spec 2.4a property 2), and the divergence `6ypimw` fixed was invisible precisely
#: because its inputs were tested in separate places: each host's `expand_selectors` carried its own
#: `status == "to-review"` closure while `determine_action` routed `to-review` AND `draft` to review,
#: so a complete draft named explicitly was reviewed while the same draft was silently absent from
#: the sweep. The four inputs INTERACT - completeness only matters on `draft`, and a terminal
#: DIRECTORY overrides an otherwise review-worthy status - so the cells worth seeing are the
#: combinations, which four separate tests cannot lay side by side.
#:
#: THE INPUTS ARE COLUMNS, NOT SEPARATE TABLES: `spec_type` (ipd and spec, since E-05 made the
#: signature type-aware), `authoring_complete` (True / False / None-not-supplied, three-valued on
#: purpose) and `file_path` (a terminal directory or a live one) all vary within one table.
#:
#: POSITIVE ROWS ARE IN THE SAME TABLE. A predicate returning False unconditionally would satisfy
#: every exclusion row here, so the rows that must answer True are what keep them honest.
_NEEDS_REVIEW_CELLS = (
    (
        "a to-review IPD in pending",
        "ipd",
        "to-review",
        None,
        None,
        True,
        "THE POSITIVE BASELINE: the plainest review-worthy case there is. Every False row below is "
        "VACUOUS while this is broken, because a predicate that answered False unconditionally "
        "would satisfy all of them - and it would also empty the `reviews` sweep entirely",
    ),
    (
        "a COMPLETE draft IPD, completeness supplied as True",
        "ipd",
        "draft",
        True,
        None,
        True,
        "THE ROW THE `6ypimw` DIVERGENCE WAS ABOUT: `determine_action` routes a complete draft to "
        'review, so sweep membership must include it. The deleted `status == "to-review"` closures '
        "excluded exactly this, which is why a draft named EXPLICITLY got reviewed while the same "
        "draft was missing from the sweep",
    ),
    (
        "an INCOMPLETE draft IPD, completeness supplied as False",
        "ipd",
        "draft",
        False,
        None,
        False,
        "spec 2.5a splits `draft` on authoring completeness: a scaffold stub has nothing to review "
        "yet. Paired with the row above, this is what makes completeness a real input rather than a "
        "parameter the predicate ignores",
    ),
    (
        "a draft IPD with completeness NOT SUPPLIED",
        "ipd",
        "draft",
        None,
        None,
        False,
        "THREE-VALUED ON PURPOSE: `None` means the caller could not determine completeness, and the "
        "answer must be False rather than defaulting to the optimistic True. A caller that cannot "
        "tell a stub from a finished plan must not sweep either into review",
    ),
    (
        "a REVIEWED IPD, with completeness supplied as True",
        "ipd",
        "reviewed",
        True,
        None,
        False,
        "`reviewed` means the review ALREADY HAPPENED; spec 3.2 dispatches it on `--full-auto`, a "
        "flag this predicate cannot see. Completeness is supplied here deliberately: only the "
        "`draft` row may consult it, so a predicate consulting it generally would wrongly answer "
        "True and re-review every past-review plan on every sweep",
    ),
    (
        "an IPD with a status nothing recognizes",
        "ipd",
        "no-such-status",
        True,
        None,
        False,
        "an unknown status is UNDETERMINED, and spec 3.2 makes it a red abort rather than a review. "
        "Guessing review here would run a session against a plan whose state nothing could read",
    ),
    (
        "a to-review SPEC handed to the predicate directly",
        "spec",
        "to-review",
        None,
        None,
        True,
        "E-05's TYPE COLUMN: the signature takes a type and consults `_ACTION_TABLES`, which carries "
        "`spec`. Without a spec row the predicate could be IPD-hardcoded and every IPD row here "
        "would still pass",
    ),
    (
        "a COMPLETE draft SPEC",
        "spec",
        "draft",
        True,
        None,
        True,
        "the draft split is a PROPERTY OF THE TABLES, not a special case bolted onto IPDs, so it "
        "must hold for `spec` too. This row plus the next are the spec-side mirror of the two IPD "
        "draft rows",
    ),
    (
        "an INCOMPLETE draft SPEC",
        "spec",
        "draft",
        False,
        None,
        False,
        "the mirror, so the spec type cannot pass by answering True to every draft",
    ),
    (
        "an APPROVED spec",
        "spec",
        "approved",
        None,
        None,
        False,
        "spec 3.3 routes an approved spec to `plan`, NOT to review: it has been reviewed and the "
        "next act is authoring a plan. Sweeping it into `reviews` would re-review settled contracts",
    ),
    (
        "an IMPLEMENTED spec",
        "spec",
        "implemented",
        None,
        None,
        False,
        "the terminal spec status. Nothing is pending on it, so a sweep that included it would grow "
        "without bound as the repository accumulates history",
    ),
    (
        "a to-review IPD in the EXECUTED directory",
        "ipd",
        "to-review",
        None,
        ".aw/records/plans/executed/20260101-s1-01-aaa111-x.ipd.md",
        False,
        "NOT REDUNDANT WITH STATUS, which is the whole reason this column exists: a directory and a "
        "`- Status:` line CAN disagree, and spec 3.2 makes that mismatch a red abort rather than a "
        "review. Both deleted closures performed this check, so dropping it would silently "
        "re-review executed work",
    ),
    (
        "a to-review IPD in the SUPERSEDED directory",
        "ipd",
        "to-review",
        None,
        ".aw/records/plans/superseded/20260101-s1-01-aaa111-x.ipd.md",
        False,
        "the second terminal directory. Four buckets are terminal and each gets a row, because a "
        "check written against one name (a `== 'executed'` comparison) passes one row and fails the "
        "other three",
    ),
    (
        "a to-review IPD in the NOT-EXECUTED directory",
        "ipd",
        "to-review",
        None,
        ".aw/records/plans/not-executed/20260101-s1-01-aaa111-x.ipd.md",
        False,
        "the third, for the same reason",
    ),
    (
        "a to-review IPD in the REUSABLE directory",
        "ipd",
        "to-review",
        None,
        ".aw/records/plans/reusable/20260101-s1-01-aaa111-x.ipd.md",
        False,
        "the fourth, and the odd one out: `reusable` is a STANDING disposition rather than a "
        "finished one, so a reader might reasonably think it belongs in a sweep. It does not, and "
        "that judgement is recorded here rather than left implicit",
    ),
    (
        "a COMPLETE draft IPD in a terminal directory",
        "ipd",
        "draft",
        True,
        ".aw/records/plans/executed/20260101-s1-01-aaa111-x.ipd.md",
        False,
        "THE INTERACTION ROW, and the reason a table beats four tests: the directory exclusion must "
        "outrank the completeness admission. Checked in the WRONG ORDER, a complete draft in an "
        "executed directory answers True, and no single-input test can see that",
    ),
    (
        "a to-review IPD in PENDING, stated as a path",
        "ipd",
        "to-review",
        None,
        ".aw/records/plans/pending/20260101-s1-01-aaa111-x.ipd.md",
        True,
        "THE SECOND POSITIVE, and what keeps the four exclusion rows above honest: a predicate that "
        "answered False whenever a `file_path` was supplied at all would satisfy every one of them",
    ),
)


def test_needs_review_answers_every_input_combination_correctly():
    wrong = []
    positive_rows_broken = 0
    for (
        case,
        spec_type,
        status,
        complete,
        file_path,
        expected,
        why,
    ) in _NEEDS_REVIEW_CELLS:
        kwargs = {}
        if complete is not None:
            kwargs["authoring_complete"] = complete
        if file_path is not None:
            kwargs["file_path"] = file_path
        got = pol.needs_review(spec_type, status, **kwargs)
        if got is not expected:
            if expected:
                positive_rows_broken += 1
            wrong.append(
                "  {0}\n    call: needs_review({1!r}, {2!r}{3})\n"
                "    - expected {4!r}, got {5!r}\n"
                "    this row exists because: {6}".format(
                    case,
                    spec_type,
                    status,
                    "".join(", {0}={1!r}".format(k, v) for k, v in kwargs.items()),
                    expected,
                    got,
                    why,
                )
            )
    extra = ""
    if positive_rows_broken:
        extra = (
            " {0} row(s) that must answer True are among the failures, and while any of those is "
            "broken every False row is VACUOUS: a predicate answering False unconditionally "
            "satisfies all of them, and it also empties the `reviews` sweep entirely.".format(
                positive_rows_broken
            )
        )
    assert not wrong, (
        "needs_review answered wrongly for {0} of {1} input combinations.{2} THIS PREDICATE IS THE "
        "SINGLE SOURCE OF `reviews` SWEEP MEMBERSHIP (spec 25kzda 2.4a property 2), so read the "
        "grouping: every DRAFT row failing means the completeness split moved; every TERMINAL "
        "DIRECTORY row failing means that exclusion was dropped, which silently re-reviews finished "
        "work; every SPEC row failing while the IPD rows pass means the predicate went back to being "
        "IPD-hardcoded. FIX: if the INTERACTION row (a complete draft in a terminal directory) is "
        "the only failure, the two checks are being applied in the wrong ORDER - the directory "
        "exclusion must outrank the completeness admission.\n{3}".format(
            len(wrong),
            len(_NEEDS_REVIEW_CELLS),
            extra,
            "\n".join(wrong),
        )
    )


def test_undetermined_is_the_action_behind_the_two_excluded_ipd_statuses():
    """Kept separate: asserts `_action_for`, the ACTION table, not the `needs_review` predicate.

    The cell table above proves `draft` and `reviewed` are not swept. This proves WHY: `_IPD_ACTIONS`
    omits both on purpose, mapping them to `ACTION_UNDETERMINED` because they branch on content,
    `--full-auto`, or `--action`. A predicate hard-coding two exclusions would pass every cell above
    while the action table said something else entirely.
    """
    assert pol._action_for("ipd", "reviewed") == pol.ACTION_UNDETERMINED
    assert pol._action_for("ipd", "draft") == pol.ACTION_UNDETERMINED


def test_only_the_draft_row_consults_completeness():
    """Kept separate: a DIFFERENT function answering "which rows need content", not a review verdict.

    `review_depends_on_completeness` is what stops each caller hard-coding `draft` for itself, so the
    rule has ONE definition. The cell table exercises completeness as an INPUT; this names the rows
    it is allowed to affect, which is a claim about the table's shape rather than about any verdict.
    """
    assert pol.review_depends_on_completeness("ipd", "draft") is True
    assert pol.review_depends_on_completeness("spec", "DRAFT ") is True
    for status in ("to-review", "reviewed", "approved", "executed", None):
        assert pol.review_depends_on_completeness("ipd", status) is False
    # A type with no action table has no completeness-dependent row either.
    assert pol.review_depends_on_completeness("research", "draft") is False


def test_the_terminal_directory_predicate_itself_classifies_every_bucket():
    """Kept separate: `is_in_terminal_directory` is a PATH classifier, not a review verdict.

    The cell table consumes this through `needs_review`, where a False can come from either the
    directory check or the status. This isolates the classifier so a regression is attributable: if
    these pass and the table's directory rows fail, `needs_review` stopped CONSULTING the classifier
    rather than the classifier being wrong.
    """
    for bucket in ("executed", "superseded", "not-executed", "reusable"):
        path = ".aw/records/plans/{0}/20260101-s1-01-aaa111-x.ipd.md".format(bucket)
        assert pol.is_in_terminal_directory(path) is True
    assert (
        pol.is_in_terminal_directory(
            ".aw/records/plans/pending/20260101-s1-01-aaa111-x.ipd.md"
        )
        is False
    )


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-05: TYPE-AWARE SIGNATURE, IPD-ONLY REACH
# --------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-03: THE DRAFT ADMISSION GATE (spec 25kzda 2.5a)
# --------------------------------------------------------------------------------------------------

SPEC_PATH = (
    Path(__file__).resolve().parents[1]
    / ".aw"
    / "records"
    / "specs"
    / "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
)


def _spec_2_5a_blocks() -> list:
    """The fenced `text` blocks of spec 2.5a, read from the SPEC FILE so a spec edit fails here."""
    text = SPEC_PATH.read_text(encoding="utf-8")
    section = text.split("### 2.5a Draft admission gate", 1)
    assert len(section) == 2, "spec 2.5a heading not found; did the spec move?"
    body = section[1].split("### 2.6", 1)[0]
    return [chunk.split("```", 1)[0].strip() for chunk in body.split("```text")[1:]]


def _drafts(complete: int = 0, incomplete: int = 0, spec_type: str = "ipd") -> list:
    out = [
        pol.DraftCandidate("c{0}".format(i), spec_type, True) for i in range(complete)
    ]
    out += [
        pol.DraftCandidate("i{0}".format(i), spec_type, False)
        for i in range(incomplete)
    ]
    return out


def test_the_exclusion_notice_is_the_specs_text_character_for_character():
    """Transcribed, never recomposed: the code prefix, the counts, and the recovery command are all
    fixed by spec 2.5a's `Exact refusal` block."""
    spec_refusal = _spec_2_5a_blocks()[-1]
    assert pol.DRAFTS_EXCLUDED_TEMPLATE == spec_refusal


def test_the_preview_is_byte_identical_to_the_specs_own_example():
    """Spec 2.5a's example block, reproduced by the SHARED renderer (2 IPDs, 1 spec, 1 incomplete)."""
    spec_preview = _spec_2_5a_blocks()[0]
    candidates = _drafts(complete=2) + [
        pol.DraftCandidate("s0", "spec", True),
        pol.DraftCandidate("bad", "ipd", False),
    ]
    verdict = pol.decide_draft_admission(
        candidates, interactive=False, allow_drafts=True
    )
    assert verdict.record.preview == spec_preview


def test_the_exact_phrase_is_required_and_reflex_answers_are_rejected():
    candidates = _drafts(complete=2)
    assert pol.DRAFTS_CONFIRM_PHRASE == "run drafts"
    good = pol.decide_draft_admission(
        candidates, interactive=True, response="run drafts\n"
    )
    assert good.admitted == ("c0", "c1")
    assert good.excluded_complete == ()
    for bad in ("y", "yes", "Y", "", "run", "run draft", "run drafts please", None):
        verdict = pol.decide_draft_admission(candidates, interactive=True, response=bad)
        assert verdict.admitted == (), "reflex answer {0!r} admitted a draft".format(
            bad
        )
        assert verdict.excluded_complete == ("c0", "c1")


def test_allow_drafts_admits_them_unattended():
    verdict = pol.decide_draft_admission(
        _drafts(complete=1), interactive=False, allow_drafts=True
    )
    assert verdict.admitted == ("c0",)
    assert verdict.record.response_or_flag == "--allow-drafts"
    assert verdict.message is None


def test_asymmetry_one_an_incomplete_draft_is_never_admitted_at_any_flag_setting():
    """spec 2.5a bullet 1. NO flag admits it, and it is never an abort: one unfinished draft must not
    deny review to the finished items beside it."""
    candidates = _drafts(complete=1, incomplete=1)
    for interactive, allow, response in (
        (False, False, None),
        (False, True, None),
        (True, False, "run drafts"),
        (True, True, "run drafts"),
    ):
        verdict = pol.decide_draft_admission(
            candidates,
            interactive=interactive,
            allow_drafts=allow,
            response=response,
        )
        assert "i0" not in verdict.admitted
        assert verdict.skipped_incomplete == ("i0",)
    # And with ONLY an incomplete draft the gate does not even apply, yet the skip is still reported.
    only_bad = pol.decide_draft_admission(_drafts(incomplete=1), interactive=False)
    assert only_bad.gate_applied is False
    assert only_bad.skipped_incomplete == ("i0",)
    assert only_bad.admitted == ()


def test_asymmetry_two_an_ungated_draft_is_excluded_while_the_run_proceeds():
    """spec 2.5a bullet 4, and the reason it differs from the mixed-type refusal.

    THE DIFFERENCE IS THE POINT: `decide` REFUSES a mixed selection (`proceed=False`, "No work
    started."), because the operator's intent is unclear. This gate excludes ONE item's admission and
    the rest proceeds, because the remaining items' intent is not in doubt. `DraftVerdict` therefore
    has no `proceed` field at all, which is what stops a later reader "fixing" the inconsistency.
    """
    verdict = pol.decide_draft_admission(
        _drafts(complete=2), interactive=False, allow_drafts=False, remaining_count=3
    )
    assert verdict.excluded_complete == ("c0", "c1")
    assert verdict.admitted == ()
    assert verdict.code == pol.RUN_DRAFTS_EXCLUDED
    assert not hasattr(verdict, "proceed")
    # The notice states what proceeded, so the operator is not told the run stopped.
    assert "2 complete draft item(s)" in verdict.message
    assert "3 item(s) proceeded" in verdict.message
    assert "No work started." not in verdict.message


def test_the_ledger_facts_are_returned_not_written():
    """`MixedTypeRecord`'s convention, followed: the module returns the facts, the runner persists."""
    verdict = pol.decide_draft_admission(
        _drafts(complete=2) + [pol.DraftCandidate("s0", "spec", True)],
        interactive=False,
        allow_drafts=True,
    )
    payload = verdict.record.as_dict()
    assert payload["draft_counts"] == {"ipd": 2, "spec": 1}
    assert payload["admitted"] == ["c0", "c1", "s0"]
    assert payload["response_or_flag"] == "--allow-drafts"
    assert payload["preview"].startswith(pol.DRAFTS_PREVIEW_HEADER)
    import json

    json.dumps(payload)  # JSON-ready, as the ledger append requires


def test_the_draft_gate_is_pure_and_deterministic():
    candidates = _drafts(complete=2, incomplete=1)
    first = pol.decide_draft_admission(candidates, interactive=False)
    second = pol.decide_draft_admission(candidates, interactive=False)
    assert first == second


def test_the_combined_case_collects_both_confirmations_in_one_interaction():
    """spec 2.5a bullet 5: both previews together, both answers before any work starts.

    PROVEN AT THE SEAM WITH A CONSTRUCTED CLASSIFICATION, and it is proven CORRECT, NOT proven FIRED:
    no real invocation can produce a mixed selection yet (discovery is IPD-only, neither host has
    `--type`), so this path cannot be triggered in production. See
    `test_no_live_invocation_can_yet_produce_a_mixed_selection` in `tests/test_run_flag_surface.py`.
    """
    mixed = _spec_example()
    assert mixed.is_mixed is True
    combined = pol.decide_selection_gates(
        mixed,
        _drafts(complete=1),
        interactive=True,
        mixed_response="run mixed",
        drafts_response="run drafts",
    )
    assert combined.proceed is True
    assert combined.mixed.gate_applied is True
    assert combined.drafts.admitted == ("c0",)
    # BOTH previews, together, in ONE rendered block.
    assert "Mixed work-item selection:" in combined.combined_preview
    assert pol.DRAFTS_PREVIEW_HEADER in combined.combined_preview
    # Each answer is independent: the mixed phrase does not admit drafts, nor vice versa.
    only_mixed = pol.decide_selection_gates(
        mixed,
        _drafts(complete=1),
        interactive=True,
        mixed_response="run mixed",
        drafts_response=None,
    )
    assert only_mixed.proceed is True
    assert only_mixed.drafts.admitted == ()
    only_drafts = pol.decide_selection_gates(
        mixed,
        _drafts(complete=1),
        interactive=True,
        mixed_response=None,
        drafts_response="run drafts",
    )
    assert only_drafts.proceed is False  # the mixed gate still refuses the run
    assert only_drafts.drafts.admitted == ("c0",)


# --------------------------------------------------------------------------------------------------
# runnoop Order 02 (`m85gxh`): the per-artifact disposition line and its closed reason set
# --------------------------------------------------------------------------------------------------
#
# WHY THESE LIVE HERE AND NEED NO RUN. The renderer is PURE, so every branch is a function of its
# inputs and can be asserted directly; a test that needed a live run to prove a reason string would be
# proving the driver's wiring, which is `tests/test_oc_runipd.py`'s and `tests/test_agy_runipd_cli.py`'s
# job. What is proven here is the CONTRACT: one renderer for both shapes, a closed reason vocabulary,
# and a dependency reason that NAMES the unmet dependency.


def _queue_entry(**over):
    """One queue entry in the shape `runner_shared.initialize_run_core` actually freezes."""
    entry = {
        "position": 1,
        "id6": "abc123",
        "setid": "wtiso",
        "action": "execute",
        "status": "reviewed",
        "attempts": [],
    }
    entry.update(over)
    return entry


def test_one_renderer_produces_the_acted_on_and_skipped_lines_in_the_same_shape():
    """The backlog item's actual requirement: a skipped artifact reported in the SAME shape.

    ASSERTED STRUCTURALLY, not by eyeballing two strings: both lines come from the SAME function, and
    the field layout (`- <pos> <id6> [<set>] <action> -> <disposition>: <reason>`) is identical up to
    the reason text. Two renderers would drift exactly as `render_action_preview`'s docstring records.
    """
    skipped = pol.render_item_disposition(
        "abc123",
        "execute",
        "reviewed",
        "needs_human_approval (frozen)",
        position=1,
        setid="wtiso",
    )
    acted = pol.render_item_disposition(
        "def456", "execute", "executed", None, position=2, setid="wtiso"
    )
    assert (
        skipped
        == "- 01 abc123 [wtiso] execute -> reviewed: needs_human_approval (frozen)"
    )
    assert acted == "- 02 def456 [wtiso] execute -> executed: acted on by this run"
    # The SHAPE is identical: same prefix, same arrow, same colon, same field count.
    for line in (skipped, acted):
        head, _, reason = line.partition(": ")
        assert head.startswith("- ")
        assert " -> " in head
        assert reason  # never blank, which is what keeps the two shapes comparable


def test_an_acted_on_artifact_never_renders_a_blank_reason():
    """A blank reason reads as missing information, so the acted-on case carries a fixed label."""
    assert pol.ACTED_REASON_LABEL in pol.render_item_disposition(
        "a", "execute", "executed"
    )
    assert pol.ACTED_REASON_LABEL in pol.render_item_disposition(
        "a", "execute", "executed", "   "
    )


def test_the_skip_reason_set_is_closed_and_uses_the_spec_names():
    """Spec `25kzda` supplies EVERY name; this plan mints none (E-02).

    The four dependency/approval/capability names come from 5.4's "Stable dependency reason codes"
    and 5.7's failure-class table; `ipd_already_executed` from Section 6's worked example item 8; and
    `type_or_status_not_runnable` from 5.7's "Non-runnable state/type" row.
    """
    assert set(pol.SKIP_REASONS) == {
        "needs_human_approval",
        "dependency_not_met",
        "dependency_not_met_external",
        "ipd_already_executed",
        "type_or_status_not_runnable",
        "host_capability_unavailable",
    }
    # Every reason is documented with WHERE its value is read from, and glossed for a human.
    for code in pol.SKIP_REASONS:
        assert pol.SKIP_REASON_SOURCES[code].strip()
        assert pol.SKIP_REASON_LABELS[code].strip()
    # CLOSED: an invented seventh reason is refused rather than silently rendered.
    with pytest.raises(ValueError) as err:
        pol.skip_reason_text("gate_refused")
    assert "unknown skip reason code" in str(err.value)


def test_every_named_reason_renders_a_line_carrying_its_code_and_gloss():
    """The code is the machine-stable half; the gloss is what makes the line legible."""
    for code in pol.SKIP_REASONS:
        line = pol.render_item_disposition_for_reason(
            "abc123", "execute", "reviewed", code
        )
        assert code in line
        assert pol.SKIP_REASON_LABELS[code] in line


#: (case, queue-entry overrides, substrings that MUST appear in the rendered line, substrings that
#: must NOT appear, why this row exists) - ONE table replacing four tests
#: (`the_dependency_reason_names_the_unmet_dependency`,
#: `an_external_unsatisfiable_dependency_takes_the_external_reason_code`,
#: `the_needs_approval_line_explains_reviewed_to_a_reader_who_does_not_know_it`,
#: `a_dependency_token_that_already_carries_its_reason_is_not_double_explained`). Every one of them
#: built ONE queue entry, rendered it, and asserted substrings of the single resulting line.
#:
#: WHY THE TABLE BEATS THE FOUR. The reason set is CLOSED (spec `25kzda` supplies every name; this
#: module mints none), and one derivation maps an entry's shape onto one of those codes plus a gloss.
#: The realistic failure is that derivation picking the WRONG CODE for a shape - which is what the
#: two dependency-producer rows exist for, since the two producers write genuinely different shapes
#: and a single `reasons.get(d, "unsatisfied")` fallback renders one of them with two contradictory
#: reasons on one line. Four tests report a wrong code as four unrelated substring misses; the table
#: reports which shapes now derive the wrong code, together, which is how a mis-mapped derivation
#: actually looks.
#:
#: THE FORBIDDEN-SUBSTRING COLUMN IS NOT DECORATION. A line can carry the right code and STILL be
#: wrong: the inline-reason row must not gain a second `(unsatisfied)` gloss, and the
#: recorded-refusal row must not also print the inferable reason it outranks. Those are claims about
#: what is ABSENT, which a present-substring-only table cannot make.
_DISPOSITION_LINES = (
    (
        "an item frozen awaiting human approval",
        {"needs_input": True},
        ("needs_human_approval", "approval"),
        (),
        "THE MEASURED DEFECT (backlog `em0z50`): `reviewed` was displayed with no explanation. The "
        "summary already showed the status; what was missing is the REASON. Both the machine CODE "
        "and the word `approval` in prose are required, because a reader who does not already know "
        "what `reviewed` implies learns nothing from the code alone",
    ),
    (
        "a dependency unmet by an IN-RUN target, reason supplied in the MAP",
        {
            "status": "dependency-blocked",
            "unsatisfied_dependencies": ["executed:zz5yxq"],
            "unsatisfied_dependency_reasons": {
                "executed:zz5yxq": "in-run target zz5yxq is 'reviewed'"
            },
        },
        (
            "dependency_not_met",
            "executed:zz5yxq",
            "in-run target zz5yxq is 'reviewed'",
        ),
        ("dependency_not_met_external",),
        "THE BACKLOG ITEM REQUIRES THE UNMET DEPENDENCY TO BE NAMED, so it is asserted specifically: "
        "the code, the dependency TOKEN, and the recorded reason must all appear. `dependency_not_met` "
        "is a prefix of `dependency_not_met_external`, so the external code is FORBIDDEN here - "
        "otherwise this row would pass against a renderer that emitted the external code for "
        "everything",
    ),
    (
        "a dependency on an OUT-OF-QUEUE target, reason supplied in the map",
        {
            "status": "dependency-blocked",
            "unsatisfied_dependencies": ["executed:aaa111"],
            "unsatisfied_dependency_reasons": {
                "executed:aaa111": (
                    "executed:aaa111: external target aaa111 is 'approved' (directory 'pending'), "
                    "it is not in this run, so it cannot become satisfied here"
                )
            },
        },
        ("dependency_not_met_external",),
        (),
        "`edge_satisfied`'s own wording for an out-of-queue target selects the spec's EXTERNAL code, "
        "and the DISTINCTION IS ACTIONABLE: an in-run dependency may yet be satisfied by this run, "
        "while an external one never can, so an operator's next step differs. Deriving the code from "
        "the reason TEXT is what makes this row a real test of the mapping",
    ),
    (
        "a dependency token that ALREADY CARRIES its reason, with no map",
        {
            "status": "dependency-blocked",
            "unsatisfied_dependencies": ["executed:aaa111 (target reviewed)"],
        },
        ("dependency_not_met", "executed:aaa111 (target reviewed)"),
        ("(unsatisfied)",),
        "THE TWO PRODUCERS WRITE DIFFERENT SHAPES (measured): the drain path writes a BARE token "
        "plus a separate reason MAP, while `cascade_dependency_blocked` writes the reason INTO the "
        'token and supplies no map. A `reasons.get(d, "unsatisfied")` fallback renders this one as '
        "`executed:aaa111 (target reviewed) (unsatisfied)` - two contradictory reasons on one line - "
        "which is why `(unsatisfied)` is the FORBIDDEN substring rather than a missing one",
    ),
    (
        "the OTHER producer's shape, bare token plus map",
        {
            "status": "dependency-blocked",
            "unsatisfied_dependencies": ["executed:bbb222"],
            "unsatisfied_dependency_reasons": {
                "executed:bbb222": "in-run target is 'reviewed'"
            },
        },
        ("executed:bbb222 (in-run target is 'reviewed')",),
        (),
        "the paired half of the row above, asserted as the EXACT composed form rather than as two "
        "separate substrings: the fix for the double-gloss must not be 'stop printing the reason', "
        "so this row pins that a bare token still gets its mapped reason parenthesized exactly once",
    ),
)


def test_every_entry_shape_renders_its_own_reason_code_and_gloss():
    wrong = []
    for case, overrides, needles, forbidden, why in _DISPOSITION_LINES:
        lines = pol.render_queue_dispositions([_queue_entry(**overrides)])
        problems = []
        if len(lines) != 2:
            problems.append(
                "expected a header plus exactly ONE artifact line, got {0} line(s): {1!r}".format(
                    len(lines), lines
                )
            )
            line = ""
        else:
            line = lines[1]
        for needle in needles:
            if needle not in line:
                problems.append(
                    "the line is missing {0!r}; it is {1!r}".format(needle, line)
                )
        for banned in forbidden:
            if banned in line:
                problems.append(
                    "the line contains {0!r}, which is WRONG for this shape; it is {1!r}".format(
                        banned, line
                    )
                )
        if problems:
            wrong.append(
                "  {0}\n".format(case)
                + "".join("    - {0}\n".format(p) for p in problems)
                + "    this row exists because: {0}".format(why)
            )
    assert not wrong, (
        "the per-artifact disposition line is wrong for {0} of {1} entry shapes. The reason set is "
        "CLOSED and spec `25kzda` supplies every name, so read the grouping: every DEPENDENCY row "
        "failing together means the dependency derivation changed, while the in-run and external "
        "rows disagreeing means the two codes are being confused - and that distinction is "
        "ACTIONABLE, since an in-run dependency may yet be satisfied by this run and an external one "
        "never can. FIX: a FORBIDDEN-substring failure is not cosmetic. `(unsatisfied)` appearing "
        "beside a reason the token already carries puts two contradictory reasons on one line, which "
        "is the measured defect these rows pin.\n{2}".format(
            len(wrong), len(_DISPOSITION_LINES), "\n".join(wrong)
        )
    )


def test_one_line_per_matched_artifact_regardless_of_attempt_count():
    """The once-per-artifact property, which is what makes child 03's counts sum (E-03)."""
    queue = [
        _queue_entry(position=1, id6="abc123", needs_input=True),
        _queue_entry(
            position=2,
            id6="def456",
            status="executed",
            attempts=[{"n": 1}, {"n": 2}, {"n": 3}],
        ),
        _queue_entry(position=3, id6="ghi789", status="executed"),
        _queue_entry(position=4, id6="jkl012", status="not-attempted"),
    ]
    lines = pol.render_queue_dispositions(queue)
    assert lines[0] == pol.DISPOSITION_HEADER
    assert len(lines) - 1 == len(queue)
    # Four DISTINCT dispositions, each explained; the three-attempt item still gets exactly one line.
    assert sum(1 for line in lines if "def456" in line) == 1
    assert "needs_human_approval" in lines[1]
    assert pol.ACTED_REASON_LABEL in lines[2]
    assert "ipd_already_executed" in lines[3]
    assert "type_or_status_not_runnable" in lines[4]


def test_a_recorded_refusal_supplies_the_reason_through_the_owning_plans_reader():
    """E-05's seam: `orchprobe` `r2i1b1`'s record WINS, and this plan defines no record type.

    The reader is INJECTED (that plan's shipped `refusal_of_item`), so this module never imports
    `render_stream` and never reads the refusal key itself.
    """
    from agent_workflows import render_stream

    entry = _queue_entry(status="merge-refused")
    render_stream.record_refusal(
        entry,
        code="merge-refused",
        reason="the lane conflicted with main on two files",
        remedy="inspect the lane, resolve, then re-integrate",
    )
    lines = pol.render_queue_dispositions(
        [entry], refusal_reader=render_stream.refusal_of_item
    )
    assert "the lane conflicted with main on two files" in lines[1]
    # The REMEDY is deliberately NOT duplicated here: the summary's diagnostics block already prints it.
    assert "inspect the lane" not in lines[1]
    # Without the reader, no refusal is consulted at all.
    assert "conflicted" not in pol.render_queue_dispositions([entry])[1]


def test_the_refusal_record_outranks_an_inferable_reason():
    """A producer that said WHY is more specific than anything inferable from a status."""
    from agent_workflows import render_stream

    entry = _queue_entry(needs_input=True)
    render_stream.record_refusal(
        entry, code="custom", reason="a specific recorded reason", remedy="do the thing"
    )
    line = pol.render_queue_dispositions(
        [entry], refusal_reader=render_stream.refusal_of_item
    )[1]
    assert "a specific recorded reason" in line
    assert "needs_human_approval" not in line


#: (renderer name, the renderer, why this row exists) - the two public renderers, each of which must
#: be PURE (return lines, print nothing) and must render NOTHING for an empty selection.
#:
#: ONE table replaces four tests (`the_renderer_is_pure_no_print_no_filesystem`,
#: `an_empty_selection_renders_no_header`, `the_summary_renderer_is_pure_no_print_no_filesystem`,
#: `an_empty_selection_renders_no_summary`) - two claims x two renderers, written out as four.
#:
#: WHY THE TABLE BEATS THE FOUR. Both claims are MODULE CONVENTIONS rather than facts about either
#: function: purity is what lets these renderers be called from anywhere (including inside a run
#: whose stdout is a machine stream), and empty-renders-nothing is what stops a stray header
#: appearing over nothing. A convention tested per-function rots per-function - a third renderer
#: added later gets neither test - whereas a table over the renderer SET makes the omission visible,
#: since adding a renderer without adding its row is now the conspicuous act.
_PURE_RENDERERS = (
    (
        "render_queue_dispositions",
        pol.render_queue_dispositions,
        "the per-artifact line renderer. Its empty case must produce NO HEADER: a stray "
        "`Per-artifact disposition` heading over zero lines reads as 'the run matched nothing and "
        "also told you nothing', which is worse than silence",
    ),
    (
        "render_disposition_summary",
        pol.render_disposition_summary,
        "the end-of-run summary renderer. Its empty case is DIFFERENT IN KIND and that is why it "
        "needs its own row: nothing matched is NOT the zero-action case, so a summary saying 'acted "
        "on 0 of 0' would be a claim about a run that never had a queue",
    ),
)


def test_every_renderer_is_pure_and_renders_nothing_for_an_empty_selection():
    import contextlib
    import io

    wrong = []
    for name, renderer, why in _PURE_RENDERERS:
        problems = []
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = renderer([_queue_entry(needs_input=True)])
        if buf.getvalue() != "":
            problems.append(
                "wrote {0!r} to stdout; a renderer must RETURN its lines so a caller decides where "
                "they go (a run whose stdout is a machine stream cannot have prose injected into "
                "it)".format(buf.getvalue()[:200])
            )
        if not isinstance(out, list):
            problems.append(
                "returned {0!r}, expected a list of lines".format(type(out).__name__)
            )
        elif not out:
            problems.append(
                "returned NO lines for a non-empty queue, so the artifact it was given is invisible"
            )
        empty_buf = io.StringIO()
        with contextlib.redirect_stdout(empty_buf):
            empty_out = renderer([])
        if empty_out != []:
            problems.append(
                "rendered {0!r} for an EMPTY selection, expected []".format(empty_out)
            )
        if empty_buf.getvalue() != "":
            problems.append(
                "wrote {0!r} to stdout for an empty selection".format(
                    empty_buf.getvalue()[:200]
                )
            )
        if problems:
            wrong.append(
                "  {0}\n".format(name)
                + "".join("    - {0}\n".format(p) for p in problems)
                + "    this row exists because: {0}".format(why)
            )
    assert not wrong, (
        "{0} of {1} renderers violate the module's conventions. BOTH ROWS FAILING THE SAME WAY means "
        "a convention was abandoned module-wide rather than one function regressing: a renderer that "
        "PRINTS cannot be called from a run whose stdout is a machine stream, and one that renders a "
        "header over an empty selection reports a run that matched nothing as though it had output. "
        "FIX: if you added a third renderer, add its row here rather than writing it two new tests - "
        "that is what this table is for.\n{2}".format(
            len(wrong), len(_PURE_RENDERERS), "\n".join(wrong)
        )
    )


# --------------------------------------------------------------------------------------------------
# The END-OF-RUN DISPOSITION SUMMARY (`runnoop` Order 03, `bsc457`)
# --------------------------------------------------------------------------------------------------


def test_a_run_that_acted_on_nothing_still_gets_a_summary_naming_every_artifact():
    """THE MEASURED INCIDENT (backlog `em0z50`), at the pure-renderer level.

    `aw oc run wtiso` matched 8 plans, acted on NONE, and no surface said so. The counts must SUM to
    the number matched, which is the property worth asserting rather than any individual number.
    """
    queue = [
        _queue_entry(position=i, id6="id%04d" % i, needs_input=True)
        for i in range(1, 9)
    ]
    lines = pol.render_disposition_summary(queue)
    text = "\n".join(lines)
    assert pol.SUMMARY_HEADER in text
    # The HONEST VERDICT: the table says COMPLETED at 100% for this same queue.
    assert "NO WORK WAS PERFORMED" in text
    assert "matched 8 artifact(s) and acted on NONE" in text
    # The count, and the remedy beside it, in the shape the backlog item specifies.
    assert "needs_human_approval (8)" in text
    assert "aw ipd set approved <id6> --by-human" in text
    rows = pol.summarize_dispositions(queue)
    assert sum(count for _c, count, _r in rows) == len(queue)


def test_the_counts_sum_to_the_number_matched_for_a_mixed_queue():
    """The partition property: every entry lands in exactly one bucket, so nothing is lost or double-counted."""
    queue = [
        _queue_entry(position=1, id6="aaa111", needs_input=True),
        _queue_entry(position=2, id6="bbb222", status="executed"),
        _queue_entry(position=3, id6="ccc333", status="not-attempted"),
        _queue_entry(
            position=4,
            id6="ddd444",
            status="dependency-blocked",
            unsatisfied_dependencies=["executed:aaa111"],
        ),
        _queue_entry(position=5, id6="eee555", status="executed", attempts=[{"n": 1}]),
    ]
    rows = pol.summarize_dispositions(queue)
    assert sum(count for _c, count, _r in rows) == len(queue)
    text = "\n".join(pol.render_disposition_summary(queue))
    assert "total: 5 matched, 1 acted on, 4 not acted on" in text


def test_every_actionable_disposition_carries_a_remedy_and_terminal_ones_do_not():
    """A needed-no-remedy disposition and an unknown one must render DIFFERENTLY, never alike."""
    # Actionable -> a remedy.
    for code in pol.DISPOSITION_REMEDIES:
        assert pol.remedy_for_disposition(code) == pol.DISPOSITION_REMEDIES[code]
    # Legitimately terminal -> None, meaning "nothing to do, and that is correct".
    for code in pol.DISPOSITIONS_NEEDING_NO_REMEDY:
        assert pol.remedy_for_disposition(code) is None
    # Unrecognized -> an explicit admission, NOT silence.
    unknown = pol.remedy_for_disposition("a_reason_nobody_wrote_a_remedy_for")
    assert unknown == pol.REMEDY_UNKNOWN_TEXT
    assert unknown != pol.remedy_for_disposition(pol.SKIP_ALREADY_EXECUTED)


def test_every_closed_skip_reason_resolves_to_a_remedy_or_an_explicit_no_remedy():
    """A new reason cannot be added without an author noticing its remedy is missing."""
    for code in pol.SKIP_REASONS:
        assert (
            code in pol.DISPOSITION_REMEDIES
            or code in pol.DISPOSITIONS_NEEDING_NO_REMEDY
        ), f"{code} has neither a remedy nor an explicit 'needs none' marker"
        assert pol.remedy_for_disposition(code) != pol.REMEDY_UNKNOWN_TEXT


def test_the_unknown_and_the_no_remedy_cases_render_differently():
    """Asserted on the RENDERED block, because rendering a gap as a correct outcome is the defect."""
    known = "\n".join(pol.render_disposition_summary([_queue_entry(status="executed")]))
    assert "ipd_already_executed (1)" in known
    assert pol.REMEDY_UNKNOWN_TEXT not in known

    class _Refusal:
        code = "a_brand_new_refusal_code"
        reason = "something novel happened"
        remedy = ""

    gap = "\n".join(
        pol.render_disposition_summary(
            [_queue_entry(status="blocked")], refusal_reader=lambda _e: _Refusal()
        )
    )
    assert "a_brand_new_refusal_code (1)" in gap
    assert pol.REMEDY_UNKNOWN_TEXT in gap


def test_a_recorded_refusals_own_remedy_is_sourced_not_duplicated():
    """E-06's executed branch: `orchprobe` `r2i1b1` shipped the record, so its remedy is the authority."""
    from agent_workflows import render_stream

    entry = _queue_entry(status="merge-needs-human", attempts=[{"n": 1}])
    render_stream.record_refusal(
        entry,
        code="merge-needs-human",
        reason="the lane finalized but could not be merged",
        remedy="re-attempt with `aw oc run integrate <run-id>`",
    )
    text = "\n".join(
        pol.render_disposition_summary(
            [entry], refusal_reader=render_stream.refusal_of_item
        )
    )
    assert "merge-needs-human (1)" in text
    # The record's OWN remedy, rather than a second copy maintained in this module.
    assert "re-attempt with `aw oc run integrate <run-id>`" in text
    assert "merge-needs-human" not in pol.DISPOSITION_REMEDIES


def test_the_line_and_the_summary_cannot_disagree_about_one_artifact():
    """CID-3: ONE disposition vocabulary, because both read the SAME derivation."""
    queue = [
        _queue_entry(position=1, id6="aaa111", needs_input=True),
        _queue_entry(position=2, id6="bbb222", status="executed"),
    ]
    lines = pol.render_queue_dispositions(queue)
    summary = "\n".join(pol.render_disposition_summary(queue))
    for code in (pol.SKIP_NEEDS_HUMAN_APPROVAL, pol.SKIP_ALREADY_EXECUTED):
        assert any(code in line for line in lines[1:])
        assert code in summary


def test_an_acted_on_artifact_is_a_real_bucket_so_the_counts_can_sum():
    """`acted_on` is a KEY, not the absence of one, or the partition would not be total."""
    queue = [_queue_entry(status="executed", attempts=[{"n": 1}])]
    rows = pol.summarize_dispositions(queue)
    assert rows == ((pol.DISPOSITION_ACTED_ON, 1, None),)
    text = "\n".join(pol.render_disposition_summary(queue))
    assert "acted on all 1 artifact(s)" in text


def test_the_summary_orders_attention_first_and_acted_on_last():
    """A reader must reach the things needing action before the total of what went fine."""
    queue = [
        _queue_entry(position=1, id6="aaa111", status="executed", attempts=[{"n": 1}]),
        _queue_entry(position=2, id6="bbb222", needs_input=True),
    ]
    codes = [code for code, _n, _r in pol.summarize_dispositions(queue)]
    assert codes == [pol.SKIP_NEEDS_HUMAN_APPROVAL, pol.DISPOSITION_ACTED_ON]
