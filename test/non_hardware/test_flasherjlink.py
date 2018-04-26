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
from mbed_flasher.flashers.FlasherJLink import FlasherJLink
from mbed_flasher.return_codes import EXIT_CODE_FLASH_FAILED


class FlasherJLinkTest(unittest.TestCase):
    def test_is_ok(self):
        self.assertTrue(issubclass(FlasherJLink, FlasherBase))

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_supported_targets(self, logger):
        jlink = FlasherJLink(logger)
        targets = jlink.get_supported_targets()
        self.assertTrue(isinstance(targets, list))

        FlasherJLink.supported_targets = []
        self.assertTrue(jlink.get_supported_targets(), [])

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_devices(self, logger):
        jlink = FlasherJLink(logger)
        targets = jlink.get_available_devices()
        self.assertTrue(isinstance(targets, list))

    @mock.patch("mbed_flasher.flash.Logger")
    def test_can_flash_when_device_type_matches(self, logger):
        jlink = FlasherJLink(logger)
        self.assertTrue(jlink.can_flash({"device_type": FlasherJLink.name}))

    @mock.patch("mbed_flasher.flash.Logger")
    def test_can_flash_returns_false(self, logger):
        jlink = FlasherJLink(logger)
        self.assertFalse(jlink.can_flash({}))
        self.assertFalse(jlink.can_flash({"device_type": "daplink"}))

    @mock.patch("distutils.spawn.find_executable")
    @mock.patch("mbed_flasher.flash.Logger")
    def test_is_executable_installed_return_true_when_found(self, logger, mock_find):
        mock_find.return_value = "some/path"

        jlink = FlasherJLink(logger)
        self.assertEqual(jlink.is_executable_installed(), True)

    @mock.patch("distutils.spawn.find_executable")
    @mock.patch("mbed_flasher.flash.Logger")
    def test_is_executable_installed_return_false_when_not_found(self, logger, mock_find):
        mock_find.return_value = None

        jlink = FlasherJLink(logger)
        self.assertEqual(jlink.is_executable_installed(), False)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_flash_constructs_correct_args(self, logger):
        jlink = FlasherJLink(logger)
        executable = "JLink.exe" if sys.platform.startswith("win") else "JLinkExe"
        expected_args = [executable,
                         "-if", "swd",
                         "-speed", "auto",
                         "-device", "test_jlink",
                         "-SelectEmuBySN", "test_target_id",
                         "-commanderscript", "not_tested"]

        # pylint: disable=unused-argument
        def mock_start(args, exe):
            self.assertEqual(args[0], expected_args[0])
            self.assertEqual(args[1], expected_args[1])
            self.assertEqual(args[2], expected_args[2])
            self.assertEqual(args[3], expected_args[3])
            self.assertEqual(args[4], expected_args[4])
            self.assertEqual(args[5], expected_args[5])
            self.assertEqual(args[6], expected_args[6])
            self.assertEqual(args[7], expected_args[7])
            self.assertEqual(args[8], expected_args[8])
            self.assertEqual(args[9], expected_args[9])
            return 0, ""

        # pylint: disable=protected-access
        jlink._start_and_wait_flash = mock_start

        target = {"jlink_device_name": "test_jlink", "target_id": "test_target_id"}
        returncode = jlink.flash("test_source", target, "", False)
        self.assertEqual(returncode, 0)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_flash_returns_non_zero_when_target_is_invalid(self, logger):
        jlink = FlasherJLink(logger)

        target = {"target_id": "test_target_id"}
        with self.assertRaises(FlashError) as cm:
            jlink.flash("test_source", target, "", False)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FLASH_FAILED)

        target = {"jlink_device_name": "test_jlink"}
        with self.assertRaises(FlashError) as cm:
            jlink.flash("test_source", target, "", False)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FLASH_FAILED)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_flash_returns_non_zero_when_process_fails(self, logger):
        jlink = FlasherJLink(logger)

        # pylint: disable=unused-argument
        def mock_start(args, exe):
            return 1, ""

        # pylint: disable=protected-access
        jlink._start_and_wait_flash = mock_start

        target = {"jlink_device_name": "test_jlink", "target_id": "test_target_id"}
        with self.assertRaises(FlashError) as cm:
            jlink.flash("test_source", target, "", False)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FLASH_FAILED)

    def test_write_file_contents(self):
        class MockFile(object):
            def __init__(self):
                self._data = b""

            def write(self, data):
                self._data += data

            def flush(self):
                pass

        mock_file = MockFile()
        # pylint: disable=protected-access
        FlasherJLink._write_file_contents(mock_file, "binary.bin", False)
        self.assertEqual(mock_file._data, b"erase\nloadfile binary.bin\nr\ng\nexit\n")
        mock_file = MockFile()
        # pylint: disable=protected-access
        FlasherJLink._write_file_contents(mock_file, "binary.bin", True)
        self.assertEqual(mock_file._data, b"erase\nloadfile binary.bin\nexit\n")

if __name__ == '__main__':
    unittest.main()
