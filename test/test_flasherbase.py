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
# pylint: disable=protected-access

import unittest
import sys

import mock

from mbed_flasher.flashers.FlasherBase import FlasherBase


class FlasherBaseTest(unittest.TestCase):
    @mock.patch("mbed_flasher.flash.Logger")
    def test_is_ok(self, logger):
        with self.assertRaises(NotImplementedError):
            FlasherBase.get_supported_targets()
        with self.assertRaises(NotImplementedError):
            FlasherBase.get_available_devices()
        with self.assertRaises(NotImplementedError):
            FlasherBase.can_flash("")
        with self.assertRaises(NotImplementedError):
            FlasherBase.is_executable_installed()

        base = FlasherBase(logger)
        with self.assertRaises(NotImplementedError):
            base.flash("", "", "", "")

        self.assertTrue(hasattr(FlasherBase, 'name'))
        self.assertTrue(hasattr(FlasherBase, 'executable'))
        self.assertTrue(hasattr(FlasherBase, 'supported_targets'))

        self.assertTrue(hasattr(base, '_start_and_wait_flash'))
        self.assertTrue(hasattr(base, '_flash_run'))

    @mock.patch("mbed_flasher.flash.Logger")
    def test_start_and_wait_flash_executes(self, logger):
        base = FlasherBase(logger)
        command = """
import sys
sys.stdout.write("asd")
        """
        args = ["python", "-uc", command]
        returncode, output = base._start_and_wait_flash(args, "")
        self.assertEqual(returncode, 0)
        self.assertEqual(output, b"asd")

    @mock.patch("mbed_flasher.flash.Logger")
    def test_start_and_wait_flash_detect_fail(self, logger):
        base = FlasherBase(logger)
        command = """
import sys
sys.stdout.write("asd")
sys.exit(1)
        """
        args = ["python", "-uc", command]
        returncode, output = base._start_and_wait_flash(args, "")
        self.assertEqual(returncode, 1)
        self.assertEqual(output, b"asd")

    @mock.patch("mbed_flasher.flash.Logger")
    def test_start_and_wait_flash_timeout_sigterm(self, logger):
        FlasherBase.FLASH_TIMEOUT = 0.5
        base = FlasherBase(logger)
        command = """
import sys
import time
sys.stdout.write("asd")
sys.stdout.flush()
time.sleep(2)
        """
        args = ["python", "-uc", command]
        returncode, output = base._start_and_wait_flash(args, "")
        if sys.platform.startswith("win"):
            self.assertEqual(returncode, 1)
        else:
            self.assertEqual(returncode, -15)
        self.assertEqual(output, b"asd")

    # No signal in windows.
    @unittest.skipIf(sys.platform.startswith("win"), 'require windows')
    @mock.patch("mbed_flasher.flash.Logger")
    def test_start_and_wait_flash_timeout_sigkill(self, logger):
        FlasherBase.FLASH_TIMEOUT = 0.5
        FlasherBase.PROCESS_END_TIMEOUT = 0.5
        base = FlasherBase(logger)
        command = """
import signal
import sys
import time
def handler(s, f):
  sys.stdout.write("asd")
  sys.stdout.flush()
  time.sleep(2)
signal.signal(signal.SIGTERM, handler)
time.sleep(2)
        """
        args = ["python", "-uc", command]
        returncode, output = base._start_and_wait_flash(args, "")
        if sys.platform.startswith("win"):
            self.assertEqual(returncode, 1)
        else:
            self.assertEqual(returncode, -9)
        self.assertEqual(output, b"asd")


if __name__ == '__main__':
    unittest.main()
