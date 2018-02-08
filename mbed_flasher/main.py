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

from __future__ import print_function
import sys
import argparse
import logging
import logging.handlers
import os
from os.path import isdir, isfile, join
import json
import time

from mbed_flasher.flash import Flash
from mbed_flasher.erase import Erase
from mbed_flasher.reset import Reset
from mbed_flasher.return_codes import FAILURE_RETURN_CODE_MAPPING_TABLE
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_FILE_MISSING
from mbed_flasher.return_codes import EXIT_CODE_NOT_SUPPORTED_PLATFORM
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_DEVICES_MISSING
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_PLATFORM_REQUIRED

LOGS_TTL = 172800 # 2 days, when log file is older it will be deleted

def get_subparser(subparsers, name, func, **kwargs):
    """
    Create a subcmd parser for command "name".

    Arguments
        subparsers The subparsers object from add_subparsers method
        name Name of the command this subparser is for
        kwargs Keyword arguments are passed to the subparser.add_parser call

    Returns
        subparser object

    """
    tmp_parser = subparsers.add_parser(name, **kwargs)
    tmp_parser.set_defaults(func=func)
    return tmp_parser

def get_resource_subparser(subparsers, name, func, **kwargs):
    """
    Create a resource specific subcmd parser for command "name".
    This adds necessary arguments for specifying resource
    etc that are common for all resource command parsers.

    Arguments
        subparsers The subparsers object from add_subparsers method
        name Name of the command this subparser is for
        kwargs Keyword arguments are passed to the subparser.add_parser call

    Returns
        subparser object

    """
    tmp_parser = get_subparser(subparsers, name, func=func, **kwargs)
    return tmp_parser

