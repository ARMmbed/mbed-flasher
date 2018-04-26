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
import mbed_lstools

from mbed_flasher.common import EraseError
from mbed_flasher.erase import Erase
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD

# pylint: disable=C0103
list_mbeds_ext = Helper.list_mbeds_ext
list_mbeds_eraseable = Helper.list_mbeds_eraseable
# pylint: enable=C0103


class EraseTestCaseHW(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """
    mbeds = mbed_lstools.create()

    all_devices = Helper.list_mbeds_ext()
    erase_allowed_devices = Helper.list_mbeds_eraseable(all_devices)

    def setUp(self):
        logging.disable(logging.CRITICAL)
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def tearDown(self):
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()
        devices = list_mbeds_ext()
        # validates that there is still all devices than was originally
        self.assertEqual(len(devices), len(EraseTestCaseHW.all_devices))
        count_eraseable = len(list_mbeds_eraseable(devices))
        self.assertEqual(count_eraseable, len(EraseTestCaseHW.erase_allowed_devices))

    def test_erase_with_all(self):
        eraser = Erase()
        ret = eraser.erase(target_id='all', method='simple')
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    def test_erase_with_target_id(self):
        eraser = Erase()
        devices = EraseTestCaseHW.erase_allowed_devices
        ret = None
        for item in devices:
            if item['target_id']:
                ret = eraser.erase(target_id=item['target_id'], method='simple')
                break

        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    def test_erase_failed_non_supported_method(self):
        devices = EraseTestCaseHW.erase_allowed_devices
        eraser = Erase()
        for item in devices:
            if item['target_id']:
                with self.assertRaises(EraseError) as cm:
                    eraser.erase(target_id=item['target_id'], method='unknown')

                self.assertEqual(cm.exception.return_code, EXIT_CODE_MISUSE_CMD)
                break

    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    def test_erase_with_target_id_no_reset(self):
        devices = EraseTestCaseHW.erase_allowed_devices
        eraser = Erase()
        ret = None
        for item in devices:
            if item['target_id']:
                ret = eraser.erase(target_id=item['target_id'],
                                   method='simple',
                                   no_reset=True)
                break
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    def test_erase_with_target_id_list(self):
        devices = EraseTestCaseHW.erase_allowed_devices
        eraser = Erase()
        ret = None
        for item in devices:
            if item['target_id']:
                ret = eraser.erase(target_id=[item['target_id']], method='simple')
                break
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

        # For some reason a bunch of tracebacks on usb.core langid problems.
        # @unittest.skipIf(all_devices == [], "no hardware attached")
        # def test_erase_with_all_pyocd(self):
        #    eraser = Erase()
        #    ret = eraser.erase(target_id='all', method='pyocd')
        #    self.assertEqual(ret, EXIT_CODE_SUCCESS)


if __name__ == '__main__':
    unittest.main()
