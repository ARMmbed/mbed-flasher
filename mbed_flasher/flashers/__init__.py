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

from mbed_flasher.flashers.FlasherMbed import FlasherMbed as mbed_flasher

# disable Invalid constant name warning, not a const
# pylint: disable=C0103
AvailableFlashers = [
    mbed_flasher
]

'''
if platform.system() == 'Windows':
    for ospath in os.environ['PATH'].split(os.pathsep):
        if ospath.find('Atmel') != -1:
            AvailableFlashers.append(FlasherAtmelAt)
        if FlasherAtmelAt not in AvailableFlashers:
            path = ''
            if os.path.exists('C:\\Program Files\\Atmel\\'):
                path = 'C:\\Program Files\\Atmel\\'
            elif os.path.exists('C:\\Program Files (x86)\\Atmel\\'):
                path = 'C:\\Program Files (x86)\\Atmel\\'
            if path:
                for dirpath, subdirs, files in os.walk(path):
                    for x in files:
                        if x.find("atprogram.exe") != -1:
                            AvailableFlashers.append(FlasherAtmelAt)
'''
