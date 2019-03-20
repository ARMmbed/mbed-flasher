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

from pyocd.core.helpers import ConnectHelper
from pyocd.flash.loader import FileProgrammer, FlashEraser

from mbed_flasher.common import FlashError, EraseError
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_USER_ERROR
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_IMPLEMENTATION_MISSING


class PyOCDMap(object):
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
        return platform in PyOCDMap.SUPPORTED_PLATFORMS.keys()

    @staticmethod
    def platform(platform):
        return PyOCDMap.SUPPORTED_PLATFORMS[platform].get("platform")

    @staticmethod
    def pack(platform):
        pack_file = PyOCDMap.SUPPORTED_PLATFORMS[platform].get("pack")
        if pack_file is None:
            return None

        pack_path = path.join(path.dirname(__file__), '..', '..', 'pyocd_packs', pack_file)
        if path.isfile(pack_path):
            return pack_path

        raise FlashError(message="Pack file does not exist for the platform: {}".format(platform),
                         return_code=EXIT_CODE_IMPLEMENTATION_MISSING)


class FlasherPyOCD(object):
    """
    Flash board using PyOCD.
    """
    name = "pyOCD"

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger('mbed-flasher')

    @staticmethod
    def can_flash(target, source):
        if not source.endswith('.hex'):
            return False

        return PyOCDMap.is_supported(target["platform_name"])

    @staticmethod
    def can_erase(target):
        return PyOCDMap.is_supported(target["platform_name"])

    # pylint: disable=unused-argument
    def flash(self, source, target, method, no_reset):
        """Flash target using pyOCD
        :param source: binary to be flashed
        :param target: target to be flashed
        :param method: method to use when flashing
        :param no_reset: do not reset flashed board at all
        """

        self.logger.debug('Flashing with pyOCD')
        session = self._get_session(target, FlashError)
        try:
            with session:
                FileProgrammer(session, chip_erase=False).program(source)

                if not no_reset:
                    session.target.reset()
        except ArgumentError as error:
            msg = "PyOCD flash failed: {}".format(error)
            self.logger.error(msg)
            raise FlashError(message=msg, return_code=EXIT_CODE_DAPLINK_USER_ERROR)

        return EXIT_CODE_SUCCESS

    def erase(self, target, no_reset):
        """Erase target using pyOCD
        :param target: target to be erased
        :param no_reset: do not reset flashed board at all
        """
        self.logger.debug('Erasing with pyOCD')
        session = self._get_session(target, EraseError)
        with session:
            FlashEraser(session, FlashEraser.Mode.CHIP).erase()

            if not no_reset:
                session.target.reset()

        return EXIT_CODE_SUCCESS

    def _get_session(self, target, error_class):
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
