################################################################################
# Makefile README
#
# This file abstracts some commonly used commands used to work on concrexit.  It
# also helps with commands you normally have to run in a specific order. This is
# useful to get started, because now you probably only have to remember make run
#
# The problem is that, while it's nice to have some magic make commands, you can
# get yourself stuck without knowing what you just did via make. By reading this
# explanation I hope you will get such a good knowledge of make and the commands
# it runs for you that you will be able to continue on your own.
#
# The `make` command line tool works by reading this Makefile you're reading now
# and then executing the recipe you specified. When you execute `make run`, make
# looks in this Makefile for the `run` recipe and works from there. If you don't
# specify anything after `make` on the command line,  it will look for the first
# recipe it finds. In this Makefile the default and first recipe is `help`. What
# is also possible is to place the default recipe you want somewhere else and to
# then explicitely specify it with .DEFAULT:
#
# Make recipes are called recipes because programmers sometimes like comparisons
# with cooking.  To be fair though,  just like with cooking recipies there is an
# important order to the steps you have to take.  And this ordering comes from a
# directed acyclic graph (DAG).  Nodes on the DAG are recipes and the edges from
# the graph specify a dependency between them.  In a Makefile the recipies start
# with a name and a colon and after the colon you write the dependencies for the
# recipe. For example in the `fmt` recipe, we can see that it requires .make/fmt
# to have been done first. The steps to execute this part of the recipe are then
# specified in the indented block.
#
# Make is mainly meant for creating new files, but in this Makefile we only have
# one good example of that.  It's the recipe for creating the website/db.sqlite3
# file.  It depends on the dependencies being installed and the migration files.
# Depending on other files---in this case it's migrations---means that this step
# will only be rerun if those other files have changed. Make looks at the change
# times or modification times of these files for this.
#
# Because only rerunning steps when needed is very useful, we abuse this feature
# by having sentinel files.  All the files in the .make directory are sentinels.
# These are empty files, which only serve the purpose of saving the modification
# time from when the recipe last ran.  A good example of a recipe that uses such
# a sentinel file is the deps recipe. You can see below in this file that it has
# a dependency on the .make/deps file. It also has a dependency on the pyproject
# and poetry.lock files.This means it will only rerun the recipe if one of those
# files changes.
#
# Besides make recipies which specify a file or sentinel file, we have some make
# recipies which should just always execute a bunch of commands.  These are more
# like scripts than recipies. In this Makefile there are a whole bunch of these,
# some of which are just a nice name for a sentinel file,  like `deps`, and some
# of which are just a simple script, like `clean`.  In make these recipies which
# don't create a file should be indicated by being declared .PHONY:. You can see
# see this declaration at the bottom of this file. What this means is  that make
# should not look for a file called clean in the root of the repository whenever
# it executes the `clean` recipe.
#
# It's not a super big deal if you forget to specify a recipe as `PHONY`, as the
# make tool will rerun that recipe whenever no file called `clean` is seen.  But
# it's nice to specify PHONY targets anyways,  as information for the reader, or
# in case a file called clean might be created some day.
#
# This has been the introduction of this Makefile. The rest of the Makefile will
# be littered with comments that explain more parts of the file. And if you want
# to learn more about all of this make stuff, you can read the manual or some of
# the blog posts that inspired me to make this Makefile:
#
# The Unreasonable Effectiveness of Makefiles:
# https://matt-rickard.com/the-unreasonable-effectiveness-of-makefiles
# A Tutorial on Portable Makefiles
# https://nullprogram.com/blog/2017/08/20/
# Why I Prefer Makefiles Over package.json Scripts
# https://spin.atomicobject.com/2021/03/22/makefiles-vs-package-json-scripts/
# The GNU make manual
# https://www.gnu.org/software/make/manual/html_node/index.html
################################################################################

# The .POSIX directive indicates that POSIX make behaviour should be used in
# cases where make implementations normally differ from POSIX behaviour.
.POSIX:
# An empty SUFFIXES directive indicates that default recipies for .c files and
# such should be ignored. More information here:
# https://www.gnu.org/software/make/manual/html_node/Suffix-Rules.html#Suffix-Rules
.SUFFIXES:

# Run a `find` command in the shell to collect the names of certain files.
# These are used in recipies as prerequisites later on. This means whenver these
# files change, make knows those recipies have to be rerun.
PYTHONFILES := $(shell find website -name '*.py')
MIGRATIONS := $(shell find website -name '*.py' | grep migrations)
TEMPLATEFILES := $(shell find website -name '*.html')

# A variable for the default port. Because this uses ?=, it's only set if not
# already specified on the command line. For example `make PORT=8080 run`
PORT ?= 8000

