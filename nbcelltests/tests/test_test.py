# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
import tempfile
import os
import sys
import unittest

from bs4 import BeautifulSoup
import pytest
from nbval.kernel import CURRENT_ENV_KERNEL_NAME
import jupyter_client.kernelspec as kspec

from nbcelltests.test import run, runWithReturn, runWithReport, runWithHTMLReturn

# Some straightforward TODOs:
#
# - We should generate the notebooks rather than having them as files
#   (same for lint ones). Would also allow for simplification of test
#   class hierarchy.
#
# - Should use assert(Regex)Raises rather than manual try/catch
#
# - Some classes are abstract but not declared as such
#
# - Should split this file up - but only after deciding on
#   organization of modules being tested


# TODO: This test file's manual use of unittest is brittle

CUMULATIVE_RUN = os.path.join(os.path.dirname(__file__), '_cumulative_run.ipynb')
CELL_ERROR = os.path.join(os.path.dirname(__file__), '_cell_error.ipynb')
TEST_ERROR = os.path.join(os.path.dirname(__file__), '_test_error.ipynb')
TEST_FAIL = os.path.join(os.path.dirname(__file__), '_test_fail.ipynb')
COUNTING = os.path.join(os.path.dirname(__file__), '_cell_counting.ipynb')
NONCODE = os.path.join(os.path.dirname(__file__), '_non_code_cell.ipynb')
EMPTY_CELL_WITH_TEST = os.path.join(os.path.dirname(__file__), '_empty_cell_with_test.ipynb')
EMPTYAST_CELL_WITH_TEST = os.path.join(os.path.dirname(__file__), '_emptyast_cell_with_test.ipynb')
SKIPS = os.path.join(os.path.dirname(__file__), '_skips.ipynb')
COVERAGE = os.path.join(os.path.dirname(__file__), '_cell_coverage.ipynb')
CELL_NOT_INJECTED_OR_MOCKED = os.path.join(os.path.dirname(__file__), '_cell_not_injected_or_mocked.ipynb')
BROKEN_MAGICS = os.path.join(os.path.dirname(__file__), '_broken_magics.ipynb')
NO_CODE_CELLS = os.path.join(os.path.dirname(__file__), '_no_code_cells.ipynb')
KERNEL_CWD = os.path.join(os.path.dirname(__file__), '_kernel_cwd.ipynb')

INPUT_CELL_MULTILINE_STRING = os.path.join(os.path.dirname(__file__), '_input_cell_multiline_string.ipynb')
INPUT_TEST_MULTILINE_STRING = os.path.join(os.path.dirname(__file__), '_input_test_multiline_string.ipynb')
INPUT_CELL_NEWLINE_STRING = os.path.join(os.path.dirname(__file__), '_input_cell_newline_string.ipynb')
INPUT_TEST_NEWLINE_STRING = os.path.join(os.path.dirname(__file__), '_input_test_newline_string.ipynb')
INPUT_TEST_INJECTION_COMMENT = os.path.join(os.path.dirname(__file__), '_input_test_injection_comment.ipynb')

# Hack. We want to test expected behavior in distributed situation,
# which we are doing via pytest --forked.
FORKED = '--forked' in sys.argv

# Default to using kernel from current environment (like --current-env of nbval).
TEST_RUN_KW = {
    'current_env': int(os.environ.get("NBCELLTESTS_TESTS_CURRENT_ENV", "1")),
    'kernel_name': os.environ.get("NBCELLTESTS_TESTS_KERNEL_NAME", "")
}


def _assert_undefined(t, name='x'):
    """
    Convenience method to assert that x is not already defined in the kernel.
    """
    t._run("""
    try:
        %s
    except NameError:
        pass
    else:
        raise Exception('%s was already defined')
    """ % (name, name))


