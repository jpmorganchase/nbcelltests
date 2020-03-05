run:
	python3.7 -m jupyterlab_celltests.tests Untitled.ipynb

testjs: ## Clean and Make js tests
	yarn test

testpy: ## Clean and Make unit tests
	python3.7 -m pytest -v tests --cov=jupyterlab_celltests
	yarn test

tests: lint ## run the tests
	python3.7 -m pytest -v tests --cov=jupyterlab_celltests --junitxml=python_junit.xml --cov-report=xml --cov-branch
	yarn test

lint: ## run linter
	flake8 jupyterlab_celltests 
	yarn lint

fix:  ## run autopep8/tslint fix
	autopep8 --in-place -r -a -a jupyterlab_celltests/
	./node_modules/.bin/tslint --fix src/*

extest:  ## run example test
	@ python3.7 -m jupyterlab_celltests.tests Untitled.ipynb

exlint:  ## run example test
	@ python3.7 -m jupyterlab_celltests.lint Untitled.ipynb

annotate: ## MyPy type annotation check
	mypy -s jupyterlab_celltests

annotate_l: ## MyPy type annotation check - count only
	mypy -s jupyterlab_celltests | wc -l 

clean: ## clean the repository
	find . -name "__pycache__" | xargs  rm -rf 
	find . -name "*.pyc" | xargs rm -rf 
	find . -name ".ipynb_checkpoints" | xargs  rm -rf 
	rm -rf .coverage coverage cover htmlcov logs build dist *.egg-info lib node_modules
	# make -C ./docs clean

docs:  ## make documentation
	make -C ./docs html
	open ./docs/_build/html/index.html

install:  ## install to site-packages
	pip3 install .

serverextension: install ## enable serverextension
	jupyter serverextension enable --py jupyterlab_celltests

js:  ## build javascript
	yarn
	yarn build

labextension: js ## enable labextension
	jupyter labextension install .

dist: js
	rm -rf dist build
	python3.7 setup.py sdist bdist_wheel

publish: dist  ## dist to pypi
	twine check dist/* && twine upload dist/*
	npm publish

# Thanks to Francoise at marmelab.com for this
.DEFAULT_GOAL := help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

print-%:
	@echo '$*=$($*)'

.PHONY: clean install serverextension labextension test tests help docs dist
