
.PHONY: lint
lint:
	ruff check .

.PHONY: format
format:
	ruff check --fix .
	ruff format .

.PHONY: test
test:
	mkdir -p test-reports && \
	. .venv/bin/activate && \
	PYTHONPATH=libs:$$PYTHONPATH pytest -v --junitxml=test-reports/hive-report.xml