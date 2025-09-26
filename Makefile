PACKAGE_NAME = hiverge-cli

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

.PHONY: build
build:
	rm -rf dist/ build/ *.egg-info
	@echo "Building $(PACKAGE_NAME)..."
	pip install --upgrade build
	python -m build

.PHONY: publish
publish: build
	@echo "Publishing $(PACKAGE_NAME) to PyPI..."
	pip install --upgrade twine
	twine upload -u __token__ -p $(HIVERGE_PYPI_TOKEN) dist/*
