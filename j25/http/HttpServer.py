from beaker.middleware import SessionMiddleware
from routes.middleware import RoutesMiddleware
import j25
import rocket
import logging
import signal

logger = logging.getLogger("HttpServer")

class HttpServer(object):
    def __init__(self, config):
        self.config = config
        logger.info("Creating HTTP server on %s:%s", config.main.ip, int(config.main.port))
        session_opts = {'session.type': config.session.type,
                        'session.cookie_expires': bool(config.session.cookie_expires),
                        'session.data_dir': '/tmp/',
                        'session.key' : config.session.key,
                        'session.url' : ';'.join(config.session.url.split(',')),
                        'session.auto': bool(config.session.auto),
                        'session.secret': config.session.secret,
                        'session.secure': bool(config.session.secure),
                        'session.timeout': int(config.session.timeout)
                        }
        app_info = {'wsgi_app': SessionMiddleware(j25._routes_middleware, session_opts, environ_key=j25.Constants.SESSION_KEY)}
        sock_list = [config.main.ip, int(config.main.port)]
        rocket.HTTP_SERVER_SOFTWARE = "J25 Web Server %s" % j25.VERSION
        self.server = rocket.Rocket(tuple(sock_list),
                                    'wsgi', 
                                    app_info, 
                                    int(config.main.num_threads), 
                                    int(config.main.request_queue_size), 
                                    int(config.main.timeout))
        
    def start(self):
        try:
            signal.signal(signal.SIGTERM, lambda a, b, s=self: s.stop())
            signal.signal(signal.SIGINT, lambda a, b, s=self: s.stop())
        except:
            pass
        
        logger.info("waiting for requests...")
        self.server.start()
        
    def is_running(self):
        return self.server.is_running()
    
    def stop(self):
        logger.info("Stopping the HTTP server")
        self.server.stop()
        if j25._reloader:
            j25._reloader.terminate()
