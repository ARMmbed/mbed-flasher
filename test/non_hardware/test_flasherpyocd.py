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
# pylint:disable=invalid-name
# pylint:disable=unused-argument
import logging
import unittest

import mock
from pyocd.core.helpers import ConnectHelper, Session
from pyocd.flash.file_programmer import FileProgrammer
from pyocd.flash.eraser import FlashEraser

from mbed_flasher.flashers.FlasherPyOCD import FlasherPyOCD
from mbed_flasher.common import FlashError, EraseError
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_USER_ERROR
from mbed_flasher.return_codes import EXIT_CODE_PYOCD_UNHANDLED_EXCEPTION
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE


class FlasherPyOCDTestCase(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def test_is_ok(self):
        FlasherPyOCD()
        self.assertTrue(hasattr(FlasherPyOCD, 'flash'))
        self.assertTrue(hasattr(FlasherPyOCD, 'erase'))
        self.assertTrue(hasattr(FlasherPyOCD, '_get_session'))

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.ConnectHelper', autospec=ConnectHelper)
    def test_flash_session_init_fails(self, mock_connect_helper):
        target = {'target_id_usb_id': '', 'platform_name': 'DISCO_L475VG_IOT01A'}
        mock_connect_helper.session_with_chosen_probe.return_value = None
        with self.assertRaises(FlashError) as cm:
            FlasherPyOCD().flash('', target, True, 'stm32l475xg', '', 'halt')

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session')
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FileProgrammer', autospec=FileProgrammer)
    def test_flash_returns_zero_on_success(self, mock_file_programmer, mock_get_session):
        return_value = FlasherPyOCD().flash('test_source', '', True, '', '', None)

        self.assertEqual(return_value, 0)
        self.assertEqual(mock_file_programmer.call_args[1], {'chip_erase': 'sector'})
        self.assertEqual(mock_file_programmer.method_calls[0][1], ('test_source',))

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session')
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FileProgrammer', autospec=FileProgrammer)
    def test_flash_no_reset_parameter_is_respected(self, mock_file_programmer, mock_get_session):
        class Target:
            def __init__(self):
                self.index = 0

            def reset(self):
                self.index += 1

        t = Target()
        m = mock.MagicMock()
        mock_get_session.return_value = m
        type(m).target = mock.PropertyMock(return_value=t)

        FlasherPyOCD().flash('', '', True, '', '', None)
        self.assertEqual(mock_get_session.call_count, 1)
        self.assertEqual(t.index, 0)

        FlasherPyOCD().flash('', '', False, '', '', None)
        self.assertEqual(mock_get_session.call_count, 2)
        self.assertEqual(t.index, 1)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.ConnectHelper', autospec=ConnectHelper)
    def test_flash_session_is_opened_with_correct_params(self, mock_connect_helper):
        mock_connect_helper.session_with_chosen_probe.return_value = None
        target = {'target_id_usb_id': 'test_id'}
        with self.assertRaises(FlashError):
            FlasherPyOCD().flash('', target, True, 'k64f', 'test_pack', 'halt')
        mock_connect_helper.session_with_chosen_probe.assert_called_with(
            blocking=False,
            connect_mode='halt',
            hide_programming_progress=True,
            pack='test_pack',
            resume_on_disconnect=False,
            target_override='k64f',
            unique_id='test_id')

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session',
                side_effect=ValueError)
    def test_flash_argument_error_leads_to_user_error(self, mock_get_session):
        with self.assertRaises(FlashError) as cm:
            FlasherPyOCD().flash('', '', True, '', '', None)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_PYOCD_USER_ERROR)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session',
                side_effect=TypeError)
    def test_flash_handles_all_exceptions(self, mock_get_session):
        with self.assertRaises(FlashError) as cm:
            FlasherPyOCD().flash('', '', True, '', '', None)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_PYOCD_UNHANDLED_EXCEPTION)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.ConnectHelper', autospec=ConnectHelper)
    def test_erase_session_init_fails(self, mock_connect_helper):
        target = {'target_id_usb_id': '', 'platform_name': 'DISCO_L475VG_IOT01A'}
        mock_connect_helper.session_with_chosen_probe.return_value = None
        with self.assertRaises(EraseError) as cm:
            FlasherPyOCD().erase(target, True, 'stm32l475xg', '', 'halt')

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session')
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlashEraser', autospec=FlashEraser)
    def test_erase_returns_zero_on_success(self, mock_flash_eraser, mock_get_session):
        return_value = FlasherPyOCD().erase('', True, '', '', None)

        self.assertEqual(return_value, 0)
        self.assertEqual(mock_flash_eraser.call_args[0][1], mock_flash_eraser.Mode.CHIP)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session')
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlashEraser', autospec=FlashEraser)
    def test_erase_no_reset_parameter_is_respected(self, mock_file_programmer, mock_get_session):
        class Target:
            def __init__(self):
                self.index = 0

            def reset(self):
                self.index += 1

        t = Target()
        m = mock.MagicMock()
        mock_get_session.return_value = m
        type(m).target = mock.PropertyMock(return_value=t)
        FlasherPyOCD().erase('', True, '', '', None)
        self.assertEqual(mock_get_session.call_count, 1)
        self.assertEqual(t.index, 0)

        FlasherPyOCD().erase('', False, '', '', None)
        self.assertEqual(mock_get_session.call_count, 2)
        self.assertEqual(t.index, 1)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.ConnectHelper', autospec=ConnectHelper)
    def test_erase_session_is_opened_with_correct_params(self, mock_connect_helper):
        mock_connect_helper.session_with_chosen_probe.return_value = None
        target = {'target_id_usb_id': 'test_id'}
        with self.assertRaises(FlashError):
            FlasherPyOCD().erase(target, True, 'k64f', 'test_pack', 'under-reset')
        mock_connect_helper.session_with_chosen_probe.assert_called_with(
            blocking=False,
            connect_mode='under-reset',
            hide_programming_progress=True,
            pack='test_pack',
            resume_on_disconnect=False,
            target_override='k64f',
            unique_id='test_id')

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session', autospec=Session)
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlashEraser.erase', side_effect=ValueError)
    def test_erase_handles_all_exceptions(self, mock_flash_eraser, mock_get_session):
        with self.assertRaises(EraseError) as cm:
            FlasherPyOCD().erase('', True, '', '', None)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_PYOCD_UNHANDLED_EXCEPTION)


if __name__ == '__main__':
    unittest.main()
