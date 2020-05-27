# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
import os

import pytest
import nbformat

from nbcelltests.shared import extract_extrametadata, get_coverage, is_empty

# TODO: should generate these
BASIC_NB = os.path.join(os.path.dirname(__file__), 'basic.ipynb')
MORE_NB = os.path.join(os.path.dirname(__file__), 'more.ipynb')
MAGICS_NB = os.path.join(os.path.dirname(__file__), 'magics.ipynb')
COVERAGE_NB = os.path.join(os.path.dirname(__file__), '_cell_coverage.ipynb')
LINT_DISABLE_NB = os.path.join(os.path.dirname(__file__), '_lint_disable.ipynb')


def test_is_empty():
    assert is_empty("import blah\nblah.do_something()") is False
    assert is_empty("%matplotlib inline") is False
    assert is_empty("pass") is False
    assert is_empty("") is True
    assert is_empty("#pass") is True
    assert is_empty("\n\n\n") is True


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
    assert _metadata(BASIC_NB, 'cell_lines') == [1] * 5

# with some magics present


def test_extract_extrametadata_functions_more():
    assert _metadata(MORE_NB, 'functions') == 1


def test_extract_extrametadata_classes_more():
    assert _metadata(MORE_NB, 'classes') == 1


def test_extract_extrametadata_cell_count_more():
    assert _metadata(MORE_NB, 'cell_count') == 4


def test_extract_extrametadata_cell_lines_more():
    assert _metadata(MORE_NB, 'cell_lines') == [2, 1] + [2, 3]


def test_extract_extrametadata_magics():
    assert _metadata(MAGICS_NB, 'magics') == set(['magics1', 'magics2', 'magics3'])


# with non-code cells present


def test_extract_extrametadata_functions_noncode():
    assert _metadata(COVERAGE_NB, 'functions') == 1


def test_extract_extrametadata_classes_noncode():
    assert _metadata(COVERAGE_NB, 'classes') == 1


def test_extract_extrametadata_cell_count_noncode():
    assert _metadata(COVERAGE_NB, 'cell_count') == 4


def test_extract_extrametadata_cell_lines_noncode():
    assert _metadata(COVERAGE_NB, 'cell_lines') == [3, 1, 1, 2]


def test_extract_extrametadata_magics_noncode():
    assert _metadata(COVERAGE_NB, 'magics') == set(['magics2'])


# coverage

# tests would clearer with multiple notebooks containing independent
# cases - i.e. should generate them

# N = contribs to numerator of calc
# D = contribs to denominator of calc
# - = contribs nothing

# --  empty code cell with test
# --  markdown cell
# ND  code cell with valid test
# --  raw cell
# -D  code cell with invalid test (no %cell)
# -D  code cell with empty test
# -D  code cell with no test
#
# i.e. coverage = 1/4
def test_extract_extrametadata_cell_count_coverage():
    assert _metadata(COVERAGE_NB, 'cell_count') == 4


def test_extract_extrametadata_cell_test_coverage():
    assert _metadata(COVERAGE_NB, 'test_count') == 1


def test_get_coverage_nb():
    assert get_coverage(extract_extrametadata(nbformat.read(COVERAGE_NB, 4))) == 25


@pytest.mark.parametrize(
    "test_count, cell_count, expected", [
        (0, 10, 0),
        (5, 10, 50),
        (10, 10, 100),
        (0, 0, 0),
        (10, 0, 0),  # this would be an error at test generation time
    ]
)
def test_get_coverage(test_count, cell_count, expected):
    metadata = {
        'test_count': test_count,
        'cell_count': cell_count
    }
    assert get_coverage(metadata) == expected


# lint disable

def test_extract_extrametadata_disable_none():
    metadata = extract_extrametadata(nbformat.read(LINT_DISABLE_NB, 4))
    assert len(metadata['noqa']) == 0


def test_extract_extrametadata_disable_notpresent():
    metadata = extract_extrametadata(nbformat.read(LINT_DISABLE_NB, 4), noqa_regex=r"^# don't noqa notebook:\s*(.*)$")
    assert len(metadata['noqa']) == 0


def test_extract_extrametadata_disable_cells_count():
    metadata = extract_extrametadata(nbformat.read(LINT_DISABLE_NB, 4), noqa_regex=r"^# noqa notebook:\s*(.*)$")
    assert metadata['noqa'] == {'cells_per_notebook'}


def test_extract_extrametadata_disable_bad_regex():
    try:
        metadata = extract_extrametadata(nbformat.read(LINT_DISABLE_NB, 4), noqa_regex=r"^# noqa notebook:\s*.*$")
    except ValueError as e:
        assert e.args[0] == "noqa_regex must contain one capture group (specifying the rule)"
    else:
        assert False, "should have raised a ValueError"
