#!/usr/bin/env python
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
import mbed_lstools


# pylint: disable=too-few-public-methods
class Helper(object):
    """
    Helper class for all tests
    """
    def __init__(self, platform_name, allowed_files):
        self.platform_name = platform_name
        self.allowed_files = []
        self.allowed_files.extend(allowed_files)

    def clear(self):
        """
        clear Files should not be put into mount point
        """
        if self.platform_name:
            targets = self._get_targets()

            # Clear files other than allowed
            for target in targets:
                mount_point = target.get('mount_point')
                if mount_point:
                    for bad_file in os.listdir(mount_point):
                        if os.path.isfile(bad_file) and bad_file not in self.allowed_files:
                            os.remove(os.path.join(mount_point, bad_file))

    def _get_targets(self):
        """
        Return targets matching passed platform name
        """
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        selected_targets = []

        if targets:
            for target in targets:
                if target['platform_name'] == self.platform_name:
                    selected_targets.append(target)

        return selected_targets

    @staticmethod
    def list_mbeds_ext():
        """
         :return: list of mbeds with details.txt content
        """
        mbeds = mbed_lstools.create()
        return mbeds.list_mbeds(read_details_txt=True)

    @staticmethod
    def list_mbeds_eraseable(devices=None):
        """
        :param devices: devices list or None
        :return: list eraseable mbeds extended list
        """
        devices = devices or Helper.list_mbeds_ext()
        devices = [dev for dev in devices if dev.get('daplink_automation_allowed') == '1']
        return devices
