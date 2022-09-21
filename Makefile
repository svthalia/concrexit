.POSIX:
.SUFFIXES:

PYTHONFILES := $(shell find website -name '*.py')
MIGRATIONS := $(shell find website -name '*.py' | grep migrations)
TEMPLATEFILES := $(shell find website -name '*.html')

PORT ?= 8000

ifdef CI
	POETRY_FLAGS := $(POETRY_FLAGS) --no-interaction --extras postgres
	BLACK_FLAGS := $(BLACK_FLAGS) --quiet
	DOCKER_FLAGS := $(DOCKER_FLAGS) --quiet
endif

help:
	@echo "\033[1mUSAGE\033[0m"
	@echo "  \033[4mmake\033[0m [options] <target>"
	@echo
	@echo "\033[1mOPTIONS\033[0m"
	@echo "The following options can be set with \033[4mmake\033[0m \033[0;32mOPTION\033[0m=\033[0;34mvalue\033[0m"
	@echo "  \033[0;32mPORT\033[0m=\033[0;34m$(PORT)\033[0m"
	@echo "  \033[0;32mPOETRY_FLAGS\033[0m=\033[0;34m$(POETRY_FLAGS)\033[0m"
	@echo "  \033[0;32mBLACK_FLAGS\033[0m=\033[0;34m$(BLACK_FLAGS)\033[0m"
	@echo
	@echo "\033[1mAVAILABLE TARGETS\033[0m"
	@grep '^[[:alnum:]_-]*:.* ##' $(MAKEFILE_LIST) \
	| sort | awk 'BEGIN {FS=":.* ## "}; {printf "  \033[0;36m%-25s\033[0m%s\n", $$1, $$2};'

.make:
	mkdir .make

run: .make/deps website/db.sqlite3 ## Run a local webserver on PORT
	poetry run website/manage.py runserver $(PORT)

.make/deps: .make poetry.lock pyproject.toml
	poetry install $(POETRY_FLAGS)
	@touch .make/deps

deps: .make/deps ## Install all the required dependencies

website/db.sqlite3: .make/deps $(MIGRATIONS)
	poetry run website/manage.py migrate

migrate: ## Run all database migrations
	poetry run website/manage.py migrate

migrations: ## Automatically create migration scripts
	poetry run website/manage.py makemigrations

superuser: .make/deps website/db.sqlite3 ## Create a superuser for your local concrexit
	poetry run website/manage.py createsuperuser

fixtures: .make/deps website/db.sqlite3 ## Create dummy database entries
	poetry run website/manage.py createfixtures -a

.make/fmt: .make .make/deps $(PYTHONFILES)
	poetry run black $(BLACK_FLAGS) website
	@touch .make/fmt

fmt: .make/fmt ## Format python code with black

blackcheck: .make/deps $(PYTHONFILES) ## Check if everything is formatted correctly
	poetry run black $(BLACK_FLAGS) --check website

.make/pylint: .make .make/deps $(PYTHONFILES)
	DJANGO_SETTINGS_MODULE=thaliawebsite.settings poetry run pylint website/**/*.py
	@touch .make/pylint

pylint: .make/pylint ## Check python code with pylint

.make/pydocstyle: .make .make/deps $(PYTHONFILES)
	poetry run pydocstyle --match-dir='(?!migrations).*' --add-ignore D100,D101,D102,D103,D104,D105,D106,D107 --add-select D212 website/

pydocstyle: .make/pydocstyle

.make/check: .make .make/deps $(PYTHONFILES)
	poetry run python website/manage.py check
	@touch .make/check

check: .make/check ## Run internal Django tests

.make/templatecheck: .make .make/deps $(TEMPLATEFILES)
	poetry run python website/manage.py templatecheck --project-only
	@touch .make/templatecheck

templatecheck: .make/templatecheck ## Test the templates

.make/migrationcheck: .make .make/deps $(PYTHONFILES)
	poetry run python website/manage.py makemigrations --no-input --check --dry-run
	@touch .make/migrationcheck

migrationcheck: .make/migrationcheck ## Check if migrations are created

.coverage: .make/deps $(PYTHONFILES)
	poetry run coverage run website/manage.py test website/

tests: .coverage ## Run tests with coverage

coverage: .coverage ## Generate a coverage report after running the tests
	poetry run coverage report --fail-under=100 --omit "website/registrations/urls.py" website/registrations/**.py
	poetry run coverage report --fail-under=100 --omit "website/payments/urls.py" website/payments/**.py
	poetry run coverage report

covhtml: .coverage ## Generate an HTML coverage report
	poetry run coverage html --directory=covhtml --no-skip-covered --title="Coverage Report"

.make/docsdeps: .make .make/deps
	poetry install $(POETRY_FLAGS) --extras "docs"
	@touch .make/docsdeps

apidocs: ## Generate API docs
	cd docs && poetry run sphinx-apidoc -M -f -o . ../website ../website/*/migrations ../website/*/tests* ../website/manage.py

.make/doctest: .make/docsdeps
	cd docs && poetry run sphinx-build -M doctest . _build

doctest: .make/doctest ## Run doctests

docs: ## Generate docs HTML files
	cd docs && poetry run sphinx-build -M html . _build

apidocscheck: apidocs # Check whether new apidocs are generated
	@git diff --name-only | grep 'docs/' >/dev/null && (echo "WARNING: you have uncommitted apidocs changes"; exit 1) || exit 0

.make/docker: .make
	docker build $(DOCKER_FLAGS) --build-arg "source_commit=$$(git rev-parse HEAD)" --tag "thalia/concrexit:$$(git rev-parse HEAD)" .

docker: .make/docker

lint: blackcheck pylint pydocstyle ## Run all linters

test: check templatecheck migrationcheck tests ## Run every kind of test

ci: blackcheck  pydocstyle coverage doctest docs apidocscheck ## Do all the checks the GitHub Actions CI does

clean: ## Remove all generated files
	rm -f .coverage website/db.sqlite3
	rm -rf website/media website/static docs/_build .make

.PHONY: ci help run deps migrate createsuperuser createfixtures fmt check \
		templatecheck migrationcheck tests coverage covhtml doctest docs \
		docker lint test clean pydocstyle apidocscheck
