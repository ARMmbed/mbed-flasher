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
# pylint: disable=missing-docstring
# pylint: disable=invalid-name

import sys
import unittest

import mock

from mbed_flasher.common import FlashError
from mbed_flasher.flashers.FlasherBase import FlasherBase
from mbed_flasher.flashers.FlasherST import FlasherSTLink
from mbed_flasher.return_codes import EXIT_CODE_FLASH_FAILED


class FlasherSTLinkTest(unittest.TestCase):
    def test_is_ok(self):
        self.assertTrue(issubclass(FlasherSTLink, FlasherBase))

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_supported_targets(self, logger):
        stlink = FlasherSTLink(logger)
        targets = stlink.get_supported_targets()
        self.assertTrue(isinstance(targets, list))

        FlasherSTLink.supported_targets = []
        self.assertTrue(isinstance(stlink.get_supported_targets(), list))

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_devices(self, logger):
        stlink = FlasherSTLink(logger)
        targets = stlink.get_available_devices()
        self.assertTrue(isinstance(targets, list))

    @mock.patch("mbed_flasher.flash.Logger")
    def test_can_flash_when_device_type_matches(self, logger):
        stlink = FlasherSTLink(logger)
        self.assertTrue(stlink.can_flash({"device_type": FlasherSTLink.name}))

    @mock.patch("mbed_flasher.flash.Logger")
    def test_can_flash_returns_false(self, logger):
        stlink = FlasherSTLink(logger)
        self.assertFalse(stlink.can_flash({}))
        self.assertFalse(stlink.can_flash({"device_type": "daplink"}))

    @mock.patch("distutils.spawn.find_executable")
    @mock.patch("mbed_flasher.flash.Logger")
    def test_is_executable_installed_return_true_when_found(self, logger, mock_find):
        mock_find.return_value = "some/path"

        jlink = FlasherSTLink(logger)
        self.assertEqual(jlink.is_executable_installed(), True)

    @mock.patch("distutils.spawn.find_executable")
    @mock.patch("mbed_flasher.flash.Logger")
    def test_is_executable_installed_return_false_when_not_found(self, logger, mock_find):
        mock_find.return_value = None

        stlink = FlasherSTLink(logger)
        self.assertEqual(stlink.is_executable_installed(), False)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_flash_constructs_correct_args(self, logger):
        stlink = FlasherSTLink(logger)
        executable = "ST-LINK_CLI.exe" if sys.platform.startswith("win") else "ST-LINK_CLI"
        expected_args = [executable,
                         "-c", "SN=test_target_id",
                         "-P", "test_source",
                         "0x08000000",
                         "-V"]

        # pylint: disable=unused-argument
        def mock_start(args, exe):
            self.assertEqual(args[0], expected_args[0])
            self.assertEqual(args[1], expected_args[1])
            self.assertEqual(args[2], expected_args[2])
            self.assertEqual(args[3], expected_args[3])
            self.assertEqual(args[4], expected_args[4])
            self.assertEqual(args[5], expected_args[5])
            self.assertEqual(args[6], expected_args[6])
            return 0, ""

        # pylint: disable=protected-access
        stlink._start_and_wait_flash = mock_start

        target = {
            "stlink_device_name": "test_stlink",
            "target_id": "test",
            "target_id_usb_id": "test_target_id"
        }
        returncode = stlink.flash("test_source", target, "", False)
        self.assertEqual(returncode, 0)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_flash_returns_non_zero_when_target_is_invalid(self, logger):
        stlink = FlasherSTLink(logger)

        target = {"target_id": "test_target_id"}
        with self.assertRaises(FlashError) as cm:
            stlink.flash("test_source", target, "", False)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FLASH_FAILED)

        target = {"stlink_device_name": "test_stlink"}
        with self.assertRaises(FlashError) as cm:
            stlink.flash("test_source", target, "", False)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FLASH_FAILED)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_flash_returns_non_zero_when_process_fails(self, logger):
        stlink = FlasherSTLink(logger)

        # pylint: disable=unused-argument
        def mock_start(args, exe):
            return 1, ""

        # pylint: disable=protected-access
        stlink._start_and_wait_flash = mock_start

        target = {"stlink_device_name": "test_stlink", "target_id": "test_target_id"}
        with self.assertRaises(FlashError) as cm:
            stlink.flash("test_source", target, "", False)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FLASH_FAILED)

if __name__ == '__main__':
    unittest.main()
