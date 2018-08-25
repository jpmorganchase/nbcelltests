import nbformat
import unittest
import sys


class TestExtension(unittest.TestCase):
    def __init__(self, sources, tests):
        self.sources = sources
        self.tests = tests
        super(TestExtension, self).__init__('test_cells')

    def test_cells(self):
        with open('tmp.py', 'w') as fp:
            for code, test in zip(self.sources, self.tests):
                for line in test:
                    if line.strip().startswith('%cell_standalone'):
                        for c in code:
                            fp.write(line.replace('%cell_standalone', ''))
                            fp.write(c)
                            fp.write('\n')
                    elif line.strip().startswith('%cell'):
                        for c in code:
                            fp.write(line.replace('%cell', ''))
                            fp.write(c)
                            fp.write('\n')
                    else:
                        fp.write(line)


def run(notebook_path):
    nb = nbformat.read(notebook, 4)

    sources = [c['source'].split('\n') for c in nb.cells]
    tests = [c['metadata'].get('tests', []) for c in nb.cells]

    test = TestExtension(sources, tests)
    res = test.run()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Usage:python jupyterlab_celltests.tests <ipynb file>')
    notebook = sys.argv[1]
    run(notebook)
