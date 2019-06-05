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

from os import path
import logging

from appdirs import user_data_dir
from pyocd.core.helpers import ConnectHelper
from pyocd.flash.loader import FileProgrammer, FlashEraser

from mbed_flasher.common import FlashError, EraseError
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_USER_ERROR
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_IMPLEMENTATION_MISSING
from mbed_flasher.return_codes import EXIT_CODE_UNHANDLED_EXCEPTION


class PyOCDMap(object):
    """
    Provide list of boards and assisting methods to support PyOCD usage.
    """
    SUPPORTED_PLATFORMS = {
        "DISCO_L475VG_IOT01A": {
            "platform": "stm32l475xg",
            "pack": None
        },
        "NUCLEO_L073RZ": {
            "platform": "stm32l073rz",
            "pack": "Keil.STM32L0xx_DFP.2.0.1.pack"
        }
    }

    @staticmethod
    def is_supported(platform):
        """
        Check if platform is supported by PyOCD
        :param platform: mbedls board platform
        :return: True if supported, otherwise False
        """
        return platform in PyOCDMap.SUPPORTED_PLATFORMS.keys()

    @staticmethod
    def platform(platform):
        """
        Map mbedls target name to pyOCD target.
        :param platform: mbedls board platform
        :return: corresponding pyOCD platform or KeyError if doesn't exist
        """
        return PyOCDMap.SUPPORTED_PLATFORMS[platform].get("platform")

    @staticmethod
    def _get_pack_path():
        """
        Return platform specific pack installation dir.
        Linux: /home/<user>/.local/share/mbed-flasher/pyocd-packs
        MacOSX: /Users/<user>/Library/Application Support/mbed-flasher/pyocd-packs
        Windows 7: C:\\Users\\<user>\\AppData\\Local\\mbed-flasher\\mbed-flasher\\pyocd-packs
        :return: path to packs folder
        """
        return path.join(user_data_dir('mbed-flasher'), 'pyocd-packs')

    @staticmethod
    def pack(platform):
        """
        Acquire path to pack file for specific platform
        :param platform: mbedls board platform
        :return: Path for pack file, None if not needed
        raises FlashError if pack file is needed but it doesn't exist
        """
        pack_file = PyOCDMap.SUPPORTED_PLATFORMS[platform].get("pack")
        if pack_file is None:
            return None

        pack_path = path.join(PyOCDMap._get_pack_path(), pack_file)
        if path.isfile(pack_path):
            return pack_path

        raise FlashError(message="Pack file does not exist for the platform: {}".format(platform),
                         return_code=EXIT_CODE_IMPLEMENTATION_MISSING)


class FlasherPyOCD(object):
    """
    Flash and erase board using PyOCD.
    """
    name = "pyOCD"

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger('mbed-flasher')

    @staticmethod
    def can_flash(target, source):
        """
        Function deciding whether the target should be flashed with pyOCD
        :param target: mbedls given target dictionary
        :param source: application to be flashed
        :return: True if target can be flashed with FlasherPyOCD otherwise False
        """
        if not source.endswith('.hex'):
            return False

        return PyOCDMap.is_supported(target["platform_name"])

    @staticmethod
    def can_erase(target):
        """
        Function deciding whether the target should be erased with pyOCD
        :param target: mbedls given target dictionary
        :return: True if target can be erased with FlasherPyOCD otherwise False
        """
        return PyOCDMap.is_supported(target["platform_name"])

    # pylint: disable=unused-argument
    def flash(self, source, target, method, no_reset):
        """Flash target using pyOCD
        :param source: binary to be flashed
        :param target: mbedls given target dictionary
        :param method: method to use when flashing
        :param no_reset: do not reset flashed board at all
        :return: 0 if success otherwise raises
        """

        self.logger.debug('Flashing with pyOCD')
        session = self._get_session(target, FlashError)
        try:
            with session:
                file_programmer = FileProgrammer(session, chip_erase="sector")
                file_programmer.program(source)

                if not no_reset:
                    self.logger.debug('Resetting with pyOCD')
                    session.target.reset()
        except ValueError as error:
            msg = "PyOCD flash failed due to invalid argument: {}".format(error)
            self.logger.error(msg)
            raise FlashError(message=msg, return_code=EXIT_CODE_DAPLINK_USER_ERROR)
        except Exception as error:
            msg = "PyOCD flash failed unexpectedly: {}".format(error)
            self.logger.error(msg)
            raise FlashError(message=msg, return_code=EXIT_CODE_UNHANDLED_EXCEPTION)

        return EXIT_CODE_SUCCESS

    def erase(self, target, no_reset):
        """Erase target using pyOCD
        :param target: mbedls given target dictionary
        :param no_reset: do not reset flashed board at all
        :return: 0 if success otherwise raises
        """
        self.logger.debug('Erasing with pyOCD')
        session = self._get_session(target, EraseError)
        try:
            with session:
                flash_eraser = FlashEraser(session, FlashEraser.Mode.CHIP)
                flash_eraser.erase()

                if not no_reset:
                    self.logger.debug('Resetting with pyOCD')
                    session.target.reset()
        except Exception as error:
            msg = "PyOCD erase failed unexpectedly: {}".format(error)
            self.logger.error(msg)
            raise EraseError(message=msg, return_code=EXIT_CODE_UNHANDLED_EXCEPTION)

        return EXIT_CODE_SUCCESS

    def _get_session(self, target, error_class):
        """
        Internal method for acquiring pyOCD session
        :param target: mbedls given target dictionary
        :param error_class: error to be risen on failure
        :return: Session
        """
        session = ConnectHelper.session_with_chosen_probe(
            unique_id=target['target_id_usb_id'],
            blocking=False,
            target_override=PyOCDMap.platform(target['platform_name']),
            halt_on_connect=True,
            resume_on_disconnect=False,
            hide_programming_progress=True,
            pack=PyOCDMap.pack(target['platform_name']))

        if session is None:
            msg = "Did not find pyOCD target: {}".format(target["target_id_usb_id"])
            self.logger.error(msg)
            raise error_class(
                message=msg,
                return_code=EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

        return session
