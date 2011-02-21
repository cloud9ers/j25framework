import pkgutil
import logging

logger = logging.getLogger("TaskLoader")

class AutoTaskLoader(object):
    @classmethod
    def load(cls, package_or_packages):
        if not isinstance(package_or_packages, list):
            package_or_packages = [package_or_packages]
        logger.debug("Scanning package(s) %s for task objects.", str(package_or_packages))
        for package_object in package_or_packages:
            for _, modname, _ in pkgutil.iter_modules(package_object.__path__):
                __import__(package_object.__name__ + "." + modname, fromlist="t")
                logger.debug("loaded task module: %s", modname)