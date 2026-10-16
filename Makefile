# Convenience targets for the agent-workflows framework. The one that matters is `test`:
# it is discoverable by the framework's own `verify` workflow (run_checks.py scans the
# Makefile), so `/verify` can find and run the self-tests here - the framework dogfooding
# its own evidence layer.

.PHONY: install-dev test test-all test-release test-serial typecheck version version-file

# Run the configured narrowed static type gate over agent_workflows/.
# CI-only gate in default posture; see CONTRIBUTING.md for details.
typecheck:
	python3 -m mypy agent_workflows

# Install everything needed to work on and test this repo. Run once after cloning.
install-dev:
	python3 -m pip install -e '.[test]'

# Pytest-xdist runs the routine and release gates with at most six workers and
# half the available CPUs. The root conftest installs xdist if needed.
# pytest and pytest-xdist are TEST-ONLY dependencies (the `test` extra in pyproject.toml):
# not imported at runtime and not shipped in the wheel.
# Routine gate: bare `python3 -m pytest` runs the core tier (budgeted under 30s wall time on 6 workers)
# and serves as the runner merge gate; an explicit path runs everything non-slow it names.
# Pytest addopts keeps slow and live-record tests out of this run.
test:
	python3 -m pytest

# Thorough suite including the `slow` subprocess/integration tests (CI runs the fast
# suite plus an advisory slow step). Use `make test-all` or `aw suite --thorough`
# for pre-push, CI, and release-review before shipping.
# `-m ""` clears the default `not slow and not livecorpus` filter (including `slow` and `livecorpus`); still parallel.
test-all:
	python3 -m pytest tests/ -m ''

test-release: test-all

# Escape hatch: explicit-only serial stdlib runner (no third-party deps), runs EVERY test
# (unittest has no marker filter). Use ONLY when deliberately debugging a test-isolation
# issue that -n auto would mask. `make test` never runs this.
test-serial:
	python3 -m unittest discover -s tests -t .

# Print the RESOLVED version (git-tag-driven; dirty/distance-aware).
version:
	@python3 -c "import versioning, pathlib; print(versioning.resolve_version(pathlib.Path('.')))"

# Regenerate the tracked VERSION file. VERSION is a DERIVED artifact; do not hand-edit it.
# Two modes:
#   make version-file                 -> bake the RESOLVED version (git-tag-driven; on a
#                                        clean tagged tree this is the release semver, on a
#                                        dirty/ahead tree a .devN string).
#   make version-file VERSION=1.2.1   -> bake an EXPLICIT intended release version. Used at
#                                        release time to bake VERSION and commit it BEFORE
#                                        tagging (bake-then-tag), so the tag's tree contains a
#                                        VERSION equal to its own tag and installs stamp the
#                                        correct number (DECISIONS: the stale-VERSION fix). The
#                                        value must be a plain release version (X.Y.Z or an
#                                        X.Y.Z-rc.N / X.Y.ZrcN pre-release); it is validated.
version-file:
	@python3 -c "import versioning, pathlib, re, sys; \
override = '$(VERSION)'.strip(); \
valid = re.match(r'^\d+\.\d+\.\d+(-?rc\.?\d+)?$$', override) if override else None; \
sys.exit('error: VERSION=%r is not a valid release version (expected X.Y.Z or X.Y.Z-rc.N)' % override) if (override and not valid) else None; \
p = pathlib.Path('.aw/system/VERSION'); \
v = override if override else versioning.resolve_version(pathlib.Path('.')); \
p.write_text(v + '\n', encoding='utf-8'); \
idx = pathlib.Path('.aw/system/workflows/index.md'); \
t = idx.read_text(encoding='utf-8') if idx.is_file() else None; \
t2 = (re.sub(r'<!-- WORKFLOWS-VERSION: [^>]*-->', '<!-- WORKFLOWS-VERSION: %s -->' % v, t, count=1) if t else t); \
t2 = (re.sub(r'(?m)^Version: \`[^\`]*\`', 'Version: \`%s\`' % v, t2, count=1) if t2 else t2); \
idx.write_text(t2, encoding='utf-8') if (t2 is not None and t2 != t) else None; \
print('wrote', p, '->', v, '(+ synced index.md stamp)' if (t2 is not None and t2 != t) else '')"
