from nose.core import TestProgram
from j25.scripts import Server
import logging

Server.setupLogging(logging.INFO)
TestProgram()