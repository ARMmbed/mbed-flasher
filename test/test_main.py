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
from mbed_flasher.main import cmd_parser_setup
from mbed_flasher.main import mbedflash_main
import argparse
import pkg_resources

class Main_TestCase(unittest.TestCase):
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

    #def test_parser_valid(self):
    #    t = cmd_parser_setup()
    #    self.assertIsInstance(t, tuple)

    def test_main(self):
        with self.assertRaises(SystemExit) as cm:
            mbedflash_main()
        self.assertEqual(cm.exception.code, 2)

    def test_main_version(self):
        class args:
            version = True
            input = "file:"
            verbose = 0
            silent=True

        with self.assertRaises(SystemExit) as cm:
            mbedflash_main(cmd_args=args)

    def test_main_verboses(self):
        class args:
            version = True
            verbose = 0
            silent = False

        for i in range(-1, 5):
            args.verbose = i
            with self.assertRaises(SystemExit) as cm:
                mbedflash_main(cmd_args=args)

    def test_main_not_installed(self):
        class args:
            version = True
            input = ""
            verbose = 0
            silent=True
        with self.assertRaises(SystemExit) as cm:
            mbedflash_main(cmd_args=args)