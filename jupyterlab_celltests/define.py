from enum import Enum


class LintType(Enum):
    LINES_PER_CELL = 'lines_per_cell'
    CELLS_PER_NOTEBOOK = 'cells_per_notebook'
    FUNCTION_DEFINITIONS = 'function_definitions'
    CLASS_DEFINITIONS = 'class_definitions'
    CELL_COVERAGE = 'cell_coverage'
    LINTER = 'linter'
    KERNELSPEC = 'kernelspec'
    MAGICS = 'magics'


class TestType(Enum):
    LINES_PER_CELL = 'lines_per_cell'
    CELLS_PER_NOTEBOOK = 'cells_per_notebook'
    FUNCTION_DEFINITIONS = 'function_definitions'
    CLASS_DEFINITIONS = 'class_definitions'
    CELL_COVERAGE = 'cell_coverage'
    CELL_TEST = 'cell_test'


class LintMessage(object):
    def __init__(self, cell, message, type, passed=False):
        self.cell = cell
        self.message = message
        self.type = type
        self.passed = passed

    def __repr__(self):
        ret = 'PASSED: ' if self.passed else 'FAILED: '
        ret += self.message
        ret += " (Cell %d)" % self.cell if self.cell > 0 else " (Notebook)"
        return ret

    def to_html(self):
        ret = '<span style="color: green;">PASSED&nbsp;</span>' if self.passed else '<span style="color: red;">FAILED&nbsp;</span>'
        ret += self.message
        ret += "(Cell %d)" % self.cell if self.cell > 0 else " (Notebook)"
        return ret


class TestMessage(object):
    def __init__(self, cell, message, type, passed=0):
        self.cell = cell
        self.message = message
        self.type = type
        self.passed = passed

    def __repr__(self):
        ret = 'PASSED: ' if self.passed > 0 else 'FAILED: ' if self.passed < 0 else 'NOT RUN: '
        ret += self.message
        ret += " (Cell %d)" % self.cell if self.cell > 0 else " (Notebook)"
        return ret

    def to_html(self):
        ret = '<span style="color: green;">PASSED&nbsp;</span>' if self.passed else '<span style="color: red;">FAILED&nbsp;</span>'
        ret += self.message
        ret += "(Cell %d)" % self.cell if self.cell > 0 else " (Notebook)"
        return ret
