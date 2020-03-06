import os
import pytest

from jupyterlab_celltests.lint import lint_lines_per_cell, lint_cells_per_notebook, lint_function_definitions, lint_class_definitions, lint_cell_coverage, lint_kernelspec, lint_magics, run

# note that list comparison with = in this file assumes pytest


@pytest.mark.parametrize(
    "max_lines_per_cell, cell_lines, expected_ret, expected_pass", [
        (3, [0, 1, 2, 3, 4], [True, True, True, True, False], False),
        (3, [0, 1, 2, 3], [True, True, True, True], True),
        (-1, [0, 1], [], True),
    ]
)
def test_lines_per_cell(max_lines_per_cell, cell_lines, expected_ret, expected_pass):
    ret, passed = lint_lines_per_cell(cell_lines, max_lines_per_cell)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "max_cells_per_notebook, cell_count, expected_ret, expected_pass", [
        (5, 10, [False], False),
        (5, 3, [True], True),
        (0, 10, [False], False),
        (10, 0, [True], True),
        (-1, 10, [], True)
    ]
)
def test_cells_per_notebook(max_cells_per_notebook, cell_count, expected_ret, expected_pass):
    ret, passed = lint_cells_per_notebook(cell_count, max_cells_per_notebook)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "max_function_definitions, functions, expected_ret, expected_pass", [
        (5, 10, [False], False),
        (5, 3, [True], True),
        (0, 10, [False], False),
        (10, 0, [True], True),
        (-1, 10, [], True)
    ]
)
def test_lint_function_definitions(max_function_definitions, functions, expected_ret, expected_pass):
    ret, passed = lint_function_definitions(functions, max_function_definitions)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "max_class_definitions, classes, expected_ret, expected_pass", [
        (5, 10, [False], False),
        (5, 3, [True], True),
        (0, 10, [False], False),
        (10, 0, [True], True),
        (-1, 10, [], True)
    ]
)
def test_lint_class_definitions(max_class_definitions, classes, expected_ret, expected_pass):
    ret, passed = lint_class_definitions(classes, max_class_definitions)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "test_count, cell_count, min_cell_coverage, expected_ret, expected_pass", [
        (0, 10, 50, [False], False),
        (5, 10, 50, [True], True),
        (0, 10, 0, [True], True),
        (0, 10, -1, [], True),
        (0, 0, 0, [], True)
    ]
)
def test_cell_coverage(test_count, cell_count, min_cell_coverage, expected_ret, expected_pass):
    ret, passed = lint_cell_coverage(test_count, cell_count, min_cell_coverage)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "kernelspec_requirements, kernelspec, expected_ret, expected_pass", [
        ({'name': 'python3'}, {'name': 'python3',
                               'display_name': 'Python 3'}, [True], True),
        ({'name': 'python3'}, {'name': 'python2'}, [False], False),
        ({}, {'name': 'python3',
              'display_name': 'Python 3'}, [True], True),
        (False, {}, [], True),
        (False, {'something': 'else'}, [], True),
    ]
)
def test_kernelspec(kernelspec_requirements, kernelspec, expected_ret, expected_pass):
    ret, passed = lint_kernelspec(kernelspec, kernelspec_requirements)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "magics_whitelist, magics_blacklist, magics, expected_ret, expected_pass", [
        # no check
        (None, None, [], [], True),
        (None, None, ['anything'], [], True),
        # empty whitelist: no magics allowed
        ([], None, ['anything'], [False], False),
        # only whitelisted
        (['ok1', 'ok2'], None, ['ok1'], [True], True),
        (['ok1', 'ok2'], None, ['notok'], [False], False),
        # no blacklisted
        (None, ['notok'], ['ok'], [True], True),
        (None, ['notok'], ['notok'], [False], False),
    ]
)
def test_magics(magics_whitelist, magics_blacklist, magics, expected_ret, expected_pass):
    ret, passed = lint_magics(magics, whitelist=magics_whitelist, blacklist=magics_blacklist)
    _verify(ret, passed, expected_ret, expected_pass)


def test_magics_lists_sanity():
    msg = "Must specify either a whitelist or a blacklist, not both."

    with pytest.raises(ValueError, match=msg):
        lint_magics(set(), whitelist=['one'], blacklist=['one'])

    with pytest.raises(ValueError, match=msg):
        lint_magics(set(), whitelist=[], blacklist=['one'])

    with pytest.raises(ValueError, match=msg):
        lint_magics(set(), whitelist=[], blacklist=[])

    with pytest.raises(ValueError, match=msg):
        lint_magics(set(), whitelist=['one'], blacklist=[])


@pytest.mark.parametrize(
    "rules, expected_ret, expected_pass", [
        # no rules
        ({}, [], True),
        # one rule, pass
        ({'lines_per_cell': -1}, [], True),
        # one rule, fail
        ({'lines_per_cell': 1}, [False, True, True, True, False, False], False),
        # multiple rules, combo fail
        ({'lines_per_cell': 5,
          'cells_per_notebook': 1}, [True, True, True, True, True, True, False], False),
        # multiple rules, combo pass
        ({'lines_per_cell': 5,
          'cells_per_notebook': 10}, [True, True, True, True, True, True, True], True),
        # all the expected rules
        ({'lines_per_cell': 5,
          'cells_per_notebook': 2,
          'function_definitions': 0,
          'class_definitions': 0,
          'cell_coverage': 90,
          'kernelspec_requirements':
            {'name': 'python3'},
          'magics_whitelist': ['matplotlib']}, [True, True, True, True, True, True, False, False, False, False, True, True], False)
    ]
)
def test_run(rules, expected_ret, expected_pass):
    nb = os.path.join(os.path.dirname(__file__), 'more.ipynb')
    ret, passed = run(nb, rules=rules)
    _verify(ret, passed, expected_ret, expected_pass)


def _verify(ret, passed, expected_ret, expected_pass):
    assert [r.passed for r in ret] == expected_ret
    assert passed is expected_pass
