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

from nbcelltests.test import run

# TODO: we should generate the notebooks rather than having them as files
# (same for lint ones)
CUMULATIVE_RUN = os.path.join(os.path.dirname(__file__), '_cumulative_run.ipynb')
CELL_ERROR = os.path.join(os.path.dirname(__file__), '_cell_error.ipynb')
TEST_ERROR = os.path.join(os.path.dirname(__file__), '_test_error.ipynb')
TEST_FAIL = os.path.join(os.path.dirname(__file__), '_test_fail.ipynb')

# Hack. We want to test expected behavior in distributed situation,
# which we are doing via pytest --forked.
FORKED = '--forked' in sys.argv


def _assert_x_undefined(t):
    t.run_test("""
    try:
        x
    except NameError:
        pass
    else:
        raise Exception('x was already defined')
    """)

# TODO: This test file's manual use of unittest is brittle


def _import_from_path(pypath, f):
    import importlib.util
    spec = importlib.util.spec_from_file_location(pypath, f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _TestCellTests(unittest.TestCase):
    # abstract :)

    @classmethod
    def setUpClass(cls):
        """
        Generate test file from notebook, then import it, and make the
        resulting module available as "generated_tests" class attribute.
        """
        tf = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf8')
        tf_name = tf.name
        try:
            cls.generated_tests = _import_from_path("nbcelltests.tests.%s.%s" % (__name__, cls.__name__), run(cls.NBNAME, filename=tf_name))
            tf.close()
        finally:
            os.remove(tf_name)


class TestCumulativeRun(_TestCellTests):

    NBNAME = CUMULATIVE_RUN

    def test_state(self):
        """
                    cell    test   state
        0:           -       -       -
        
        1: either   x=0      -      x=0   (expected)
               or    -       -      x>0   (bad; x was previously defined in kernel)
        
        2: either   x+=1     -      x=1   (expected)
               or   x+=1     -      x>1   (bad)
        
        3: either   x+=1     -      x=2   (expected)
               or   x+=1     -      x>2   (bad)
        
        4: either    -      x+=1    x=3   (expected)
               or    -      x+=1    x>3   (bad)
        """
        t = self.generated_tests.TestNotebook()
        t.setUpClass()

        # check cell did not run
        # (no %cell in test)
        t.setUp()
        _assert_x_undefined(t)
        t.test_cell_0()
        _assert_x_undefined(t)
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # check cell ran
        # (%cell in test)
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_cell_1()
        t.run_test("""
        assert x == 0, x
        """)
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # check cumulative cells ran
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_cell_2()
        t.run_test("""
        assert x == 1, x
        """)
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # check cumulative cells ran (but not multiple times!)
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_cell_3()
        t.run_test("""
        assert x == 2, x
        """)
        t.tearDown()
        if FORKED:
            t.tearDownClass()

        # check test affects state
        if FORKED:
            t.setUpClass()
        t.setUp()
        t.test_cell_4()
        t.run_test("""
        assert x == 3, x
        """)
        t.tearDown()

        t.tearDownClass()


class TestExceptionInCell(_TestCellTests):

    NBNAME = CELL_ERROR

    def test_exception_in_cell_is_detected(self):
        t = self.generated_tests.TestNotebook()

        t.setUpClass()
        t.setUp()

        # cell should error out
        try:
            t.test_cell_0()
        except Exception as e:
            assert e.args[0].startswith("Cell execution caused an exception")
            assert e.args[0].endswith("My code does not even run")
        else:
            raise Exception("Cell should have errored out")
        finally:
            t.tearDown()
            t.tearDownClass()


class TestExceptionInTest(_TestCellTests):

    NBNAME = TEST_ERROR

    def test_exception_in_test_is_detected(self):
        t = self.generated_tests.TestNotebook()
        t.setUpClass()
        t.setUp()

        # caught cell error
        t.test_cell_0()

        t.tearDown()
        if FORKED:
            t.tearDownClass()

        if FORKED:
            t.setUpClass()
        t.setUp()

        _assert_x_undefined(t)

        # test should error out
        try:
            t.test_cell_1()
        except Exception as e:
            assert e.args[0].startswith("Cell execution caused an exception")
            assert e.args[0].endswith("My test is bad too")
        else:
            raise Exception("Test should have failed")
        finally:
            t.tearDown()
            t.tearDownClass()


class TestFailureInTest(_TestCellTests):

    NBNAME = TEST_FAIL

    def test_failure_is_detected(self):
        t = self.generated_tests.TestNotebook()
        t.setUpClass()
        t.setUp()

        # caught cell error
        try:
            t.test_cell_0()
        except Exception as e:
            assert e.args[0].startswith("Cell execution caused an exception")
            assert e.args[0].endswith("x should have been -1 but was 1")
        else:
            raise Exception("Test should have failed")
        finally:
            t.tearDown()
            t.tearDownClass()
