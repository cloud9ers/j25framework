"""

The Multiprocessing Worker Server

"""
import socket
import logging
import traceback
from multiprocessing.util import Finalize

from celery import beat
from celery import conf
from celery import log
from celery import registry
from celery import platforms
from celery import signals
from celery.utils import noop, instantiate

from celery.worker import state
from celery.worker.buckets import TaskBucket, FastQueue

RUN = 0x1
CLOSE = 0x2
TERMINATE = 0x3

WORKER_SIGRESET = frozenset(["SIGTERM",
                             "SIGHUP",
                             "SIGTTIN",
                             "SIGTTOU"])
WORKER_SIGIGNORE = frozenset(["SIGINT"])


def process_initializer(hostname):
    """Initializes the process so it can be used to process tasks.

    Used for multiprocessing environments.

    """
    map(platforms.reset_signal, WORKER_SIGRESET)
    map(platforms.ignore_signal, WORKER_SIGIGNORE)
    platforms.set_mp_process_title("celeryd", hostname=hostname)

    # This is for windows and other platforms not supporting
    # fork(). Note that init_worker makes sure it's only
    # run once per process.
    from celery.loaders import current_loader
    current_loader().init_worker()

    signals.worker_process_init.send(sender=None)


class WorkController(object):
    """Executes tasks waiting in the task queue.

    :param concurrency: see :attr:`concurrency`.
    :param logfile: see :attr:`logfile`.
    :param loglevel: see :attr:`loglevel`.
    :param embed_clockservice: see :attr:`embed_clockservice`.
    :param send_events: see :attr:`send_events`.

    .. attribute:: concurrency

        The number of simultaneous processes doing work (default:
        ``conf.CELERYD_CONCURRENCY``)

    .. attribute:: loglevel

        The loglevel used (default: :const:`logging.INFO`)

    .. attribute:: logfile

        The logfile used, if no logfile is specified it uses ``stderr``
        (default: `celery.conf.CELERYD_LOG_FILE`).

    .. attribute:: embed_clockservice

        If :const:`True`, celerybeat is embedded, running in the main worker
        process as a thread.

    .. attribute:: send_events

        Enable the sending of monitoring events, these events can be captured
        by monitors (celerymon).

    .. attribute:: logger

        The :class:`logging.Logger` instance used for logging.

    .. attribute:: pool

        The :class:`multiprocessing.Pool` instance used.

    .. attribute:: ready_queue

        The :class:`Queue.Queue` that holds tasks ready for immediate
        processing.

    .. attribute:: schedule_controller

        Instance of :class:`celery.worker.controllers.ScheduleController`.

    .. attribute:: mediator

        Instance of :class:`celery.worker.controllers.Mediator`.

    .. attribute:: listener

        Instance of :class:`CarrotListener`.

    """
    loglevel = logging.ERROR
    concurrency = conf.CELERYD_CONCURRENCY
    logfile = conf.CELERYD_LOG_FILE
    _state = None
    _running = 0

    def __init__(self, concurrency=None, logfile=None, loglevel=None,
            send_events=conf.SEND_EVENTS, hostname=None,
            ready_callback=noop, embed_clockservice=False,
            pool_cls=conf.CELERYD_POOL, listener_cls=conf.CELERYD_LISTENER,
            mediator_cls=conf.CELERYD_MEDIATOR,
            eta_scheduler_cls=conf.CELERYD_ETA_SCHEDULER,
            schedule_filename=conf.CELERYBEAT_SCHEDULE_FILENAME,
            task_time_limit=conf.CELERYD_TASK_TIME_LIMIT,
            task_soft_time_limit=conf.CELERYD_TASK_SOFT_TIME_LIMIT,
            max_tasks_per_child=conf.CELERYD_MAX_TASKS_PER_CHILD,
            pool_putlocks=conf.CELERYD_POOL_PUTLOCKS,
            disable_rate_limits=conf.DISABLE_RATE_LIMITS,
            db=conf.CELERYD_STATE_DB,
            scheduler_cls=conf.CELERYBEAT_SCHEDULER):

        # Options
        self.loglevel = loglevel or self.loglevel
        self.concurrency = concurrency or self.concurrency
        self.logfile = logfile or self.logfile
        self.logger = log.get_default_logger()
        self.hostname = hostname or socket.gethostname()
        self.embed_clockservice = embed_clockservice
        self.ready_callback = ready_callback
        self.send_events = send_events
        self.task_time_limit = task_time_limit
        self.task_soft_time_limit = task_soft_time_limit
        self.max_tasks_per_child = max_tasks_per_child
        self.pool_putlocks = pool_putlocks
        self.timer_debug = log.SilenceRepeated(self.logger.debug,
                                               max_iterations=10)
        self.db = db
        self._finalize = Finalize(self, self.stop, exitpriority=1)

        if self.db:
            persistence = state.Persistent(self.db)
            Finalize(persistence, persistence.save, exitpriority=5)

        # Queues
        if disable_rate_limits:
            self.ready_queue = FastQueue()
            self.ready_queue.put = self.process_task
        else:
            self.ready_queue = TaskBucket(task_registry=registry.tasks)

        self.logger.debug("Instantiating thread components...")

        # Threads + Pool + Consumer
        self.pool = instantiate(pool_cls, self.concurrency,
                                logger=self.logger,
                                initializer=process_initializer,
                                initargs=(self.hostname, ),
                                maxtasksperchild=self.max_tasks_per_child,
                                timeout=self.task_time_limit,
                                soft_timeout=self.task_soft_time_limit,
                                putlocks=self.pool_putlocks)

        self.mediator = None
        if not disable_rate_limits:
            self.mediator = instantiate(mediator_cls, self.ready_queue,
                                        callback=self.process_task,
                                        logger=self.logger)
        self.scheduler = instantiate(eta_scheduler_cls,
                               precision=conf.CELERYD_ETA_SCHEDULER_PRECISION,
                               on_error=self.on_timer_error,
                               on_tick=self.on_timer_tick)

        self.beat = None
        if self.embed_clockservice:
            self.beat = beat.EmbeddedService(logger=self.logger,
                                    schedule_filename=schedule_filename,
                                    scheduler_cls=scheduler_cls)

        prefetch_count = self.concurrency * conf.CELERYD_PREFETCH_MULTIPLIER
        self.listener = instantiate(listener_cls,
                                    self.ready_queue,
                                    self.scheduler,
                                    logger=self.logger,
                                    hostname=self.hostname,
                                    send_events=self.send_events,
                                    init_callback=self.ready_callback,
                                    initial_prefetch_count=prefetch_count,
                                    pool=self.pool)

        # The order is important here;
        #   the first in the list is the first to start,
        # and they must be stopped in reverse order.
        self.components = filter(None, (self.pool,
                                        self.mediator,
                                        self.scheduler,
                                        self.beat,
                                        self.listener))

    def start(self):
        """Starts the workers main loop."""
        self._state = RUN

        for i, component in enumerate(self.components):
            self.logger.debug("Starting thread %s..." % (
                                    component.__class__.__name__))
            self._running = i + 1
            component.start()

    def process_task(self, wrapper):
        """Process task by sending it to the pool of workers."""
        try:
            try:
                wrapper.task.execute(wrapper, self.pool,
                    self.loglevel, self.logfile)
            except Exception, exc:
                self.logger.critical("Internal error %s: %s\n%s" % (
                                exc.__class__, exc, traceback.format_exc()))
        except (SystemExit, KeyboardInterrupt):
            self.stop()

    def stop(self):
        """Graceful shutdown of the worker server."""
        self._shutdown(warm=True)

    def terminate(self):
        """Not so graceful shutdown of the worker server."""
        self._shutdown(warm=False)

    def _shutdown(self, warm=True):
        """Gracefully shutdown the worker server."""
        what = (warm and "stopping" or "terminating").capitalize()

        if self._state != RUN or self._running != len(self.components):
            # Not fully started, can safely exit.
            return

        self._state = CLOSE
        signals.worker_shutdown.send(sender=self)

        for component in reversed(self.components):
            self.logger.debug("%s thread %s..." % (
                    what, component.__class__.__name__))
            stop = component.stop
            if not warm:
                stop = getattr(component, "terminate", stop)
            stop()

        self.listener.close_connection()
        self._state = TERMINATE

    def on_timer_error(self, exc_info):
        _, exc, _ = exc_info
        self.logger.error("Timer error: %r" % (exc, ))

    def on_timer_tick(self, delay):
        self.timer_debug("Scheduler wake-up! Next eta %s secs." % delay)
