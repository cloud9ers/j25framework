import celery.decorators
from celery.task.base import Task
task = celery.decorators.task
from celery.execute import send_task
Task = Task

CONFIG = None