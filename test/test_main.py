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
from StringIO import StringIO
import mock
import mbed_lstools
from mbed_flasher.main import FlasherCLI

FLASHER_VERSION = '0.4.2'


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

    def tearDown(self):
        pass

    def test_parser_invalid(self):
        with self.assertRaises(SystemExit) as context:
            FlasherCLI()
        self.assertEqual(context.exception.code, 2)

    # def test_parser_valid(self):
    #    t = cmd_parser_setup()
    #    self.assertIsInstance(t, tuple)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main(self, mock_stdout):
        with self.assertRaises(SystemExit) as context:
            FlasherCLI([])
        self.assertEqual(context.exception.code, 2)
        if mock_stdout:
            pass

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main_version(self, mock_stdout):
        fcli = FlasherCLI(["version"])
        self.assertEqual(fcli.execute(), 0)
        self.assertEqual(mock_stdout.getvalue(), FLASHER_VERSION + '\n')
        #self.assertRegexpMatches(mock_stdout.getvalue(), r"^\d+\.\d+\.\d+$")

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main_verboses(self, mock_stdout):
        fcli = FlasherCLI(["-v", "version"])
        self.assertEqual(fcli.execute(), 0)
        self.assertIsNot(len("\n".split(mock_stdout.getvalue())), 0)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_file_does_not_exist(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", "None"])
        self.assertEqual(fcli.execute(), 5)
        self.assertEqual(mock_stdout.getvalue(), 'Could not find given file: None\n')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_file_not_given(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", None])
        self.assertEqual(fcli.execute(), 5)
        self.assertEqual(mock_stdout.getvalue(), 'File is missing\n')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_wrong_platform(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", "test/helloworld.bin", "-t", "K65G"])
        self.assertEqual(fcli.execute(), 10)
        self.assertIn("Not supported platform: K65G", mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_tid_missing(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", "test/helloworld.bin", "-t", "K64F"])
        self.assertEqual(fcli.execute(), 15)
        self.assertEqual(mock_stdout.getvalue(), "Target_id is missing\n")

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_wrong_tid(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", "test/helloworld.bin",
                           "--tid", "555", "-t", "K64F"])
        self.assertEqual(fcli.execute(), 20)
        self.assertEqual(mock_stdout.getvalue(), "Could not find any connected device\n")

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_tid_missing(self, mock_stdout):
        fcli = FlasherCLI(["reset"])
        self.assertEqual(fcli.execute(), 15)
        self.assertEqual(mock_stdout.getvalue(), "Target_id is missing\n")

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_wrong_tid(self, mock_stdout):
        fcli = FlasherCLI(["reset", "--tid", "555"])
        self.assertEqual(fcli.execute(), 20)
        self.assertEqual(mock_stdout.getvalue(), "Could not find any connected device\n")

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_all(self, mock_stdout):
        fcli = FlasherCLI(["reset", "--tid", "all"])
        self.assertEqual(fcli.execute(), 20)
        self.assertEqual(mock_stdout.getvalue(), "Could not find any connected device\n")

    # test name is meaningful
    # pylint: disable=invalid-name
    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_wrong_tid_with_device(self, mock_stdout):
        fcli = FlasherCLI(["reset", "--tid", "555"])
        self.assertEqual(fcli.execute(), 25)
        self.assertRegexpMatches(mock_stdout.getvalue(),
                                 r"Could not find given target_id from attached devices"
                                 r"\nAvailable target_ids:\n\[(\'[0-9a-fA-F]+\')"
                                 r"(,\s\'[0-9a-fA-F]+\')*\]",
                                 "Regex match failed")

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_tid_missing(self, mock_stdout):
        fcli = FlasherCLI(["erase"])
        self.assertEqual(fcli.execute(), 15)
        self.assertEqual(mock_stdout.getvalue(), "Target_id is missing\n")

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_wrong_tid(self, mock_stdout):
        fcli = FlasherCLI(["erase", "--tid", "555"])
        self.assertEqual(fcli.execute(), 20)
        self.assertEqual(mock_stdout.getvalue(), "Could not find any connected device\n")

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_wrong_tid_with_device(self, mock_stdout):
        fcli = FlasherCLI(["erase", "--tid", "555"])
        self.assertEqual(fcli.execute(), 25)
        self.assertRegexpMatches(mock_stdout.getvalue(),
                                 r"Could not find given target_id from attached devices"
                                 r"\nAvailable target_ids:\n\[(\'[0-9a-fA-F]+\')"
                                 r"(,\s\'[0-9a-fA-F]+\')*\]",
                                 "Regex match failed")

if __name__ == '__main__':
    unittest.main()
