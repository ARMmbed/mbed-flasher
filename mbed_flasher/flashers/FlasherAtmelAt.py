"""
mbed SDK
Copyright (c) 2011-2015 ARM Limited
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author:
Jussi Vatjus-Anttila <jussi.vatjus-anttila@arm.com>

Note:

These devices is not originally mbed -devices, but is also supported
"""

import os
import re
import subprocess
import logging
import tempfile
import platform


class FlasherAtmelAt(object):
    name = "Atprogram"
    exe = None
    supported_targets = ["SAM4E"]
    logger = logging

    def __init__(self, exe=None):
        FlasherAtmelAt.set_atprogram_exe(exe)
        self.logger = logging.getLogger('mbed-flasher')

    @staticmethod
    def get_supported_targets():
        return {
            "SAM4E": {
                "yotta_targets": [],
                "properties": {
                    "binary_type": ".bin",
                    "copy_method": "atprogram",
                    "reset_method": "default",
                    "program_cycle_s": 0
                }
            }
        }

    @staticmethod
    def set_atprogram_exe(exe):
        FlasherAtmelAt.logger = logging.getLogger('mbed-flasher')
        if exe is None:
            path = ''
            if os.path.exists('C:\\Program Files\\Atmel\\'):
                path = 'C:\\Program Files\\Atmel\\'
            elif os.path.exists('C:\\Program Files (x86)\\Atmel\\'):
                path = 'C:\\Program Files (x86)\\Atmel\\'
            if path:
                for dirpath, subdirs, files in os.walk(path):
                    for x in files:
                        if x.find("atprogram.exe") != -1:
                            FlasherAtmelAt.exe = os.path.join(dirpath, x)
        if not FlasherAtmelAt.exe:
            for ospath in os.environ['PATH'].split(os.pathsep):
                if ospath.find('Atmel') != -1:
                    FlasherAtmelAt.exe = "atprogram.exe"  # assume that atprogram is in path
                    break
            else:
                FlasherAtmelAt.exe = exe
        
        FlasherAtmelAt.logger.debug("atprogram location: %s", FlasherAtmelAt.exe)
    
    @staticmethod
    def set_edbg_exe(exe):
        FlasherAtmelAt.logger = logging.getLogger('mbed-flasher')
        if exe is None:
            if platform.system() == 'Windows':
                FlasherAtmelAt.exe = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', 'bin', 'edbg', 'edbg.exe'))
            elif platform.system() == 'Linux':
                if os.uname()[4].startswith("arm"):
                    FlasherAtmelAt.exe = './' + os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', 'bin', 'edbg', 'edbg_raspbian'))
                else:
                    FlasherAtmelAt.exe = './' + os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', 'bin', 'edbg', 'edbg_ubuntu'))
            elif platform.system() == 'Darwin':
                print "Support for OS X is missing"
                FlasherAtmelAt.exe = None
    
    @staticmethod
    def get_available_devices():
        """list available devices
        """
        FlasherAtmelAt.logger = logging.getLogger('mbed-flasher')
        if platform.system() == 'Windows':
            FlasherAtmelAt.set_atprogram_exe(FlasherAtmelAt.exe)
            if FlasherAtmelAt.exe:
                cmd = FlasherAtmelAt.exe + " list"
                lookup = 'edbg\W+(.*)'
        if not FlasherAtmelAt.exe:
            FlasherAtmelAt.set_edbg_exe(FlasherAtmelAt.exe)
            cmd = FlasherAtmelAt.exe + " --list"
            lookup = '(\S.*) - Atmel.*'
            if not FlasherAtmelAt.exe:
                return []
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        connected_devices = []
        if proc.returncode == 0:
            lines = stdout.splitlines()
            for line in lines:
                ret = FlasherAtmelAt.find_match(line, lookup)
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
    def flash(self, source, target, pyocd=None):
        """flash device
        :param sn: device serial number to be flashed
        :param binary: binary file to be flash
        :return: 0 when flashing success
        """
        if str(self.exe).find('atprogram.exe') != -1:
            cmd = self.exe+" -t edbg -i SWD -d atsam4e16e -s "+target['target_id']+" -v -cl 10mhz  program --verify -f "+ source
        else:
            cmd = self.exe+" -bpv -t atmel_cm4 -s "+target['target_id']+" -f " + source
        FlasherAtmelAt.logger.debug(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        FlasherAtmelAt.logger.debug(stdout)
        FlasherAtmelAt.logger.debug(stderr)
        return proc.returncode

    @staticmethod
    def find_match(line, lookup):
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
