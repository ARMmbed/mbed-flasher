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
try:
    import queue
except ImportError:
    import Queue as queue
import subprocess
import threading


class FlasherBase(object):
    """
    Class FlasherBase

    Base class for (eventually) all flashers
    """
    name = None
    executable = None
    supported_targets = None
    FLASH_TIMEOUT = 60
    PROCESS_END_TIMEOUT = 10
    QUEUE_TIMEOUT = 5

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger("mbed-flasher")
        self._process = None

    @staticmethod
    def get_supported_targets():
        """
        :return: supported targets
        """
        raise NotImplementedError

    @staticmethod
    def get_available_devices():
        """
        :return: list of available devices
        """
        raise NotImplementedError

    @staticmethod
    def can_flash(target):
        """
        Check if target should be flashed using this flasher.
        :param target: target board
        :return: boolean
        """
        raise NotImplementedError

    @staticmethod
    def is_executable_installed():
        """
        Check if executable needed for flashing is installed
        :return: boolean
        """
        raise NotImplementedError

    def flash(self, source, target, method, no_reset):
        """flash device
        :param source: binary to be flashed
        :param target: target to be flashed
        :param method: method to use when flashing
        :param no_reset: do not reset flashed board at all
        :return: 0 when flashing success
        """
        raise NotImplementedError

    def _start_and_wait_flash(self, args, process_str):
        """
        Initiate and wait for flashing thread to end. Forcefully end
        it if timeout is reached.
        :param thread: thread where flashing process is run
        :param process_str: process string descriptor
        :return: tuple of returncode and output
        """
        def try_end(method, method_str):
            """
            Run method and wait for thread to die
            :param method: method to be run
            :param method_str: textual representation of the method
            """
            if thread.is_alive():
                self.logger.error("Flash timeout, ending {} with {}", process_str, method_str)
                method()
                thread.join(FlasherBase.PROCESS_END_TIMEOUT)

        return_queue = queue.Queue(maxsize=1)
        thread = threading.Thread(target=self._flash_run, args=(args, return_queue))
        thread.start()

        thread.join(FlasherBase.FLASH_TIMEOUT)
        try_end(self._process.terminate, 'terminate')
        try_end(self._process.kill, 'kill')

        return return_queue.get(block=True, timeout=FlasherBase.QUEUE_TIMEOUT)

    def _flash_run(self, command, return_queue):
        """
        Thread target which runs the flashing process in subprocess.
        :param command: Popen arguments
        :param return_queue: channel to return data from thread
        :return: tuple of returncode and output
        """
        self._process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = self._process.communicate()
        returncode = self._process.returncode
        return_queue.put_nowait((returncode, output[0]))
