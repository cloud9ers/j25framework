import os
import sys

from importlib import import_module

from celery.utils.mail import mail_admins

BUILTIN_MODULES = ["celery.task"]


class BaseLoader(object):
    """The base class for loaders.

    Loaders handles to following things:

        * Reading celery client/worker configurations.

        * What happens when a task starts?
            See :meth:`on_task_init`.

        * What happens when the worker starts?
            See :meth:`on_worker_init`.

        * What modules are imported to find tasks?

    """
    _conf_cache = None
    worker_initialized = False
    override_backends = {}
    configured = False

    def on_task_init(self, task_id, task):
        """This method is called before a task is executed."""
        pass

    def on_process_cleanup(self):
        """This method is called after a task is executed."""
        pass

    def on_worker_init(self):
        """This method is called when the worker (``celeryd``) starts."""
        pass

    def import_task_module(self, module):
        return self.import_from_cwd(module)

    def import_module(self, module):
        return import_module(module)

    def import_default_modules(self):
        imports = getattr(self.conf, "CELERY_IMPORTS", None) or []
        imports = set(list(imports) + BUILTIN_MODULES)
        return map(self.import_task_module, imports)

    def init_worker(self):
        if not self.worker_initialized:
            self.worker_initialized = True
            self.on_worker_init()

    def import_from_cwd(self, module, imp=None):
        """Import module, but make sure it finds modules
        located in the current directory.

        Modules located in the current directory has
        precedence over modules located in ``sys.path``.
        """
        if imp is None:
            imp = self.import_module
        cwd = os.getcwd()
        if cwd in sys.path:
            return imp(module)
        sys.path.insert(0, cwd)
        try:
            return imp(module)
        finally:
            try:
                sys.path.remove(cwd)
            except ValueError:          # pragma: no cover
                pass

    def mail_admins(self, subject, body, fail_silently=False):
        return mail_admins(subject, body, fail_silently=fail_silently)

    @property
    def conf(self):
        """Loader configuration."""
        if not self._conf_cache:
            self._conf_cache = self.read_configuration()
        return self._conf_cache
