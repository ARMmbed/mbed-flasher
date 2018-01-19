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
from test.test_helper import Helper
import mock
import mbed_lstools
from mbed_flasher.erase import Erase
from mbed_flasher.flashers.FlasherMbed import FlasherMbed
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_IMPLEMENTATION_MISSING
from mbed_flasher.return_codes import EXIT_CODE_MOUNT_POINT_MISSING
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_PORT_MISSING
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD

# pylint: disable=C0103
list_mbeds_ext = Helper.list_mbeds_ext
list_mbeds_eraseable = Helper.list_mbeds_eraseable
# pylint: enable=C0103

class EraseTestCase(unittest.TestCase):
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
        self.assertEqual(len(devices), len(EraseTestCase.all_devices))
        count_eraseable = len(list_mbeds_eraseable(devices))
        self.assertEqual(count_eraseable, len(EraseTestCase.erase_allowed_devices))

    def test_erase_with_none(self):
        eraser = Erase()
        ret = eraser.erase(target_id=None, method='simple')
        self.assertEqual(ret, EXIT_CODE_TARGET_ID_MISSING)

    def test_erase_with_wrong_target_id(self):
        eraser = Erase()
        ret = eraser.erase(target_id='555', method='simple')
        self.assertEqual(ret, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

    def test_erase_with_all_no_devices(self):
        with mock.patch.object(FlasherMbed, "get_available_devices") as mocked_get:
            mocked_get.return_value = []
            eraser = Erase()
            ret = eraser.erase(target_id='all', method='simple')
            self.assertEqual(ret, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

    @unittest.skipIf(all_devices == [], "no hardware attached")
    @unittest.skipIf(erase_allowed_devices != all_devices, "cannot erase all mbeds")
    def test_erase_with_all(self):
        eraser = Erase()
        ret = eraser.erase(target_id='all', method='simple')
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    @unittest.skipIf(erase_allowed_devices == [], "no erase allowed mbeds")
    def test_erase_with_target_id(self):
        eraser = Erase()
        devices = EraseTestCase.erase_allowed_devices
        ret = None
        for item in devices:
            if item['target_id']:
                ret = eraser.erase(target_id=item['target_id'], method='simple')
                break
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    @mock.patch("os.path.isfile", return_value=True)
    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    def test_erase_failed_non_supported_devices(self, _):
        with mock.patch.object(FlasherMbed, "get_available_devices") as mocked_get:
            devices = [{"target_id": "123",
                        "platform_name": "K64F",
                        "mount_point": "/mnt/k64f",
                        "serial_port": "/dev/uart"}]
            mocked_get.return_value = devices
            eraser = Erase()
            ret = None
            for item in devices:
                if item['target_id']:
                    ret = eraser.erase(target_id=item['target_id'], method='simple')
                    break
            self.assertEqual(ret, EXIT_CODE_IMPLEMENTATION_MISSING)

    @mock.patch("os.path.isfile", return_value=True)
    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    def test_erase_failed_mount_point_missing(self, _):
        with mock.patch.object(FlasherMbed, "get_available_devices") as mocked_get:
            devices = [{"target_id": "123",
                        "platform_name": "K64F",
                        "serial_port": "/dev/uart"}]
            mocked_get.return_value = devices
            eraser = Erase()
            ret = None
            for item in devices:
                if item['target_id']:
                    ret = eraser.erase(target_id=item['target_id'], method='simple')
                    break
            self.assertEqual(ret, EXIT_CODE_MOUNT_POINT_MISSING)

    @mock.patch("os.path.isfile", return_value=True)
    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    def test_erase_failed_serial_port_missing(self, _):
        with mock.patch.object(FlasherMbed, "get_available_devices") as mocked_get:
            devices = [{"target_id": "123",
                        "platform_name": "K64F",
                        "mount_point": "/mnt/k64f"}]
            mocked_get.return_value = devices
            eraser = Erase()
            ret = None
            for item in devices:
                if item['target_id']:
                    ret = eraser.erase(target_id=item['target_id'], method='simple')
                    break
            self.assertEqual(ret, EXIT_CODE_SERIAL_PORT_MISSING)

    @unittest.skipIf(erase_allowed_devices == [], "no hardware attached")
    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    def test_erase_failed_non_supported_method(self):
        devices = EraseTestCase.erase_allowed_devices
        eraser = Erase()
        ret = None
        for item in devices:
            if item['target_id']:
                ret = eraser.erase(target_id=item['target_id'], method='unknown')
                break
        self.assertEqual(ret, EXIT_CODE_MISUSE_CMD)

    @unittest.skipIf(all_devices == [], "no hardware attached")
    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    def test_erase_with_target_id_no_reset(self):
        devices = EraseTestCase.erase_allowed_devices
        eraser = Erase()
        ret = None
        for item in devices:
            if item['target_id']:
                ret = eraser.erase(target_id=item['target_id'],
                                   method='simple',
                                   no_reset=True)
                break
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    @unittest.skipIf(erase_allowed_devices == [], "no erase allowed hardware attached")
    def test_erase_with_target_id_list(self):
        devices = EraseTestCase.erase_allowed_devices
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
