import os

import nbformat

from jupyterlab_celltests.shared import extract_extrametadata


BASIC_NB = os.path.join(os.path.dirname(__file__), 'basic.ipynb')
MORE_NB = os.path.join(os.path.dirname(__file__), 'more.ipynb')


def _metadata(nb, what):
    extra_metadata = extract_extrametadata(nbformat.read(nb, 4))
    return extra_metadata[what]


def test_extract_extrametadata_functions_basic():
    assert _metadata(BASIC_NB, 'functions') == 2

def test_extract_extrametadata_classes_basic():
    assert _metadata(BASIC_NB, 'classes') == 2

def test_extract_extrametadata_cell_count_basic():
    assert _metadata(BASIC_NB, 'cell_count') == 5

def test_extract_extrametadata_cell_lines_basic():
    assert _metadata(BASIC_NB, 'cell_lines') == [1]*5


def test_extract_extrametadata_functions_more():
    assert _metadata(MORE_NB, 'functions') == 1

def test_extract_extrametadata_classes_more():
    assert _metadata(MORE_NB, 'classes') == 1

def test_extract_extrametadata_cell_count_more():
    assert _metadata(MORE_NB, 'cell_count') == 6

def test_extract_extrametadata_cell_lines_more():
    assert _metadata(MORE_NB, 'cell_lines') == [1]*4 + [2,3]
