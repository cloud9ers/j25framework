from j25.web import ActionWrapper

class exposed(ActionWrapper):
    def __init__(self, func):
        ActionWrapper.__init__(self, func)
        #not directly callable through HTTP
        self.not_exposed = True

class endpoint(ActionWrapper):
    pass


#class XMLRPCService(BaseService):
#    FACTORY = XMLRPCServiceFactory
#    
#    def __init__(self, instance=None):
#        self.dispatcher = SimpleXMLRPCDispatcher(allow_none=True, encoding="UTF-8")
#        for member in filter(lambda x: hasattr(x, '__call__'), map(lambda x: not x.startswith('__') and getattr(instance, x), dir(instance))):
#            if getattr(member, "exposed", False):
#                self.dispatcher.register_function(member)
#        self.dispatcher.register_introspection_functions()
#    
#    def handle(self, environ, responder):
#        """XMLRPC service"""
#
#        if environ['REQUEST_METHOD'] == 'POST':
#            return self.handle_POST(environ, responder)
#        else:
#            responder(HTTP.BAD_REQUEST, [('Content-Type','text/plain'),
#                                         ('Cache-Control', 'no-cache')])
#            return ['']
#        
#    def handle_POST(self, environ, responder):
#        """Handles the HTTP POST request.
#
#        Attempts to interpret all HTTP POST requests as XML-RPC calls,
#        which are forwarded to the server's _dispatch method for handling.
#        
#        Most code taken from SimpleXMLRPCServer with modifications for wsgi and my custom dispatcher.
#        """
#        
#        try:
#            # Get arguments by reading body of request.
#            # We read this in chunks to avoid straining
#            # socket.read(); around the 10 or 15Mb mark, some platforms
#            # begin to have problems (bug #792570).
#
#            length = int(environ['CONTENT_LENGTH'])
#            data = environ['wsgi.input'].read(length)
#            
#            response = self.dispatcher._marshaled_dispatch(
#                    data, getattr(self.dispatcher, '_dispatch', None)
#                )
#            response += '\n'
#        except Exception, e: # This should only happen if the module is buggy
#            # internal error, report as HTTP server error
#            logging.error("Cannot dispatch XMLRPC request: %s", e)
#            responder(HTTP.INTERNAL_SERVER_ERROR, [('Content-Type', 'text/plain'),
#                                                   ('Cache-Control', 'no-cache')])
#            return []
#        else:
#            # got a valid XML RPC response
#            responder(HTTP.OK, [('Content-Type','text/xml'),
#                                ('Content-Length', str(len(response))),
#                                ('Cache-Control', 'no-cache')])
#            return [response]