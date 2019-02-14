__version__ = '0.0.3'


def _jupyter_server_extension_paths():
    return [{
        "module": "jupyterlab_celltests.extension"
    }]
