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

from os.path import join, isfile
import six

from mbed_flasher.common import Common, Logger, EraseError
from mbed_flasher.mbed_common import MbedCommon
from mbed_flasher.reset import Reset
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_MISSING
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_ERASE_FAILED
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD
from mbed_flasher.return_codes import EXIT_CODE_IMPLEMENTATION_MISSING
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_MOUNT_POINT_MISSING
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_PORT_MISSING
from mbed_flasher.return_codes import EXIT_CODE_FILE_STILL_PRESENT

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
        Get available devices
        :return: list of devices
        """
        return Common(self.logger).get_available_device_mapping(self.flashers)

    @staticmethod
    def __get_flashers():
        """
        :return: list of available flashers
        """
        from mbed_flasher.flashers import AvailableFlashers
        return AvailableFlashers

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

    def erase(self, target_id=None, no_reset=None, method=None):
        """
        Erase (mbed) device(s).
        :param target_id: target_id
        :param no_reset: erase with/without reset
        :param method: method for erase i.e. simple, pyocd or edbg
        """
        if target_id is None:
            raise EraseError(message="target id is missing",
                             return_code=EXIT_CODE_TARGET_ID_MISSING)

        self.logger.info("Starting erase for given target_id %s", target_id)
        self.logger.info("method used for reset: %s", method)
        available_devices = Common(self.logger).get_available_device_mapping(
            self.flashers, target_id)

        targets_to_erase = self.prepare_target_to_erase(target_id, available_devices)

        if len(targets_to_erase) <= 0:
            msg = "Could not map given target_id(s) to available devices"
            raise EraseError(message=msg,
                             return_code=EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

        for item in targets_to_erase:
            if method == 'simple':
                erase_fnc = self._erase_board_simple
            elif method == 'pyocd':
                erase_fnc = self._erase_board_with_pyocd
            elif method == 'edbg':
                raise EraseError(message="egdb not supported",
                                 return_code=EXIT_CODE_IMPLEMENTATION_MISSING)
            else:
                raise EraseError(message="Selected method {} not supported".format(method),
                                 return_code=EXIT_CODE_MISUSE_CMD)

            erase_fnc(target=item, no_reset=no_reset)

        return EXIT_CODE_SUCCESS

    # pylint: disable=too-many-return-statements, too-many-branches
    def _erase_board_simple(self, target, no_reset):
        """
        :param target: target to which perform the erase
        :param no_reset: erase with/without reset
        :return: exit code
        """
        if "mount_point" not in target:
            raise EraseError(message="mount point missing from target",
                             return_code=EXIT_CODE_MOUNT_POINT_MISSING)

        if "serial_port" not in target:
            raise EraseError(message="serial port missing from target",
                             return_code=EXIT_CODE_SERIAL_PORT_MISSING)

        Erase._can_be_erased(target)

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

    def _erase_board_with_pyocd(self, target, no_reset):
        try:
            from pyOCD.board import MbedBoard
            from pyOCD.pyDAPAccess import DAPAccessIntf
        except ImportError:
            raise EraseError(message="pyOCD is not installed",
                             return_code=EXIT_CODE_PYOCD_MISSING)

        target_id = target["target_id"]
        board = MbedBoard.chooseBoard(board_id=target_id)
        self.logger.info("erasing device: %s", target_id)
        ocd_target = board.target
        flash = ocd_target.flash
        try:
            flash.eraseAll()
            if not no_reset:
                ocd_target.reset()
        except DAPAccessIntf.TransferFaultError:
            msg = "PyOCD erase failed"
            self.logger.exception(msg)
            raise EraseError(message=msg, return_code=EXIT_CODE_PYOCD_ERASE_FAILED)

        self.logger.info("erase completed for target: %s", target_id)
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
