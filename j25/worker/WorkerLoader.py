from celery.loaders.base import BaseLoader
from j25.Configuration import Configuration
import sys
import j25.worker
from j25.worker.TasksLoader import AutoTasksLoader
import os
import logging
_RACE_PROTECTION = False

class WorkerLoader(BaseLoader):
    def on_worker_init(self):
        autoLoadTasks(self._tasksPackage)
    
    def read_configuration(self):
        os.putenv('WORKER_CONFIG', 'workerconfig')
        configName = os.environ.setdefault("WORKER_CONFIG", "workerconfig")
        try:
            logging.info("loading configuration from %s", configName)
            configModule = __import__(configName, fromlist="t")
        except ImportError:
            logging.info("Couldn't access configuration %s", configName)
            sys.exit(1)    
        
        if hasattr(configModule, 'APPSERVER_CONFIG') and configModule.APPSERVER_CONFIG is not None:
            logging.info("loaded %s", configModule.APPSERVER_CONFIG)
            config = Configuration.load_file(configModule.APPSERVER_CONFIG)
        else:
            logging.info("loaded application server defaults")
            config = Configuration.load_defaults()
        j25.worker.CONFIG = config
        self.configured = True
        self._tasksPackage = configModule.TASKS_PACKAGE
        return configModule

def autoLoadTasks(basePackage):
    global _RACE_PROTECTION
    
    if _RACE_PROTECTION:
        return
    
    _RACE_PROTECTION = True
    logging.info("Loading tasks from package %s" % basePackage)
    AutoTasksLoader(basePackage)
    _RACE_PROTECTION = False