# jupyterlab_celltests
Cell-by-cell testing for production Jupyter notebooks in JupyterLab

[![Build Status](https://travis-ci.org/timkpaine/jupyterlab_celltests.svg?branch=master)](https://travis-ci.org/timkpaine/jupyterlab_celltests)
[![PyPI](https://img.shields.io/pypi/l/jupyterlab_celltests.svg)](https://pypi.python.org/pypi/jupyterlab_celltests)
[![PyPI](https://img.shields.io/pypi/v/jupyterlab_celltests.svg)](https://pypi.python.org/pypi/jupyterlab_celltests)
[![npm](https://img.shields.io/npm/v/jupyterlab_celltests.svg)](https://www.npmjs.com/package/jupyterlab_celltests)


# Overview
`Celltests` is designed for writing tests for linearly executed notebooks. Its primary use is for report unit tests. 

### "Linearly executed notebooks?"
When converting notebooks into html/pdf/email reports, they are executed from top-to-bottom one time, and are expected contain as little code as reasonable, focusing primarily on the plotting and markdown bits. Libraries for this type of thing include [Papermill](https://github.com/nteract/papermill), [JupyterLab Emails](https://github.com/timkpaine/jupyterlab_email), etc. 

### Doesn't this already exist?
[Nbval](https://github.com/computationalmodelling/nbval) is a great product and I recommend using it for notebook regression tests. But it compares the executed notebook's outputs to its existing outputs, which doesn't align well with dynamic reports which might be run everyday with different input/output data. 