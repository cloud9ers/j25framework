import atexit
import logging
import multiprocessing
import platform as _platform
import os
import socket
import sys
import warnings

from celery import __version__
from celery import platforms
from celery import signals
from celery.exceptions import ImproperlyConfigured
from celery.routes import Router
from celery.task import discard_all
from celery.utils import get_full_cls_name, LOG_LEVELS
from celery.utils import info
from celery.utils import term
from celery.worker import WorkController


SYSTEM = _platform.system()
IS_OSX = SYSTEM == "Darwin"

STARTUP_INFO_FMT = """
Configuration ->
    . broker -> %(conninfo)s
    . queues ->
%(queues)s
    . concurrency -> %(concurrency)s
    . loader -> %(loader)s
    . logfile -> %(logfile)s@%(loglevel)s
    . events -> %(events)s
    . beat -> %(celerybeat)s
%(tasks)s
""".strip()

TASK_LIST_FMT = """    . tasks ->\n%s"""


class Worker(object):
    WorkController = WorkController

    def __init__(self, concurrency=None, loglevel=None, logfile=None,
            hostname=None, discard=False, run_clockservice=False,
            schedule=None, task_time_limit=None, task_soft_time_limit=None,
            max_tasks_per_child=None, queues=None, events=False, db=None,
            include=None, defaults=None, pidfile=None,
            redirect_stdouts=None, redirect_stdouts_level=None,
            scheduler_cls=None, **kwargs):
        if defaults is None:
            from celery import conf
            defaults = conf
        self.defaults = defaults
        self.concurrency = (concurrency or
                            defaults.CELERYD_CONCURRENCY or
                            multiprocessing.cpu_count())
        self.loglevel = loglevel or defaults.CELERYD_LOG_LEVEL
        self.logfile = logfile or defaults.CELERYD_LOG_FILE
        self.hostname = hostname or socket.gethostname()
        self.discard = discard
        self.run_clockservice = run_clockservice
        self.schedule = schedule or defaults.CELERYBEAT_SCHEDULE_FILENAME
        self.scheduler_cls = scheduler_cls or defaults.CELERYBEAT_SCHEDULER
        self.events = events
        self.task_time_limit = (task_time_limit or
                                defaults.CELERYD_TASK_TIME_LIMIT)
        self.task_soft_time_limit = (task_soft_time_limit or
                                     defaults.CELERYD_TASK_SOFT_TIME_LIMIT)
        self.max_tasks_per_child = (max_tasks_per_child or
                                    defaults.CELERYD_MAX_TASKS_PER_CHILD)
        self.redirect_stdouts = (redirect_stdouts or
                                 defaults.REDIRECT_STDOUTS)
        self.redirect_stdouts_level = (redirect_stdouts_level or
                                       defaults.REDIRECT_STDOUTS_LEVEL)
        self.db = db
        self.queues = queues or []
        self.include = include or []
        self.pidfile = pidfile
        self._isatty = sys.stdout.isatty()
        self.colored = term.colored(enabled=defaults.CELERYD_LOG_COLOR)

        if isinstance(self.queues, basestring):
            self.queues = self.queues.split(",")
        if isinstance(self.include, basestring):
            self.include = self.include.split(",")

        if not isinstance(self.loglevel, int):
            try:
                self.loglevel = LOG_LEVELS[self.loglevel.upper()]
            except KeyError:
                self.die("Unknown level %r. Please use one of %s." % (
                            self.loglevel,
                            "|".join(l for l in LOG_LEVELS.keys()
                                        if isinstance(l, basestring))))

    def run(self):
        self.init_loader()
        self.init_queues()
        self.worker_init()
        self.redirect_stdouts_to_logger()
        print(str(self.colored.cyan(
                "celery@%s v%s is starting." % (self.hostname, __version__))))

        if getattr(os, "geteuid", None) and os.geteuid() == 0:
            warnings.warn(
                "Running celeryd with superuser privileges is not encouraged!")

        if getattr(self.settings, "DEBUG", False):
            warnings.warn("Using settings.DEBUG leads to a memory leak, "
                    "never use this setting in a production environment!")

        if self.discard:
            self.purge_messages()

        # Dump configuration to screen so we have some basic information
        # for when users sends bug reports.
        print(str(self.colored.reset(" \n", self.startup_info())))
        self.set_process_status("Running...")

        self.run_worker()

    def on_listener_ready(self, listener):
        signals.worker_ready.send(sender=listener)
        print("celery@%s has started." % self.hostname)

    def init_queues(self):
        conf = self.defaults
        if self.queues:
            conf.QUEUES = dict((queue, options)
                                for queue, options in conf.QUEUES.items()
                                    if queue in self.queues)
            for queue in self.queues:
                if queue not in conf.QUEUES:
                    if conf.CREATE_MISSING_QUEUES:
                        Router(queues=conf.QUEUES).add_queue(queue)
                    else:
                        raise ImproperlyConfigured(
                            "Queue '%s' not defined in CELERY_QUEUES" % queue)

    def init_loader(self):
        from celery.loaders import current_loader, load_settings
        self.loader = current_loader()
        self.settings = load_settings()
        if not self.loader.configured:
            raise ImproperlyConfigured(
                    "Celery needs to be configured to run celeryd.")
        map(self.loader.import_module, self.include)

    def redirect_stdouts_to_logger(self):
        from celery import log
        handled = log.setup_logging_subsystem(loglevel=self.loglevel,
                                              logfile=self.logfile)
        # Redirect stdout/stderr to our logger.
        if not handled:
            logger = log.get_default_logger()
            if self.redirect_stdouts:
                log.redirect_stdouts_to_logger(logger,
                        loglevel=self.redirect_stdouts_level)

    def purge_messages(self):
        discarded_count = discard_all()
        what = discarded_count > 1 and "messages" or "message"
        print("discard: Erased %d %s from the queue.\n" % (
            discarded_count, what))

    def worker_init(self):
        # Run the worker init handler.
        # (Usually imports task modules and such.)
        self.loader.init_worker()

    def tasklist(self, include_builtins=True):
        from celery.registry import tasks
        tasklist = tasks.keys()
        if not include_builtins:
            tasklist = filter(lambda s: not s.startswith("celery."),
                              tasklist)
        return TASK_LIST_FMT % "\n".join("\t. %s" % task
                                            for task in sorted(tasklist))

    def startup_info(self):
        tasklist = ""
        if self.loglevel <= logging.INFO:
            include_builtins = self.loglevel <= logging.DEBUG
            tasklist = self.tasklist(include_builtins=include_builtins)

        queues = self.defaults.get_queues()

        return STARTUP_INFO_FMT % {
            "conninfo": info.format_broker_info(),
            "queues": info.format_queues(queues, indent=8),
            "concurrency": self.concurrency,
            "loglevel": LOG_LEVELS[self.loglevel],
            "logfile": self.logfile or "[stderr]",
            "celerybeat": self.run_clockservice and "ON" or "OFF",
            "events": self.events and "ON" or "OFF",
            "tasks": tasklist,
            "loader": get_full_cls_name(self.loader.__class__),
        }

    def run_worker(self):
        if self.pidfile:
            pidlock = platforms.create_pidlock(self.pidfile).acquire()
            atexit.register(pidlock.release)
        worker = self.WorkController(concurrency=self.concurrency,
                                loglevel=self.loglevel,
                                logfile=self.logfile,
                                hostname=self.hostname,
                                ready_callback=self.on_listener_ready,
                                embed_clockservice=self.run_clockservice,
                                schedule_filename=self.schedule,
                                scheduler_cls=self.scheduler_cls,
                                send_events=self.events,
                                db=self.db,
                                max_tasks_per_child=self.max_tasks_per_child,
                                task_time_limit=self.task_time_limit,
                                task_soft_time_limit=self.task_soft_time_limit)
        self.install_platform_tweaks(worker)
        worker.start()

    def install_platform_tweaks(self, worker):
        """Install platform specific tweaks and workarounds."""
        if IS_OSX:
            self.osx_proxy_detection_workaround()

        # Install signal handler so SIGHUP restarts the worker.
        if not self._isatty:
            # only install HUP handler if detached from terminal,
            # so closing the terminal window doesn't restart celeryd
            # into the background.
            if IS_OSX:
                # OS X can't exec from a process using threads.
                # See http://github.com/ask/celery/issues#issue/152
                install_HUP_not_supported_handler(worker)
            else:
                install_worker_restart_handler(worker)
        install_worker_term_handler(worker)
        install_worker_int_handler(worker)
        signals.worker_init.send(sender=worker)

    def osx_proxy_detection_workaround(self):
        """See http://github.com/ask/celery/issues#issue/161"""
        os.environ.setdefault("celery_dummy_proxy", "set_by_celeryd")

    def set_process_status(self, info):
        info = "%s (%s)" % (info, platforms.strargv(sys.argv))
        return platforms.set_mp_process_title("celeryd",
                                              info=info,
                                              hostname=self.hostname)

    def die(self, msg, exitcode=1):
        sys.stderr.write("Error: %s\n" % (msg, ))
        sys.exit(exitcode)


