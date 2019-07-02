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
import os
import unittest

import mock
from pyocd.core.helpers import ConnectHelper, Session
from pyocd.flash.loader import FileProgrammer, FlashEraser

from mbed_flasher.flashers.FlasherPyOCD import FlasherPyOCD, PyOCDMap
from mbed_flasher.common import FlashError, EraseError
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_USER_ERROR
from mbed_flasher.return_codes import EXIT_CODE_UNHANDLED_EXCEPTION
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_IMPLEMENTATION_MISSING


class PyOCDMapTestCase(unittest.TestCase):
    def test_supported_boards(self):
        self.assertTrue(PyOCDMap.is_supported('DISCO_L475VG_IOT01A'))
        self.assertTrue(PyOCDMap.is_supported('NUCLEO_L073RZ'))
        self.assertTrue(PyOCDMap.is_supported('NUCLEO_F429ZI'))
        self.assertTrue(PyOCDMap.is_supported('NUCLEO_F411RE'))


class PyOCDTestCase(unittest.TestCase):
    def test_is_supported(self):
        self.assertTrue(PyOCDMap.is_supported('DISCO_L475VG_IOT01A'))
        self.assertTrue(PyOCDMap.is_supported('NUCLEO_L073RZ'))
        self.assertFalse(PyOCDMap.is_supported(''))
        self.assertFalse(PyOCDMap.is_supported(None))
        self.assertFalse(PyOCDMap.is_supported(1))

    def test_platform(self):
        self.assertEqual(PyOCDMap.platform('DISCO_L475VG_IOT01A'), 'stm32l475xg')
        self.assertEqual(PyOCDMap.platform('NUCLEO_L073RZ'), 'stm32l073rz')
        self.assertEqual(PyOCDMap.platform('NUCLEO_F411RE'), 'stm32f411re')
        self.assertEqual(PyOCDMap.platform('NUCLEO_F429ZI'), 'stm32f429xi')
        with self.assertRaises(KeyError):
            PyOCDMap.platform('')

    def test_pack(self):
        self.assertEqual(PyOCDMap.pack('DISCO_L475VG_IOT01A'), None)
        with self.assertRaises(FlashError) as cm:
            PyOCDMap.pack('NUCLEO_L073RZ')
        self.assertEqual(cm.exception.return_code, EXIT_CODE_IMPLEMENTATION_MISSING)

        with self.assertRaises(KeyError):
            PyOCDMap.pack('')

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.PyOCDMap._get_pack_path', return_value='hih')
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.path.isfile', return_value=True)
    def test_pack_exists(self, mock_is_file, mock_get_pack_path):
        # pylint:disable=protected-access
        expected_dir = os.path.join(PyOCDMap._get_pack_path(), 'Keil.STM32L0xx_DFP.2.0.1.pack')
        self.assertEqual(PyOCDMap.pack('NUCLEO_L073RZ'), expected_dir)
        expected_dir = os.path.join(PyOCDMap._get_pack_path(), 'Keil.STM32F4xx_DFP.2.13.0.pack')
        self.assertEqual(PyOCDMap.pack('NUCLEO_F411RE'), expected_dir)


