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
import mock
import mbed_lstools
from mbed_flasher.erase import Erase


class EraseTestCase(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """
    mbeds = mbed_lstools.create()

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        pass

    def test_erase_with_none(self):
        eraser = Erase()
        ret = eraser.erase(target_id=None, method='simple')
        self.assertEqual(ret, 34)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_with_wrong_target_id(self, mock_stdout):
        eraser = Erase()
        ret = eraser.erase(target_id='555', method='simple')
        self.assertEqual(ret, 21)
        if mock_stdout:
            self.assertEqual(mock_stdout.getvalue(),
                             'Could not map given target_id(s) to available devices\n')

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_with_all_no_devices(self, mock_stdout):
        eraser = Erase()
        ret = eraser.erase(target_id='all', method='simple')
        self.assertEqual(ret, 21)
        if mock_stdout:
            self.assertEqual(mock_stdout.getvalue(),
                             'Could not map given target_id(s) to available devices\n')

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_erase_with_all(self):
        eraser = Erase()
        ret = eraser.erase(target_id='all', method='simple')
        self.assertEqual(ret, 0)

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_erase_with_target_id(self):
        mbeds = mbed_lstools.create()
        devices = mbeds.list_mbeds()
        eraser = Erase()
        ret = None
        for item in devices:
            if item['target_id']:
                ret = eraser.erase(target_id=item['target_id'], method='simple')
                break
        self.assertEqual(ret, 0)

    # test func name is larger than 30, but is meaningful
    # pylint: disable=invalid-name
    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_erase_with_target_id_no_reset(self):
        mbeds = mbed_lstools.create()
        devices = mbeds.list_mbeds()
        eraser = Erase()
        ret = None
        for item in devices:
            if item['target_id']:
                ret = eraser.erase(target_id=item['target_id'],
                                   method='simple',
                                   no_reset=True)
                break
        self.assertEqual(ret, 0)

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    def test_erase_with_target_id_list(self):
        mbeds = mbed_lstools.create()
        devices = mbeds.list_mbeds()
        eraser = Erase()
        ret = None
        for item in devices:
            if item['target_id']:
                ret = eraser.erase(target_id=[item['target_id']], method='simple')
                break
        self.assertEqual(ret, 0)

    # For some reason a bunch of tracebacks on usb.core langid problems.
    # @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    # @mock.patch('sys.stdout', new_callable=StringIO)
    # def test_erase_with_all_pyocd(self, mock_stdout):
    #    eraser = Erase()
    #    ret = eraser.erase(target_id='all', method='pyocd')
    #    self.assertEqual(ret, 0)

if __name__ == '__main__':
    unittest.main()
