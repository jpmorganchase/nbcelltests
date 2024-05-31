# *****************************************************************************
#
# Copyright (c) 2019, the nbcelltests authors.
#
# This file is part of the nbcelltests library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#
import json
import os
import os.path
import nbformat
import sys
import tornado.gen
import tornado.web
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.utils import url_path_join

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

from .test import run as runTest
from .lint import run as runLint


class RunCelltestsHandler(JupyterHandler):
    executor = ThreadPoolExecutor(4)

    def initialize(self, rules=None, executable=None):
        self.rules = rules
        self.executable = executable

    @tornado.web.authenticated
    def get(self):
        self.finish({"status": 0, "rules": self.rules})

    @run_on_executor
    def _run(self, body, path, name):
        with TemporaryDirectory() as tempdir:
            path = os.path.abspath(os.path.join(tempdir, name))
            node = nbformat.from_dict(body.get("model"))
            nbformat.write(node, path)
            ret = runTest(path, html=True, executable=self.executable, rules=self.rules)
            return ret

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def post(self):
        body = json.loads(self.request.body)
        path = os.path.join(os.getcwd(), body.get("path"))
        name = os.path.basename(path)
        ret = yield self._run(body, path, name)
        self.finish({"status": 0, "test": ret})


class RunLintsHandler(JupyterHandler):
    executor = ThreadPoolExecutor(4)

    def initialize(self, rules=None, executable=None):
        self.rules = rules
        self.executable = executable

    @tornado.web.authenticated
    def get(self):
        self.finish({"status": 0, "rules": self.rules})

    @run_on_executor
    def _run(self, body, path, name):
        with TemporaryDirectory() as tempdir:
            path = os.path.abspath(os.path.join(tempdir, name))
            node = nbformat.from_dict(body.get("model"))
            nbformat.write(node, path)
            ret, status = runLint(
                path, html=True, executable=self.executable, rules=self.rules
            )
            return ret, status
            self.finish({"status": status, "lint": ret})

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def post(self):
        body = json.loads(self.request.body)
        path = os.path.join(os.getcwd(), body.get("path"))
        name = os.path.basename(path)
        ret, status = yield self._run(body, path, name)
        self.finish({"status": status, "lint": ret})


def _load_jupyter_server_extension(nb_server_app):
    """
    Called when the extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    web_app = nb_server_app.web_app

    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    # host_pattern = '.*$'
    print(
        "Installing nbcelltests handler on path %s"
        % url_path_join(base_url, "celltests")
    )

    rules = nb_server_app.config.get("JupyterLabCelltests", {}).get("rules", {})
    test_executable = nb_server_app.config.get("JupyterLabCelltests", {}).get(
        "test_executable", [sys.executable, "-m", "pytest", "-v"]
    )
    lint_executable = nb_server_app.config.get("JupyterLabCelltests", {}).get(
        "lint_executable", [sys.executable, "-m", "flake8", "--ignore=W391"]
    )

    web_app.add_handlers(
        host_pattern,
        [
            (
                url_path_join(base_url, "celltests/test/run"),
                RunCelltestsHandler,
                {"rules": rules, "executable": test_executable},
            )
        ],
    )
    web_app.add_handlers(
        host_pattern,
        [
            (
                url_path_join(base_url, "celltests/lint/run"),
                RunLintsHandler,
                {"rules": rules, "executable": lint_executable},
            )
        ],
    )
