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

import logging
import unittest
import mbed_lstools
import mock

from mbed_flasher.main import FlasherCLI
from StringIO import StringIO

flasher_version = '0.3.1'


class MainTestCase(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """

    mbeds = mbed_lstools.create()

    def setUp(self):
        self.logging_patcher = mock.patch("mbed_flasher.main.logging")
        mock_logging = self.logging_patcher.start()
        mock_logging.getLogger = mock.MagicMock(return_value=mock.Mock(spec=logging.Logger))
        mock_logging.disable(logging.CRITICAL)

    def tearDown(self):
        pass

    def test_parser_invalid(self):
        with self.assertRaises(SystemExit) as cm:
            FlasherCLI()
        self.assertEqual(cm.exception.code, 2)

    # def test_parser_valid(self):
    #    t = cmd_parser_setup()
    #    self.assertIsInstance(t, tuple)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            FlasherCLI([])
        self.assertEqual(cm.exception.code, 2)
        if mock_stdout:
            pass

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main_version(self, mock_stdout):
        fcli = FlasherCLI(["version"])
        self.assertEqual(fcli.execute(), 0)
        self.assertEqual(mock_stdout.getvalue(), flasher_version+'\n')
        #self.assertRegexpMatches(mock_stdout.getvalue(), r"^\d+\.\d+\.\d+$")

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main_verboses(self, mock_stdout):
        fcli = FlasherCLI(["-v", "version"])
        self.assertEqual(fcli.execute(), 0)
        self.assertRegexpMatches(mock_stdout.getvalue(), r"^(\s*\S+\s+\S+\n)+$")

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_file_does_not_exist(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", "None" ])
        self.assertEqual(fcli.execute(), 5)
        self.assertEqual(mock_stdout.getvalue(), 'Could not find given file: None\n')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_file_not_given(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", None])
        self.assertEqual(fcli.execute(), 5)
        self.assertEqual(mock_stdout.getvalue(), 'File is missing\n')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_wrong_platform(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", "test/helloworld.bin", "-t", "K65G"])
        self.assertEqual(fcli.execute(), 10)
        self.assertIn(mock_stdout.getvalue(), "Not supported platform: K65G\nSupported platforms: "
                                              "[u'LPC2368', u'UBLOX_C027', u'KL25Z', u'KL05Z', u'HEXIWEAR',"
                                              " u'KL46Z', u'K20D50M', u'K22F', u'K64F', u'MTS_GAMBIT',"
                                              " u'MTS_MDOT_F405RG', u'MTS_DRAGONFLY_F411RE',"
                                              " u'MTS_MDOT_F411RE', u'MAXWSNENV', u'MAX32600MBED',"
                                              " u'SPANSION_PLACEHOLDER', u'NUCLEO_F103RB',"
                                              " u'NUCLEO_F302R8', u'NUCLEO_L152RE', u'NUCLEO_L053R8',"
                                              " u'NUCLEO_F401RE', u'NUCLEO_F030R8', u'NUCLEO_F072RB',"
                                              " u'NUCLEO_F334R8', u'NUCLEO_F411RE', u'NUCLEO_F410RB',"
                                              " u'NUCLEO_F303RE', u'NUCLEO_F303ZE', u'NUCLEO_F091RC',"
                                              " u'NUCLEO_F070RB', u'NUCLEO_L073RZ', u'NUCLEO_L476RG',"
                                              " u'NUCLEO_L432KC', u'NUCLEO_F303K8', u'NUCLEO_F446RE',"
                                              " u'NUCLEO_F446ZE', u'NUCLEO_L011K4', u'NUCLEO_F042K6',"
                                              " u'DISCO_F469NI', u'NUCLEO_L031K6', u'NUCLEO_F031K6',"
                                              " u'DISCO_F429ZI', u'NUCLEO_F429ZI', u'ST_PLACEHOLDER',"
                                              " u'DISCO_L053C8', u'DISCO_F334C8', u'DISCO_F746NG',"
                                              " u'NUCLEO_F746ZG', u'DISCO_F769NI', u'NUCLEO_F767ZI',"
                                              " u'DISCO_L476VG', u'LPC824', u'NUCLEO_F207ZG', u'B96B_F446VE',"
                                              " u'XPRO_SAMR21', u'XPRO_SAMW25', u'XPRO_SAML21', u'XPRO_SAMD21',"
                                              " u'LPC1768', u'HRM1017', u'SSCI824', u'TY51822R3', u'LPC11U34',"
                                              " u'LPC11U24', u'LPC812', u'LPC4088', u'LPC11U35_401', u'LPC4088_DM',"
                                              " u'NRF51822', u'NRF51822_OTA', u'OC_MBUINO', u'RBLAB_NRF51822',"
                                              " u'RBLAB_BLENANO', u'NRF51_DK', u'NRF52_DK', u'NRF51_DK_OTA',"
                                              " u'LPC1114', u'NRF51_DONGLE', u'NRF51822_SBK', u'WALLBOT_BLE',"
                                              " u'LPC11U68', u'NCS36510', u'UBLOX_C029', u'NUC472-NUTINY', u'NUMBED',"
                                              " u'NUMAKER_PFM_NUC472', u'NUMAKER_PFM_M453', u'LPC1549', u'LPC4330_M4',"
                                              " u'EFM32_G8XX_STK', u'EFM32HG_STK3400', u'EFM32WG_STK3800',"
                                              " u'EFM32GG_STK3700', u'EFM32LG_STK3600', u'EFM32TG_STK3300',"
                                              " u'EFM32ZG_STK3200', u'EFM32PG_STK3401', u'XBED_LPC1768',"
                                              " u'WIZWIKI_W7500', u'WIZWIKI_W7500ECO', u'WIZWIKI_W7500P',"
                                              " u'LPC11U35_Y5_MBUG', u'NRF51822_Y5_MBUG', u'MOTE_L152RC',"
                                              " u'LPC4337', u'DELTA_DFCM_NNN40', u'ARM_MPS2', u'ARM_MPS2_M0',"
                                              " u'ARM_BEETLE_SOC', u'ARM_MPS2_M0DS', u'ARM_MPS2_M1', u'ARM_MPS2_M3',"
                                              " u'ARM_MPS2_M4', u'ARM_MPS2_M7', u'HOME_GATEWAY_6LOWPAN', u'RZ_A1H',"
                                              " u'NZ32_SC151', u'TEENSY3_1', u'LPC1347', u'ARCH_PRO', u'LPC11U35_501',"
                                              " u'XADOW_M0', u'ARCH_BLE', u'ARCH_GPRS', u'ARCH_MAX', u'SEEED_TINY_BLE',"
                                              " u'NRF51_MICROBIT', u'VK_RZ_A1H', u'K20 BOOTLOADER', u'RIOT']\n")

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_tid_missing(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", "test/helloworld.bin", "-t", "K64F"])
        self.assertEqual(fcli.execute(), 15)
        self.assertEqual(mock_stdout.getvalue(), "Target_id is missing\n")

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_wrong_tid(self, mock_stdout):
        fcli = FlasherCLI(["flash", "-i", "test/helloworld.bin", "--tid", "555", "-t", "K64F"])
        self.assertEqual(fcli.execute(), 20)
        self.assertEqual(mock_stdout.getvalue(), "Could not find any connected device\n")

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_tid_missing(self, mock_stdout):
        fcli = FlasherCLI(["reset"])
        self.assertEqual(fcli.execute(), 15)
        self.assertEqual(mock_stdout.getvalue(), "Target_id is missing\n")

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_wrong_tid(self, mock_stdout):
        fcli = FlasherCLI(["reset", "--tid", "555"])
        self.assertEqual(fcli.execute(), 20)
        self.assertEqual(mock_stdout.getvalue(), "Could not find any connected device\n")

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_reset_wrong_tid_with_device(self, mock_stdout):
        fcli = FlasherCLI(["reset", "--tid", "555"])
        self.assertEqual(fcli.execute(), 25)
        self.assertRegexpMatches(mock_stdout.getvalue(), r"Could not find given target_id from attached devices\nAvailable target_ids:\n\[(\'[0-9a-fA-F]+\')(,\s\'[0-9a-fA-F]+\')*\]", "Regex match failed")

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_tid_missing(self, mock_stdout):
        fcli = FlasherCLI(["erase"])
        self.assertEqual(fcli.execute(), 15)
        self.assertEqual(mock_stdout.getvalue(), "Target_id is missing\n")

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_wrong_tid(self, mock_stdout):
        fcli = FlasherCLI(["erase", "--tid", "555"])
        self.assertEqual(fcli.execute(), 20)
        self.assertEqual(mock_stdout.getvalue(), "Could not find any connected device\n")

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_erase_wrong_tid_with_device(self, mock_stdout):
        fcli = FlasherCLI(["erase", "--tid", "555"])
        self.assertEqual(fcli.execute(), 25)
        self.assertRegexpMatches(mock_stdout.getvalue(), r"Could not find given target_id from attached devices\nAvailable target_ids:\n\[(\'[0-9a-fA-F]+\')(,\s\'[0-9a-fA-F]+\')*\]", "Regex match failed")

if __name__ == '__main__':
    unittest.main()
