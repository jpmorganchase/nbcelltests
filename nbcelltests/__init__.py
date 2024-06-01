# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
from .lint import run as runLint  # noqa: F401
from .test import run as runTest  # noqa: F401

__version__ = "0.2.3"


def _jupyter_server_extension_paths():
    return [{"module": "nbcelltests"}]


def _jupyter_server_extension_points():
    return [{"module": "nbcelltests"}]


def load_jupyter_server_extension(nb_server_app):
    # avoid pulling in extension whenever nbcelltests is imported (e.g. for cli)
    from .extension import _load_jupyter_server_extension

    _load_jupyter_server_extension(nb_server_app)
