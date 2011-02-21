import pkgutil

class AutoTasksLoader(object):
    def __init__(self, basePackage):
        total = self.load_package(basePackage)
        self.loadedCount = total
        
    def load_package(self, packageOrPackages):
        if not isinstance(packageOrPackages, list):
            packageOrPackages = [packageOrPackages]
        total = 0
        for packageObject in packageOrPackages:
            for _, modname, ispkg in pkgutil.iter_modules(packageObject.__path__):
                moduleObject = __import__(packageObject.__name__ + "." + modname, fromlist="t")
                if ispkg:
                    # is package
                    packageObject = moduleObject
                    total += self.load_package(packageObject)
            
        return total
