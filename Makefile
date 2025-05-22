# Do not forget to configure pypi token:
# poetry config pypi-token.pypi <token>

.PHONY: publish
publish:
	poetry build
	poetry publish

.PHONY: format
format:
	ruff format .

.PHONY: lint
lint:
	ruff check . --fix
	mypy .

# Windows only
PHONY: kill
kill:
	TASKKILL /F /IM python.exe
