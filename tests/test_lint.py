import pytest
# for Coverage
from mock import patch, MagicMock

from jupyterlab_celltests.lint import lint_lines_per_cell, lint_cells_per_notebook, lint_function_definitions, lint_class_definitions, lint_cell_coverage

# note that list comparison with = in this file assumes pytest

class TestLint:
    def test_run(self):
        pass

@pytest.mark.parametrize(
    "lines_per_cell, cell_lines, expected_ret, expected_pass", [
        ( 3, [0,1,2,3,4], [True, True, True, True,False], False),
        ( 3,   [0,1,2,3],       [True, True, True, True],  True),
        (-1,       [0,1],                             [],  True), 
    ]
)
def test_lines_per_cell(lines_per_cell, cell_lines, expected_ret, expected_pass):
    metadata = {
        'lines_per_cell': lines_per_cell,
        'cell_lines': cell_lines,
    }
    ret, passed = lint_lines_per_cell(metadata['lines_per_cell'], metadata)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "cells_per_notebook, cell_count, expected_ret, expected_pass", [
        ( 5, 10, [False], False),
        ( 5,  3,  [True],  True),
        ( 0, 10, [False], False),
        (10,  0,  [True],  True),
        (-1, 10,      [],  True)
    ]
)
def test_cells_per_notebook_bad(cells_per_notebook, cell_count, expected_ret, expected_pass):
    metadata = {
        'cells_per_notebook': cells_per_notebook,
        'cell_count': cell_count
    }
    ret, passed = lint_cells_per_notebook(metadata['cells_per_notebook'], metadata)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "function_definitions, functions, expected_ret, expected_pass", [
        ( 5, 10, [False], False),
        ( 5,  3,  [True],  True),
        ( 0, 10, [False], False),
        (10,  0,  [True],  True),
        (-1, 10,      [],  True)
    ]
)
def test_lint_function_definitions(function_definitions, functions, expected_ret, expected_pass):
    metadata = {
        'function_definitions': function_definitions,
        'functions': functions
    }
    ret, passed  = lint_function_definitions(function_definitions, metadata)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "class_definitions, classes, expected_ret, expected_pass", [
        ( 5, 10, [False], False),
        ( 5,  3,  [True],  True),
        ( 0, 10, [False], False),
        (10,  0,  [True],  True),
        (-1, 10,      [],  True)
    ]
)
def test_lint_class_definitions(class_definitions, classes, expected_ret, expected_pass):
    metadata = {
        'class_definitions': class_definitions,
        'classes': classes
    }
    ret, passed = lint_class_definitions(class_definitions, metadata)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "test_count, cell_count, cell_coverage, expected_ret, expected_pass", [
        ( 0, 10, 50, [False], False),
        ( 5, 10, 50,  [True],  True),
        ( 0, 10,  0,  [True],  True),
        ( 0, 10, -1,      [],  True)
    ]
)
def test_cell_coverage(test_count, cell_count, cell_coverage, expected_ret, expected_pass):
    metadata = {
        'test_count': test_count,
        'cell_count': cell_count,
        'cell_coverage': cell_coverage
    }
    ret, passed = lint_cell_coverage(cell_coverage, metadata)
    _verify(ret, passed, expected_ret, expected_pass)


def _verify(ret, passed, expected_ret, expected_pass):
    assert [r.passed for r in ret] == expected_ret
    assert passed is expected_pass
