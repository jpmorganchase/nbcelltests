import nbformat
import os
import sys
import subprocess
from nbconvert import ScriptExporter
from tempfile import NamedTemporaryFile
from .shared import extract_extrametadata
from .define import LintMessage, LintType

# TODO why do these fns take a parameter that's also present in
# metadata?  (e.g. lint function take lines_per_cell, but that's
# already in metadata)

# TODO: there's duplication with tests here. Should both use same
# underlying code. Also, some of these things are not lint (e.g.
# test coverage, while some of the tests are really just lint).


def lint_lines_per_cell(lines_per_cell, metadata):
    ret = []
    if lines_per_cell < 0:
        return [], True
    for i, lines_in_cell in enumerate(metadata.get('cell_lines', [])):
        # TODO: ambiguous - e.g. cell 0 or first cell?
        ret.append(
            LintMessage(
                i + 1,
                'Checking lines in cell (max={max_}; actual={actual})'.format(
                    max_=lines_per_cell,
                    actual=lines_in_cell),
                LintType.LINES_PER_CELL,
                lines_in_cell <= lines_per_cell))
    return ret, all([x.passed for x in ret])


def lint_cells_per_notebook(cells_per_notebook, metadata):
    if cells_per_notebook < 0:
        return [], True
    cell_count = metadata.get('cell_count', -1)
    passed = cell_count <= cells_per_notebook
    return [LintMessage(-1, 'Checking cells per notebook (max={max_}; actual={actual})'.format(max_=cells_per_notebook, actual=cell_count), LintType.CELLS_PER_NOTEBOOK, passed)], passed


def lint_function_definitions(function_definitions, metadata):
    if function_definitions < 0:
        return [], True
    functions = metadata.get('functions', -1)
    passed = functions <= function_definitions
    return [LintMessage(-1, 'Checking functions per notebook (max={max_}; actual={actual})'.format(max_=function_definitions, actual=functions), LintType.FUNCTION_DEFINITIONS, passed)], passed


def lint_class_definitions(class_definitions, metadata):
    if class_definitions < 0:
        return [], True
    classes = metadata.get('classes', -1)
    passed = classes <= class_definitions
    return [LintMessage(-1, 'Checking classes per notebook (max={max_}; actual={actual})'.format(max_=class_definitions, actual=classes), LintType.FUNCTION_DEFINITIONS, passed)], passed


# TODO: I think this isn't lint and should be removed.
def lint_cell_coverage(cell_coverage, metadata):
    if cell_coverage < 0:
        return [], True
    measured_cell_coverage = 100 * metadata.get('test_count', 0) / metadata.get('cell_count', -1)
    passed = measured_cell_coverage >= cell_coverage
    return [LintMessage(-1, 'Checking cell test coverage (min={min_}; actual={actual})'.format(min_=cell_coverage, actual=measured_cell_coverage), LintType.CELL_COVERAGE, passed)], passed


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
            tf.close()
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
    return subprocess.run(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', **run_kw)


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
