# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
import nbformat
import os
import pytest

from nbcelltests.shared import (
    cell_injected_into_test,
    empty_ast,
    extract_extrametadata,
    get_cell_inj_span,
    get_coverage,
    only_whitespace,
)

# TODO: should generate these
BASIC_NB = os.path.join(os.path.dirname(__file__), "basic.ipynb")
MORE_NB = os.path.join(os.path.dirname(__file__), "more.ipynb")
MAGICS_NB = os.path.join(os.path.dirname(__file__), "magics.ipynb")
COVERAGE_NB = os.path.join(os.path.dirname(__file__), "_cell_coverage.ipynb")
LINT_DISABLE_NB = os.path.join(os.path.dirname(__file__), "_lint_disable.ipynb")
LINT_DISABLE_NB_EMPTY_CELL = os.path.join(os.path.dirname(__file__), "_lint_disable_empty_cell.ipynb")

# TODO should parameterize test_empty_ast _whitespace

# empty ast, empty whitespace
_empty_empty = ["", " ", "\t", "\n", "\r\n"]

# empty ast, non-empty whitespace
_empty_nonempty = [
    "#pass",
]


# non-empty ast, non-empty whitespace
_nonempty_nonempty = ["import blah\nblah.do_something()", "%matplotlib inline", "pass"]


def test_empty_ast():
    for x in _empty_empty:
        assert empty_ast(x) is True

    for x in _empty_nonempty:
        assert empty_ast(x) is True

    for x in _nonempty_nonempty:
        assert empty_ast(x) is False


def test_only_whitespace():
    for x in _empty_empty:
        assert only_whitespace(x) is True

    for x in _empty_nonempty:
        assert only_whitespace(x) is False

    for x in _nonempty_nonempty:
        assert only_whitespace(x) is False


def _metadata(nb, what):
    extra_metadata = extract_extrametadata(nbformat.read(nb, 4))
    return extra_metadata[what]


def test_extract_extrametadata_functions_basic():
    assert _metadata(BASIC_NB, "functions") == 2


def test_extract_extrametadata_classes_basic():
    assert _metadata(BASIC_NB, "classes") == 2


def test_extract_extrametadata_cell_count_basic():
    assert _metadata(BASIC_NB, "cell_count") == 5


def test_extract_extrametadata_cell_lines_basic():
    assert _metadata(BASIC_NB, "cell_lines") == [1] * 5


# with some magics present


def test_extract_extrametadata_functions_more():
    assert _metadata(MORE_NB, "functions") == 1


def test_extract_extrametadata_classes_more():
    assert _metadata(MORE_NB, "classes") == 1


def test_extract_extrametadata_cell_count_more():
    assert _metadata(MORE_NB, "cell_count") == 4


def test_extract_extrametadata_cell_lines_more():
    assert _metadata(MORE_NB, "cell_lines") == [2, 1] + [2, 3]


def test_extract_extrametadata_magics():
    assert _metadata(MAGICS_NB, "magics") == set(["magics1", "magics2", "magics3"])


# with non-code cells present


def test_extract_extrametadata_functions_noncode():
    assert _metadata(COVERAGE_NB, "functions") == 1


def test_extract_extrametadata_classes_noncode():
    assert _metadata(COVERAGE_NB, "classes") == 1


def test_extract_extrametadata_cell_count_noncode():
    assert _metadata(COVERAGE_NB, "cell_count") == 4


def test_extract_extrametadata_cell_lines_noncode():
    assert _metadata(COVERAGE_NB, "cell_lines") == [3, 1, 1, 2]


def test_extract_extrametadata_magics_noncode():
    assert _metadata(COVERAGE_NB, "magics") == set(["dirs"])


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
    assert _metadata(COVERAGE_NB, "cell_count") == 4


def test_extract_extrametadata_cell_test_coverage():
    assert _metadata(COVERAGE_NB, "test_count") == 1


def test_get_coverage_nb():
    assert get_coverage(extract_extrametadata(nbformat.read(COVERAGE_NB, 4))) == 25


