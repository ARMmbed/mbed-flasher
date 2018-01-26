#!/usr/bin/env python
"""
Copyright 2018 ARM Limited

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
# pylint:disable=missing-docstring

import os
import subprocess
import unittest
import mbed_lstools

from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_USER_ERROR


class ApiTests(unittest.TestCase):

    mbeds = mbed_lstools.create()

    @staticmethod
    def spawn(parameters):
        parameters.insert(0, "mbedflash")
        return subprocess.call(parameters)

    def find_platform(self, platform_name):
        return next((x for x in self.mbeds if x['platform_name'] == platform_name), None)

    def setUp(self):
        self.mbeds = ApiTests.mbeds.list_mbeds()
        self.bin_hello_world = os.path.join('test', 'helloworld.bin')
        self.bin_corrupted = os.path.join('test', 'corrupted.bin')

    def test_help(self):
        parameters = ['--help']
        self.assertEqual(ApiTests.spawn(parameters), EXIT_CODE_SUCCESS)

    def test_misuse_cmd(self):
        parameters = ['a']
        self.assertEqual(ApiTests.spawn(parameters), EXIT_CODE_MISUSE_CMD)

    def test_flash_success_no_reset(self):
        first_or_default = self.find_platform('K64F')
        if not first_or_default:
            self.skipTest('No any k64f devices connected')
            return
        filename = self.bin_hello_world
        target_id = first_or_default['target_id']
        parameters = ['flash', '--no-reset', '-i', filename, '--tid', target_id]
        self.assertEqual(ApiTests.spawn(parameters), EXIT_CODE_SUCCESS)

    def test_flash_success_with_reset(self):
        first_or_default = self.find_platform('K64F')
        if not first_or_default:
            self.skipTest('No any k64f devices connected')
            return
        filename = self.bin_hello_world
        target_id = first_or_default['target_id']
        parameters = ['flash', '-i', filename, '--tid', target_id]
        self.assertEqual(ApiTests.spawn(parameters), EXIT_CODE_SUCCESS)

    def test_flash_user_error_k64f(self):
        first_or_default = self.find_platform('K64F')
        if not first_or_default:
            self.skipTest('No any k64f devices connected')
            return
        filename = self.bin_corrupted
        target_id = first_or_default['target_id']
        parameters = ['flash', '--no-reset', '-i', filename, '--tid', target_id]
        self.assertEqual(ApiTests.spawn(parameters), EXIT_CODE_DAPLINK_USER_ERROR)
