import ast


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


def extract_cellsources(notebook):
    return [c['source'].split('\n') for c in notebook.cells if c.get('cell_type') == 'code']


def extract_celltests(notebook):
    return [c['metadata'].get('tests', []) for c in notebook.cells]


# TODO: I think it's confusing to insert the actual counts into the metadata.
# Why not keep them separate?
def extract_extrametadata(notebook, override=None):
    base = notebook.metadata.get('celltests', {})
    override = override or {}
    base['cell_count'] = 0
    base['cell_tested'] = []
    base['test_count'] = 0
    base['cell_lines'] = []
    base['lines'] = 0  # TODO: is this used?
    base['functions'] = 0
    base['classes'] = 0

    for c in notebook.cells:
        if c.get('cell_type') in ('markdown', 'raw',):
            continue

        base['cell_lines'].append(0)
        base['cell_tested'].append(False)
        base['cell_count'] += 1

        parsed_source = ast.parse(c['source'])
        fn_def_counter = FnDefCounter()
        fn_def_counter.visit(parsed_source)
        base['functions'] += fn_def_counter.count

        class_counter = ClassDefCounter()
        class_counter.visit(parsed_source)
        base['classes'] += class_counter.count

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
