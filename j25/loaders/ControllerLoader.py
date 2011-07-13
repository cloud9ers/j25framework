from j25.web import Controller
import inspect
import logging
import pkgutil
import traceback

logger = logging.getLogger("ControllerLoader")

class AutoControllerLoader(object):
    @classmethod
    def load(cls, app_name, router, dispatcher, package_or_packages):
        if not isinstance(package_or_packages, list):
            package_or_packages = [package_or_packages]
        total = 0
        logger.debug("Scanning package(s) %s for controllers.", str(package_or_packages))
        controllers = {}
        for base_package in package_or_packages:
            for _, modname, ispkg in pkgutil.iter_modules(base_package.__path__):
                if ispkg == False:
                    module = __import__(base_package.__name__ + "." + modname, fromlist="t")
                    for class_name in dir(module):
                        klass = getattr(module, class_name)
                        if inspect.isclass(klass):
                            if klass is Controller:
                                continue
                            if not issubclass(klass, Controller):
                                logger.debug("Class %s was found in '%s' package but is not a subclass of j25.web.Controller -- ignoring...", klass.__name__, base_package.__path__)
                                continue
                            # load it
                            try:
#                                dispatcher.registerServiceFactory(klass.PATH, klass.BASE_SERVICE.createFactory(klass.NAME, config, klass))
                                controllers[klass.__name__] = klass
                                logger.debug("Controller %s is loaded.", klass.__name__)
                                total += 1
                            except:
                                logger.error("Failed to load controller %s:%s", klass.__name__, traceback.format_exc())
        if controllers:
#            app_package = importlib.import_module(app_name)
            app_package = __import__(app_name, fromlist="t")
            if not dispatcher.register_app(app_package, controllers, router):
                logger.error("Couldn't register application %s", app_name)
                return 0
        if total > 0:
            logger.info("%s controller(s) are/is loaded successfully from app (%s)", total, app_name)
        return total