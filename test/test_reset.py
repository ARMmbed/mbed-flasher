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
try:
    from StringIO import StringIO
except ImportError:
    # python 3 compatible import
    from io import StringIO
from test.test_helper import Helper
import mock
import mbed_lstools
from mbed_flasher.reset import Reset
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE


class ResetTestCase(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """
    mbeds = mbed_lstools.create()

    def setUp(self):
        logging.disable(logging.CRITICAL)
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def tearDown(self):
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def test_reset_with_none(self):
        resetter = Reset()
        ret = resetter.reset(target_id=None, method='simple')
        self.assertEqual(ret, EXIT_CODE_TARGET_ID_MISSING)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_with_wrong_target_id(self, mock_stdout):
        resetter = Reset()
        ret = resetter.reset(target_id='555', method='simple')
        self.assertEqual(ret, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)
        if mock_stdout:
            self.assertEqual(mock_stdout.getvalue(),
                             'Could not map given target_id(s) to available devices\n')

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_with_all_no_devices(self, mock_stdout):
        resetter = Reset()
        ret = resetter.reset(target_id='all', method='simple')
        self.assertEqual(ret, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)
        if mock_stdout:
            self.assertEqual(mock_stdout.getvalue(),
                             'Could not map given target_id(s) to available devices\n')

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_reset_with_all(self):
        resetter = Reset()
        ret = resetter.reset(target_id='all', method='simple')
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_reset_with_target_id(self):
        mbeds = mbed_lstools.create()
        devices = mbeds.list_mbeds()
        resetter = Reset()
        ret = None
        for item in devices:
            if item['target_id']:
                ret = resetter.reset(target_id=item['target_id'], method='simple')
                break
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_reset_with_target_id_list(self):
        mbeds = mbed_lstools.create()
        devices = mbeds.list_mbeds()
        resetter = Reset()
        ret = None
        for item in devices:
            if item['target_id']:
                ret = resetter.reset(target_id=[item['target_id']], method='simple')
                break
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    #For some reason a bunch of tracebacks on usb.core langid problems.
    # @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    # @mock.patch('sys.stdout', new_callable=StringIO)
    # def test_reset_with_all_pyocd(self, mock_stdout):
    #     resetter = Reset()
    #     ret = resetter.reset(target_id='all', method='pyocd')
    #     self.assertEqual(ret, EXIT_CODE_SUCCESS)


if __name__ == '__main__':
    unittest.main()
