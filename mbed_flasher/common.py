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
import six

from mbed_flasher.return_codes import EXIT_CODE_FILE_MISSING
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_USER_ERROR


from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_UNHANDLED_EXCEPTION


DEFAULT_RETRY_AMOUNT = 3
ALLOWED_FILE_EXTENSIONS = (".bin", ".hex", ".act", ".cfg")


# pylint: disable=too-few-public-methods
class Common(object):
    """
    Class for holding common methods for all operations (flash, erase, reset).
    """
    GET_DEVICES_RETRY = 5

    def __init__(self, logger):
        self.logger = logger

    def get_available_device_mapping(self, flashers, target=None):
        """
        Loop through flashers in search for devices.
        If specific device is given retry multiple times if not found.
        :return: list of available devices
        """

        def get_devices(required_target_id=None):
            """
            Get unique devices from flashers.
            :return: list of devices
            """
            available_devices = []
            for flasher in flashers:
                available_devices.extend(flasher.get_available_devices())

            try:
                # Filter unique devices as flashers could list same devices
                found = list({dev["target_id"]: dev for dev in available_devices}.values())

                # If not searching for specific target, just return what is found.
                if not required_target_id:
                    return found

                for target_id in [device["target_id"] for device in found]:
                    if target in target_id:
                        return found

                raise GeneralFatalError(message="Did not find target",
                                        return_code=EXIT_CODE_COULD_NOT_MAP_DEVICE)
            except (KeyError, TypeError):
                msg = "Invalid device listing from flasher"
                self.logger.exception(msg)
                raise GeneralFatalError(message=msg,
                                        return_code=EXIT_CODE_UNHANDLED_EXCEPTION)

        if isinstance(target, list) and len(target) == 1:
            target = target[0]

        if not isinstance(target, six.string_types) or target == "all":
            return get_devices()

        # This is a workaround for a problem where mbedls (basically mount command)
        # fails to list mount point sometimes in linux. Occurs at least in Raspberry Pi3.
        return retry(logger=self.logger,
                     func=get_devices,
                     func_args=(target, ),
                     retries=Common.GET_DEVICES_RETRY,
                     conditions=[EXIT_CODE_COULD_NOT_MAP_DEVICE])


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


class GeneralFatalError(FlashError):
    """
    Exception class for general errors which should make the program quit immediately.
    """