@pytest.mark.parametrize(
    "test_count, cell_count, expected",
    [
        (0, 10, 0),
        (5, 10, 50),
        (10, 10, 100),
        (0, 0, 0),
        (10, 0, 0),  # this would be an error at test generation time
    ],
)
def test_get_coverage(test_count, cell_count, expected):
    metadata = {"test_count": test_count, "cell_count": cell_count}
    assert get_coverage(metadata) == expected


# lint disable


def test_extract_extrametadata_disable_none():
    metadata = extract_extrametadata(nbformat.read(LINT_DISABLE_NB, 4))
    assert len(metadata["noqa"]) == 0


def test_extract_extrametadata_disable_notpresent():
    metadata = extract_extrametadata(nbformat.read(LINT_DISABLE_NB, 4), noqa_regex=r"^# don't noqa notebook:\s*(.*)$")
    assert len(metadata["noqa"]) == 0


def test_extract_extrametadata_disable_cells_count():
    metadata = extract_extrametadata(nbformat.read(LINT_DISABLE_NB, 4), noqa_regex=r"^# noqa notebook:\s*(.*)$")
    assert metadata["noqa"] == {"cells_per_notebook"}


def test_extract_extrametadata_disable_cells_count_in_empty_cell():
    metadata = extract_extrametadata(
        nbformat.read(LINT_DISABLE_NB_EMPTY_CELL, 4),
        noqa_regex=r"^# noqa notebook:\s*(.*)$",
    )
    assert metadata["noqa"] == {"cells_per_notebook"}


def test_extract_extrametadata_disable_bad_regex():
    try:
        _ = extract_extrametadata(nbformat.read(LINT_DISABLE_NB, 4), noqa_regex=r"^# noqa notebook:\s*.*$")
    except ValueError as e:
        assert e.args[0] == "noqa_regex must contain one capture group (specifying the rule)"
    else:
        assert False, "should have raised a ValueError"


@pytest.mark.parametrize(
    "test_line, expected",
    [
        (r"%cell", (0, 5)),
        (r"%cell;x", (0, 5)),
        pytest.param(
            r"%celll",
            None,
            marks=pytest.mark.xfail(reason="need to decide rules/really treat as token"),
        ),
        (r"", None),
        (r"    %cell", (4, 9)),
        (r"# no %cell", None),
        (r"# %cell", None),
    ],
)
def test_get_cell_inj_span(test_line, expected):
    assert get_cell_inj_span(test_line) == expected


# TODO could clean up with textwrap dedent etc
@pytest.mark.parametrize(
    "test_source, expected, exception",
    [
        (
            r"""\
%cell
""",
            True,
            None,
        ),
        (
            r"""\
%cell
%cell
""",
            True,
            None,
        ),
        (
            r"""\
%cell;x
""",
            True,
            None,
        ),
        pytest.param(
            r"""\
%celll
""",
            None,
            None,
            marks=pytest.mark.xfail(reason="need to decide rules/really treat as token"),
        ),
        (
            r"""\
""",
            None,
            None,
        ),
        (
            r"""\
%cell l
""",
            True,
            None,
        ),
        (
            r"""\
x = 1
%cell
""",
            True,
            None,
        ),
        (
            r"""\
x = 1
if x==1:
    %cell
""",
            True,
            None,
        ),
        (
            r"""\
# no %cell
""",
            False,
            None,
        ),
        (
            r"""\
x = 1
if x==1:
    pass
    # no %cell
""",
            False,
            None,
        ),
        (
            r"""\
%cell # no %cell
""",
            True,
            None,
        ),
        (
            r"""\
%cell
# no %cell
""",
            NotImplemented,
            (ValueError, "mutually exclusive"),
        ),
    ],
)
def test_cell_injected_into_test(test_source, expected, exception):
    if exception is None:
        assert cell_injected_into_test(test_source) is expected
    else:
        with pytest.raises(exception[0], match=exception[1]):
            cell_injected_into_test(test_source)
