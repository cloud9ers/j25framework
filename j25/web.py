#Contract 
from j25.exceptions import HttpExceptions
from j25.exceptions.HttpExceptions import HTTPResponse, Http404, Http403
from j25.http import HttpResponse
from j25.http.contenttype import contenttype
from j25.http.formatters import MAPPING
from mako import exceptions
from mako.lookup import TemplateLookup
import errno
import inspect
import logging
import os
import stat
import time

DEFAULT_CHUNK_SIZE = 64 * 1024

def _streamer(stream, chunk_size=DEFAULT_CHUNK_SIZE, bytes=None):
    '''internal streamer for files'''
    offset = 0
    while bytes == None or offset < bytes:
        if bytes != None and bytes - offset < chunk_size:
            chunk_size = bytes - offset
        data = stream.read(chunk_size)
        length = len(data)
        if not length:
            break
        else:
            yield data
        if length < chunk_size:
            break
        offset += length
    stream.close()
     
    
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
    
def render_template(params, headers, app_package, controller_instance, request):
    headers['Content-Type'] = 'text/html; charset=UTF-8'
    template_dirs = [os.path.join(os.getcwd(), 'templates')]
    template_dirs.append(os.path.join(app_package.__path__[0], 'templates'))
    tmpDir = os.path.join(app_package.__path__[0], 'tmp')
    templateFile = os.path.join(controller_instance.__class__.__name__, "%s.html" % request.urlvars.get('action'))
    myLookup = TemplateLookup(directories=template_dirs, module_directory=tmpDir, input_encoding='utf-8')
    #@todo : neater handling and error reporting
    try:
        myTemplate = myLookup.get_template(templateFile)
        result = myTemplate.render_unicode(**params)
    except:
        controller_instance.set_response_code(HttpExceptions.INTERNAL_SERVER_ERROR)
        result = exceptions.html_error_template().render()
    return result
    
class ActionWrapper(object):
    '''In order to have an action exposed, the action method must be wrapped by one of the ActionWrappers'''
    logger = logging.getLogger("ActionWrapper")
    def __init__(self, func):
        self.func = func
        #this indicates if the action is wrapped by a custom wrapper or not.
        self.wrapped = True
        
    def __call__(self, *args, **kwargs):
        raise NotImplemented

class HttpResponder(ActionWrapper):
    def __call__(self, environ, start_response, request, session, app_package, controller_instance):
        ''' app_package can be used to locate templates potentially'''
        #argument extraction
        args, kwargs = extract_args(environ, start_response, request, session)
        try:
            result = apply_action(self.func, controller_instance, args, kwargs)
        except HTTPResponse, e:
            #need to return an error
            start_response(e.status, [('Content-Type', 'text/plain; charset=UTF-8')])
            return str(e)
        
        format = request.urlvars.get('format')
        headers = controller_instance.get_headers()
        
        if result is None:
            headers['Content-Length'] = 0
            controller_instance.set_response_code(HttpExceptions.NO_CONTENT)
            start_response(controller_instance.get_response_code(), headers.items())
            return []
        
        if inspect.isclass(result) and issubclass(result, HttpResponse):
            headers['Content-Length'] = 0
            controller_instance.set_response_code(result.get_http_response())
            start_response(controller_instance.get_response_code(), headers.items())
            return []
        
        if format:
            #formatter specified
            if format not in MAPPING:
                start_response(HttpExceptions.NOTFOUND, [('Content-Type', 'text/plain; charset=UTF-8')])
                return [HttpExceptions.NOTFOUND + ": No formatter defined for %s" % (environ['PATH_INFO'])]

            result = MAPPING[format](result, request, session, app_package, controller_instance)
        else:
            #text/plain or text/html
            if isinstance(result, dict):
                #go and render the template
                result = render_template(result, headers, app_package, controller_instance, request)
            elif hasattr(result, '__iter__'):
                #streaming
                #TODO: do we need to set the Content-Length here?
                start_response(controller_instance.get_response_code(), headers.items())
                return result
            else:
                headers['Content-Type'] = 'text/plain; charset=UTF-8'
                
        headers['Content-Length'] = len(unicode(result))
        start_response(controller_instance.get_response_code(), headers.items())
        return str(result)
    
class Controller(object):
    def __init__(self, session, url, app_config, request=None):
        self._headers = {}
        self._http_response_code = HttpExceptions.OK
        self._template = None
        self._template_engine = None
        self.session = session
        self.request = request
        self.config = app_config
        self.url = url
    
    #named with underscore to remove potential name collision with controller actions
    def call_controller_action(self, environ, start_response, route, appPackage):
        #find the action
        #action filter
        if route['action'].startswith('_'):
            start_response(HttpExceptions.NOTFOUND, [('Content-Type', 'text/plain; charset=UTF-8')])
            return [HttpExceptions.NOTFOUND + ": No action defined to '%s'" % environ['PATH_INFO']]

        action = getattr(self, route['action'], None)
        if not action or (not hasattr(action, '__call__')):
            start_response(HttpExceptions.NOTFOUND, [('Content-Type', 'text/plain; charset=UTF-8')])
            return [HttpExceptions.NOTFOUND + ": No action '%s' was found defined to %s" % (route['action'], environ['PATH_INFO'])]
           
        if not getattr(action, 'wrapped', None):
            #wrap with HttpResponder if not wrapped already
            action = HttpResponder(action)
        else:
            #if wrapped, make sure it's callable
            if getattr(action, 'not_exposed', False):
                #barf
                start_response(HttpExceptions.NOTFOUND, [('Content-Type', 'text/plain; charset=UTF-8')])
                logging.warn("Access trial to non-exposed action %s", route['action'])
                return [HttpExceptions.NOTFOUND + ": No action '%s' was found defined to %s" % (route['action'], environ['PATH_INFO'])]
            
        return action(environ, start_response, self.request, self.session, appPackage, self)
    
    def stream_file(self, filename):
        try:
            fp = open(filename, 'rb')
        except IOError, e:
            fp.close()
            if e[0] == errno.EISDIR:
                raise Http403("file is a directory")
            elif e[0] == errno.EACCES:
                raise Http403("inaccessible file")
            else:
                raise Http404("invalid file")
            
        stat_file = os.stat(filename)
        fsize = stat_file[stat.ST_SIZE]
        mtime = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stat_file[stat.ST_MTIME]))
        self.set_contenttype(contenttype(filename))
        self.add_header('Last-Modified', mtime)
        self.add_header('Content-Transfer-Encoding', 'binary')
        
        self.add_header('Pragma', 'cache')
        self.add_header('Cache-Control', 'private')
        self.add_header('Content-Length', fsize)
        return _streamer(fp)
    
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
        
    def set_contenttype(self, value):
        self._headers['Content-Type'] = value
            
    def add_header(self, key, value):
        self._headers[key] = value
        
    def remove_header(self, key):
        return self._headers.pop(key)
    
    def get_headers(self):
        return self._headers
