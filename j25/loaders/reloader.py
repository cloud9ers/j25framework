# Python Module Reloader
#
# Copyright (c) 2009, 2010 Jon Parise <jon@indelible.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import Importer
import j25
import logging
import os
import sys
import threading
import time
try:
    import queue
except ImportError:
    #python 2.x
    import Queue as queue

_win32 = (sys.platform == 'win32')

logger = logging.getLogger("Module Reloader")

class ModuleMonitor(threading.Thread):
    """Monitor module source file changes"""

    def __init__(self, interval=1):
        threading.Thread.__init__(self)
        self.daemon = True
        self.mtimes = {}
        self.queue = queue.Queue()
        self.interval = interval
        self.is_running = True
    
    def terminate(self):
        self.is_running = False
        
    def run(self):
        while self.is_running:
            self._scan()
            time.sleep(self.interval)
        logger.info("ModuleMonitor terminated")
        
    def _scan(self):
        # We're only interested in file-based modules (not C extensions).
        # We are only interested in project files changes
        modules = [m.__file__ for m in sys.modules.values()
                if m and '__file__' in m.__dict__ and m.__file__.startswith(j25.project_directory)]

        for filename in modules:
            # We're only interested in the source .py files.
            if filename.endswith('.pyc') or filename.endswith('.pyo'):
                filename = filename[:-1]

            # stat() the file. This might fail if the module is part of a
            # bundle (.egg). We simply skip those modules because they're
            # not really reloadable anyway.
            try:
                stat = os.stat(filename)
            except OSError:
                continue

            # Check the modification time. We need to adjust on Windows.
            mtime = stat.st_mtime
            if _win32:
                mtime -= stat.st_ctime

            # Check if we've seen this file before. We don't need to do
            # anything for new files.
            if filename in self.mtimes:
                # If this file's mtime has changed, queue it for reload.
                if mtime != self.mtimes[filename]:
                    print "file %s enqueued" % filename
                    self.queue.put(filename)

            # Record this filename's current mtime.
            self.mtimes[filename] = mtime

class Reloader(threading.Thread):

    def __init__(self, interval=1):
        threading.Thread.__init__(self)
        self.monitor = ModuleMonitor(interval=interval)
        self.monitor.start()
        self.interval = interval
        self.is_running = True
        logging.info("Module Monitor Started")

    def run(self):
        self._logger = logging.getLogger("Reloader")
        while self.is_running:
            self.poll()
            time.sleep(self.interval)
        self.monitor.terminate()
        self._logger.info("Module Reloader terminated")

    def terminate(self):
        self.is_running = False
            
    def poll(self):
        filenames = set()
        while not self.monitor.queue.empty():
            try:
                filename = self.monitor.queue.get_nowait()
                filenames.add(filename)
            except queue.Empty:
                break
        if filenames:
            self._reload(filenames)
    
    def _check(self, filenames, module):
        mod_file = getattr(module, '__file__', None)
        if mod_file:
            for filename in filenames:
                if mod_file.startswith(filename):
                    return True
            return False
            
    def _reload(self, filenames):
        modules = [m for m in sys.modules.values()
                if self._check(filenames, m)]

        for mod in modules:
            self._logger.info("Reloading module %s", mod.__name__)
            Importer.reload(mod)
        else:
            j25._load_routing()
            j25._update_mapper()
            j25._dispatcher.register_all_apps_router()