# Convenience targets for the agent-workflows framework. The one that matters is `test`:
# it is discoverable by the framework's own `verify` workflow (run_checks.py scans the
# Makefile), so `/verify` can find and run the self-tests here - the framework dogfooding
# its own evidence layer.

.PHONY: test version version-file

test:
	python3 -m unittest discover -s tests -t .

# Print the RESOLVED version (git-tag-driven; dirty/distance-aware).
version:
	@python3 -c "import versioning, pathlib; print(versioning.resolve_version(pathlib.Path('.')))"

# Regenerate the tracked VERSION file from the git tag. VERSION is a DERIVED artifact;
# do not hand-edit it. Run this on a clean, tagged tree to bake the release version
# (e.g. 1.0.0); on a dirty/ahead tree it writes a .devN string.
version-file:
	@python3 -c "import versioning, pathlib; \
p = pathlib.Path('.agents/workflows/VERSION'); \
v = versioning.resolve_version(pathlib.Path('.')); \
p.write_text(v + '\n', encoding='utf-8'); \
print('wrote', p, '->', v)"