# The CI environment variable is defined whenever make is run in GitHub Actions.
# Environment variables are only used when they aren't defined in the Makefile:
# https://www.gnu.org/software/make/manual/html_node/Environment.html
ifdef CI
# These add to any existing POETRY_FLAGS variable, it doesn't replace existing
# flags.
	POETRY_FLAGS := $(POETRY_FLAGS) --no-interaction --with postgres
	BLACK_FLAGS := $(BLACK_FLAGS) --quiet
	DOCKER_FLAGS := $(DOCKER_FLAGS) --quiet
endif

# This help recipe might look very confusing, depending on how familiar you are
# with terminal color codes. The basic idea of this recipe is that it shows some
# help text, and then the list of recipes/targets you can use. Because it's the
# top recipe in this file, make uses it as the default when you don't specify
# a recipe on the command line.
#
# The commands in this recipe all start with @, this means `make` doesn't print
# this command when it's executing it. That would be a little redundant. The
# text this recipe print is littered with \033, which is the escape code for the
# ESC ascii character. All terminal style commands start with ESC[. Some of these
# are colors and some are bold or underscore. To learn about using colors in the
# terminal you can read this page:
# https://misc.flogisoft.com/bash/tip_colors_and_formatting
.PHONY: help
help:
	@echo "\033[1mUSAGE\033[0m"
	@echo "  \033[4mmake\033[0m [options] <target>"
	@echo
	@echo "\033[1mOPTIONS\033[0m"
	@echo "The following options can be set with \033[4mmake\033[0m \033[0;32mOPTION\033[0m=\033[0;34mvalue\033[0m"
# Print the current value of the PORT variable with $(PORT). This looks like a
# shell variable usage with $(PORT), but it's actually a make variable usage.
# To do a $(VAR) in the shell in a Makefile you have to type $$(VAR).
	@echo "  \033[0;32mPORT\033[0m=\033[0;34m$(PORT)\033[0m"
	@echo "  \033[0;32mPOETRY_FLAGS\033[0m=\033[0;34m$(POETRY_FLAGS)\033[0m"
	@echo "  \033[0;32mBLACK_FLAGS\033[0m=\033[0;34m$(BLACK_FLAGS)\033[0m"
	@echo
	@echo "\033[1mAVAILABLE TARGETS\033[0m"
# This is some shell trickery to print out all the documented recipes. The grep
# command filters all the recipes that have a ## documentation comment after it.
# You can run this in your terminal to see the output of the grep command:
#     grep '^[[:alnum:]_-]*:.* ##' Makefile
# The $(MAKEFILE_LIST) variable contains all the Makefiles that make has read
# in a list, but we only use one Makefile, so the command below is equivalent to
# the command above.
# Then this grepped list is sorted using sort.
# Then this sorted list is altered using awk. Awk splits the list based on the
# ##, then displays it nicely with spacing and colors.
	@grep '^[[:alnum:]_-]*:.* ##' $(MAKEFILE_LIST) \
	| sort | awk 'BEGIN {FS=":.* ## "}; {printf "  \033[0;36m%-25s\033[0m%s\n", $$1, $$2};'

# This just creates the .make dir which contains the sentinel files
.make:
	mkdir .make

# Before the steps from `run` can be executed first we must have created
# .make/deps and website/db.sqlite3
# This is also a PHONY target, because it doesn't create a file called `run`.
.PHONY: run
run: .make/deps website/db.sqlite3 ## Run a local webserver on PORT
	poetry run website/manage.py runserver $(PORT)

# Sentinel file remembers if this recipe was run after poetry.lock, pyproject.toml
# and .pre-commit-config.yaml where changed. If those files are changed again,
# this recipe is run again.
.make/deps: .make poetry.lock pyproject.toml .pre-commit-config.yaml
	poetry install $(POETRY_FLAGS)
	poetry run pre-commit install
	@touch .make/deps

# Nice name for the sentinel file
.PHONY: deps
deps: .make/deps ## Install all the required dependencies

# This recipe depends on all the migrations, which were collected above using
# `find`. If we have new or changed migrations, we have to run them again on the
# database!
website/db.sqlite3: .make/deps $(MIGRATIONS)
	poetry run website/manage.py migrate
	poetry run website/manage.py createcachetable

.PHONY: migrate
migrate: ## Run all database migrations
	poetry run website/manage.py migrate

.PHONY: migrations
migrations: ## Automatically create migration scripts
	poetry run website/manage.py makemigrations

.PHONY: superuser
superuser: .make/deps website/db.sqlite3 ## Create a superuser for your local concrexit
	poetry run website/manage.py createsuperuser

.PHONY: member
member: .make/deps website/db.sqlite3 ## Create a member for your local concrexit
	poetry run website/manage.py createmember