def _import_from_path(path, module_name):
    """
    Import and return a python module at the given path, with
    module_name setting __name__.

    See e.g. https://stackoverflow.com/a/67692.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _generate_test_module(notebook, module_name, run_kw=None):
    """
    Generate test file from notebook, then import it with __name__ set
    to module_name, and return it.
    """
    if run_kw is None:
        run_kw = TEST_RUN_KW

    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf8')
    tf_name = tf.name
    try:
        # the module name (__name__) doesn't really matter, but
        # will be nbcelltests.tests.test_tests.X, where X is
        # whatever concrete subclass is this method belongs to.
        generated_module = _import_from_path(run(notebook, filename=tf_name, **run_kw), module_name)
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

    def test_coverage(self):
        """
        Subclasses should override this if they want to check coverage.
        """
        assert not hasattr(self, 'test_cell_coverage')


class TestMethodGenerationError(_TestCellTests):
    """Tests of things that should fail during test script generation"""

    @classmethod
    def setUpClass(cls):
        # we're testing what happens in setUpClass
        pass

    def test_non_code_cell_with_test_causes_error(self):
        try:
            _generate_test_module(NONCODE, "module.name.irrelevant")
        except ValueError as e:
            assert e.args[0] == 'Cell 1 is not a code cell, but metadata contains test code!'
        else:
            raise Exception("Test script should fail to generate")

    def test_onlywhitespace_code_cell_with_test_causes_error(self):
        try:
            _generate_test_module(EMPTY_CELL_WITH_TEST, "module.name.irrelevant")
        except ValueError as e:
            assert e.args[0] == 'Code cell 2 is empty, but test contains code.'
        else:
            raise Exception("Test script should fail to generate")

    def test_emptyast_code_cell_with_test_causes_error(self):
        try:
            _generate_test_module(EMPTYAST_CELL_WITH_TEST, "module.name.irrelevant")
        except ValueError as e:
            assert e.args[0] == 'Code cell 2 is empty, but test contains code.'
        else:
            raise Exception("Test script should fail to generate")

    def test_code_not_injected_or_mocked(self):
        try:
            _generate_test_module(CELL_NOT_INJECTED_OR_MOCKED, "module.name.irrelevant")
        except ValueError as e:
            assert e.args[0].startswith('Test 5: cell code not injected into test')
        else:
            raise Exception("Test script should fail to generate")


class TestNoCodeCells(_TestCellTests):
    """Notebook with no code cells."""

    NBNAME = NO_CODE_CELLS

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

    def test_no_code_cells(self):
        test_methods = [mthd for mthd in dir(self.t) if mthd.startswith("test_code_cell")]
        assert len(test_methods) == 0


class TestSkips(_TestCellTests):
    """Tests that various conditions result in test methods being generated or not as expected."""

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
        """Empty cell and test"""
        assert not hasattr(self.t, "test_code_cell_1")

    def test_skip_no_code_code_cell(self):
        """Cell's just a comment, and no test."""
        assert not hasattr(self.t, "test_code_cell_2")

    def test_noskip_with_no_test_field_in_metadata(self):
        """Test where cell has no test metadata is just cell"""
        self.t.test_code_cell_3()
        self.t._run("assert x == 3")

    def test_noskip_with_completely_empty_test(self):
        """Test is just %cell where test is completely empty"""
        self.t.test_code_cell_4()
        self.t._run("assert x == 4")

    def test_noskip_with_deliberate_no_cell_injection(self):
        """Runs test but not cell"""
        self.t.test_code_cell_5()
        self.t._run("assert x == 6")  # value from test, not cell


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
        # (deliberate no cell in test, no code in test)
        # TODO: should this be no method, as there's only empty ast in the test
        t.setUp()
        _assert_undefined(t, 'x')
        t.test_code_cell_1()
        _assert_undefined(t, 'x')
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
        if FORKED:
            t.tearDownClass()

        # test defaults to %cell
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_code_cell_6()
        t._run("""
        assert y == 10
        """)
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # deliberate no %cell; cell 8 will check it's also not subsequently run
        # i.e. a will never be defined
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_code_cell_7()
        _assert_undefined(t, 'a')
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # check cell 7 above did not run
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_code_cell_8()
        t._run("""
        assert z == 1
        assert y == 10
        """)
        _assert_undefined(t, 'a')
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

        _assert_undefined(t, 'x')

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


