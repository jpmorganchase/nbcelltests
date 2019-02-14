# jupyterlab_celltests
Cell-by-cell testing for production Jupyter notebooks in JupyterLab

[![Build Status](https://travis-ci.org/timkpaine/jupyterlab_celltests.svg?branch=master)](https://travis-ci.org/timkpaine/jupyterlab_celltests)
[![PyPI](https://img.shields.io/pypi/l/jupyterlab_celltests.svg)](https://pypi.python.org/pypi/jupyterlab_celltests)
[![PyPI](https://img.shields.io/pypi/v/jupyterlab_celltests.svg)](https://pypi.python.org/pypi/jupyterlab_celltests)
[![npm](https://img.shields.io/npm/v/jupyterlab_celltests.svg)](https://www.npmjs.com/package/jupyterlab_celltests)


# Overview
`Celltests` is designed for writing tests for linearly executed notebooks. Its primary use is for report unit tests. 

### "Linearly executed notebooks?"
When converting notebooks into html/pdf/email reports, they are executed from top-to-bottom one time, and are expected contain as little code as reasonably possible, focusing primarily on the plotting and markdown bits. Libraries for this type of thing include [Papermill](https://github.com/nteract/papermill), [JupyterLab Emails](https://github.com/timkpaine/jupyterlab_email), etc. 

### Doesn't this already exist?
[Nbval](https://github.com/computationalmodelling/nbval) is a great product and I recommend using it for notebook regression tests. But it compares the executed notebook's outputs to its existing outputs, which doesn't align well with dynamic reports which might be run everyday with different input/output data. 

### So why do I want this again?
This doesn't necessarily help you if your data sources go down, but its likely you'll notice this anyway. Where this comes in handy is:

- when the environment (e.g. package versions) are changing in your system
- when you play around in the notebook (e.g. nonlinear execution) but aren't sure if your reports will still generate
- when your software lifecycle systems have a hard time dealing with notebooks (can't lint/audit them as code unless integrated nbdime/nbconvert to script, tough to test, tough to ensure what works today works tomorrow)

### So what does this do?
Given a notebook, you can write mocks and assertions for individual cells. You can then generate a testing script for this notebook, allowing you to hook it into your testing system and thereby provide unittests of your report. 

## Writing tests
![](https://raw.githubusercontent.com/timkpaine/jupyterlab_celltests/master/docs/demo.gif)

## Running tests
![](https://raw.githubusercontent.com/timkpaine/jupyterlab_celltests/master/docs/demo2.gif)
