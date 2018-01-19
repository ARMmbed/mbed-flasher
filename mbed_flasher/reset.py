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

from serial.serialutil import SerialException
from mbed_flasher.flashers.enhancedserial import EnhancedSerial
from mbed_flasher.common import Logger
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_MISSING
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_RESET_FAILED
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_PORT_OPEN_FAILED
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_RESET_FAILED
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING


class Reset(object):
    """ Reset object, which manages reset for given devices
    """
    _flashers = []
    def __init__(self):
        logger = Logger('mbed-flasher')
        self.logger = logger.logger
        self._flashers = self.__get_flashers()

    def get_available_device_mapping(self):
        """
        :return: available devices
        """
        available_devices = []
        for flasher in self._flashers:
            devices = flasher.get_available_devices()
            available_devices.extend(devices)
        return available_devices

    @staticmethod
    def __get_flashers():
        """
        :return: available flashers
        """
        from mbed_flasher.flashers import AvailableFlashers
        return AvailableFlashers

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
                print('Reset could not be given. Close your Serial connection to device.')
            return EXIT_CODE_SERIAL_PORT_OPEN_FAILED
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
                self.logger.error("reset failed")
                return EXIT_CODE_SERIAL_RESET_FAILED
        port.close()

    def reset(self, target_id=None, method=None):
        """Reset (mbed) device
        :param target_id: target_id
        :param method: method for reset i.e. simple, pyocd or edbg
        """
        self.logger.info("Starting reset for target_id %s", target_id)
        self.logger.info("Method for reset: %s", method)
        available_devices = self.get_available_device_mapping()

        if target_id is None:
            return EXIT_CODE_TARGET_ID_MISSING

        targets_to_reset = self.prepare_target_to_reset(target_id, available_devices)

        if len(targets_to_reset) <= 0:
            print("Could not map given target_id(s) to available devices")
            return EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE

        for item in targets_to_reset:
            if method == 'simple' and 'serial_port' in item:
                self.reset_board(item['serial_port'])
            elif method == 'pyocd':
                return self.try_pyocd_reset(item)
            elif method == 'edbg':
                print("Not supported yet")
            else:
                print("Selected method %s not supported" % method)
                return EXIT_CODE_MISUSE_CMD

        return EXIT_CODE_SUCCESS

    @staticmethod
    def prepare_target_to_reset(target_id, available_devices):
        """
        prepare target to reset
        """
        targets_to_reset = []

        if isinstance(target_id, list):
            for target in target_id:
                for device in available_devices:
                    if target == device['target_id'] and \
                                    device not in targets_to_reset:
                        targets_to_reset.append(device)
        else:
            if target_id == 'all':
                targets_to_reset = available_devices
            elif len(target_id) <= 48:
                for device in available_devices:
                    if (target_id == device['target_id'] or
                            device['target_id'].startswith(target_id)) and \
                                    device not in targets_to_reset:
                        targets_to_reset.append(device)
        return targets_to_reset

    def try_pyocd_reset(self, item):
        """
        try pyOCD reset
        """
        try:
            from pyOCD.board import MbedBoard
        except ImportError:
            print('pyOCD missing, install it\n')
            return EXIT_CODE_PYOCD_MISSING

        try:
            with MbedBoard.chooseBoard(board_id=item["target_id"]) \
                    as board:
                self.logger.info("resetting device")
                ocd_target = board.target
                ocd_target.reset()
                self.logger.info("reset completed")
            return EXIT_CODE_SUCCESS
        except AttributeError as err:
            self.logger.error("reset failed: %s.", err)
            self.logger.error("tid=%s", item["target_id"])
            return EXIT_CODE_PYOCD_RESET_FAILED
