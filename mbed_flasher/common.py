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
from time import sleep
import six


DEFAULT_RETRY_AMOUNT = 3


# pylint: disable=too-few-public-methods
class Common(object):
    """
    Class for holding common methods for all operations (flash, erase, reset).
    """
    GET_DEVICES_RETRY = 5
    GET_DEVICES_RETRY_INTERVAL = 1

    def __init__(self, logger):
        self.logger = logger

    def get_available_device_mapping(self, flashers, target=None):
        """
        Loop through flashers in search for devices.
        If specific device is given retry multiple times if not found.
        :return: list of available devices
        """

        def get_devices():
            """
            Get unique devices from flashers.
            :return: list of devices
            """
            available_devices = []
            for flasher in flashers:
                available_devices.extend(flasher.get_available_devices())

            # Filter unique devices as flashers could list same devices
            return list({dev["target_id"]: dev for dev in available_devices}.values())

        if isinstance(target, list) and len(target) == 1:
            target = target[0]

        if not isinstance(target, six.string_types) or target == "all":
            return get_devices()

        devices = []
        # This is a workaround for a problem where mbedls (basically mount command)
        # fails to list mount point sometimes in linux. Occurs at least in Raspberry Pi3.
        for index in range(Common.GET_DEVICES_RETRY):
            if index > 0:
                self.logger.warning("Did not find %s, trying again (%d)", target, index)

            try:
                devices = get_devices()
                for target_id in [device["target_id"] for device in devices]:
                    if target in target_id:
                        return devices
            except (KeyError, TypeError):
                self.logger.exception("Invalid device listing from flasher")
                return []

            sleep(Common.GET_DEVICES_RETRY_INTERVAL)

        self.logger.warning("Did not find %s giving up", target)
        return devices


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
    return_value = None
    if conditions is None:
        conditions = []

    for index in range(retries):
        try:
            return func(*func_args)
        except FlashError as error:
            return_value = error
            if error.return_code not in conditions:
                raise error

        logger.info("Starting retry round {}".format(str(index + 1)))

    # pylint: disable=raising-bad-type
    if isinstance(return_value, Exception):
        raise return_value
    else:
        return return_value


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
