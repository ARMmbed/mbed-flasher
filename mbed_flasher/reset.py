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
Veli-Matti Lahtela <veli-matti.lahtela@arm.com>
"""

import logging
import types
from flashers.enhancedserial import EnhancedSerial
from serial.serialutil import SerialException

EXIT_CODE_COULD_NOT_MAP_TO_DEVICE = 3
EXIT_CODE_PYOCD_MISSING = 5
EXIT_CODE_PYOCD_RESET_FAILED = 7
EXIT_CODE_NONSUPPORTED_METHOD_FOR_RESET = 9
EXIT_CODE_RESET_FAILED_PORT_OPEN = 11
EXIT_CODE_SERIAL_RESET_FAILED = 13


class Reset(object):
    """ Reset object, which manages reset for given devices
    """
    FLASHERS = []
    def __init__(self):
        self.logger = logging.getLogger('mbed-flasher')
        self.FLASHERS = self.__get_flashers()

    def get_available_device_mapping(self):
        available_devices = []
        for Flasher in self.FLASHERS:
            devices = Flasher.get_available_devices()
            available_devices.extend(devices)
        return available_devices

    @staticmethod
    def __get_flashers():
        from flashers import AvailableFlashers
        return AvailableFlashers
        
    def reset_board(self, serial_port):
        try:
            port = EnhancedSerial(serial_port)
        except SerialException as e:
            self.logger.info("reset could not be sent")
            self.logger.error(e)
            if e.message.find('could not open port') != -1:
                print 'Reset could not be given. Close your Serial connection to device.'
            return EXIT_CODE_RESET_FAILED_PORT_OPEN
        port.baudrate = 115200
        port.timeout = 1
        port.xonxoff = False
        port.rtscts = False
        port.flushInput()
        port.flushOutput()

        if port:
            self.logger.info("sendBreak to device to reboot")
            result = port.safe_sendBreak()
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
        self.logger.info("Starting reset for target_id %s" % target_id)
        self.logger.info("Method for reset: %s" % method)
        available_devices = self.get_available_device_mapping()
        targets_to_reset = []
        
        if isinstance(target_id, types.ListType):
            for target in target_id:
                for device in available_devices:
                    if target == device['target_id']:
                        if device not in targets_to_reset:
                            targets_to_reset.append(device)
        else:
            if target_id == 'all':
               targets_to_reset = available_devices
            elif len(target_id) <= 48:
                for device in available_devices:
                    if target_id == device['target_id'] or device['target_id'].startswith(target_id):
                        if device not in targets_to_reset:
                            targets_to_reset.append(device)
        
        if len(targets_to_reset) > 0:
            for item in targets_to_reset:
                if method == 'simple' and 'serial_port' in item:
                    self.reset_board(item['serial_port'])
                elif method == 'pyocd':
                    try:
                        from pyOCD.board import MbedBoard
                    except ImportError:
                        print 'pyOCD missing, install it\n'
                        return EXIT_CODE_PYOCD_MISSING
                    try:
                        with MbedBoard.chooseBoard(board_id=item["target_id"]) as board:
                            self.logger.info("resetting device")
                            ocd_target = board.target
                            ocd_target.reset()
                            self.logger.info("reset completed")
                    except AttributeError as e:
                        self.logger.error("reset failed: %s. tid=%s" % (e, item["target_id"]))
                        return EXIT_CODE_PYOCD_RESET_FAILED
                elif method == 'edbg':
                    print "Not supported yet"
                else:
                    print "Selected method %s not supported" % method
                    return EXIT_CODE_NONSUPPORTED_METHOD_FOR_RESET
        else:
            print "Could not map given target_id(s) to available devices"
            return EXIT_CODE_COULD_NOT_MAP_TO_DEVICE
        
        retcode = 0
        return retcode
