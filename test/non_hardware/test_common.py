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

from mbed_flasher.common import Common, retry, DEFAULT_RETRY_AMOUNT,\
    FlashError, EraseError, ResetError, GeneralFatalError


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
        flasher = Flasher([{"target_id": "asd"}])
        results = Common(logger).get_available_device_mapping([flasher])
        self.assertEqual(results, [{"target_id": "asd"}])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_with_target_empty_list(self, logger):
        flasher = Flasher([{"target_id": "asd"}])
        results = Common(logger).get_available_device_mapping([flasher], [])
        self.assertEqual(results, [{"target_id": "asd"}])
        self.assertEqual(flasher.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_get_available_device_mapping_returns_with_target_all(self, logger):
        flasher = Flasher([{"target_id": "asd"}])
        results = Common(logger).get_available_device_mapping([flasher], "all")
        self.assertEqual(results, [{"target_id": "asd"}])
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


class RetryTestCase(unittest.TestCase):
    def setUp(self):
        self.call_count = 0

    @mock.patch("mbed_flasher.flash.Logger")
    def test_retry_succeeds_first_try(self, logger):
        def func():
            self.call_count += 1
            return 0

        return_code = retry(logger=logger, func=func, func_args=(), conditions=[1])

        self.assertEqual(return_code, 0)
        self.assertEqual(self.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_retries_on_condition(self, logger):
        def func():
            self.call_count += 1
            raise FlashError(message="", return_code=1)

        with self.assertRaises(FlashError) as cm:
            retry(logger=logger, func=func, func_args=(), conditions=[1])

        self.assertEqual(cm.exception.return_code, 1)
        self.assertEqual(self.call_count, DEFAULT_RETRY_AMOUNT)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_retry_returns_last_return_code(self, logger):
        def func():
            self.call_count += 1
            raise FlashError(message="", return_code=self.call_count)

        with self.assertRaises(FlashError) as cm:
            retry(logger=logger, func=func, func_args=(), conditions=[1, 2])

        self.assertEqual(cm.exception.return_code, 3)
        self.assertEqual(self.call_count, DEFAULT_RETRY_AMOUNT)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_retry_breaks_when_condition_doesnt_match(self, logger):
        def func():
            self.call_count += 1
            raise FlashError(message="", return_code=self.call_count)

        with self.assertRaises(FlashError) as cm:
            retry(logger=logger, func=func, func_args=(), conditions=[1])

        self.assertEqual(cm.exception.return_code, 2)
        self.assertEqual(self.call_count, 2)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_retry_has_no_condition_by_default(self, logger):
        def func():
            self.call_count += 1
            raise FlashError(message="", return_code=self.call_count)

        with self.assertRaises(FlashError) as cm:
            retry(logger=logger, func=func, func_args=())

        self.assertEqual(cm.exception.return_code, 1)
        self.assertEqual(self.call_count, 1)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_retries_amount_can_be_changed(self, logger):
        def func():
            self.call_count += 1
            raise FlashError(message="", return_code=1)

        with self.assertRaises(FlashError) as cm:
            retry(logger=logger, func=func, func_args=(), conditions=[1], retries=5)

        self.assertEqual(cm.exception.return_code, 1)
        self.assertEqual(self.call_count, 5)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_retry_raises_at_last_try(self, logger):
        def func():
            self.call_count += 1
            raise FlashError(message="", return_code=1)

        with self.assertRaises(FlashError) as cm:
            retry(logger=logger, func=func, func_args=(), conditions=[1], retries=5)

        self.assertEqual(cm.exception.return_code, 1)
        self.assertEqual(self.call_count, 5)


class FlashErrorTestCase(unittest.TestCase):
    def test_can_be_risen(self):
        with self.assertRaises(FlashError) as cm:
            raise FlashError(message="test", return_code=0)

        self.assertEqual(cm.exception.message, "test")
        self.assertEqual(cm.exception.return_code, 0)


class EraseErrorTestCase(unittest.TestCase):
    def test_can_be_risen(self):
        with self.assertRaises(FlashError) as cm:
            raise EraseError(message="test", return_code=0)

        self.assertEqual(cm.exception.message, "test")
        self.assertEqual(cm.exception.return_code, 0)


class GeneralFatalErrorTestCase(unittest.TestCase):
    def test_can_be_risen(self):
        with self.assertRaises(GeneralFatalError) as cm:
            raise GeneralFatalError(message="test", return_code=0)

        self.assertEqual(cm.exception.message, "test")
        self.assertEqual(cm.exception.return_code, 0)


class ResetErrorTestCase(unittest.TestCase):
    def test_can_be_risen(self):
        with self.assertRaises(ResetError) as cm:
            raise ResetError(message="test", return_code=0)

        self.assertEqual(cm.exception.message, "test")
        self.assertEqual(cm.exception.return_code, 0)


if __name__ == '__main__':
    unittest.main()
