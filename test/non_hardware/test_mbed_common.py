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
# pylint: disable=unused-argument

import os
import unittest
import mock

from mbed_flasher.mbed_common import MbedCommon


class MbedCommonTestCase(unittest.TestCase):
    def test_get_binary_destination_returns_expected_path(self):
        mount_point = "/test/mount_point_0_1_0"
        source = "/workspace/flasher/test.bin"

        result = MbedCommon.get_binary_destination(mount_point, source)
        self.assertEqual(
            result, os.path.abspath(os.path.join("/test/mount_point_0_1_0", "test.bin")))

    @mock.patch('mbed_flasher.mbed_common.mbed_lstools.create')
    def test_refresh_target_returns_target(self, mock_mbed_lstools_create):
        # pylint:disable=too-few-public-methods
        class MockLS(object):
            def __init__(self):
                pass

            # pylint:disable=no-self-use
            def list_mbeds(self, filter_function=None):
                return [{"target_id": "test_id"}]

        mock_mbed_lstools_create.return_value = MockLS()

        target = {"target_id": "test_id"}
        self.assertEqual(target, MbedCommon.refresh_target(target["target_id"]))

    @mock.patch("time.sleep", return_value=None)
    @mock.patch('mbed_flasher.mbed_common.mbed_lstools.create')
    def test_refresh_target_returns_empty_list_when_no_devices(
            self, mock_mbed_lstools_create, mock_sleep):
        # pylint:disable=too-few-public-methods
        class MockLS(object):
            def __init__(self):
                pass

            # pylint:disable=no-self-use
            def list_mbeds(self, filter_function=None):
                return []

        mock_mbed_lstools_create.return_value = MockLS()

        target = {"target_id": "test_id"}
        self.assertEqual(None, MbedCommon.refresh_target(target["target_id"]))

    @mock.patch("mbed_flasher.mbed_common.MbedCommon.refresh_target_once", return_value=[])
    @mock.patch("time.sleep", return_value=None)
    def test_wait_for_file_disappear_tries_many_times(self, mock_sleep, mock_refresh_target_once):
        target = {"target_id": "test"}
        new_target = MbedCommon.wait_for_file_disappear(target, "")
        self.assertEqual(mock_sleep.call_count, 60)
        self.assertEqual(mock_refresh_target_once.call_count, 60)
        self.assertEqual(target, new_target)

    @mock.patch("os.listdir", return_value=["details.txt", "mbed.htm"])
    @mock.patch("os.path.isfile", return_value=False)
    @mock.patch("mbed_flasher.mbed_common.MbedCommon.refresh_target_once",
                return_value=[{"mount_point": ""}])
    @mock.patch("time.sleep", return_value=None)
    def test_wait_for_file_disappear_find_lowercase_htm_file(
            self, mock_sleep, mock_refresh_target_once, mock_isfile, mock_listdir):
        target = {"target_id": "test"}
        new_target = MbedCommon.wait_for_file_disappear(target, "")
        self.assertEqual(mock_sleep.call_count, 0)
        self.assertEqual(mock_refresh_target_once.call_count, 1)
        self.assertEqual(mock_isfile.call_count, 1)
        self.assertEqual(mock_listdir.call_count, 1)
        self.assertEqual(new_target, {"mount_point": ""})

    @mock.patch("os.listdir", return_value=["details.txt", "MBED.HTM"])
    @mock.patch("os.path.isfile", return_value=False)
    @mock.patch("mbed_flasher.mbed_common.MbedCommon.refresh_target_once",
                return_value=[{"mount_point": ""}])
    @mock.patch("time.sleep", return_value=None)
    def test_wait_for_file_disappear_find_uppercase_htm_file(
            self, mock_sleep, mock_refresh_target_once, mock_isfile, mock_listdir):
        target = {"target_id": "test"}
        new_target = MbedCommon.wait_for_file_disappear(target, "")
        self.assertEqual(mock_sleep.call_count, 0)
        self.assertEqual(mock_refresh_target_once.call_count, 1)
        self.assertEqual(mock_isfile.call_count, 1)
        self.assertEqual(mock_listdir.call_count, 1)
        self.assertEqual(new_target, {"mount_point": ""})

    @mock.patch("os.listdir", side_effect=OSError)
    @mock.patch("os.path.isfile", return_value=False)
    @mock.patch("mbed_flasher.mbed_common.MbedCommon.refresh_target_once",
                return_value=[{"target_id": "test", "mount_point": ""}])
    @mock.patch("time.sleep", return_value=None)
    def test_wait_for_file_disappear_survives_winerror(
            self, mock_sleep, mock_refresh_target_once, mock_isfile, mock_listdir):
        target = {"target_id": "test"}
        new_target = MbedCommon.wait_for_file_disappear(target, "")
        self.assertEqual(mock_sleep.call_count, 60)
        self.assertEqual(mock_refresh_target_once.call_count, 60)
        self.assertEqual(mock_isfile.call_count, 60)
        self.assertEqual(mock_listdir.call_count, 60)
        self.assertEqual(new_target, {"target_id": "test", "mount_point": ""})

if __name__ == '__main__':
    unittest.main()
