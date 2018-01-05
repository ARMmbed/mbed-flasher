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

from time import sleep, time
from os.path import join, isfile
from threading import Thread
import platform
from subprocess import PIPE, Popen
import six
from mbed_flasher.common import Logger, MountVerifier

EXIT_CODE_SUCCESS = 0
EXIT_CODE_RESET_FAILED_PORT_OPEN = 11
EXIT_CODE_SERIAL_RESET_FAILED = 13
EXIT_CODE_COULD_NOT_MAP_TO_DEVICE = 21
EXIT_CODE_PYOCD_MISSING = 23
EXIT_CODE_PYOCD_ERASE_FAILED = 27
EXIT_CODE_NONSUPPORTED_METHOD_FOR_ERASE = 29
EXIT_CODE_IMPLEMENTATION_MISSING = 31
EXIT_CODE_ERASE_FAILED_NOT_SUPPORTED = 33
EXIT_CODE_TARGET_ID_MISSING = 34
ERASE_REMOUNT_TIMEOUT = 10
ERASE_VERIFICATION_TIMEOUT = 30
ERASE_DAPLINK_SUPPORT_VERSION = 243


class Erase(object):
    """ Erase object, which manages erasing for given devices
    """

    def __init__(self):
        logger = Logger('mbed-flasher')
        self.logger = logger.logger
        self.flashers = self.__get_flashers()

    def get_available_device_mapping(self):
        """
        :return: list of available devices
        """
        available_devices = []
        for flasher in self.flashers:
            devices = flasher.get_available_devices()
            available_devices.extend(devices)
        return available_devices

    @staticmethod
    def __get_flashers():
        """
        :return: list of available flashers
        """
        from mbed_flasher.flashers import AvailableFlashers
        return AvailableFlashers

    def reset_board(self, serial_port):
        """
        :param serial_port: board serial port
        :return: return exit code based on if successfully reset a board
        """
        from mbed_flasher.flashers.enhancedserial import EnhancedSerial
        from serial.serialutil import SerialException
        try:
            port = EnhancedSerial(serial_port)
        except SerialException as err:
            self.logger.info("reset could not be sent")
            self.logger.error(err)
            # SerialException.message is type "string", it has 'find'
            #  pylint: disable=no-member
            if err.message.find('could not open port') != -1:
                print('Reset could not be given. Close your Serial connection to device.')
            return EXIT_CODE_RESET_FAILED_PORT_OPEN
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
        return EXIT_CODE_SUCCESS

    def wait_to_disappear(self, mount_point):
        """
        :param mount_point: mount_point to watch disappear
        """
        start_time = time()
        while True:
            sleep(0.1)
            if platform.system() == 'Windows':
                proc = Popen(["dir", mount_point], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
            else:
                proc = Popen(["ls", mount_point], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            err = proc.stderr.read()
            proc.communicate()

            if err:
                self.logger.debug("Remount due to erase")
                break

            if time() - start_time > ERASE_REMOUNT_TIMEOUT:
                self.logger.debug("Didn't notice device to disappear for remount")
                break

    def runner(self, mount_point, filename):
        """
        :param mount_point: mount_point to check for
        :param filename: erase command filename
        """
        start_time = time()
        while True:
            sleep(0.3)
            if platform.system() == 'Windows':
                proc = Popen(["dir", mount_point], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
            else:
                proc = Popen(["ls", mount_point], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            out = proc.stdout.read()
            proc.communicate()
            if out.find(b'.HTM') != -1:
                if out.find(filename.encode()) == -1:
                    break

            if time() - start_time > ERASE_VERIFICATION_TIMEOUT:
                self.logger.debug("erase check timed out for %s", mount_point)
                break

    # pylint: disable=too-many-return-statements, too-many-branches
    def erase_board(self, target, no_reset):
        """
        :param target: target to which perform the erase
        :param no_reset: erase with/without reset
        :return: exit code
        """
        automation_activated = False
        daplink_version = 0
        if not isfile(join(target["mount_point"], 'DETAILS.TXT')):
            self.logger.error("No DETAILS.TXT found")
            return EXIT_CODE_IMPLEMENTATION_MISSING

        self.logger.error(join(target["mount_point"], 'DETAILS.TXT'))
        with open(join(target["mount_point"], 'DETAILS.TXT'), 'rb') as new_file:
            for line in new_file:
                if line.find(b"Automation allowed: 1") != -1:
                    automation_activated = True
                if line.find(b"Interface Version") != -1:
                    try:
                        if six.PY2:
                            daplink_version = int(line.split(' ')[-1])
                        else:
                            daplink_version = int(line.decode('utf-8').split(' ')[-1])
                    except (IndexError, ValueError):
                        self.logger.error("Failed to parse DAPLINK version from DETAILS.TXT")
                        return EXIT_CODE_IMPLEMENTATION_MISSING

        if not automation_activated:
            self.logger.error("Selected device does not support erasing through DAPLINK")
            return EXIT_CODE_IMPLEMENTATION_MISSING

        if daplink_version < ERASE_DAPLINK_SUPPORT_VERSION:
            msg = "Selected device has Daplink version %s," \
                  "erasing supported from version %s onwards"
            self.logger.error(msg, daplink_version, ERASE_DAPLINK_SUPPORT_VERSION)
            return EXIT_CODE_IMPLEMENTATION_MISSING

        with open(join(target["mount_point"], 'ERASE.ACT'), 'wb'):
            pass

        auto_thread = Thread(target=self.wait_to_disappear,
                             args=(target["mount_point"],))
        auto_thread.start()
        while auto_thread.is_alive():
            auto_thread.join(0.5)

        new_target = MountVerifier(self.logger).check_points_unchanged(target)
        if isinstance(new_target, int):
            return new_target

        auto_thread = Thread(target=self.runner,
                             args=(new_target["mount_point"], 'ERASE.ACT'))
        auto_thread.start()
        while auto_thread.is_alive():
            auto_thread.join(0.5)

        if not no_reset:
            success = self.reset_board(target["serial_port"])
            if success != 0:
                self.logger.error("erase failed")
                return success

        self.logger.info("erase completed")
        return EXIT_CODE_SUCCESS

    def erase(self, target_id=None, no_reset=None, method=None):
        """
        Erase (mbed) device
        :param target_id: target_id
        :param method: method for erase i.e. simple, pyocd or edbg
        """
        self.logger.info("Starting erase for given target_id %s", target_id)
        self.logger.info("method used for reset: %s", method)
        available_devices = self.get_available_device_mapping()

        if target_id is None:
            return EXIT_CODE_TARGET_ID_MISSING

        targets_to_erase = self.prepare_target_to_erase(target_id, available_devices)

        if len(targets_to_erase) <= 0:
            print("Could not map given target_id(s) to available devices")
            return EXIT_CODE_COULD_NOT_MAP_TO_DEVICE

        for item in targets_to_erase:
            if item['platform_name'] != 'K64F':
                print("Only mbed devices supported")
                return EXIT_CODE_SUCCESS

            if method == 'simple' and 'mount_point' in item and 'serial_port' in item:
                self.erase_board(target=item, no_reset=no_reset)
            elif method == 'pyocd':
                try:
                    from pyOCD.board import MbedBoard
                    from pyOCD.pyDAPAccess import DAPAccessIntf
                except ImportError:
                    print('pyOCD missing, install it\n')
                    return EXIT_CODE_PYOCD_MISSING
                board = MbedBoard.chooseBoard(board_id=item["target_id"])
                self.logger.info("erasing device")
                ocd_target = board.target
                flash = ocd_target.flash
                try:
                    flash.eraseAll()
                    if not no_reset:
                        ocd_target.reset()
                except DAPAccessIntf.TransferFaultError:
                    pass
                self.logger.info("erase completed")
            elif method == 'edbg':
                print("Not supported yet")
            else:
                print("Selected method %s not supported" % method)
                return EXIT_CODE_NONSUPPORTED_METHOD_FOR_ERASE

        return EXIT_CODE_SUCCESS

    @staticmethod
    def prepare_target_to_erase(target_id, available_devices):
        """
        prepare target to erase
        """
        targets_to_erase = []
        if isinstance(target_id, list):
            for target in target_id:
                for device in available_devices:
                    if target == device['target_id']:
                        if device not in targets_to_erase:
                            targets_to_erase.append(device)
        else:
            if target_id == 'all':
                targets_to_erase = available_devices
            elif len(target_id) <= 48:
                for device in available_devices:
                    if target_id == device['target_id'] \
                            or device['target_id'].startswith(target_id):
                        if device not in targets_to_erase:
                            targets_to_erase.append(device)

        return targets_to_erase
