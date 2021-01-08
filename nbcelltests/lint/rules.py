# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
from ..define import LintMessage, LintType


def lint_lines_per_cell(cell_lines, max_lines_per_cell=-1):
    ret = []
    if max_lines_per_cell < 0:
        return [], True
    for i, lines_in_cell in enumerate(cell_lines):
        ret.append(
            LintMessage(
                i + 1,  # TODO: ambiguous - e.g. cell 0 or first cell?
                "Checking lines in cell (max={max_}; actual={actual})".format(
                    max_=max_lines_per_cell, actual=lines_in_cell
                ),
                LintType.LINES_PER_CELL,
                lines_in_cell <= max_lines_per_cell,
            )
        )
    return ret, all([x.passed for x in ret])


def lint_cells_per_notebook(cell_count, max_cells_per_notebook=-1):
    if max_cells_per_notebook < 0:
        return [], True
    passed = cell_count <= max_cells_per_notebook
    return [
        LintMessage(
            -1,
            "Checking cells per notebook (max={max_}; actual={actual})".format(
                max_=max_cells_per_notebook, actual=cell_count
            ),
            LintType.CELLS_PER_NOTEBOOK,
            passed,
        )
    ], passed


def lint_function_definitions(functions, max_function_definitions=-1):
    if max_function_definitions < 0:
        return [], True
    passed = functions <= max_function_definitions
    return [
        LintMessage(
            -1,
            "Checking functions per notebook (max={max_}; actual={actual})".format(
                max_=max_function_definitions, actual=functions
            ),
            LintType.FUNCTION_DEFINITIONS,
            passed,
        )
    ], passed


def lint_class_definitions(classes, max_class_definitions=-1):
    if max_class_definitions < 0:
        return [], True
    passed = classes <= max_class_definitions
    return [
        LintMessage(
            -1,
            "Checking classes per notebook (max={max_}; actual={actual})".format(
                max_=max_class_definitions, actual=classes
            ),
            LintType.CLASS_DEFINITIONS,
            passed,
        )
    ], passed


def lint_kernelspec(kernelspec, kernelspec_requirements=False):
    """Check that kernelspec fulfills kernelspec_requirements.

    If kernelspec_requirements is False, no check will happen.

    If kernelspec_requirements is None, requires an empty kernelspec
    (use to enforce saving without kernelspec details).

    Otherwise, kernelspec must contain at least the same key: value
    pairs as are in kernelspec_requirements.
    """
    if kernelspec_requirements is False:
        return [], True
    # assumes kernelspec dict values are hashable (they're strings)
    passed = set(kernelspec.items()).issuperset(kernelspec_requirements.items())
    return [
        LintMessage(
            -1,
            "Checking kernelspec (min. required={required}; actual={actual})".format(
                required=kernelspec_requirements, actual=kernelspec
            ),
            LintType.KERNELSPEC,
            passed,
        )
    ], passed


def lint_magics(magics, allowlist=None, denylist=None):
    """Check that magics are acceptable.

    Specify either a allowlist or a denylist (or neither), but not
    both.
    """
    if allowlist is None and denylist is None:
        return [], True

    if allowlist is not None and denylist is not None:
        raise ValueError(
            "Must specify either a allowlist or a denylist, not both. denylist: {}; allowlist: {}".format(
                denylist, allowlist
            )
        )

    if allowlist is not None:
        bad = set(magics) - set(allowlist)
        msg = "missing from allowlist:"
    elif denylist is not None:
        bad = set(magics) & set(denylist)
        msg = "present in denylist:"

    passed = not (bad)
    return [
        LintMessage(
            -1,
            "Checking magics{}".format(" ({} {})".format(msg, bad) if bad else ""),
            LintType.MAGICS,
            passed,
        )
    ], passed
