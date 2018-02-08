"""
Copyright 2016 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
# pylint: disable=E0611,F0401
#         No name 'core' in module 'distutils'
#         Unable to import 'distutils.core'
from distutils.core import setup
from setuptools import find_packages


LICENSE = open("LICENSE").read()
DESCRIPTION = "mbed-flasher"
OWNER_NAMES = "Jussi Vatjus-Anttila"
OWNER_EMAILS = "Jussi.Vatjus-Anttila@arm.com"
VERSION = "0.6.3"

# Utility function to cat in a file (used for the README)
def read(fname):
    """
    read file by filename
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name="mbed-flasher",
      version=VERSION,
      description=DESCRIPTION,
      long_description=read("README.md"),
      author=OWNER_NAMES,
      author_email=OWNER_EMAILS,
      maintainer=OWNER_NAMES,
      maintainer_email=OWNER_EMAILS,
      url="https://github.com/ARMmbed/mbed-flasher",
      download_url="https://api.github.com/repos/ARMmbed/mbed-flasher/tarball/v{}".format(VERSION),
      packages=find_packages(exclude=["doc", "test", "logs"]),
      license=LICENSE,
      test_suite="test",
      tests_require=["mock"],
      entry_points={
          "console_scripts": ["mbedflash=mbed_flasher:mbedflash_main",],
      },
      install_requires=[
          "mbed-ls==1.3.6",
          "six",
          "pyserial",
          "pyOCD"
      ],
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "License :: OSI Approved :: Apache Software License",
          "Intended Audience :: Developers",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Topic :: Software Development :: Embedded Systems",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.6"
      ])
