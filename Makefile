# Convenience targets for the agent-workflows framework. The one that matters is `test`:
# it is discoverable by the framework's own `verify` workflow (run_checks.py scans the
# Makefile), so `/verify` can find and run the self-tests here - the framework dogfooding
# its own evidence layer.

.PHONY: test test-serial version version-file

# Parallel by default: pytest-xdist spreads the suite across all CPUs (the install/
# uninstall tests are subprocess/IO bound and independent), cutting wall time ~5-8x
# (measured ~4:20 serial -> ~0:40 on a 12-core machine, identical results). `make test`
# is the canonical evidence command. Falls back to serial stdlib unittest when
# pytest/xdist are not installed, so a minimal env still works. pytest and pytest-xdist
# are TEST-ONLY dependencies (the `test` extra in pyproject.toml; D138): not imported at
# runtime and not shipped in the wheel.
test:
	@if python3 -c "import xdist" >/dev/null 2>&1; then \
		echo "running: pytest -n auto"; \
		python3 -m pytest tests/ -n auto -q; \
	else \
		echo "pytest-xdist not found; running serial unittest (pip install '.[test]' for parallel)"; \
		python3 -m unittest discover -s tests -t .; \
	fi

# Always-serial stdlib runner (no third-party deps). Kept as the guaranteed fallback.
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
