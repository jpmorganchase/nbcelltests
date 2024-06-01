import argparse
import sys

from .lint import run as runLint
from .test import run as runTest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("option", help="Which option to run", default="lint", choices=("lint", "test"))

    parser.add_argument("notebook", help="On which notebook to run")

    parser.add_argument(
        "--lines_per_cell",
        help="How many lines to allowed per cell",
        type=int,
    )

    parser.add_argument(
        "--cells_per_notebook",
        help="How many cells are allowed per notebook",
        type=int,
    )

    parser.add_argument(
        "--function_definitions",
        help="How many function definitions are allowed per notebook",
        type=int,
    )

    parser.add_argument(
        "--class_definitions",
        help="How many class definitions are allowed per notebook",
        type=int,
    )

    parser.add_argument(
        "--kernelspec",
        help="Requirements of the kernelspec used in the notebook",
    )

    parser.add_argument(
        "--kernelspec_requirements",
        help="Requirements of the kernelspec used in the notebook",
    )

    parser.add_argument(
        "--magics_allowlist",
        help="Magics to explicitly allow",
    )

    parser.add_argument(
        "--magics_denylist",
        help="Magics to explicitly deny",
    )

    parser.add_argument(
        "--executable",
        help="String executable to execute lint/test",
    )

    # process args
    args = parser.parse_args()

    rules = {}
    if args.lines_per_cell:
        rules["lines_per_cell"] = args.lines_per_cell
    if args.cells_per_notebook:
        rules["cells_per_notebook"] = args.cells_per_notebook
    if args.function_definitions:
        rules["function_definitions"] = args.function_definitions
    if args.class_definitions:
        rules["class_definitions"] = args.class_definitions
    if args.kernelspec and args.kernelspec_requirements:
        rules["kernelspec"] = args.kernelspec
        rules["kernelspec_requirements"] = args.kernelspec_requirements
    if args.magics_allowlist:
        rules["magics_allowlist"] = args.magics_allowlist
    if args.magics_denylist:
        rules["magics_denylist"] = args.magics_denylist

    if args.option == "lint":
        ret, passed = runLint(
            args.notebook,
            html=False,
            executable=args.executable.split(" ") if args.executable else None,
            rules=rules,
            run_python_linter=True,
        )
        print("\n".join(str(r) for r in ret))
        sys.exit(passed)
    else:
        runTest(
            args.notebook,
            html=False,
            executable=args.executable.split(" ") if args.executable else None,
            rules=rules,
        )


if __name__ == "__main__":
    main()
