import platform
import os
from mbed_flasher.flashers.FlasherMbed import FlasherMbed
from mbed_flasher.flashers.FlasherAtmelAt import FlasherAtmelAt

AvailableFlashers = [
    FlasherMbed
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