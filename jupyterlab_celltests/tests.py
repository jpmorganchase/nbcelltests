import nbformat
import sys
import nose
import os
import os.path
import tempfile

base = '''import unittest
import nose


class TestExtension(unittest.TestCase):
'''


runner = '''

if __name__ == '__main__':
    argv = [{name}, '-v', '--with-coverage', '--cover-erase', '--cover-package=.']
    nose.run(defaultTest={name}, argv=argv)
'''


def run(notebook_path):
    nb = nbformat.read(notebook, 4)
    name = notebook.rsplit(os.path.sep, 1)[-1].replace('.ipynb', '') + '_test.py'

    sources = [c['source'].split('\n') for c in nb.cells]
    tests = [c['metadata'].get('tests', []) for c in nb.cells]

    cells = []
    indent = '    '

    for i, [code, test] in enumerate(zip(sources, tests)):
        cells.append([i, [], 'def test_cell%d(self):\n' % i])

        for line in test:
            if line.strip().startswith('%cell'):
                for c in code:
                    cells[-1][1].append(indent + line.replace('%cell', '') + c + '\n')

            else:
                cells[-1][1].append(indent + line)

    with open(name, 'w') as fp:
        fp.write(base)
        for i, code, meth in cells:
            fp.write('\n')
            fp.write(indent + meth)

            to_write = []
            for j, code2, _ in cells:
                if j < i:
                    for c in code2:
                        to_write.append(indent + c)
                else:
                    break
            for c in code:
                to_write.append(indent + c)

            if len(to_write) == 0:
                to_write.append(indent + 'pass')

            fp.writelines(to_write)
        fp.write(runner.format(name=name))
    return name

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Usage:python jupyterlab_celltests.tests <ipynb file>')
    notebook = sys.argv[1]
    name = run(notebook)
    argv = [name, '-v', '--with-coverage', '--cover-erase', '--cover-package=.']
    nose.run(defaultTest=name, argv=argv)
