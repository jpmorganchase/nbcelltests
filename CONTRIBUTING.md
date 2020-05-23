# Contributing

Thank you for your interest in contributing to nbcelltests!

We invite you to contribute enhancements. Upon review you will be required to complete the [Contributor License Agreement (CLA)](https://github.com/jpmorganchase/cla) before we are able to merge. 

If you have any questions about the contribution process, please feel free to send an email to [open_source@jpmorgan.com](mailto:open_source@jpmorgan.com).

## Reporting bugs, feature requests, etc.

To report bugs, request new features or similar, please open an issue on the Github
repository.

A good bug report includes:

- Expected behavior
- Actual behavior
- Steps to reproduce (preferably as minimal as possible)
- Possibly any output from the browser console (typically available via Ctrl + Shift + J or via F12).

## Minor changes, typos etc.

Minor changes can be contributed by navigating to the relevant files on the Github repository,
and clicking the "edit file" icon. By following the instructions on the page you should be able to
create a pull-request proposing your changes. A repository maintainer will then review your changes,
and either merge them, propose some modifications to your changes, or reject them (with a reason for
the rejection).

## Setting up a development environment

If you want to help resolve an issue by making some changes that are larger than that covered by the above paragraph, it is recommended that you:

- Fork the repository on Github
- Clone your fork to your computer
- Run the following commands inside the cloned repository:
  - `pip install -e .[dev]` - This will install the Python package in development
    mode.
  - `jupyter labextension install .` - This will add the lab extension in development
    mode.
  - `jupyter serverextension enable --py nbcelltests` - This will enable the server extension (note: you might want to supply `--sys-prefix` or a related option here).
- Validate the install by running the tests:
  - `py.test` - This command will run the Python tests.
  - `yarn test` - This command will run the JS tests.

Once you have such a development setup, you should:

- Make the changes you consider necessary
- Run the tests to ensure that your changes does not break anything
- If you add new code, preferably write one or more tests for checking that your code works as expected.
- Commit your changes and publish the branch to your github repo.
- Open a pull-request (PR) back to the main repo on Github.

# Releasing

To make a new release of nbcelltests:

1. Assuming `jpmorgan/celltests` is `origin` (note: package uploads do not work from forks).
2. The version in `.bumpversion.cfg` should already be something like `(0, 2, 0, 'alpha', 0)` or similar (i.e. some pre-release version that is ahead of the most recent version at pypi). If not, you should increment: `bumpversion patch` (replace `patch` with whatever is appropriate for the current release, e.g. `minor`, `major`, etc) - This will also create a git commit (but not a tag). Say the version is now `(0, 2, 0, 'alpha', 0)`.
3. `git tag -a v0.2.0a0 "Release new alpha"`
4. `git push origin && git push origin --tags v0.2.0a0` - This will push the tag you created above, which will trigger python and npm package builds on azure, and upload to [our azure feed](https://dev.azure.com/tpaine154/jupyter/_packaging?_a=feed&feed=python-packages).
5. Check the resulting packages:
  - Install and test in a clean environment:
    - You can install for python with `pip install --index-url=https://pkgs.dev.azure.com/tpaine154/jupyter/_packaging/python-packages/pypi/simple/ nbcelltests==0.2.0a0 --extra-index-url=https://pypi.org/simple`, modifying as appropriate to use the wheel or the sdist, and to install the version you want to test. Following that, you should at least run the installed package's tests (after installing the test dependencies - see setup.py's dev dependencies): `python -m py.test --pyargs nbcelltests`.
    - Download the nbcelltests npm package from [our azure feed](https://dev.azure.com/tpaine154/jupyter/_packaging?_a=feed&feed=python-packages) and then install with `jupyter labextension install /path/to/nbcelltests-0.2.0-alpha.0.tgz` (replacing the filename with whatever you downloaded).
  - Inspect the sdist, wheel, and npm tgz to make sure they contain the right files, version numbers, etc.
6. You can upload release candidates to pypi and npm if you want:
  - pypi: `twine check /path/to/dist/* && twine upload /path/to/dist/*` (updating the path to match what you downloaded from azure).
  - npm: `npm publish --tag beta /path/to/nbcelltests-0.2.0-alpha.0.tgz` (updating the filename to match what you downloaded from azure).
7. Once satisfied, use `bumpversion` either to set or increment `release` to `final` (e.g.  `bumpversion release`), and then repeat steps 3 and 4. Grab the resulting releases from azure and upload to pypi and npm.
8. At some point after this (?), someone should bump the version to something something alpha (?).
