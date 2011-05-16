from celery.loaders.base import BaseLoader
from j25.Configuration import Configuration
from j25.loaders.TaskLoader import AutoTaskLoader
import sys
import j25
import os
import logging
from celery.datastructures import DictAttribute
_RACE_PROTECTION = False

class WorkerLoader(BaseLoader):
    def on_worker_init(self):
        autoLoadTasks()
    
    def read_configuration(self):
        configName = os.environ.setdefault("WORKER_CONFIG", "workerconfig")
        try:
            logging.info("loading configuration from %s", configName)
            configModule = __import__(configName, fromlist="t")
        except ImportError:
            logging.info("Couldn't access configuration %s", configName)
            sys.exit(1)    
        
        config = Configuration.load_file("server.ini")
        j25.config = config
        self.configured = True
        return DictAttribute(configModule)

def autoLoadTasks():
    global _RACE_PROTECTION
    
    if _RACE_PROTECTION:
        return
    
    _RACE_PROTECTION = True
    apps = eval(j25.config.main.applications)
    logging.debug("Loading tasks from apps %s" % apps)
    count = AutoTaskLoader.load_apps(apps)
    if count:
        logging.info("Loaded tasks from %s app(s)" % count)
    else:
        logging.critical("No Applications were found in this project")
        exit(33)
    _RACE_PROTECTION = False