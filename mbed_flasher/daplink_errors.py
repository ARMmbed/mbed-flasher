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

from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_SOFTWARE_ERROR
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_TRANSIENT_ERROR
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_USER_ERROR
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_TARGET_ERROR
from mbed_flasher.return_codes import EXIT_CODE_DAPLINK_INTERFACE_ERROR

# pylint: disable=line-too-long
DAPLINK_ERRORS = {
    # DAPLink software error
    "An internal error has occurred": EXIT_CODE_DAPLINK_SOFTWARE_ERROR,
    "End of stream has been reached": EXIT_CODE_DAPLINK_SOFTWARE_ERROR,
    "End of stream is unknown": EXIT_CODE_DAPLINK_SOFTWARE_ERROR,

    # Transient error - Transfer should be retried
    "An error occurred during the transfer": EXIT_CODE_DAPLINK_TRANSIENT_ERROR,
    "Possible mismatch between file size and size programmed": EXIT_CODE_DAPLINK_TRANSIENT_ERROR,
    "File sent out of order by PC. Target might not be programmed correctly.": EXIT_CODE_DAPLINK_TRANSIENT_ERROR,
    "An error has occurred": EXIT_CODE_DAPLINK_TRANSIENT_ERROR,

    # User error
    "The transfer timed out.": EXIT_CODE_DAPLINK_USER_ERROR,
    "The interface firmware ABORTED programming. Image is trying to set security bits": EXIT_CODE_DAPLINK_USER_ERROR,
    "The hex file cannot be decoded. Checksum calculation failure occurred.": EXIT_CODE_DAPLINK_USER_ERROR,
    "The hex file cannot be decoded. Parser logic failure occurred.": EXIT_CODE_DAPLINK_USER_ERROR,
    "The hex file cannot be programmed. Logic failure occurred.": EXIT_CODE_DAPLINK_USER_ERROR,
    "The hex file you dropped isn't compatible with this mode or device.Are you in MAINTENANCE mode? See HELP FAQ.HTM": EXIT_CODE_DAPLINK_USER_ERROR,
    "The hex file offset load address is not correct.": EXIT_CODE_DAPLINK_USER_ERROR,
    "The starting address for the bootloader update is wrong.": EXIT_CODE_DAPLINK_USER_ERROR,
    "The starting address for the interface update is wrong.": EXIT_CODE_DAPLINK_USER_ERROR,
    "The application file format is unknown and cannot be parsed and/or processed.": EXIT_CODE_DAPLINK_USER_ERROR,

    # Target error
    "The interface firmware FAILED to reset/halt the target MCU": EXIT_CODE_DAPLINK_TARGET_ERROR,
    "The interface firmware FAILED to download the flash programming algorithms to the target MCU": EXIT_CODE_DAPLINK_TARGET_ERROR,
    "The interface firmware FAILED to download the flash data contents to be programmed": EXIT_CODE_DAPLINK_TARGET_ERROR,
    "The interface firmware FAILED to initialize the target MCU": EXIT_CODE_DAPLINK_TARGET_ERROR,
    "The interface firmware FAILED to unlock the target for programming": EXIT_CODE_DAPLINK_TARGET_ERROR,
    "Flash algorithm erase sector command FAILURE": EXIT_CODE_DAPLINK_TARGET_ERROR,
    "Flash algorithm erase all command FAILURE": EXIT_CODE_DAPLINK_TARGET_ERROR,
    "Flash algorithm write command FAILURE": EXIT_CODE_DAPLINK_TARGET_ERROR,

    # Interface error
    "In application programming aborted due to an out of bounds address.": EXIT_CODE_DAPLINK_INTERFACE_ERROR,
    "In application programming initialization failed.": EXIT_CODE_DAPLINK_INTERFACE_ERROR,
    "In application programming uninit failed.": EXIT_CODE_DAPLINK_INTERFACE_ERROR,
    "In application programming write failed.": EXIT_CODE_DAPLINK_INTERFACE_ERROR,
    "In application programming sector erase failed.": EXIT_CODE_DAPLINK_INTERFACE_ERROR,
    "In application programming mass erase failed.": EXIT_CODE_DAPLINK_INTERFACE_ERROR,
    "In application programming not supported on this device.": EXIT_CODE_DAPLINK_INTERFACE_ERROR,
    "In application programming failed because the update sent was incomplete.": EXIT_CODE_DAPLINK_INTERFACE_ERROR,
    "The bootloader CRC did not pass.": EXIT_CODE_DAPLINK_INTERFACE_ERROR
}
