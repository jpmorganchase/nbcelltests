# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
from bs4 import BeautifulSoup
import tempfile
import os
import sys
import unittest

from nbcelltests.test import run, runWithReturn, runWithReport, runWithHTMLReturn

# TODO: we should generate the notebooks rather than having them as
# files (same for lint ones). Would also allow for simplification of
# test class hierarchy.
CUMULATIVE_RUN = os.path.join(os.path.dirname(__file__), '_cumulative_run.ipynb')
CELL_ERROR = os.path.join(os.path.dirname(__file__), '_cell_error.ipynb')
TEST_ERROR = os.path.join(os.path.dirname(__file__), '_test_error.ipynb')
TEST_FAIL = os.path.join(os.path.dirname(__file__), '_test_fail.ipynb')
COUNTING = os.path.join(os.path.dirname(__file__), '_cell_counting.ipynb')
NONCODE = os.path.join(os.path.dirname(__file__), '_non_code_cell.ipynb')
SKIPS = os.path.join(os.path.dirname(__file__), '_skips.ipynb')
COVERAGE = os.path.join(os.path.dirname(__file__), '_cell_coverage.ipynb')

# Hack. We want to test expected behavior in distributed situation,
# which we are doing via pytest --forked.
FORKED = '--forked' in sys.argv


def _assert_x_undefined(t):
    """
    Convenience method to assert that x is not already defined in the kernel.
    """
    t._run("""
    try:
        x
    except NameError:
        pass
    else:
        raise Exception('x was already defined')
    """)

# TODO: This test file's manual use of unittest is brittle


def _import_from_path(path, module_name):
    """
    Import and return a python module at the given path, with
    module_name setting __name__.

    See e.g. https://stackoverflow.com/a/67692.
    """
    # TODO: need to test over multiple python versions
    # (https://github.com/jpmorganchase/nbcelltests/issues/106)
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _generate_test_module(notebook, module_name):
    """
    Generate test file from notebook, then import it with __name__ set
    to module_name, and return it.
    """
    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf8')
    tf_name = tf.name
    try:
        # the module name (__name__) doesn't really matter, but
        # will be nbcelltests.tests.test_tests.X, where X is
        # whatever concrete subclass is this method belongs to.
        generated_module = _import_from_path(run(notebook, filename=tf_name), module_name)
    finally:
        try:
            tf.close()
        except Exception:
            pass
        os.remove(tf_name)

    return generated_module


class _TestCellTests(unittest.TestCase):
    # abstract :)

    @classmethod
    def setUpClass(cls):
        assert hasattr(cls, "NBNAME"), "Subclasses must have NBNAME attribute."  # TODO: make actually abstract
        cls.generated_tests = _generate_test_module(notebook=cls.NBNAME, module_name="nbcelltests.tests.%s.%s" % (__name__, cls.__name__))

    def _assert_skipped(self, mthd, reason):
        # TODO: actually calling the skipped method here ends
        # everything! It's some pytest issue, I think. So for now we
        # are checking that it would be skipped, rather than that it is
        # definitely skipped.
        msg = "Should have generated a skipped test method"
        self.assertTrue(hasattr(mthd, '__unittest_skip__'), msg=msg)
        self.assertEqual(mthd.__unittest_skip__, True, msg=msg)
        self.assertEqual(mthd.__unittest_skip_why__, reason, msg="Skip reason should have been %s" % reason)

    def test_coverage(self):
        """
        Subclasses should override this if they want to check coverage.
        """
        assert not hasattr(self, 'test_cell_coverage')


class TestMethodGenerationError(_TestCellTests):
    """Tests of things that should fail during test script generation"""

    NBNAME = NONCODE

    @classmethod
    def setUpClass(cls):
        # we're testing what happens in setUpClass
        pass

    def test_non_code_cell_with_test_causes_error(self):
        try:
            _generate_test_module(self.NBNAME, "module.name.irrelevant")
        except ValueError as e:
            assert e.args[0] == 'Cell 1 is not a code cell, but metadata contains test code!'
        else:
            raise Exception("Test script should fail to generate")


