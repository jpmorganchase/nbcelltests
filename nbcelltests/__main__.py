import sys
import argparse
import subprocess
from .lint import run as runLint
from .test import run as runTest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'option',
        help='Which option to run',
        default='lint',
        choices=('lint', 'test'))

    parser.add_argument(
        'notebook',
        help='On which notebook to run')

    # process args
    args = parser.parse_args()

    if args.option == 'lint':
        ret, passed = runLint(args.notebook, ['flake8', '--ignore=W391'])
        if passed:
            print('\n'.join(str(r) for r in ret))
            sys.exit(0)
        else:
            print('\n'.join(str(r) for r in ret))
            sys.exit(1)
    else:
        name = runTest(args.notebook)


if __name__ == '__main__':
    main()
