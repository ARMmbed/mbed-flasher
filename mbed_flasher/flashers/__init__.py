import platform
import os
from FlasherMbed import FlasherMbed
from FlasherAtmelAt import FlasherAtmelAt

AvailableFlashers = [
    FlasherMbed
]

if platform.system() == 'Windows':
    for dir in os.environ['PATH'].split(os.pathsep):
        if dir.find('Atmel') != -1:
            AvailableFlashers.append(FlasherAtmelAt)
        if not FlasherAtmelAt in AvailableFlashers:
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