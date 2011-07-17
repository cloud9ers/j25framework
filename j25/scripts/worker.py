#!/usr/bin/env python

def main():
    from celery.bin import celeryd
    from j25.scripts import Server
    print Server.getBanner()
    
    celeryd.main()

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()