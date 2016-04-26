#!/usr/bin/env python
"""
mbed SDK
Copyright (c) 2011-2015 ARM Limited

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

import logging
import unittest
import mbed_lstools
import time
import mock
from mbed_flasher.flash import Flash
from StringIO import StringIO
from mbed_flasher.flashers import AvailableFlashers

def check_two_different_boards():
    available_devices = []
    for Flasher in AvailableFlashers:
        devices = Flasher.get_available_devices()
        available_devices.extend(devices)
    found_platform = ''
    for item in available_devices:
        if not found_platform:
            found_platform = item['platform_name']
        else:
            if item['platform_name'] != found_platform:
                return True
    else:
        return False

class FlashTestCase(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """
    mbeds = mbed_lstools.create()

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        pass
    
    def test_run_file_does_not_exist(self):
        flasher = Flash()
        with self.assertRaises(SyntaxError) as cm:
            flasher.flash(build='file.bin', target_id=None, platform_name=None, device_mapping_table=False, pyocd=False)
        self.assertIn("target_id or target_name is required", cm.exception, )

    def test_run_target_id_and_platform_missing(self):
        flasher = Flash()
        ret = flasher.flash(build='file.bin', target_id=True, platform_name=False, device_mapping_table=False,
                            pyocd=False)
        self.assertEqual(ret, -5)

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    def test_run_with_file_with_target_id_all(self):
        flasher = Flash()
        ret = flasher.flash(build='test/helloworld.bin', target_id='all', platform_name=False,
                            device_mapping_table=False, pyocd=False)
        self.assertEqual(ret, -3)

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    def test_run_with_file_with_one_target_id(self):
        flasher = Flash()
        ret = flasher.flash(build='test/helloworld.bin', target_id='0240000029164e45002f0012706e0006f301000097969900',
                            platform_name=False, device_mapping_table=False, pyocd=False)
        self.assertEqual(ret, -3)

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_run_with_file_with_one_target_id_wrong_platform(self):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        target_id = None
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'target_id' in target:
                    target_id = target['target_id']
                    break
        if target_id:
            flasher = Flash()
            with self.assertRaises(NotImplementedError) as cm:
                flasher.flash(build='test/helloworld.bin', target_id=target_id, platform_name='K65G',
                              device_mapping_table=False, pyocd=False)
            self.assertIn("Platform 'K65G' is not supported by mbed-flasher", cm.exception, )

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_hw_flash(self):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        target_id = None
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'target_id' in target:
                    target_id = target['target_id']
                    break
        if target_id:
            flasher = Flash()
            ret = flasher.flash(build='test/helloworld.bin', target_id=target_id, platform_name=False,
                                device_mapping_table=False, pyocd=False)
            self.assertEqual(ret, 0)

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_run_with_file_with_all(self, mock_stdout):
        time.sleep(4)
        flasher = Flash()
        ret = flasher.flash(build='test/helloworld.bin', target_id='all', platform_name='K64F',
                            device_mapping_table=False, pyocd=False)
        self.assertEqual(ret, 0)
        if mock_stdout:
            pass

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_run_with_file_with_prefix(self, mock_stdout):
        time.sleep(4)
        flasher = Flash()
        ret = flasher.flash(build='test/helloworld.bin', target_id='0', platform_name='K64F', device_mapping_table=False,
                            pyocd=False)
        self.assertEqual(ret, 0)
        if mock_stdout:
            pass

    @unittest.skipIf(len(AvailableFlashers) < 2, "Only one flasher supported in system")
    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_wrong_platform(self):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        target_id = None
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'target_id' in target:
                    target_id = target['target_id']
                    break
        if target_id:
            flasher = Flash()
            with self.assertRaises(SyntaxError) as cm:
                flasher.flash(build='test/helloworld.bin', target_id=target_id, platform_name='SAM4E',
                              device_mapping_table=False, pyocd=False)
            self.assertIn("Platform 'K64F' is not supported by Flasher Atprogram, please change the selected flasher", cm.exception, )

    def test_broken_mapping_table_dict(self):
        flasher = Flash()
        ret = flasher.flash(build='test/helloworld.bin', target_id='0240000029164e45002f0012706e0006f301000097969900', platform_name='K64F',
                      device_mapping_table={'target_id':'not_found'}, pyocd=False)
        self.assertEqual(ret, -3)
    
    def test_broken_mapping_table_int(self):
        flasher = Flash()
        with self.assertRaises(SystemError) as cm:
            flasher.flash(build='test/helloworld.bin', target_id='0240000029164e45002f0012706e0006f301000097969900', platform_name='K64F',
                    device_mapping_table=11, pyocd=False)
        self.assertIn("device_mapping_table wasn't list or dictionary", cm.exception, )
    
    @unittest.skipIf(not check_two_different_boards(), "Either one Atmel board and one Mbed board or two different MBED boards required to run this")
    def test_no_platform_selected_while_multiple_available(self):
        flasher = Flash()
        ret = flasher.flash(build='test/helloworld.bin', target_id='all', platform_name=False,
                    device_mapping_table=False, pyocd=False)
        self.assertEqual(ret, -9)
        
if __name__ == '__main__':
    unittest.main()
