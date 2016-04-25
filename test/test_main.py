#!/usr/bin/env python
"""
mbed SDK
Copyright (c) 2011-2015 ARM Limited

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
import mock
from mbed_flasher.main import cmd_parser_setup
from mbed_flasher.main import mbedflash_main
from StringIO import StringIO

flasher_version = '0.3.1'


class MainTestCase(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        pass

    def test_parser_invalid(self):
        with self.assertRaises(SystemExit) as cm:
            cmd_parser_setup()
        self.assertEqual(cm.exception.code, 2)

    # def test_parser_valid(self):
    #    t = cmd_parser_setup()
    #    self.assertIsInstance(t, tuple)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            mbedflash_main()
        self.assertEqual(cm.exception.code, 2)
        if mock_stdout:
            pass

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main_version(self, mock_stdout):
        class Args:
            def __init__(self):
                pass
            version = True
            input = "file:"
            verbose = 0
            silent = True

        with self.assertRaises(SystemExit) as cm:
            mbedflash_main(cmd_args=Args)
        self.assertEqual(mock_stdout.getvalue(), flasher_version+"\n")
        self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main_verboses(self, mock_stdout):
        class Args:
            def __init__(self):
                pass
            version = True
            verbose = 0
            silent = False

        for i in range(-1, 5):
            Args.verbose = i
            with self.assertRaises(SystemExit) as cm:
                mbedflash_main(cmd_args=Args)
                self.assertEqual(mock_stdout.getvalue(), flasher_version+"\n")
                self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_main_not_installed(self, mock_stdout):
        class Args:
            def __init__(self):
                pass
            version = True
            input = ""
            verbose = 0
            silent = True

        with self.assertRaises(SystemExit) as cm:
            mbedflash_main(cmd_args=Args, module_name='mbed-flash')
        self.assertEqual(mock_stdout.getvalue(), "not-installed\n")
        self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_list(self, mock_stdout):
        class Args:
            def __init__(self):
                pass
            version = False
            verbose = 0
            list = True
            flashers = False
            silent = False

        with self.assertRaises(SystemExit) as cm:
            mbedflash_main(cmd_args=Args)
        self.assertEqual(mock_stdout.getvalue(), '["NRF51822", "K64F", "NRF51_DK", "NUCLEO_F401RE"]\n')
        self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_flashers(self, mock_stdout):
        class Args:
            def __init__(self):
                pass
            version = False
            verbose = False
            list = False
            flashers = True
            silent = False

        with self.assertRaises(SystemExit) as cm:
            mbedflash_main(cmd_args=Args)
        self.assertEqual(mock_stdout.getvalue(), '["Mbed"]\n')
        self.assertEqual(cm.exception.code, 0)

    def test_incorrect_file_target_platform(self):
        class Args:
            def __init__(self):
                pass
            version = False
            input = None
            target_id = None
            verbose = False
            list = False
            flashers = False
            silent = False
            platform_name = False

        with self.assertRaises(SystemExit) as cm:
            mbedflash_main(cmd_args=Args)
        self.assertEqual(cm.exception.code, "No input, nothing to do.\nTry mbedflash --help")

    def test_incorrect_file(self):
        class Args:
            def __init__(self):
                pass
            version = False
            input = None
            target_id = '01234567890'
            verbose = False
            list = False
            flashers = False
            silent = False
            platform_name = False

        with self.assertRaises(SystemExit) as cm:
            mbedflash_main(cmd_args=Args)
        self.assertEqual(cm.exception.code, "Missing file to flash, provide a file with -i <file>")

    def test_incorrect_target(self):
        class Args:
            def __init__(self):
                pass
            version = False
            input = True
            target_id = False
            verbose = False
            list = False
            flashers = False
            silent = False
            platform_name = False

        with self.assertRaises(SystemExit) as cm:
            mbedflash_main(cmd_args=Args)
        self.assertEqual(cm.exception.code,
                         "Missing TargetID to flash.\nProvide a TargetID with --tid <TID> or "
                         "--tid ALL to flash all connected devices corresponding to provided platform")


if __name__ == '__main__':
    unittest.main()
