import nbformat
import sys
import subprocess
from .shared import extract_extrametadata


def lint_lines_per_cell(fp, lines_per_cell, metadata):
    ret = ''
    fail = False
    if lines_per_cell:
        for i, lines_in_cell in enumerate(metadata.get('cell_lines', [])):
            ret += "Checking lines in cell %d\n" % i
            if lines_in_cell < lines_per_cell:
                ret += "\tPASSED\n"
            else:
                ret += "\tFAILED\n"
                fail = True
    return ret, fail


def lint_cells_per_notebook(fp, cells_per_notebook, metadata):
    ret = ''
    fail = False
    if cells_per_notebook:
        ret += 'Checking cells per notebook <= %d:\n' % cells_per_notebook
        if metadata.get('cell_count', -1) <= cells_per_notebook:
            ret += "\tPASSED\n"
        else:
            ret += "\tFAILED\n"
            fail = True
    return ret, fail


def lint_function_definitions(fp, function_definitions, metadata):
    ret = ''
    fail = False
    if function_definitions:
        ret += 'Checking functions per notebook <= %d:\n' % function_definitions
        if metadata.get('functions', -1) <= function_definitions:
            ret += "\tPASSED\n"
        else:
            ret += "\tFAILED\n"
            fail = True
    return ret, fail


def lint_class_definitions(fp, class_definitions, metadata):
    ret = ''
    fail = False

    if class_definitions:
        ret += 'Checking classes per notebook <= %d:\n' % class_definitions
        if metadata.get('classes', -1) <= class_definitions:
            ret += "\tPASSED\n"
        else:
            ret += "\tFAILED\n"
            fail = True
    return ret, fail


def lint_cell_coverage(fp, cell_coverage, metadata):
    ret = ''
    fail = False

    if cell_coverage:
        ret += "Checking cell test coverage >= %d:\n" % cell_coverage
        if (metadata.get('test_count', 0)/metadata.get('cell_count', -1))*100 >= cell_coverage:
            ret += "\tPASSED\n"
        else:
            ret += "\tFAILED\n"
            fail = True
    return ret, fail


def run(notebook):
    nb = nbformat.read(notebook, 4)
    extra_metadata = extract_extrametadata(nb)
    if 'lines_per_cell' in extra_metadata:
        lines_per_cell = extra_metadata.get('lines_per_cell', -1)
        lint_lines_per_cell(fp, lines_per_cell, extra_metadata)

    if 'cells_per_notebook' in extra_metadata:
        cells_per_notebook = extra_metadata.get('cells_per_notebook', -1)
        lint_cells_per_notebook(fp, cells_per_notebook, extra_metadata)

    if 'function_definitions' in extra_metadata:
        function_definitions = extra_metadata.get('function_definitions', -1)
        lint_function_definitions(fp, function_definitions, extra_metadata)

    if 'class_definitions' in extra_metadata:
        class_definitions = extra_metadata.get('class_definitions', -1)
        lint_class_definitions(fp, class_definitions, extra_metadata)

    if 'cell_coverage' in extra_metadata:
        pass
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

    # doesnt refresh modules, dont use
    # print('running from main')
    # pytest.main([name, '-v', '--cov=' + name])
