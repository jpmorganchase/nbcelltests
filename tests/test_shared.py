import os

import nbformat

from jupyterlab_celltests.shared import extract_extrametadata


BASIC_NB = os.path.join(os.path.dirname(__file__), 'basic.ipynb')
MORE_NB = os.path.join(os.path.dirname(__file__), 'more.ipynb')


def test_extract_extrametadata_basic():
    nb = nbformat.read(BASIC_NB, 4)
    res = extract_extrametadata(nb)
    assert res['functions'] == 2
    assert res['classes'] == 2


def test_extract_extrametadata_more():
    nb = nbformat.read(MORE_NB, 4)
    res = extract_extrametadata(nb)
    assert res['functions'] == 1
    assert res['classes'] == 1
