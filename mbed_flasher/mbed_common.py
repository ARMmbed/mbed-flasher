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

import os
import time

import mbed_lstools


CHECK_BINARY_DISAPPEAR_RETRIES = 60
CHECK_BINARY_DISAPPEAR_SLEEP = 1
REFRESH_TARGET_RETRIES = 100
REFRESH_TARGET_SLEEP = 1


class MbedCommon(object):
    """
    Collection of functions common for mbed operations.
    """
    @staticmethod
    def get_binary_destination(mount_point, source_file):
        """
        Form absolute path from mount point and file name
        :param mount_point: mount point
        :param source_file: source file name
        :return: absolute path
        """
        mount_point = os.path.abspath(mount_point)
        (_, tail) = os.path.split(os.path.abspath(source_file))
        return os.path.abspath(os.path.join(mount_point, tail))

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

        for _ in range(REFRESH_TARGET_RETRIES):
            mbeds = mbedls.list_mbeds(filter_function=lambda m: m["target_id"] == target_id)
            if mbeds:
                return mbeds[0]

            time.sleep(REFRESH_TARGET_SLEEP)

        return None

    @staticmethod
    def wait_for_file_disappear(target, source):
        """
        Wait for flashed binary to disappear from the mount point.
        Does not raise exceptions.
        :param target: target object
        :param source: binary name
        :return: target object
        """
        for _ in range(CHECK_BINARY_DISAPPEAR_RETRIES):
            try:
                target = MbedCommon.refresh_target_once(target["target_id"])[0]
            except IndexError:
                # This is entered when mbedls fails to find the board,
                # most likely due to remount in progress.
                time.sleep(CHECK_BINARY_DISAPPEAR_SLEEP)
                continue

            if not os.path.isfile(MbedCommon.get_binary_destination(target["mount_point"], source)):
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

            time.sleep(CHECK_BINARY_DISAPPEAR_SLEEP)

        return target
