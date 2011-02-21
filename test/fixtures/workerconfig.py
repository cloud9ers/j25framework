import sys
import os
import tasks
import test.tasks
import model
from test.TestConfiguration import TestConfiguration
sys.path.insert(0, os.getcwd())

BROKER_HOST = "localhost"
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"
CELERYD_CONCURRENCY=1

#CELERY_IMPORTS = ("tasklets.",)

## Using the database to store results
# CELERY_RESULT_BACKEND = "database"
# CELERY_RESULT_DBURI = "sqlite:///celerydb.sqlite"

# Results published as messages (requires AMQP).
CELERY_RESULT_BACKEND = "amqp"

APPSERVER_CONFIG=None
TASKS_PACKAGE=[tasks, test.tasks]

#a hack to pass a temporary file name with a generated TestConfiguration
config = TestConfiguration.create_instance()
MODEL_PACKAGE=model