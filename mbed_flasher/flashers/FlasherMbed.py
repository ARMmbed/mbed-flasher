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
from time import sleep, time
from threading import Thread
import hashlib
from subprocess import PIPE, Popen
from serial.serialutil import SerialException
import six

import mbed_lstools

from mbed_flasher.common import MountVerifier
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


class FlasherMbed(object):
    """
    Implementation class of mbed-flasher flash operation
    """
    name = "mbed"
    FLASHING_VERIFICATION_TIMEOUT = 100

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger('mbed-flasher')

    @staticmethod
    def get_supported_targets():
        """
        Load target mapping information
        """
        mbeds = mbed_lstools.create()

        # this should works for >=v1.3.0
        # @todo this is workaround until mbed-ls provide public
        #       API to get list of supported platform names
        list_supported_targets = sorted(set(name for id, name in mbeds.plat_db.items()))
        return list_supported_targets

    @staticmethod
    def get_available_devices():
        """
        Get available devices
        """
        mbeds = mbed_lstools.create()
        return mbeds.list_mbeds()

    def reset_board(self, serial_port):
        """
        Reset board
        """
        try:
            port = EnhancedSerial(serial_port)
        except SerialException as err:
            self.logger.info("reset could not be sent")
            self.logger.error(err)
            # SerialException.message is type "string"
            # pylint: disable=no-member
            if err.message.find('could not open port') != -1:
                # python 3 compatibility
                # pylint: disable=superfluous-parens
                print('Reset could not be given. Close your Serial connection to device.')
            return EXIT_CODE_RESET_FAIL

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

    def runner(self, drive):
        """
        Runner
        """
        start_time = time()
        while True:
            sleep(2)
            if platform.system() == 'Windows':
                proc = Popen(["dir", drive[0]], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
            else:
                proc = Popen(["ls", drive[0]], stdin=PIPE, stdout=PIPE, stderr=PIPE)

            # todo: replace read() -> "(stdout, stderr) = proc.communicate()"
            # see: https://docs.python.org/2/library/subprocess.html#subprocess.Popen.kill
            # "Use communicate() rather than .stdin.write, .stdout.read or .stderr.read to
            # avoid deadlocks due to any of the other OS pipe buffers filling up and blocking
            # the child process."
            out = proc.stdout.read()
            proc.communicate()

            if out.lower().find(b'.htm') != -1:
                if out.find(drive[1].encode()) == -1:
                    break

            if time() - start_time > FlasherMbed.FLASHING_VERIFICATION_TIMEOUT:
                self.logger.debug("re-mount check timed out for %s", drive[0])
                break

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

        mount_point = os.path.abspath(target['mount_point'])
        (_, tail) = os.path.split(os.path.abspath(source))
        destination = abspath(join(mount_point, tail))

        if method == 'pyocd':
            self.logger.debug("pyOCD selected for flashing")
            return self.try_pyocd_flash(source, target)

        if method == 'edbg':
            self.logger.debug("edbg is not supported for Mbed devices")
            return EXIT_CODE_EGDB_NOT_SUPPORTED

        try:
            if 'serial_port' in target and not no_reset:
                self.reset_board(target['serial_port'])
                sleep(0.1)

            copy_file_success = self.copy_file(source, destination)
            if copy_file_success == EXIT_CODE_FILE_COULD_NOT_BE_READ:
                return EXIT_CODE_FILE_COULD_NOT_BE_READ

            self.logger.debug("copy finished")
            sleep(4)

            new_target = MountVerifier(self.logger).check_points_unchanged(target)

            if isinstance(new_target, int):
                return new_target

            thread = Thread(target=self.runner,
                            args=([target['mount_point'], tail],))
            thread.start()
            while thread.is_alive():
                thread.join(2.5)

            if not no_reset:
                if 'serial_port' in new_target:
                    self.reset_board(new_target['serial_port'])
                else:
                    self.reset_board(target['serial_port'])
                sleep(0.4)

            # verify flashing went as planned
            self.logger.debug("verifying flash")
            return self.verify_flash_success(new_target, target, tail)
        except IOError as err:
            self.logger.error(err)
            raise err
        except OSError as err:
            self.logger.error("Write failed due to OSError: %s", err)
            return EXIT_CODE_OS_ERROR

    def try_pyocd_flash(self, source, target):
        """
        try pyOCD flash
        """
        try:
            from pyOCD.board import MbedBoard
        except ImportError:
            # python 3 compatibility
            # pylint: disable=superfluous-parens
            self.logger.error("pyOCD missing, install")
            return EXIT_CODE_PYOCD_NOT_INSTALLED

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
            self.logger.error("Flashing failed: %s. tid=%s",
                              err, target["target_id"])
            return EXIT_CODE_FLASH_FAILED

    def copy_file(self, source, destination):
        """
        copy file from os
        """
        if platform.system() == 'Windows':

            with open(source, 'rb') as source_file:
                aux_source = source_file.read()
                self.logger.debug("SHA1: %s",
                                  hashlib.sha1(aux_source).hexdigest())
            self.logger.debug("copying file: \"%s\" to \"%s\"",
                              source, destination)
            os.system("copy \"%s\" \"%s\"" % (os.path.abspath(source), destination))
        else:
            self.logger.debug('read source file')
            with open(source, 'rb') as source_file:
                aux_source = source_file.read()

            if not aux_source:
                self.logger.error("File couldn't be read")
                return EXIT_CODE_FILE_COULD_NOT_BE_READ

            self.logger.debug("SHA1: %s",
                              hashlib.sha1(aux_source).hexdigest())
            self.logger.debug("writing binary: %s (size=%i bytes)",
                              destination,
                              len(aux_source))

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

    def verify_flash_success(self, new_target, target, tail):
        """
        verify flash went well
        """
        if 'mount_point' in new_target:
            mount = new_target['mount_point']
        else:
            mount = target['mount_point']

        if isfile(join(mount, 'FAIL.TXT')):
            fault = FlasherMbed._read_file(mount, "FAIL.TXT")
            self.logger.error("Flashing failed: %s. tid=%s",
                              fault, target["target_id"])

            try:
                errors = [error for error in DAPLINK_ERRORS if error in fault]
                assert len(errors) == 1
                return DAPLINK_ERRORS[errors[0]]
            except AssertionError:
                self.logger.warning("Expected to find exactly one error in fault: %s",
                                    fault)
                return EXIT_CODE_FLASH_FAILED
            except KeyError:
                return EXIT_CODE_FLASH_FAILED

        if isfile(join(mount, 'ASSERT.TXT')):
            fault = FlasherMbed._read_file(mount, "ASSERT.TXT")
            self.logger.error("Flashing failed: %s. tid=%s",
                              fault, target)
            return EXIT_CODE_FLASH_FAILED

        if isfile(join(mount, tail)):
            self.logger.error("Flashing failed: File still present "
                              "in mount point. tid info: %s", target)
            return EXIT_CODE_FILE_STILL_PRESENT

        self.logger.debug("ready")
        return EXIT_CODE_SUCCESS
