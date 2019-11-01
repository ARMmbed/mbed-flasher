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
# pylint:disable=missing-docstring
# pylint:disable=invalid-name
# pylint:disable=unused-argument

import os
import logging
import unittest
import re
import sys
try:
    from StringIO import StringIO
except ImportError:
    # python 3 compatible import
    from io import StringIO
import mock
import mbed_lstools

from mbed_flasher.common import FlashError, EraseError, ResetError
from mbed_flasher.main import FlasherCLI
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_FILE_MISSING
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE


class MainTestCase(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """

    mbeds = mbed_lstools.create()

    def setUp(self):
        self.logging_patcher = mock.patch("mbed_flasher.main.logging")
        mock_logging = self.logging_patcher.start()
        mock_logging.getLogger = \
            mock.MagicMock(return_value=mock.Mock(spec=logging.Logger))
        # Mock logging
        # pylint: disable=no-member
        mock_logging.disable(logging.CRITICAL)

    def test_parser_invalid(self):
        with self.assertRaises(SystemExit) as context:
            FlasherCLI()

        self.assertEqual(context.exception.code, EXIT_CODE_MISUSE_CMD)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main(self, mock_stdout):
        with self.assertRaises(SystemExit) as context:
            FlasherCLI([])

        self.assertEqual(context.exception.code, EXIT_CODE_MISUSE_CMD)

    # argparse version action prints to stderr before 3.4 version
    # https://bugs.python.org/issue18920
    std_channel = 'sys.stderr'
    if sys.version_info.major == 3 and sys.version_info.minor >= 4:
        std_channel = 'sys.stdout'

    @mock.patch(std_channel, new_callable=StringIO)
    def test_main_version(self, mock_std):
        with self.assertRaises(SystemExit) as context:
            FlasherCLI(["--version"])

        self.assertEqual(context.exception.code, EXIT_CODE_SUCCESS)
        r_match = re.compile(r"^\d+\.\d+\.\d+$")
        value = mock_std.getvalue()
        self.assertTrue(r_match.match(value))

    @mock.patch(std_channel, new_callable=StringIO)
    def test_main_verboses(self, mock_stderr):
        with self.assertRaises(SystemExit) as context:
            FlasherCLI(["-v", "--version"])
        self.assertEqual(context.exception.code, EXIT_CODE_SUCCESS)
        r_match = re.compile(r"^\d+\.\d+\.\d+$")
        value = mock_stderr.getvalue()
        self.assertTrue(r_match.match(value))

    def test_main_sets_verbosity(self):
        # pylint: disable=no-member
        fcli = FlasherCLI(["-v", "flash", "-i", "None", "--tid", "target"])
        self.assertEqual(fcli.args.verbose, 1)
        fcli.console_handler.setLevel.assert_called_with("WARNING")

        fcli = FlasherCLI(["-vv", "flash", "-i", "None", "--tid", "target"])
        self.assertEqual(fcli.args.verbose, 2)
        fcli.console_handler.setLevel.assert_called_with("INFO")

        fcli = FlasherCLI(["-vvv", "flash", "-i", "None", "--tid", "target"])
        self.assertEqual(fcli.args.verbose, 3)
        fcli.console_handler.setLevel.assert_called_with("DEBUG")

    def test_file_does_not_exist(self):
        fcli = FlasherCLI(["flash", "-i", "None", "--tid", "target"])
        with self.assertRaises(FlashError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FILE_MISSING)
        self.assertEqual(cm.exception.message, 'Could not find given file: None')

    def test_file_not_given(self):
        fcli = FlasherCLI(["flash", "-i", None, "--tid", "target"])
        with self.assertRaises(FlashError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FILE_MISSING)
        self.assertEqual(cm.exception.message, 'File to be flashed was not given')

    def test_tid_missing(self):
        bin_path = os.path.join('test', 'helloworld.bin')
        fcli = FlasherCLI(["flash", "-i", bin_path])
        with self.assertRaises(FlashError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_TARGET_ID_MISSING)
        self.assertEqual(cm.exception.message, "Target_id is missing")

    @mock.patch("time.sleep", return_value=None)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_wrong_tid(self, mock_stdout, mock_sleep):
        bin_path = os.path.join('test', 'helloworld.bin')
        fcli = FlasherCLI(["flash", "-i", bin_path, "--tid", "555"])
        with self.assertRaises(FlashError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)
        self.assertEqual(cm.exception.message, "Did not find target: 555")

    def test_reset_tid_missing(self):
        fcli = FlasherCLI(["reset"])
        with self.assertRaises(ResetError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_TARGET_ID_MISSING)
        self.assertEqual(cm.exception.message, "target_id is missing")

    @mock.patch("time.sleep", return_value=None)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_wrong_tid(self, mock_stdout, mock_sleep):
        fcli = FlasherCLI(["reset", "--tid", "555"])
        with self.assertRaises(ResetError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)
        self.assertEqual(cm.exception.message, "Did not find target: 555")

    def test_erase_tid_missing(self):
        fcli = FlasherCLI(["erase"])
        with self.assertRaises(EraseError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_TARGET_ID_MISSING)
        self.assertEqual(cm.exception.message, "target_id is missing")

    @mock.patch("time.sleep", return_value=None)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_wrong_tid(self, mock_stdout, mock_sleep):
        fcli = FlasherCLI(["erase", "--tid", "555"])
        with self.assertRaises(EraseError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)
        self.assertEqual(cm.exception.message, "Did not find target: 555")


if __name__ == '__main__':
    unittest.main()
