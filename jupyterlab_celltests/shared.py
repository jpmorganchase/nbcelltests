# import pytest
import re

FUNCTION_REGEX = r'def (.*?):'
CLASS_REGEX = r'class (.*?):'


def extract_cellsources(notebook):
    return [c['source'].split('\n') for c in notebook.cells]


def extract_celltests(notebook):
    return [c['metadata'].get('tests', []) for c in notebook.cells]


def extract_extrametadata(notebook, override=None):
    base = notebook.metadata.get('celltests', {})
    override = override or {}
    base['cell_count'] = 0
    base['cell_tested'] = []
    base['test_count'] = 0
    base['cell_lines'] = []
    base['lines'] = 0
    base['functions'] = 0
    base['classes'] = 0

    foo_regex = re.compile(FUNCTION_REGEX)
    class_regex = re.compile(CLASS_REGEX)

    for c in notebook.cells:
        base['cell_lines'].append(0)
        base['cell_tested'].append(False)
        base['cell_count'] += 1
        for line in c['source'].split('\n'):
            base['lines'] += 1
            base['cell_lines'][-1] += 1
            if re.search(foo_regex, line):
                base['functions'] += 1
            if re.search(class_regex, line):
                base['classes'] += 1
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
    return meta['cell_tested']/meta['cell_count']*100
