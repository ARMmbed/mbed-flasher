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

import logging
import unittest
from test.hardware.test_helper import Helper
import six
try:
    from StringIO import StringIO
except ImportError:
    # python 3 compatible import
    from io import StringIO
import mock
import mbed_lstools

from mbed_flasher.common import GeneralFatalError
from mbed_flasher.main import FlasherCLI
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_DEVICE


class MainTestCaseHW(unittest.TestCase):
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
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def tearDown(self):
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def test_parser_invalid(self):
        with self.assertRaises(SystemExit) as context:
            FlasherCLI()
        self.assertEqual(context.exception.code, EXIT_CODE_MISUSE_CMD)

    # test name is meaningful
    # pylint: disable=invalid-name
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_wrong_tid_with_device(self, mock_stdout):
        fcli = FlasherCLI(["reset", "--tid", "555"])
        with self.assertRaises(GeneralFatalError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_DEVICE)
        six.assertRegex(self, mock_stdout.getvalue(),
                        r"Could not find given target_id from attached devices"
                        r"\nAvailable target_ids:\n\[u?(\'[0-9a-fA-F]+\')"
                        r"(,\su?\'[0-9a-fA-F]+\')*\]",
                        "Regex match failed")

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_wrong_tid_with_device(self, mock_stdout):
        fcli = FlasherCLI(["erase", "--tid", "555"])
        with self.assertRaises(GeneralFatalError) as cm:
            fcli.execute()

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_DEVICE)
        six.assertRegex(self, mock_stdout.getvalue(),
                        r"Could not find given target_id from attached devices"
                        r"\nAvailable target_ids:\n\[u?(\'[0-9a-fA-F]+\')"
                        r"(,\su?\'[0-9a-fA-F]+\')*\]",
                        "Regex match failed")

if __name__ == '__main__':
    unittest.main()
