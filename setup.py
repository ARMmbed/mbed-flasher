"""
This module defines the attributes of the
PyPI package for the mbed SDK test suite
"""

"""
mbed SDK
Copyright (c) 2011-2015 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Jussi Vatjus-Anttila <jussi.vatjus-anttila@arm.com>
"""

import os
from distutils.core import setup
from setuptools import find_packages


LICENSE = open('LICENSE').read()
DESCRIPTION = "mbed 3.0 flasher"
OWNER_NAMES = 'Jussi Vatjus-Anttila, Azim Khan'
OWNER_EMAILS = 'Jussi.Vatjus-Anttila@arm.com'

# Utility function to cat in a file (used for the README)
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='mbed-flasher',
      version='0.0.1',
      description=DESCRIPTION,
      long_description=read('README.md'),
      author=OWNER_NAMES,
      author_email=OWNER_EMAILS,
      maintainer=OWNER_NAMES,
      maintainer_email=OWNER_EMAILS,
      url='https://github.com/ARMmbed/mbed-flasher',
      packages=find_packages(),
      package_data={'': ['FlasherMbed.target_info.json']},
      license=LICENSE,
      test_suite = 'test',
      entry_points={
        "console_scripts": ["mbedflash=mbed_flasher:mbedflash_main",],
      },
      install_requires=["PrettyTable>=0.7.2",
        "mbed-ls",
        "colorama>=0.3,<0.4",
       ])
