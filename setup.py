import sys
from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

required_packages = ['mako >= 0.3.6',
                     'mongoengine >= v0.4-0',
                     'routes >= 1.12.3',
                     'simplejson >= 2.1.2',
                     'celery >= 2.3.1',
                     'WebOb >= 1.0.8',
                     'Beaker >= 1.5.4',
                     'python-memcached >= 1.47'
                    ]
if sys.version_info < (2, 7):
    required_packages.append('importlib')
    
console_scripts = ['j25 =  j25.scripts.run:main']
setup(name='j25framework',
      description="A highly scalable REST application development framework",
      long_description="A highly scalable REST application development framework",
      version="0.5.1",
      url='http://confluence.cloud9ers.com/display/j25www/',
      author="Cloud Niners Ltd.",
      author_email="asoliman@cloud9ers.com",
      packages=find_packages(exclude=['test', 'test.*', 'rbac', 'rbac.*', ]),
      zip_safe=False,
      install_requires= required_packages,
      entry_points = {
                      'console_scripts': console_scripts
                      },
      license = "LGPLv3",
      
      )
