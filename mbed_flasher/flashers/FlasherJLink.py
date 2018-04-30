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

from distutils import spawn
import os
try:
    import queue
except ImportError:
    import Queue as queue
import sys
import tempfile

import mbed_lstools

from mbed_flasher.common import FlashError
from mbed_flasher.flashers.FlasherBase import FlasherBase
from mbed_flasher.return_codes import EXIT_CODE_SUCCESS
from mbed_flasher.return_codes import EXIT_CODE_FLASH_FAILED


class FlasherJLink(FlasherBase):
    """
    Class FlasherJLink

    Target on flashing JLink boards with JLinkExe.
    """
    name = "jlink"
    executable = "JLink.exe" if sys.platform.startswith("win") else "JLinkExe"
    supported_targets = None

    def __init__(self, logger=None):
        FlasherBase.__init__(self, logger)

    @staticmethod
    def get_supported_targets():
        """
        :return: supported JLink types
        """
        if not FlasherJLink.supported_targets:
            mbeds = mbed_lstools.create()
            # @todo this is workaround until mbed-ls provide public api
            db_items = list(mbeds.plat_db.items(device_type='jlink'))
            FlasherJLink.supported_targets = sorted([i[1]["platform_name"] for i in db_items])

        return FlasherJLink.supported_targets

    @staticmethod
    def get_available_devices():
        """
        :return: list of available devices
        """
        mbeds = mbed_lstools.create()
        # device_type introduced in mbedls version 1.4.0
        return mbeds.list_mbeds(filter_function=lambda m: m['device_type'] == 'jlink')

    @staticmethod
    def can_flash(target):
        """
        Check if target should be flashed by using JLinkExe.
        :param target: target board
        :return: boolean
        """
        try:
            return target["device_type"] == FlasherJLink.name
        except KeyError:
            return False

    @staticmethod
    def is_executable_installed():
        """
        Check if JLinkExe can be found from path.
        :return: boolean
        """
        return spawn.find_executable(FlasherJLink.executable) is not None

    def flash(self, source, target, method, no_reset):
        """flash device
        :param source: binary to be flashed
        :param target: target to be flashed
        :param method: method to use when flashing
        :param no_reset: do not reset flashed board at all
        :return: 0 when flashing success
        """

        cmd_script = tempfile.NamedTemporaryFile(delete=False)
        FlasherJLink._write_file_contents(cmd_script, source, no_reset)
        cmd_script.close()

        def remove_commander_script():
            """
            Removes the temporary file. Cannot use delete=True for NamedTemporaryFile
            since Windows doesn't allow another program to read it while not closed.
            """
            os.remove(cmd_script.name)

        try:
            args = [
                FlasherJLink.executable,
                "-if", "swd",
                "-speed", "auto",
                "-device", target["jlink_device_name"],
                "-SelectEmuBySN", target["target_id"],
                "-commanderscript", cmd_script.name
            ]
        except KeyError:
            remove_commander_script()
            raise FlashError(message="Invalid target", return_code=EXIT_CODE_FLASH_FAILED)

        try:
            self.logger.info("Flashing {} with command {}".format(target["target_id"], args))
            returncode, output = self._start_and_wait_flash(args, FlasherJLink.executable)
        except queue.Empty:
            raise FlashError(message="No returncode from JLinkExe",
                             return_code=EXIT_CODE_FLASH_FAILED)
        finally:
            remove_commander_script()

        if returncode != 0:
            msg = "Flash of {} failed, with returncode {}".format(target["target_id"], returncode)
            raise FlashError(message=msg, return_code=EXIT_CODE_FLASH_FAILED)

        self.logger.info("Flash of {} succeeded".format(target["target_id"]))
        self.logger.debug(output)
        return EXIT_CODE_SUCCESS

    @staticmethod
    def _write_file_contents(file_obj, source, no_reset):
        # JLinkExe flash has a check for binary content, erase
        # before flash to disable it.
        file_obj.write(b"erase\n")
        file_obj.write(("loadfile {}\n".format(source)).encode())
        if not no_reset:
            file_obj.write(b"r\n")
            file_obj.write(b"g\n")
        file_obj.write(b"exit\n")
        file_obj.flush()
