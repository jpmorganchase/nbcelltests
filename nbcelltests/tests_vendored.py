# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#

# TODO go back and get version of nbval it was copied from, and record
# what modifications have been made.

# This file includes code copied from nbval under the following license:
# Copyright (C) 2014  Oliver W. Laslett  <O.Laslett@soton.ac.uk>
#               David Cortes-Ortuno
#           Maximilian Albert
#           Ondrej Hovorka
#           Hans Fangohr
#           (University of Southampton, UK)
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# Neither the names of the contributors nor the associated institutions
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


try:
    from Queue import Empty
except ImportError:
    from queue import Empty
import logging
import unittest

import nbformat
from nbval.kernel import RunningKernel

from nbcelltests.shared import empty_ast, cell_injected_into_test, source2lines, lines2source, get_cell_inj_span, get_test, only_whitespace, CELL_SKIP_TOKEN, CELL_INJ_TOKEN


def get_kernel(path_to_notebook):
    notebook = nbformat.read(path_to_notebook, 4)
    # TODO don't default kernel like this here (address as part of https://github.com/jpmorganchase/nbcelltests/issues/164)
    return notebook['metadata'].get('kernelspec', {}).get('name', 'python')


def _inject_cell_into_test(cell_source, test_source):
    """Inserts cell_source into test.

    The cell_source is inserted wherever %cell appears at the stripped
    start of a line.

    All lines of cell_source are prefixed with the same leading
    whitespace as %cell.

    Example:

      test:
        if x > 0:
            %cell # end of %cell
        assert x == 10
        assert z == 15

      cell:
        x*=5
        z = x + \
            5
        print(x)

      celltest:
        if x > 0:
            x*=5
            z = x + \
                5
            print(x) # end of %cell
        assert x == 10
        assert z == 15
    """
    celltest_lines = []
    for test_line in source2lines(test_source):
        cell_inj_span = get_cell_inj_span(test_line)
        if cell_inj_span is not None:
            prefix = test_line[0:cell_inj_span[0]]
            for cell_line in source2lines(cell_source):
                celltest_lines.append(prefix + cell_line)

            suffix = test_line[cell_inj_span[1]::]
            if len(suffix) > 0:
                if len(celltest_lines) == 0:
                    celltest_lines.append('')
                celltest_lines[-1] += suffix
        else:
            celltest_lines.append(test_line)
    return lines2source(celltest_lines)


def get_celltests(path_to_notebook):
    """
    Return a dictionary of {code cell number: celltest_info} for all
    non-empty code cells in the given notebook.

    celltest_info is a dictionary containing:

      * 'source' string of the test supplied for a cell, plus the
        cell itself wherever injected into the test using %cell.

      * 'cell_injected' flag indicating whether the cell was injected
        into the test
    """
    notebook = nbformat.read(path_to_notebook, 4)
    celltests = {}
    code_cell = 0
    for i, cell in enumerate(notebook.cells, start=1):
        test_source = lines2source(get_test(cell))
        test_ast_empty = empty_ast(_inject_cell_into_test("pass", test_source))

        if cell.get('cell_type') != 'code':
            if not test_ast_empty:
                raise ValueError("Cell %d is not a code cell, but metadata contains test code!" % i)
            continue

        code_cell += 1

        if empty_ast(cell['source']):  # TODO: maybe this should be only_whitespace?
            if not test_ast_empty:
                raise ValueError("Code cell %d is empty, but test contains code." % code_cell)
            continue

        cell_injected = cell_injected_into_test(test_source)

        if only_whitespace(test_source):
            celltest = cell['source']
            cell_injected = True
        elif cell_injected is None:
            raise ValueError(
                r"Test {}: cell code not injected into test; either add '{}' to the test, or add '{}' to deliberately suppress cell execution".format(
                    code_cell, CELL_INJ_TOKEN, CELL_SKIP_TOKEN))
        elif cell_injected is False:
            celltest = test_source
        else:
            celltest = _inject_cell_into_test(cell['source'], test_source)

        celltests[code_cell] = {'source': celltest, 'cell_injected': cell_injected}

    return celltests


def generate_name(testcase_func, param_num, param):
    """Used to generate parameterized method names like test_code_cell_n"""
    return "test_code_cell_%s" % param.args[0]


