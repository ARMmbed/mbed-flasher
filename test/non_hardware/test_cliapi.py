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
# pylint:disable=invalid-name
# pylint:disable=no-self-use

import subprocess
import unittest

import mock

from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD
from mbed_flasher.flash import Flash
from mbed_flasher.main import FlasherCLI


def spawn(parameters):
    parameters.insert(0, "mbedflash")
    return subprocess.call(parameters, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


class APITests(unittest.TestCase):
    def test_help(self):
        parameters = ['--help']
        self.assertEqual(spawn(parameters), EXIT_CODE_SUCCESS)

    def test_misuse_cmd(self):
        parameters = ['a']
        self.assertEqual(spawn(parameters), EXIT_CODE_MISUSE_CMD)


class EraseAPITest(unittest.TestCase):
    @mock.patch('mbed_flasher.mbed_common.MbedCommon.refresh_target')
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD.erase')
    def test_parameters_are_relayed_to_pyocd(self, mock_erase, mock_refresh_target):
        device = {"target_id": "1"}
        mock_refresh_target.return_value = device
        parameters = ['erase',
                      '--target_id', '1',
                      '--no-reset',
                      '--method', Flash.PYOCD_METHOD,
                      '--pyocd_platform', 'someplatform',
                      '--pyocd_pack', 'somepack',
                      '--pyocd_connect_mode', 'halt']

        cli = FlasherCLI(args=parameters)
        try:
            cli.execute()
        except: # pylint:disable=bare-except
            pass

        mock_erase.assert_called_once_with(
            target={"target_id": "1"},
            no_reset=True,
            platform="someplatform",
            pack="somepack",
            connect_mode="halt"
        )


class FlashAPITest(unittest.TestCase):
    @mock.patch('mbed_flasher.flash.check_file_exists')
    @mock.patch('mbed_flasher.mbed_common.MbedCommon.refresh_target')
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD.flash')
    def test_parameters_are_relayed_to_pyocd(
            self, mock_flash, mock_refresh_target, mock_file_exists):
        device = {"target_id": "1"}
        mock_refresh_target.return_value = device
        mock_file_exists.return_value = True
        parameters = ['flash',
                      '--target_id', '1',
                      '--no-reset',
                      '--method', Flash.PYOCD_METHOD,
                      '--pyocd_platform', 'someplatform',
                      '--pyocd_pack', 'somepack',
                      '--pyocd_connect_mode', 'halt',
                      '-i', 'test_file.hex']

        cli = FlasherCLI(args=parameters)
        try:
            cli.execute()
        except: # pylint:disable=bare-except
            pass

        mock_flash.assert_called_once_with(
            source='test_file.hex',
            target={"target_id": "1"},
            no_reset=True,
            platform="someplatform",
            pack="somepack",
            connect_mode="halt"
        )
