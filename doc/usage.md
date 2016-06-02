# Usage documentation

## Table of Contents
* [Python API](#python-api)
    * [Flash API](#flash-api)
        * [Flash Setup](#flash-setup)
        * [Querying available flashers](#querying-available-flashers)
        * [Querying supported targets](#querying-supported-targets)
        * [Querying attached devices](#querying-attached-devices)
        * [Flashing a single device](#flashing-a-single-device)
        * [Flashing devices with prefix](#flashing-devices-with-prefix)
        * [Flashing all devices by platform](#flashing-all-devices-by-platform)
        * [Flashing a device using pyOCD](#flashing-a-device-using-pyocd)
    * [Erase API](#erase-api)
        * [Erase Setup](#erase-setup)
        * [Querying attached devices](#querying-attached-devices-1)
        * [Erase a single device](#erase-a-single-device)
        * [Erase a single device using pyocd](#erase-a-single-device-using-pyocd)
        * [Erase devices with prefix](#erase-devices-with-prefix)
        * [Erase all devices using pyocd](#erase-all-devices-using-pyocd)
    * [Reset API](#reset-api)
        * [Reset Setup](#reset-setup)
        * [Querying attached devices](#querying-attached-devices-2)
        * [Reset a single device](#reset-a-single-device)
        * [Reset a single device using pyocd](#reset-a-single-device-using-pyocd)
        * [Reset devices with prefix](#reset-devices-with-prefix)
        * [Reset all devices using pyocd](#reset-all-devices-using-pyocd)
        
* [Command Line Interface](#command-line-interface)
    * [Listing commands](#listing commands)
        * [Running mbedflash without input](#running-mbedflash-without-input)
        * [Running mbedflash to list supported devices](#running-mbedflash-to-list-supported-devices)
        * [Running mbedflash to list supported flashers](#running-mbedflash-to-list-supported-flashers)
    * [Flash](#flash)
        * [Flashing a single device](#flashing-a-single-device-1)
        * [Flashing with prefix](#flashing-with-prefix)
        * [Flashing all devices by platform](#flashing-all-devices-by-platform-1)
        * [Flashing a single device with verbose output](#flashing-a-single-device-with-verbose-output)
        * [Flashing a device using pyOCD](#flashing-a-device-using-pyocd-1)
        * [Flashing multiple devices using pyocd](#flashing-multiple-devices-using-pyocd)
    * [Erase](#erase)
        * [Erasing a single device](#erasing-a-single-device)
        * [Erasing a single device using pyocd](#erasing-a-single-device-using-pyocd)
        * [Erasing a single device using pyocd verbose output](#erasing-a-single-device-using-pyocd-verbose-output)
        * [Erasing with prefix using pyocd](#erasing-with-prefix-using-pyocd)
        * [Erasing all devices using pyocd](#erasing-all-devices-using-pyocd)
    * [Reset](#reset)
        * [Resetting a single device](#resetting-a-single-device)
        * [Resetting a single device verbose output](#Resetting-a-single-device-verbose-output)
        * [Resetting a single device using pyocd](#resetting-a-single-device-using-pyocd)
        * [Resetting with prefix verbose output](#resetting-with-prefix-verbose-output)
        * [Resetting all devices verbose output](#resetting-all-devices-verbose-output)
    
## Python API

### Flash API

Typically we would use mbed-flasher as follows:

1. Find out what devices are available
2. Select the devices we would like to flash
3. Flash the selected devices

#### Flash Setup

Start by importing the mbed-flasher module:
```python
>>> from mbed_flasher.flash import Flash
>>> flasher = Flash()
```

#### Querying available flashers

```python
>>> flasher.FLASHERS
[<class 'mbed_flasher.flashers.FlasherMbed.FlasherMbed'>, <class 'mbed_flasher.flashers.FlasherAtmelAt.FlasherAtmelAt'>]
```

#### Querying supported targets

```python
>>> flasher.SUPPORTED_TARGETS
{
u'NRF51822': {u'properties': {u'binary_type': u'-combined.hex', u'copy_method': u'cp', u'program_cycle_s': 4, u'reset_method': u'default'}}, 
u'K64F': {u'properties': {u'binary_type': u'.bin', u'copy_method': u'default', u'program_cycle_s': 4, u'reset_method': u'default'}, u'yotta_targets': [{u'mbed_toolchain': u'GCC_ARM', u'yotta_target': u'frdm-k64f-gcc'}, {u'mbed_toolchain': u'ARM', u'yotta_target': u'frdm-k64f-armcc'}]}, 
'SAM4E': {'properties': {'binary_type': '.bin', 'copy_method': 'atprogram', 'program_cycle_s': 0, 'reset_method': 'default'}, 'yotta_targets': []}, 
u'NRF51_DK': {u'properties': {u'binary_type': u'-combined.hex', u'copy_method': u'shell', u'program_cycle_s': 4, u'reset_method': u'default'}, u'yotta_targets': [{u'mbed_toolchain': u'GCC_ARM', u'yotta_target': u'nrf51dk-gcc'}]}, 
u'NUCLEO_F401RE': {u'properties': {u'binary_type': u'.bin', u'copy_method': u'cp', u'program_cycle_s': 4, u'reset_method': u'default'}, u'yotta_targets': [{u'mbed_toolchain': u'GCC_ARM', u'yotta_target': u'st-nucleo-f401re-gcc'}]}
}
```

#### Querying attached devices:

```python
>>> for item in flasher.FLASHERS:
...     print item.get_available_devices()
...
[{'target_id_mbed_htm': '0240000028884e450019700f6bf0000f8021000097969900', 'mount_point': 'X:', 'target_id': '0240000028884e450019700f6bf0000f8021000097969900', 'serial_port': u'COM36', 'target_id_usb_id': '0240000028884e450019700f6bf0000f8021000097969900', 'platform_name': 'K64F'}]
[{'platform_name': 'SAM4E', 'baud_rate': 460800, 'mount_point': None, 'target_id': 'ATML2081030200003217', 'serial_port': None}]
```

#### Flashing a single device

```python
>>> flasher.flash(build="C:\\path_to_file\\myfile.bin", target_id="0240000028884e450019700f6bf0000f8021000097969900", platform_name="K64F")
0
```

#### Flashing devices with prefix

```python
>>> flasher.flash(build="C:\\path_to_file\\myfile.bin", target_id="02400000288", platform_name="K64F")
Going to flash following devices:
0240000028884e450019700f6bf0000f8021000097969900
0240000028884e450031700f6bf000118021000097969900
0
```

#### Flashing all devices by platform

```python
>>> flasher.flash(build="C:\\path_to_file\\myfile.bin", target_id="all", platform_name="K64F")
Going to flash following devices:
0240000028884e450019700f6bf0000f8021000097969900
0240000028884e450031700f6bf000118021000097969900
0
```

#### Flashing a device using pyOCD

Warning, not working reliably.

```python
>>> flasher.flash(build="C:\\path_to_file\\myfile.bin", target_id="0240000028884e450019700f6bf0000f8021000097969900", platform_name="K64F", method='pyocd')
DEBUG:mbed-flasher:atprogram location: C:\Program Files (x86)\Atmel\Studio\7.0\atbackend\atprogram.exe
DEBUG:mbed-flasher:Connected atprogrammer supported devices: []
DEBUG:mbed-flasher:[{'target_id_mbed_htm': '0240000028884e450019700f6bf0000f8021000097969900', 'mount_point': 'X:', 'target_id': '0240000028884e450019700f6bf0000f8021000097969900', 'serial_port': u'COM36', 'target_id_usb_id': '0240000028884e450019700f6bf0000f8021000097969900', 'platform_name': 'K64F'}]
DEBUG:mbed-flasher:Flashing: 0240000028884e450019700f6bf0000f8021000097969900
DEBUG:mbed-flasher:pyOCD selected for flashing
DEBUG:mbed-flasher:resetting device: 0240000028884e450019700f6bf0000f8021000097969900
DEBUG:mbed-flasher:flashing device: 0240000028884e450019700f6bf0000f8021000097969900
DEBUG:mbed-flasher:resetting device: 0240000028884e450019700f6bf0000f8021000097969900
INFO:mbed-flasher:flash ready
0
```

### Erase API

Typical use case:

1. Find out what devices are available
2. Select the devices we would like to erase
3. Erase the selected devices

Erasing a device is supported using pyocd or simple erasing. Simple erasing uses DAPLINK erasing and requires the device to be in automation mode and is experimental.

#### Erase Setup

Start by importing the mbed-flasher module:
```python
>>> from mbed_flasher.erase import Erase
>>> eraser = Erase()
```

#### Querying attached devices

```python
>>> eraser.get_available_device_mapping()
[{'target_id_mbed_htm': '0240000033514e45000b500585d40029e981000097969900', 'mount_point': 'D:', 'target_id': '0240000033514e45000b500585d40029e981000097969900', 'serial_port': u'COM78', 'target_id_usb_id': '0240000033514e45000b500585d40029e981000097969900', 'platform_name': 'K64F'}]
>>>
```

#### Erase a single device

```python
>>> eraser.erase(target_id='0240000033514e45000b500585d40029e981000097969900', method='simple')
Selected device does not support erasing through DAPLINK
0
```

Automation mode enabled:

```python
>>> eraser.erase(target_id='0240000033514e45000b500585d40029e981000097969900', method='simple')
WARNING:mbed-flasher:Experimental feature, might not do anything!
0
```

#### Erase a single device using pyocd

```python
>>> eraser.erase(target_id='0240000033514e45000b500585d40029e981000097969900', method='pyocd')
0
>>>
```

#### Erase devices with prefix

```python
>>> eraser.erase(target_id='024000003', method='simple')
WARNING:mbed-flasher:Experimental feature, might not do anything!
0
>>>
```

#### Erase all devices using pyocd

Warning, not working reliably.

```python
>>> eraser.erase(target_id='all', method='pyocd')
0
>>>
```

### Reset API

Typical use case:

1. Find out what devices are available
2. Select the devices we would like to reset
3. Reset the selected devices

Resetting a device is supported using pyocd or simple reset. simple reset uses serial reset.

#### Reset Setup

Start by importing the mbed-flasher module:

```python
>>> from mbed_flasher.reset import Reset
>>> resetter = Reset()
```

#### Querying attached devices

```python
>>> resetter.get_available_device_mapping()
[{'target_id_mbed_htm': '0240000028884e450051700f6bf000128021000097969900', 'mount_point': 'K:', 'target_id': '0240000028884e450051700f6bf000128021000097969900', 'serial_port': u'COM49', 'target_id_us
b_id': '0240000028884e450051700f6bf000128021000097969900', 'platform_name': 'K64F'}, {'target_id_mbed_htm': '0240000033514e45000b500585d40029e981000097969900', 'mount_point': 'D:', 'target_id': '02400
00033514e45000b500585d40029e981000097969900', 'serial_port': u'COM78', 'target_id_usb_id': '0240000033514e45000b500585d40029e981000097969900', 'platform_name': 'K64F'}]
>>>
```

#### Reset a single device

```python
>>> resetter.reset(target_id='0240000028884e450051700f6bf000128021000097969900', method='simple')
0
>>>
```

#### Reset a single device using pyocd

```python
>>> resetter.reset(target_id='0240000028884e450051700f6bf000128021000097969900', method='pyocd')
0
>>>
```

#### Reset devices with prefix

```python
>>> resetter.reset(target_id='024000002', method='simple')
0
>>>
```

#### Reset all devices using pyocd

```python
>>> resetter.reset(target_id='all', method='pyocd')
0
>>>
```

## Command Line Interface

### Listing commands

#### Running mbedflash without input

```batch
usage: mbedflash [-h] [-v] [-s] <command> ...
mbedflash: error: too few arguments
```

#### Running mbedflash to list supported devices

```batch
C:\>mbedflash list
["NRF51822", "K64F", "SAM4E", "NRF51_DK", "NUCLEO_F401RE"]
```

#### Running mbedflash to list supported flashers

```batch
C:\>mbedflash flashers
["Mbed", "Atprogram"]
```

### Flash

#### Flashing a single device

```batch
C:\>mbedflash flash -i C:\path_to_file\myfile.bin --tid 0240000028884e450019700f6bf0000f8021000097969900 -t K64F

C:\>
```

#### Flashing with prefix

```batch
C:\>mbedflash flash -i C:\path_to_file\myfile.bin --tid 02400 -t K64F
Going to flash following devices:
0240000028884e450019700f6bf0000f8021000097969900
0240000033514e45003f500585d4000ae981000097969900

C:\>
```

#### Flashing all devices by platform

```batch
C:\>mbedflash flash -i C:\path_to_file\myfile.bin --tid all -t K64F
Going to flash following devices:
0240000028884e450019700f6bf0000f8021000097969900
0240000033514e45003f500585d4000ae981000097969900

C:\>
```

#### Flashing a single device with verbose output

```batch
C:\>mbedflash -vvv flash -i C:\path_to_file\myfile.bin --tid 0240000033514e45000b500585d40029e981000097969900 -t K64F
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, SAM4E, NRF51_DK, NUCLEO_F401RE
[DEBUG](mbed-flasher): [{'target_id_mbed_htm': '0240000033514e45000b500585d40029e981000097969900', 'mount_point': 'D:', 'target_id': '0240000033514e45000b500585d40029e981000097969900', 'serial_port':
u'COM78', 'target_id_usb_id': '0240000033514e45000b500585d40029e981000097969900', 'platform_name': 'K64F'}]
Going to flash following devices:
0240000033514e45000b500585d40029e981000097969900
[DEBUG](mbed-flasher): [{'target_id_mbed_htm': '0240000033514e45000b500585d40029e981000097969900', 'mount_point': 'D:', 'target_id': '0240000033514e45000b500585d40029e981000097969900', 'serial_port':
u'COM78', 'target_id_usb_id': '0240000033514e45000b500585d40029e981000097969900', 'platform_name': 'K64F'}]
[DEBUG](mbed-flasher): Flashing: 0240000033514e45000b500585d40029e981000097969900
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed
[DEBUG](mbed-flasher): SHA1: dcbaa46d6500194a8a6d55c07bfa0ee0524c379c
[DEBUG](mbed-flasher): copying file: c:\path_to_file\myfile.bin to D:\image.bin
[DEBUG](mbed-flasher): copy finished
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed
[DEBUG](mbed-flasher): verifying flash
[DEBUG](mbed-flasher): ready
[INFO](mbed-flasher): flash ready
[DEBUG](mbed-flasher): dev#1 -> SUCCESS

C:\>
```

#### Flashing a device using pyOCD

```batch
C:\>mbedflash flash -i C:\path_to_file\myfile.bin --tid 0240000033514e45000b500585d40029e981000097969900 -t K64F pyocd
Going to flash following devices:
0240000033514e45000b500585d40029e981000097969900
DEBUG:mbed-flasher:resetting device: 0240000033514e45000b500585d40029e981000097969900
DEBUG:mbed-flasher:flashing device: 0240000033514e45000b500585d40029e981000097969900
DEBUG:mbed-flasher:resetting device: 0240000033514e45000b500585d40029e981000097969900
INFO:mbed-flasher:flash ready
DEBUG:mbed-flasher:dev#1 -> SUCCESS

C:\>
```

#### Flashing multiple devices using pyocd

```batch
C:\>mbedflash flash -i C:\path_to_file\myfile.bin --tid all -t K64F pyocd
Going to flash following devices:
0240000028884e450019700f6bf0000f8021000097969900
0240000033514e45003f500585d4000ae981000097969900
DEBUG:mbed-flasher:resetting device: 0240000028884e450019700f6bf0000f8021000097969900
DEBUG:mbed-flasher:flashing device: 0240000028884e450019700f6bf0000f8021000097969900
DEBUG:mbed-flasher:resetting device: 0240000028884e450019700f6bf0000f8021000097969900
INFO:mbed-flasher:flash ready
DEBUG:mbed-flasher:[{'target_id_mbed_htm': '0240000028884e450019700f6bf0000f8021000097969900', 'mount_point': 'X:', 'target_id': '0240000028884e450019700f6bf0000f8021000097969900', 'serial_port': u'COM36', 'target_id_usb_id': '0240000028884e450019700f6bf0000f8021000097969900', 'platform_name': 'K64F', u'yotta_targets': [{u'mbed_toolchain': u'GCC_ARM', u'yotta_target': u'frdm-k64f-gcc'}, {u'mbed_toolchain': u'ARM', u'yotta_target': u'frdm-k64f-armcc'}], u'properties': {u'binary_type': u'.bin', u'copy_method': u'default', u'program_cycle_s': 4, u'reset_method': u'default'}}, {'target_id_mbed_htm': '0240000033514e45003f500585d4000ae981000097969900', 'mount_point': 'D:', 'target_id': '0240000033514e45003f500585d4000ae981000097969900', 'serial_port': u'COM79', 'target_id_usb_id': '0240000033514e45003f500585d4000ae981000097969900', 'platform_name': 'K64F'}]
DEBUG:mbed-flasher:Flashing: 0240000033514e45003f500585d4000ae981000097969900
DEBUG:mbed-flasher:pyOCD selected for flashing
DEBUG:mbed-flasher:resetting device: 0240000033514e45003f500585d4000ae981000097969900
DEBUG:mbed-flasher:flashing device: 0240000033514e45003f500585d4000ae981000097969900
DEBUG:mbed-flasher:resetting device: 0240000033514e45003f500585d4000ae981000097969900
INFO:mbed-flasher:flash ready
DEBUG:mbed-flasher:dev#1 -> SUCCESS
DEBUG:mbed-flasher:dev#2 -> SUCCESS

C:\>
```

### Erase

#### Erasing a single device

This functionality experimental, automation mode has to be activated for DAPLINK for it to work

```batch
C:\>mbedflash -vvv erase --tid 0240000033514e45000b500585d40029e981000097969900
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, SAM4E, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting erase for given target_id ['0240000033514e45000b500585d40029e981000097969900']
[INFO](mbed-flasher): method used for reset: simple
[WARNING](mbed-flasher): Experimental feature, might not do anything!
[INFO](mbed-flasher): erasing device
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed
[INFO](mbed-flasher): erase completed

C:\>
```

or

```batch
c:\>mbedflash erase --tid 0240000033514e45000b500585d40029e981000097969900
Attached device does not support erasing through DAPLINK

c:\>
```

#### Erasing a single device using pyocd

```batch
C:\>mbedflash erase --tid 0240000028884e450051700f6bf000128021000097969900 pyocd
WARNING:root:K64F in secure state: will try to unlock via mass erase
WARNING:root:K64F secure state: unlocked successfully
INFO:mbed-flasher:erasing device
INFO:mbed-flasher:erase completed

C:\>
```

#### Erasing a single device using pyocd verbose output

```batch
C:\>mbedflash -vvv erase --tid 0240000028884e450051700f6bf000128021000097969900 pyocd
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, SAM4E, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting erase for given target_id ['0240000028884e450051700f6bf000128021000097969900']
[INFO](mbed-flasher): method used for reset: pyocd
[INFO](mbed-flasher): erasing device
INFO:mbed-flasher:erasing device
[INFO](mbed-flasher): erase completed
INFO:mbed-flasher:erase completed

C:\>
```

#### Erasing with prefix using pyocd

```batch
C:\>mbedflash erase --tid 024000002 pyocd
WARNING:root:K64F in secure state: will try to unlock via mass erase
WARNING:root:K64F secure state: unlocked successfully
INFO:mbed-flasher:erasing device
INFO:mbed-flasher:erase completed

C:\>
```

#### Erasing all devices using pyocd

```batch
C:\>mbedflash erase --tid all pyocd
WARNING:root:K64F in secure state: will try to unlock via mass erase
WARNING:root:K64F secure state: unlocked successfully
INFO:mbed-flasher:erasing device
INFO:mbed-flasher:erase completed
WARNING:root:K64F in secure state: will try to unlock via mass erase
WARNING:root:K64F secure state: unlocked successfully
INFO:mbed-flasher:erasing device
INFO:mbed-flasher:erase completed

C:\>
```

### Reset

#### Resetting a single device

```batch
C:\>mbedflash reset --tid 0240000028884e450051700f6bf000128021000097969900

C:\>
````

#### Resetting a single device verbose output

```batch
c:\>mbedflash -vvv reset --tid 0240000028884e450051700f6bf000128021000097969900
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, SAM4E, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting reset for target_id ['0240000028884e450051700f6bf000128021000097969900']
[INFO](mbed-flasher): Method for reset: simple
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed

C:\>
```

#### Resetting a single device using pyocd

```batch
C:\>mbedflash reset --tid 0240000028884e450051700f6bf000128021000097969900 pyocd
INFO:mbed-flasher:resetting device
INFO:mbed-flasher:reset completed

C:\>
```

#### Resetting with prefix verbose output

```batch
C:\>mbedflash -vvv reset --tid 024000002
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, SAM4E, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting reset for target_id ['0240000028884e450051700f6bf000128021000097969900']
[INFO](mbed-flasher): Method for reset: simple
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed

C:\>
```

#### Resetting all devices verbose output

```batch
C:\>mbedflash -vvv reset --tid all
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, SAM4E, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting reset for target_id all
[INFO](mbed-flasher): Method for reset: simple
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed

C:\>
```

