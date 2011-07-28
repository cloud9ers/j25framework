#!/usr/bin/env python
import logging, sys

def main(configFile):
    from celery.bin import celeryd
    from j25.scripts import Server
    print Server.getBanner()
    logger = logging.getLogger("j25")
    logger.debug("Started with argv=%s", str(sys.argv))    
    if configFile:
        from j25.Configuration import Configuration
        config = Configuration.load_file(configFile)
    else:
        config = Configuration.load_defaults()
    
    import j25
#    if config.main.mode == "DEV":
#        Importer.enable()
#        j25._reloader = Reloader(0.6)
#        j25._reloader.start()
#        logger.warning("\033[1;31mDEVELOPMENT MODE ACTIVE\033[0m")

    logger.info("\033[1;33mProject: %s\033[0m", config.main.project_name)    
    #setting configuration global
    j25.config = config
    
    #init store
    logger.debug("Connecting to Database")
    j25.initStore()
    
    celeryd.main()

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()