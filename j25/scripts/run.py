import Server
from Server import setupLogging, logLevelsMap
from j25 import Constants
from j25.utils.ColoredLogger import COLOR_SEQ, RESET_SEQ
from uuid import uuid4
import logging
import optparse
import os
import sys
import j25
from multiprocessing import freeze_support
from j25.scripts.utils import RelaxedOptionParser, _checkProject, _addPythonPath,\
    _createPythonPackage

#add libs in the framework
libs = os.path.join(j25.__path__[0], os.path.pardir, 'lib')
sys.path.insert(0, libs)

#initialize the framework constants
j25.init()

HERE = os.getcwd()

AUTO_APP_DIRS = [('model', True),
                  ('lib', True),
                  ('tmp', False),
                  ('controllers', True), 
                  ('tasks', True), 
                  ('tests', True), 
                  ('templates', True), 
                  ('static', False)
                  ]

AUTO_PROJECT_DIRS = [('apps', True), 
                     ('static', False), 
                     ('templates', True)
                     ]

project_routing_template = '''def router(map):
    pass'''

app_workerconfig = '''import sys
import os
sys.path.insert(0, os.getcwd())

BROKER_HOST = "localhost"
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"

CELERYD_CONCURRENCY=2
## Using the database to store results
# CELERY_RESULT_BACKEND = "database"
# CELERY_RESULT_DBURI = "sqlite:///celerydb.sqlite"

# Results published as messages (requires AMQP).
CELERY_RESULT_BACKEND = "amqp"
DISABLE_RATE_LIMITS=True
'''

app_config_template='''#J25_TEMPLATE_ENGINE="mako"'''
app_routing_template='''APP_ROOT = '/%s'

def router(map):
    #map.connect('master', '/{controller}/{action}') # master app example
    with map.submapper(path_prefix=APP_ROOT) as m:
        m.connect("home", "/", controller="main", action="index")
        m.connect(None, "/{controller}/{action}")
        # ADD CUSTOM ROUTES HERE
        #m.connect(None, "/error/{action}/{id}", controller="error")
        #m.connect("home", "/{controller}/{action}/{id}", controller="batates")
'''
logger = logging.getLogger('j25')


def newApp(args, options):
    from j25.Configuration import Configuration

    if len(args) < 2:
        print >> sys.stderr, "you must supply the name of the app"
        exit(1)
    _checkProject(AUTO_PROJECT_DIRS)
    appName = args[1]
    appDirectory = os.path.join('apps', appName)
    print Server.getBanner()
    print COLOR_SEQ % 33
    try:
        _createPythonPackage(HERE, appDirectory, True)
        f = open(os.path.join(appDirectory, 'config.py'), 'w')
        f.write(app_config_template)
        f.close()
        f = open(os.path.join(appDirectory, 'routing.py'), 'w')
        f.write(app_routing_template % appName)
        f.close()
        for directory, is_python_package in AUTO_APP_DIRS:
            _createPythonPackage(appDirectory, directory, is_python_package)
        #update configuration
        config = Configuration.load_file("server.ini", False)
        currentApps = eval(config.main.applications)
        assert isinstance(currentApps, list)
        currentApps.append('apps.%s' % appName)
        config.main.applications = str(list(set(currentApps)))
        Configuration.dump_file("server.ini", config)
        logger.info("Application %s has been created. Current project has been configured." % appName)
    finally:
        print RESET_SEQ
    
def runServer(args, options):
    _checkProject(AUTO_PROJECT_DIRS)
    _addPythonPath()
    args.pop(0)
    j25.project_directory = HERE
    Server.Main("server.ini")

def runWorker(args, options):
    import worker
    freeze_support()
    sys.argv.pop(0)
    j25.project_directory = HERE
    worker.main("server.ini")
    
def dumpConfig(args, options):
    from j25.Configuration import Configuration
    if len(args) < 2:
        print >> sys.stderr, "Please supply a configuration filename"
        exit(1)
    Configuration.dump_file(args[1])
                   
