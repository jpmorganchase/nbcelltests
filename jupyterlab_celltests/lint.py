import nbformat
import sys
from .shared import extract_extrametadata


def lint_lines_per_cell(lines_per_cell, metadata):
    ret = ''
    passed = True

    if lines_per_cell:
        for i, lines_in_cell in enumerate(metadata.get('cell_lines', [])):
            ret += "Checking lines in cell %d:" % i
            if lines_in_cell <= lines_per_cell:
                ret += "\tPASSED\n"
            else:
                ret += "\tFAILED\n"
                passed = False
    return ret, passed


def lint_cells_per_notebook(cells_per_notebook, metadata):
    ret = ''
    passed = True

    if cells_per_notebook:
        ret += 'Checking cells per notebook <= %d:' % cells_per_notebook
        if metadata.get('cell_count', -1) <= cells_per_notebook:
            ret += "\tPASSED"
        else:
            ret += "\tFAILED"
            passed = False
    return ret, passed


def lint_function_definitions(function_definitions, metadata):
    ret = ''
    passed = True

    if function_definitions:
        ret += 'Checking functions per notebook <= %d:' % function_definitions
        if metadata.get('functions', -1) <= function_definitions:
            ret += "\tPASSED"
        else:
            ret += "\tFAILED"
            passed = False
    return ret, passed


def lint_class_definitions(class_definitions, metadata):
    ret = ''
    passed = True

    if class_definitions:
        ret += 'Checking classes per notebook <= %d:' % class_definitions
        if metadata.get('classes', -1) <= class_definitions:
            ret += "\tPASSED"
        else:
            ret += "\tFAILED"
            passed = False
    return ret, passed


def lint_cell_coverage(cell_coverage, metadata):
    ret = ''
    passed = True

    if cell_coverage:
        ret += "Checking cell test coverage >= %d:" % cell_coverage
        if (metadata.get('test_count', 0)/metadata.get('cell_count', -1))*100 >= cell_coverage:
            ret += "\tPASSED"
        else:
            ret += "\tFAILED"
            passed = False
    return ret, passed


def run(notebook):
    nb = nbformat.read(notebook, 4)
    extra_metadata = extract_extrametadata(nb)
    ret = ''
    passed = True

    if 'lines_per_cell' in extra_metadata:
        lines_per_cell = extra_metadata.get('lines_per_cell', -1)
        lintret, lintfail = lint_lines_per_cell(lines_per_cell, extra_metadata)
        ret += lintret
        passed = passed and lintfail

    if 'cells_per_notebook' in extra_metadata:
        cells_per_notebook = extra_metadata.get('cells_per_notebook', -1)
        lintret, lintfail = lint_cells_per_notebook(cells_per_notebook, extra_metadata)
        ret += lintret + '\n'
        passed = passed and lintfail

    if 'function_definitions' in extra_metadata:
        function_definitions = extra_metadata.get('function_definitions', -1)
        lintret, lintfail = lint_function_definitions(function_definitions, extra_metadata)
        ret += lintret + '\n'
        passed = passed and lintfail

    if 'class_definitions' in extra_metadata:
        class_definitions = extra_metadata.get('class_definitions', -1)
        lintret, lintfail = lint_class_definitions(class_definitions, extra_metadata)
        ret += lintret + '\n'
        passed = passed and lintfail

    if 'cell_coverage' in extra_metadata:
        cell_coverage = extra_metadata.get('cell_coverage', 0)
        lintret, lintfail = lint_cell_coverage(cell_coverage, extra_metadata)
        ret += lintret + '\n'
        passed = passed and lintfail
    return ret, passed


def runWithReturn(notebook):
    ret, fail = run(notebook)
    return ret


def runWithHTMLReturn(notebook):
    ret = ''
    ret_tmp, fail = run(notebook)
    for split in ret_tmp.split('\n'):
        ret += '<p>' + split.replace('FAILED', '<span style="color: red;">FAILED</span>') \
                            .replace('PASSED', '<span style="color: green;">PASSED</span>') \
                     + '</p>'
    return '<div style="display: flex; flex-direction: column;">' + ret + '</div>', fail


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Usage:python jupyterlab_celltests.lint <ipynb file>')
    notebook = sys.argv[1]
    ret, passed = run(notebook)
    if passed:
        print(ret)
        sys.exit(0)
    else:
        print(ret)
        sys.exit(1)
