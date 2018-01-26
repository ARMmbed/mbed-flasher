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

from os.path import isfile

from mbed_flasher.common import Logger
from mbed_flasher.flashers import AvailableFlashers
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_PLATFORM_REQUIRED
from mbed_flasher.return_codes import EXIT_CODE_FILE_DOES_NOT_EXIST
from mbed_flasher.return_codes import EXIT_CODE_KEYBOARD_INTERRUPT
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_SYSTEM_INTERRUPT
from mbed_flasher.return_codes import EXIT_CODE_REQUESTED_FLASHER_DOES_NOT_EXIST


class Flash(object):
    """ Flash object, which manage flashing single device
    """
    _flashers = []
    supported_targets = {}

    def __init__(self, logger=None):
        if logger is None:
            logger = Logger('mbed-flasher')
            logger = logger.logger
        self.logger = logger
        self._flashers = self.__get_flashers()
        self.supported_targets = self.__update_supported_targets()

    def get_supported_targets(self):
        """
        :return: supported targets
        """
        return self.supported_targets

    def get_supported_flashers(self):
        """
        :return: supported flashers
        """
        available_flashers = []
        for flasher in self._flashers:
            available_flashers.append(flasher.name)
        return available_flashers

    def __update_supported_targets(self):
        """
        :return: list of all supported targets
        """
        all_supported_targets = []
        for flasher in self._flashers:
            supported_targets = flasher.get_supported_targets()
            all_supported_targets.extend(supported_targets)
        return all_supported_targets

    @staticmethod
    def __get_flashers():
        """
        :return: list of available flashers
        """
        return AvailableFlashers

    @staticmethod
    def get_flasher(flasher=None):
        """
        :param flasher: None, if not given a flasher
        :return: return available flasher if found, otherwise return exit code
        """
        for available_flasher in AvailableFlashers:
            if available_flasher.name.lower() == flasher.lower():
                return available_flasher

        return EXIT_CODE_REQUESTED_FLASHER_DOES_NOT_EXIST

    def get_available_device_mapping(self):
        """
        :return: list of available devices
        """
        available_devices = []
        for flasher in self._flashers:
            devices = flasher.get_available_devices()
            available_devices.extend(devices)
        return available_devices

    def __get_flasher(self, platform_name):
        """
        :param platform_name: platform name
        :return:
        """
        if platform_name not in self.supported_targets:
            raise NotImplementedError("Flashing %s is not supported" % platform_name)

        for flasher in self._flashers:
            return flasher(logger=self.logger)

        raise Exception("oh nou")

    @staticmethod
    def __find_by_target_id(target_id, target_list):
        """find target by id
        """
        for target in target_list:
            if target_id == target['target_id']:
                return target
        raise KeyError("target_id: %s not found" % target_id)

    @staticmethod
    def __find_by_platform_name(platform_name, target_list):
        """
        :param platform_name: platform name
        :param target_list: target list
        :return: target
        """
        for target in target_list:
            if platform_name == target['platform_name']:
                return target
        raise KeyError("platform_name: %s not found" % platform_name)

    def _verify_platform_coherence(self, device_mapping_table):
        """
        Verify platform is same across devices.
        :param device_mapping_table: list of devices to verify
        :return: return code
        """
        found_platform = ''
        for item in device_mapping_table:
            if not found_platform:
                found_platform = item['platform_name']
            elif item['platform_name'] != found_platform:
                self.logger.error('Multiple devices and platforms found,'
                                  'please specify preferred platform with'
                                  ' -t <platform>.')
                return EXIT_CODE_PLATFORM_REQUIRED

    # pylint: disable=too-many-arguments
    def flash_multiple(self, build, platform_name,
                       method='simple', target_ids_or_prefix='', no_reset=None):
        """
        :param build: build
        :param platform_name: platform name
        :param method: method
        :param target_ids_or_prefix: target ids or prefix
        :param no_reset: with/without reset
        :return:
        """
        device_mapping_table = self.get_available_device_mapping()

        if not platform_name:
            return_code = self._verify_platform_coherence(device_mapping_table)
            if return_code:
                return return_code

        if isinstance(target_ids_or_prefix, list):
            aux_device_mapping_table = Flash._map_by_target_id(
                device_mapping_table=device_mapping_table,
                platform_name=platform_name,
                target_ids=target_ids_or_prefix)
        elif target_ids_or_prefix:
            aux_device_mapping_table = Flash._map_by_prefix(
                device_mapping_table=device_mapping_table,
                platform_name=platform_name,
                prefix=target_ids_or_prefix)
        else:
            aux_device_mapping_table = Flash._map_by_platform(
                device_mapping_table=device_mapping_table,
                platform_name=platform_name)

        if aux_device_mapping_table:
            device_mapping_table = aux_device_mapping_table

        if not device_mapping_table:
            self.logger.error('no devices to flash')
            return EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE

        self.logger.debug(device_mapping_table)

        self.logger.info('Going to flash following devices:')
        for item in device_mapping_table:
            self.logger.info(item['target_id'])

        i = 1
        for device in device_mapping_table:
            ret = self.flash(build=build,
                             target_id=device['target_id'],
                             platform_name=None,
                             device_mapping_table=device_mapping_table,
                             method=method,
                             no_reset=no_reset)
            if ret == EXIT_CODE_SUCCESS:
                self.logger.debug("dev#%i -> SUCCESS", i)
            else:
                self.logger.warning("dev#%i -> FAIL", i)
                return ret
            i += 1

        return EXIT_CODE_SUCCESS

    # pylint: disable=too-many-return-statements
    def flash(self, build, target_id=None, platform_name=None,
              device_mapping_table=None, method='simple', no_reset=None):
        """Flash (mbed) device
        :param build:  Build -object or string (file-path)
        :param target_id: target_id
        :param platform_name: platform_name, to flash multiple devices of same type
        :param device_mapping_table: individual devices mapping table
        :param method: method for flashing i.e. simple, pyocd or edbg
        """

        k64f_target_id_length = 48

        if target_id is None and platform_name is None:
            raise SyntaxError("target_id or target_name is required")

        if not isfile(build):
            self.logger.error("Given file does not exist")
            return EXIT_CODE_FILE_DOES_NOT_EXIST
        if isinstance(target_id, list):
            return self.flash_multiple(build=build,
                                       platform_name=platform_name,
                                       method=method,
                                       target_ids_or_prefix=target_id,
                                       no_reset=no_reset)
        else:
            if target_id.lower() == 'all':
                return self.flash_multiple(build=build,
                                           platform_name=platform_name,
                                           method=method,
                                           no_reset=no_reset)
            elif len(target_id) < k64f_target_id_length and device_mapping_table is None:
                return self.flash_multiple(build=build,
                                           platform_name=platform_name,
                                           method=method,
                                           target_ids_or_prefix=target_id,
                                           no_reset=no_reset)

        device_mapping_table = self._refine__device_mapping_table(device_mapping_table)

        try:
            if target_id:
                target_mbed = self.__find_by_target_id(target_id, device_mapping_table)
            else:
                target_mbed = self.__find_by_platform_name(platform_name,
                                                           device_mapping_table)
        except KeyError as err:
            self.logger.error(err)
            return EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE

        platform_name = self._get_platform_name(platform_name, target_mbed)

        self.logger.debug("Flashing: %s", target_mbed["target_id"])

        flasher = self.__get_flasher(platform_name)
        try:
            retcode = flasher.flash(source=build,
                                    target=target_mbed,
                                    method=method,
                                    no_reset=no_reset)
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

    def _refine__device_mapping_table(self, device_mapping_table):
        """
        get device mapping table if it's None.
        refine device_mapping table to be list
        :param device_mapping_table: individual devices mapping table
        """
        if device_mapping_table:
            if isinstance(device_mapping_table, dict):
                device_mapping_table = [device_mapping_table]
            elif not isinstance(device_mapping_table, list):
                raise SystemError('device_mapping_table wasn\'t list or dictionary')
        else:
            device_mapping_table = self.get_available_device_mapping()

        self.logger.debug(device_mapping_table)

        return device_mapping_table

    def _get_platform_name(self, platform_name, target_mbed):
        """
        get supported platform name
        :param platform_name: None or list
        :param target_mbed: target mbed
        """
        if not platform_name:
            platform_name = target_mbed['platform_name']

        if platform_name not in self.supported_targets:
            raise NotImplementedError("Platform '%s' is not supported by mbed-flasher"
                                      % platform_name)

        return platform_name

    @staticmethod
    def _map_by_target_id(device_mapping_table, platform_name, target_ids):
        """
        Map available devices to required devices by target id
        :param device_mapping_table: available devices
        :param platform_name: platform
        :param target_ids: list of target ids
        :return: list of targets which matched the requirements
        """
        aux_device_mapping_table = []
        for tid in target_ids:
            for item in device_mapping_table:
                if platform_name:
                    if item['platform_name'] != platform_name:
                        # skipping boards that do not match with specified platform
                        continue

                if item['target_id'] == tid:
                    aux_device_mapping_table.append(item)

        return aux_device_mapping_table

    @staticmethod
    def _map_by_prefix(device_mapping_table, platform_name, prefix):
        """
        Map available devices to required devices by prefix
        :param device_mapping_table: available devices
        :param platform_name: platform
        :param prefix: prefix with to find
        :return: list of targets which matched the requirements
        """
        aux_device_mapping_table = []
        for item in device_mapping_table:
            if platform_name:
                if item['platform_name'] != platform_name:
                    # skipping boards that do not match
                    # with specified platform
                    continue

            if item['target_id'].startswith(str(prefix)):
                aux_device_mapping_table.append(item)

        return aux_device_mapping_table

    @staticmethod
    def _map_by_platform(device_mapping_table, platform_name):
        """
        Map available devices to required devices by platform
        :param device_mapping_table: available devices
        :param platform_name: platform
        :return: list of targets which matched the requirements
        """
        aux_device_mapping_table = []
        for item in device_mapping_table:
            if platform_name:
                if item['platform_name'] == platform_name:
                    aux_device_mapping_table.append(item)

        return aux_device_mapping_table
