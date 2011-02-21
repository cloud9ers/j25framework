import logging
import os
import sys
import unittest2 as unittest

from multiprocessing import get_logger, current_process
from StringIO import StringIO

from celery import conf
from celery import platforms
from celery import signals
from celery import log
from celery.apps import worker as cd
from celery.bin.celeryd import WorkerCommand, main as celeryd_main
from celery.exceptions import ImproperlyConfigured
from celery.utils import patch
from celery.utils.functional import wraps

from celery.tests.compat import catch_warnings
from celery.tests.utils import execute_context


patch.ensure_process_aware_logger()


def disable_stdouts(fun):

    @wraps(fun)
    def disable(*args, **kwargs):
        sys.stdout, sys.stderr = StringIO(), StringIO()
        try:
            return fun(*args, **kwargs)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    return disable


class _WorkController(object):

    def __init__(self, *args, **kwargs):
        self.logger = log.get_default_logger()

    def start(self):
        pass


class Worker(cd.Worker):
    WorkController = _WorkController


class test_Worker(unittest.TestCase):
    Worker = Worker

    @disable_stdouts
    def test_queues_string(self):
        worker = self.Worker(queues="foo,bar,baz")
        self.assertEqual(worker.queues, ["foo", "bar", "baz"])

    @disable_stdouts
    def test_loglevel_string(self):
        worker = self.Worker(loglevel="INFO")
        self.assertEqual(worker.loglevel, logging.INFO)

    def test_run_worker(self):
        handlers = {}

        def i(sig, handler):
            handlers[sig] = handler

        p = platforms.install_signal_handler
        platforms.install_signal_handler = i
        try:
            w = self.Worker()
            w._isatty = False
            w.run_worker()
            for sig in "SIGINT", "SIGHUP", "SIGTERM":
                self.assertIn(sig, handlers)

            handlers.clear()
            w = self.Worker()
            w._isatty = True
            w.run_worker()
            for sig in "SIGINT", "SIGTERM":
                self.assertIn(sig, handlers)
            self.assertNotIn("SIGHUP", handlers)
        finally:
            platforms.install_signal_handler = p

    @disable_stdouts
    def test_startup_info(self):
        worker = self.Worker()
        worker.run()
        self.assertTrue(worker.startup_info())
        worker.loglevel = logging.DEBUG
        self.assertTrue(worker.startup_info())
        worker.loglevel = logging.INFO
        self.assertTrue(worker.startup_info())

    @disable_stdouts
    def test_run(self):
        self.Worker().run()
        self.Worker(discard=True).run()

        worker = self.Worker()
        worker.init_loader()
        worker.settings.DEBUG = True

        def with_catch_warnings(log):
            worker.run()
            self.assertIn("memory leak", log[0].message.args[0])

        context = catch_warnings(record=True)
        execute_context(context, with_catch_warnings)
        worker.settings.DEBUG = False

    @disable_stdouts
    def test_purge_messages(self):
        self.Worker().purge_messages()

    @disable_stdouts
    def test_init_queues(self):
        p, conf.QUEUES = conf.QUEUES, {
                "celery": {"exchange": "celery",
                           "binding_key": "celery"},
                "video": {"exchange": "video",
                           "binding_key": "video"}}
        try:
            self.Worker(queues=["video"]).init_queues()
            self.assertIn("video", conf.QUEUES)
            self.assertNotIn("celery", conf.QUEUES)

            conf.CREATE_MISSING_QUEUES = False
            self.assertRaises(ImproperlyConfigured,
                    self.Worker(queues=["image"]).init_queues)
            conf.CREATE_MISSING_QUEUES = True
            self.Worker(queues=["image"]).init_queues()
            self.assertIn("image", conf.QUEUES)
        finally:
            conf.QUEUES = p

    @disable_stdouts
    def test_on_listener_ready(self):
        worker_ready_sent = [False]

        def on_worker_ready(**kwargs):
            worker_ready_sent[0] = True

        signals.worker_ready.connect(on_worker_ready)

        self.Worker().on_listener_ready(object())
        self.assertTrue(worker_ready_sent[0])


