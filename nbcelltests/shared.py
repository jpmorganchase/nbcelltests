# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
import sys
import ast
import re
import nbconvert


# note: could consider combining these separate classes
class FnDefCounter(ast.NodeVisitor):
    """Counts function definitions (ignoring class methods)."""

    count = 0

    def visit_FunctionDef(self, node):
        self.count += 1

    def visit_ClassDef(self, node):
        return

    # to count lambdas, add visit_Lambda


class ClassDefCounter(ast.NodeVisitor):
    """Counts class declarations."""

    count = 0

    def visit_ClassDef(self, node):
        self.count += 1


class MagicsRecorder(ast.NodeVisitor):
    """Record magics.

    Magics are like this:
      * get_ipython().run_line_magic(name, line)
      * get_ipython().run_cell_magic(name, line, cell)

    Or this (py2):
      * get_ipython().magic(magic_string)

    """

    magic_fn_names_py3 = set(['run_line_magic',
                              'run_cell_magic'])
    magic_fn_names_py2 = set(['magic'])

    magic_fn_names = magic_fn_names_py3 | magic_fn_names_py2

    def __init__(self):
        self.seen = set()

    def visit_Call(self, node):
        if hasattr(node.func, 'attr') and node.func.attr in self.magic_fn_names:
            # should maybe find ipython's own parsing code and use that instead
            if node.func.value.func.id == 'get_ipython':
                magic_name = node.args[0].s
                if node.func.attr in self.magic_fn_names_py2:
                    magic_name = magic_name.split()[0]  # (again, find ipython's parsing?)
                self.seen.add(magic_name)


# Note: I think it's confusing to insert the actual counts into the
# metadata.  Why not keep them separate?
#
# Note: this always does everything, which might be unnecessary
# (e.g. if haven't asked for magics checking, don't need to extract
# them)
def extract_extrametadata(notebook, override=None, noqa_regex=None):
    if noqa_regex is not None:
        noqa_regex = re.compile(noqa_regex)
        if not noqa_regex.groups == 1:
            raise ValueError("noqa_regex must contain one capture group (specifying the rule)")

    base = notebook.metadata.get('celltests', {})
    override = override or {}
    base['lines'] = 0  # TODO: is this used?
    base['kernelspec'] = notebook.metadata.get('kernelspec', {})

    # "python code" things (e.g. number of function definitions)...
    # note: no attempt to be clever here (so e.g. "%time def f: pass" would be missed, as would the contents of
    # a cell using %%capture cell magics; possible to handle those scenarios but would take more effort)
    code = nbconvert.PythonExporter(exclude_raw=True).from_notebook_node(notebook)[0]
    # notebooks start with "coding: utf-8"
    parsed_source = ast.parse(code.encode('utf8') if sys.version_info[0] == 2 else code)

    fn_def_counter = FnDefCounter()
    fn_def_counter.visit(parsed_source)
    base['functions'] = fn_def_counter.count

    class_counter = ClassDefCounter()
    class_counter.visit(parsed_source)
    base['classes'] = class_counter.count

    # alternative to doing it this way would be to check the ipython
    # souce for %magic, %%magics before it's converted to regular python
    magics_recorder = MagicsRecorder()
    magics_recorder.visit(parsed_source)
    base['magics'] = magics_recorder.seen

    # "notebook structure" things...
    base['cell_count'] = 0
    base['cell_tested'] = []
    base['test_count'] = 0
    base['cell_lines'] = []
    base['noqa'] = set()

    for c in notebook.cells:
        if c['cell_type'] != 'code':
            continue

        # noqa comments can be in otherwise code-less cells
        if noqa_regex:
            for line in c['source'].split('\n'):
                noqa_match = noqa_regex.match(line)
                if noqa_match:
                    base['noqa'].add(noqa_match.group(1))

        if empty_ast(c['source']):
            continue

        base['cell_lines'].append(0)
        base['cell_tested'].append(False)
        base['cell_count'] += 1

        for line in c['source'].split('\n'):
            if not empty_ast(line):
                base['lines'] += 1
                base['cell_lines'][-1] += 1
        if cell_injected_into_test(get_test(c)):
            base['test_count'] += 1
            base['cell_tested'][-1] = True

    # in case you want to override notebook settings
    if override:
        base.update(override)

    return base


def get_test(cell):
    return lines2source(cell.get('metadata', {}).get('tests', []))


def empty_ast(source):
    """
    Whether the supplied source string has an empty ast.

    >>> empty_ast(" ")
    True

    >>> empty_ast("pass")
    False

    >>> empty_ast("# hello")
    True

    """
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        # If there's a syntax error, it's not an empty code cell.
        # Handling and communicating syntax errors is a general issue
        # (https://github.com/jpmorganchase/nbcelltests/issues/101).
        # Note: this will also handle magics.
        return False

    # TODO: py2 utf8
    return len(parsed.body) == 0


def only_whitespace(source):
    """
    Whether the supplied source string contains only whitespace.

    >>> only_whitespace(" ")
    True

    >>> only_whitespace("pass")
    False

    >>> only_whitespace("# hello")
    False
    """
    return len(source.strip()) == 0


# TODO drop the "token" part
CELL_INJ_TOKEN = r"%cell"
CELL_SKIP_TOKEN = r"# no %cell"


def source2lines(source):
    return source.splitlines(True)


def lines2source(lines):
    return "".join(lines)


def get_cell_inj_span(test_line):
    """
    Return the location of %cell in the given line as (start_index,
    end_index), or None if %cell does not occur.
    """
    if not test_line.strip().startswith(CELL_INJ_TOKEN):
        return None
    else:
        cell_start = test_line.index(CELL_INJ_TOKEN)
        cell_end = cell_start + len(CELL_INJ_TOKEN)
        return cell_start, cell_end


def cell_injected_into_test(test_source):
    """
    Return True if the corresponding cell is injected into the test,
    False if the cell is deliberately not injected, or None if there
    is no deliberate command either way.
    """
    inject = False
    run = None
    for test_line in source2lines(test_source):
        if inject is False and get_cell_inj_span(test_line) is not None:
            inject = True
        elif run is None and test_line.strip().startswith(CELL_SKIP_TOKEN):
            run = False

    if run is False and inject:
        raise ValueError("'%s' and '%s' are mutually exclusive but both were supplied:\n%s" % (CELL_SKIP_TOKEN, CELL_INJ_TOKEN, test_source))

    return inject or run


def get_coverage(metadata):
    if metadata['cell_count'] == 0:
        return 0
    return 100.0 * metadata['test_count'] / metadata['cell_count']