class FlasherCLI(object):
    """
    FlasherCLI module
    """
    def __init__(self, args=None):
        self.logger = logging.getLogger('mbed-flasher')
        self.logger.handlers = []
        self.logs_folder = join(os.getcwd(), 'logs')
        if not isdir(self.logs_folder):
            os.mkdir(self.logs_folder)
        log_file = 'logs/%s_mbed-flasher.txt' % time.strftime("%Y%m%d-%H%M%S")
        self.log_file_handler = logging.handlers.RotatingFileHandler(log_file)
        self.log_file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s [%(levelname)s]'
                '(%(name)s:%(funcName)s:%(lineno)d):%(thread)d: %(message)s'))
        self.log_file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(self.log_file_handler)
        # also log to the console at a level determined by the --verbose flag
        self.console_handler = logging.StreamHandler()  # sys.stderr
        # set later by set_log_level_from_verbose() in interactive sessions
        self.console_handler.setLevel(logging.CRITICAL)
        self.console_handler.setFormatter(
            logging.Formatter('[%(levelname)s](%(name)s): %(message)s'))
        self.logger.addHandler(self.console_handler)
        self.logger.info('Writing logs to file %s', log_file)
        self.logger.setLevel(logging.DEBUG)

        if args is None:
            args = sys.argv[1:]
        self.args = self.argparser_setup(args)
        self.set_log_level_from_verbose()

        # always write everything to the rotating log files
        if not os.path.exists('logs'):
            os.mkdir('logs')
        files_to_be_removed = []
        old_logs = time.time()-LOGS_TTL
        for root, _, files in os.walk('logs/'):
            for name in files:
                if str(name).find('_mbed-flasher.txt') != -1:
                    if old_logs > time.mktime(
                            time.strptime(str(name).split('_')[0], "%Y%m%d-%H%M%S")):
                        files_to_be_removed.append(str(os.path.join(root, name)))
                elif str(name).find('mbed-flasher.log') != -1:
                    files_to_be_removed.append(str(os.path.join(root, name)))

        if files_to_be_removed:
            for filename in files_to_be_removed:
                try:
                    os.remove(filename)
                except OSError as err:
                    print(err)


    def execute(self):
        """
        :return: 0 or args.func()
        """
        if self.args.func:
            return self.args.func(self.args)
        self.parser.print_usage()
        return EXIT_CODE_SUCCESS

    def argparser_setup(self, sysargs):
        """! Configure CLI (Command Line options) options
        @return Returns ArgumentParser's tuple of (options, arguments)
        @details Add new command line options
        """

        parser = argparse.ArgumentParser('mbedflash',
                                         description="For specific command help, "
                                                     "run: mbedflash <command> --help")


        parser.add_argument('-v', '--verbose',
                            dest="verbose",
                            action="count",
                            help="Verbose level... repeat up to three times.")

        parser.add_argument('-s', '--silent',
                            dest="silent",
                            default=False,
                            action="store_true",
                            help="Silent - only errors will be printed.")

        subparsers = parser.add_subparsers(title='command',
                                           dest='command',
                                           help='command help',
                                           metavar='<command>')
        subparsers.required = True
        get_subparser(subparsers,
                      'list',
                      func=self.subcmd_list_platforms,
                      help='Prints a list of supported platforms.')
        get_subparser(subparsers,
                      'flashers',
                      func=self.subcmd_list_flashers,
                      help='Prints a list of supported flashers.')
        get_subparser(subparsers,
                      'version',
                      func=self.subcmd_version_handler,
                      help='Display version information')

        # Initialize flash command
        parser_flash = get_resource_subparser(subparsers,
                                              'flash',
                                              func=self.subcmd_flash_handler,
                                              help='Flash given resource')
        parser_flash.add_argument('-i', '--input',
                                  help='Binary input to be flashed.',
                                  default=None, metavar='INPUT')
        parser_flash.add_argument('--tid', '--target_id',
                                  help='Target to be flashed, '
                                       'ALL will flash all connected devices '
                                       'with given platform-name, '
                                       'also multiple targets can be given. '
                                       'Short target_id matches boards by prefix',
                                  default=None, metavar='TARGET_ID', action='append')
        parser_flash.add_argument('-t', '--platform_name',
                                  help='Platform of the target device(s)',
                                  default=None)
        parser_flash.add_argument('--no-reset',
                                  help='Do not reset device before or after flashing',
                                  default=None, dest='no_reset', action='store_true')
        parser_flash.add_argument('method', help='<simple|pyocd|edbg>, used for flashing',
                                  metavar='method',
                                  choices=['simple', 'pyocd', 'edbg'],
                                  nargs='?')
        # Initialize reset command
        parser_reset = get_resource_subparser(subparsers, 'reset',
                                              func=self.subcmd_reset_handler,
                                              help='Reset given resource')
        parser_reset.add_argument('--tid', '--target_id',
                                  help='Target to be reset or ALL, '
                                       'also multiple targets can be given.'
                                       'Does not continue flashing next device in case of failures.'
                                       'Short target_id matches boards by prefix',
                                  default=None, metavar='TARGET_ID', action='append')
        parser_reset.add_argument('method',
                                  help='<simple|pyocd|edbg>, used for reset',
                                  metavar='method',
                                  choices=['simple', 'pyocd', 'edbg'],
                                  nargs='?')
        # Initialize erase command
        parser_erase = get_resource_subparser(subparsers, 'erase',
                                              func=self.subcmd_erase_handler,
                                              help='Erase given resource')
        parser_erase.add_argument('--tid', '--target_id',
                                  help='Target to be erased or ALL, '
                                       'also multiple targets can be given. '
                                       'Short target_id matches boards by prefix',
                                  default=None, metavar='TARGET_ID', action='append')
        parser_erase.add_argument('--no-reset',
                                  help='Do not reset device after erase',
                                  default=None, dest='no_reset', action='store_true')
        parser_erase.add_argument('method',
                                  help='<simple|pyocd|edbg>, used for erase',
                                  metavar='method',
                                  choices=['simple', 'pyocd', 'edbg'],
                                  nargs='?')

        #parser.add_argument('-m', '--mapping',
        #                    dest='device_mapping_table', help='Device mapping table.')

        args = parser.parse_args(args=sysargs)
        if 'method' in args:
            if args.method is None:
                args.method = 'simple'
        self.parser = parser
        return args

    def set_log_level_from_verbose(self):
        """ set logging level, silent, or some of verbose level
        :param args: command line arguments
        """
        if self.args.silent:
            self.console_handler.setLevel('NOTSET')
        elif not self.args.verbose:
            self.console_handler.setLevel('ERROR')
        elif self.args.verbose == 1:
            self.console_handler.setLevel('WARNING')
        elif self.args.verbose == 2:
            self.console_handler.setLevel('INFO')
        elif self.args.verbose >= 3:
            self.console_handler.setLevel('DEBUG')
        else:
            self.logger.critical("UNEXPLAINED NEGATIVE COUNT!")

    # the cli decorator doesn't need self as a arg,
    # operation wrapper is used
    # pylint: disable=no-self-argument, not-callable
    def cli_decorator(operation):
        """
        cli decorator
        """
        def operation_wrapper(self, args):
            """
            wrapper
            """
            retcode = operation(self, args)
            return retcode
        return operation_wrapper

    # pylint: disable=too-many-return-statements
    @cli_decorator
    def subcmd_flash_handler(self, args):
        """
        flash command handler
        """
        flasher = Flash()
        available = flasher.get_available_device_mapping()
        available_target_ids = []
        retcode = 0
        #print(args)
        if args.input:
            if not isfile(args.input):
                print("Could not find given file: %s" % args.input)
                return EXIT_CODE_FILE_MISSING
        else:
            print("File is missing")
            return EXIT_CODE_FILE_MISSING
        if args.platform_name:
            if args.platform_name not in flasher.get_supported_targets():
                print("Not supported platform: %s" % args.platform_name)
                print("Supported platforms: %s" % flasher.get_supported_targets())
                return EXIT_CODE_NOT_SUPPORTED_PLATFORM

        if not args.tid:
            print("Target_id is missing")
            return EXIT_CODE_TARGET_ID_MISSING

        if 'all' in args.tid:
            retcode = flasher.flash(build=args.input, target_id='all',
                                    platform_name=args.platform_name,
                                    method=args.method, no_reset=args.no_reset)

        if len(available) <= 0:
            print("Could not find any connected device")
            return EXIT_CODE_DEVICES_MISSING

        available_platforms, target_ids_to_flash = \
            self.prepare_platforms_and_targets(available, args.tid, available_target_ids)

        if not target_ids_to_flash:
            print("Could not find given target_id from attached devices")
            print("Available target_ids:")
            print(available_target_ids)
            return EXIT_CODE_COULD_NOT_MAP_DEVICE

        elif len(available_platforms) > 1:
            if not args.platform_name:
                print("More than one platform detected for given target_id")
                print("Please specify the platform with -t <PLATFORM_NAME>")
                print("Found platforms:")
                print(available_platforms)
                return EXIT_CODE_PLATFORM_REQUIRED
        else:
            #print(target_ids_to_flash)
            retcode = flasher.flash(build=args.input,
                                    target_id=target_ids_to_flash,
                                    platform_name=available_platforms[0],
                                    method=args.method,
                                    no_reset=args.no_reset)

        return retcode

    @staticmethod
    def prepare_platforms_and_targets(available, tid, available_target_ids):
        """
        prepare available platforms and target ids to flash
        """
        available_platforms = []
        target_ids_to_flash = []

        for device in available:
            available_target_ids.append(device['target_id'])
            if isinstance(tid, list):
                for item in tid:
                    if device['target_id'] == item \
                            or device['target_id'].startswith(item):
                        if device['target_id'] not in target_ids_to_flash:
                            target_ids_to_flash.append(device['target_id'])

                        if 'platform_name' in device \
                                and device['platform_name'] not in available_platforms:
                            available_platforms.append(device['platform_name'])

            else:
                if device['target_id'] == tid \
                        or device['target_id'].startswith(tid):
                    if device['target_id'] not in target_ids_to_flash:
                        target_ids_to_flash.append(device['target_id'])

                    if 'platform_name' in device and \
                                    device['platform_name'] not in available_platforms:
                        available_platforms.append(device['platform_name'])

        return available_platforms, target_ids_to_flash

    def subcmd_reset_handler(self, args):
        """
        reset command handler
        """
        resetter = Reset()
        if args.tid:
            ids = self.parse_id_to_devices(args.tid)
            if isinstance(ids, int):
                retcode = ids
            else:
                retcode = resetter.reset(target_id=ids, method=args.method)
        else:
            print("Target_id is missing")
            return EXIT_CODE_TARGET_ID_MISSING

        return retcode

    def subcmd_erase_handler(self, args):
        """
        erase command handler
        """
        eraser = Erase()
        if args.tid:
            ids = self.parse_id_to_devices(args.tid)
            if isinstance(ids, int):
                retcode = ids
            else:
                retcode = eraser.erase(target_id=ids,
                                       no_reset=args.no_reset,
                                       method=args.method)
        else:
            print("Target_id is missing")
            return EXIT_CODE_TARGET_ID_MISSING

        return retcode

    # args not used, but the logic to call sub cmd handler is passing two args
    # pylint: disable=unused-argument
    def subcmd_version_handler(self, args):
        """
        version command handler
        """
        import pkg_resources  # part of setuptools
        versions = pkg_resources.require("mbed-flasher")
        if self.args.verbose:
            for version in versions:
                print(version)
        else:
            print(versions[0].version)

        return EXIT_CODE_SUCCESS

    # pylint: disable=no-self-use
    def subcmd_list_platforms(self, args):
        """
        list platform command
        """
        flasher = Flash()
        print(json.dumps(flasher.get_supported_targets()))
        return EXIT_CODE_SUCCESS

    def subcmd_list_flashers(self, args):
        """
        list flasher command handler
        """
        flasher = Flash()
        print(json.dumps(flasher.get_supported_flashers()))
        return EXIT_CODE_SUCCESS

    def parse_id_to_devices(self, tid):
        """
        :param tid: target id
        """
        flasher = Flash()
        available = flasher.get_available_device_mapping()
        target_ids = []
        available_target_ids = []
        if not available:
            print("Could not find any connected device")
            return EXIT_CODE_DEVICES_MISSING
        if 'all' in tid:
            for device in available:
                target_ids.append(device['target_id'])
        else:
            for item in tid:
                for device in available:
                    available_target_ids.append(device['target_id'])
                    if device['target_id'] == item or \
                            device['target_id'].startswith(item):
                        if device['target_id'] not in target_ids:
                            target_ids.append(device['target_id'])
        if not target_ids:
            print("Could not find given target_id from attached devices")
            print("Available target_ids:")
            print(available_target_ids)
            return EXIT_CODE_COULD_NOT_MAP_DEVICE

        if len(target_ids) == 1:
            return target_ids[0]

        return target_ids

def mbedflash_main():
    """
    Function used to drive CLI (command line interface) application.
    Function exits back to command line with ERRORLEVEL

    Returns:
        Function exits with success-code
    """

    cli = FlasherCLI()
    retcode = cli.execute()
    if retcode:
        try:
            cli.logger.error("Failed: %s", FAILURE_RETURN_CODE_MAPPING_TABLE[retcode])
        except KeyError:
            cli.logger.error("Failed with unknown reason: %s", str(retcode))
    exit(retcode)

if __name__ == '__main__':
    mbedflash_main()
