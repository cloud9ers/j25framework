# will be set by Main() or any runner to app server
from j25.caching.CacheManager import CacheFactory
import logging
import sys

VERSION = '0.5'
logger = logging.getLogger("Framework")

###### GLOBALLY AVAILABLE ##########
config = None
project_directory = None
####################################

_cache = None
_store = None
try:
    import mongoengine
except ImportError:
    logger.critical("MongoEngine is not installed, all store operations will fail!")
else:
    sys.modules['j25.model'] = mongoengine

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

def is_dev():
    return config.main.mode == "DEV"

def onAppServerStart(func):
    func.onStart = True
    return func