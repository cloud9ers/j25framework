"""celery.registry"""
import inspect
from UserDict import UserDict

from celery.exceptions import NotRegistered


class TaskRegistry(UserDict):
    """Site registry for tasks."""

    NotRegistered = NotRegistered

    def __init__(self):
        self.data = {}

    def regular(self):
        """Get all regular task types."""
        return self.filter_types("regular")

    def periodic(self):
        """Get all periodic task types."""
        return self.filter_types("periodic")

    def register(self, task):
        """Register a task in the task registry.

        The task will be automatically instantiated if not already an
        instance.

        """
        task = inspect.isclass(task) and task() or task
        name = task.name
        self.data[name] = task

    def unregister(self, name):
        """Unregister task by name.

        :param name: name of the task to unregister, or a
            :class:`celery.task.base.Task` with a valid ``name`` attribute.

        :raises celery.exceptions.NotRegistered: if the task has not
            been registered.

        """
        try:
            # Might be a task class
            name = name.name
        except AttributeError:
            pass

        self.pop(name)

    def filter_types(self, type):
        """Return all tasks of a specific type."""
        return dict((task_name, task)
                        for task_name, task in self.data.items()
                            if task.type == type)

    def __getitem__(self, key):
        try:
            return UserDict.__getitem__(self, key)
        except KeyError, exc:
            raise self.NotRegistered(str(exc))

    def pop(self, key, *args):
        try:
            return UserDict.pop(self, key, *args)
        except KeyError, exc:
            raise self.NotRegistered(str(exc))


"""
.. data:: tasks

    The global task registry.

"""
tasks = TaskRegistry()


def _unpickle_task(name):
    return tasks[name]
