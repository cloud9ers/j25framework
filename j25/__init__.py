# will be set by Main() or any runner to app server
from j25.caching.CacheManager import CacheFactory
import logging
import sys
from j25 import http

#Remember to modify setup.py
VERSION = '0.5.5'

###### GLOBALLY AVAILABLE ##########
config = None
framework_directory = __path__[0]
project_directory = None
####################################

_cache = None
_store = None
_reloader = None
_dispatcher = None
_routes_middleware = None
_mapper = None
_apps = []
model = None
Http = http

def is_dev():
    return config.main.mode == "DEV"

def _create_routing_middleware():
    global _routes_middleware
    from routes.middleware import RoutesMiddleware
    _load_routing()
    assert _mapper is not None
    _mapper.sub_domains = eval(config.main.is_subdomain_aware)
    _routes_middleware = RoutesMiddleware(_dispatcher.create_application, _mapper)

def _update_mapper():
    _routes_middleware.mapper = _mapper

def _load_routing():
    global _mapper
    logger = logging.getLogger("j25 Framework")
    from routes import Mapper
    if is_dev():
        always_scan = True
    else:
        always_scan = False
    _mapper = Mapper(controller_scan=_dispatcher.get_controller_names, always_scan=always_scan)
    try:
        import routing
    except ImportError:
        logger.warn("No routing.py defined in the project, can be safe if app routing.py is correctly configured")
    else:
        routing.router(_mapper)
    logger.info("Routing is loaded")
        
def init():    
    logger = logging.getLogger("Framework")
    try:
        import mongoengine
    except ImportError, e:
        logger.critical("MongoEngine is not installed, all store operations will fail!, this shouldn't ever happen!... Reason: %s", e)
        print >> sys.stderr, "MongoEngine is not installed, all store operations will fail!, this shouldn't ever happen!... Reason: %s" % e
        exit(22)
    else:
        sys.modules['j25.model'] = mongoengine
        global model
        model = mongoengine


class CacheProxy(object):
    def __getattribute__(self, attr):
        global _cache
        if not _cache:
            _cache = CacheFactory.create_instance(config)
        return getattr(_cache, attr)

def initStore():
    global _store
    from j25.exceptions.StoreExceptions import UnknownStoreException
    from j25.stores.StoreFactory import StoreFactory
    if _store:
        return _store
    try:
        _store = StoreFactory.create_instance(config) 
    except UnknownStoreException, e:
        logging.critical(str(e))
         
cache = CacheProxy()

