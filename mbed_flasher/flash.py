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
from Queue import Queue
import threading
from os.path import join, abspath, walk
from time import sleep
from enhancedserial import EnhancedSerial

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

    def flash_multiple(self, build, platform_name, device_mapping_table=None):
        device_mapping_table = self.get_available_device_mapping()
        device_count = len(device_mapping_table)
        if device_count == 0:
            self.logger.error('no devices to flash')
            return -3
        self.logger.debug(device_mapping_table)
        ans_q = Queue()
        parameters = [(build, target['target_id'], None, device_mapping_table, ans_q) for target in device_mapping_table]
        threads = [ (threading.Thread(target=self.flash, args=args)) for args in parameters]

        for t in threads:
            t.start()

        passes = []
        retcodes = 0
        for t in threads:
            t.join()

        results = [ ans_q.get() for _ in threads ]
        for retcode in results:
            retcodes += retcode
            if retcode == 0:
                passes.append(True)
            else:
                passes.append(False)

        i=1
        for ok in passes:
            if ok: self.logger.debug("dev#%i -> SUCCESS" % i)
            else:  self.logger.warning("dev#%i -> FAIL :(" % i)
            i += 1

        return retcodes

    def flash(self, build, target_id=None, platform_name=None, device_mapping_table=None, ret_q=None):
        """Flash (mbed) device
        :param build:  Build -object or string (file-path)
        :param target_id: target_id
        :param target_name: target_name, to flash multiple devices
        :param device_mapping_table: individual devices mapping table
        """

        if target_id is None and platform_name is None:
            raise SyntaxError("target_id or target_name is required")

        if target_id == '*':
            return self.flash_multiple(build, platform_name, device_mapping_table)

        if device_mapping_table:
            if isinstance(device_mapping_table, dict):
                device_mapping_table = [device_mapping_table]
            elif not isinstance(device_mapping_table, list):
                raise SystemError('device_mapping_table wasnt list or dictionary')
        else:
            device_mapping_table = self.get_available_device_mapping()

        try:
            if not target_id is None:
                target_mbed = self.__find_by_target_id(target_id, device_mapping_table)
            else:
                target_mbed = self.__find_by_platform_name(platform_name, device_mapping_table)
        except KeyError as err:
            self.logger.error(err)
            if ret_q:
                ret_q.put(-3)
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
            if ret_q:
                ret_q.put(-1)
            return -1
        except SystemExit:
            self.logger.error("Aborted by SystemExit event")
            if ret_q:
                ret_q.put(-2)
            return -2

        if retcode == 0:
            self.logger.info("waiting for 10 second")
            sleep(10)
            self.logger.info("flash ready")

            self.port = False
            if 'serial_port' in target_mbed:
                self.port = EnhancedSerial(target_mbed["serial_port"])
                self.port.baudrate = 115200
                self.port.timeout = 0.01
                self.port.xonxoff = False
                self.port.rtscts = False
                self.port.flushInput()
                self.port.flushOutput()
                
                if self.port:
                    self.logger.info("sendBreak to device to reboot")
                    result = self.port.safe_sendBreak()
                    if result:
                        self.logger.info("reset completed")
                    else:
                        self.logger.info("reset failed")
        else:
            self.logger.info("flash fails")
        if ret_q:
            ret_q.put(retcode)
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
