# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
import json
import nbformat
import os
import shutil
import sys
import subprocess
import tempfile
from .define import TestMessage, TestType
from .shared import extract_extrametadata, get_coverage
from .tests_vendored import BASE, JSON_CONFD


def generateTests(notebook,
                  rules=None,
                  filename=None,
                  kernel_name="",
                  current_env=False):
    '''Runs no tests: just generates test script for supplied notebook. kernel_name and current_env 'will be passed to nbval'.

    Args:
        notebook (str): Path to notebook to run
        rules (list): list of extra rules to enforce
        filename (Optional[str]): filename to output the tests in, if not provided will use the name of the notebook prefixed with a "_" and .py ending
        kernel_name (Optional[str]): optional kernel name to use
        current_env (bool):
    Returns:
        str: name of file where tests were output
    '''
    nb = nbformat.read(notebook, 4)
    path = os.path.splitext(notebook)[0].split(os.path.sep)
    py_path = filename or os.path.join(os.path.sep.join(path[:-1]), "_{}_test.py".format(path[-1]))
    extra_metadata = extract_extrametadata(nb)
    rules = rules or {}
    extra_metadata.update(rules)

    # TODO: Coverage shouldn't be recorded at generation time as it
    # will go stale if the notebook changes. Should move to same
    # mechanism as source/tests. However, we plan to replace coverage
    # with code coverage measured during test execution.
    coverage = []
    if 'cell_coverage' in extra_metadata:
        coverage.append((get_coverage(extra_metadata), extra_metadata['cell_coverage']))

    # output tests to test file
    with open(py_path, 'w', encoding='utf-8') as fp:
        fp.write(BASE.format(kernel_name=kernel_name, current_env=current_env, path_to_notebook=notebook, coverage=coverage))

    return py_path


def run(notebook, html=False, executable=None, **kwargs):
    '''Run notebook's celltests in a subprocess and optionally return html report using pytest's --self-contained-html.

    Note - htlm report leaves behind the following generated files for
    "/path/to/notebook.ipynb":
      * /path/to/_notebook_test.py (notebook test script)
      * /path/to/_notebook_test.html (pytest's html report)
    '''
    name = generateTests(notebook, **kwargs)
    executable = executable or [sys.executable, '-m', 'pytest', '-vvv']

    if html:
        # return html report
        html = name.replace('.py', '.html')
        argv = executable + ['--html=' + html, '--self-contained-html', name]
        subprocess.call(argv)
        with open(html, 'r', encoding='utf-8') as fp:
            return fp.read()

    # otherwise run inline
    argv = executable + [name]
    return subprocess.call(argv)


def _pytest_nodeid_prefix(path):
    return os.path.splitdrive(path)[1][1:].replace(os.path.sep, '/') + '/'


def runWithReport(notebook, executable=None, collect_only=False, **run_kw):
    '''Run notebook's celltests in a subprocess and return exit status.'''
    tmpd = tempfile.mkdtemp()
    py_file = os.path.join(tmpd, os.path.basename(notebook).replace('.ipynb', '.py'))
    json_file = os.path.join(tmpd, os.path.basename(notebook).replace('.ipynb', '.json'))
    _ = run(notebook, filename=py_file, **run_kw)
    ret = []
    try:
        # enable collecting info via json
        with open(os.path.join(tmpd, 'conftest.py'), 'w', encoding='utf8') as f:
            f.write(JSON_CONFD)
        executable = executable or [sys.executable, '-m', 'pytest', '-v']
        argv = executable + ['--internal-json-report=' + json_file, py_file]
        if collect_only:
            argv.append('--collect-only')
        subprocess.call(argv)
        with open(json_file, 'r', encoding='utf-8') as f:
            # load json from file
            data = json.load(f)

        data = [d for d in data['reports'] + data['collected_items'] if d.get('nodeid', '') and (collect_only or d.get('when') == 'call')]
        prefix = _pytest_nodeid_prefix(tmpd)
        for node in data:
            # replace relative path, strip leading ::
            node['nodeid'] = node['nodeid'].replace(prefix, '').strip(':')

            if node.get('outcome') == 'passed':
                outcome = 1
            elif 'outcome' not in node:
                outcome = 0
            else:
                outcome = -1

            if 'test_cell_coverage' in node['nodeid']:
                ret.append(TestMessage(-1, 'Testing cell coverage', TestType.CELL_COVERAGE, outcome))
            elif 'test_cell' in node['nodeid']:
                cell_no = node['nodeid'].rsplit('_', 1)[-1]
                ret.append(TestMessage(int(cell_no) + 1, 'Testing cell', TestType.CELL_TEST, outcome))
            else:
                continue
    finally:
        shutil.rmtree(tmpd)
    return ret


def _runWithHTMLReturnNoPytest(notebook, executable=None, **run_kw):
    '''internal method to avoid pytest HTML'''
    ret = ''
    executable = executable or [sys.executable, '-m', 'pytest', '-v']
    ret_tmp = run(notebook, **run_kw)
    for test in ret_tmp:
        test = test.to_html()
        ret += '<p>' + test + '</p>'
    return '<div style="display: flex; flex-direction: column;">' + test + '</div>'
