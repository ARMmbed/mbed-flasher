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
from Queue import Queue
import threading
from os.path import isfile
import platform
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

    def flash_multiple(self, build, platform_name, device_mapping_table=None, pyocd=False, target_prefix=''):
        device_mapping_table = self.get_available_device_mapping()
        aux_device_mapping_table = []
        
        if not platform_name:
            found_platform = ''
            for item in device_mapping_table:
                if not found_platform:
                    found_platform = item['platform_name']
                else:
                    if item['platform_name'] != found_platform:
                        self.logger.error('Multiple devices and platforms found, please specify preferred platform with -t <platform>.')
                        return -9
        
        if target_prefix:
            if len(target_prefix) >= 1:
                for item in device_mapping_table:
                    if platform_name:
                        if item['platform_name'] != platform_name:
                            #skipping boards that do not match with specified platform
                            continue
                    if item['target_id'].startswith(str(target_prefix)):
                        aux_device_mapping_table.append(item)
        else:
            for item in device_mapping_table:
                if platform_name:
                    if item['platform_name'] == platform_name:
                        aux_device_mapping_table.append(item)
                    
        if len(aux_device_mapping_table) > 0:
            device_mapping_table = aux_device_mapping_table
            
        device_count = len(device_mapping_table)
        if device_count == 0:
            self.logger.error('no devices to flash')
            return -3
        self.logger.debug(device_mapping_table)
        
        print 'Going to flash following devices:'
        for item in device_mapping_table:
            print item['target_id']
        retcodes = 0
        if pyocd and platform.system() != 'Windows':
            # pyOCD support for Linux based OSs is not so robust, flashing works sequentially not parallel
            i = 0
            for device in device_mapping_table:
                ret = self.flash(build, device['target_id'], None, device_mapping_table, pyocd)
                if ret == 0:
                    self.logger.debug("dev#%i -> SUCCESS" % i)
                else:
                    self.logger.warning("dev#%i -> FAIL :(" % i)
                retcodes += ret
                i += 1
            
        else:
            '''
            ans_q = Queue()
            parameters = [(build, target['target_id'], None, device_mapping_table, pyocd, ans_q) for target in device_mapping_table]
            threads = [ (threading.Thread(target=self.flash, args=args)) for args in parameters]

            for t in threads:
                sleep(0.2)
                t.start()

            passes = []
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
            '''
            passes = []
            retcodes = 0
            for target in device_mapping_table:
                retcode = 0
                retcode = self.flash(build, target['target_id'], None, device_mapping_table, pyocd)
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

    def flash(self, build, target_id=None, platform_name=None, device_mapping_table=None, pyocd=False, ret_q=None):
        """Flash (mbed) device
        :param build:  Build -object or string (file-path)
        :param target_id: target_id
        :param target_name: target_name, to flash multiple devices
        :param device_mapping_table: individual devices mapping table
        """

        if target_id is None and platform_name is None:
            raise SyntaxError("target_id or target_name is required")

        if not isfile(build):
            self.logger.error("Given file does not exist")
            return -5

        if target_id.lower() == 'all':
            return self.flash_multiple(build, platform_name, device_mapping_table, pyocd)
        elif len(target_id) < 48:
            return self.flash_multiple(build, platform_name, device_mapping_table, pyocd, target_id)
        
        if device_mapping_table:
            if isinstance(device_mapping_table, dict):
                device_mapping_table = [device_mapping_table]
            elif not isinstance(device_mapping_table, list):
                raise SystemError('device_mapping_table wasn\'t list or dictionary')
        else:
            device_mapping_table = self.get_available_device_mapping()
        
        self.logger.debug(device_mapping_table)
        
        try:
            if target_id:
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
            raise NotImplementedError("Platform '%s' is not supported by mbed-flasher" % platform_name )

        #if not isinstance(build, Build):
        #    build = Build.init(ref=build)
        target_mbed.update(self.SUPPORTED_TARGETS[platform_name])
        self.logger.debug("Flashing: %s",target_mbed["target_id"])

        flasher = self.__get_flasher(platform_name)
        try:
            retcode = flasher.flash(source=build, target=target_mbed, pyocd=pyocd)
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
            self.logger.info("flash ready")
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
