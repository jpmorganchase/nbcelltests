# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
from ._version import __version__  # noqa: F401


def _jupyter_server_extension_paths():
    return [{
        "module": "nbcelltests.extension"
    }]
