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
from os.path import join, isfile
import os
from time import sleep
import hashlib
import platform
import subprocess

import six

from mbed_flasher.common import FlashError, EraseError
from mbed_flasher.mbed_common import MbedCommon
from mbed_flasher.daplink_errors import DAPLINK_ERRORS
from mbed_flasher.reset import Reset
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_FLASH_FAILED
from mbed_flasher.return_codes import EXIT_CODE_FILE_COULD_NOT_BE_READ
from mbed_flasher.return_codes import EXIT_CODE_OS_ERROR
from mbed_flasher.return_codes import EXIT_CODE_FILE_STILL_PRESENT
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_MOUNT_POINT_MISSING
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_PORT_MISSING
from mbed_flasher.return_codes import EXIT_CODE_IMPLEMENTATION_MISSING

ERASE_REMOUNT_TIMEOUT = 10
ERASE_VERIFICATION_TIMEOUT = 30
ERASE_DAPLINK_SUPPORT_VERSION = 243


class FlasherMbed(object):
    """
    Implementation class of mbed-flasher flash operation
    """
    name = "mbed"

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger('mbed-flasher')

    # pylint: disable=unused-argument
    def flash(self, source, target, no_reset):
        """copy file to the destination
        :param source: binary to be flashed
        :param target: target to be flashed
        :param no_reset: do not reset flashed board at all
        """
        if not isinstance(source, six.string_types):
            return

        return self.try_drag_and_drop_flash(source, target, no_reset)

    # pylint: disable=too-many-return-statements, too-many-branches
    def erase(self, target, no_reset):
        """
        :param target: target to which perform the erase
        :param no_reset: erase with/without reset
        :return: exit code
        """
        self.logger.debug('Erasing with drag and drop')
        if "mount_point" not in target:
            raise EraseError(message="mount point missing from target",
                             return_code=EXIT_CODE_MOUNT_POINT_MISSING)

        if "serial_port" not in target:
            raise EraseError(message="serial port missing from target",
                             return_code=EXIT_CODE_SERIAL_PORT_MISSING)

        FlasherMbed._can_be_erased(target)

        # Copy ERASE.ACT to target mount point, this will trigger the erasing.
        destination = MbedCommon.get_binary_destination(target["mount_point"], "ERASE.ACT")
        with open(destination, "wb"):
            pass

        target = MbedCommon.wait_for_file_disappear(target, "ERASE.ACT")

        if not no_reset:
            Reset(logger=self.logger).reset_board(target["serial_port"])

        self._verify_erase_success(MbedCommon.get_binary_destination(
            target["mount_point"], "ERASE.ACT"))

        self.logger.info("erase %s completed", target["target_id"])
        return EXIT_CODE_SUCCESS

    def try_drag_and_drop_flash(self, source, target, no_reset):
        """
        Try to flash the target using drag and drop method.
        :param source: file to be flashed
        :param target: target board to be flashed
        :param no_reset: whether to reset the board after flash
        :return: 0 if success
        """

        target = MbedCommon.refresh_target(target["target_id"])
        if not target:
            raise FlashError(message="Target ID is missing",
                             return_code=EXIT_CODE_TARGET_ID_MISSING)

        destination = MbedCommon.get_binary_destination(target["mount_point"], source)

        try:
            if 'serial_port' in target and not no_reset:
                Reset(logger=self.logger).reset_board(target["serial_port"])
                sleep(0.1)

            self.copy_file(source, destination)
            self.logger.debug("copy finished")

            target = MbedCommon.wait_for_file_disappear(target, source)

            if not no_reset:
                Reset(logger=self.logger).reset_board(target["serial_port"])
                sleep(0.4)

            # verify flashing went as planned
            self.logger.debug("verifying flash")
            return self.verify_flash_success(
                target, MbedCommon.get_binary_destination(target["mount_point"], source))
        # In python3 IOError is just an alias for OSError
        except (OSError, IOError) as error:
            msg = "File copy failed due to: {}".format(str(error))
            self.logger.exception(msg)
            raise FlashError(message=msg,
                             return_code=EXIT_CODE_OS_ERROR)

    def copy_file(self, source, destination):
        """
        copy file from os
        """
        self.logger.debug('read source file')
        try:
            with open(source, 'rb') as source_file:
                aux_source = source_file.read()
        except (IOError, OSError):
            self.logger.exception("File couldn't be read")
            raise FlashError(message="File couldn't be read",
                             return_code=EXIT_CODE_FILE_COULD_NOT_BE_READ)

        self.logger.debug("SHA1: %s", hashlib.sha1(aux_source).hexdigest())

        try:
            if platform.system() == "Windows":
                self._copy_file_windows(source, destination)
            else:
                self._copy_file(aux_source, destination)
        except (IOError, OSError, subprocess.CalledProcessError):
            self.logger.exception("File couldn't be copied")
            raise FlashError(message="File couldn't be copied",
                             return_code=EXIT_CODE_OS_ERROR)

    def _copy_file_windows(self, source, destination):
        command = ["cmd", "/c", "copy", os.path.abspath(source), destination]
        self.logger.debug("Copying with command: {}".format(command))
        subprocess.check_call(command)

    def _copy_file(self, aux_source, destination):
        destination_fd = None
        try:
            if os.uname()[4].startswith('arm'):
                destination_fd = os.open(
                    destination,
                    os.O_CREAT | os.O_TRUNC | os.O_RDWR | os.O_DIRECT)
            else:
                destination_fd = os.open(
                    destination,
                    os.O_CREAT | os.O_TRUNC | os.O_RDWR | os.O_SYNC)

            self.logger.debug("Copying binary: %s (size=%i bytes)", destination, len(aux_source))
            os.write(destination_fd, aux_source)
        finally:
            if destination_fd:
                os.close(destination_fd)

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
                assert len(errors) <= 1
                raise FlashError(message=fault, return_code=DAPLINK_ERRORS[errors[0]])
            except AssertionError:
                msg = "Found multiple errors from FAIL.TXT: {}".format(fault)
                self.logger.exception(msg)
                raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)
            except IndexError:
                msg = "Error in FAIL.TXT is unknown: {}".format(fault)
                self.logger.exception(msg)
                raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)

        if isfile(join(mount, 'ASSERT.TXT')):
            fault = FlasherMbed._read_file(mount, "ASSERT.TXT")
            msg = "Found ASSERT.TXT: {}".format(fault)
            self.logger.error("{} found ASSERT.txt: {}".format(target["target_id"], fault))
            raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)

        if isfile(file_path):
            msg = "File still present in mount point"
            self.logger.error("{} file still present in mount point".format(target["target_id"]))
            raise FlashError(message=msg, return_code=EXIT_CODE_FILE_STILL_PRESENT)

        self.logger.debug("ready")
        return EXIT_CODE_SUCCESS

    def _verify_erase_success(self, destination):
        """
        Verify that ERASE.ACT is not present in the target mount point.
        :param destination: target mount point
        :return: None on success, raises otherwise
        """
        if isfile(destination):
            msg = "Erase failed: ERASE.ACT still present in mount point"
            self.logger.error(msg)
            raise EraseError(message=msg, return_code=EXIT_CODE_FILE_STILL_PRESENT)

    @staticmethod
    def _can_be_erased(target):
        """
        Check if target can be erased.
        :param target: target board to be checked
        :return: None if can be erased, raises otherwise
        """
        try:
            with open(join(target["mount_point"], 'DETAILS.TXT'), 'rb') as new_file:
                details_txt = new_file.readlines()
        except (OSError, IOError):
            raise EraseError(message="No DETAILS.TXT found",
                             return_code=EXIT_CODE_IMPLEMENTATION_MISSING)

        automation_activated = False
        daplink_version = 0
        for line in details_txt:
            if line.find(b"Automation allowed: 1") != -1:
                automation_activated = True
            if line.find(b"Interface Version") != -1:
                try:
                    if six.PY2:
                        daplink_version = int(line.split(' ')[-1])
                    else:
                        daplink_version = int(line.decode('utf-8').split(' ')[-1])
                except (IndexError, ValueError):
                    raise EraseError(message="Failed to parse DAPLINK version from DETAILS.TXT",
                                     return_code=EXIT_CODE_IMPLEMENTATION_MISSING)

        if not automation_activated:
            msg = "Selected device does not have automation activated in DAPLINK"
            raise EraseError(message=msg, return_code=EXIT_CODE_IMPLEMENTATION_MISSING)

        if daplink_version < ERASE_DAPLINK_SUPPORT_VERSION:
            msg = "Selected device has Daplink version {}," \
                  "erasing supported from version {} onwards". \
                format(daplink_version, ERASE_DAPLINK_SUPPORT_VERSION)
            raise EraseError(message=msg, return_code=EXIT_CODE_IMPLEMENTATION_MISSING)
