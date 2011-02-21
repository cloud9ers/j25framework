#!/usr/bin/env python
from celery.bin import celeryd
from multiprocessing import freeze_support
import logging
import os
from j25.scripts import Server

def main():
    os.putenv('CELERY_LOADER', 'j25.worker.WorkerLoader.WorkerLoader')
    os.environ['CELERY_LOADER'] = 'j25.worker.WorkerLoader.WorkerLoader'
    Server.setupLogging(logging.INFO)
    celeryd.main()

if __name__ == "__main__":
    freeze_support()
    main()