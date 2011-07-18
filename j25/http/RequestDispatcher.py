import logging
import traceback
from j25.exceptions import HttpExceptions as HTTP
from webob.request import Request
import j25

logger = logging.getLogger("RequestDispatcher")
error_format = "%s\n\n--------------%s"

class RequestDispatcher(object):
    def __init__(self, app_loader):
        self._apps = {} #key: appName, value: (appPackage, controllers)
        self._app_loader = app_loader
        
    def load_applications(self):
        self._app_loader.load_applications(self)
    
    def create_application(self, environ, start_response):
        try:
            logger.debug("WSGI Call")
            url, route = environ['wsgiorg.routing_args']
            if not route:
                start_response(HTTP.NOTFOUND, [('Content-Type', 'text/plain')])
                return [HTTP.NOTFOUND + ''': No route defined to %s
                
Route:%s
                

Tried to match:

%s
''' % (environ['PATH_INFO'], route, str(j25._mapper))]
            
            if 'app' not in route:
                logger.error("'app' is not defined for %s (route:%)", environ['PATH_INFO'], route)
                start_response(HTTP.INTERNAL_SERVER_ERROR, [('Content-Type', 'text/plain')])
                error_message = HTTP.INTERNAL_SERVER_ERROR
                if j25.is_dev():
                    error_message = error_format % (HTTP.INTERNAL_SERVER_ERROR, "'app' is not defined for %s (route:%s)" % (environ['PATH_INFO'], route))
                return [error_message]
            
            if 'action' not in route:
                logger.error("'action' is not defined for %s (route:%)", environ['PATH_INFO'], route)
                start_response(HTTP.INTERNAL_SERVER_ERROR, [('Content-Type', 'text/plain')])
                error_message = HTTP.INTERNAL_SERVER_ERROR
                if j25.is_dev():
                    error_message = error_format % (HTTP.INTERNAL_SERVER_ERROR, "'action' is not defined for %s (route:%s)" % (environ['PATH_INFO'], route))

                return [error_message]
    
                    
            app_name = route['app']
            self.reload_app(app_name)
            app_config = __import__("%s.config" % app_name, fromlist="t")
            app = self._apps[app_name]
            controller_name = route['controller']
            controllers = app[1]
            if controller_name not in controllers:
                start_response(HTTP.NOTFOUND, [('Content-Type', 'text/plain')])
                return [HTTP.NOTFOUND + ": No controller defined under name %s in application %s" % (controller_name, app_name)]
            
            return self.dispatch(app_name, controller_name, app, route, url, environ, start_response, app_config)
        except:
            tb = traceback.format_exc()
            logger.critical("Cannot handle request to %s: %s", environ['PATH_INFO'], tb)
            start_response(HTTP.INTERNAL_SERVER_ERROR, [('Content-Type', 'text/plain')])
            error_message = HTTP.INTERNAL_SERVER_ERROR
            if j25.is_dev():
                error_message = error_format % (HTTP.INTERNAL_SERVER_ERROR, tb)

            return [error_message]
            
              
    def dispatch(self, app_name, controller_name, app, route, url, environ, start_response, app_config):
        # create the service instance and inject the context
        session = environ[j25.Constants.SESSION_KEY]
        request = Request(environ)
        app_controllers = app[1]
        controller = app_controllers[controller_name](session=session, request=request, url=url, app_config=app_config)
        try:
            return controller.call_controller_action(environ, start_response, route, app[0]) #app[0] appPackage
        except:
            tb = traceback.format_exc()
            logger.critical("Cannot handle request on (%s): %s" % (environ['PATH_INFO'], tb))
            start_response(HTTP.INTERNAL_SERVER_ERROR, [('Content-Type', 'text/plain')])
            error_message = HTTP.INTERNAL_SERVER_ERROR
            if j25.is_dev():
                error_message = error_format % (HTTP.INTERNAL_SERVER_ERROR, tb)
            return [error_message]
    
    def unregister_app(self, app_package):
        #@todo: misses resetting the mapper for now
        self._apps.pop(app_package)
    
    def register_all_apps_router(self):
        import importlib
        for app in j25._apps:
            router = importlib.import_module(".routing", package=app)
            self.register_app_router(router, app)
            
    def register_app_router(self, router, app_package):
        router.router(j25._mapper.submapper(app=app_package))

    def register_app(self, app_package, controllers, router):
        '''
        @param controllers: {'controller_name': ControllerClass} 
        '''
        app_name = app_package.__name__
        self.register_app_router(router, app_name)
        if app_name in self._apps:
            logger.error("Application %s is already registered in the application server", app_name)
            return False
        for controller in controllers.values():
            if not self._run_on_server_start(app_name, controller):
                return False
        # application is registered here
        self._apps[app_name] = (app_package, controllers)
        return True
    
    def _run_on_server_start(self, app_name, controller):
        for attribute in filter(lambda x: hasattr(x, '__call__'), map(lambda x: not x.startswith('__') and getattr(controller, x), dir(controller))):
            if getattr(attribute, "onStart", False):
                if isinstance(controller, attribute.im_self):
                    logger.critical("Cannot launch method (%s) in controller (%s) in application (%s) on boot because it's not a @staticmethod or @classmethod", attribute.__name__, controller.__name__, app_name)
                    logger.critical("Application '%s' cannot be registered due to previous errors", app_name)
                    return True
                try:
                    attribute()
                except:
                    logger.critical("Application '%s' can't be registered: ", app_name, traceback.format_exc())
                    return False
                else:
                    return True
        else:
            return True
        
    def reload_app(self, app_name):
        if j25.is_dev():
            self._app_loader.reload(app_name, self)
                
    def _any_controller(self):
        return
    
    def get_controller_names(self):
#        if j25.is_dev():
##            reload apps
#            self.load_applications()
            
        controllers = [app[1] for app in self._apps.values()]
        return [item for sublist in controllers for item in sublist]
    
    def get_number_of_apps(self):
        return len(self._apps)
    
    def is_path_routable(self, path):
        return self._mapper.match(path) != {}