class TestSkips(_TestCellTests):
    """Tests that various conditions result in skipped tests"""

    NBNAME = SKIPS

    # the tests are independent, so it's fine to call setUpClass and
    # setUp before every test (and same for tearDown after). When we
    # are generating notebooks, we won't need the single, shared
    # notebook.
    def setUp(self):
        self.t = self.generated_tests.TestNotebook()
        self.t.setUpClass()
        self.t.setUp()

    def tearDown(self):
        self.t.tearDown()
        self.t.tearDownClass()

    def test_skip_completely_empty_code_cell(self):
        """Test+cell where cell has nothing at all in should be skipped"""
        self._assert_skipped(self.t.test_code_cell_1, "empty code cell")

    def test_skip_no_code_code_cell(self):
        """Test+cell where cell had e.g. just a comment in should be skipped"""
        self._assert_skipped(self.t.test_code_cell_2, "empty code cell")

    def test_skip_no_test_field_in_metadata(self):
        """Cell with no test metadata should be skipped"""
        self._assert_skipped(self.t.test_code_cell_3, "no test supplied")

    def test_skip_no_code_in_test(self):
        """Test+cell where test is just e.g. a comment should be skipped"""
        self._assert_skipped(self.t.test_code_cell_4, "no test supplied")

    def test_skip_completely_empty_test(self):
        """Cell where test is completely empty should be skipped"""
        self._assert_skipped(self.t.test_code_cell_5, "no test supplied")

    def test_skip_if_no_cell_injection(self):
        """Test+cell where test does not inject cell should be skipped"""
        self._assert_skipped(self.t.test_code_cell_6, "cell code not injected into test")


class TestCumulativeRun(_TestCellTests):
    """Tests that state in notebook is built up correctly."""

    NBNAME = CUMULATIVE_RUN

    def test_state(self):
        """In the expected case, the five cells of the notebook should work
        out as follows:

             cell    test   state
        1:    -       -       -
        2:   x=0      -      x=0
        3:   x+=1     -      x=1
        4:   x+=1     -      x=2
        5:    -      x+=1    x=3

        However, these tests originally detected repeated execution of
        cells in the same kernel. Cell 2 actually only sets x to 0 if
        x is not already defined; if x is already defined, cell 2 does
        not change x's value. If for some reason each test results in
        multiple executions of the cells, the results will look like
        this:

             cell    test   state
        1:    -       -       -
        2:    -       -      x>0   (bad; x was previously defined in kernel)
        3:   x+=1     -      x>1   (bad)
        4:   x+=1     -      x>2   (bad)
        5:    -      x+=1    x>3   (bad)
        """
        # this is one long method rather individual ones because of
        # building up state

        t = self.generated_tests.TestNotebook()
        t.setUpClass()

        # check cell did not run
        # (no %cell in test)
        t.setUp()
        _assert_x_undefined(t)
        self._assert_skipped(t.test_code_cell_1, "cell code not injected into test")
        # t.test_code_cell_1()
        # _assert_x_undefined(t)
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # check cell ran
        # (%cell in test)
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_code_cell_2()
        t._run("""
        assert x == 0, x
        """)
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # check cumulative cells ran
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_code_cell_3()
        t._run("""
        assert x == 1, x
        """)
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # check cumulative cells ran (but not multiple times!)
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_code_cell_4()
        t._run("""
        assert x == 2, x
        """)
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # check test affects state
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_code_cell_5()
        t._run("""
        assert x == 3, x
        """)
        t.tearDown()

        t.tearDownClass()


class TestExceptionInCell(_TestCellTests):
    """Tests related to exceptions in cells"""

    NBNAME = CELL_ERROR

    def test_exception_in_cell_is_detected(self):
        t = self.generated_tests.TestNotebook()

        t.setUpClass()
        t.setUp()

        # cell should error out
        try:
            t.test_code_cell_1()
        except Exception as e:
            assert e.args[0].startswith("Running cell+test for code cell 1; execution caused an exception")
            assert e.args[0].endswith("My code does not even run")
        else:
            raise Exception("Cell should have errored out")
        finally:
            t.tearDown()
            t.tearDownClass()


class TestExceptionInTest(_TestCellTests):
    """Tests related to exeptions in tests"""

    NBNAME = TEST_ERROR

    def test_exception_in_test_is_detected(self):
        t = self.generated_tests.TestNotebook()
        t.setUpClass()
        t.setUp()

        # caught cell error
        t.test_code_cell_1()

        t.tearDown()
        if FORKED:
            t.tearDownClass()

        if FORKED:
            t.setUpClass()
        t.setUp()

        _assert_x_undefined(t)

        # test should error out
        try:
            t.test_code_cell_2()
        except Exception as e:
            assert e.args[0].startswith("Running cell+test for code cell 2; execution caused an exception")
            assert e.args[0].endswith("My test is bad too")
        else:
            raise Exception("Test should have failed")
        finally:
            t.tearDown()
            t.tearDownClass()


