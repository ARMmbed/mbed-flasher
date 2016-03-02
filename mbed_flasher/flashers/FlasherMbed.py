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

Author:
Jussi Vatjus-Anttila <jussi.vatjus-anttila@arm.com>
"""

import json
import logging
import sys
import six
from os.path import join, abspath, dirname
from shutil import copy
import os
import platform


class FlasherMbed(object):
    name = "Mbed"

    def __init__(self):
        self.logger = logging.getLogger('mbed-flasher')

    @staticmethod
    def get_supported_targets():
        """Load target mapping information
        """
        libpath = dirname(abspath(sys.modules[__name__].__file__))
        return json.loads(open( join(libpath, "FlasherMbed.target_info.json"), "rb").read())

    @staticmethod
    def get_available_devices():
        import mbed_lstools
        mbeds = mbed_lstools.create()
        return mbeds.list_mbeds()

    def flash(self, source, target):
        """copy file to the destination
        :param binary_data: binary data to be flashed
        :param target: target
        """

        mount_point = target['mount_point']+'/'
        binary_type = target['properties']['binary_type']
        destination=abspath(join(mount_point, 'image'+binary_type))

        if isinstance(source, six.string_types):
            try:
                if platform.system() == 'Windows':
                    self.logger.debug("copying file: %s to %s" % (source, destination))
                    copy(source, destination)
                else:
                    self.logger.debug('read source file')
                    source = open(source, 'rb').read()
                    self.logger.debug("writing binary: %s (size=%i bytes)", destination, len(source))
                    new_file = os.open(destination, os.O_CREAT | os.O_DIRECT | os.O_TRUNC | os.O_RDWR )
                    os.write(new_file, source)
                    os.close(new_file)

                self.logger.debug("ready")
                return 0
            except IOError as err:
                self.logger.error(err)
                raise err
