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
from .shared import extract_extrametadata, get_coverage, is_empty, cell_injected_into_test
from .tests_vendored import BASE, JSON_CONFD

# TODO: eventually want assemble() and the rest to be doing something
# better than building up code in strings. It's tricky to work with,
# tricky to read, can't lint, can't test easily, unlikely to be
# generally correct, etc etc :)

# TODO: there are multiple definitions of "is tested", "is code cell"
# throughout the code.

INDENT = '    '


def assemble_code(notebook):
    cells = []
    code_cell = 0
    # notes:
    #   * code cell counting is 1 based
    #   * the only import in the template is nbcelltests.tests_vendored
    for i, cell in enumerate(notebook.cells, start=1):
        # TODO: duplicate definition how to get tests
        test_lines = cell.get('metadata', {}).get('tests', [])

        if cell.get('cell_type') != 'code':
            if len(test_lines) > 0:
                raise ValueError("Cell %d is not a code cell, but metadata contains test code!" % i)
            continue

        code_cell += 1

        if is_empty(cell['source']):
            skiptest = "@nbcelltests.tests_vendored.unittest.skip('empty code cell')\n" + INDENT
        elif is_empty("".join(test_lines).replace(r"%cell", "pass # no test was supplied")):
            skiptest = "@nbcelltests.tests_vendored.unittest.skip('no test supplied')\n" + INDENT
        elif not cell_injected_into_test(test_lines):
            skiptest = "@nbcelltests.tests_vendored.unittest.skip('cell code not injected into test')\n" + INDENT
        else:
            skiptest = ""

        # TODO: Use namedtuples for these:
        cells.append([code_cell, [], "%sdef test_code_cell_%d(self):\n" % (skiptest, code_cell)])

        if skiptest:
            cells[-1][1].append(INDENT + 'pass # code cell %d was skipped\n' % code_cell)
            continue

        for test_line in test_lines:
            if test_line.strip().startswith(r"%cell"):
                # add comment in test for readability
                cells[-1][1].append(INDENT + test_line.replace(r'%cell', '# Cell {' + str(code_cell) + '} content\n'))

                # add all code for cell
                for cell_line in cell['source'].split('\n'):
                    # TODO: is this going to replace %cell appearing in a comment?
                    cells[-1][1].append(INDENT + test_line.replace('\n', '').replace(r'%cell', '') + cell_line + '\n')

            # else just write test
            else:
                cells[-1][1].append(INDENT + test_line)
                if not test_line[-1] == '\n':
                    cells[-1][1][-1] += '\n'
    return cells


def writeout_test(fp, cells, kernel_name):
    fp.write(BASE.format(kernel_name=kernel_name))

    # write out source of cells+tests
    fp.write(INDENT + "cells_and_tests = {")
    for i, code, _ in cells:
        fp.write('\n')
        fp.write(INDENT * 2 + '%d: """\n' % i)
        for line in code:
            fp.write(INDENT + line)
        fp.write(INDENT * 2 + '""",\n')
    fp.write(INDENT + "}\n")

    # write out test methods
    for i, _, meth in cells:
        fp.write('\n')
        fp.write(INDENT + meth)
        fp.write(INDENT * 2 + 'self.run_test(%d)\n' % i)


def writeout_cell_coverage(fp, cell_coverage, metadata):
    if cell_coverage:
        fp.write(INDENT + 'def test_cell_coverage(self):\n')
        fp.write(
            2 *
            INDENT +
            'assert {cells_covered} >= {limit}, "Actual cell coverage {cells_covered} < minimum required of {limit}"\n\n'.format(
                limit=cell_coverage,
                cells_covered=get_coverage(metadata)))


def run(notebook, rules=None, filename=None):
    """Runs no tests: just generates test script for supplied notebook."""
    nb = nbformat.read(notebook, 4)
    name = filename or notebook[:-6] + '_test.py'  # remove .ipynb, replace with _test.py

    kernel_name = nb.metadata.get('kernelspec', {}).get('name', 'python')
    cells = assemble_code(nb)
    extra_metadata = extract_extrametadata(nb)
    rules = rules or {}
    extra_metadata.update(rules)

    # output tests to test file
    with open(name, 'w', encoding='utf-8') as fp:
        writeout_test(fp, cells, kernel_name)

        if 'cell_coverage' in extra_metadata:
            cell_coverage = extra_metadata['cell_coverage']
            writeout_cell_coverage(fp, cell_coverage, extra_metadata)

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
