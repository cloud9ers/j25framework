#Contract 
from j25.exceptions.HttpExceptions import HTTPResponse
from j25.http.formatters import MAPPING
from j25.utils import HTTP
from mako import exceptions
from mako.lookup import TemplateLookup
import logging
import os

class ActionWrapper(object):
    logger = logging.getLogger("ActionWrapper")
    def __init__(self, func):
        self.func = func
        self.wrapped = True
        
    def __call__(self, *args, **kwargs):
        raise NotImplemented
    
def extract_args(environ, start_response, request, session):
    return ([], request.urlvars)

def apply_action(func, controller_instance, args, kwargs):
    newKwargs = {}
    import inspect
    argSpecs = inspect.getargspec(func).args
    for arg in argSpecs:
        if arg in kwargs:
            newKwargs[arg] = kwargs[arg]
    if inspect.ismethod(func):
        return func(*args, **newKwargs)
    else:
        return func(controller_instance, *args, **newKwargs)

class http_responder(ActionWrapper):
    def __call__(self, environ, start_response, request, session, app_package, controller_instance):
        ''' app_package can be used to locate templates potentially'''
        #argument extraction
        args, kwargs = extract_args(environ, start_response, request, session)
        try:
            result = apply_action(self.func, controller_instance, args, kwargs)
        except HTTPResponse, e:
            #need to return an error
            start_response(e.status, [('Content-Type', 'text/plain')])
            return str(e)
        
        format = request.urlvars.get('format')
        headers = controller_instance.get_headers()
        headers['Content-Type'] = 'text/plain'
        
        if result is None:
            controller_instance.set_response_code(HTTP.NO_CONTENT)
            start_response(controller_instance.get_response_code(), headers.items())
            return ''
        
        if format:
            #formatter specified
            if format not in MAPPING:
                start_response(HTTP.NOTFOUND, [('Content-Type', 'text/plain')])
                return [HTTP.NOTFOUND + ": No formatter defined for %s" % (environ['PATH_INFO'])]

            result = MAPPING[format](result, request, session, app_package, controller_instance)
        else:
            #text/plain or text/html
            if isinstance(result, dict):
                headers['Content-Type'] = 'text/html'
                template_dirs = [os.path.join(os.getcwd(), 'templates')]
                template_dirs.append(os.path.join(app_package.__path__[0], 'templates'))
                tmpDir = os.path.join(app_package.__path__[0], 'tmp')
                templateFile = os.path.join(controller_instance.__class__.__name__, "%s.html" % request.urlvars.get('action'))
                myLookup = TemplateLookup(directories=template_dirs, module_directory=tmpDir, input_encoding='utf-8')
                #@todo : neater handling and error reporting
                try:
                    myTemplate = myLookup.get_template(templateFile)
                    result = myTemplate.render_unicode(**result)
                except:
                    controller_instance.set_response_code(HTTP.INTERNAL_SERVER_ERROR)
                    result = exceptions.html_error_template().render()
        headers['Content-Length'] = len(str(result))
        start_response(controller_instance.get_response_code(), headers.items())
        return str(result)
    
class Controller(object):
    def __init__(self, session, url, app_config, request=None):
        self._headers = {}
        self.session = session
        self.request = request
        self.config = app_config
        self.url = url
        self._http_response_code = HTTP.OK
        self._template = None
        self._template_engine = None
    
    #named with underscore to remove potential name collision with controller actions
    def call_controller_action(self, environ, start_response, route, appPackage):
        #find the action
        #action filter
        if route['action'].startswith('_'):
            start_response(HTTP.NOTFOUND, [('Content-Type', 'text/plain')])
            return [HTTP.NOTFOUND + ": No action defined to '%s'" % environ['PATH_INFO']]

        action = getattr(self, route['action'], None)
        if not action or (not hasattr(action, '__call__')):
            start_response(HTTP.NOTFOUND, [('Content-Type', 'text/plain')])
            return [HTTP.NOTFOUND + ": No action '%s' was found defined to %s" % (route['action'], environ['PATH_INFO'])]
           
        if not getattr(action, 'wrapped', None):
            #wrap with http_responder if not wrapped already
            action = http_responder(action)
        else:
            #if wrapped, make sure it's callable
            if getattr(action, 'not_exposed', False):
                #barf
                start_response(HTTP.NOTFOUND, [('Content-Type', 'text/plain')])
                logging.warn("Access trial to non-exposed action %s", route['action'])
                return [HTTP.NOTFOUND + ": No action '%s' was found defined to %s" % (route['action'], environ['PATH_INFO'])]
            
        return action(environ, start_response, self.request, self.session, appPackage, self)
    
    def set_template_engine(self, engine):
        self._template_engine = engine
    
    def get_template_engine(self):
        return self._template_engine

    def set_template(self, template):
        self._template = template
    
    def get_template(self):
        return self._template
    
    def get_response_code(self):
        return self._http_response_code
    
    def set_response_code(self, code):
        self._http_response_code = code
        
    def add_header(self, key, value):
        self._headers[key] = value
        
    def remove_header(self, key):
        return self._headers.pop(key)
    
    def get_headers(self):
        return self._headers