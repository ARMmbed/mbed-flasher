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
from os.path import join, isfile, isdir
from os import listdir, remove
from time import sleep
import hashlib
import platform
import subprocess
import tarfile
import shutil
import six

from mbed_flasher.flashers.FlasherMbed import FlasherMbed
from mbed_flasher.common import retry, FlashError
from mbed_flasher.mbed_common import MbedCommon
from mbed_flasher.daplink_errors import DAPLINK_ERRORS
from mbed_flasher.reset import Reset
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_FLASH_FAILED
from mbed_flasher.return_codes import EXIT_CODE_FILE_COULD_NOT_BE_READ
from mbed_flasher.return_codes import EXIT_CODE_OS_ERROR
from mbed_flasher.return_codes import EXIT_CODE_FILE_STILL_PRESENT
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_TRANSIENT_ERROR
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_SOFTWARE_ERROR


class FlasherMPS2(FlasherMbed):
    """
    Implementation class of mps2-flasher flash operation
    """
    name = "mbed_mps2"
    DRAG_AND_DROP_FLASH_RETRIES = 5
    
    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger('mbed-flasher')

    # pylint: disable=unused-argument
    def flash(self, source, target, method, no_reset):
        """copy file to the destination
        :param source: binary to be flashed
        :param target: target to be flashed
        :param method: method to use when flashing
        :param no_reset: do not reset flashed board at all
        """
        if not isinstance(source, six.string_types):
            return
        if source.endswith(".tar"):
           return retry(
                logger=self.logger,
                func=self.try_extract_tar_flash,
                func_args=(source, target, no_reset),
                retries=FlasherMPS2.DRAG_AND_DROP_FLASH_RETRIES,
                conditions=[EXIT_CODE_OS_ERROR,
                            EXIT_CODE_DAPLINK_TRANSIENT_ERROR,
                            EXIT_CODE_DAPLINK_SOFTWARE_ERROR])
        else:
            return retry(
                logger=self.logger,
                func=self.try_drag_and_drop_flash,
                func_args=(source, target, no_reset),
                retries=FlasherMPS2.DRAG_AND_DROP_FLASH_RETRIES,
                conditions=[EXIT_CODE_OS_ERROR,
                            EXIT_CODE_DAPLINK_TRANSIENT_ERROR,
                            EXIT_CODE_DAPLINK_SOFTWARE_ERROR])

    def try_extract_tar_flash(self, source, target, no_reset):
        """
        Try to flash the target by extracting tar file.
        :param source: file to be flashed
        :param target: target board to be flashed
        :param no_reset: whether to reset the board after flash
        :return: 0 if success
        """
        target = MbedCommon.refresh_target(target["target_id"])
        if not target:
            raise FlashError(message="Target ID is missing",
                             return_code=EXIT_CODE_TARGET_ID_MISSING)

        destination = target["mount_point"]

        # start by removing old files from sdcard
        self.logger.debug("Clean mount point: %s", destination)
        try:
            for fname in listdir(destination):
                if fname == "mbed.htm":
                    continue
                fpath = join(destination, fname)
                if isfile(fpath):
                    remove(fpath)
                elif isdir(fpath):
                    shutil.rmtree(fpath)
        except Exception as error:
            msg = "Erasing sdcard failed due to: {}".format(str(error))
            self.logger.exception(msg)
            raise FlashError(message=msg,
                             return_code=EXIT_CODE_FLASH_FAILED)

        try:
            self.logger.debug("Extract file: %s", source)
            tar = tarfile.open(source)
            tar.extractall(path=destination)
            tar.close()
            # Find mount node
            command = "mount"
            self._process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = self._process.communicate()[0]

            for line in output.split("\n"):
                if destination in line.split():
                    node = line.split()[0]
            command = "pumount %s" % destination
            self._process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = self._process.communicate()

            command = "pmount --sync --fmask 0022 --dmask 0022 -A %s %s" % (node, destination)
            self._process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = self._process.communicate()
            sleep(3)

            if not no_reset:
                Reset(logger=self.logger).reset_mps2(target)
                self.logger.debug("Verifying flash")
                target = MbedCommon.refresh_target(target["target_id"])
                return self.verify_flash_success(
                    target, MbedCommon.get_binary_destination(target["mount_point"], source))
            else:
                return EXIT_CODE_SUCCESS
        except Exception as error:
            msg = "Extracting to sdcard failed due to: {}".format(str(error))
            self.logger.exception(msg)
            raise FlashError(message=msg,
                             return_code=EXIT_CODE_FLASH_FAILED)
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
            self.copy_file(source, destination)
            self.logger.debug("copy finished")

            if not no_reset:
                Reset(logger=self.logger).reset_mps2(target)
                self.logger.debug("verifying flash")
                return self.verify_flash_success(
                    target, MbedCommon.get_binary_destination(target["mount_point"], source))
        # In python3 IOError is just an alias for OSError
        except (OSError, IOError) as error:
            msg = "File copy failed due to: {}".format(str(error))
            self.logger.exception(msg)
            raise FlashError(message=msg,
                             return_code=EXIT_CODE_OS_ERROR)
        return EXIT_CODE_SUCCESS

    def verify_flash_success(self, target, file_path):
        """
        verify flash went well
        """
        mount = target['mount_point']
        if isfile(join(mount, 'LOG.TXT')):
            log = FlasherMbed._read_file(mount, "LOG.TXT")
            for line in log.split("\n"):
                if line.startswith("ERROR:"):
                    msg = "Found {}".format(line)
                    self.logger.error("{} found {}".format(target["target_id"], line))
                    raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)
        else:
            msg = "No LOG.TXT, sdcard corrupt"
            self.logger.error("{} found no LOG.TXT".format(target["target_id"]))
            raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)

        self.logger.debug("ready")
        return EXIT_CODE_SUCCESS
