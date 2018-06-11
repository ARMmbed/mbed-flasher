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
# pylint:disable=invalid-name
# pylint:disable=unused-argument

import logging
import unittest
try:
    from StringIO import StringIO
except ImportError:
    # python 3 compatible import
    from io import StringIO
import mock

from mbed_flasher.common import ResetError, GeneralFatalError
from mbed_flasher.reset import Reset
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_DEVICE


class ResetTestCase(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def test_reset_with_none(self):
        resetter = Reset()
        with self.assertRaises(ResetError) as cm:
            resetter.reset(target_id=None, method='simple')

        self.assertEqual(cm.exception.return_code, EXIT_CODE_TARGET_ID_MISSING)

    @mock.patch("time.sleep", return_value=None)
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_with_wrong_target_id(self, mock_stdout, mock_sleep):
        resetter = Reset()
        with self.assertRaises(GeneralFatalError) as cm:
            resetter.reset(target_id='555', method='simple')

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_DEVICE)

    @mock.patch('mbed_flasher.mbed_common.mbed_lstools.create')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_with_all_no_devices(self, mock_stdout, mock_mbed_lstools_create):
        # pylint:disable=too-few-public-methods
        class MockLS(object):
            def __init__(self):
                pass

            # pylint:disable=no-self-use
            def list_mbeds(self, filter_function=None):
                return []

        mock_mbed_lstools_create.return_value = MockLS()
        resetter = Reset()
        with self.assertRaises(ResetError) as cm:
            resetter.reset(target_id='all', method='simple')

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)


if __name__ == '__main__':
    unittest.main()