class FlasherPyOCDTestCase(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def test_is_ok(self):
        FlasherPyOCD()
        self.assertTrue(hasattr(FlasherPyOCD, 'can_flash'))
        self.assertTrue(hasattr(FlasherPyOCD, 'can_erase'))
        self.assertTrue(hasattr(FlasherPyOCD, 'flash'))
        self.assertTrue(hasattr(FlasherPyOCD, 'erase'))
        self.assertTrue(hasattr(FlasherPyOCD, '_get_session'))

    def test_can_flash_does_not_care_about_extension(self):
        target = {'platform_name': 'DISCO_L475VG_IOT01A'}
        self.assertTrue(FlasherPyOCD.can_flash(target, 'asd.hex'))
        self.assertTrue(FlasherPyOCD.can_flash(target, 'asd.bin'))
        self.assertTrue(FlasherPyOCD.can_flash(target, 'asd.elf'))
        self.assertTrue(FlasherPyOCD.can_flash(target, 'asd'))

    def test_can_flash_allows_only_supported_platforms(self):
        target = {'platform_name': 'DISCO_L475VG_IOT01A'}
        self.assertTrue(FlasherPyOCD.can_flash(target, 'asd.hex'))
        target = {'platform_name': 'NUCLEO_L073RZ'}
        self.assertTrue(FlasherPyOCD.can_flash(target, 'asd.hex'))
        target = {'platform_name': 'K64F'}
        self.assertFalse(FlasherPyOCD.can_flash(target, 'asd.hex'))
        target = {'platform_name': ''}
        self.assertFalse(FlasherPyOCD.can_flash(target, 'asd.hex'))
        target = {'platform_name': None}
        self.assertFalse(FlasherPyOCD.can_flash(target, 'asd.hex'))
        target = {}
        with self.assertRaises(KeyError):
            FlasherPyOCD.can_flash(target, 'asd.hex')

    def test_can_erase_allows_only_supported_platforms(self):
        target = {'platform_name': 'DISCO_L475VG_IOT01A'}
        self.assertTrue(FlasherPyOCD.can_erase(target))
        target = {'platform_name': 'NUCLEO_L073RZ'}
        self.assertTrue(FlasherPyOCD.can_erase(target))
        target = {'platform_name': 'K64F'}
        self.assertFalse(FlasherPyOCD.can_erase(target))
        target = {'platform_name': ''}
        self.assertFalse(FlasherPyOCD.can_erase(target))
        target = {'platform_name': None}
        self.assertFalse(FlasherPyOCD.can_erase(target))
        target = {}
        with self.assertRaises(KeyError):
            FlasherPyOCD.can_erase(target)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.ConnectHelper', autospec=ConnectHelper)
    def test_flash_session_init_fails(self, mock_connect_helper):
        target = {'target_id_usb_id': '', 'platform_name': 'DISCO_L475VG_IOT01A'}
        mock_connect_helper.session_with_chosen_probe.return_value = None
        with self.assertRaises(FlashError) as cm:
            FlasherPyOCD().flash('', target, '', True)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session', autospec=Session)
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FileProgrammer', autospec=FileProgrammer)
    def test_flash_returns_zero_on_success(self, mock_file_programmer, mock_get_session):
        return_value = FlasherPyOCD().flash('test_source', '', '', True)

        self.assertEqual(return_value, 0)
        self.assertEqual(mock_file_programmer.call_args[1], {'chip_erase': 'sector'})
        self.assertEqual(mock_file_programmer.method_calls[0][1], ('test_source',))

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session', autospec=Session)
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FileProgrammer', autospec=FileProgrammer)
    def test_flash_no_reset_parameter_is_respected(self, mock_file_programmer, mock_get_session):
        FlasherPyOCD().flash('', '', '', True)
        self.assertEqual(mock_get_session.call_count, 1)

        FlasherPyOCD().flash('', '', '', False)
        self.assertEqual(mock_get_session.call_count, 2)
        self.assertEqual(str(mock_get_session.method_calls[0]), 'call().target.reset()')

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session', autospec=Session)
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FileProgrammer.program', side_effect=ValueError)
    def test_flash_argument_error_leads_to_user_error(self, mock_file_programmer, mock_get_session):
        with self.assertRaises(FlashError) as cm:
            FlasherPyOCD().flash('', '', '', True)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_DAPLINK_USER_ERROR)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session', autospec=Session)
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FileProgrammer.program', side_effect=TypeError)
    def test_flash_handles_all_exceptions(self, mock_file_programmer, mock_get_session):
        with self.assertRaises(FlashError) as cm:
            FlasherPyOCD().flash('', '', '', True)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_UNHANDLED_EXCEPTION)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.ConnectHelper', autospec=ConnectHelper)
    def test_erase_session_init_fails(self, mock_connect_helper):
        target = {'target_id_usb_id': '', 'platform_name': 'DISCO_L475VG_IOT01A'}
        mock_connect_helper.session_with_chosen_probe.return_value = None
        with self.assertRaises(EraseError) as cm:
            FlasherPyOCD().erase(target, True)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session', autospec=Session)
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlashEraser', autospec=FlashEraser)
    def test_erase_returns_zero_on_success(self, mock_flash_eraser, mock_get_session):
        return_value = FlasherPyOCD().erase('', True)

        self.assertEqual(return_value, 0)
        self.assertEqual(mock_flash_eraser.call_args[0][1], mock_flash_eraser.Mode.CHIP)

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session', autospec=Session)
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlashEraser', autospec=FlashEraser)
    def test_erase_no_reset_parameter_is_respected(self, mock_file_programmer, mock_get_session):
        FlasherPyOCD().erase('', True)
        self.assertEqual(mock_get_session.call_count, 1)

        FlasherPyOCD().erase('', False)
        self.assertEqual(mock_get_session.call_count, 2)
        self.assertEqual(str(mock_get_session.method_calls[0]), 'call().target.reset()')

    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlasherPyOCD._get_session', autospec=Session)
    @mock.patch('mbed_flasher.flashers.FlasherPyOCD.FlashEraser.erase', side_effect=ValueError)
    def test_erase_handles_all_exceptions(self, mock_flash_eraser, mock_get_session):
        with self.assertRaises(EraseError) as cm:
            FlasherPyOCD().erase('', True)

        self.assertEqual(cm.exception.return_code, EXIT_CODE_UNHANDLED_EXCEPTION)


if __name__ == '__main__':
    unittest.main()
