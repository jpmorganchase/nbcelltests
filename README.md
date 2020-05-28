# nbcelltests
Cell-by-cell testing for production Jupyter notebooks in JupyterLab

[![Build Status](https://dev.azure.com/tpaine154/jupyter/_apis/build/status/jpmorganchase.nbcelltests?branchName=master)](https://dev.azure.com/tpaine154/jupyter/_build/latest?definitionId=24&branchName=master)
[![Coverage](https://img.shields.io/azure-devops/coverage/tpaine154/jupyter/24/master)](https://dev.azure.com/tpaine154/jupyter/_build?definitionId=24&_a=summary)
[![Docs](https://img.shields.io/readthedocs/nbcelltests.svg)](https://nbcelltests.readthedocs.io)
[![PyPI](https://img.shields.io/pypi/l/nbcelltests.svg)](https://pypi.python.org/pypi/nbcelltests)
[![PyPI](https://img.shields.io/pypi/v/nbcelltests.svg)](https://pypi.python.org/pypi/nbcelltests)
[![npm](https://img.shields.io/npm/v/jupyterlab_celltests.svg)](https://www.npmjs.com/package/jupyterlab_celltests)


# Overview
`Celltests` is designed for writing tests for linearly executed notebooks. Its primary use is for unit testing reports. 

## Installation
Python package installation: `pip install nbcelltests`

To use in JupyterLab, you will also need the lab and server extensions. Typically, these are
automatically installed alongside nbcelltests, so you should not need to do anything special
to use them. The lab extension will require a rebuild of JupyterLab, which you'll be prompted
to do on starting JupyterLab the first time after installing celltests (or you can do manually
with `jupyter lab build`. Note that you must have node.js installed (as for any lab extension).

To see what extensions you have, check the output of `jupyter labextension list` (look for
`jupyterlab_celltests`, and `jupyter serverextension list` (look for `nbcelltests`).
If for some reason you need to manually install the extensions, you can do so as follows:

```bash
jupyter labextension install jupyterlab_celltests
jupyter serverextension enable --py nbcelltests
```

(Note: if using in an environment, you might wish to add `--sys-prefix` to the `serverextension` command.)

## "Linearly executed notebooks?"
When converting notebooks into html/pdf/email reports, they are executed top-to-bottom one time, and are expected to contain as little code as reasonably possible, focusing primarily on the plotting and markdown bits. Libraries for this type of thing include [Papermill](https://github.com/nteract/papermill), [JupyterLab Emails](https://github.com/timkpaine/jupyterlab_email), etc. 

## Doesn't this already exist?
[Nbval](https://github.com/computationalmodelling/nbval) is a great product and I recommend using it for notebook regression tests. But it only allows for testing for unexpected failures or simple output equality tests.

## So why do I want this again?
This doesn't necessarily help you if your data sources go down, but its likely you'll notice this anyway. Where this comes in handy is:

- when the environment (e.g. package versions) are changing in your system
- when you play around in the notebook (e.g. nonlinear execution) but aren't sure if your reports will still generate
- when your software lifecycle systems have a hard time dealing with notebooks (can't lint/audit them as code unless integrated nbdime/nbconvert to script, tough to test, tough to ensure what works today works tomorrow)

## So what does this do?
Given a notebook, you can write mocks and assertions for individual cells. You can then generate a testing script for this notebook, allowing you to hook it into your testing system and thereby provide unittests of your report. 

## Writing tests
When you write tests for a cell, we create a new method on a `unittest` class corresponding to the index of your cell, and including the cumulative tests for all previous cells (to mimic what has happened so far in the notebook's linear execution). You can write whatever mocking and asserts you like, and can call `%cell` to inject the contents of the cell into your test. 
![](https://raw.githubusercontent.com/timkpaine/nbcelltests/master/docs/demo.gif)
The tests themselves are stored in the cell metadata, similar to celltags, slide information, etc. 

## Running tests
You can run the tests offline from an `.ipynb` file, or you can execute them from the browser and view the results of `pytest-html`'s html plugin.
![](https://raw.githubusercontent.com/timkpaine/nbcelltests/master/docs/demo2.gif)

## Extra Tests
- Max number of lines per cell
- Max number of cells per notebook
- Max number of function definitions per notebook
- Max number of class definitions per notebook
- Percentage of cells tested

## Example
In the committed `Untitled.ipynb` notebook, but modified so that cell 0 has its import statement copied 10 times (to trigger test and lint failures):


### Tests
```bash
Untitled_test.py::TestExtension::test_cell0 PASSED                                                                                     [  8%]
Untitled_test.py::TestExtension::test_cell1 PASSED                                                                                     [ 16%]
Untitled_test.py::TestExtension::test_cell2 PASSED                                                                                     [ 25%]
Untitled_test.py::TestExtension::test_cell3 PASSED                                                                                     [ 33%]
Untitled_test.py::TestExtension::test_cell_coverage PASSED                                                                             [ 41%]
Untitled_test.py::TestExtension::test_cells_per_notebook PASSED                                                                        [ 50%]
Untitled_test.py::TestExtension::test_class_definition_count PASSED                                                                    [ 58%]
Untitled_test.py::TestExtension::test_function_definition_count PASSED                                                                 [ 66%]
Untitled_test.py::TestExtension::test_lines_per_cell_0 FAILED                                                                          [ 75%]
Untitled_test.py::TestExtension::test_lines_per_cell_1 PASSED                                                                          [ 83%]
Untitled_test.py::TestExtension::test_lines_per_cell_2 PASSED                                                                          [ 91%]
Untitled_test.py::TestExtension::test_lines_per_cell_3 PASSED                                                                          [100%]
```
### Lint
```bash
Checking lines in cell 0:   FAILED
Checking lines in cell 1:   PASSED
Checking lines in cell 2:   PASSED
Checking lines in cell 3:   PASSED
Checking cells per notebook <= 10:  PASSED
Checking functions per notebook <= 10:  PASSED
Checking classes per notebook <= 10:    PASSED
Checking cell test coverage >= 50:  PASSED
```

NB: In jupyterlab, notebooks will be lint checked using the version of
python that is running jupyter lab itself. A notebook intended to be
run with a Python 2 kernel could therefore generate syntax errors
during lint checking.
