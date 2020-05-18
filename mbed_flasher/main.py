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
import traceback

from mbed_flasher.common import FlashError, EraseError, ResetError
from mbed_flasher.flashers.FlasherPyOCD import ConnectMode
from mbed_flasher.flash import Flash
from mbed_flasher.erase import Erase
from mbed_flasher.reset import Reset
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_UNHANDLED_EXCEPTION


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
        # Log to the console at a level determined by the --verbose flag
        self.console_handler = logging.StreamHandler()  # sys.stderr
        # set correct level later by set_log_level_from_verbose() in interactive sessions
        self.console_handler.setLevel(logging.CRITICAL)
        self.console_handler.setFormatter(
            logging.Formatter('[%(levelname)s](%(name)s): %(message)s'))
        self.logger.addHandler(self.console_handler)
        self.logger.setLevel(logging.DEBUG)
        self.parser = None
        if args is None:
            args = sys.argv[1:]
        self.args = self.argparser_setup(args)
        self.set_log_level_from_verbose()

    def execute(self):
        """
        :return: 0 or args.func()
        """
        if self.args.func:
            return self.args.func()
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

        parser.add_argument('--version',
                            action='version',
                            version=FlasherCLI._get_version())

        subparsers = parser.add_subparsers(title='command',
                                           dest='command',
                                           help='command help',
                                           metavar='<command>')
        subparsers.required = True

        # Initialize flash command
        parser_flash = get_resource_subparser(subparsers,
                                              'flash',
                                              func=self.subcmd_flash_handler,
                                              help='Flash given resource')
        parser_flash.add_argument('-i', '--input',
                                  help='Binary input to be flashed.',
                                  default=None, metavar='INPUT')
        parser_flash.add_argument('--tid', '--target_id',
                                  help='Target to be flashed',
                                  default=None, metavar='TARGET_ID')
        parser_flash.add_argument('--no-reset',
                                  help='Do not drive any external reset to the device',
                                  default=None, dest='no_reset', action='store_true')
        parser_flash.add_argument('--method',
                                  help='Select flash method to be used',
                                  default=Flash.MSD_METHOD,
                                  choices=[Flash.MSD_METHOD, Flash.PYOCD_METHOD])
        parser_flash.add_argument('--pyocd_platform',
                                  help='PyOCD target platform, only used with pyocd method',
                                  default=None,
                                  metavar='PYOCD_PLATFORM')
        parser_flash.add_argument('--pyocd_pack',
                                  help='PyOCD pack, only used with pyocd method',
                                  default=None,
                                  metavar='PYOCD_PACK')
        parser_flash.add_argument('--pyocd_connect_mode',
                                  help='PyOCD connect mode, only used with pyocd method',
                                  default=ConnectMode.UNDER_RESET.value,
                                  choices=[ConnectMode.HALT.value,
                                           ConnectMode.PRE_RESET.value,
                                           ConnectMode.UNDER_RESET.value,
                                           ConnectMode.ATTACH.value],
                                  metavar='PYOCD_CONNECT_MODE')
        # Initialize reset command
        parser_reset = get_resource_subparser(subparsers, 'reset',
                                              func=self.subcmd_reset_handler,
                                              help='Reset given resource')
        parser_reset.add_argument('--tid', '--target_id',
                                  help='Target to be reset',
                                  default=None, metavar='TARGET_ID')
        parser_reset.add_argument('--method',
                                  help='<simple>, used for reset',
                                  default='simple',
                                  choices=['simple'])
        # Initialize erase command
        parser_erase = get_resource_subparser(subparsers, 'erase',
                                              func=self.subcmd_erase_handler,
                                              help='Erase given resource')
        parser_erase.add_argument('--tid', '--target_id',
                                  help='Target to be erased',
                                  default=None, metavar='TARGET_ID')
        parser_erase.add_argument('--no-reset',
                                  help='Do not reset device after erase',
                                  default=None, dest='no_reset', action='store_true')
        parser_erase.add_argument('--method',
                                  help='Select erase method to be used',
                                  default=Flash.MSD_METHOD,
                                  choices=[Flash.MSD_METHOD, Flash.PYOCD_METHOD])
        parser_erase.add_argument('--pyocd_platform',
                                  help='PyOCD target platform, only used with pyocd method',
                                  default=None,
                                  metavar='PYOCD_PLATFORM')
        parser_erase.add_argument('--pyocd_pack',
                                  help='PyOCD pack, only used with pyocd method',
                                  default=None,
                                  metavar='PYOCD_PACK')
        parser_erase.add_argument('--pyocd_connect_mode',
                                  help='PyOCD connect mode, only used with pyocd method.',
                                  default=ConnectMode.UNDER_RESET.value,
                                  choices=[ConnectMode.HALT.value,
                                           ConnectMode.PRE_RESET.value,
                                           ConnectMode.UNDER_RESET.value,
                                           ConnectMode.ATTACH.value],
                                  metavar='PYOCD_CONNECT_MODE')

        args = parser.parse_args(args=sysargs)
        if 'method' in args:
            if args.method is None:
                args.method = 'simple'
        self.parser = parser
        return args

    def set_log_level_from_verbose(self):
        """ set logging level, silent, or some of verbose level
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

    def subcmd_flash_handler(self):
        """
        flash command handler
        """
        flasher = Flash()
        return flasher.flash(
            build=self.args.input,
            target_id=self.args.tid,
            method=self.args.method,
            no_reset=self.args.no_reset,
            pyocd_platform=self.args.pyocd_platform,
            pyocd_pack=self.args.pyocd_pack,
            pyocd_connect_mode=self.args.pyocd_connect_mode)

    def subcmd_reset_handler(self):
        """
        reset command handler
        """
        reset = Reset()
        return reset.reset(target_id=self.args.tid, method=self.args.method)

    def subcmd_erase_handler(self):
        """
        erase command handler
        """
        eraser = Erase()
        return eraser.erase(
            target_id=self.args.tid,
            no_reset=self.args.no_reset,
            method=self.args.method,
            pyocd_platform=self.args.pyocd_platform,
            pyocd_pack=self.args.pyocd_pack,
            pyocd_connect_mode=self.args.pyocd_connect_mode)

    @staticmethod
    def _get_version():
        """
        version command handler
        """
        import pkg_resources  # part of setuptools
        versions = pkg_resources.require("mbed-flasher")
        return versions[0].version


def mbedflash_main():
    """
    Function used to drive CLI (command line interface) application.
    Function exits back to command line with ERRORLEVEL

    Returns:
        Function exits with success-code
    """

    cli = FlasherCLI()
    # Catch all exceptions to be able to set specific error format.
    # pylint: disable=broad-except
    try:
        retcode = cli.execute()
        if retcode:
            cli.logger.error("Failed with return code: %s", str(retcode))

        exit(retcode)
    except (FlashError, EraseError, ResetError) as error:
        cli.logger.error("Failed: %s", error.message)
        exit(error.return_code)
    except Exception as error:
        cli.logger.error("Failed with unknown reason: %s", str(error))
        cli.logger.error(traceback.format_exc())
        exit(EXIT_CODE_UNHANDLED_EXCEPTION)


if __name__ == '__main__':
    mbedflash_main()
