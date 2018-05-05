WATCH_EVENTS=modify,close_write,moved_to,create
PACKAGE=django_sorcery
FILES=$(shell find $(PACKAGE) -iname '*.py')

.PHONY: docs $(FILES)

init:  ## setup environment
	pip install pipenv
	pipenv install --dev

help:
	@for f in $(MAKEFILE_LIST) ; do \
		echo "$$f:" ; \
		grep -E '^[a-zA-Z_-%]+:.*?## .*$$' $$f | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' ; \
	done ; \

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build:  ## remove build artifacts
	find -name '*.sqlite3' -delete
	rm -rf build/ dist/ .eggs/
	rm -rf '*.egg-info'
	rm -rf '*.egg'

clean-pyc:  ## remove Python file artifacts
	find -name '*.pyc' -delete
	find -name '*.pyo' -delete
	find -name '*~' -delete
	find -name '__pycache__' -delete

clean-test:  ## remove test and coverage artifacts
	rm -rf .tox/ .coverage htmlcov/

lint:  ## run pre-commit hooks on all files
	pipenv run pre-commit run --files $$(git ls-files)

coverage: ## check code coverage quickly with the default Python
	pipenv run py.test \
		--cov-report html \
		--cov-report term-missing \
		--cov=django_sorcery tests \
		--doctest-modules \
		django_sorcery tests

$(FILES):  ## helper target to run coverage tests on a module
	pipenv run py.test --cov-report term-missing --cov-fail-under 100 --cov=$(subst /,.,$(firstword $(subst ., ,$@))) $(subst $(PACKAGE),tests,$(dir $@))test_$(notdir $@)

test:  ## run tests
	pipenv run py.test --doctest-modules django_sorcery tests

check:  ## run all tests
	tox

history:  ## generate HISTORY.rst
	pipenv run gitchangelog > HISTORY.rst

docs:  ## generate docs
	$(MAKE) -C docs html

livedocs:  ## generate docs live
	$(MAKE) -C docs html

version:  # print version
	@python setup.py --version

tag:  ## tags branch
	git tag -a $$(python setup.py --version) -m $$(python setup.py --version)

release: dist  ## package and upload a release
	twine upload dist/*

dist: clean  ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
