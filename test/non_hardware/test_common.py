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
# pylint: disable=unused-argument

import os
try:
    from StringIO import StringIO
except ImportError:
    # python 3 compatible import
    from io import StringIO
import unittest
import mock

from mbed_flasher.common import FlashError, EraseError,\
    ResetError, check_is_file_flashable
from mbed_flasher.return_codes import EXIT_CODE_FILE_MISSING
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_USER_ERROR


# pylint: disable=too-few-public-methods
class Flasher(object):
    def __init__(self, result):
        self._result = result
        self.call_count = 0

    def get_available_devices(self):
        self.call_count += 1
        return self._result


class CheckIsFileFlashableTestCase(unittest.TestCase):
    @mock.patch("mbed_flasher.flash.Logger")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_raises_when_file_path_is_invalid(self, mock_stdout, logger):
        with self.assertRaises(FlashError) as cm:
            check_is_file_flashable(logger, "")

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FILE_MISSING)

        with self.assertRaises(FlashError) as cm:
            check_is_file_flashable(logger, None)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FILE_MISSING)

    @mock.patch("mbed_flasher.flash.Logger")
    @mock.patch('os.path.isfile', return_value=True)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_allows_good_file_path(self, mock_stdout, mock_isfile, logger):
        self.assertEqual(check_is_file_flashable(logger, "./test.bin"), None)

    @mock.patch("mbed_flasher.flash.Logger")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_raises_when_file_does_not_exist(self, mock_stdout, logger):
        with self.assertRaises(FlashError) as cm:
            check_is_file_flashable(logger, "should/not/exist")

        self.assertEqual(cm.exception.return_code, EXIT_CODE_FILE_MISSING)

    @mock.patch("mbed_flasher.flash.Logger")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_allows_existing_file(self, mock_stdout, logger):
        file_path = os.path.join("test", "helloworld.bin")
        self.assertEqual(check_is_file_flashable(logger, file_path), None)

    @mock.patch("mbed_flasher.flash.Logger")
    @mock.patch('os.path.isfile', return_value=True)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_raises_when_file_has_bad_extension(self, mock_stdout, mock_isfile, logger):
        with self.assertRaises(FlashError) as cm:
            check_is_file_flashable(logger, "test.heh")

        self.assertEqual(cm.exception.return_code, EXIT_CODE_DAPLINK_USER_ERROR)

    @mock.patch("mbed_flasher.flash.Logger")
    @mock.patch('os.path.isfile', return_value=True)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_allows_extensions(self, mock_stdout, mock_isfile, logger):
        for ext in ["bin", "hex", "act", "cfg", "BIN", "HEX", "ACT", "CFG"]:
            self.assertEqual(check_is_file_flashable(logger, "test.{}".format(ext)), None)


class FlashErrorTestCase(unittest.TestCase):
    def test_can_be_risen(self):
        with self.assertRaises(FlashError) as cm:
            raise FlashError(message="test", return_code=0)

        self.assertEqual(cm.exception.message, "test")
        self.assertEqual(cm.exception.return_code, 0)


class EraseErrorTestCase(unittest.TestCase):
    def test_can_be_risen(self):
        with self.assertRaises(FlashError) as cm:
            raise EraseError(message="test", return_code=0)

        self.assertEqual(cm.exception.message, "test")
        self.assertEqual(cm.exception.return_code, 0)


class ResetErrorTestCase(unittest.TestCase):
    def test_can_be_risen(self):
        with self.assertRaises(ResetError) as cm:
            raise ResetError(message="test", return_code=0)

        self.assertEqual(cm.exception.message, "test")
        self.assertEqual(cm.exception.return_code, 0)


if __name__ == '__main__':
    unittest.main()
