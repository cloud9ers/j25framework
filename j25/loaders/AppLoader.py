from j25.loaders.ControllerLoader import AutoControllerLoader
from j25.loaders.TaskLoader import AutoTaskLoader
import importlib
import logging
import traceback

logger = logging.getLogger("AppLoader")

class AutoAppLoader(object):
    def __init__(self, applications):
        self.apps = []
        self.applications = applications
        
    def load_applications(self, dispatcher):
        logger.debug("Loading installed applications")
        for package in self.applications:
            #load application
            if self.load_application(package, dispatcher):
                self.apps.append(str(package))
        logger.info("%s application(s) loaded", len(self.apps))
        
    def unload_application(self, app, dispatcher):
        dispatcher.unregister_app(app)
       
    def reload(self, app, dispatcher):
        logger.info("Reloading application %s", app)
        self.unload_application(app, dispatcher)
        return self.load_application(app, dispatcher, reload_app=True)
    
    def load_application(self, package, dispatcher, reload_app=False):
        #loading application means loading all the models, controllers, tasks
        logger.debug("Loading app %s", package)
        try:
            if reload_app:
                reload(__import__('%s.config' % package, fromlist="t"))
            logger.debug("%s model objects loaded from app %s", AutoControllerLoader.load(package,
                                                                                            importlib.import_module(".routing", package=package), 
                                                                                            dispatcher, importlib.import_module(".controllers", package=package),
                                                                                            reload_controllers=reload_app),
                                                                                            package)
            AutoTaskLoader.load(importlib.import_module(".tasks", package=package))
        except:
            logger.error("Failed to load app %s: %s", str(package), traceback.format_exc())
            return False
        else:
            logger.info("Application: '%s' has been loaded", package)
            return True