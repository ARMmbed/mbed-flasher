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
EXIT_CODE_UNHANDLED_EXCEPTION = 1
EXIT_CODE_MISUSE_CMD = 2

# generic failures
EXIT_CODE_IMPLEMENTATION_MISSING = 10
EXIT_CODE_OS_ERROR = 11
EXIT_CODE_KEYBOARD_INTERRUPT = 12
EXIT_CODE_SYSTEM_INTERRUPT = 13
EXIT_CODE_FLASH_FAILED = 14
EXIT_CODE_RESET_FAIL = 15
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

# Daplink related issues
EXIT_CODE_DAPLINK_SOFTWARE_ERROR = 100
EXIT_CODE_DAPLINK_TRANSIENT_ERROR = 101
EXIT_CODE_DAPLINK_USER_ERROR = 102
EXIT_CODE_DAPLINK_TARGET_ERROR = 103
EXIT_CODE_DAPLINK_INTERFACE_ERROR = 104
