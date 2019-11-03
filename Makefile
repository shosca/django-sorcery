PACKAGE=django_sorcery
FILES=$(shell find $(PACKAGE) -iname '*.py' ! -iname '__*')
VERSION=$(shell python setup.py --version)
NEXT=$(shell semver -i $(BUMP) $(VERSION))
DBS=\
	default_db \
	fromdbs \
	test \
	minimal \
	minimal_backpop
RESETDBS=$(addsuffix -resetdb,$(DBS))
COVERAGE_FLAGS?=--cov-report term-missing --cov-fail-under=100

.PHONY: help list docs $(FILES)


help:
	@for f in $(MAKEFILE_LIST) ; do \
		echo "$$f:" ; \
		grep -E '^[^[:space:]].*:.*?## .*$$' $$f | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' ; \
	done ; \

list:  ## list all possible targets
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build:  ## remove build artifacts
	find -name '*.sqlite3' -delete
	rm -rf build dist .eggs .mypy_cache .pytest_cache docs/_build *.egg*

clean-pyc:  ## remove Python file artifacts
	find -name '*.pyc' -delete
	find -name '*.pyo' -delete
	find -name '*~' -delete
	find -name '__pycache__' -delete

clean-test:  ## remove test and coverage artifacts
	rm -rf .tox .coverage htmlcov

%-resetdb:
	-psql -c "drop database $*;" -h localhost -U postgres
	-psql -c "create database $*;" -h localhost -U postgres

resetdb: $(RESETDBS)

lint:  ## run pre-commit hooks on all files
	if python -c "import sys; exit(1) if sys.version_info.major < 3 else exit(0)"; then \
		pre-commit run --all-files ; \
	fi

coverage: ## check code coverage quickly with the default Python
	py.test $(PYTEST_OPTS) \
		--cov=django_sorcery \
		$(COVERAGE_FLAGS) \
		tests

$(FILES):  ## helper target to run coverage tests on a module
	py.test $(PYTEST_OPTS) $(COVERAGE_FLAGS) \
		--cov=$(subst /,.,$(firstword $(subst ., ,$@))) $(subst $(PACKAGE),tests,$(dir $@))test_$(notdir $@)

test:  ## run tests
	py.test $(PYTEST_OPTS) tests django_sorcery

check:  ## run all tests
	tox

history: docs  ## generate HISTORY.rst
	gitchangelog > HISTORY.rst

docs:  ## generate docs
	$(MAKE) -C docs html

livedocs:  ## generate docs live
	$(MAKE) -C docs live

version:  # print version
	@python setup.py --version

bump: history
	@sed -i 's/$(VERSION)/$(NEXT)/g' $(PACKAGE)/__version__.py
	@sed -i 's/Next version (unreleased yet)/$(NEXT) ($(shell date +"%Y-%m-%d"))/g' HISTORY.rst
	@git add .
	@git commit -am "Bump version: $(VERSION) → $(NEXT)"

tag:  ## tags branch
	git tag -a $$(python setup.py --version) -m $$(python setup.py --version)

release: dist  ## package and upload a release
	twine upload dist/*

dist: clean  ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
