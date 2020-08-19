# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
from .rules import (lint_lines_per_cell, lint_cells_per_notebook,
                    lint_function_definitions, lint_class_definitions,
                    lint_kernelspec, lint_magics)
# noqa: F401

import nbformat
import os
import sys
import subprocess
from nbconvert import ScriptExporter
from tempfile import NamedTemporaryFile
from ..shared import extract_extrametadata
from ..define import LintMessage, LintType


def run(notebook, html=False, executable=None, rules=None, noqa_regex=None, run_python_linter=False):
    nb = nbformat.read(notebook, 4)
    extra_metadata = extract_extrametadata(nb, noqa_regex=noqa_regex)
    print(executable)
    executable = executable or ['flake8', '--ignore=W391']
    ret = []
    passed = True

    rules = rules or {}
    extra_metadata.update(rules)

    # TODO: consider warning if referring to non-existent rules
    # set() is for python 2; remove when py2 is fully dropped
    rules_to_remove = extra_metadata['noqa'] & set(extra_metadata.keys())
    for rule in rules_to_remove:
        del extra_metadata[rule]

    if 'lines_per_cell' in extra_metadata:
        lintret, lintpassed = lint_lines_per_cell(extra_metadata['cell_lines'], max_lines_per_cell=extra_metadata['lines_per_cell'])
        ret.extend(lintret)
        passed = passed and lintpassed

    if 'cells_per_notebook' in extra_metadata:
        lintret, lintpassed = lint_cells_per_notebook(extra_metadata['cell_count'], max_cells_per_notebook=extra_metadata['cells_per_notebook'])
        ret.extend(lintret)
        passed = passed and lintpassed

    if 'function_definitions' in extra_metadata:
        lintret, lintpassed = lint_function_definitions(extra_metadata['functions'], max_function_definitions=extra_metadata['function_definitions'])
        ret.extend(lintret)
        passed = passed and lintpassed

    if 'class_definitions' in extra_metadata:
        lintret, lintpassed = lint_class_definitions(extra_metadata['classes'], max_class_definitions=extra_metadata['class_definitions'])
        ret.extend(lintret)
        passed = passed and lintpassed

    if 'kernelspec_requirements' in extra_metadata:
        lintret, lintpassed = lint_kernelspec(kernelspec=extra_metadata['kernelspec'], kernelspec_requirements=extra_metadata['kernelspec_requirements'])
        ret.extend(lintret)
        passed = passed and lintpassed

    if 'magics_allowlist' in extra_metadata or 'magics_denylist' in extra_metadata:
        lintret, lintpassed = lint_magics(magics=extra_metadata['magics'], allowlist=extra_metadata.get('magics_allowlist', None), denylist=extra_metadata.get('magics_denylist', None))
        ret.extend(lintret)
        passed = passed and lintpassed

    if run_python_linter:
        exp = ScriptExporter()
        (body, resources) = exp.from_notebook_node(nb)
        tf = NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf8')
        tf_name = tf.name
        try:
            tf.write(body)
            tf.close()
            executable.append(tf_name)
            ret2 = _run_and_capture_utf8(executable)
            msg = ret2.stdout + '\t' + ret2.stderr
            msg = '\n'.join('\t{}'.format(_) for _ in msg.strip().replace(tf_name, '{} (in {})'.format(notebook, tf_name)).split('\n'))
            ret.append(LintMessage(-1,
                                   'Checking lint:\n' + msg,
                                   LintType.LINTER,
                                   False if msg else True))
        finally:
            os.remove(tf_name)

    if html:
        ret_html = ''
        for lint in ret:
            lint = lint.to_html()
            ret_html += '<p>' + lint + '</p>'
        return '<div style="display: flex; flex-direction: column;">' + ret_html + '</div>', passed

    return ret, passed


def _run_and_capture_utf8(args):
    # PYTHONIOENCODING for pyflakes on Windows
    run_kw = {'env': dict(os.environ, PYTHONIOENCODING='utf8')} if sys.platform == 'win32' else {}
    return subprocess.run(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', **run_kw)
