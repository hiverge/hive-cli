
.PHONY: lint
lint:
	ruff check .

.PHONY: format
format:
	ruff check --fix .
	ruff format .
