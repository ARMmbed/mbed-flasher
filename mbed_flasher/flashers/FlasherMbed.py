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

import logging
from os.path import join, abspath, isfile
import os
import platform
from time import sleep
import hashlib
from serial.serialutil import SerialException
import six

import mbed_lstools

from mbed_flasher.common import retry, FlashError
from mbed_flasher.daplink_errors import DAPLINK_ERRORS
from mbed_flasher.flashers.enhancedserial import EnhancedSerial
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_FLASH_FAILED
from mbed_flasher.return_codes import EXIT_CODE_RESET_FAIL
from mbed_flasher.return_codes import EXIT_CODE_FILE_COULD_NOT_BE_READ
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_NOT_INSTALLED
from mbed_flasher.return_codes import EXIT_CODE_EGDB_NOT_SUPPORTED
from mbed_flasher.return_codes import EXIT_CODE_OS_ERROR
from mbed_flasher.return_codes import EXIT_CODE_FILE_STILL_PRESENT
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_TRANSIENT_ERROR
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_SOFTWARE_ERROR


class FlasherMbed(object):
    """
    Implementation class of mbed-flasher flash operation
    """
    name = "mbed"
    supported_targets = None
    REFRESH_TARGET_RETRIES = 100
    REFRESH_TARGET_SLEEP = 1
    CHECK_BINARY_DISAPPEAR_RETRIES = 60
    CHECK_BINARY_DISAPPEAR_SLEEP = 1

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger('mbed-flasher')

    @staticmethod
    def get_supported_targets():
        """
        Load target mapping information
        """
        if not FlasherMbed.supported_targets:
            mbeds = mbed_lstools.create()

            # this should works for >=v1.3.0
            # @todo this is workaround until mbed-ls provide public
            #       API to get list of supported platform names
            FlasherMbed.supported_targets = sorted(set(name for id, name in mbeds.plat_db.items()))

        return FlasherMbed.supported_targets

    @staticmethod
    def get_available_devices():
        """
        Get available devices
        """
        mbeds = mbed_lstools.create()
        return mbeds.list_mbeds()

    # pylint: disable=unused-argument
    @staticmethod
    def can_flash(target):
        """
        Check if target should be flashed by drag and drop method.
        Currently there is no reason not to try it.
        :param target: target board
        :return: True
        """
        return True

    @staticmethod
    def refresh_target_once(target_id):
        """
        Refresh target once with help of mbedls.
        :param target_id: target_id to be searched for
        :return: list of targets
        """
        mbedls = mbed_lstools.create()
        return mbedls.list_mbeds(filter_function=lambda m: m["target_id"] == target_id)

    @staticmethod
    def refresh_target(target_id):
        """
        Refresh target with help of mbedls.
        :param target_id: target_id to be searched for
        :return: target or None
        """
        mbedls = mbed_lstools.create()

        for _ in range(FlasherMbed.REFRESH_TARGET_RETRIES):
            mbeds = mbedls.list_mbeds(filter_function=lambda m: m["target_id"] == target_id)
            if mbeds:
                return mbeds[0]

            sleep(FlasherMbed.REFRESH_TARGET_SLEEP)

        return None

    @staticmethod
    def _wait_for_binary_disappear(target, source):
        """
        Wait for flashed binary to disappear from the mount point.
        :param target: target object
        :param source: binary name
        :return: target object
        """
        for _ in range(FlasherMbed.CHECK_BINARY_DISAPPEAR_RETRIES):
            try:
                target = FlasherMbed.refresh_target_once(target["target_id"])[0]
            except IndexError:
                # This is entered when mbedls fails to find the board,
                # most likely due to remount in progress.
                sleep(FlasherMbed.CHECK_BINARY_DISAPPEAR_SLEEP)
                continue

            if not isfile(FlasherMbed._get_binary_destination(target["mount_point"], source)):
                # Flashed file is no more found from the mount point,
                # ready to progress further.
                # Even though the mount point is accessible it does not seem
                # to guarantee that files in it are.
                # Continue looping until any .htm file is found.
                try:
                    for file_name in os.listdir(target["mount_point"]):
                        if file_name.lower().endswith("htm"):
                            return target
                # Windows might raise WinError 21 when opening mount point too quickly.
                except OSError:
                    pass

            sleep(FlasherMbed.CHECK_BINARY_DISAPPEAR_SLEEP)

        return target

    @staticmethod
    def _get_binary_destination(mount_point, source_file):
        """
        Form absolute path from mount point and file name
        :param mount_point: mount point
        :param source_file: source file name
        :return: absolute path
        """
        mount_point = os.path.abspath(mount_point)
        (_, tail) = os.path.split(os.path.abspath(source_file))
        return abspath(join(mount_point, tail))

    def reset_board(self, serial_port):
        """
        Reset board
        """
        try:
            port = EnhancedSerial(serial_port)
        except SerialException as err:
            self.logger.exception("reset could not be sent")
            # SerialException.message is type "string"
            # pylint: disable=no-member
            if err.message.find('could not open port') != -1:
                # python 3 compatibility
                # pylint: disable=superfluous-parens
                self.logger.error(
                    "Reset could not be given. Close your Serial connection to device.")

            raise FlashError(message="Reset failed", return_code=EXIT_CODE_RESET_FAIL)

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
                self.logger.info("reset failed")

        port.close()

    # pylint: disable=too-many-return-statements, duplicate-except
    def flash(self, source, target, method, no_reset):
        """copy file to the destination
        :param source: binary to be flashed
        :param target: target to be flashed
        :param method: method to use when flashing
        :param no_reset: do not reset flashed board at all
        """
        if not isinstance(source, six.string_types):
            return

        if method == 'pyocd':
            self.logger.debug("pyOCD selected for flashing")
            return self.try_pyocd_flash(source, target)

        if method == 'edbg':
            raise FlashError(message="edbg is not supported for Mbed devices",
                             return_code=EXIT_CODE_EGDB_NOT_SUPPORTED)

        return retry(
            logger=self.logger,
            func=self.try_drag_and_drop_flash,
            func_args=(source, target, no_reset),
            conditions=[EXIT_CODE_OS_ERROR,
                        EXIT_CODE_DAPLINK_TRANSIENT_ERROR,
                        EXIT_CODE_DAPLINK_SOFTWARE_ERROR])

    def try_pyocd_flash(self, source, target):
        """
        try pyOCD flash
        """
        try:
            from pyOCD.board import MbedBoard
        except ImportError:
            # python 3 compatibility
            # pylint: disable=superfluous-parens
            raise FlashError(message="PyOCD is missing",
                             return_code=EXIT_CODE_PYOCD_NOT_INSTALLED)

        try:
            with MbedBoard.chooseBoard(board_id=target["target_id"]) as board:
                ocd_target = board.target
                ocd_flash = board.flash
                self.logger.debug("resetting device: %s", target["target_id"])
                sleep(0.5)  # small sleep for lesser HW ie raspberry
                ocd_target.reset()
                self.logger.debug("flashing device: %s", target["target_id"])
                ocd_flash.flashBinary(source)
                self.logger.debug("resetting device: %s", target["target_id"])
                sleep(0.5)  # small sleep for lesser HW ie raspberry
                ocd_target.reset()
            return EXIT_CODE_SUCCESS
        except AttributeError as err:
            msg = "Flashing failed: {}. tid={}".format(err, target["target_id"])
            self.logger.error(msg)
            raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)

    def try_drag_and_drop_flash(self, source, target, no_reset):
        """
        Try to flash the target using drag and drop method.
        :param source: file to be flashed
        :param target: target board to be flashed
        :param no_reset: whether to reset the board after flash
        :return: 0 if success
        """

        target = FlasherMbed.refresh_target(target["target_id"])
        if not target:
            raise FlashError(message="Target ID is missing",
                             return_code=EXIT_CODE_TARGET_ID_MISSING)

        destination = FlasherMbed._get_binary_destination(target["mount_point"], source)

        try:
            if 'serial_port' in target and not no_reset:
                self.reset_board(target['serial_port'])
                sleep(0.1)

            self.copy_file(source, destination)
            self.logger.debug("copy finished")

            target = FlasherMbed._wait_for_binary_disappear(target, source)

            if not no_reset:
                self.reset_board(target['serial_port'])
                sleep(0.4)

            # verify flashing went as planned
            self.logger.debug("verifying flash")
            return self.verify_flash_success(
                target, FlasherMbed._get_binary_destination(target["mount_point"], source))
        # In python3 IOError is just an alias for OSError
        except (OSError, IOError) as err:
            msg = "Write failed due to OSError: {}".format(err)
            self.logger.error(msg)
            raise FlashError(message=msg, return_code=EXIT_CODE_OS_ERROR)

    def copy_file(self, source, destination):
        """
        copy file from os
        """
        self.logger.debug('read source file')
        with open(source, 'rb') as source_file:
            aux_source = source_file.read()

        if not aux_source:
            raise FlashError(message="File couldn't be read",
                             return_code=EXIT_CODE_FILE_COULD_NOT_BE_READ)

        self.logger.debug("SHA1: %s", hashlib.sha1(aux_source).hexdigest())

        if platform.system() == 'Windows':
            self.logger.debug("copying file: \"%s\" to \"%s\"",
                              source, destination)
            os.system("copy \"%s\" \"%s\"" % (os.path.abspath(source), destination))
        else:
            self.logger.debug("writing binary: %s (size=%i bytes)", destination, len(aux_source))
            new_file = self.get_file(destination)
            os.write(new_file, aux_source)
            os.close(new_file)

    @staticmethod
    def get_file(destination):
        """
        Get file
        """
        if platform.system() == 'Darwin':
            return os.open(
                destination,
                os.O_CREAT | os.O_TRUNC | os.O_RDWR | os.O_SYNC)

        return os.open(
            destination,
            os.O_CREAT | os.O_DIRECT | os.O_TRUNC | os.O_RDWR)

    @staticmethod
    def _read_file(path, file_name):
        with open(join(path, file_name), 'r') as fault:
            return fault.read().strip()

    def verify_flash_success(self, target, file_path):
        """
        verify flash went well
        """
        mount = target['mount_point']
        if isfile(join(mount, 'FAIL.TXT')):
            fault = FlasherMbed._read_file(mount, "FAIL.TXT")
            self.logger.error("Flashing failed: %s. tid=%s",
                              fault, target["target_id"])

            try:
                errors = [error for error in DAPLINK_ERRORS if error in fault]
                assert len(errors) == 1
                raise FlashError(message=fault, return_code=DAPLINK_ERRORS[errors[0]])
            except AssertionError:
                msg = "Expected to find exactly one error in fault: {}".format(fault)
                self.logger.exception(msg)
                raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)
            except KeyError:
                msg = "Did not find error with key {}".format(fault)
                self.logger.exception(msg)
                raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)

        if isfile(join(mount, 'ASSERT.TXT')):
            fault = FlasherMbed._read_file(mount, "ASSERT.TXT")
            msg = "Flashing failed: {}. tid={}".format(fault, target)
            raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)

        if isfile(file_path):
            msg = "Flashing failed: File still present in mount point. tid info: {}".format(target)
            raise FlashError(message=msg, return_code=EXIT_CODE_FILE_STILL_PRESENT)

        self.logger.debug("ready")
        return EXIT_CODE_SUCCESS
