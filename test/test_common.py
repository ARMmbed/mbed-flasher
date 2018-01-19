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

import unittest
import mock

from mbed_flasher.common import MountVerifier
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_CONFLICT
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_PORT_REAPPEAR_TIMEOUT

class MountVerifierTestCase(unittest.TestCase):
    # pylint: disable=invalid-name
    @mock.patch("mbed_flasher.common.check_output")
    @mock.patch("mbed_flasher.flash.Logger")
    def test_check_serial_duplicates_succeeds(self, logger, mock_check_output):
        mock_check_output.return_value = b'test_target_id /testTTY'
        mount_verifier = MountVerifier(logger)
        target = {'target_id': 'test_target_id',
                  'serial_port': '/testTTY'}
        # pylint: disable=protected-access
        return_value = mount_verifier._check_serial_point_duplicates(
            target=target, new_target={})

        self.assertEqual(return_value, None)

        mock_check_output.return_value = b'test_target_id /testTTY1'
        # pylint: disable=protected-access
        return_value = mount_verifier._check_serial_point_duplicates(
            target=target, new_target={})

        self.assertEqual(return_value, None)

    # pylint: disable=invalid-name
    @mock.patch("mbed_flasher.common.check_output")
    @mock.patch("mbed_flasher.flash.Logger")
    def test_check_serial_duplicates_finds(self, logger, mock_check_output):
        mock_check_output.return_value = b'test_target_id /testTTY1\ntest_target_id /testTTY1'
        mount_verifier = MountVerifier(logger)
        target = {'target_id': 'test_target_id',
                  'serial_port': '/testTTY'}
        # pylint: disable=protected-access
        return_value = mount_verifier._check_serial_point_duplicates(
            target=target, new_target={})

        self.assertEqual(return_value, EXIT_CODE_TARGET_ID_CONFLICT)

    # pylint: disable=invalid-name
    @mock.patch("mbed_flasher.common.check_output")
    @mock.patch("mbed_flasher.flash.Logger")
    def test_check_serial_duplicates_timeouts(self, logger, mock_check_output):
        mock_check_output.return_value = b''
        MountVerifier.SERIAL_POINT_TIMEOUT = 1
        mount_verifier = MountVerifier(logger)
        # pylint: disable=protected-access
        return_value = mount_verifier._check_serial_point_duplicates(
            target={'target_id': 'test'}, new_target={})

        self.assertEqual(return_value, EXIT_CODE_SERIAL_PORT_REAPPEAR_TIMEOUT)


if __name__ == '__main__':
    unittest.main()
