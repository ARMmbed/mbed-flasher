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

from enum import Enum
import logging
import traceback

from intelhex import IntelHexError
from pyocd.core.helpers import ConnectHelper
from pyocd.flash.file_programmer import FileProgrammer
from pyocd.flash.eraser import FlashEraser

from mbed_flasher.common import FlashError, EraseError
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_USER_ERROR
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_UNHANDLED_EXCEPTION


class ConnectMode(Enum):
    """
    Options for pyocd session connect_mode parameter.
    """
    HALT = "halt"
    PRE_RESET = "pre-reset"
    UNDER_RESET = "under-reset"
    ATTACH = "attach"


class FlasherPyOCD(object):
    """
    Flash and erase board using PyOCD.
    """
    name = "pyOCD"

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger('mbed-flasher')

    # pylint: disable=too-many-arguments
    def flash(self, source, target, no_reset, platform, pack, connect_mode):
        """Flash target using pyOCD
        :param source: binary to be flashed
        :param target: mbedls given target dictionary
        :param no_reset: do not reset flashed board at all
        :param platform: target platform
        :param pack: path of pack file
        :param connect_mode: mode used when connecting
        :return: 0 if success otherwise raises
        """
        self.logger.debug('Flashing with pyOCD')
        try:
            session = self._get_session(target, platform, pack, connect_mode, FlashError)
            with session:
                file_programmer = FileProgrammer(session, chip_erase="sector")
                file_programmer.program(source)

                if not no_reset:
                    self.logger.debug('Resetting with pyOCD')
                    session.target.reset()
        except FlashError:
            raise
        except IntelHexError as error:
            msg = "PyOCD flash failed due to invalid hex file: {}".format(error)
            self.logger.error(msg)
            raise FlashError(message=msg, return_code=EXIT_CODE_PYOCD_USER_ERROR)
        except ValueError as error:
            msg = "PyOCD flash failed due to invalid argument: {}".format(error)
            self.logger.error(msg)
            raise FlashError(message=msg, return_code=EXIT_CODE_PYOCD_USER_ERROR)
        except Exception as error:
            msg = "PyOCD flash failed unexpectedly: {}".format(error)
            self.logger.error(msg)
            self.logger.error(traceback.format_exc())
            raise FlashError(message=msg, return_code=EXIT_CODE_PYOCD_UNHANDLED_EXCEPTION)

        return EXIT_CODE_SUCCESS

    def erase(self, target, no_reset, platform, pack, connect_mode):
        """Erase target using pyOCD
        :param target: mbedls given target dictionary
        :param no_reset: do not reset flashed board at all
        :param platform: target platform
        :param pack: path of pack file
        :param connect_mode: mode used when connecting
        :return: 0 if success otherwise raises
        """
        self.logger.debug('Erasing with pyOCD')
        try:
            session = self._get_session(target, platform, pack, connect_mode, EraseError)
            with session:
                flash_eraser = FlashEraser(session, FlashEraser.Mode.CHIP)
                flash_eraser.erase()

                if not no_reset:
                    self.logger.debug('Resetting with pyOCD')
                    session.target.reset()
        except EraseError:
            raise
        except Exception as error:
            msg = "PyOCD erase failed unexpectedly: {}".format(error)
            self.logger.error(msg)
            self.logger.error(traceback.format_exc())
            raise EraseError(message=msg, return_code=EXIT_CODE_PYOCD_UNHANDLED_EXCEPTION)

        return EXIT_CODE_SUCCESS

    def _get_session(self, target, platform, pack, connect_mode, error_class):
        """
        Internal method for acquiring pyOCD session
        :param target: mbedls given target dictionary
        :param platform: target platform
        :param pack: path of pack file
        :param connect_mode: mode used when connecting, one of
        halt, pre-reset, under-reset, attach
        :param error_class: error to be risen on failure
        :return: Session on success, raises AssertionError or error_class on failure
        """
        assert isinstance(platform, str)
        assert isinstance(pack, str) or pack is None
        assert isinstance(connect_mode, str)

        session = ConnectHelper.session_with_chosen_probe(
            unique_id=target['target_id_usb_id'],
            blocking=False,
            target_override=platform,
            connect_mode=connect_mode,
            resume_on_disconnect=False,
            hide_programming_progress=True,
            pack=pack)

        if session is None:
            msg = "Did not find pyOCD target: {}".format(target["target_id_usb_id"])
            self.logger.error(msg)
            raise error_class(
                message=msg,
                return_code=EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

        return session
