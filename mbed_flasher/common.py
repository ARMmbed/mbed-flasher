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
import os
import time

from mbed_flasher.return_codes import EXIT_CODE_FILE_MISSING
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_USER_ERROR


DEFAULT_RETRY_AMOUNT = 3
ALLOWED_FILE_EXTENSIONS = (".bin", ".hex", ".act", ".cfg", ".tar", ".axf")


# pylint: disable=too-few-public-methods
class Logger(object):
    """
    Logger provider
    """
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self.logger.addHandler(logging.NullHandler())
            self.logger.setLevel(logging.ERROR)
            self.logger.propagate = False
            self.logger.info('No logger supplied, using default logging logger')

    def __call__(self, name):
        return self.logger


def retry(logger, func, func_args, retries=DEFAULT_RETRY_AMOUNT, conditions=None):
    """
    Generic retry component.
    :param logger: logger to use
    :param func: function to run and possibly retry
    :param func_args: args for func
    :param retries: max amount of retires
    :param conditions: conditions on when to retry
    :return: latest return code
    """
    if conditions is None:
        conditions = []

    for index in range(retries):
        try:
            return func(*func_args)
        except FlashError as error:
            if error.return_code not in conditions:
                raise error

            index_from_one = index + 1
            if index_from_one == retries:
                raise error

            retry_interval = index_from_one ** 2
            logger.info("Starting retry round {} after {} sleep"
                        .format(index_from_one, retry_interval))
            time.sleep(retry_interval)


def check_is_file_flashable(logger, file_path):
    """
    Checks file existence and extension, raises if any of the checks fail.
    :param logger: logger object
    :param file_path: file to be flashed (string)
    :return: None on success, raise FlashError otherwise
    """
    check_file(logger, file_path)
    check_file_exists(logger, file_path)
    check_file_extension(logger, file_path)


def check_file(logger, file_path):
    """
    CHeck if file_path is not "False"
    :param logger: logger object
    :param file_path: file to be flashed (string)
    :return: None on success, raise FlashError otherwise
    """
    if not file_path:
        msg = "File to be flashed was not given"
        logger.error(msg)
        # pylint: disable=superfluous-parens
        raise FlashError(message=msg, return_code=EXIT_CODE_FILE_MISSING)


def check_file_exists(logger, file_path):
    """
    CHeck if file exists
    :param logger: logger object
    :param file_path: file to be flashed (string)
    :return: None on success, raise FlashError otherwise
    """
    if not os.path.isfile(file_path):
        msg = "Could not find given file: {}".format(file_path)
        logger.error(msg)
        # pylint: disable=superfluous-parens
        raise FlashError(message=msg, return_code=EXIT_CODE_FILE_MISSING)


def check_file_extension(logger, file_path):
    """
    CHeck if file name extension is valid
    :param logger: logger object
    :param file_path: file to be flashed (string)
    :return: None on success, raise FlashError otherwise
    """
    if not file_path.lower().endswith(ALLOWED_FILE_EXTENSIONS):
        msg = "File extension is not supported: {}".format(file_path)
        logger.error(msg)
        # pylint: disable=superfluous-parens
        raise FlashError(message=msg, return_code=EXIT_CODE_DAPLINK_USER_ERROR)


class FlashError(Exception):
    """
    Exception class for flash errors.
    Should be raised when flashing cannot be continued further.
    """
    def __init__(self, message, return_code):
        super(FlashError, self).__init__(message)
        self.message = message
        self.return_code = return_code


class EraseError(FlashError):
    """
    Exception class for erase errors.
    Should be raised when erasing cannot be continued further.
    """


class ResetError(FlashError):
    """
    Exception class for reset errors.
    Should be raised when resetting cannot be continued further.
    """
