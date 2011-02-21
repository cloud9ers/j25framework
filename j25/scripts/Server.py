from j25.utils.ColoredLogger import ColoredFormatter
import logging
import sys

logLevelsMap = {"DEBUG": logging.DEBUG,
                "INFO" : logging.INFO,
                "WARN" : logging.WARN,
                "ERROR": logging.ERROR
                }
def getBanner():
    return '''\033[1m\033[1;34m
    ------------------------------------------
       _                 _  ___               
      | |               | |/ _ \              
   ___| | ___  _   _  __| | (_) |___ _ __ ___ TM
  / __| |/ _ \| | | |/ _` |\__, / _ \ '__/ __| 
 | (__| | (_) | |_| | (_| |  / /  __/ |  \__ \  
  \___|_|\___/ \__,_|\__,_| /_/ \___|_|  |___/
    ==========================================  
           CLOUD DEVELOPMENT MADE FUN!
    \033[0m'''
    
def Main(configuration):
    boot(configuration)

def setupLogging(level):
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)
    logger.setLevel(level)
    
def boot(configFile):
    from j25.Configuration import Configuration
    from j25.http.HttpServer import HttpServer
    from j25.http.RequestDispatcher import RequestDispatcher
    from j25.loaders import AppLoader
    import j25
    logger = logging.getLogger("j25")
    logger.debug("Started with argv=%s", str(sys.argv))    
    if configFile:
        config = Configuration.load_file(configFile)
    else:
        config = Configuration.load_defaults()
    
    logger.info("\033[1;33mProject: %s\033[0m", config.main.project_name)    
    #setting configuration global
    j25.config = config
    
    #init store
    logger.debug("Connecting to MongoDB")
    j25.initStore()
        
    if config.main.mode == "DEV":
        logger.warning("\033[1;31mDEVELOPMENT MODE ACTIVE\033[0m")
    #create the dispatcher
    dispatcher = RequestDispatcher(AppLoader.AutoAppLoader(eval(config.main.applications)))
    #run the server and loop forever

    ws = HttpServer(dispatcher, config)
    logger.info(getBanner())
    ws.start()
        
if __name__ == '__main__':
    Main()