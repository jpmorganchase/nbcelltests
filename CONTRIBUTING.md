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

To make a new release of nbcelltests from a fork, you can follow the
procedure below to have package building and testing occur on neutral
CI machines across multiple platforms. This is best viewed as a
somewhat asynchronous process, during which you'll likely want to be
working on other things. If you are further from release and want to
iterate faster, you can of course use local commands and environments
to build and test packages (see the Makefile, e.g. `make dist`).

1. Assuming `jpmorgan/celltests` is `upstream` (note: package uploads to azure feed not possible from forks).
2. The version in `.bumpversion.cfg` should already be something like `(0, 2, 0, 'alpha', 0)` or similar (i.e. some pre-release version that is ahead of the most recent version at pypi). If not, you should increment: `bumpversion patch` (replace `patch` with whatever is appropriate for the current release, e.g. `minor`, `major`, etc) - This will also create a git commit (but not a tag). You will need to do this in your fork, then open a PR and get it approved and merged. Say the version is now `(0, 2, 0, 'alpha', 0)`. 
3. After your PR is merged, update your fork, and then `git tag -a v0.2.0a0 -m "Release new alpha"` followed by `git push upstream --tags v0.2.0a0` - Pushing the tag will trigger python and npm package builds on azure, and upload to [our azure feed](https://dev.azure.com/tpaine154/jupyter/_packaging?_a=feed&feed=packages-testing).
4. Assuming packages were built and tested successfully on azure, you should then manually check the resulting packages:
    - Install and test the packages generated above in a clean environment (containing python and node.js).
        - See `.azure/test-template.yml` for the commands run by CI to install and test from the azure feed.
        - There are no tests of the labextension, so run jupyterlab with a sample notebook and check you can run lint tests, run cell tests, write tests, etc.
    - Inspect the sdist, wheel, and npm tgz to make sure they contain the right files, version numbers, etc.
5. You can upload release candidates to pypi and npm if you want to do an extra check:
    - pypi: `twine check /path/to/dist/* && twine upload /path/to/dist/*` (updating the path to match what you downloaded from azure).
    - npm: `npm publish --tag beta /path/to/nbcelltests-0.2.0-alpha.0.tgz` (updating the filename to match what you downloaded from azure).
6. If there's a problem with the packages, fix the issue, then go back to step 2.
7. Once satisfied with the packages, repeat steps 2 and 3, using `bumpversion` in step 2 either to set or increment `release` to `final` (e.g.  `bumpversion release`). Grab the resulting releases from azure and upload to pypi and npm.
8. At some point (?) after the release, bump the version to (?).
