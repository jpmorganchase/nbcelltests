import nbformat
import sys
import subprocess
from .shared import extract_cellsources, extract_celltests, extract_extrametadata

BASE = '''import unittest


class TestExtension(unittest.TestCase):
'''

INDENT = '    '


def assemble_code(sources, tests):
    cells = []

    # for cell of notebook,
    # assemble code to write
    for i, [code, test] in enumerate(zip(sources, tests)):
        # add celltest
        cells.append([i, [], 'def test_cell%d(self):\n' % i])

        for line in test:
            # if testing the cell,
            # write code from cell
            if line.strip().startswith('%cell'):

                # add comment in test for readability
                cells[-1][1].append(INDENT + line.replace('%cell', '# Cell {' + str(i) + '} content\n'))

                # add all code for cell
                for c in code:
                    cells[-1][1].append(INDENT + line.replace('\n', '').replace('%cell', '') + c + '\n')

                cells[-1][1].append('\n')

            # else just write test
            else:
                cells[-1][1].append(INDENT + line)
                if not line[-1] == '\n':
                    # add newline if missing
                    cells[-1][1][-1] += '\n'

    return cells


def writeout_test(fp, cells):
    # base import and class
    fp.write(BASE)

    # grab all code to write out
    for i, code, meth in cells:
        fp.write('\n')
        fp.write(INDENT + meth)

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
    fp.write('\n')


def writeout_lines_per_cell(fp, lines_per_cell, metadata):
    if lines_per_cell:
        for i, lines_in_cell in enumerate(metadata.get('cell_lines', [])):
            fp.write(INDENT + 'def test_lines_per_cell_%d(self):\n' % i)
            fp.write(2*INDENT + 'assert {lines_in_cell} <= {limit}\n\n'.format(limit=lines_per_cell, lines_in_cell=lines_in_cell))


def writeout_cells_per_notebook(fp, cells_per_notebook, metadata):
    if cells_per_notebook:
        fp.write(INDENT + 'def test_cells_per_notebook(self):\n')
        fp.write(2*INDENT + 'assert {cells_in_notebook} <= {limit}\n\n'.format(limit=cells_per_notebook, cells_in_notebook=metadata.get('cell_count', -1)))


def writeout_function_definitions(fp, function_definitions, metadata):
    if function_definitions:
        fp.write(INDENT + 'def test_function_definition_count(self):\n')
        fp.write(2*INDENT + 'assert {functions_in_notebook} <= {limit}\n\n'.format(limit=function_definitions, functions_in_notebook=metadata.get('functions', -1)))


def writeout_class_definitions(fp, class_definitions, metadata):
    if class_definitions:
        fp.write(INDENT + 'def test_class_definition_count(self):\n')
        fp.write(2*INDENT + 'assert {classes_in_notebook} <= {limit}\n\n'.format(limit=class_definitions, classes_in_notebook=metadata.get('classes', -1)))


def writeout_cell_coverage(fp, cell_coverage, metadata):
    if cell_coverage:
        fp.write(INDENT + 'def test_cell_coverage(self):\n')
        fp.write(2*INDENT + 'assert {cells_covered} >= {limit}\n\n'.format(limit=cell_coverage, cells_covered=(metadata.get('test_count', 0)/metadata.get('cell_count', -1))*100))


def run(notebook):
    nb = nbformat.read(notebook, 4)
    name = notebook[:-6] + '_test.py'  # remove .ipynb, replace with _test.py

    sources = extract_cellsources(nb)
    tests = extract_celltests(nb)
    extra_metadata = extract_extrametadata(nb)
    cells = assemble_code(sources, tests)

    # output tests to test file
    with open(name, 'w') as fp:
        writeout_test(fp, cells)

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


def runWithReturn(notebook):
    name = run(notebook)
    argv = ['py.test', name, '-v']
    return subprocess.check_output(argv)


def runWithHTMLReturn(notebook):
    name = run(notebook)
    html = name.replace('.py', '.html')
    argv = ['py.test', name, '-v', '--html=' + html, '--self-contained-html']
    subprocess.call(argv)
    with open(html, 'r') as fp:
        return fp.read()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Usage:python jupyterlab_celltests.tests <ipynb file>')
    notebook = sys.argv[1]
    name = run(notebook)
    argv = ['py.test', name, '-v', '--html=' + name.replace('.py', '.html'), '--self-contained-html']
    print(' '.join(argv))
    subprocess.call(argv)
