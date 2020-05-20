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

import unittest

from nbval.kernel import RunningKernel


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

    This is an abstract class; subclasses will supply the source of
    code cells and their associated tests in cells_and_tests, plus
    test methods as entry points for test runners.

    Note: 'cell' used in this class refers to cell number; 'cell
    content' typically refers to code_cell+test (depending what is
    passed in).
    """
    # abstract - subclasses will define KERNEL_NAME (TODO: make
    # actually abstract...)

    @classmethod
    def setUpClass(cls):
        cls.kernel = RunningKernel(cls.KERNEL_NAME)
        cls.cells_run = set()

    @classmethod
    def tearDownClass(cls):
        cls.kernel.stop()

    def run_test(self, cell):
        """
        Run any cells preceding cell (number) that have not already been
        run, then run cell itself.
        """
        # maybe do some assertions that we didn't get all messed up
        # with missing cells etc
        preceding_cells = set(range(1, cell))
        for preceding_cell in sorted(set(preceding_cells) - self.cells_run):
            self._run_cell(preceding_cell)
        self._run_cell(cell)

    def _run_cell(self, cell):
        # convenience method
        self._run(self.cells_and_tests[cell], "Running cell+test for code cell %d" % cell)
        # will only add if there was no error running
        self.cells_run.add(cell)

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


BASE = '''
import nbcelltests.tests_vendored

class TestNotebook(nbcelltests.tests_vendored.TestNotebookBase):
    KERNEL_NAME = "{kernel_name}"

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
