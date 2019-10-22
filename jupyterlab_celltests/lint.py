import nbformat
import os
import sys
import subprocess
from nbconvert import ScriptExporter
from tempfile import NamedTemporaryFile
from .shared import extract_extrametadata
from .define import LintMessage, LintType


def lint_lines_per_cell(lines_per_cell, metadata):
    ret = []
    passed = True

    if lines_per_cell:
        for i, lines_in_cell in enumerate(metadata.get('cell_lines', [])):
            if lines_in_cell <= lines_per_cell:
                ret.append(LintMessage(i+1, 'Checking lines in cell', LintType.LINES_PER_CELL, True))
            else:
                ret.append(LintMessage(i+1, 'Checking lines in cell', LintType.LINES_PER_CELL, False))
                passed = False
    return ret, passed


def lint_cells_per_notebook(cells_per_notebook, metadata):
    ret = []
    passed = True

    if cells_per_notebook:
        if metadata.get('cell_count', -1) <= cells_per_notebook:
            ret.append(LintMessage(-1, 'Checking cells per notebook', LintType.CELLS_PER_NOTEBOOK, True))
        else:
            ret.append(LintMessage(-1, 'Checking cells per notebook', LintType.CELLS_PER_NOTEBOOK, False))
            passed = False
    return ret, passed


def lint_function_definitions(function_definitions, metadata):
    ret = []
    passed = True

    if function_definitions:
        if metadata.get('functions', -1) <= function_definitions:
            ret.append(LintMessage(-1, 'Checking functions per notebook', LintType.FUNCTION_DEFINITIONS, True))
        else:
            ret.append(LintMessage(-1, 'Checking functions per notebook', LintType.FUNCTION_DEFINITIONS, False))
            passed = False
    return ret, passed


def lint_class_definitions(class_definitions, metadata):
    ret = []
    passed = True

    if class_definitions:
        if metadata.get('classes', -1) <= class_definitions:
            ret.append(LintMessage(-1, 'Checking classes per notebook', LintType.CLASS_DEFINITIONS, True))
        else:
            ret.append(LintMessage(-1, 'Checking classes per notebook', LintType.CLASS_DEFINITIONS, False))
            passed = False
    return ret, passed


def lint_cell_coverage(cell_coverage, metadata):
    ret = []
    passed = True

    if cell_coverage:
        if (metadata.get('test_count', 0)/metadata.get('cell_count', -1))*100 >= cell_coverage:
            ret.append(LintMessage(-1, 'Checking cell test coverage', LintType.CELL_COVERAGE, True))
        else:
            ret.append(LintMessage(-1, 'Checking cell test coverage', LintType.CELL_COVERAGE, False))
            passed = False
    return ret, passed


def run(notebook, executable=None, rules=None):
    nb = nbformat.read(notebook, 4)
    extra_metadata = extract_extrametadata(nb)
    ret = []
    passed = True

    rules = rules or {}
    extra_metadata.update(rules)

    if 'lines_per_cell' in extra_metadata:
        lines_per_cell = extra_metadata.get('lines_per_cell', -1)
        lintret, lintfail = lint_lines_per_cell(lines_per_cell, extra_metadata)
        ret.extend(lintret)
        passed = passed and lintfail

    if 'cells_per_notebook' in extra_metadata:
        cells_per_notebook = extra_metadata.get('cells_per_notebook', -1)
        lintret, lintfail = lint_cells_per_notebook(cells_per_notebook, extra_metadata)
        ret.extend(lintret)
        passed = passed and lintfail

    if 'function_definitions' in extra_metadata:
        function_definitions = extra_metadata.get('function_definitions', -1)
        lintret, lintfail = lint_function_definitions(function_definitions, extra_metadata)
        ret.extend(lintret)
        passed = passed and lintfail

    if 'class_definitions' in extra_metadata:
        class_definitions = extra_metadata.get('class_definitions', -1)
        lintret, lintfail = lint_class_definitions(class_definitions, extra_metadata)
        ret.extend(lintret)
        passed = passed and lintfail

    if 'cell_coverage' in extra_metadata:
        cell_coverage = extra_metadata.get('cell_coverage', 0)
        lintret, lintfail = lint_cell_coverage(cell_coverage, extra_metadata)
        ret.extend(lintret)
        passed = passed and lintfail

    if executable:
        exp = ScriptExporter()
        (body, resources) = exp.from_notebook_node(nb)
        try:
            tf = NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf8')
            tf.write(body)
            tf.close() # for Windows
            executable.append(tf.name)
            ret2 = _run_and_capture_utf8(executable)
            msg = ret2.stdout + '\t' + ret2.stderr
            ret.append(LintMessage(-1, 'Checking lint:\n' + msg.strip(), LintType.LINTER, False if msg.strip() else True))
        finally:
            os.remove(tf.name)

    return ret, passed


def _run_and_capture_utf8(args):
    # PYTHONIOENCODING for pyflakes on Windows
    run_kw = {'env': dict(os.environ, PYTHONIOENCODING='utf8')} if sys.platform == 'win32' else {}
    return subprocess.run(args, capture_output=True, encoding='utf-8', **run_kw)


def runWithReturn(notebook, executable=None, rules=None):
    ret, fail = run(notebook)
    return ret


def runWithHTMLReturn(notebook, executable=None, rules=None):
    ret = ''
    ret_tmp, fail = run(notebook, executable)
    for lint in ret_tmp:
        lint = lint.to_html()
        ret += '<p>' + lint + '</p>'
    return '<div style="display: flex; flex-direction: column;">' + ret + '</div>', fail


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Usage:python -m jupyterlab_celltests.lint <ipynb file>')
    notebook = sys.argv[1]
    ret, passed = run(notebook, ['flake8', '--ignore=W391'])
    if passed:
        print('\n'.join(str(r) for r in ret))
        sys.exit(0)
    else:
        print('\n'.join(str(r) for r in ret))
        sys.exit(1)
