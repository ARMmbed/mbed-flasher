import platform 
from FlasherMbed import FlasherMbed
from FlasherAtmelAt import FlasherAtmelAt

AvailableFlashers = [
    FlasherMbed
]

if platform.system() == 'Windows':
    AvailableFlashers.append(FlasherAtmelAt)