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

import logging
import subprocess

from os.path import join, abspath, walk
from time import sleep

class Flash(object):
    """ Flash object, which manage flashing single device
    """
    FLASHERS = []
    SUPPORTED_TARGETS = {}

    def __init__(self):
        self.logger = logging.getLogger('mbed-flasher')
        self.FLASHERS = self.__get_flashers()
        self.SUPPORTED_TARGETS = self.__update_supported_targets()
        self.logger.debug("Supported targets: "+', '.join(self.SUPPORTED_TARGETS.keys()))

    def get_supported_targets(self):
        return self.SUPPORTED_TARGETS.keys()

    def get_supported_flashers(self):
        available_flashers = []
        for Flasher in self.FLASHERS:
            available_flashers.append(Flasher.name)
        return available_flashers

    def __update_supported_targets(self):
        all_supported_targets = {}
        for Flasher in self.FLASHERS:
            supported_targets = Flasher.get_supported_targets()
            all_supported_targets.update(supported_targets)
        return all_supported_targets

    def __get_flashers(self):
        from flashers import AvailableFlashers
        return AvailableFlashers

    def get_available_device_mapping(self):
        available_devices = []
        for Flasher in self.FLASHERS:
            devices = Flasher.get_available_devices()
            available_devices.extend(devices)
        return available_devices

    def __get_flasher(self, platform_name):
        if not (platform_name in self.SUPPORTED_TARGETS.keys()):
            raise NotImplementedError("Flashing %s is not supported" % platform_name)

        for Flasher in self.FLASHERS:
            if platform_name in self.SUPPORTED_TARGETS.keys():
                return Flasher()

        raise Exception("oh nou")

    def flash(self, build, target_id=None, platform_name=None, device_mapping_table=None):
        """Flash (mbed) device
        :param build:  Build -object or string (file-path)
        :param target_id: target_id
        :param target_name: target_name, to flash multiple devices
        :param device_mapping_table: individual devices mapping table
        """

        if target_id is None and platform_name is None:
            raise SyntaxError("target_id or target_name is required")

        if device_mapping_table is None:
            device_mapping_table = self.get_available_device_mapping()

        try:
            if not target_id is None:
                target_mbed = self.__find_by_target_id(target_id, device_mapping_table)
            else:
                target_mbed = self.__find_by_platform_name(platform_name, device_mapping_table)
        except KeyError as err:
            self.logger.error(err)
            return -3

        if not platform_name:
            platform_name = target_mbed['platform_name']
        if not platform_name in self.SUPPORTED_TARGETS:
            raise NotImplementedError("Platform '%s' is not supproted by mbed-flasher" % platform_name )

        #if not isinstance(build, Build):
        #    build = Build.init(ref=build)
        target_mbed.update(self.SUPPORTED_TARGETS[platform_name])
        self.logger.debug("Flashing: %s",target_mbed["target_id"])

        flasher = self.__get_flasher(platform_name)
        try:
            retcode = flasher.flash(source=build, target=target_mbed)
        except KeyboardInterrupt:
            self.logger.error("Aborted by user")
            return -1
        except SystemExit:
            self.logger.error("Aborted by SystemExit event")
            return -2

        if retcode == 0:
            waitTime = target_mbed['properties']['program_cycle_s']
            self.logger.info("waiting for %.1f second" % waitTime)
            sleep(waitTime)
            self.logger.info("flash ready")
        else:
            self.logger.info("flash fails")
        return retcode

    def __find_by_target_id(self, target_id, ls):
        """find target by id
        """
        for target in ls:
            if target_id == target['target_id']:
                return target
        raise KeyError("target_id: %s not found" % target_id)

    def __find_by_platform_name(self, platform_name, ls):
        for target in ls:
            if platform_name == target['platform_name']:
                return target
        raise KeyError("platform_name: %s not found" % platform_name)