def newProject(args, options):
    from j25.Configuration import Configuration

    if len(args) < 2:
        print >> sys.stderr, "Please supply a project name"
        exit(1)
    appName = options.withapp
    projectName = args[1]
    print Server.getBanner()
    print COLOR_SEQ % 33
    print "Creating project: %s" % projectName
    _createPythonPackage(HERE, projectName, False)
    #creating project structure
    for directory, is_python_package in AUTO_PROJECT_DIRS:
        _createPythonPackage(projectName, directory, is_python_package)
    #creating templates
    config = Configuration.create_empty_config()
    s1 = config.add_section('main')
    s1.add_option('project_name', projectName)
    s1.add_option('applications', [])
    s1.add_option('excluded_applications_from_worker', [])
    s1.add_option("mode", "DEV")
    s1.add_option("ip", "0.0.0.0")
    s1.add_option("port", "8800")
    s1.add_option("is_subdomain_aware", True) 
    
    s2 = config.add_section('session')
    s1.add_option('project_name', projectName)
    s2.add_option('secret', uuid4().hex + uuid4().hex)
    s2.add_option('url', ('%s/c9#session' % Constants.MONGODB_URL))
    s2.add_option('secure', 'False')
    s2.add_option('timeout', '600')
    s3 = config.add_section('store')
    s3.add_option("db_name", "c9_%s" % projectName)
    s3.add_option("ip", "127.0.0.1")
    s3.add_option("auto_create_collections", None)  
    Configuration.dump_file(os.path.join(projectName, 'server.ini'), config)
    f = open(os.path.join(projectName, 'routing.py'), 'w')
    f.write(project_routing_template)
    f.close()
    f = open(os.path.join(projectName, 'workerconfig.py'), 'w')
    f.write(app_workerconfig)
    f.close()
    if options.withapp:
        config = Configuration.load_file(os.path.join(projectName, 'server.ini'), False)
        builtin_Apps = eval(config.main.applications)
        assert isinstance(builtin_Apps, list)
        if not appName in builtin_Apps:
            builtin_Apps.append(appName)
            config.main.applications = str(builtin_Apps)
            Configuration.dump_file(os.path.join(projectName, 'server.ini'), config)
            logger.info("\033[1;33mProject %s Created with Application %s.\033[0m"% (projectName, appName))
        else:
            logger.info("\033[1;33mApplication %s already installed in the project by Default.\033[0m" % appName)
    print RESET_SEQ
    
def installApp(args, options):
    from j25.Configuration import Configuration
    if len(args) < 2:
        print >> sys.stderr, "you must supply the name of the app"
        exit(1)
    _checkProject(AUTO_PROJECT_DIRS)
    appName = args[1]
    print Server.getBanner()
    print COLOR_SEQ % 33
    config = Configuration.load_file('server.ini', False)
    currentApps = eval(config.main.applications)
    assert isinstance(currentApps, list)
    if not appName in currentApps:
        currentApps.append(appName)
        config.main.applications = str(currentApps)
        Configuration.dump_file('server.ini', config)
        logger.info("\033[1;33mApplication %s added to project.\033[0m"% appName)
    else:
        logger.info("\033[1;33mApplication %s already installed in the project.\033[0m" % appName)
    
COMMANDS = {'new-app': newApp, 
            'run-server': runServer,
            'run-worker': runWorker,
            'dump-config': dumpConfig,
            'new-project': newProject,
            'install-app': installApp,
            }

def main():
    parser = RelaxedOptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", default=False, help="Set verbosity level")
    parser.add_option("-l", "--logging", dest="logging", default="INFO", help="Set logging level")
    parser.add_option("-w", "--with", dest="withapp", default="", help="Add built in app to new project")
    
    options, args = parser.parse_args()
    setupLogging(logLevelsMap.get(options.logging, logging.INFO))

    if not args:
        print >> sys.stderr, "No command is given"
        print >> sys.stderr, "    Possible commands: %s" % str(COMMANDS.keys())
        
        exit(1)
    if args[0] not in COMMANDS:
        print >> sys.stderr, "Unknown command %s is given" % args[0]
        exit(1)
    import j25.loaders.WorkerLoader
    os.putenv('CELERY_LOADER', j25.loaders.WorkerLoader.__name__ + '.WorkerLoader')
    os.environ['CELERY_LOADER'] = j25.loaders.WorkerLoader.__name__ + '.WorkerLoader'
    os.putenv('WORKER_CONFIG', 'workerconfig')
    COMMANDS[args[0]](args, options)
    
if __name__ == '__main__':
    main()
