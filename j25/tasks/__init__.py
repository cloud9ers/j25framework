import celery.decorators
from celery.task.base import Task
task = celery.decorators.task
Task = Task

CONFIG = None