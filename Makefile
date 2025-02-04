APP_PATH = auth365
TESTS_PATH = tests

# Do not forget to configure pypi token:
# poetry config pypi-token.pypi <token>

.PHONY: publish
publish:
	poetry build
	poetry publish

.PHONY: format
format:
	ruff format $(APP_PATH) $(TESTS_PATH)

.PHONY: lint
lint:
	ruff check $(APP_PATH) $(TESTS_PATH) --fix
	mypy $(APP_PATH) --install-types

# Windows only
PHONY: kill
kill:
	TASKKILL /F /IM python.exe
