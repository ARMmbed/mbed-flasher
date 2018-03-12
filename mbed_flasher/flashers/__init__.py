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
from mbed_flasher.flashers.FlasherJLink import FlasherJLink as jlink_flasher

# disable Invalid constant name warning, not a const
# pylint: disable=C0103
AvailableFlashers = []

# Order matters since JLinkExe flash is preferred for JLink boards
if jlink_flasher.is_executable_installed():
    AvailableFlashers.append(jlink_flasher)
AvailableFlashers.append(mbed_flasher)