class TestFailureInTest(_TestCellTests):
    """Tests related to test failures"""

    NBNAME = TEST_FAIL

    def test_failure_is_detected(self):
        """Test expected to fail - make sure we detect that."""
        t = self.generated_tests.TestNotebook()
        t.setUpClass()
        t.setUp()

        try:
            t.test_code_cell_1()
        except Exception as e:
            assert e.args[0].startswith("Running cell+test for code cell 1; execution caused an exception")
            assert e.args[0].endswith("x should have been -1 but was 1")
        else:
            raise Exception("Test should have failed")

        t.tearDown()
        if FORKED:
            t.tearDownClass()

        if FORKED:
            t.setUpClass()
        t.setUp()
        # subsequent cell should also fail
        try:
            t.test_code_cell_2()
        except Exception as e:
            assert e.args[0].startswith("Running cell+test for code cell 1; execution caused an exception")
            assert e.args[0].endswith("x should have been -1 but was 1")
        else:
            raise Exception("Test should have failed at cell 1")

        t.tearDown()
        t.tearDownClass()


class TestCellCounting(_TestCellTests):
    """Check that various things don't throw off cell+test correspondence."""

    NBNAME = COUNTING

    # the tests are independent, so it's fine to call setUpClass and
    # setUp before every test (and same for tearDown after). When we
    # are generating notebooks, we won't need the single, shared
    # notebook.
    def setUp(self):
        self.t = self.generated_tests.TestNotebook()
        self.t.setUpClass()
        self.t.setUp()

    def tearDown(self):
        self.t.tearDown()
        self.t.tearDownClass()

    def test_skips(self):
        """
        There's a skipped test at the start of the notebook to make sure skips don't
        affect test/cell correspondence.
        """
        self._assert_skipped(self.t.test_code_cell_1, "cell code not injected into test")

    def test_still_ok_after_markdown(self):
        """Correspondence still ok after markdown cell?"""
        self.t.test_code_cell_2()

    def test_still_ok_after_raw(self):
        """Correspondence still ok after raw cell?"""
        self.t.test_code_cell_3()

    def test_count(self):
        """No unexpected extra test methods"""
        test_methods = [mthd for mthd in dir(self.t) if mthd.startswith("test_code_cell")]
        self.assertListEqual(sorted(test_methods), ['test_code_cell_1', 'test_code_cell_2', 'test_code_cell_3'])


class TestCellCoverage(_TestCellTests):
    """Test that test_coverage works."""

    NBNAME = COVERAGE

    # the tests are independent, so it's fine to call setUpClass and
    # setUp before every test (and same for tearDown after). When we
    # are generating notebooks, we won't need the single, shared
    # notebook.
    def setUp(self):
        self.t = self.generated_tests.TestNotebook()
        self.t.setUpClass()
        self.t.setUp()

    def tearDown(self):
        self.t.tearDown()
        self.t.tearDownClass()

    def test_coverage(self):
        """
        There's a skipped test at the start of the notebook to make sure skips don't
        affect test/cell correspondence.
        """
        try:
            self.t.test_cell_coverage()
        except AssertionError as e:
            assert e.args[0] == 'Actual cell coverage 25.0 < minimum required of 50'
        else:
            raise ValueError("Cell coverage test should have failed.")


######

# should split this file up - but only after deciding on organization
# of module being tested

# TODO: there's a repeated pattern of cleaning up files generated
# during tests, but address
# https://github.com/jpmorganchase/nbcelltests/issues/125 before
# deciding how to handle that better here.

# runWithReturn

def test_basic_runWithReturn_pass():
    """Basic check - just that it runs without error"""
    generates = os.path.join(os.path.dirname(__file__), "_cell_coverage_test.py")
    if os.path.exists(generates):
        raise ValueError("Going to generate %s but it already exists." % generates)

    try:
        _ = runWithReturn(COVERAGE, rules={'cell_coverage': 10})
    finally:
        try:
            os.remove(generates)
        except Exception:
            pass


