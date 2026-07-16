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
p = pathlib.Path('.agents/workflows/VERSION'); \
v = override if override else versioning.resolve_version(pathlib.Path('.')); \
p.write_text(v + '\n', encoding='utf-8'); \
idx = pathlib.Path('.agents/workflows/index.md'); \
t = idx.read_text(encoding='utf-8') if idx.is_file() else None; \
t2 = (re.sub(r'<!-- WORKFLOWS-VERSION: [^>]*-->', '<!-- WORKFLOWS-VERSION: %s -->' % v, t, count=1) if t else t); \
t2 = (re.sub(r'(?m)^Version: \`[^\`]*\`', 'Version: \`%s\`' % v, t2, count=1) if t2 else t2); \
idx.write_text(t2, encoding='utf-8') if (t2 is not None and t2 != t) else None; \
print('wrote', p, '->', v, '(+ synced index.md stamp)' if (t2 is not None and t2 != t) else '')"
