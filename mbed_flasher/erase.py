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
Veli-Matti Lahtela <veli-matti.lahtela@arm.com>
"""

import logging
import types

EXIT_CODE_COULD_NOT_MAP_TO_DEVICE = 21
EXIT_CODE_PYOCD_MISSING = 23
EXIT_CODE_PYOCD_ERASE_FAILED = 27
EXIT_CODE_NONSUPPORTED_METHOD_FOR_ERASE = 29
EXIT_CODE_IMPLEMENTATION_MISSING = 31

class Erase(object):
    """ Flash object, which manage flashing single device
    """

    def __init__(self):
        self.logger = logging.getLogger('mbed-flasher')
        self.FLASHERS = self.__get_flashers()

    def get_available_device_mapping(self):
        available_devices = []
        for Flasher in self.FLASHERS:
            devices = Flasher.get_available_devices()
            available_devices.extend(devices)
        return available_devices

    @staticmethod
    def __get_flashers():
        from flashers import AvailableFlashers
        return AvailableFlashers
    
    def erase_board(self, mount_point):
        print "Not supported yet"
        return EXIT_CODE_IMPLEMENTATION_MISSING

    def erase(self, target_id=None, method=None):
        """Erase (mbed) device
        :param target_id: target_id
        :param method: method for erase i.e. simple, pyocd or edbg
        """
        self.logger.info("Starting erase for given target_id %s" % target_id)
        self.logger.info("method used for reset: %s" % method)
        available_devices = self.get_available_device_mapping()
        targets_to_erase = []
        
        if isinstance(target_id, types.ListType):
            for target in target_id:
                for device in available_devices:
                    if target == device['target_id']:
                        if device not in targets_to_erase:
                            targets_to_erase.append(device)
        else:
            if target_id == 'all':
               targets_to_erase = available_devices
            elif len(target_id) <= 48:
                for device in available_devices:
                    if target_id == device['target_id'] or device['target_id'].startswith(target_id):
                        if device not in targets_to_erase:
                            targets_to_erase.append(device)
        
        if len(targets_to_erase) > 0:
            for item in targets_to_erase:
                if item['platform_name'] == 'K64F':
                    if method == 'simple' and 'mount_point' in item:
                        self.erase_board(item['mount_point'])
                    elif method == 'pyocd':
                        try:
                            from pyOCD.board import MbedBoard
                            from pyOCD.pyDAPAccess import DAPAccessIntf
                        except ImportError:
                            print 'pyOCD missing, install it\n'
                            return EXIT_CODE_PYOCD_MISSING
                        board = MbedBoard.chooseBoard(board_id=item["target_id"]) 
                        self.logger.info("erasing device")
                        ocd_target = board.target
                        flash = ocd_target.flash
                        try:
                            flash.eraseAll()
                            ocd_target.reset()
                        except DAPAccessIntf.TransferFaultError as e:
                            pass
                        self.logger.info("erase completed")
                    elif method == 'edbg':
                        print "Not supported yet"
                    else:
                        print "Selected method %s not supported" % method
                        return EXIT_CODE_NONSUPPORTED_METHOD_FOR_ERASE
                else:
                    print "Only mbed devices supported"
                    return EXIT_CODE_IMPLEMENTATION_MISSING
        else:
            print "Could not map given target_id(s) to available devices"
            return EXIT_CODE_COULD_NOT_MAP_TO_DEVICE
        
        retcode = 0
        return retcode
