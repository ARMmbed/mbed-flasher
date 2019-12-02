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

    def setUp(self):
        logging.disable(logging.CRITICAL)
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()
        all_devices = Helper.list_mbeds_ext()
        erase_allowed_devices = Helper.list_mbeds_eraseable(all_devices)
        for dev in erase_allowed_devices:
            if dev['platform_name'] == 'K64F':
                self.target_id = dev['target_id']
                break

    def tearDown(self):
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def test_erase_with_target_id(self):
        ret = Erase().erase(target_id=self.target_id, method='msd')

        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    def test_erase_failed_non_supported_method(self):
        with self.assertRaises(EraseError) as cm:
            Erase().erase(target_id=self.target_id, method='unknown')

        self.assertEqual(cm.exception.return_code, EXIT_CODE_MISUSE_CMD)

    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    def test_erase_with_target_id_no_reset(self):
        ret = Erase().erase(target_id=self.target_id,
                            method='pyocd',
                            pyocd_platform='k64f',
                            no_reset=True)
        self.assertEqual(ret, EXIT_CODE_SUCCESS)


if __name__ == '__main__':
    unittest.main()
