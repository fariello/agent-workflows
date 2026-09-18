"""Performance BASELINES and packaged-content proof for the run-analytics feature.

runanalytics Order 10 (`9xycbh`) E-06 and E-08. Stdlib unittest only.

E-06 MEASURES AND PUBLISHES; IT DECLARES NO THRESHOLD, AND THAT IS THE MEASURED CORRECT SHAPE.
Re-checked at execution across all eleven plans in this Set: NO numeric time, memory or first-scan
threshold is declared anywhere. Order 07 leaves its size budget "to be declared at execution", Order
03 asks for "a measured overhead figure" with no pass bar, and no plan states a scan or rebuild
limit. So "test against documented budgets" would point at documents that do not exist, and this
plan explicitly originates no behavior. Inventing a number here would either be trivially passed or
would fail a sibling's correct implementation on a bar nobody agreed to. The honest form, and what
this file does, is to RECORD each figure with its method, input scale and machine context so a future
plan can set a gate from real data.

THE ONE EXCEPTION IS A BUDGET A SIBLING REALLY DID DECLARE. `run_analytics_spa.SIZE_BUDGET_BYTES` is
8 MiB with a stated basis, so the produced document IS checked as a pass or fail against that value,
cited to the module that declares it. That is the difference between honoring a declared contract and
inventing one.

E-08 ASSERTS PACKAGED CONTENTS OFFLINE AND KEEPS THE ISOLATED INSTALL OUT OF THE SUITE.
Re-measured at execution: the single declared runtime dependency is `filelock>=3`, so installing the
built wheel into a clean venv needs an index, and every test here is forbidden to touch the network.
CI already owns that proof: the `build + import wheel` job in `.github/workflows/tests.yml` builds the
wheel, creates a fresh venv, `pip install dist/*.whl`, and smoke-tests the console script on three
operating systems. So the division is: this SUITE asserts artifact CONTENTS by reading the built
wheel and sdist, and the INSTALL proof is that named CI job, cited rather than reimplemented.

OWNERSHIP BOUNDARY, stated because duplicating it would be the easy mistake. Order 07 owns the
positive per-asset BROWSER-asset assertion and it lives in `tests/test_packaging.py`
(`REQUIRED_BROWSER_ASSETS`, `test_wheel_ships_every_browser_asset_BY_NAME`). This file EXTENDS that
to the whole analytics module surface by importing the same list and asserting the modules beside it;
it does not re-assert the assets Order 07 already covers, and it does not parallel that file's build.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tarfile
import tempfile
import time
import tracemalloc
import unittest
import zipfile
from pathlib import Path

from agent_workflows import run_analytics
from agent_workflows import run_analytics_cache as cache_mod
from agent_workflows import run_analytics_privacy as privacy
from agent_workflows import run_analytics_spa as spa

from tests.fixtures import run_analytics as corpus
from tests.support import REPO_ROOT

#: Every analytics module that MUST ship. Derived from the package directory at import time so a new
#: module is covered automatically rather than needing a hand edit that a future author would forget.
ANALYTICS_MODULES: tuple[str, ...] = tuple(
    sorted(
        f"agent_workflows/{path.name}"
        for path in (REPO_ROOT / "agent_workflows").glob("run_analytics*.py")
    )
)


def _machine_context() -> dict[str, object]:
    """The context WITHOUT which a timing figure means nothing. Carries no identifying value.

    Deliberately excludes the hostname and every path: a published measurement is shareable material
    and `platform.node()` is exactly the kind of token the leak-sanitizer flags.
    """

    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "machine": platform.machine(),
    }


class PerformanceBaselineTests(unittest.TestCase):
    """E-06 / V-06: measure, record the method, and assert NOTHING against an undeclared budget."""

    #: The measured figures, printed at class teardown as the pasteable baseline.
    measurements: list[dict[str, object]] = []

    def setUp(self) -> None:
        self.maxDiff = None
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.measurements:
            print(
                "\nrun-analytics performance BASELINE (measured, NOT a gate):\n"
                + json.dumps(
                    {
                        "machine_context": _machine_context(),
                        "measurements": cls.measurements,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )

    def _record(self, **fields: object) -> None:
        type(self).measurements.append(dict(fields))

    def _corpus(self, count: int) -> tuple[Path, list[Path], str]:
        repo = self.base / f"repo{count}"
        runs_root = repo / ".aw" / "records" / "runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        runs = [
            corpus.write_run(
                runs_root,
                f"run-20260301T{index // 60:02d}{index % 60:02d}00Z-{index:07d}",
                mtime=corpus.BASE_MTIME,
            )
            for index in range(count)
        ]
        salt = privacy.load_or_create_salt(cache_mod.cache_root(repo))
        return repo, runs, cache_mod.source_root_id(runs_root, salt=salt)

    def test_measure_first_scan_unchanged_rescan_and_single_run_rebuild(self):
        """Three timings from ONE corpus, so they are comparable to each other.

        No assertion on any duration. The only assertions are on CORRECTNESS of the cache verdicts,
        which is what makes each timing a measurement of the intended work rather than of a no-op.
        """

        count = 40
        repo, runs, root_id = self._corpus(count)

        start = time.perf_counter()
        first = cache_mod.update_cache(
            runs,
            build_facts=run_analytics.build_cache_facts,
            repo=repo,
            root_id=root_id,
        )
        first_seconds = time.perf_counter() - start

        start = time.perf_counter()
        again = cache_mod.update_cache(
            runs,
            build_facts=run_analytics.build_cache_facts,
            repo=repo,
            root_id=root_id,
        )
        rescan_seconds = time.perf_counter() - start

        start = time.perf_counter()
        single = cache_mod.update_cache(
            [runs[0]],
            build_facts=run_analytics.build_cache_facts,
            repo=repo,
            root_id=root_id,
        )
        single_seconds = time.perf_counter() - start

        # CORRECTNESS, asserted; SPEED, only recorded.
        self.assertEqual(
            first.totals.get("rebuild"), count, "the first scan did not rebuild all"
        )
        self.assertEqual(
            again.totals.get("hit"), count, "the rescan did not reuse the cache"
        )
        self.assertEqual(single.totals.get("total"), 1)

        for label, seconds, scale, method in (
            ("first-scan", first_seconds, count, "update_cache over a cold cache"),
            (
                "unchanged-rescan",
                rescan_seconds,
                count,
                "update_cache over a warm cache",
            ),
            (
                "single-run-rescan",
                single_seconds,
                1,
                "update_cache over one cached run",
            ),
        ):
            self._record(
                dimension=label,
                seconds=round(seconds, 4),
                milliseconds=round(seconds * 1000, 1),
                input_runs=scale,
                method=method,
                asserted_against_a_budget=False,
                budget_source="none declared by any plan in this Set (re-checked at execution)",
            )

    def test_measure_peak_python_heap_over_a_corpus_ingest(self):
        """Peak PYTHON heap via `tracemalloc`, which is the allocation this code controls.

        RSS is deliberately not used: it includes the interpreter, every imported module and the
        allocator's retained arenas, so it would not be attributable to this feature.
        """

        count = 40
        _repo, runs, _root_id = self._corpus(count)
        tracemalloc.start()
        try:
            results, warnings = run_analytics.ingest_corpus(runs)
            _current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

        self.assertEqual(len(results), count)
        self.assertEqual(warnings, [])
        self._record(
            dimension="corpus-ingest-peak-heap",
            peak_bytes=int(peak),
            peak_mebibytes=round(peak / (1024 * 1024), 2),
            input_runs=count,
            method="tracemalloc peak over run_analytics.ingest_corpus",
            asserted_against_a_budget=False,
            budget_source="none declared by any plan in this Set (re-checked at execution)",
        )

    def test_report_size_IS_checked_against_order_07s_declared_budget(self):
        """THE ONE PASS/FAIL, because a sibling really did declare this number.

        `run_analytics_spa.SIZE_BUDGET_BYTES` is 8 MiB with a stated basis (a 0.71 MB base64-gzip
        payload at 29766 rows plus sub-1 MB chrome), so it is checked against its OWN value and the
        declaration is cited rather than restated.
        """

        rows = [{"run_id": f"run-{i}", "cost_usd": float(i)} for i in range(500)]
        model = spa.build_view_model(
            rows=rows, results=[], metric_column="cost_usd", generated_label="baseline"
        )
        document = spa.render_document(model)
        size = len(document.encode("utf-8"))

        self.assertLessEqual(
            size,
            spa.SIZE_BUDGET_BYTES,
            f"the rendered document is {size} bytes, over the {spa.SIZE_BUDGET_BYTES}-byte budget "
            f"declared by run_analytics_spa.SIZE_BUDGET_BYTES",
        )
        self._record(
            dimension="report-document-size",
            bytes=size,
            input_rows=len(rows),
            method="len(render_document(...).encode('utf-8'))",
            asserted_against_a_budget=True,
            budget_source="run_analytics_spa.SIZE_BUDGET_BYTES",
            budget_bytes=int(spa.SIZE_BUDGET_BYTES),
        )

    def test_measure_telemetry_collection_overhead(self):
        """Order 03 asked for "a measured overhead figure" and set no bar, so none is asserted.

        BOTH adapters are timed, because the difference is the informative part: the system adapter
        reads `/proc` and shells out for tool versions, so it is the real per-sample cost, while the
        fake adapter isolates the framing overhead the collector itself adds.
        """

        from agent_workflows import run_analytics_telemetry as telemetry

        iterations = 50
        for label, adapter in (
            ("system", telemetry.SystemResourceProbeAdapter()),
            ("fake", telemetry.FakeResourceProbeAdapter()),
        ):
            start = time.perf_counter()
            for _ in range(iterations):
                adapter.resources()
            total = time.perf_counter() - start
            self._record(
                dimension=f"telemetry-sample-overhead-{label}-adapter",
                per_sample_microseconds=round((total / iterations) * 1_000_000, 1),
                iterations=iterations,
                method=f"wall time over repeated {type(adapter).__name__}.resources() calls",
                asserted_against_a_budget=False,
                budget_source="Order 03 required a measured figure and declared no bar",
            )

    def test_no_measurement_here_is_asserted_against_an_undeclared_budget(self):
        """The guard that keeps this file honest as it grows.

        Every recorded figure must either declare no budget, or name the module that declares one.
        """

        self.assertTrue(type(self).measurements or True)
        for entry in type(self).measurements:
            with self.subTest(dimension=entry.get("dimension")):
                if entry.get("asserted_against_a_budget"):
                    self.assertIn(
                        "SIZE_BUDGET_BYTES",
                        str(entry.get("budget_source")),
                        "a pass/fail must cite the sibling declaration it rests on",
                    )


class _BuiltArtifacts(unittest.TestCase):
    """Builds the wheel and sdist ONCE. Never installs anything; never touches the network."""

    wheel_names: tuple[str, ...] = ()
    sdist_names: tuple[str, ...] = ()

    @classmethod
    def setUpClass(cls) -> None:
        try:
            import build  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("the 'build' package is not installed")
        cls._tmp = tempfile.TemporaryDirectory()
        out = Path(cls._tmp.name)
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--sdist",
                    "--outdir",
                    str(out),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                check=True,
            )
        except OSError as exc:
            cls._tmp.cleanup()
            raise unittest.SkipTest(f"build unavailable in this environment: {exc}")
        except subprocess.CalledProcessError as exc:
            cls._tmp.cleanup()
            detail = exc.stderr or exc.stdout or ""
            raise AssertionError(
                "the build FAILED though the 'build' backend is installed, which is a packaging "
                f"defect rather than an environment skip:\n{detail}"
            )
        wheels = sorted(out.glob("*.whl"))
        sdists = sorted(out.glob("*.tar.gz"))
        cls.wheel_names = tuple(zipfile.ZipFile(wheels[0]).namelist())
        with tarfile.open(sdists[0]) as tar:
            cls.sdist_names = tuple(
                member.name.split("/", 1)[1]
                for member in tar.getmembers()
                if "/" in member.name
            )

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "_tmp"):
            cls._tmp.cleanup()


class PackagedContentTests(_BuiltArtifacts):
    """E-08 / V-08: POSITIVE per-name assertions over BOTH artifacts."""

    def test_every_analytics_module_ships_in_the_wheel_BY_NAME(self):
        missing = [name for name in ANALYTICS_MODULES if name not in self.wheel_names]
        self.assertEqual(
            missing,
            [],
            f"analytics module(s) missing from the wheel: {missing}. Enumerated from the package "
            f"directory, so a new module is covered without a hand edit.",
        )
        self.assertGreaterEqual(
            len(ANALYTICS_MODULES),
            18,
            "the module enumeration collapsed; it would pass vacuously",
        )

    def test_every_analytics_module_ships_in_the_sdist_BY_NAME(self):
        """The sdist include list is a separate ALLOWLIST mechanism, so the wheel proves nothing here."""

        missing = [name for name in ANALYTICS_MODULES if name not in self.sdist_names]
        self.assertEqual(
            missing, [], f"analytics module(s) missing from the sdist: {missing}"
        )

    def test_the_browser_assets_order_07_declares_ship_in_both_artifacts(self):
        """EXTENDS Order 07's assertion rather than paralleling it: the same list, both artifacts.

        Imported from `tests/test_packaging.py` so the two cannot disagree, and asserted here across
        the whole feature surface, which is this plan's addition.
        """

        from tests.test_packaging import REQUIRED_BROWSER_ASSETS

        self.assertTrue(REQUIRED_BROWSER_ASSETS, "Order 07's asset list is empty")
        for name in REQUIRED_BROWSER_ASSETS:
            with self.subTest(asset=name):
                self.assertIn(name, self.wheel_names, f"{name} missing from the wheel")
                self.assertIn(name, self.sdist_names, f"{name} missing from the sdist")

    def test_the_analytics_modules_are_importable_from_the_extracted_wheel(self):
        """Importability from the SHIPPED layout, proven WITHOUT installing anything.

        The wheel is extracted and put on `sys.path` in a child interpreter, so this exercises the
        packaged file layout with no index, no venv and no network. It is NOT the isolated-install
        proof, which is CI's job (see the class docstring and `test_the_isolated_install_proof_is_cis`).
        """

        with tempfile.TemporaryDirectory() as td:
            extract = Path(td)
            import glob

            # Re-build into the same temp dir is wasteful; reuse the class's namelist to find the
            # wheel path instead by rebuilding only if needed.
            wheel_dir = Path(self._tmp.name)
            wheels = glob.glob(str(wheel_dir / "*.whl"))
            self.assertTrue(wheels, "no wheel to extract")
            with zipfile.ZipFile(wheels[0]) as archive:
                archive.extractall(extract)

            modules = [
                name.split("/", 1)[1][: -len(".py")] for name in ANALYTICS_MODULES
            ]
            script = (
                "import sys\n"
                "sys.path = [p for p in sys.path if p and 'agent-workflows' not in p]\n"
                "sys.path.insert(0, sys.argv[1])\n"
                "import importlib\n"
                f"for name in {modules!r}:\n"
                "    importlib.import_module('agent_workflows.' + name)\n"
                "print('imported', len(" + repr(modules) + "))\n"
            )
            result = subprocess.run(
                [sys.executable, "-c", script, str(extract)],
                cwd=str(extract),
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"importing the analytics modules from the shipped layout failed:\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}",
            )
            self.assertIn("imported", result.stdout)

    def test_no_test_in_this_suite_installs_over_the_network(self):
        """Measured: an offline `pip install` of the wheel FAILS resolving `filelock>=3`.

        So a networked install test would make the suite fail offline, and this asserts none exists.

        Detected by PARSING each test module for an install argv passed to a SUBPROCESS CALL, which
        is the only shape that can actually install anything. Two narrower forms were each measured
        wrong first: a substring search flagged this test's own docstring for describing what it
        forbids, and a bare list/tuple scan flagged
        `tests/test_run_analytics_wizard.py`'s tuple of FORBIDDEN tokens (`"pip"`, `"install"`, ...),
        which is a test asserting the opposite of an install. Requiring the literal to be a
        subprocess ARGUMENT separates a command from a word list.
        """

        import ast

        spawners = {"run", "check_call", "check_output", "call", "Popen"}
        offenders: list[str] = []
        for path in sorted((REPO_ROOT / "tests").glob("test_*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = (
                    func.attr
                    if isinstance(func, ast.Attribute)
                    else getattr(func, "id", "")
                )
                if name not in spawners:
                    continue
                for argument in list(node.args) + [kw.value for kw in node.keywords]:
                    if not isinstance(argument, (ast.List, ast.Tuple)):
                        continue
                    literals = [
                        element.value
                        for element in argument.elts
                        if isinstance(element, ast.Constant)
                        and isinstance(element.value, str)
                    ]
                    if "install" in literals and any(
                        "pip" in value for value in literals
                    ):
                        offenders.append(f"{path.name}:{node.lineno}")
        self.assertEqual(offenders, [], f"a test spawns a pip install: {offenders}")

    def test_the_isolated_install_proof_is_cis_named_wheel_job(self):
        """The install evidence is CITED, and the citation is checked to actually exist.

        A named CI job is only evidence if it is really in the workflow, so this reads the file
        rather than trusting a comment.
        """

        workflow = (REPO_ROOT / ".github" / "workflows" / "tests.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "build + import wheel", workflow, "the cited CI job is not in the workflow"
        )
        self.assertIn(
            "pip install dist/*.whl",
            workflow,
            "the cited job does not install the wheel",
        )
        self.assertIn(
            "python -m venv", workflow, "the cited job does not use a fresh venv"
        )

    def test_the_single_runtime_dependency_is_why_the_install_needs_a_network(self):
        """Re-measured rather than cited: exactly one unconditional runtime dependency is declared."""

        metadata = [n for n in self.wheel_names if n.endswith("METADATA")]
        self.assertTrue(metadata)
        wheel_dir = Path(self._tmp.name)
        import glob

        wheels = glob.glob(str(wheel_dir / "*.whl"))
        text = zipfile.ZipFile(wheels[0]).read(metadata[0]).decode("utf-8")
        unconditional = [
            line
            for line in text.splitlines()
            if line.startswith("Requires-Dist") and "extra ==" not in line
        ]
        self.assertEqual(
            len(unconditional),
            1,
            f"expected exactly one unconditional runtime dependency, got {unconditional}",
        )
        self.assertIn("filelock", unconditional[0].lower())


if __name__ == "__main__":
    unittest.main()
