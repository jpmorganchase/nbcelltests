import sys
import ast
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


def extract_cellsources(notebook):
    return [c['source'].split('\n') for c in notebook.cells if c.get('cell_type') == 'code']


def extract_celltests(notebook):
    return [c['metadata'].get('tests', []) for c in notebook.cells]


# Note: I think it's confusing to insert the actual counts into the
# metadata.  Why not keep them separate?
#
# Note: this always does everything, which might be unnecessary
# (e.g. if haven't asked for magics checking, don't need to extract
# them)
def extract_extrametadata(notebook, override=None):
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

    for c in notebook.cells:
        if c.get('cell_type') in ('markdown', 'raw',):
            continue

        base['cell_lines'].append(0)
        base['cell_tested'].append(False)
        base['cell_count'] += 1

        for line in c['source'].split('\n'):
            base['lines'] += 1
            base['cell_lines'][-1] += 1
        for t in c['metadata'].get('tests', []):
            if t.strip().startswith('%cell'):
                base['test_count'] += 1
                base['cell_tested'][-1] = True
                break

    # in case you want to override notebook settings
    if override:
        base.update(override)

    return base


def get_coverage(notebook):
    meta = extract_extrametadata(notebook)
    return meta['cell_tested'] / meta['cell_count'] * 100
