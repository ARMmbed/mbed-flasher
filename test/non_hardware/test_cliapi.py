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

import subprocess
import unittest

from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD


class ApiTests(unittest.TestCase):
    @staticmethod
    def spawn(parameters):
        parameters.insert(0, "mbedflash")
        return subprocess.call(parameters)

    def test_help(self):
        parameters = ['--help']
        self.assertEqual(ApiTests.spawn(parameters), EXIT_CODE_SUCCESS)

    def test_misuse_cmd(self):
        parameters = ['a']
        self.assertEqual(ApiTests.spawn(parameters), EXIT_CODE_MISUSE_CMD)