def install_worker_int_handler(worker):

    def _stop(signum, frame):
        process_name = multiprocessing.current_process().name
        if process_name == "MainProcess":
            worker.logger.warn(
                "celeryd: Hitting Ctrl+C again will terminate "
                "all running tasks!")
            install_worker_int_again_handler(worker)
            worker.logger.warn("celeryd: Warm shutdown (%s)" % (
                process_name))
            worker.stop()
        raise SystemExit()

    platforms.install_signal_handler("SIGINT", _stop)


def install_worker_int_again_handler(worker):

    def _stop(signum, frame):
        process_name = multiprocessing.current_process().name
        if process_name == "MainProcess":
            worker.logger.warn("celeryd: Cold shutdown (%s)" % (
                process_name))
            worker.terminate()
        raise SystemExit()

    platforms.install_signal_handler("SIGINT", _stop)


def install_worker_term_handler(worker):

    def _stop(signum, frame):
        process_name = multiprocessing.current_process().name
        if process_name == "MainProcess":
            worker.logger.warn("celeryd: Warm shutdown (%s)" % (
                process_name))
            worker.stop()
        raise SystemExit()

    platforms.install_signal_handler("SIGTERM", _stop)


def install_worker_restart_handler(worker):

    def restart_worker_sig_handler(signum, frame):
        """Signal handler restarting the current python program."""
        worker.logger.warn("Restarting celeryd (%s)" % (
            " ".join(sys.argv)))
        worker.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    platforms.install_signal_handler("SIGHUP", restart_worker_sig_handler)


def install_HUP_not_supported_handler(worker):

    def warn_on_HUP_handler(signum, frame):
        worker.logger.error("SIGHUP not supported: "
            "Restarting with HUP is unstable on this platform!")

    platforms.install_signal_handler("SIGHUP", warn_on_HUP_handler)


def run_worker(*args, **kwargs):
    return Worker(*args, **kwargs).run()
