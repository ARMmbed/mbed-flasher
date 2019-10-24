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
# pylint:disable=too-few-public-methods
# pylint:disable=unused-argument

import logging
import unittest
import os
from test.hardware.test_helper import Helper

try:
    from StringIO import StringIO
except ImportError:
    # python 3 compatible import
    from io import StringIO
import platform

import mock
import mbed_lstools

from mbed_flasher.common import FlashError
from mbed_flasher.flash import Flash
from mbed_flasher.flashers.FlasherMbed import FlasherMbed
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_FILE_MISSING
from mbed_flasher.return_codes import EXIT_CODE_FILE_STILL_PRESENT
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_USER_ERROR


class FlashTestCaseHW(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """
    mbeds = mbed_lstools.create()
    bin_path = os.path.join('test', 'helloworld.bin')

    def setUp(self):
        logging.disable(logging.CRITICAL)
        helper = Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM'])
        helper.clear()
        helper.reset()

    def tearDown(self):
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def test_run_file_does_not_exist(self):
        flasher = Flash()
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        with self.assertRaises(FlashError) as context:
            flasher.flash(build='file.bin', target_id=targets[0], method='simple')

        self.assertEqual(context.exception.return_code, EXIT_CODE_FILE_MISSING)

    def test_hw_flash(self):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        target_id = None
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'target_id' in target:
                    target_id = target['target_id']
                    break

        flasher = Flash()
        ret = flasher.flash(build=self.bin_path,
                            target_id=target_id,
                            method='simple')
        self.assertEqual(ret, EXIT_CODE_SUCCESS)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_run_fail_file(self, mock_stdout):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        mount_point = None
        target_to_test = None
        fail_txt_path = os.path.join('test', 'failing.txt')
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'target_id' in target and 'mount_point' in target:
                    target_to_test = target
                    mount_point = target['mount_point']
                    break

        with open(fail_txt_path, 'w') as new_file:
            new_file.write("0000000000000000000000000000000000")

        with self.assertRaises(FlashError) as context:
            flasher = FlasherMbed()
            flasher.flash(source=fail_txt_path, target=target_to_test,
                          method='simple', no_reset=False)

        if platform.system() == 'Windows':
            os.system('del %s' % os.path.join(mount_point, 'failing.txt'))
            os.system('del %s' % os.path.join(os.getcwd(), fail_txt_path))
        else:
            os.system('rm %s' % os.path.join(mount_point, 'failing.txt'))
            os.system('rm %s' % os.path.join(os.getcwd(), fail_txt_path))

        self.assertEqual(context.exception.return_code, EXIT_CODE_FILE_STILL_PRESENT)

    # PyOCD does not have verification for .bin files.
    # Success is expected as K64F moves to PyOCD.
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_run_fail_binary(self, mock_stdout):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        target_id = None
        fail_bin_path = os.path.join('test', 'fail.bin')
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'target_id' in target and 'mount_point' in target:
                    target_id = target['target_id']
                    break

        with open(fail_bin_path, 'w') as new_file:
            new_file.write("0000000000000000000000000000000000")

        flasher = Flash()
        return_code = flasher.flash(build=fail_bin_path, target_id=target_id, method='simple')
        self.assertEqual(return_code, EXIT_CODE_SUCCESS)

    # NUCLEO_F429ZI is flashed with PyOCD
    @mock.patch('sys.stdout', new_callable=StringIO)
    @unittest.skipIf(platform.system() != 'Linux', 'require linux')
    def test_run_fail_binary_pyocd(self, mock_stdout):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        target_id = None
        fail_bin_path = os.path.join('test', 'corrupt_app_NUCLEO_F429ZI.hex')
        for target in targets:
            if target['platform_name'] == 'NUCLEO_F429ZI':
                if 'target_id' in target:
                    target_id = target['target_id']
                    break

        with self.assertRaises(FlashError) as context:
            flasher = Flash()
            flasher.flash(build=fail_bin_path, target_id=target_id)

        self.assertEqual(context.exception.return_code, EXIT_CODE_PYOCD_USER_ERROR)


if __name__ == '__main__':
    unittest.main()