# TODO: see https://github.com/computationalmodelling/nbval/issues/147
class TestSomeSanity(_TestCellTests):

    NBNAME = BROKEN_MAGICS

    @pytest.mark.xfail(reason="error messages on shell channel are ignored by nbval")
    def test_bad_magic_does_let_everything_pass(self):
        t = self.generated_tests.TestNotebook()

        t.setUpClass()
        t.setUp()

        # cell should error out
        try:
            t.test_code_cell_1()
        except Exception as e:
            assert e.args[0].startswith("UsageError: Line magic function `%magics2` not found.")
        else:
            raise Exception("Cell should have errored out")
        finally:
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
        There's an empty cell at the start of the notebook to make sure skips don't
        affect test/cell correspondence.
        """
        assert not hasattr(self.t, "test_code_cell_1")

    def test_still_ok_after_markdown(self):
        """Correspondence still ok after markdown cell?"""
        self.t.test_code_cell_2()

    def test_still_ok_after_raw(self):
        """Correspondence still ok after raw cell?"""
        self.t.test_code_cell_3()

    def test_count(self):
        """No unexpected extra test methods"""
        test_methods = [mthd for mthd in dir(self.t) if mthd.startswith("test_code_cell")]
        self.assertListEqual(sorted(test_methods), ['test_code_cell_2', 'test_code_cell_3'])


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


class _TestInput(unittest.TestCase):
    """Various input that breaks celltests."""

    # abstract

    @classmethod
    def setUpClass(cls):
        assert hasattr(cls, "NBNAME"), "Subclasses must have NBNAME attribute."  # TODO: make actually abstract
        cls.generated_tests = _generate_test_module(notebook=cls.NBNAME, module_name="nbcelltests.tests.%s.%s" % (__name__, cls.__name__))

    def setUp(self):
        self.t = self.generated_tests.TestNotebook()
        self.t.setUpClass()
        self.t.setUp()

    def tearDown(self):
        self.t.tearDown()
        self.t.tearDownClass()


class TestInputCellMultilineString(_TestInput):

    NBNAME = INPUT_CELL_MULTILINE_STRING

    def test_input_cell_multiline_string(self):
        self.t.test_code_cell_1()
        expected = "\nanything\n"
        self.t._run('assert problemc == """%s"""' % expected)


class TestInputTestMultilineString(_TestInput):

    NBNAME = INPUT_TEST_MULTILINE_STRING

    def test_input_celltest_multiline_string(self):
        self.t.test_code_cell_1()
        self.t._run("assert x == 1")
        expected = "\nanything\n"
        self.t._run('assert problemt == """%s"""' % expected)


class TestInputCellNewlineString(_TestInput):

    NBNAME = INPUT_CELL_NEWLINE_STRING

    def test_input_cell_newline_string(self):
        self.t.test_code_cell_1()
        expected = "\\n"
        self.t._run('assert problem == "%s"' % expected)


class TestInputTestNewlineString(_TestInput):

    NBNAME = INPUT_TEST_NEWLINE_STRING

    def test_input_celltest_newline_string(self):
        self.t.test_code_cell_1()
        self.t._run("assert problemc == 'x'")
        expected = "\\n"
        self.t._run("assert problemt == '%s'" % expected)


class TestInputTestInjectionComment(_TestInput):

    NBNAME = INPUT_TEST_INJECTION_COMMENT

    def test_input_celltest_injection_comment(self):
        self.t.test_code_cell_1()
        # though it's in the nb test itself, make sure the test
        # actually ran
        self.t._run("assert x == 1")


class TestKernelCwd(_TestCellTests):
    """Do we remember to set cwd?"""

    NBNAME = KERNEL_CWD

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

    def test_file_in_nb_dir(self):
        """file in same dir as nb, which nb will look for"""
        target_file = os.path.join(os.path.dirname(self.NBNAME), "hello.txt")
        if os.path.exists(target_file):
            raise ValueError("Going to generate %s but it already exists." % target_file)

        try:
            open(target_file, 'w').close()
            self.t.test_code_cell_1()
        finally:
            try:
                os.remove(target_file)
            except BaseException:
                pass


# some cryptic interface going on here, could be improved :)

@pytest.mark.parametrize(
    "notebook, current_env, kernel_name, exception, expected_text", [
        # the notebook's own kernel
        ('_kernel_check.ipynb', False, "", kspec.NoSuchKernel, "NOBODY WOULD EVER CALL A KERNEL THIS"),
        # current env's kernel
        ('_kernel_check.ipynb', True, "", None, CURRENT_ENV_KERNEL_NAME),
        # named kernel
        ('_kernel_check.ipynb', False, "OR THIS", kspec.NoSuchKernel, None),
        # default kernel if none specified or in nb
        ('_kernel_check1.ipynb', False, "python3", None, None),
        # inconsistent request
        ('_kernel_check.ipynb', True, "something", ValueError, "mutually exclusive"),
    ]
)
def test_kernel_selection(notebook, current_env, kernel_name, exception, expected_text):
    if not expected_text:
        expected_text = kernel_name

    nb = os.path.join(os.path.dirname(__file__), notebook)

    def make_test_mod():
        return _generate_test_module(nb, module_name="nbcelltests.tests.%s.%s" % (__name__, "test_kernel_selection"),
                                     run_kw=dict(current_env=current_env, kernel_name=kernel_name))

    if exception:
        try:
            test_mod = make_test_mod()
            test_mod.TestNotebook.setUpClass()
        except exception as e:
            assert e.args[0].endswith(expected_text)
        else:
            raise ValueError("Expected exception %s(%s) to be raised", (exception, expected_text))
    else:
        test_mod = make_test_mod()
        test_mod.TestNotebook.setUpClass()
        assert test_mod.TestNotebook.kernel.km.kernel_name == expected_text

######


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
        _ = runWithReturn(COVERAGE, rules={'cell_coverage': 10}, **TEST_RUN_KW)
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
        _ = runWithReturn(COVERAGE, rules={'cell_coverage': 100}, **TEST_RUN_KW)
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
        ret = runWithReport(COVERAGE, executable=None, rules={'cell_coverage': 10}, **TEST_RUN_KW)
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
        ret = runWithHTMLReturn(COVERAGE, executable=None, rules={'cell_coverage': 10}, **TEST_RUN_KW)

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
        ret = runWithHTMLReturn(COVERAGE, executable=None, rules={'cell_coverage': 100}, **TEST_RUN_KW)

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
        if p.text.startswith("5 tests ran in"):
            tests_ran = True
            break

    assert tests_ran

    expected_results = {
        "test_code_cell_2": "Passed",
        "test_code_cell_3": "Passed",
        "test_code_cell_4": "Passed",
        "test_code_cell_5": "Passed",
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


# TODO: either make genuinely abstract, or don't use classes/inheritance at all here (since classes/inheritance are not meaningful here anyway).
del _TestCellTests
del _TestInput
