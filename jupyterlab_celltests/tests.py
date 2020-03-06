import json
import nbformat
import os
import shutil
import sys
import subprocess
import tempfile
from .define import TestMessage, TestType
from .shared import extract_cellsources, extract_celltests, extract_extrametadata
from .tests_vendored import BASE, JSON_CONFD

INDENT = '    '


def assemble_code(sources, tests):
    cells = []

    # for cell of notebook,
    # assemble code to write
    for i, [code, test] in enumerate(zip(sources, tests)):
        # add celltest
        cells.append([i, [], 'def test_cell_%d(self):\n' % i])

        for line in test:
            # if testing the cell,
            # write code from cell
            if line.strip().startswith(r'%cell'):

                # add comment in test for readability
                cells[-1][1].append(INDENT + line.replace(r'%cell', '# Cell {' + str(i) + '} content\n'))

                # add all code for cell
                for c in code:
                    cells[-1][1].append(INDENT + line.replace('\n', '').replace(r'%cell', '') + c + '\n')

                cells[-1][1].append('\n')

            # else just write test
            else:
                cells[-1][1].append(INDENT + line)
                if not line[-1] == '\n':
                    # add newline if missing
                    cells[-1][1][-1] += '\n'

    return cells


def writeout_test(fp, cells, kernel_name):
    # base import and class
    fp.write(BASE.format(kernel_name=kernel_name))

    # grab all code to write out
    for i, code, meth in cells:
        fp.write('\n')
        fp.write(INDENT + meth)
        fp.write(INDENT * 2 + 'self.run_test("""\n')
        to_write = []

        for j, code2, _ in cells:
            if j < i:
                for c in code2:
                    if(c != '\n'):
                        # indent if necessary
                        to_write.append(INDENT + c)
                    else:
                        to_write.append(c)

            else:
                break

        for c in code:
            if(c != '\n'):
                to_write.append(INDENT + c)
            else:
                to_write.append(c)

        if len(to_write) == 0:
            to_write.append(INDENT + 'pass')

        fp.writelines(to_write)
        fp.write('        """)\n')

    fp.write('\n')


def writeout_lines_per_cell(fp, lines_per_cell, metadata):
    if lines_per_cell:
        for i, lines_in_cell in enumerate(metadata.get('cell_lines', [])):
            fp.write(INDENT + 'def test_lines_per_cell_%d(self):\n' % i)
            fp.write(2 * INDENT + 'assert {lines_in_cell} <= {limit}\n\n'.format(limit=lines_per_cell, lines_in_cell=lines_in_cell))


def writeout_cells_per_notebook(fp, cells_per_notebook, metadata):
    if cells_per_notebook:
        fp.write(INDENT + 'def test_cells_per_notebook(self):\n')
        fp.write(2 * INDENT + 'assert {cells_in_notebook} <= {limit}\n\n'.format(limit=cells_per_notebook, cells_in_notebook=metadata.get('cell_count', -1)))


def writeout_function_definitions(fp, function_definitions, metadata):
    if function_definitions:
        fp.write(INDENT + 'def test_function_definition_count(self):\n')
        fp.write(2 * INDENT + 'assert {functions_in_notebook} <= {limit}\n\n'.format(limit=function_definitions, functions_in_notebook=metadata.get('functions', -1)))


def writeout_class_definitions(fp, class_definitions, metadata):
    if class_definitions:
        fp.write(INDENT + 'def test_class_definition_count(self):\n')
        fp.write(2 * INDENT + 'assert {classes_in_notebook} <= {limit}\n\n'.format(limit=class_definitions, classes_in_notebook=metadata.get('classes', -1)))


def writeout_cell_coverage(fp, cell_coverage, metadata):
    if cell_coverage:
        fp.write(INDENT + 'def test_cell_coverage(self):\n')
        fp.write(2 * INDENT + 'assert {cells_covered} >= {limit}\n\n'.format(limit=cell_coverage, cells_covered=(metadata.get('test_count', 0) / metadata.get('cell_count', -1)) * 100))