class TestNotebookBase(unittest.TestCase):
    """Base class for representing a notebook's code cells and their
    associated tests; can submit cells to a kernel, track which cells
    have been executed, and ensure all necessary cells are executed in
    order.

    For instance, requesting to run test_code_cell_7,
    test_code_cell_8, and test_code_cell_9 (in that order) will result
    in:

      1. test_code_cell_7: executes cells 1, 2, 3, 4, 5, 6, 7
      2. test_code_cell_8: executes cell 8
      3. test_code_cell_9: executes cell 9

    The above assumes all cells+tests succeed.

    If e.g. cell 3 fails, the above changes to:

      1. test_code_cell_7: executes cells 1, 2; fails on 3 (with a
                           message that cell 3 failed)
      2. test_code_cell_8: also fails on 3
      3. test_code_cell_9: also fails on 3

    Requesting to run test_code_cell_5 and test_code_cell_3 (in that order)
    will result in:

      1. test_code_cell_5: executes cells 1, 2, 3, 4, 5 (test passes)
      2. test_code_cell_3: execute nothing (test passes)


    When does a cell execute?
    -------------------------

    A cell's test will execute its corresponding cell wherever %cell
    appears at the start of a stripped line.

    If a cell does not have a test defined, or the test is only
    whitespace, the cell will be executed (i.e. the test will be
    assumed to be just %cell).

    If a cell's test contains a "# no %cell" comment line, the cell
    will not be executed (though the test will). Use for mocking out a
    whole cell (ideally it's better to avoid this and mock things the
    cell uses, but that might not be possible).

    Code cells that have an empty ast are considered empty. An
    exception will be raised if attempting to test empty code cells or
    non-code cells.


    Notes
    -----

    This is an abstract class; subclasses will supply the source of
    code cells and their associated tests in celltests, plus test
    methods as entry points for test runners.

    'cell' used in this class refers to cell number; 'cell content'
    typically refers to code_cell+test (depending what is passed in).

    """
    # abstract - subclasses will define KERNEL_NAME and celltests
    # (TODO: make actually abstract...)

    @classmethod
    def setUpClass(cls):
        cls.kernel = RunningKernel(cls.KERNEL_NAME)
        cls.celltests_run = set()

    @classmethod
    def tearDownClass(cls):
        cls.kernel.stop()

    def assert_coverage(self, cells_covered, min_required):
        assert cells_covered >= min_required, "Actual cell coverage %s < minimum required of %s" % (cells_covered, min_required)

    def run_test(self, cell):
        """
        Run any cells preceding cell (number) that have not already been
        run, then run cell itself.
        """
        preceding_cells = set(range(1, cell)) & self.celltests.keys()
        for preceding_cell in sorted(set(preceding_cells) - self.celltests_run):
            self._run_cell(preceding_cell)
        self._run_cell(cell)
        if not self.celltests[cell]['cell_injected']:
            # TODO: this will appear in the html report under the test
            # method as captured logging, but it would be better
            # reported as a warning by pytest. However, (a) pytest is
            # already reporting various spurious warnings
            # (e.g. traitlets deprecations), and (b) pytest warnings
            # are not being reported in the html we show right now.
            logging.warning("Cell %d was not executed as part of the cell test", cell)

    def _run_cell(self, cell):
        """Run cell and record its execution"""
        self._run(self.celltests[cell]["source"], "Running cell+test for code cell %d" % cell)
        self.celltests_run.add(cell)

    def _run(self, cell_content, description=''):
        """
        Send supplied cell_content (cell source string) to kernel and
        check it runs without exception.
        """
        # Start of code from nbval (with modifications)
        # https://github.com/computationalmodelling/nbval
        #
        # Modifications:
        #   * ? (things before 2020)
        #   * Add description to exception messages, so it's easy to see which
        #     cell is failing.
        msg_id = self.kernel.execute_cell_input(cell_content, allow_stdin=False)

        # Poll the shell channel to get a message
        try:
            self.kernel.await_reply(msg_id)
        except Empty:
            raise Exception('%s; Kernel timed out waiting for message!' % description)

        while True:
            # The iopub channel broadcasts a range of messages. We keep reading
            # them until we find the message containing the side-effects of our
            # code execution.
            try:
                # Get a message from the kernel iopub channel
                msg = self.kernel.get_message(stream='iopub')

            except Empty:
                raise Exception('%s; Kernel timed out waiting for message!' % description)

            # now we must handle the message by checking the type and reply
            # info and we store the output of the cell in a notebook node object
            msg_type = msg['msg_type']
            reply = msg['content']

            # Is the iopub message related to this cell execution?
            if msg['parent_header'].get('msg_id') != msg_id:
                continue

            # When the kernel starts to execute code, it will enter the 'busy'
            # state and when it finishes, it will enter the 'idle' state.
            # The kernel will publish state 'starting' exactly
            # once at process startup.
            if msg_type == 'status':
                if reply['execution_state'] == 'idle':
                    break
                else:
                    continue
            elif msg_type == 'execute_input':
                continue
            elif msg_type.startswith('comm'):
                continue
            elif msg_type == 'execute_reply':
                continue
            elif msg_type in ('display_data', 'execute_result'):
                continue
            elif msg_type == 'stream':
                # TODO: temporary/should not be here; needs fix in nbval
                if msg['content']['name'] == 'stderr':
                    raise Exception(msg['content']['text'])
                continue

            # if the message type is an error then an error has occurred during
            # cell execution. Therefore raise a cell error and pass the
            # traceback information.
            elif msg_type == 'error':
                traceback = '\\n' + '\\n'.join(reply['traceback'])
                msg = "%s; execution caused an exception" % description
                raise Exception(msg + '\\n' + traceback)

            # any other message type is not expected
            # should this raise an error?
            else:
                print("%s; unhandled iopub msg:" % description, msg_type)

        # End of code from nbval


