# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
from collections import namedtuple
import os
from operator import itemgetter
from bs4 import BeautifulSoup
import pytest

from nbcelltests.lint import lint_lines_per_cell, lint_cells_per_notebook, lint_function_definitions, lint_class_definitions, lint_kernelspec, lint_magics, run, runWithHTMLReturn
from nbcelltests.define import LintType

LR = namedtuple("lint_result", ['passed', 'type'])

# note that list comparison with = in this file assumes pytest


@pytest.mark.parametrize(
    "max_lines_per_cell, cell_lines, expected_ret, expected_pass", [
        (3, [0, 1, 2, 3, 4], [LR(x, LintType.LINES_PER_CELL) for x in [True, True, True, True, False]], False),
        (3, [0, 1, 2, 3], [LR(x, LintType.LINES_PER_CELL) for x in [True, True, True, True]], True),
        (-1, [0, 1], [], True),
    ]
)
def test_lines_per_cell(max_lines_per_cell, cell_lines, expected_ret, expected_pass):
    ret, passed = lint_lines_per_cell(cell_lines, max_lines_per_cell)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "max_cells_per_notebook, cell_count, expected_ret, expected_pass", [
        (5, 10, [LR(False, LintType.CELLS_PER_NOTEBOOK)], False),
        (5, 3, [LR(True, LintType.CELLS_PER_NOTEBOOK)], True),
        (0, 10, [LR(False, LintType.CELLS_PER_NOTEBOOK)], False),
        (10, 0, [LR(True, LintType.CELLS_PER_NOTEBOOK)], True),
        (-1, 10, [], True)
    ]
)
def test_cells_per_notebook(max_cells_per_notebook, cell_count, expected_ret, expected_pass):
    ret, passed = lint_cells_per_notebook(cell_count, max_cells_per_notebook)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "max_function_definitions, functions, expected_ret, expected_pass", [
        (5, 10, [LR(False, LintType.FUNCTION_DEFINITIONS)], False),
        (5, 3, [LR(True, LintType.FUNCTION_DEFINITIONS)], True),
        (0, 10, [LR(False, LintType.FUNCTION_DEFINITIONS)], False),
        (10, 0, [LR(True, LintType.FUNCTION_DEFINITIONS)], True),
        (-1, 10, [], True)
    ]
)
def test_lint_function_definitions(max_function_definitions, functions, expected_ret, expected_pass):
    ret, passed = lint_function_definitions(functions, max_function_definitions)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "max_class_definitions, classes, expected_ret, expected_pass", [
        (5, 10, [LR(False, LintType.CLASS_DEFINITIONS)], False),
        (5, 3, [LR(True, LintType.CLASS_DEFINITIONS)], True),
        (0, 10, [LR(False, LintType.CLASS_DEFINITIONS)], False),
        (10, 0, [LR(True, LintType.CLASS_DEFINITIONS)], True),
        (-1, 10, [], True)
    ]
)
def test_lint_class_definitions(max_class_definitions, classes, expected_ret, expected_pass):
    ret, passed = lint_class_definitions(classes, max_class_definitions)
    _verify(ret, passed, expected_ret, expected_pass)


