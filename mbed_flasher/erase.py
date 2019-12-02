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

# python 3 compatibility
# pylint: disable=superfluous-parens

from mbed_flasher.common import Logger, EraseError
from mbed_flasher.flashers.FlasherMbed import FlasherMbed
from mbed_flasher.flashers.FlasherPyOCD import FlasherPyOCD
from mbed_flasher.mbed_common import MbedCommon
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE
from mbed_flasher.return_codes import EXIT_CODE_MISUSE_CMD
from mbed_flasher.return_codes import EXIT_CODE_TARGET_ID_MISSING


# pylint: disable=too-few-public-methods
class Erase(object):
    """ Erase object, which manages erasing for given devices
    """

    def __init__(self):
        logger = Logger('mbed-flasher')
        self.logger = logger.logger

    # pylint: disable=too-many-arguments
    def erase(self, target_id=None, no_reset=None, method=None,
              pyocd_platform=None, pyocd_pack=None):
        """
        Erase (mbed) device(s).
        :param target_id: target_id
        :param no_reset: erase with/without reset
        :param method: method for erase
        :param pyocd_platform: target platform to pyocd
        :param pyocd_pack: pack file path to pyocd
        """
        if target_id is None:
            raise EraseError(message="target_id is missing",
                             return_code=EXIT_CODE_TARGET_ID_MISSING)

        target_mbed = MbedCommon.refresh_target(target_id)
        if target_mbed is None:
            raise EraseError(message="Did not find target: {}".format(target_id),
                             return_code=EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE)

        self.logger.info("Erasing: %s", target_id)

        if method == 'msd':
            FlasherMbed(logger=self.logger).erase(target=target_mbed, no_reset=no_reset)
        elif method == 'pyocd':
            FlasherPyOCD(logger=self.logger).erase(
                target=target_mbed, no_reset=no_reset, platform=pyocd_platform, pack=pyocd_pack)
        else:
            raise EraseError(message="Selected method {} not supported".format(method),
                             return_code=EXIT_CODE_MISUSE_CMD)

        return EXIT_CODE_SUCCESS
