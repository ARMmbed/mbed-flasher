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

# python 3 compatibility
# pylint: disable=superfluous-parens

import logging

from serial.serialutil import SerialException
from mbed_flasher.flashers.enhancedserial import EnhancedSerial
from mbed_flasher.common import ResetError
from mbed_flasher.mbed_common import MbedCommon
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_PORT_OPEN_FAILED
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_RESET_FAILED
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING


class Reset(object):
    """ Reset object, which manages reset for given devices
    """
    _flashers = []

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger("mbed-flasher")

    def reset_board(self, serial_port):
        """
        :param serial_port: serial port
        :return: return exit code if failed
        """
        try:
            port = EnhancedSerial(serial_port)
        except SerialException as err:
            self.logger.info("reset could not be sent")
            self.logger.error(err)
            # SerialException.message is type "string"
            # pylint: disable=no-member
            if err.message.find('could not open port') != -1:
                self.logger.error(
                    "Reset could not be given. Close your Serial connection to device.")

            raise ResetError(message="Reset failed",
                             return_code=EXIT_CODE_SERIAL_PORT_OPEN_FAILED)

        port.baudrate = 115200
        port.timeout = 1
        port.xonxoff = False
        port.rtscts = False
        port.flushInput()
        port.flushOutput()

        if port:
            self.logger.info("sendBreak to device to reboot")
            result = port.safe_send_break()
            if result:
                self.logger.info("reset completed")
            else:
                raise ResetError(message="Reset failed",
                                 return_code=EXIT_CODE_SERIAL_RESET_FAILED)

        port.close()

    def reset(self, target_id=None, method=None):
        """Reset (mbed) device
        :param target_id: target_id
        :param method: method for reset i.e. simple
        """
        if target_id is None:
            raise ResetError(message="target_id is missing",
                             return_code=EXIT_CODE_TARGET_ID_MISSING)

        self.logger.info("Starting reset for target_id %s", target_id)
        self.logger.info("Method for reset: %s", method)
        target_mbed = MbedCommon.refresh_target(target_id)
        if target_mbed is None:
            raise ResetError(message="Did not find target: {}".format(target_id),
                             return_code=EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

        if method == 'simple' and 'serial_port' in target_mbed:
            self.reset_board(target_mbed['serial_port'])
        else:
            raise ResetError(message="Selected method {} not supported".format(method),
                             return_code=EXIT_CODE_MISUSE_CMD)

        return EXIT_CODE_SUCCESS
