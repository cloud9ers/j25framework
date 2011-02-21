class CacheManager(object):        
    def __init__(self, config):
        self._config = config
    
    def _get_regions_configuration(self):
        cacheConfig = {}
        regions = self._config.cache.regions and [r.strip() for r in self._config.cache.regions.split(",")]
        if regions:
            for region in regions:
                keys = ["%s_type" % region, "%s_url" % region, "%s_expire" % region]
                for k in keys:
                    cacheConfig['cache.%s' % k.replace('_', '.')] = self._config.cache.get_option(k)        
        return cacheConfig 
    
    def get_beaker_cache_manager(self):
        import beaker.cache
        from beaker.util import parse_cache_config_options
        cache_opts = {           
                      'cache.regions': self._config.cache.regions,
                      'cache.type' : self._config.cache.type,
                      'cache.url' : self._config.cache.url,
                      'cache.lock_dir': self._config.cache.lock_dir,
                      'cache.data_dir': self._config.cache.data_dir,
                      'cache.expire' : self._config.cache.expire
                      }
        cache_opts.update(self._get_regions_configuration())
        cacheManager = beaker.cache.CacheManager(**parse_cache_config_options(cache_opts))
        return cacheManager
                    
class CacheFactory(object):     
    @staticmethod
    def create_instance(config):
        return CacheManager(config).get_beaker_cache_manager()