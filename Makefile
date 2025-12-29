###############
# Build Tools #
###############
build:  ## build python/javascript
	python -m build .

develop:  ## install to site-packages in editable mode
	python -m pip install --upgrade build jupyterlab pip setuptools twine wheel
	cd js; jlpm && npx playwright install
	python -m pip install -e .[develop]

install:  ## install to site-packages
	python -m pip install .

###########
# Testing #
###########
testpy: ## clean and Make unit tests
	python -m pytest -v nbcelltests/tests --junitxml=junit.xml --cov=nbcelltests --cov-report=xml:.coverage.xml --cov-branch --cov-fail-under=0 --cov-report term-missing

testjs: ## clean and Make js tests
	cd js; jlpm test

test: tests
tests: testpy testjs ## run the tests

###########
# Linting #
###########
lintpy:  ## lint python with ruff and isort
	python -m isort --check nbcelltests
	python -m ruff check nbcelltests
	python -m ruff format --check nbcelltests

lintjs:  ## lint javascript with eslint
	cd js; jlpm lint

lint: lintpy lintjs  ## run linters

fixpy:  ## autoformat python with ruff and isort
	python -m isort nbcelltests
	python -m ruff format nbcelltests

fixjs:  ## autoformat javascript with eslint
	cd js; jlpm fix

fix: fixpy fixjs  ## run black/tslint fix
format: fix

############
# Examples #
############
PYTHON := python
PIP := pip

run:
	${PYTHON} -m nbcelltests.test Untitled.ipynb

extest:  ## run example test
	@ ${PYTHON} -m nbcelltests test examples/Example.ipynb

exlint:  ## run example test
	@ ${PYTHON} -m nbcelltests lint examples/Example.ipynb

################
# Distribution #
################
dist: clean build  ## create dists
	python -m twine check dist/*

publishpy:  ## dist to pypi
	python -m twine upload dist/* --skip-existing

publishjs:  ## dist to npm
	cd js; npm publish || echo "can't publish - might already exist"

publish: dist publishpy publishjs  ## dist to pypi and npm

############
# Cleaning #
############
clean: ## clean the repository
	find . -name "__pycache__" | xargs  rm -rf
	find . -name "*.pyc" | xargs rm -rf
	find . -name ".ipynb_checkpoints" | xargs  rm -rf
	rm -rf .coverage coverage *.xml build dist *.egg-info lib node_modules .pytest_cache *.egg-info
	rm -rf nbcelltests/labextension
	cd js && jlpm clean
	git clean -fd

###########
# Helpers #
###########
# Thanks to Francoise at marmelab.com for this
.DEFAULT_GOAL := help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

print-%:
	@echo '$*=$($*)'

.PHONY: testjs testpy tests test lintpy lintjs lint fixpy fixjs fix format build develop install labextension dist publishpy publishjs publish docs clean
