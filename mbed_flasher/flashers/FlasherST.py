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

from distutils import spawn
try:
    import queue
except ImportError:
    import Queue as queue
import sys

import mbed_lstools

from mbed_flasher.common import FlashError
from mbed_flasher.flashers.FlasherBase import FlasherBase
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_FLASH_FAILED


class FlasherSTLink(FlasherBase):
    """
    Class FlasherJLink

    Target on flashing JLink boards with JLinkExe.
    """
    name = "stlink"
    executable = "ST-LINK_CLI.exe" if sys.platform.startswith("win") else "ST-LINK_CLI"
    # supported_targets = None
    # workaround for IOTMORF-2205
    supported_targets = ["NUCLEO_F401RE",
                         "NUCLEO_F411RE",
                         "NUCLEO_F429ZI",
                         "NUCLEO_L476RG",
                         "NUCLEO_F767ZI",
                         "UBLOX_EVK_ODIN_W2"]

    def __init__(self, logger=None):
        FlasherBase.__init__(self, logger)

    @staticmethod
    def get_supported_targets():
        """
        :return: supported JLink types
        """
        if not FlasherSTLink.supported_targets:
            mbeds = mbed_lstools.create()
            # @todo this is workaround until mbed-ls provide public api
            db_items = list(mbeds.plat_db.items(device_type=FlasherSTLink.name))
            FlasherSTLink.supported_targets = sorted([i[1]["platform_name"] for i in db_items])

        return FlasherSTLink.supported_targets

    @staticmethod
    def get_available_devices():
        """
        :return: list of available devices
        """
        mbeds = mbed_lstools.create()
        # device_type introduced in mbedls version 1.4.0
        return mbeds.list_mbeds(filter_function=FlasherSTLink.can_flash)

    @staticmethod
    def can_flash(target):
        """
        Check if target should be flashed by using JLinkExe.
        :param target: target board
        :return: boolean
        """
        try:
            return target.get("device_type") == FlasherSTLink.name or \
                target['platform_name'] in FlasherSTLink.supported_targets # IOTMORF-2205
        except KeyError:
            return False

    @staticmethod
    def is_executable_installed():
        """
        Check if JLinkExe can be found from path.
        :return: boolean
        """
        return spawn.find_executable(FlasherSTLink.executable) is not None

    def flash(self, source, target, method, no_reset):
        """flash device
        :param source: binary to be flashed
        :param target: target to be flashed
        :param method: method to use when flashing
        :param no_reset: do not reset flashed board at all
        :return: 0 when flashing success
        """
        try:
            args = [
                FlasherSTLink.executable,
                "-c", "SN=" + target['target_id_usb_id'],  # chip to be flash
                "-P", source, "0x08000000",  # Loads file into device memory
                "-V"  # Verifies that the programming operation was performed successfully.
            ]
        except KeyError:
            raise FlashError(message="Invalid target", return_code=EXIT_CODE_FLASH_FAILED)

        try:
            self.logger.info("Flashing {} with command {}".format(target["target_id"], args))
            returncode, output = self._start_and_wait_flash(args, FlasherSTLink.executable)
        except queue.Empty:
            raise FlashError(message="No returncode from ST-LINK_CLI",
                             return_code=EXIT_CODE_FLASH_FAILED)

        if returncode != 0:
            self.logger.error("Flash of {} failed, with returncode {}"
                              .format(target["target_id"], returncode))
            self.logger.debug(output if output else "")
            msg = "Flash failed with STLink return code: {}".format(returncode)
            raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)

        self.logger.info("Flash of {} succeeded".format(target["target_id"]))
        self.logger.debug(output)
        return EXIT_CODE_SUCCESS