class test_funs(unittest.TestCase):

    @disable_stdouts
    def test_set_process_status(self):
        worker = Worker(hostname="xyzza")
        prev1, sys.argv = sys.argv, ["Arg0"]
        try:
            st = worker.set_process_status("Running")
            self.assertIn("celeryd", st)
            self.assertIn("xyzza", st)
            self.assertIn("Running", st)
            prev2, sys.argv = sys.argv, ["Arg0", "Arg1"]
            try:
                st = worker.set_process_status("Running")
                self.assertIn("celeryd", st)
                self.assertIn("xyzza", st)
                self.assertIn("Running", st)
                self.assertIn("Arg1", st)
            finally:
                sys.argv = prev2
        finally:
            sys.argv = prev1

    @disable_stdouts
    def test_parse_options(self):
        cmd = WorkerCommand()
        opts, args = cmd.parse_options("celeryd", ["--concurrency=512"])
        self.assertEqual(opts.concurrency, 512)

    @disable_stdouts
    def test_run_worker(self):
        p, cd.Worker = cd.Worker, Worker
        try:
            cd.run_worker(discard=True)
        finally:
            cd.Worker = p

    @disable_stdouts
    def test_main(self):
        p, cd.Worker = cd.Worker, Worker
        s, sys.argv = sys.argv, ["celeryd", "--discard"]
        try:
            celeryd_main()
        finally:
            cd.Worker = p
            sys.argv = s


class test_signal_handlers(unittest.TestCase):

    class _Worker(object):
        stopped = False
        terminated = False
        logger = get_logger()

        def stop(self):
            self.stopped = True

        def terminate(self):
            self.terminated = True

    def psig(self, fun, *args, **kwargs):
        handlers = {}

        def i(sig, handler):
            handlers[sig] = handler

        p, platforms.install_signal_handler = \
                platforms.install_signal_handler, i
        try:
            fun(*args, **kwargs)
            return handlers
        finally:
            platforms.install_signal_handler = p

    @disable_stdouts
    def test_worker_int_handler(self):
        worker = self._Worker()
        handlers = self.psig(cd.install_worker_int_handler, worker)
        next_handlers = {}

        def i(sig, handler):
            next_handlers[sig] = handler

        p = platforms.install_signal_handler
        platforms.install_signal_handler = i
        try:
            self.assertRaises(SystemExit, handlers["SIGINT"],
                              "SIGINT", object())
            self.assertTrue(worker.stopped)
        finally:
            platforms.install_signal_handler = p

        self.assertRaises(SystemExit, next_handlers["SIGINT"],
                          "SIGINT", object())
        self.assertTrue(worker.terminated)

    @disable_stdouts
    def test_worker_int_handler_only_stop_MainProcess(self):
        process = current_process()
        name, process.name = process.name, "OtherProcess"
        try:
            worker = self._Worker()
            handlers = self.psig(cd.install_worker_int_handler, worker)
            self.assertRaises(SystemExit, handlers["SIGINT"],
                            "SIGINT", object())
            self.assertFalse(worker.stopped)
        finally:
            process.name = name

    @disable_stdouts
    def test_worker_int_again_handler_only_stop_MainProcess(self):
        process = current_process()
        name, process.name = process.name, "OtherProcess"
        try:
            worker = self._Worker()
            handlers = self.psig(cd.install_worker_int_again_handler, worker)
            self.assertRaises(SystemExit, handlers["SIGINT"],
                            "SIGINT", object())
            self.assertFalse(worker.terminated)
        finally:
            process.name = name

    @disable_stdouts
    def test_worker_term_handler(self):
        worker = self._Worker()
        handlers = self.psig(cd.install_worker_term_handler, worker)
        self.assertRaises(SystemExit, handlers["SIGTERM"],
                          "SIGTERM", object())
        self.assertTrue(worker.stopped)

    @disable_stdouts
    def test_worker_term_handler_only_stop_MainProcess(self):
        process = current_process()
        name, process.name = process.name, "OtherProcess"
        try:
            worker = self._Worker()
            handlers = self.psig(cd.install_worker_term_handler, worker)
            self.assertRaises(SystemExit, handlers["SIGTERM"],
                          "SIGTERM", object())
            self.assertFalse(worker.stopped)
        finally:
            process.name = name

    @disable_stdouts
    def test_worker_restart_handler(self):
        argv = []

        def _execv(*args):
            argv.extend(args)

        execv, os.execv = os.execv, _execv
        try:
            worker = self._Worker()
            handlers = self.psig(cd.install_worker_restart_handler, worker)
            handlers["SIGHUP"]("SIGHUP", object())
            self.assertTrue(worker.stopped)
            self.assertTrue(argv)
        finally:
            os.execv = execv
