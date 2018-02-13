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

import unittest
import mock

from mbed_flasher.common import Common, MountVerifier
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_CONFLICT
from mbed_flasher.return_codes import EXIT_CODE_SERIAL_PORT_REAPPEAR_TIMEOUT

# pylint: disable=too-few-public-methods
class Flasher(object):
    def __init__(self, result):
        self._result = result
        self.call_count = 0

    def get_available_devices(self):
        self.call_count += 1
        return self._result


class CommonTestCase(unittest.TestCase):
    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_no_devices(self, logger):
        flasher = Flasher([])
        results = Common(logger).get_available_device_mapping([flasher])
        self.assertEqual(results, [])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_no_target(self, logger):
        flasher = Flasher(["asd"])
        results = Common(logger).get_available_device_mapping([flasher])
        self.assertEqual(results, ["asd"])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_with_target_empty_list(self, logger):
        flasher = Flasher(["asd"])
        results = Common(logger).get_available_device_mapping([flasher], [])
        self.assertEqual(results, ["asd"])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_with_target_all(self, logger):
        flasher = Flasher(["asd"])
        results = Common(logger).get_available_device_mapping([flasher], "all")
        self.assertEqual(results, ["asd"])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_with_target_not_matching(self, logger):
        flasher = Flasher([{"target_id": "asd"}])
        results = Common(logger).get_available_device_mapping([flasher], "dsd")
        self.assertEqual(results, [{"target_id": "asd"}])
        self.assertEqual(flasher.call_count, 5)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_with_target_matching(self, logger):
        flasher = Flasher([{"target_id": "asd"}])
        results = Common(logger).get_available_device_mapping([flasher], "asd")
        self.assertEqual(results, [{"target_id": "asd"}])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_with_target_partly_matching(self, logger):
        flasher = Flasher([{"target_id": "asd"}])
        results = Common(logger).get_available_device_mapping([flasher], "as")
        self.assertEqual(results, [{"target_id": "asd"}])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_empty_with_invalid_listing(self, logger):
        flasher = Flasher([{"target": "asd"}])
        results = Common(logger).get_available_device_mapping([flasher], "as")
        self.assertEqual(results, [])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_empty_with_invalid_listing_2(self, logger):
        flasher = Flasher("asd")
        results = Common(logger).get_available_device_mapping([flasher], "as")
        self.assertEqual(results, [])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_list_of_one(self, logger):
        flasher = Flasher([{"target_id": "asd"}])
        results = Common(logger).get_available_device_mapping([flasher], ["asd"])
        self.assertEqual(results, [{"target_id": "asd"}])
        self.assertEqual(flasher.call_count, 1)


class MountVerifierTestCase(unittest.TestCase):
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
