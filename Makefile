# Convenience targets for the agent-workflows framework. The one that matters is `test`:
# it is discoverable by the framework's own `verify` workflow (run_checks.py scans the
# Makefile), so `/verify` can find and run the self-tests here - the framework dogfooding
# its own evidence layer.

.PHONY: test version

test:
	python3 -m unittest discover -s tests -t .

version:
	@cat .agents/workflows/VERSION
