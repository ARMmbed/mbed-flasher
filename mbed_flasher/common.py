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
import platform
from time import sleep
from subprocess import check_output, CalledProcessError
import six

import mbed_lstools

from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_CONFLICT
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_PORT_REAPPEAR_TIMEOUT
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_MOUNT_POINT_MISSING


# pylint: disable=too-few-public-methods
class Common(object):
    """
    Class for holding common methods for all operations (flash, erase, reset).
    """
    GET_DEVICES_RETRY = 5

    def __init__(self, logger):
        self.logger = logger

    def get_available_device_mapping(self, flashers, target=None):
        """
        Loop through flashers in search for devices.
        If specific device is given retry multiple times if not found.
        :return: list of available devices
        """

        def get_devices():
            """
            Get devices from flasher.
            :return: list of devices
            """
            available_devices = []
            for flasher in flashers:
                available_devices.extend(flasher.get_available_devices())

            return available_devices

        if isinstance(target, list) and len(target) == 1:
            target = target[0]

        if not isinstance(target, six.string_types) or target == "all":
            return get_devices()

        devices = []
        # This is a workaround for a problem where mbedls (basically mount command)
        # fails to list mount point sometimes in linux. Occurs at least in Raspberry Pi3.
        for index in range(Common.GET_DEVICES_RETRY):
            if index > 0:
                self.logger.warning("Did not find %s, trying again (%d)", target, index)

            devices = get_devices()
            try:
                for target_id in [device["target_id"] for device in devices]:
                    if target in target_id:
                        return devices
            except (KeyError, TypeError):
                self.logger.exception("Invalid device listing from flasher")
                return []

        self.logger.warning("Did not find %s giving up", target)
        return devices


# pylint: disable=too-few-public-methods
class Logger(object):
    """
    Logger provider
    """
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self.logger.addHandler(logging.NullHandler())
            self.logger.setLevel(logging.ERROR)
            self.logger.propagate = False
            self.logger.info('No logger supplied, using default logging logger')

    def __call__(self, name):
        return self.logger


class MountVerifier(object):
    """
    Verifier class used to verify that device returns to operational state
    after flash or erase.
    """
    MOUNT_POINT_TIMEOUT = 20
    SERIAL_POINT_TIMEOUT = 20

    def __init__(self, logger):
        self.logger = logger

    def check_points_unchanged(self, target):
        """
        Check if points are unchanged
        """
        new_target = {}
        if platform.system() == 'Windows':
            mbedls = mbed_lstools.create()
            mbeds = mbedls.list_mbeds(filter_function=
                                      lambda m: m['target_id'] == target['target_id'])
            if len(mbeds) == 1:
                if target['serial_port'] != mbeds[0]['serial_port']:
                    new_target['serial_port'] = mbeds[0]['serial_port']
            elif len(mbeds) > 1:
                self.logger.warning('got multiple target with same target_id: %s',
                                    target['target_id'])
            return self._get_target(new_target=new_target, target=target)

        if platform.system() == 'Darwin':
            return self._get_target(new_target, target)

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

        return self._get_target(new_target, target)

    def _get_target(self, new_target, target):
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

        return target

    def _check_serial_point_duplicates(self, target, new_target):
        """
        Verify that target is not listed multiple times in /dev/serial/by-id
        :param target: old target
        :param new_target: new target
        :return: if all is well None, otherwise error code
        """
        for _ in range(MountVerifier.SERIAL_POINT_TIMEOUT):
            try:
                lines = check_output(["ls", "-oA", "/dev/serial/by-id/"]).splitlines()
            except CalledProcessError:
                lines = []

            target_found_once = False
            for line in lines:
                if six.PY3:
                    line = line.decode('utf-8')

                if line.find(target['target_id']) != -1:
                    target_found_once = True
                    if target['serial_port'].split('/')[-1] != line.split('/')[-1]:
                        if 'serial_port' not in new_target:
                            new_target['serial_port'] = '/dev/' + line.split('/')[-1]
                            self.logger.debug('target_id %s serial port changed from %s to %s',
                                              target['target_id'], target['serial_port'],
                                              new_target['serial_port'])
                        else:
                            self.logger.error('target_id %s has more than 1 '
                                              'serial port in the system',
                                              target['target_id'])
                            return EXIT_CODE_TARGET_ID_CONFLICT

            # If target is found even once expect duplication to have appeared
            if target_found_once:
                return

            sleep(1)

        self.logger.error(
            "serial point for %s did not re-appear in the system in %i seconds",
            target['target_id'], MountVerifier.SERIAL_POINT_TIMEOUT)
        return EXIT_CODE_SERIAL_PORT_REAPPEAR_TIMEOUT

    def _check_device_point_duplicates(self, target, new_target):
        """
        Verify that target is not listed multiple times in /dev/disk/by-id
        :param target: old target
        :param new_target: new target
        :return: if all is well None, otherwise error code
        """
        lines = check_output(["ls", "-oA", "/dev/disk/by-id/"]).splitlines()
        for dev_line in lines:
            if six.PY3:
                dev_line = dev_line.decode('utf-8')
            if dev_line.find(target['target_id']) != -1:
                if 'dev_point' not in new_target:
                    new_target['dev_point'] = '/dev/' + dev_line.split('/')[-1]
                else:
                    self.logger.error("target_id %s has more than 1 "
                                      "device point in the system",
                                      target['target_id'])
                    return EXIT_CODE_TARGET_ID_CONFLICT

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
            return EXIT_CODE_TARGET_ID_MISSING

        for _ in range(MountVerifier.MOUNT_POINT_TIMEOUT):
            mounts = check_output(["mount", "|", "grep", "vfat"], shell=True).splitlines()
            for mount in mounts:
                if six.PY3:
                    mount = mount.decode('utf-8')
                if mount.find(new_target['dev_point']) != -1:
                    new_target['mount_point'] = \
                        mount.split('on')[1].split('type')[0].strip()
                    return
            sleep(1)

        self.logger.error(
            "vfat mount point for %s did not re-appear in the system in %i seconds",
            target['target_id'], MountVerifier.MOUNT_POINT_TIMEOUT)
        return EXIT_CODE_MOUNT_POINT_MISSING