# Fetches notebook source at import time. Don't necessarily think we
# should do the dynamic test generation this way; first priority was
# just to clean up so code's not built up in string.

BASE = '''
from parameterized import parameterized
from nbcelltests.tests_vendored import TestNotebookBase, get_celltests, get_kernel, generate_name

_celltests = get_celltests(r"{path_to_notebook}")
_kernel_name = get_kernel(r"{path_to_notebook}")

class TestNotebook(TestNotebookBase):
    KERNEL_NAME = "{override_kernel_name}" or _kernel_name
    celltests = _celltests

    @parameterized.expand([(i,) for i in _celltests], name_func=generate_name)
    def _test_code_cell(self, cell_num):
        self.run_test(cell_num)

    @parameterized.expand({coverage}, skip_on_empty=True, name_func=lambda *args: "test_cell_coverage")
    def _test_coverage(self, actual,required):
        self.assert_coverage(actual,required)
'''

JSON_CONFD = '''
import pytest
import json
import io

class JsonReporter:
    def __init__(self, config):
        self.config = config
        self.verbosity = self.config.option.verbose
        self.serializable_collection_reports = []
        self.serializable_test_reports = []
        self.serializable_collect_items = []

    # ---- These functions store captured test items and reports ----

    def pytest_runtest_logreport(self, report):
        """Store all test reports for evaluation on finish"""
        data = self.config.hook.pytest_report_to_serializable(
            config=self.config, report=report
        )
        self.serializable_test_reports.append(data)

    def pytest_collectreport(self, report):
        """Store all collected reports for evaluation on finish
        """
        data = self.config.hook.pytest_report_to_serializable(
            config=self.config, report=report
        )
        self.serializable_collection_reports.append(data)

    def pytest_collection_finish(self, session):
        if self.config.getoption("collectonly"):
            self.serializable_collect_items = [
                dict(nodeid=i.nodeid)
                for i in session.items
            ]


    # ---- Code below writes up report ----

    @pytest.hookimpl(hookwrapper=True)
    def pytest_sessionfinish(self, exitstatus):
        """Called when test session has finished.
        """
        yield
        with io.open(self.config.getoption("jsonpath"), "w", encoding="utf-8") as fp:
            json.dump(
                dict(
                    reports=self.serializable_collection_reports +
                        self.serializable_test_reports,
                    collected_items=self.serializable_collect_items,
                ),
                fp)

def pytest_configure(config):
    reporter = JsonReporter(config)
    config.pluginmanager.register(reporter, 'jsonreporter')

def pytest_addoption(parser):
    term_group = parser.getgroup("terminal reporting")
    term_group._addoption(
        '--internal-json-report', action='store', dest='jsonpath',
        metavar='path', default=None,
        help='create JSON report file at given path.')

'''
