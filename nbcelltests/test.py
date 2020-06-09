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


def run(notebook, rules=None, filename=None, override_kernel_name=""):
    """Runs no tests: just generates test script for supplied notebook."""
    nb = nbformat.read(notebook, 4)
    name = filename or os.path.splitext(notebook)[0] + '_test.py'
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
    with open(name, 'w', encoding='utf-8') as fp:
        fp.write(BASE.format(override_kernel_name=override_kernel_name, path_to_notebook=notebook, coverage=coverage))

    return name


def runWithReturn(notebook, executable=None, rules=None):
    """
    Run notebook's celltests in a subprocess and return exit status.

    rules: coverage requirements (if any).
    """
    name = run(notebook, rules=rules)
    executable = executable or [sys.executable, '-m', 'pytest', '-v']
    argv = executable + [name]
    return subprocess.check_output(argv)


def _pytest_nodeid_prefix(path):
    return os.path.splitdrive(path)[1][1:].replace(os.path.sep, '/') + '/'


def runWithReport(notebook, executable=None, rules=None, collect_only=False):
    tmpd = tempfile.mkdtemp()
    py_file = os.path.join(tmpd, os.path.basename(notebook).replace('.ipynb', '.py'))
    json_file = os.path.join(tmpd, os.path.basename(notebook).replace('.ipynb', '.json'))
    _ = run(notebook, filename=py_file, rules=rules)
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


def runWithHTMLReturn(notebook, executable=None, rules=None):
    """
    Run notebook's celltests in a subprocess and return html generated
    by pytest's --self-contained-html.

    rules: coverage requirements (if any).

    Note - leaves behind the following generated files for
    "/path/to/notebook.ipynb":
      * /path/to/notebook_test.py (notebook test script)
      * /path/to/notebook_test.html (pytest's html report)
    """
    name = run(notebook, rules=rules)
    html = name.replace('.py', '.html')
    executable = executable or [sys.executable, '-m', 'pytest', '-v']
    argv = executable + ['--html=' + html, '--self-contained-html', name]
    subprocess.call(argv)
    with open(html, 'r', encoding='utf-8') as fp:
        return fp.read()


def runWithHTMLReturn2(notebook, executable=None, rules=None):
    '''use custom return objects'''
    ret = ''
    executable = executable or [sys.executable, '-m', 'pytest', '-v']
    ret_tmp = run(notebook, rules=rules)
    for test in ret_tmp:
        test = test.to_html()
        ret += '<p>' + test + '</p>'
    return '<div style="display: flex; flex-direction: column;">' + test + '</div>'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Usage:python -m nbcelltests.test <ipynb file>')
    notebook = sys.argv[1]
    # TODO: seems likely this should use one of the above run fns.
    name = run(notebook)
    argv = [sys.executable, '-m', 'pytest', name, '-v', '--html=' + name.replace('.py', '.html'), '--self-contained-html']
    print(' '.join(argv))
    subprocess.call(argv)
