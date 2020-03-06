import json
import os
import os.path
import nbformat
import sys
import tornado.gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from notebook.base.handlers import IPythonHandler
from notebook.utils import url_path_join
try:
    from backports.tempfile import TemporaryDirectory
except ImportError:
    from tempfile import TemporaryDirectory

from .test import runWithHTMLReturn as runTest
from .lint import runWithHTMLReturn as runLint


class RunCelltestsHandler(IPythonHandler):
    executor = ThreadPoolExecutor(4)

    def initialize(self, rules=None, executable=None):
        self.rules = rules
        self.executable = executable

    def get(self):
        self.finish({'status': 0, 'test': self.rules})

    @run_on_executor
    def _run(self, body, path, name):
        with TemporaryDirectory() as tempdir:
            path = os.path.abspath(os.path.join(tempdir, name))
            node = nbformat.from_dict(body.get('model'))
            nbformat.write(node, path)
            ret = runTest(path, executable=self.executable, rules=self.rules)
            return ret

    @tornado.gen.coroutine
    def post(self):
        body = json.loads(self.request.body)
        path = os.path.join(os.getcwd(), body.get('path'))
        name = os.path.basename(path)
        ret = yield self._run(body, path, name)
        self.finish({'status': 0, 'test': ret})


class RunLintsHandler(IPythonHandler):
    executor = ThreadPoolExecutor(4)

    def initialize(self, rules=None, executable=None):
        self.rules = rules
        self.executable = executable

    def get(self):
        self.finish({'status': 0, 'linters': self.rules})

    @run_on_executor
    def _run(self, body, path, name):
        with TemporaryDirectory() as tempdir:
            path = os.path.abspath(os.path.join(tempdir, name))
            node = nbformat.from_dict(body.get('model'))
            nbformat.write(node, path)
            ret, status = runLint(path, executable=self.executable, rules=self.rules)
            return ret, status
            self.finish({'status': status, 'lint': ret})

    @tornado.gen.coroutine
    def post(self):
        body = json.loads(self.request.body)
        path = os.path.join(os.getcwd(), body.get('path'))
        name = os.path.basename(path)
        ret, status = yield self._run(body, path, name)
        self.finish({'status': status, 'lint': ret})


def load_jupyter_server_extension(nb_server_app):
    """
    Called when the extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    web_app = nb_server_app.web_app

    host_pattern = '.*$'
    base_url = web_app.settings['base_url']
    # host_pattern = '.*$'
    print('Installing jupyterlab_celltests handler on path %s' % url_path_join(base_url, 'celltests'))

    rules = nb_server_app.config.get('JupyterLabCelltests', {}).get('rules', {})
    test_executable = nb_server_app.config.get('JupyterLabCelltests', {}).get('test_executable', [sys.executable, '-m', 'pytest', '-v'])
    lint_executable = nb_server_app.config.get('JupyterLabCelltests', {}).get('lint_executable', [sys.executable, '-m', 'flake8', '--ignore=W391'])

    web_app.add_handlers(host_pattern, [(url_path_join(base_url, 'celltests/test/run'), RunCelltestsHandler, {'rules': rules, 'executable': test_executable})])
    web_app.add_handlers(host_pattern, [(url_path_join(base_url, 'celltests/lint/run'), RunLintsHandler, {'rules': rules, 'executable': lint_executable})])
