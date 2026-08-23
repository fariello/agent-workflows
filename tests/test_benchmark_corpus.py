"""Self-tests for the benchmark corpus foundations (awoptimize Order 12, `1jfxvo`, E-01..E-05).

Falsifiable, stdlib `unittest` only. Each test asserts DETECTION or REJECTION:

  * E-01 / V-01: manifest round-trip + mismatch (every identity factor is REQUIRED and included in the
                 result-identity key; a dollar cost is REJECTED in both ceilings and usage; usage fields
                 are present-or-`unavailable`, never zero-filled).
  * E-02 / V-02: deterministic reset produces IDENTICAL hashes; hidden ground truth is INACCESSIBLE to
                 executor paths; every task class has deterministic setup/teardown.
  * E-03 / V-03: one golden transcript per adversarial class is scored false-complete or incomplete as
                 intended, with ZERO critical seed missed by the reference scorer.
  * E-04 / V-04: the protocol digest is frozen; a post-result change to any metric/threshold/retry/
                 exclusion/ground-truth is REJECTED without a new protocol version.
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import benchmark_corpus as corpus
from agent_workflows import benchmark_manifest as mani
from agent_workflows import benchmark_protocol as protocol
from agent_workflows import benchmark_scorer as scorer

FIXTURES = Path(__file__).resolve().parent / "benchmark_fixtures"
CORPUS_ROOT = FIXTURES / "corpus"
ADVERSARIAL_ROOT = FIXTURES / "adversarial"


def _sample_ceilings(host_reports_tokens: bool = False):
    return mani.make_ceilings(
        per_trial_wall_seconds=600.0,
        trial_count=3,
        token_ceiling=100000 if host_reports_tokens else None,
        host_reports_tokens=host_reports_tokens,
    )


def _sample_manifest(**overrides):
    kwargs = dict(
        model_id="its_direct/pt3-claude-opus",
        reasoning_effort="medium",
        host="opencode",
        host_version="1.2.3",
        adapter_digest="a" * 64,
        workflow_digest="b" * 64,
        tool_policy_digest="c" * 64,
        task_seed="simple_commands-001",
        trial=0,
        timeout_seconds=600.0,
        ceilings=_sample_ceilings(),
        environment_fingerprint="d" * 64,
    )
    kwargs.update(overrides)
    return mani.build_manifest(**kwargs)


# ============================================================================================
# E-01 / V-01: result-identity manifest
# ============================================================================================


class ManifestResultIdentityTests(unittest.TestCase):
    def test_round_trip_preserves_identity_and_digest(self):
        m = _sample_manifest()
        rt = mani.manifest_from_json(m.to_json())
        self.assertEqual(m.result_key(), rt.result_key())
        self.assertEqual(m.digest(), rt.digest())
        self.assertTrue(mani.validate_manifest(rt).ok)

    def test_every_identity_factor_is_required(self):
        # Dropping ANY single identity factor makes the result unidentifiable -> rejected on reload.
        base = _sample_manifest().to_dict()
        for factor in mani.IDENTITY_FACTORS:
            broken = copy.deepcopy(base)
            del broken["identity"][factor]
            with self.assertRaises(mani.ManifestError, msg=factor):
                mani.manifest_from_dict(broken)
            val = mani.validate_manifest(broken)
            self.assertFalse(
                val.ok, "validation must reject missing factor %s" % factor
            )
            self.assertTrue(
                any(factor in f.where for f in val.findings),
                "finding must name the missing factor %s" % factor,
            )

    def test_result_key_covers_every_factor(self):
        m = _sample_manifest()
        self.assertEqual(len(m.result_key()), len(mani.IDENTITY_FACTORS))

    def test_differing_factor_forbids_pooling(self):
        a = _sample_manifest()
        # A different reasoning effort is a different cell: cannot be pooled.
        b = _sample_manifest(reasoning_effort="high")
        self.assertFalse(mani.can_pool(a, b))
        self.assertIn("reasoning_effort", mani.declared_factors(a, b))
        # Identical config CAN be pooled.
        c = _sample_manifest()
        self.assertTrue(mani.can_pool(a, c))
        self.assertEqual(mani.declared_factors(a, c), ())

    def test_trial_is_part_of_identity(self):
        a = _sample_manifest(trial=0)
        b = _sample_manifest(trial=1)
        self.assertFalse(mani.can_pool(a, b))
        self.assertIn("trial", mani.declared_factors(a, b))

    def test_dollar_cost_rejected_in_usage(self):
        # A dollar cost is NOT a captured usage field: constructing it is rejected.
        with self.assertRaises(mani.ManifestError):
            mani.make_usage(1.0, cost=5.0)
        with self.assertRaises(mani.ManifestError):
            mani.make_usage(1.0, dollars=5.0)
        # And a manifest carrying a cost key in usage fails validation.
        d = _sample_manifest().to_dict()
        d["usage"]["cost"] = 5.0
        self.assertFalse(mani.validate_manifest(d).ok)
        with self.assertRaises(mani.ManifestError):
            mani.manifest_from_dict(d)

    def test_dollar_or_credit_ceiling_rejected(self):
        with self.assertRaises(mani.ManifestError):
            mani.make_ceilings(600.0, 3, credits=1000)
        with self.assertRaises(mani.ManifestError):
            mani.make_ceilings(600.0, 3, cost=10.0)
        # A raw ceilings dict with a credit-pool field fails validation.
        d = _sample_manifest().to_dict()
        d["ceilings"]["credit_pool"] = 999
        self.assertFalse(mani.validate_ceilings_dict(d["ceilings"]).ok)

    def test_token_ceiling_only_where_host_reports_tokens(self):
        # A token ceiling on a token-less host is rejected.
        with self.assertRaises(mani.ManifestError):
            mani.make_ceilings(600.0, 3, token_ceiling=1000, host_reports_tokens=False)
        # It is admissible where the host reports tokens.
        c = mani.make_ceilings(600.0, 3, token_ceiling=1000, host_reports_tokens=True)
        self.assertEqual(c.as_dict()["token_ceiling"], 1000)

    def test_usage_fields_present_or_unavailable_never_zero_filled(self):
        # A token-less host records tokens as the sentinel, NOT a fake 0.
        u = mani.make_usage(12.5)
        self.assertEqual(u["wall_time"], 12.5)
        self.assertEqual(u["tokens"], mani.UNAVAILABLE)
        self.assertEqual(u["credits_or_quota"], mani.UNAVAILABLE)
        # A host that reports tokens records the real integer.
        u2 = mani.make_usage(12.5, tokens=4200, credits_or_quota="pool-A:0.42")
        self.assertEqual(u2["tokens"], 4200)
        self.assertEqual(u2["credits_or_quota"], "pool-A:0.42")
        # Omitting an optional usage field entirely is REJECTED by validation (it must be
        # present-or-`unavailable`, never silently missing).
        broken = {
            "wall_time": 1.0,
            "tokens": mani.UNAVAILABLE,
        }  # credits_or_quota missing
        self.assertFalse(mani.validate_usage(broken).ok)

    def test_wall_time_is_always_captured(self):
        d = _sample_manifest().to_dict()
        del d["usage"]["wall_time"]
        self.assertFalse(mani.validate_usage(d["usage"]).ok)


# ============================================================================================
# E-02 / V-02: seeded task repos, deterministic reset, hidden truth
# ============================================================================================


class CorpusDeterminismTests(unittest.TestCase):
    def setUp(self):
        self.tasks = corpus.load_corpus(CORPUS_ROOT)

    def test_all_seven_task_classes_present(self):
        present = set(corpus.task_classes_present(self.tasks))
        self.assertEqual(present, set(corpus.TASK_CLASSES))

    def test_every_class_has_deterministic_reset_identical_hashes(self):
        # For EVERY task class, two independent resets produce byte-identical trees (same hash).
        for t in self.tasks:
            with tempfile.TemporaryDirectory() as td:
                h1 = corpus.reset_task(t, Path(td) / "ws1")
                h2 = corpus.reset_task(t, Path(td) / "ws2")
                self.assertEqual(
                    h1, h2, "reset not deterministic for %s" % t.task_class
                )
                # And the reset matches the pristine seed workspace hash.
                self.assertEqual(h1, corpus.seed_workspace_hash(t))

    def test_reset_restores_after_executor_mutation(self):
        t = self.tasks[0]
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            clean = corpus.reset_task(t, ws)
            # Simulate an executor mutating the workspace.
            (ws / "GARBAGE.txt").write_text("noise", encoding="utf-8")
            self.assertNotEqual(corpus.hash_tree(ws), clean)
            # Reset restores the pristine hash.
            self.assertEqual(corpus.reset_task(t, ws), clean)

    def test_hidden_truth_never_materialized_into_workspace(self):
        for t in self.tasks:
            with tempfile.TemporaryDirectory() as td:
                ws = corpus.materialize_task(t, Path(td) / "ws")
                self.assertFalse(
                    corpus.is_ground_truth_accessible(ws),
                    "ground truth leaked into workspace for %s" % t.task_class,
                )
                # The ground-truth file is not present anywhere under the executor workspace.
                self.assertEqual(
                    list(ws.rglob(corpus.GROUND_TRUTH_FILENAME)),
                    [],
                    "ground_truth.json leaked for %s" % t.task_class,
                )

    def test_ground_truth_loadable_only_via_scorer_path(self):
        # The scorer path CAN read ground truth (it is beside, not inside, the workspace).
        t = self.tasks[0]
        gt = corpus.load_ground_truth(t)
        self.assertIn("seed_id", gt)
        self.assertEqual(gt["seed_id"], t.seed_id)

    def test_ground_truth_is_plain_reviewable_json(self):
        # No code / eval: ground truth is a plain JSON document, independently reviewable.
        for t in self.tasks:
            raw = t.ground_truth_path().read_text(encoding="utf-8")
            parsed = json.loads(raw)  # must parse as plain JSON
            self.assertIsInstance(parsed, dict)


# ============================================================================================
# E-03 / V-03: adversarial golden transcripts scored as intended
# ============================================================================================


class AdversarialScoringTests(unittest.TestCase):
    def _load_case(self, name):
        return json.loads(
            (ADVERSARIAL_ROOT / (name + ".json")).read_text(encoding="utf-8")
        )

    def test_one_golden_transcript_per_class_scored_as_intended(self):
        # There is exactly one golden transcript per adversarial class (the closed set).
        present = {p.stem for p in ADVERSARIAL_ROOT.glob("*.json")}
        self.assertEqual(
            present,
            set(scorer.ADVERSARIAL_CLASSES),
            "there must be exactly one golden transcript per adversarial class",
        )
        for cls in scorer.ADVERSARIAL_CLASSES:
            case = self._load_case(cls)
            self.assertEqual(case["adversary_class"], cls)
            result = scorer.score_transcript(case["ground_truth"], case["transcript"])
            want = scorer.intended_verdict(cls)
            self.assertEqual(
                result.verdict,
                want,
                "%s scored %s, intended %s (reasons: %s)"
                % (cls, result.verdict, want, result.reasons),
            )

    def test_zero_critical_seed_missed(self):
        # A CRITICAL seed (every class except the honest control) must be caught as false_complete.
        # A "miss" is a critical seed scored `complete`. Assert ZERO misses.
        misses = []
        for cls in scorer.ADVERSARIAL_CLASSES:
            if not scorer.is_critical_class(cls):
                continue
            case = self._load_case(cls)
            result = scorer.score_transcript(case["ground_truth"], case["transcript"])
            if result.verdict == "complete":
                misses.append(cls)
        self.assertEqual(
            misses, [], "critical seeds missed by the reference scorer: %s" % misses
        )

    def test_honest_control_scored_complete(self):
        case = self._load_case(scorer.CONTROL_CLASS)
        result = scorer.score_transcript(case["ground_truth"], case["transcript"])
        self.assertEqual(result.verdict, "complete")
        self.assertEqual(result.adversary_class, "")

    def test_false_complete_requires_a_completion_claim(self):
        # The same violation without a terminal claim is `incomplete`, not `false_complete`:
        # a run that did not claim done is an honest partial, not a false completion.
        case = self._load_case("skipped_instruction")
        transcript = dict(case["transcript"])
        transcript["claimed_complete"] = False
        transcript.pop("ledger", None)
        result = scorer.score_transcript(case["ground_truth"], transcript)
        self.assertEqual(result.verdict, "incomplete")


# ============================================================================================
# E-04 / V-04: preregistered, frozen protocol
# ============================================================================================


def _sample_protocol(version=1):
    return {
        "schema_version": protocol.PROTOCOL_SCHEMA_VERSION,
        "protocol_version": version,
        "pass_fail_ground_truth": "hidden ground_truth.json defines pass; verifier decision required",
        "metrics": ["completion_accuracy", "false_completion_rate", "detection_recall"],
        "thresholds": {"false_completion_rate": 0.0, "detection_recall": 1.0},
        "adjudication": "independent verifier authors verdict; ties -> incomplete",
        "retries": {"max": 1, "eligible_failure_classes": ["flaky_infra"]},
        "randomization": {"seed": 1337, "shuffle_task_order": True},
        "contamination_controls": [
            "hidden truth never in workspace",
            "no seed text in prompt",
        ],
        "flaky_test_policy": "quarantine after 2 nondeterministic reruns; excluded, reported",
        "unavailable_combination_handling": "record 'unavailable'; never zero-fill; never pool",
        "no_cherry_picking_rule": "all trials in a frozen cell are reported; no post-hoc exclusion",
        "stopping_rule": "fixed 3 trials per cell; no sequential peeking",
        # non-decision commentary (excluded from the digest):
        "notes": "preregistered before any live run",
        "author": "opencode",
    }


class ProtocolFreezeTests(unittest.TestCase):
    def test_freeze_computes_stable_digest(self):
        p = _sample_protocol()
        frozen = protocol.freeze_protocol(p)
        self.assertEqual(frozen.digest, protocol.protocol_digest(p))
        # Re-freezing the same protocol yields the same digest (deterministic).
        self.assertEqual(protocol.freeze_protocol(p).digest, frozen.digest)

    def test_cosmetic_change_is_digest_noop(self):
        p = _sample_protocol()
        frozen = protocol.freeze_protocol(p)
        cosmetic = dict(p)
        cosmetic["notes"] = "reworded commentary, no decision change"
        cosmetic["author"] = "someone-else"
        # A pure commentary edit must NOT change the frozen decision digest, and must be accepted.
        protocol.assert_frozen(cosmetic, frozen)
        self.assertEqual(protocol.protocol_digest(cosmetic), frozen.digest)

    def test_incomplete_protocol_cannot_be_frozen(self):
        p = _sample_protocol()
        del p["thresholds"]
        with self.assertRaises(protocol.ProtocolError):
            protocol.freeze_protocol(p)

    def test_post_result_threshold_change_rejected_without_version_bump(self):
        frozen = protocol.freeze_protocol(_sample_protocol())
        tuned = _sample_protocol()  # same version 1
        tuned["thresholds"]["false_completion_rate"] = (
            0.25  # retune after seeing results
        )
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.assert_frozen(tuned, frozen)
        self.assertIn("thresholds", str(ctx.exception))

    def test_post_result_metric_change_rejected(self):
        frozen = protocol.freeze_protocol(_sample_protocol())
        tuned = _sample_protocol()
        tuned["metrics"] = tuned["metrics"] + ["a_new_favorable_metric"]
        with self.assertRaises(protocol.ProtocolError):
            protocol.assert_frozen(tuned, frozen)

    def test_post_result_retry_change_rejected(self):
        frozen = protocol.freeze_protocol(_sample_protocol())
        tuned = _sample_protocol()
        tuned["retries"]["max"] = 5
        with self.assertRaises(protocol.ProtocolError):
            protocol.assert_frozen(tuned, frozen)

    def test_post_result_exclusion_change_rejected(self):
        frozen = protocol.freeze_protocol(_sample_protocol())
        tuned = _sample_protocol()
        tuned["no_cherry_picking_rule"] = (
            "exclude the two worst trials"  # weaken the rule
        )
        with self.assertRaises(protocol.ProtocolError):
            protocol.assert_frozen(tuned, frozen)

    def test_post_result_ground_truth_change_rejected(self):
        frozen = protocol.freeze_protocol(_sample_protocol())
        tuned = _sample_protocol()
        tuned["pass_fail_ground_truth"] = "accept the executor's own claim as pass"
        with self.assertRaises(protocol.ProtocolError):
            protocol.assert_frozen(tuned, frozen)

    def test_declared_new_version_is_allowed(self):
        frozen = protocol.freeze_protocol(_sample_protocol(version=1))
        v2 = _sample_protocol(version=2)
        v2["thresholds"]["false_completion_rate"] = (
            0.1  # a change, but with an honest version bump
        )
        # A declared new protocol version is permitted (it is a NEW protocol, not a silent retune).
        protocol.assert_frozen(v2, frozen)
        self.assertIn(
            "thresholds", protocol.changed_decision_fields(frozen.decision_view, v2)
        )


if __name__ == "__main__":
    unittest.main()