def test_basic_runWithReturn_fail():
    """Basic check - just that it fails"""
    generates = os.path.join(os.path.dirname(__file__), "_cell_coverage_test.py")
    if os.path.exists(generates):
        raise ValueError("Going to generate %s but it already exists." % generates)

    try:
        _ = runWithReturn(COVERAGE, rules={'cell_coverage': 100})
    except Exception:
        pass  # would need to alter run fn or capture output to check more exactly
    else:
        raise ValueError("coverage check should have failed, but didn't")
    finally:
        try:
            os.remove(generates)
        except Exception:
            pass


# runWithReport

def test_basic_runWithReport_pass():
    """Basic check - just that it runs without error"""
    generates = os.path.join(os.path.dirname(__file__), "_cell_coverage_test.py")
    if os.path.exists(generates):
        raise ValueError("Going to generate %s but it already exists." % generates)

    from nbcelltests.define import TestType
    try:
        ret = runWithReport(COVERAGE, executable=None, rules={'cell_coverage': 10})
    finally:
        try:
            os.remove(generates)
        except Exception:
            pass

    assert len(ret) == 1
    assert (ret[0].passed, ret[0].type, ret[0].message) == (1, TestType.CELL_COVERAGE, 'Testing cell coverage')


# def test_basic_runWithReport_fail():
#    from nbcelltests.define import TestType
#    # TODO it fails here, but it shouldn't, right? we want to be able to report
#    ret = runWithReport(COVERAGE, executable=None, rules={'cell_coverage':100})
#    assert len(ret) == 1
#    assert (ret[0].passed, ret[0].type, ret[0].message) == (False, TestType.CELL_COVERAGE, 'Testing cell coverage')


# runWithHTMLReturn

def test_basic_runWithHTMLReturn_pass():
    """Check it runs without error and generates the expected files and html."""
    generates = [os.path.join(os.path.dirname(__file__), "_cell_coverage_test.py"),
                 os.path.join(os.path.dirname(__file__), "_cell_coverage_test.html")]
    exists_check = [os.path.exists(f) for f in generates]
    if any(exists_check):
        raise ValueError("Going to generate %s but already exist(s)" % [f for f, exists in zip(generates, exists_check) if exists])

    try:
        ret = runWithHTMLReturn(COVERAGE, executable=None, rules={'cell_coverage': 10})

        for f in generates:
            assert os.path.exists(f), "Should have generated %s but did not" % f
    finally:
        try:
            for f in generates:
                os.remove(f)
        except Exception:
            pass

        _check(ret, coverage_result="Passed")


def test_basic_runWithHTMLReturn_fail():
    """Check it runs without error and generates the expected files and html."""
    generates = [os.path.join(os.path.dirname(__file__), "_cell_coverage_test.py"),
                 os.path.join(os.path.dirname(__file__), "_cell_coverage_test.html")]
    exists_check = [os.path.exists(f) for f in generates]
    if any(exists_check):
        raise ValueError("Going to generate %s but already exist(s)" % [f for f, exists in zip(generates, exists_check) if exists])

    try:
        ret = runWithHTMLReturn(COVERAGE, executable=None, rules={'cell_coverage': 100})

        for f in generates:
            assert os.path.exists(f), "Should have generated %s but did not" % f
    finally:
        try:
            for f in generates:
                os.remove(f)
        except Exception:
            pass

        _check(ret, coverage_result="Failed")


def _check(html, coverage_result):
    """
    Check html report contains expected results.

    coverage_result is 'Passed' or 'Failed' depending what you want to
    check.
    """
    html_soup = BeautifulSoup(html, "html.parser")

    tests_ran = False
    for p in html_soup.find_all("p"):
        # 1 cell test plus coverage test
        if p.text.startswith("2 tests ran in"):
            tests_ran = True
            break

    assert tests_ran

    expected_results = {
        "test_code_cell_1": "Skipped",
        "test_code_cell_2": "Passed",
        "test_code_cell_3": "Skipped",
        "test_code_cell_4": "Skipped",
        "test_code_cell_5": "Skipped",
        "test_cell_coverage": coverage_result,
    }

    actual_results = html_soup.find_all(class_="results-table-row")

    assert len(actual_results) == len(expected_results)

    for actual_result, expected_name in zip(sorted(actual_results, key=lambda x: x.find_next(class_="col-name").text),
                                            sorted(expected_results)):
        name = actual_result.find_next(class_="col-name").text
        state = actual_result.find_next(class_="col-result").text

        assert name.endswith(expected_name)
        assert state == expected_results[expected_name]


del _TestCellTests  # TODO: either make genuinely abstract, or don't use classes/inheritance at all here (since classes/inheritance are not meaningful here anyway).
