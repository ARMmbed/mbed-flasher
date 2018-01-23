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
import os
from test.test_helper import Helper

try:
    from StringIO import StringIO
except ImportError:
    # python 3 compatible import
    from io import StringIO
import platform

import mock
import mbed_lstools

from mbed_flasher.flash import Flash
from mbed_flasher.flashers.FlasherMbed import FlasherMbed
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_FILE_DOES_NOT_EXIST
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_FILE_STILL_PRESENT
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_USER_ERROR
from mbed_flasher.return_codes import EXIT_CODE_FLASH_FAILED
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_SOFTWARE_ERROR
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_TRANSIENT_ERROR
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_TARGET_ERROR
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_INTERFACE_ERROR


class FlashTestCase(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """
    mbeds = mbed_lstools.create()
    bin_path = os.path.join('test', 'helloworld.bin')

    def setUp(self):
        logging.disable(logging.CRITICAL)
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def tearDown(self):
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def test_run_file_does_not_exist(self):
        flasher = Flash()
        with self.assertRaises(SyntaxError) as context:
            flasher.flash(build='file.bin', target_id=None,
                          platform_name=None, device_mapping_table=None, method='simple')
        self.assertIn("target_id or target_name is required", context.exception.msg)

    # test with name longer than 30, disable the warning here
    # pylint: disable=invalid-name
    def test_run_target_id_and_platform_missing(self):
        flasher = Flash()
        ret = flasher.flash(build='file.bin', target_id=True,
                            platform_name=False, device_mapping_table=None,
                            method='simple')
        self.assertEqual(ret, EXIT_CODE_FILE_DOES_NOT_EXIST)

    @mock.patch("mbed_flasher.flash.Logger")
    def test_flash_logger_created(self, mock_logger):  # pylint: disable=no-self-use
        mock_logger.return_value = mock.MagicMock()
        flash = Flash()  # pylint: disable=unused-variable
        mock_logger.assert_called_once_with("mbed-flasher")

    @mock.patch("mbed_flasher.flash.Logger")
    def test_flash_logger_not_created(self, mock_logger):
        mock_logger.return_value = mock.MagicMock()
        very_real_logger = mock.MagicMock()
        flash = Flash(logger=very_real_logger)
        mock_logger.assert_not_called()
        self.assertEqual(very_real_logger, flash.logger)

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    def test_run_with_file_with_target_id_all(self):
        flasher = Flash()
        ret = flasher.flash(build=self.bin_path,
                            target_id='all',
                            platform_name=False,
                            device_mapping_table=None,
                            method='simple')
        self.assertEqual(ret, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

    @unittest.skipIf(mbeds.list_mbeds() != [], "hardware attached")
    def test_run_with_file_with_one_target_id(self):
        flasher = Flash()
        ret = flasher.flash(build=self.bin_path,
                            target_id='0240000029164e45002f0012706e0006f301000097969900',
                            platform_name=False,
                            device_mapping_table=None,
                            method='simple')
        self.assertEqual(ret, EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

    # pylint: disable=unused-argument
    @mock.patch('mbed_flasher.flashers.FlasherMbed.FlasherMbed.copy_file')
    @mock.patch('mbed_flasher.common.MountVerifier.check_points_unchanged')
    @mock.patch('mbed_flasher.flashers.FlasherMbed.Popen')
    def test_run_with_uppercase_HTM(self, mock_popen, mock_verifier, mock_copy_file):
        mock_verifier.return_value = {'target_id':'123',
                                      'platform_name': 'K64F',
                                      'mount_point': 'path/'}

        mock_stdout = mock.Mock()
        mock_out = mock.Mock(side_effect=[b"no-htm", b"test.HTM", b"no-htm"])
        mock_stdout.read = mock_out
        mock_popen.return_value.stdout = mock_stdout

        mock_popen.return_value.communicate.return_value = ('', '')

        flasher = Flash()
        ret = flasher.flash(build=self.bin_path,
                            target_id='123',
                            platform_name='K64F',
                            device_mapping_table=[{
                                'target_id': '123',
                                'platform_name': 'K64F',
                                'mount_point': '',
                            }],
                            method='simple',
                            no_reset=True)
        self.assertEqual(ret, EXIT_CODE_SUCCESS)
        self.assertEqual(2, mock_out.call_count)

    # pylint: disable=no-self-use
    @unittest.skipIf(platform.system() != 'Windows', 'require windows')
    @mock.patch('os.system')
    def test_copy_file_with_spaces(self, mock_system):
        flasher = FlasherMbed()
        flasher.copy_file(__file__, "tar get")
        should_be = 'copy "%s" "tar get"' % __file__
        mock_system.assert_called_once_with(should_be)

    @mock.patch('mbed_flasher.flashers.FlasherMbed.FlasherMbed.copy_file')
    @mock.patch('mbed_flasher.common.MountVerifier.check_points_unchanged')
    @mock.patch('mbed_flasher.flashers.FlasherMbed.Popen')
    def test_run_with_lowercase_HTM(self, mock_popen, mock_verifier, mock_copy_file):
        mock_verifier.return_value = {'target_id': '123',
                                      'platform_name': 'K64F',
                                      'mount_point': 'path/'}

        mock_stdout = mock.Mock()
        mock_out = mock.Mock(side_effect=[b"no-htm", b"test.htm", b"no-htm"])
        mock_stdout.read = mock_out
        mock_popen.return_value.stdout = mock_stdout

        mock_popen.return_value.communicate.return_value = ('', '')

        flasher = Flash()
        ret = flasher.flash(build=self.bin_path,
                            target_id='123',
                            platform_name='K64F',
                            device_mapping_table=[{
                                'target_id': '123',
                                'platform_name': 'K64F',
                                'mount_point': '',
                            }],
                            method='simple',
                            no_reset=True)
        self.assertEqual(ret, EXIT_CODE_SUCCESS)
        self.assertEqual(2, mock_out.call_count)

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
            with self.assertRaises(NotImplementedError) as context:
                flasher.flash(build=self.bin_path,
                              target_id=target_id,
                              platform_name='K65G',
                              device_mapping_table=None,
                              method='simple')
            self.assertIn("Platform 'K65G' is not supported by mbed-flasher",
                          str(context.exception))

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
            ret = flasher.flash(build=self.bin_path,
                                target_id=target_id,
                                platform_name=False,
                                device_mapping_table=None,
                                method='simple')
            self.assertEqual(ret, EXIT_CODE_SUCCESS)

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_run_with_file_with_all(self, mock_stdout):
        flasher = Flash()
        ret = flasher.flash(build=self.bin_path,
                            target_id='all',
                            platform_name='K64F',
                            device_mapping_table=None,
                            method='simple')
        self.assertEqual(ret, EXIT_CODE_SUCCESS)
        if mock_stdout:
            pass

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_run_with_file_with_prefix(self, mock_stdout):
        flasher = Flash()
        ret = flasher.flash(build=self.bin_path,
                            target_id='0',
                            platform_name=None,
                            device_mapping_table=None,
                            method='simple')
        self.assertEqual(ret, EXIT_CODE_SUCCESS)
        if mock_stdout:
            pass

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_run_fail_file(self, mock_stdout):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        mount_point = None
        target_to_test = None
        fail_txt_path = os.path.join('test', 'failing.txt')
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'target_id' in target and 'mount_point' in target:
                    target_to_test = target
                    mount_point = target['mount_point']
                    break
        if target_to_test:
            flasher = FlasherMbed()
            flasher.FLASHING_VERIFICATION_TIMEOUT = 2
            with open(fail_txt_path, 'w') as new_file:
                new_file.write("0000000000000000000000000000000000")
            ret = flasher.flash(source=fail_txt_path,
                                target=target_to_test,
                                method='simple',
                                no_reset=False)
            if platform.system() == 'Windows':
                os.system('del %s' % os.path.join(mount_point, 'failing.txt'))
                os.system('del %s' % os.path.join(os.getcwd(), fail_txt_path))
            else:
                os.system('rm %s' % os.path.join(mount_point, 'failing.txt'))
                os.system('rm %s' % os.path.join(os.getcwd(), fail_txt_path))
            self.assertEqual(ret, EXIT_CODE_FILE_STILL_PRESENT)
        if mock_stdout:
            pass

    @unittest.skipIf(mbeds.list_mbeds() == [], "no hardware attached")
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_run_fail_binary(self, mock_stdout):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        target_id = None
        mount_point = None
        fail_bin_path = os.path.join('test', 'fail.bin')
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'target_id' in target and 'mount_point' in target:
                    target_id = target['target_id']
                    mount_point = target['mount_point']
                    break

        if target_id:
            flasher = Flash()
            with open(fail_bin_path, 'w') as new_file:
                new_file.write("0000000000000000000000000000000000")
            ret = flasher.flash(build=fail_bin_path,
                                target_id=target_id,
                                platform_name='K64F',
                                device_mapping_table=None,
                                method='simple')
            if platform.system() == 'Windows':
                os.system('del /F %s' % os.path.join(mount_point, 'FAIL.TXT'))
                os.system('del %s' % os.path.join(os.getcwd(), fail_bin_path))
            else:
                os.system('rm -f %s' % os.path.join(mount_point, 'FAIL.TXT'))
                os.system('rm %s' % os.path.join(os.getcwd(), fail_bin_path))

            self.assertEqual(ret, EXIT_CODE_DAPLINK_USER_ERROR)
        if mock_stdout:
            pass


class FlashVerify(unittest.TestCase):
    @mock.patch('mbed_flasher.flashers.FlasherMbed.isfile')
    def test_verify_flash_success_ok(self, mock_isfile):
        mock_isfile.return_value = False

        new_target = {"mount_point": ""}
        return_value = FlasherMbed().verify_flash_success(
            new_target=new_target, target={}, tail="")

        self.assertEqual(return_value, EXIT_CODE_SUCCESS)

    # test with name longer than 30, disable the warning here
    # pylint: disable=invalid-name
    @mock.patch('mbed_flasher.flashers.FlasherMbed.FlasherMbed._read_file')
    @mock.patch('mbed_flasher.flashers.FlasherMbed.isfile')
    def test_verify_flash_success_fail_no_reason(self, mock_isfile, mock_read_file):
        def isfile_function(path):
            if "FAIL" in path:
                return True
            return False

        mock_isfile.side_effect = isfile_function
        mock_read_file.return_value = ""

        new_target = {"mount_point": ""}
        target = {"target_id": ""}
        return_value = FlasherMbed().verify_flash_success(
            new_target=new_target, target=target, tail="")

        self.assertEqual(return_value, EXIT_CODE_FLASH_FAILED)

    # test with name longer than 30, disable the warning here
    # pylint: disable=invalid-name
    @mock.patch('mbed_flasher.flashers.FlasherMbed.FlasherMbed._read_file')
    @mock.patch('mbed_flasher.flashers.FlasherMbed.isfile')
    def test_verify_flash_success_fail_reasons(self, mock_isfile, mock_read_file):
        def isfile_function(path):
            if "FAIL" in path:
                return True
            return False

        mock_isfile.side_effect = isfile_function
        new_target = {"mount_point": ""}
        target = {"target_id": ""}

        def check(reason, code):
            mock_read_file.return_value = reason
            return_value = FlasherMbed().verify_flash_success(
                new_target=new_target, target=target, tail="")
            self.assertEqual(return_value, code)

        check("An internal error has occurred", EXIT_CODE_DAPLINK_SOFTWARE_ERROR)
        check("End of stream has been reached", EXIT_CODE_DAPLINK_SOFTWARE_ERROR)
        check("End of stream is unknown", EXIT_CODE_DAPLINK_SOFTWARE_ERROR)

        check("An error occurred during the transfer", EXIT_CODE_DAPLINK_TRANSIENT_ERROR)
        check("Possible mismatch between file size and size programmed",
              EXIT_CODE_DAPLINK_TRANSIENT_ERROR)
        check("File sent out of order by PC. Target might not be programmed correctly.",
              EXIT_CODE_DAPLINK_TRANSIENT_ERROR)
        check("An error has occurred", EXIT_CODE_DAPLINK_TRANSIENT_ERROR)

        check("The transfer timed out.", EXIT_CODE_DAPLINK_USER_ERROR)
        check("The interface firmware ABORTED programming. Image is trying to set security bits",
              EXIT_CODE_DAPLINK_USER_ERROR)
        check("The hex file cannot be decoded. Checksum calculation failure occurred.",
              EXIT_CODE_DAPLINK_USER_ERROR)
        check("The hex file cannot be decoded. Parser logic failure occurred.",
              EXIT_CODE_DAPLINK_USER_ERROR)
        check("The hex file cannot be programmed. Logic failure occurred.",
              EXIT_CODE_DAPLINK_USER_ERROR)
        check("The hex file you dropped isn't compatible with this mode or device."
              "Are you in MAINTENANCE mode? See HELP FAQ.HTM", EXIT_CODE_DAPLINK_USER_ERROR)
        check("The hex file offset load address is not correct.", EXIT_CODE_DAPLINK_USER_ERROR)
        check("The starting address for the bootloader update is wrong.",
              EXIT_CODE_DAPLINK_USER_ERROR)
        check("The starting address for the interface update is wrong.",
              EXIT_CODE_DAPLINK_USER_ERROR)
        check("The application file format is unknown and cannot be parsed and/or processed.",
              EXIT_CODE_DAPLINK_USER_ERROR)

        check("The interface firmware FAILED to reset/halt the target MCU",
              EXIT_CODE_DAPLINK_TARGET_ERROR)
        check("The interface firmware FAILED to download the flash programming"
              " algorithms to the target MCU", EXIT_CODE_DAPLINK_TARGET_ERROR)
        check("The interface firmware FAILED to download the flash"
              " data contents to be programmed", EXIT_CODE_DAPLINK_TARGET_ERROR)
        check("The interface firmware FAILED to initialize the target MCU",
              EXIT_CODE_DAPLINK_TARGET_ERROR)
        check("The interface firmware FAILED to unlock the target for programming",
              EXIT_CODE_DAPLINK_TARGET_ERROR)
        check("Flash algorithm erase sector command FAILURE", EXIT_CODE_DAPLINK_TARGET_ERROR)
        check("Flash algorithm erase all command FAILURE", EXIT_CODE_DAPLINK_TARGET_ERROR)
        check("Flash algorithm write command FAILURE", EXIT_CODE_DAPLINK_TARGET_ERROR)

        check("In application programming aborted due to an out of bounds address.",
              EXIT_CODE_DAPLINK_INTERFACE_ERROR)
        check("In application programming initialization failed.",
              EXIT_CODE_DAPLINK_INTERFACE_ERROR)
        check("In application programming uninit failed.", EXIT_CODE_DAPLINK_INTERFACE_ERROR)
        check("In application programming write failed.", EXIT_CODE_DAPLINK_INTERFACE_ERROR)
        check("In application programming sector erase failed.",
              EXIT_CODE_DAPLINK_INTERFACE_ERROR)
        check("In application programming mass erase failed.", EXIT_CODE_DAPLINK_INTERFACE_ERROR)
        check("In application programming not supported on this device.",
              EXIT_CODE_DAPLINK_INTERFACE_ERROR)
        check("In application programming failed because the update sent was incomplete.",
              EXIT_CODE_DAPLINK_INTERFACE_ERROR)
        check("The bootloader CRC did not pass.", EXIT_CODE_DAPLINK_INTERFACE_ERROR)

    @mock.patch('mbed_flasher.flashers.FlasherMbed.FlasherMbed._read_file')
    @mock.patch('mbed_flasher.flashers.FlasherMbed.isfile')
    def test_verify_flash_success_new_style(self, mock_isfile, mock_read_file):
        def isfile_function(path):
            if "FAIL" in path:
                return True
            return False

        mock_isfile.side_effect = isfile_function
        mock_read_file.return_value = """
error: File sent out of order by PC. Target might not be programmed correctly.
error type: transient, user
        """

        new_target = {"mount_point": ""}
        target = {"target_id": ""}
        return_value = FlasherMbed().verify_flash_success(
            new_target=new_target, target=target, tail="")

        self.assertEqual(return_value, EXIT_CODE_DAPLINK_TRANSIENT_ERROR)

    @mock.patch('mbed_flasher.flashers.FlasherMbed.FlasherMbed._read_file')
    @mock.patch('mbed_flasher.flashers.FlasherMbed.isfile')
    def test_verify_flash_success_multiple_hits(self, mock_isfile, mock_read_file):
        def isfile_function(path):
            if "FAIL" in path:
                return True
            return False

        mock_isfile.side_effect = isfile_function
        mock_read_file.return_value = """
error: File sent out of order by PC. Target might not be programmed correctly.
An error occurred during the transfer.
error type: transient, user
        """

        new_target = {"mount_point": ""}
        target = {"target_id": ""}
        return_value = FlasherMbed().verify_flash_success(
            new_target=new_target, target=target, tail="")

        self.assertEqual(return_value, EXIT_CODE_FLASH_FAILED)

if __name__ == '__main__':
    unittest.main()
