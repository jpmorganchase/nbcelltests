# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
import tempfile
import os
import unittest

from nbcelltests.test import run

# TODO: we should generate the notebooks rather than having them as files
# (same for lint ones)
CUMULATIVE_RUN = os.path.join(os.path.dirname(__file__), '_cumulative_run.ipynb')
CELL_ERROR = os.path.join(os.path.dirname(__file__), '_cell_error.ipynb')
TEST_ERROR = os.path.join(os.path.dirname(__file__), '_test_error.ipynb')
TEST_FAIL = os.path.join(os.path.dirname(__file__), '_test_fail.ipynb')

# TODO: each generated test includes all the previous cells+tests.
# I.e. each test could be run in independent (fresh) kernel (allows
# things like distributing tests etc - but at the cost of slow kernel
# startup per test). Currently the generated tests just create the
# kernel per notebook not per cell, so test like that.
FRESH_KERNEL_PER_TEST = False


def _check_fresh(t, force_fresh=False):
    if FRESH_KERNEL_PER_TEST or force_fresh:
        t.run_test("""
        try:
            x
        except NameError:
            pass
        else:
            raise Exception('x was already defined - kernel is not fresh')
        """)

# TODO: This test file's manual use of unittest is brittle, but just
# want to get started asserting what the current behavior is before
# cleaning up/documenting.


def _import_from_path(pypath, f):
    # TODO consider py version compat
    import importlib.util
    spec = importlib.util.spec_from_file_location(pypath, f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _TestTest(unittest.TestCase):
    # abstract :)

    @classmethod
    def setUpClass(cls):
        with tempfile.NamedTemporaryFile(suffix='.py') as f:
            cls.generated_tests = _import_from_path("nbcelltests.tests.%s.%s" % (__name__, cls.__name__), run(cls.NBNAME, filename=f.name))


class TestTestCumulativeRun(_TestTest):

    NBNAME = CUMULATIVE_RUN

    def test_state(self):
        # TODO: and split up, depending whether testing fresh kernel per test or not

        t = self.generated_tests.TestNotebook()
        t.setup_class()

        # check cell did not run
        _check_fresh(t)
        t.test_cell_0()
        _check_fresh(t, force_fresh=True)

        # check cell ran
        _check_fresh(t)
        t.test_cell_1()
        t.run_test("""
        assert x == 0, x
        """)

        # cumulative cells ran
        _check_fresh(t)
        t.test_cell_2()
        t.run_test("""
        assert x == 1, x
        """)

        # check test affects state
        _check_fresh(t)
        t.test_cell_3()
        t.run_test("""
        assert x == 2, x
        """)

        t.teardown_class()


class TestTestCellException(_TestTest):

    NBNAME = CELL_ERROR

    def test_cell_exception(self):
        t = self.generated_tests.TestNotebook()
        t.setup_class()

        # cell errors
        _check_fresh(t)

        try:
            t.test_cell_0()
        except Exception as e:
            assert e.args[0].startswith("Cell execution caused an exception")
            assert e.args[0].endswith("My code does not even run")
        else:
            raise Exception("Cell should have errored out")

        t.teardown_class()


class TestTestTestException(_TestTest):

    NBNAME = TEST_ERROR

    def test_exception_in_test(self):
        t = self.generated_tests.TestNotebook()
        t.setup_class()

        # caught cell error
        _check_fresh(t)
        t.test_cell_0()

        # test errors
        _check_fresh(t)
        try:
            t.test_cell_1()
        except Exception as e:
            assert e.args[0].startswith("Cell execution caused an exception")
            assert e.args[0].endswith("My test is bad too")
        else:
            raise Exception("Test should have failed")

        t.teardown_class()


class TestTestTestFail(_TestTest):

    NBNAME = TEST_FAIL

    def test_expected_fail(self):
        t = self.generated_tests.TestNotebook()
        t.setup_class()

        # caught cell error
        _check_fresh(t)
        try:
            t.test_cell_0()
        except Exception as e:
            assert e.args[0].startswith("Cell execution caused an exception")
            assert e.args[0].endswith("x should have been -1 but was 1")
        else:
            raise Exception("Test should have failed")

        t.teardown_class()
