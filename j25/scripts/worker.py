#!/usr/bin/env python
from celery.bin import celeryd
from multiprocessing import freeze_support
import os
from j25.scripts import Server
import j25.worker.WorkerLoader

def main():
    print Server.getBanner()

    celeryd.main()

if __name__ == "__main__":
    freeze_support()
    main()