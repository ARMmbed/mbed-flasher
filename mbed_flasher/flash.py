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
from os.path import isfile
import platform
import types

EXIT_CODE_NO_PLATFORM_GIVEN = 35
EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE = 40
EXIT_CODE_FILE_DOES_NOT_EXIST = 45
EXIT_CODE_KEYBOARD_INTERRUPT = 50
EXIT_CODE_TARGET_ID_COULD_NOT_BE_MAPPED_TO_DEVICE = 55
EXIT_CODE_SYSTEM_INTERRUPT = 60

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

    @staticmethod
    def __get_flashers():
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

    @staticmethod
    def __find_by_target_id(target_id, ls):
        """find target by id
        """
        for target in ls:
            if target_id == target['target_id']:
                return target
        raise KeyError("target_id: %s not found" % target_id)

    @staticmethod
    def __find_by_platform_name(platform_name, ls):
        for target in ls:
            if platform_name == target['platform_name']:
                return target
        raise KeyError("platform_name: %s not found" % platform_name)

    def flash_multiple(self, build, platform_name, method='simple', target_ids_or_prefix=''):
        device_mapping_table = self.get_available_device_mapping()
        aux_device_mapping_table = []

        if not platform_name:
            found_platform = ''
            for item in device_mapping_table:
                if not found_platform:
                    found_platform = item['platform_name']
                else:
                    if item['platform_name'] != found_platform:
                        self.logger.error('Multiple devices and platforms found, '
                                          'please specify preferred platform with -t <platform>.')
                        return EXIT_CODE_NO_PLATFORM_GIVEN

        if isinstance(target_ids_or_prefix, types.ListType):
            for tid in target_ids_or_prefix:
                for item in device_mapping_table:
                    if platform_name:
                        if item['platform_name'] != platform_name:
                            # skipping boards that do not match with specified platform
                            continue
                    if item['target_id'] == tid:
                        aux_device_mapping_table.append(item)
        else:
            if target_ids_or_prefix:
                if len(target_ids_or_prefix) >= 1:
                    for item in device_mapping_table:
                        if platform_name:
                            if item['platform_name'] != platform_name:
                                # skipping boards that do not match with specified platform
                                continue
                        if item['target_id'].startswith(str(target_ids_or_prefix)):
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
            return EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
        self.logger.debug(device_mapping_table)

        print 'Going to flash following devices:'
        for item in device_mapping_table:
            print item['target_id']
        retcodes = 0
        if method == 'pyocd' and platform.system() != 'Windows':
            # pyOCD support for Linux based OSs is not so robust, flashing works sequentially not parallel
            i = 0
            for device in device_mapping_table:
                ret = self.flash(build, device['target_id'], None, device_mapping_table, method)
                if ret == 0:
                    self.logger.debug("dev#%i -> SUCCESS" % i)
                else:
                    self.logger.warning("dev#%i -> FAIL :(" % i)
                retcodes += ret
                i += 1
        else:
            passes = []
            retcodes = 0
            for target in device_mapping_table:
                retcode = self.flash(build, target['target_id'], None, device_mapping_table, method)
                retcodes += retcode
                if retcode == 0:
                    passes.append(True)
                else:
                    passes.append(False)
            i = 1
            for ok in passes:
                if ok:
                    self.logger.debug("dev#%i -> SUCCESS" % i)
                else:
                    self.logger.warning("dev#%i -> FAIL :(" % i)
                i += 1

        return retcodes

    def flash(self, build, target_id=None, platform_name=None, device_mapping_table=None, method='simple'):
        """Flash (mbed) device
        :param build:  Build -object or string (file-path)
        :param target_id: target_id
        :param platform_name: platform_name, to flash multiple devices of same type
        :param device_mapping_table: individual devices mapping table
        :param method: method for flashing i.e. simple, pyocd or edbg
        """
        
        K64F_TARGET_ID_LENGTH = 48

        if target_id is None and platform_name is None:
            raise SyntaxError("target_id or target_name is required")

        if not isfile(build):
            self.logger.error("Given file does not exist")
            return EXIT_CODE_FILE_DOES_NOT_EXIST
        if isinstance(target_id, types.ListType):
            return self.flash_multiple(build, platform_name, method, target_id)
        else:
            if target_id.lower() == 'all':
                return self.flash_multiple(build, platform_name, method)
            elif len(target_id) < K64F_TARGET_ID_LENGTH:
                return self.flash_multiple(build, platform_name, method, target_id)

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
            return EXIT_CODE_TARGET_ID_COULD_NOT_BE_MAPPED_TO_DEVICE

        if not platform_name:
            platform_name = target_mbed['platform_name']
        if platform_name not in self.SUPPORTED_TARGETS:
            raise NotImplementedError("Platform '%s' is not supported by mbed-flasher" % platform_name)

        target_mbed.update(self.SUPPORTED_TARGETS[platform_name])
        self.logger.debug("Flashing: %s", target_mbed["target_id"])

        flasher = self.__get_flasher(platform_name)
        try:
            retcode = flasher.flash(source=build, target=target_mbed, method=method)
        except KeyboardInterrupt:
            self.logger.error("Aborted by user")
            return EXIT_CODE_KEYBOARD_INTERRUPT
        except SystemExit:
            self.logger.error("Aborted by SystemExit event")
            return EXIT_CODE_SYSTEM_INTERRUPT

        if retcode == 0:
            self.logger.info("flash ready")
        else:
            self.logger.info("flash fails")
        return retcode
