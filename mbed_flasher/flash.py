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

from mbed_flasher.common import Logger, FlashError,\
    check_file, check_file_exists, check_file_extension
from mbed_flasher.flashers.FlasherMbed import FlasherMbed
from mbed_flasher.flashers.FlasherPyOCD import FlasherPyOCD, ConnectMode
from mbed_flasher.mbed_common import MbedCommon
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_KEYBOARD_INTERRUPT
from mbed_flasher.return_codes import EXIT_CODE_SYSTEM_INTERRUPT
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD


# pylint: disable=too-few-public-methods
class Flash(object):
    """ Flash object, which manage flashing single device
    """
    _flashers = []
    supported_targets = {}

    MSD_METHOD = 'msd'
    PYOCD_METHOD = 'pyocd'

    def __init__(self, logger=None):
        if logger is None:
            logger = Logger('mbed-flasher')
            logger = logger.logger
        self.logger = logger

    # pylint: disable=too-many-arguments
    def flash(self, build, target_id=None, method=MSD_METHOD, no_reset=None,
              pyocd_platform=None, pyocd_pack=None,
              pyocd_connect_mode=ConnectMode.UNDER_RESET.value):
        """Flash (mbed) device
        :param build: string (file-path)
        :param target_id: target_id
        :param method: method for flashing i.e. simple
        :param no_reset: whether to reset the board after flash
        :param pyocd_platform: target platform to pyocd
        :param pyocd_pack: pack file path to pyocd
        :param pyocd_connect_mode: connect_mode used with pyocd
        """
        if target_id is None:
            msg = "Target_id is missing"
            raise FlashError(message=msg,
                             return_code=EXIT_CODE_TARGET_ID_MISSING)

        check_file(self.logger, build)
        check_file_exists(self.logger, build)
        check_file_extension(self.logger, build)

        target_mbed = MbedCommon.refresh_target(target_id)
        if target_mbed is None:
            raise FlashError(message="Did not find target: {}".format(target_id),
                             return_code=EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

        self.logger.debug("Flashing: %s", target_mbed["target_id"])

        try:
            if method == Flash.MSD_METHOD:
                FlasherMbed(logger=self.logger).flash(
                    source=build, target=target_mbed, no_reset=no_reset)
            elif method == Flash.PYOCD_METHOD:
                FlasherPyOCD(logger=self.logger).flash(
                    source=build,
                    target=target_mbed,
                    no_reset=no_reset,
                    platform=pyocd_platform,
                    pack=pyocd_pack,
                    connect_mode=pyocd_connect_mode)
            else:
                raise FlashError(message="Selected method {} not supported".format(method),
                                 return_code=EXIT_CODE_MISUSE_CMD)
        except KeyboardInterrupt:
            raise FlashError(message="Aborted by user",
                             return_code=EXIT_CODE_KEYBOARD_INTERRUPT)
        except SystemExit:
            raise FlashError(message="Aborted by SystemExit event",
                             return_code=EXIT_CODE_SYSTEM_INTERRUPT)

        self.logger.info("%s flash success", target_mbed["target_id"])

        return EXIT_CODE_SUCCESS