def run(notebook, rules=None, filename=None):
    nb = nbformat.read(notebook, 4)
    name = filename or notebook[:-6] + '_test.py'  # remove .ipynb, replace with _test.py

    kernel_name = nb.metadata.get('kernelspec', {}).get('name', 'python')

    sources = extract_cellsources(nb)
    tests = extract_celltests(nb)
    extra_metadata = extract_extrametadata(nb)
    cells = assemble_code(sources, tests)

    rules = rules or {}
    extra_metadata.update(rules)

    # output tests to test file
    with open(name, 'w', encoding='utf-8') as fp:
        writeout_test(fp, cells, kernel_name)

        if 'lines_per_cell' in extra_metadata:
            lines_per_cell = extra_metadata.get('lines_per_cell', -1)
            writeout_lines_per_cell(fp, lines_per_cell, extra_metadata)

        if 'cells_per_notebook' in extra_metadata:
            cells_per_notebook = extra_metadata.get('cells_per_notebook', -1)
            writeout_cells_per_notebook(fp, cells_per_notebook, extra_metadata)

        if 'function_definitions' in extra_metadata:
            function_definitions = extra_metadata.get('function_definitions', -1)
            writeout_function_definitions(fp, function_definitions, extra_metadata)

        if 'class_definitions' in extra_metadata:
            class_definitions = extra_metadata.get('class_definitions', -1)
            writeout_class_definitions(fp, class_definitions, extra_metadata)

        if 'cell_coverage' in extra_metadata:
            cell_coverage = extra_metadata.get('cell_coverage', 0)
            writeout_cell_coverage(fp, cell_coverage, extra_metadata)

    return name


def runWithReturn(notebook, executable=None, rules=None):
    name = run(notebook)
    executable = executable or [sys.executable, '-m', 'pytest', '-v']
    argv = executable + [name]
    return subprocess.check_output(argv)


def _pytest_nodeid_prefix(path):
    return os.path.splitdrive(path)[1][1:].replace(os.path.sep, '/') + '/'


def runWithReport(notebook, executable=None, rules=None, collect_only=False):
    tmpd = tempfile.mkdtemp()
    py_file = os.path.join(tmpd, os.path.basename(notebook).replace('.ipynb', '.py'))
    json_file = os.path.join(tmpd, os.path.basename(notebook).replace('.ipynb', '.json'))
    _ = run(notebook, filename=py_file)
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
            elif 'test_cells_per_notebook' in node['nodeid']:
                ret.append(TestMessage(-1, 'Testing cells per notebook', TestType.CELLS_PER_NOTEBOOK, outcome))
            elif 'test_class_definition_count' in node['nodeid']:
                ret.append(TestMessage(-1, 'Testing class definitions per notebook', TestType.CLASS_DEFINITIONS, outcome))
            elif 'test_function_definition_count' in node['nodeid']:
                ret.append(TestMessage(-1, 'Testing function definitions per notebook', TestType.FUNCTION_DEFINITIONS, outcome))
            elif 'test_lines_per_cell_' in node['nodeid']:
                cell_no = node['nodeid'].rsplit('_', 1)[-1]
                ret.append(TestMessage(int(cell_no) + 1, 'Testing lines per cell', TestType.LINES_PER_CELL, outcome))
            elif 'test_cell' in node['nodeid']:
                cell_no = node['nodeid'].rsplit('_', 1)[-1]
                ret.append(TestMessage(int(cell_no) + 1, 'Testing cell', TestType.CELL_TEST, outcome))
            else:
                continue
    finally:
        shutil.rmtree(tmpd)
    return ret


def runWithHTMLReturn(notebook, executable=None, rules=None):
    '''use pytest self contained html'''
    name = run(notebook)
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
    ret_tmp = run(notebook)
    for test in ret_tmp:
        test = test.to_html()
        ret += '<p>' + test + '</p>'
    return '<div style="display: flex; flex-direction: column;">' + test + '</div>'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Usage:python -m jupyterlab_celltests.tests <ipynb file>')
    notebook = sys.argv[1]
    name = run(notebook)
    argv = [sys.executable, '-m', 'pytest', name, '-v', '--html=' + name.replace('.py', '.html'), '--self-contained-html']
    print(' '.join(argv))
    subprocess.call(argv)