@pytest.mark.parametrize(
    "kernelspec_requirements, kernelspec, expected_ret, expected_pass", [
        ({'name': 'python3'}, {'name': 'python3',
                               'display_name': 'Python 3'}, [LR(True, LintType.KERNELSPEC)], True),
        ({'name': 'python3'}, {'name': 'python2'}, [LR(False, LintType.KERNELSPEC)], False),
        ({}, {'name': 'python3',
              'display_name': 'Python 3'}, [LR(True, LintType.KERNELSPEC)], True),
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
        ([], None, ['anything'], [LR(False, LintType.MAGICS)], False),
        # only whitelisted
        (['ok1', 'ok2'], None, ['ok1'], [LR(True, LintType.MAGICS)], True),
        (['ok1', 'ok2'], None, ['notok'], [LR(False, LintType.MAGICS)], False),
        # no blacklisted
        (None, ['notok'], ['ok'], [LR(True, LintType.MAGICS)], True),
        (None, ['notok'], ['notok'], [LR(False, LintType.MAGICS)], False),
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
    "rules, noqa_regex, expected_ret, expected_pass", [
        # no rules
        ({}, None, [], True),
        # one rule, pass
        ({'lines_per_cell': -1}, None, [], True),
        # one rule, fail
        ({'lines_per_cell': 1}, None, [LR(x, LintType.LINES_PER_CELL) for x in [False, True, False, False]], False),
        # multiple rules, combo fail
        ({'lines_per_cell': 5,
          'cells_per_notebook': 1}, None, [LR(True, LintType.LINES_PER_CELL)] * 4 + [LR(False, LintType.CELLS_PER_NOTEBOOK)], False),
        # multiple rules, one disabled, combo pass
        ({'lines_per_cell': 1,
          'cells_per_notebook': 10}, "# LINT_DISABLE: notebook_(.*)$", [LR(True, LintType.CELLS_PER_NOTEBOOK)], True),
        # multiple rules, combo pass
        ({'lines_per_cell': 5,
          'cells_per_notebook': 10}, None, [LR(True, LintType.LINES_PER_CELL)] * 4 + [LR(True, LintType.CELLS_PER_NOTEBOOK)], True),
        # all the expected rules
        ({'lines_per_cell': 5,
          'cells_per_notebook': 2,
          'function_definitions': 0,
          'class_definitions': 0,
          'kernelspec_requirements':
            {'name': 'python3'},
          'magics_whitelist': ['matplotlib']}, None, [LR(True, LintType.LINES_PER_CELL)] * 4 +
                                                     [LR(False, LintType.CELLS_PER_NOTEBOOK)] +
                                                     [LR(False, LintType.FUNCTION_DEFINITIONS)] +
                                                     [LR(False, LintType.CLASS_DEFINITIONS)] +
                                                     [LR(True, LintType.KERNELSPEC)] +
                                                     [LR(True, LintType.MAGICS)], False)
    ]
)
def test_run(rules, noqa_regex, expected_ret, expected_pass):
    nb = os.path.join(os.path.dirname(__file__), 'more.ipynb')
    ret, passed = run(nb, rules=rules, noqa_regex=noqa_regex)
    _verify(ret, passed, expected_ret, expected_pass)


def _verify(ret, passed, expected_ret, expected_pass):
    assert [(r.passed, r.type) for r in ret] == [(e.passed, e.type) for e in expected_ret]
    assert passed is expected_pass


def test_runWithHTMLReturn_norules():
    # no rules, so will pass without any checks
    nb = os.path.join(os.path.dirname(__file__), 'more.ipynb')
    html, passed = runWithHTMLReturn(nb)
    assert passed is True
    _check(html, [])


def test_runWithHTMLReturn_pass():
    # checks should pass
    nb = os.path.join(os.path.dirname(__file__), 'more.ipynb')
    html, passed = runWithHTMLReturn(nb, rules={"cells_per_notebook": 10})
    assert passed is True
    _check(html, [("PASSED", "Checking cells per notebook (max=10; actual=4) (Notebook)")])


def test_runWithHTMLReturn_fail():
    # checks should fail
    nb = os.path.join(os.path.dirname(__file__), 'more.ipynb')
    html, passed = runWithHTMLReturn(nb, rules={"cells_per_notebook": 1, "lines_per_cell": 2})
    assert passed is False
    _check(html, [
        ("PASSED", "Checking lines in cell (max=2; actual=2)(Cell 1)"),
        ("PASSED", "Checking lines in cell (max=2; actual=1)(Cell 2)"),
        ("PASSED", "Checking lines in cell (max=2; actual=2)(Cell 3)"),
        ("FAILED", "Checking lines in cell (max=2; actual=3)(Cell 4)"),
        ("FAILED", "Checking cells per notebook (max=1; actual=4) (Notebook)")])


def _check(html, expected_results):
    # quick checking html matches expected results
    soup = BeautifulSoup(html, "html.parser")
    actual_results = soup.find_all("p")
    assert len(actual_results) == len(expected_results)
    for actual, expected in zip(sorted(actual_results, key=lambda x: x.text[x.text.find("Checking ")::]), sorted(expected_results, key=itemgetter(1))):
        assert actual.text.startswith(expected[0])
        assert actual.text.endswith(expected[1])
