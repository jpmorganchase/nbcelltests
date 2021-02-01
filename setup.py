from setuptools import setup, find_packages
from codecs import open
from os import path

from jupyter_packaging import (
    create_cmdclass,
    install_npm,
    ensure_targets,
    combine_commands,
    get_version,
)

pjoin = path.join

name = "nbcelltests"
here = path.abspath(path.dirname(__file__))
jshere = path.join(here, "js")
version = get_version(pjoin(here, name, "_version.py"))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read().replace("\r\n", "\n")

requires = [
    'backports.tempfile ; python_version < "3"',
    "flake8",
    "nbconvert",
    "nbformat>=4.0.0",
    "nbval>=0.9.1",
    "notebook",
    "parameterized",
    "pytest>=4.4.0",
    "pytest-cov",
    "pytest-html>=1.20.0",
]

dev_requires = requires + [
    "black>=20.",
    "beautifulsoup4",
    "bump2version>=1.0.0",
    "flake8>=3.7.8",
    "flake8-black>=0.2.1",
    "mock",
    "pytest",
    "pytest-cov>=2.6.1",
    "pytest-xdist",
    "Sphinx>=1.8.4",
    "sphinx-markdown-builder>=0.5.2",
]

data_spec = [
    # Lab extension installed by default:
    ("share/jupyter/lab/extensions", "js/lab-dist", "jupyterlab_celltests-*.tgz"),
    # Config to enable server extension by default:
    ("etc/jupyter/jupyter_server_config.d", "jupyter-config", "*.json"),
]


cmdclass = create_cmdclass("js", data_files_spec=data_spec)
cmdclass["js"] = combine_commands(
    install_npm(jshere, build_cmd="build:all"),
    ensure_targets(
        [pjoin(jshere, "lib", "index.js"), pjoin(jshere, "style", "index.css")]
    ),
)


setup(
    name=name,
    version=version,
    description="Cell-by-cell tests for JupyterLab",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jpmorganchase/nbcelltests",
    author="The nbcelltests authors",
    license="Apache 2.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: Jupyter",
    ],
    cmdclass=cmdclass,
    keywords="jupyter jupyterlab",
    packages=find_packages(),
    install_requires=requires,
    extras_require={"dev": dev_requires},
    entry_points={
        "console_scripts": [
            "nbcelltests=nbcelltests.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
