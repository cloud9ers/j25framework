import os
import sys
from optparse import OptionParser

class ShellCommand(object):
    def get_option_group(self, parser):
        pass
    
    def execute(self, args):
        pass
    
    def get_name(self):
        pass
    
    def get_description(self):
        pass

class RelaxedOptionParser(OptionParser):
    ''' an option parser that doesn't throw errors on unknown options '''
    
    def _process_args(self, largs, rargs, values):
        while rargs:
            arg = rargs[0]
            try:
                if arg[0:2] == '--' and len(arg) > 2:
                    self._process_long_opt(rargs, values)
                elif arg[:1] == '-' and len(arg) > 1:
                    self._process_short_opts(rargs, values)
                else:
                    del rargs[0]
                    raise Exception
            except:
                largs.append(arg) 
                                               
def _createPythonPackage(parent, name, is_python_package):
    path = os.path.join(parent, name)
    os.mkdir(path)
    if is_python_package:
        open(os.path.join(path, '__init__.py'), 'w').close()

def _addPythonPath():
    sys.path.append(".")
    sys.path.append("./apps")

def _checkProject(AUTO_PROJECT_DIRS):
    if not _isProject(AUTO_PROJECT_DIRS):
        print >> sys.stderr, "current directory doesn't seem to be a correct project directory"
        exit(1)
          
def _isProject(auto_project_dirs):
    for directory, mandatory in auto_project_dirs:
        if not os.path.isdir(directory) and mandatory:
            return False
    if not os.path.isfile("server.ini"):
        return False
    return True