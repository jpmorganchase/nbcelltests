PYTHON := python
PIP := pip

run:
	${PYTHON} -m nbcelltests.test Untitled.ipynb

testjs: ## Clean and Make js tests
	cd js; yarn test

testpy: ## Clean and Make unit tests
	${PYTHON} -m pytest -v nbcelltests/tests --cov=nbcelltests

testpy-distributed: ## Python unit tests parallelized across two CPUs
# --dist=loadscope causes tests in the same class to be run sequentially
# Required until https://github.com/jpmorganchase/nbcelltests/issues/207 is addressed
	${PYTHON} -m pytest -v -n 2 --dist=loadscope nbcelltests/tests

tests: lint ## run the tests
	rm -rf nbcelltests/tests/_*_test.py
	${PYTHON} -m pytest -v nbcelltests/tests --cov=nbcelltests --junitxml=python_junit.xml --cov-report=xml --cov-branch
	cd js; yarn test

lint: ## run linter
	flake8 nbcelltests setup.py
	cd js; yarn lint

fix:  ## run autopep8/tslint fix
	autopep8 --in-place -r -a -a nbcelltests/
	cd js; yarn fix

extest:  ## run example test
	@ ${PYTHON} -m nbcelltests test examples/Example.ipynb

exlint:  ## run example test
	@ ${PYTHON} -m nbcelltests lint examples/Example.ipynb

annotate: ## MyPy type annotation check
	mypy -s nbcelltests

annotate_l: ## MyPy type annotation check - count only
	mypy -s nbcelltests | wc -l

clean: ## clean the repository
	find . -name "__pycache__" | xargs  rm -rf
	find . -name "*.pyc" | xargs rm -rf
	find . -name ".ipynb_checkpoints" | xargs  rm -rf
	find . -name "_*_test.py" | xargs rm -rf
	find . -name "_*_test.html" | xargs rm -rf
	rm -rf .coverage coverage cover htmlcov logs build dist *.egg-info lib node_modules coverage.xml python_junit.xml
	# make -C ./docs clean

docs:  ## make documentation
	make -C ./docs html
	open ./docs/_build/html/index.html

install:  ## install to site-packages
	${PIP} install .

serverextension: install ## enable serverextension
	jupyter serverextension enable --py nbcelltests

js:  ## build javascript
	cd js; yarn
	cd js; yarn build

labextension: js ## enable labextension
	cd js; jupyter labextension install .

dist: js  ## create dists
	rm -rf dist build
	${PYTHON} setup.py sdist bdist_wheel
	${PYTHON} -m twine check dist/*

publishpy: dist  ## dist to pypi
	${PYTHON} -m twine upload dist/* --skip-existing

publishjs: dist  ## dist to npm
	cd js; npm publish || echo "can't publish - might already exist"

publish: publishpy publishjs  ## dist to pypi and npm

verify-install:  ## verify all components are installed and active
	${PYTHON} -c "import nbcelltests"
	jupyter labextension check jupyterlab_celltests
# apparently can't ask serverextension about individual extensions (and it's OK on linux/mac but ok on windows :) )
	${PYTHON} -c "import subprocess,re,sys; import nbcelltests;  ext=subprocess.check_output(['jupyter','serverextension','list'],stderr=subprocess.STDOUT).decode();  print(ext);  res0=re.search('.*nbcelltests.*{}.*ok'.format(nbcelltests.__version__),ext,re.IGNORECASE);  res1=re.search('nbcelltests.*enabled', ext);  sys.exit(not (res0 and res1))"

# Thanks to Francoise at marmelab.com for this
.DEFAULT_GOAL := help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

print-%:
	@echo '$*=$($*)'

# TODO looks out of date...most if not all targets in here are phony
.PHONY: clean install serverextension labextension test tests help docs dist
