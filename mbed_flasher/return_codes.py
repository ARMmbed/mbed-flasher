"""
Copyright 2018 ARM Limited

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

# Exit codes

# basic exit codes
EXIT_CODE_SUCCESS = 0
EXIT_CODE_MISUSE_CMD = 2

# generic failures
EXIT_CODE_IMPLEMENTATION_MISSING = 10
EXIT_CODE_OS_ERROR = 11
EXIT_CODE_KEYBOARD_INTERRUPT = 12
EXIT_CODE_SYSTEM_INTERRUPT = 13
EXIT_CODE_FLASH_FAILED = 14
EXIT_CODE_RESET_FAIL = 15
EXIT_CODE_FILE_DOES_NOT_EXIST = 16
EXIT_CODE_FILE_COULD_NOT_BE_READ = 17
EXIT_CODE_TARGET_ID_CONFLICT = 18

# device mapping related failure codes
EXIT_CODE_TARGET_ID_MISSING = 20
EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE = 21
EXIT_CODE_COULD_NOT_MAP_DEVICE = 22
EXIT_CODE_COULD_NOT_MAP_ALL_DEVICE = 23
EXIT_CODE_FILE_MISSING = 24
EXIT_CODE_NOT_SUPPORTED_PLATFORM = 25
EXIT_CODE_PLATFORM_REQUIRED = 26
EXIT_CODE_REQUESTED_FLASHER_DOES_NOT_EXIST = 27
EXIT_CODE_DEVICES_MISSING = 28

# serial port related failure codes
EXIT_CODE_SERIAL_PORT_OPEN_FAILED = 40
EXIT_CODE_SERIAL_RESET_FAILED = 41
EXIT_CODE_SERIAL_PORT_MISSING = 42
EXIT_CODE_SERIAL_PORT_REAPPEAR_TIMEOUT = 43

# Mount point related failure codes
EXIT_CODE_MOUNT_POINT_MISSING = 50
EXIT_CODE_FILE_STILL_PRESENT = 51

# PyOCD related failure codes
EXIT_CODE_PYOCD_MISSING = 60
EXIT_CODE_PYOCD_ERASE_FAILED = 61
EXIT_CODE_PYOCD_RESET_FAILED = 62
EXIT_CODE_PYOCD_NOT_INSTALLED = 63

# egdb related failure codes
EXIT_CODE_EGDB_NOT_SUPPORTED = 70

# Daplink related issues
EXIT_CODE_DAPLINK_SOFTWARE_ERROR = 100
EXIT_CODE_DAPLINK_TRANSIENT_ERROR = 101
EXIT_CODE_DAPLINK_USER_ERROR = 102
EXIT_CODE_DAPLINK_TARGET_ERROR = 103
EXIT_CODE_DAPLINK_INTERFACE_ERROR = 104

FAILURE_RETURN_CODE_MAPPING_TABLE = {
    EXIT_CODE_MISUSE_CMD: 'misuse cmd',
    EXIT_CODE_IMPLEMENTATION_MISSING: 'implementation missing',
    EXIT_CODE_OS_ERROR: 'os error',
    EXIT_CODE_KEYBOARD_INTERRUPT: 'keyboard interrupt',
    EXIT_CODE_SYSTEM_INTERRUPT: 'system interrupt',
    EXIT_CODE_FLASH_FAILED: 'flash failed',
    EXIT_CODE_RESET_FAIL: 'reset fail',
    EXIT_CODE_FILE_DOES_NOT_EXIST: 'file does not exists',
    EXIT_CODE_FILE_COULD_NOT_BE_READ: 'file could not be read',
    EXIT_CODE_TARGET_ID_CONFLICT: 'target id conflict',
    EXIT_CODE_TARGET_ID_MISSING: 'target id missing',
    EXIT_CODE_COULD_NOT_MAP_TARGET_ID_TO_DEVICE: 'could not map target id to device',
    EXIT_CODE_COULD_NOT_MAP_DEVICE: 'could not map device',
    EXIT_CODE_COULD_NOT_MAP_ALL_DEVICE: 'could not map all device',
    EXIT_CODE_FILE_MISSING: 'file missing',
    EXIT_CODE_NOT_SUPPORTED_PLATFORM: 'not supported platform',
    EXIT_CODE_PLATFORM_REQUIRED: 'platform required',
    EXIT_CODE_REQUESTED_FLASHER_DOES_NOT_EXIST: 'requested flashed does not exists',
    EXIT_CODE_DEVICES_MISSING: 'devices missing',
    EXIT_CODE_SERIAL_PORT_OPEN_FAILED: 'serial port open failed',
    EXIT_CODE_SERIAL_RESET_FAILED: 'serial reset failed',
    EXIT_CODE_SERIAL_PORT_MISSING: 'serial port missing',
    EXIT_CODE_SERIAL_PORT_REAPPEAR_TIMEOUT: 'serial port reappear timeout',
    EXIT_CODE_MOUNT_POINT_MISSING: 'mount point missing',
    EXIT_CODE_FILE_STILL_PRESENT: 'file still present',
    EXIT_CODE_PYOCD_MISSING: 'pyocd missing',
    EXIT_CODE_PYOCD_ERASE_FAILED: 'pyocd erase failed',
    EXIT_CODE_PYOCD_RESET_FAILED: 'pyocd reset failed',
    EXIT_CODE_PYOCD_NOT_INSTALLED: 'pyocd not installed',
    EXIT_CODE_EGDB_NOT_SUPPORTED: 'egdb  not supported',
    EXIT_CODE_DAPLINK_SOFTWARE_ERROR: 'daplink software error',
    EXIT_CODE_DAPLINK_TRANSIENT_ERROR: 'daplink transient error',
    EXIT_CODE_DAPLINK_USER_ERROR: 'daplink user error',
    EXIT_CODE_DAPLINK_TARGET_ERROR: 'daplink target error',
    EXIT_CODE_DAPLINK_INTERFACE_ERROR: 'daplink interface error'
}
