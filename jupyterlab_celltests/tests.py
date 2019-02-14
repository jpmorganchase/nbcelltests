# import pytest
import nbformat
import sys
import subprocess


base = '''import unittest

class TestExtension(unittest.TestCase):
'''


def run(notebook):
    nb = nbformat.read(notebook, 4)
    name = notebook[:-6] + '_test.py'  # remove .ipynb, replace with _test.py

    sources = [c['source'].split('\n') for c in nb.cells]
    tests = [c['metadata'].get('tests', []) for c in nb.cells]

    cells = []
    indent = '    '

    for i, [code, test] in enumerate(zip(sources, tests)):
        cells.append([i, [], 'def test_cell%d(self):\n' % i])

        for line in test:
            if line.strip().startswith('%cell'):
                cells[-1][1].append(indent + line.replace('%cell', '# Cell {' + str(i) + '} content\n'))

                for c in code:
                    cells[-1][1].append(indent + line.replace('\n', '').replace('%cell', '') + c + '\n')
                cells[-1][1].append('\n')

            else:
                if not line[-1] == '\n':
                    cells[-1][1].append(indent + line + '\n')
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
                        if(c != '\n'):
                            to_write.append(indent + c)
                        else:
                            to_write.append(c)

                else:
                    break
            for c in code:
                if(c != '\n'):
                    to_write.append(indent + c)
                else:
                    to_write.append(c)

            if len(to_write) == 0:
                to_write.append(indent + 'pass')

            fp.writelines(to_write)
        fp.write('\n')
    return name


def runWithReturn(notebook):
    name = run(notebook)
    argv = ['py.test', name, '-v']
    return subprocess.check_output(argv)


def runWithHTMLReturn(notebook):
    name = run(notebook)
    html = name.replace('.py', '.html')
    argv = ['py.test', name, '-v', '--html=' + html, '--self-contained-html']
    subprocess.call(argv)
    with open(html, 'r') as fp:
        return fp.read()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('Usage:python jupyterlab_celltests.tests <ipynb file>')
    notebook = sys.argv[1]
    name = run(notebook)
    argv = ['py.test', name, '-v', '--html=' + name.replace('.py', '.html'), '--self-contained-html']
    print(' '.join(argv))
    subprocess.call(argv)

    # doesnt refresh modules, dont use
    # print('running from main')
    # pytest.main([name, '-v', '--cov=' + name])
