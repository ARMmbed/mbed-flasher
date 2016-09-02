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

import os
import re
import subprocess
import logging
import tempfile


class FlasherAtmelAt(object):
    name = "atmel"
    exe = None
    supported_targets = ["SAM4E"]
    logger = logging

    def __init__(self, exe=None):
        FlasherAtmelAt.set_atprogram_exe(exe)
        self.logger = logging.getLogger('mbed-flasher')

    @staticmethod
    def get_supported_targets():
        return ["SAM4E"]

    @staticmethod
    def set_atprogram_exe(exe):
        if exe is None:
            path = ''
            if os.path.exists('C:\\Program File\\Atmel\\'):
                path = 'C:\\Program Files\\Atmel\\'
            elif os.path.exists('C:\\Program File (x86)\\Atmel\\'):
                path = 'C:\\Program Files (x86)\\Atmel\\'
            if path:
                for dirpath, subdirs, files in os.walk(path):
                    for x in files:
                        if x.find("atprogram.exe") != -1:
                            FlasherAtmelAt.exe = os.path.join(dirpath, x)
                            print FlasherAtmelAt.exe
        if not FlasherAtmelAt.exe:
            for ospath in os.environ['PATH'].split(os.pathsep):
                if ospath.find('Atmel') != -1:
                    FlasherAtmelAt.exe = "atprogram.exe"  # assume that atprogram is in path
                    break
            else:
                FlasherAtmelAt.exe = exe
        
        FlasherAtmelAt.logger.debug("atprogram location: %s", FlasherAtmelAt.exe)

    @staticmethod
    def get_available_devices():
        """list available devices
        """
        if not FlasherAtmelAt.exe:
            return []
        FlasherAtmelAt.set_atprogram_exe(FlasherAtmelAt.exe)
        cmd = FlasherAtmelAt.exe + " list"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        connected_devices = []
        if proc.returncode == 0:
            lines = stdout.splitlines()
            for line in lines:
                ret = FlasherAtmelAt.find(line, 'edbg\W+(.*)')
                if ret:
                    connected_devices.append({
                        "platform_name": "SAM4E",
                        "serial_port": None,
                        "mount_point": None,
                        "target_id": ret,
                        "baud_rate": 460800
                    })
        FlasherAtmelAt.logger.debug("Connected atprogrammer supported devices: %s", connected_devices)
        return connected_devices

    # actual flash procedure
    def flash(self, source, target):
        """flash device
        :param sn: device serial number to be flashed
        :param binary: binary file to be flash
        :return: 0 when flashing success
        """
        with tempfile.TemporaryFile() as temp:
            temp.write(source)
            temp.close()
            temp.name
            # actual flash procedure

            cmd = self.exe+" -t edbg -i SWD -d atsam4e16e -s "+target['target_id']+" -v -cl 10mhz  program --verify -f "+temp.name
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            FlasherAtmelAt.logger.debug(stdout)
            FlasherAtmelAt.logger.debug(stderr)
            return proc.returncode

    @staticmethod
    def lookupExe(alternatives):
        """lookup existing exe
        :param alternatives: exes
        :return: founded exe
        """
        for exe in alternatives:
            if os.path.exists(exe):
                return exe
        return None

    @staticmethod
    def find(line, lookup):
        """find with regexp
        :param line:
        :param lookup:
        :return:
        """
        m = re.search(lookup, line)
        if m:
            if m.group(1):
                return m.group(1)
        return False
