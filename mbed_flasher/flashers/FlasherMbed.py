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
from mbed_flasher.flashers.enhancedserial import EnhancedSerial
import mbed_lstools


class FlasherMbed(object):
    """
    Implementation class of mbed-flasher flash operation
    """
    name = "mbed"
    FLASHING_VERIFICATION_TIMEOUT = 100

    def __init__(self):
        self.logger = logging.getLogger('mbed-flasher')

    @staticmethod
    def get_supported_targets():
        """
        Load target mapping information
        """
        mbeds = mbed_lstools.create()
        return sorted(set(mbeds.manufacture_ids.values()))

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
            return -6
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

    @staticmethod
    def auxiliary_drive_check(drive):
        """
        Check if auxiliary drive exists
        """
        out = os.listdir(drive[0])
        for item in out:
            if item.find('.HTM') != -1:
                break
        else:
            return False
        if drive[1] not in out:
            return True

    def runner(self, drive):
        """
        Runner
        """
        start_time = time()
        while True:
            sleep(2)
            if platform.system() == 'Windows':
                proc = Popen(["dir", drive[0]],
                             stdin=PIPE,
                             stdout=PIPE,
                             stderr=PIPE,
                             shell=True)
            else:
                proc = Popen(["ls", drive[0]], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            out = proc.stdout.read()
            proc.communicate()
            if out.find(b'.HTM') != -1:
                if out.find(drive[1].encode()) == -1:
                    break
            if platform.system() == 'Windows':
                if not out:
                    if self.auxiliary_drive_check(drive):
                        break
            if time() - start_time > self.FLASHING_VERIFICATION_TIMEOUT:
                self.logger.debug("re-mount check timed out for %s", drive[0])
                break

    def _check_serial_point_duplicates(self, target, new_target):
        """
        Verify that target is not listed multiple times in /dev/serial/by-id
        :param target: old target
        :param new_target: new target
        :return: if all is well None, otherwise error code
        """
        for line in os.popen('ls -oA /dev/serial/by-id/').read().splitlines():
            if line.find(target['target_id']) != -1 \
                    and target['serial_port'].split('/')[-1] != line.split('/')[-1]:
                if 'serial_port' not in new_target:
                    new_target['serial_port'] = '/dev/' + line.split('/')[-1]
                else:
                    self.logger.error('target_id %s has more than 1 '
                                      'serial port in the system',
                                      target['target_id'])
                    return -10

    def _check_device_point_duplicates(self, target, new_target):
        """
        Verify that target is not listed multiple times in /dev/disk/by-id
        :param target: old target
        :param new_target: new target
        :return: if all is well None, otherwise error code
        """
        for dev_line in os.popen('ls -oA /dev/disk/by-id/').read().splitlines():
            if dev_line.find(target['target_id']) != -1:
                if 'dev_point' not in new_target:
                    new_target['dev_point'] = '/dev/' + dev_line.split('/')[-1]
                else:
                    self.logger.error("target_id %s has more than 1 "
                                      "device point in the system",
                                      target['target_id'])
                    return -11

    def _verify_mount_point(self, target, new_target):
        """
        Verify that if target has changed points a mount point can still be found for it
        :param target: old target
        :param new_target: new target
        :return: if all is well None, otherwise error code
        """
        if not new_target:
            return

        if 'dev_point' not in new_target:
            self.logger.error("Target %s is missing /dev/disk/by-id/ point",
                              target['target_id'])
            return -12

        for _ in range(10):
            mounts = os.popen('mount |grep vfat').read().splitlines()
            for mount in mounts:
                if mount.find(new_target['dev_point']) != -1:
                    new_target['mount_point'] = \
                        mount.split('on')[1].split('type')[0].strip()
                    return
                sleep(1)

        self.logger.error("vfat mount point for %s did not re-appear in "
                          "the system in 10 seconds", target['target_id'])
        return -12

    def check_points_unchanged(self, target):
        """
        Check if points are unchanged
        """
        new_target = {}
        if platform.system() == 'Windows':
            mbeds = mbed_lstools.create()
            if target['serial_port'] != mbeds.get_mbed_com_port(target['target_id']):
                new_target['serial_port'] = mbeds.get_mbed_com_port(target['target_id'])

            return self.get_target(new_target=new_target, target=target)

        if platform.system() == 'Darwin':
            return self.get_target(new_target, target)

        return_code = self._check_serial_point_duplicates(target=target,
                                                          new_target=new_target)
        if return_code:
            return return_code

        return_code = self._check_device_point_duplicates(target=target,
                                                          new_target=new_target)
        if return_code:
            return return_code

        return_code = self._verify_mount_point(target=target, new_target=new_target)
        if return_code:
            return return_code

        return self.get_target(new_target, target)

    def get_target(self, new_target, target):
        """
        get target
        """
        if new_target:
            if 'serial_port' in new_target:
                self.logger.debug("serial port %s has changed to %s",
                                  target['serial_port'], new_target['serial_port'])
            else:
                self.logger.debug("serial port %s has not changed",
                                  target['serial_port'])
            if 'mount_point' in new_target:
                self.logger.debug("mount point %s has changed to %s",
                                  target['mount_point'], new_target['mount_point'])
            else:
                self.logger.debug("mount point %s has not changed",
                                  target['mount_point'])
            new_target['target_id'] = target['target_id']
            return new_target
        else:
            return target

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
            return -13

        try:
            if 'serial_port' in target and not no_reset:
                self.reset_board(target['serial_port'])
                sleep(0.1)

            copy_file_success = self.copy_file(source, destination)
            if copy_file_success == -7:
                return -7

            self.logger.debug("copy finished")
            sleep(4)

            new_target = self.check_points_unchanged(target)

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
            return -14

    def try_pyocd_flash(self, source, target):
        """
        try pyOCD flash
        """
        try:
            from pyOCD.board import MbedBoard
        except ImportError:
            # python 3 compatibility
            # pylint: disable=superfluous-parens
            print('pyOCD missing, install\n')
            return -8

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
            return 0
        except AttributeError as err:
            self.logger.error("Flashing failed: %s. tid=%s",
                              err, target["target_id"])
            return -4

    def copy_file(self, source, destination):
        """
        copy file from os
        """
        if platform.system() == 'Windows':

            with open(source, 'rb') as source_file:
                aux_source = source_file.read()
                self.logger.debug("SHA1: %s",
                                  hashlib.sha1(aux_source).hexdigest())
            self.logger.debug("copying file: %s to %s",
                              source, destination)
            os.system("copy %s %s" % (os.path.abspath(source), destination))
        else:
            self.logger.debug('read source file')
            with open(source, 'rb') as source_file:
                aux_source = source_file.read()
            if not aux_source:
                self.logger.error("File couldn't be read")
                return -7
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

    def verify_flash_success(self, new_target, target, tail):
        """
        verify flash went well
        """
        if 'mount_point' in new_target:
            mount = new_target['mount_point']
        else:
            mount = target['mount_point']
        if isfile(join(mount, 'FAIL.TXT')):
            with open(join(mount, 'FAIL.TXT'), 'r') as fault:
                fault = fault.read().strip()
            self.logger.error("Flashing failed: %s. tid=%s",
                              fault, target["target_id"])
            return -4
        if isfile(join(mount, 'ASSERT.TXT')):
            with open(join(mount, 'ASSERT.TXT'), 'r') as fault:
                fault = fault.read().strip()
            self.logger.error("Flashing failed: %s. tid=%s",
                              fault, target)
            return -4
        if isfile(join(mount, tail)):
            self.logger.error("Flashing failed: File still present "
                              "in mount point. tid info: %s", target)
            return -15
        self.logger.debug("ready")
        return 0