.PHONY: fixtures
fixtures: .make/deps website/db.sqlite3 ## Create dummy database entries
	poetry run website/manage.py createfixtures -a

# The BLACK_FLAGS variable from above is used here to optionally add some extra
# flags to the black command.
.make/fmt: .make .make/deps $(PYTHONFILES)
	poetry run isort website
	poetry run black $(BLACK_FLAGS) website
	@touch .make/fmt

.PHONY: fmt
fmt: .make/fmt ## Format python code with black

.PHONY: isortcheck
isortcheck: .make/deps $(PYTHONFILES) ## Check if python imports are sorted
	poetry run isort --check website

.PHONY: blackcheck
blackcheck: .make/deps $(PYTHONFILES) ## Check if everything is formatted correctly
	poetry run black $(BLACK_FLAGS) --check website

.PHONY: ruff
ruff: .make .make/deps $(PYTHONFILES) ## Check python linting with ruff.
	poetry run ruff check website

.make/check: .make .make/deps $(PYTHONFILES)
	poetry run python website/manage.py check
	@touch .make/check

.PHONY: check
check: .make/check ## Run internal Django tests

.make/templatecheck: .make .make/deps $(TEMPLATEFILES)
	poetry run python website/manage.py templatecheck --project-only
	@touch .make/templatecheck

.PHONY: templatecheck
templatecheck: .make/templatecheck ## Test the templates

.make/migrationcheck: .make .make/deps $(PYTHONFILES)
	poetry run python website/manage.py makemigrations --no-input --check --dry-run
	@touch .make/migrationcheck

.PHONY: migrationcheck
migrationcheck: .make/migrationcheck ## Check if migrations are created

.coverage: .make/deps $(PYTHONFILES)
	poetry run coverage run website/manage.py test website/

.PHONY: tests
tests: .coverage ## Run tests with coverage

.PHONY: coverage
coverage: .coverage ## Generate a coverage report after running the tests
	poetry run coverage report --fail-under=100 --omit "website/registrations/urls.py" website/registrations/**.py
	poetry run coverage report --fail-under=100 --omit "website/payments/urls.py" website/payments/**.py
	poetry run coverage report

.PHONY: covhtml
covhtml: .coverage ## Generate an HTML coverage report
	poetry run coverage html --directory=covhtml --no-skip-covered --title="Coverage Report"

.make/docsdeps: .make .make/deps
	poetry install $(POETRY_FLAGS) --with docs
	@touch .make/docsdeps

.PHONY: apidocs
apidocs: ## Generate API docs
	cd docs && poetry run sphinx-apidoc -M -f -o . ../website ../website/*/migrations ../website/*/tests* ../website/manage.py

.make/doctest: .make/docsdeps
	cd docs && poetry run sphinx-build -M doctest . _build

.PHONY: doctest
doctest: .make/doctest ## Run doctests

# This could be a recipe which checks the modification date of input files, but
# that would be too complicated and this isn't run that often anyways.
.PHONY: docs
docs: ## Generate docs HTML files
	cd docs && poetry run sphinx-build -M html . _build

.PHONY: apidocscheck
apidocscheck: apidocs # Check whether new apidocs are generated
	@git diff --name-only | grep 'docs/' >/dev/null && (echo "WARNING: you have uncommitted apidocs changes"; exit 1) || exit 0

.PHONY: graphs
graphs: ## Generate model graphs
	@echo "Generating full models graph"
	@poetry run website/manage.py graph_models --pydot -a -g -o full_models_graph.png
	@echo "Generating partial models graph"
	@poetry run website/manage.py graph_models --pydot -X LogEntry,ContentType,Permission,PermissionsMixin,AbstractUser,AbstractBaseUser,Group -o partial_models_graph.png

.make/docker: .make
	docker build $(DOCKER_FLAGS) --build-arg "source_commit=$$(git rev-parse HEAD)" --tag "thalia/concrexit:$$(git rev-parse HEAD)" .

.PHONY: docker
docker: .make/docker

.PHONY: lint
lint: isortcheck blackcheck ruff ## Run all linters

.PHONY: test
test: check templatecheck migrationcheck tests ## Run every kind of test

.PHONY: ci
ci: isortcheck blackcheck ruff coverage doctest docs apidocscheck ## Do all the checks the GitHub Actions CI does

# Sometimes you don't want make to do the whole modification time checking thing
# so this cleans up the whole repository and allows you to start over from
# scratch. If you just want to force rerun a make recipe, it's easiest to copy
# the commands in the recipe steps by hand.
.PHONY: clean
clean: ## Remove all generated files
	rm -f .coverage website/db.sqlite3
	rm -rf website/media website/static docs/_build .make
