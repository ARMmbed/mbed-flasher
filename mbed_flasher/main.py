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

Author:
Jussi Vatjus-Anttila <jussi.vatjus-anttila@arm.com>
"""

from __future__ import print_function
import sys
import argparse
import logging
import logging.handlers
import os
import json

from flash import Flash

logger = logging.getLogger('mbed-flasher')
logger.handlers = []
logger.setLevel(logging.DEBUG)

# always write everything to the rotating log files
if not os.path.exists('logs'):
    os.mkdir('logs')
log_file_handler = logging.handlers.TimedRotatingFileHandler(
    'logs/mbed-flasher.log', when='M', interval=2)
log_file_handler.setFormatter(
    logging.Formatter(
        '%(asctime)s [%(levelname)s](%(name)s:%(funcName)s:%(lineno)d): %(message)s'))
log_file_handler.setLevel(logging.DEBUG)
logger.addHandler(log_file_handler)

# also log to the console at a level determined by the --verbose flag
console_handler = logging.StreamHandler() # sys.stderr
# set later by set_log_level_from_verbose() in interactive sessions
console_handler.setLevel(logging.CRITICAL)
console_handler.setFormatter(logging.Formatter('[%(levelname)s](%(name)s): %(message)s'))
logger.addHandler(console_handler)

def cmd_parser_setup():
    """! Configure CLI (Command Line options) options
    @return Returns ArgumentParser's tuple of (options, arguments)
    @details Add new command line options
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--verbose',
                        dest="verbose",
                        action="count",
                        help="Verbose level... repeat up to three times.")

    parser.add_argument('-s', '--silent',
                        dest="silent", default=False,
                        action="store_true",
                        help="Silent - only errors will be printed.")

    parser.add_argument('--version',
                        dest='version',
                        action="store_true",
                        help='Prints the package version and exits.')


    parser.add_argument('-i', '--input',
                        dest='input', help='Binary input to be flash.')

    parser.add_argument('-m', '--mapping',
                        dest='device_mapping_table', help='Device mapping table.')

    parser.add_argument('-l', '--list',
                        dest='list',
                        action="store_true",
                        help='Prints a list of supported platforms.')

    parser.add_argument('--flashers',
                        dest='flashers',
                        action="store_true",
                        help='Prints a list of supported flashers.')

    parser.add_argument('--tid', '--target_id',
                        dest='target_id', help='Target to be flashed, ALL will flash all connected devices with given platform-name')
    
    parser.add_argument('-t', '--platform_name',
                        dest='platform_name', help='Platform/target name to be flashed')

    args = parser.parse_args()
    return args

def set_log_level_from_verbose(args):
    """ set logging level, silent, or some of verbose level
    :param args: command line arguments
    """
    if args.silent:
        console_handler.setLevel('NOTSET')
    elif not args.verbose:
        console_handler.setLevel('ERROR')
    elif args.verbose == 1:
        console_handler.setLevel('WARNING')
    elif args.verbose == 2:
        console_handler.setLevel('INFO')
    elif args.verbose >= 3:
        console_handler.setLevel('DEBUG')
    else:
        logger.critical("UNEXPLAINED NEGATIVE COUNT!")


def mbedflash_main(cmd_args=None, module_name="mbed-flash"):
    """! Function used to drive CLI (command line interface) application
    @return Function exits with success-code
    @details Function exits back to command line with exit_status(=ERRORLEVEL in windows)
    """
    exit_status = 0
    
    args = cmd_parser_setup() if cmd_args == None else cmd_args
    set_log_level_from_verbose(args)

    if args.version:
        import pkg_resources  # part of setuptools
        try:
            version = pkg_resources.require(module_name)[0].version
            print(version)
        except pkg_resources.DistributionNotFound:
            print("not-installed")
    else:
        flasher = Flash()
        if args.list:
            print(json.dumps(flasher.get_supported_targets()))
        elif args.flashers:
            print(json.dumps(flasher.get_supported_flashers()))
        else:
            if args.input and args.target_id:
                exit_status = flasher.flash(build=args.input, target_id=args.target_id, platform_name=args.platform_name, device_mapping_table=args.device_mapping_table)
            else:
                if not args.input and not args.target_id and not args.platform_name:
                    sys.exit("No input, nothing to do.\nTry mbedflash --help")
                elif not args.input:
                    sys.exit("Missing file to flash, provide a file with -i <file>")
                elif not args.target_id:
                    sys.exit("Missing TargetID to flash.\nProvide a TargetID with --tid <TID> or --tid ALL to flash all connected devices corresponding to provided platform")
                    
    sys.exit(exit_status)
