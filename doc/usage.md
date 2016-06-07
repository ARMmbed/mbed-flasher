# Usage documentation

## Table of Contents
* [Python API](#python-api)
    * [Flash API](#flash-api)
        * [Flash setup](#flash-setup)
        * [Querying available flashers](#querying-available-flashers)
        * [Querying supported targets](#querying-supported-targets)
        * [Querying attached devices](#querying-attached-devices)
        * [Flashing a single device](#flashing-a-single-device)
        * [Flashing devices with prefix](#flashing-devices-with-a-prefix)
        * [Flashing all devices by platform](#flashing-all-devices-by-platform)
        * [Flashing a device using pyOCD](#flashing-a-device-using-pyocd)
    * [Erase API](#erase-api)
        * [Erase setup](#erase-setup)
        * [Querying attached devices](#querying-attached-devices-1)
        * [Erasing a single device](#erasing-a-single-device)
        * [Erasing a single device using pyOCD](#erasing-a-single-device-using-pyocd)
        * [Erasing devices with a prefix](#erasing-devices-with-a-prefix)
        * [Erasing all devices using pyOCD](#erasing-all-devices-using-pyocd)
    * [Reset API](#reset-api)
        * [Reset setup](#reset-setup)
        * [Querying attached devices](#querying-attached-devices-2)
        * [Resetting a single device](#resetting-a-single-device)
        * [Resetting a single device using pyOCD](#resetting-a-single-device-using-pyocd)
        * [Resetting devices with a prefix](#resetting-devices-with-a-prefix)
        * [Resetting all devices using pyOCD](#reset-all-devices-using-pyocd)
        
* [Command Line Interface](#command-line-interface)
    * [Listing commands](#listing commands)
        * [Running mbed-flasher without input](#running-mbed-flasher-without-input)
        * [Running mbed-flasher to list supported devices](#running-mbed-flasher-to-list-supported-devices)
        * [Running mbed-flasher to list supported flashers](#running-mbed-flasher-to-list-supported-flashers)
    * [Flashing](#flashing)
        * [Flashing a single device](#flashing-a-single-device)
        * [Flashing with a prefix](#flashing-with-a-prefix)
        * [Flashing all devices by platform](#flashing-all-devices-by-platform)
        * [Flashing a single device with verbose output](#flashing-a-single-device-with-verbose-output)
        * [Flashing a device using pyOCD](#flashing-a-device-using-pyocd)
        * [Flashing multiple devices using pyocd](#flashing-multiple-devices-using-pyocd)
    * [Erasing](#erasing)
        * [Erasing a single device](#erasing-a-single-device)
        * [Erasing a single device using pyocd](#erasing-a-single-device-using-pyocd)
        * [Erasing a single device using pyocd verbose output](#erasing-a-single-device-using-pyocd-verbose-output)
        * [Erasing with prefix using pyocd](#erasing-with-prefix-using-pyocd)
        * [Erasing all devices using pyocd](#erasing-all-devices-using-pyocd)
    * [Resetting](#resetting)
        * [Resetting a single device](#resetting-a-single-device)
        * [Resetting a single device verbose output](#Resetting-a-single-device-with-verbose-output)
        * [Resetting a single device using pyocd](#resetting-a-single-device-using-pyocd)
        * [Resetting with a prefix with verbose output](#resetting-with-a-prefix-with-verbose-output)
        * [Resetting all devices with verbose output](#resetting-all-devices-with-verbose-output)
    
## Python API

### Flash API

Typically, mbed-flasher is used for:

* Detecting available devices.
* Selecting the devices to flash.
* Flashing the selected devices.

#### Flash setup

To import the mbed-flasher module:

```python
>>> from mbed_flasher.flash import Flash
>>> flasher = Flash()
```

#### Querying available flashers

```python
>>> flasher.get_supported_flashers()
['Mbed']
```

#### Querying supported targets

```python
>>> flasher.get_supported_targets()
[u'NRF51822', u'K64F', u'NRF51_DK', u'NUCLEO_F401RE']
```

#### Querying attached devices

```python
>>> for item in flasher.FLASHERS:
...     print item.get_available_devices()
...
[{'target_id_mbed_htm': '0240000028884e450019700f6bf0000f8021000097969900', 'mount_point': 'X:', 'target_id': '0240000028884e450019700f6bf0000f8021000097969900', 'serial_port': u'COM36', 'target_id_usb_id': '0240000028884e450019700f6bf0000f8021000097969900', 'platform_name': 'K64F'}]
```

or get everything in one list:

```python
>>> flasher.get_available_device_mapping()
[{'target_id_mbed_htm': '0240000033514e45003f500585d4000ae981000097969900', 'mount_point': 'D:', 'target_id': '0240000033514e45003f500585d4000ae981000097969900', 'serial_port': u'COM79', 'target_id_us
b_id': '0240000033514e45003f500585d4000ae981000097969900', 'platform_name': 'K64F'}]
```

#### Flashing a single device

```python
>>> flasher.flash(build="C:\\path_to_file\\myfile.bin", target_id="0240000028884e450019700f6bf0000f8021000097969900", platform_name="K64F")
0
```

#### Flashing devices with a prefix

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

<span class="warnings">**Warning:** Currently, not working reliably.</span>

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

Typical use cases:

* Detecting available devices.
* Selecting the devices to erase.
* Erasing the selected devices.

To erase a device you can use pyOCD or simple erasing. Simple erasing is still experimental. It uses DAPLINK erasing and requires the device to be in automation mode.

#### Erase setup

To import the mbed-flasher module:

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

#### Erasing a single device

```python
>>> eraser.erase(target_id='0240000033514e45000b500585d40029e981000097969900', method='simple')
Selected device does not support erasing through DAPLINK
0
```

**Automation mode enabled:**

```python
>>> eraser.erase(target_id='0240000033514e45000b500585d40029e981000097969900', method='simple')
WARNING:mbed-flasher:Experimental feature, might not do anything!
0
```

#### Erasing a single device using pyOCD

```python
>>> eraser.erase(target_id='0240000033514e45000b500585d40029e981000097969900', method='pyocd')
0
>>>
```

#### Erasing devices with a prefix

```python
>>> eraser.erase(target_id='024000003', method='simple')
WARNING:mbed-flasher:Experimental feature, might not do anything!
0
>>>
```

#### Erasing all devices using pyOCD

<span class="warnings">**Warning:** Currently, not working reliably.</span>

```python
>>> eraser.erase(target_id='all', method='pyocd')
0
>>>
```

### Reset API

Typical use cases:

* Detecting available devices.
* Selecting the devices to reset.
* Resetting the selected devices.

To reset a device you can use pyOCD or simple reset. The simple reset uses serial reset.

#### Reset setup

To import the mbed-flasher module:

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

#### Resetting a single device

```python
>>> resetter.reset(target_id='0240000028884e450051700f6bf000128021000097969900', method='simple')
0
>>>
```

#### Resetting a single device using pyOCD

```python
>>> resetter.reset(target_id='0240000028884e450051700f6bf000128021000097969900', method='pyocd')
0
>>>
```

#### Resetting devices with a prefix

```python
>>> resetter.reset(target_id='024000002', method='simple')
0
>>>
```

#### Resetting all devices using pyOCD

```python
>>> resetter.reset(target_id='all', method='pyocd')
0
>>>
```

## Command Line Interface

### Listing commands

#### Running mbed-flasher without input

```batch
usage: mbedflash [-h] [-v] [-s] <command> ...
mbedflash: error: too few arguments
```

#### Running mbed-flasher to list supported devices

```batch
C:\>mbedflash list
["NRF51822", "K64F", "NRF51_DK", "NUCLEO_F401RE"]
```

#### Running mbed-flasher to list supported flashers

```batch
C:\>mbedflash flashers
["Mbed"]
```

### Flashing

#### Flashing a single device

```batch
C:\>mbedflash flash -i C:\path_to_file\myfile.bin --tid 0240000028884e450019700f6bf0000f8021000097969900 -t K64F

C:\>
```

#### Flashing with a prefix

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
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, NRF51_DK, NUCLEO_F401RE
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

#### Flashing multiple devices using pyOCD

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

### Erasing

#### Erasing a single device

<span class="notes">**Note:** This functionality experimental. You need to activate the automation mode to make the DAPLINK work.</span>

```batch
C:\>mbedflash -vvv erase --tid 0240000033514e45000b500585d40029e981000097969900
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting erase for given target_id ['0240000033514e45000b500585d40029e981000097969900']
[INFO](mbed-flasher): method used for reset: simple
[WARNING](mbed-flasher): Experimental feature, might not do anything!
[INFO](mbed-flasher): erasing device
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed
[INFO](mbed-flasher): erase completed

C:\>
```

Alternatively:

```batch
c:\>mbedflash erase --tid 0240000033514e45000b500585d40029e981000097969900
Attached device does not support erasing through DAPLINK

c:\>
```

#### Erasing a single device using pyOCD

```batch
C:\>mbedflash erase --tid 0240000028884e450051700f6bf000128021000097969900 pyocd
WARNING:root:K64F in secure state: will try to unlock via mass erase
WARNING:root:K64F secure state: unlocked successfully
INFO:mbed-flasher:erasing device
INFO:mbed-flasher:erase completed

C:\>
```

#### Erasing a single device using pyOCD with verbose output

```batch
C:\>mbedflash -vvv erase --tid 0240000028884e450051700f6bf000128021000097969900 pyocd
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting erase for given target_id ['0240000028884e450051700f6bf000128021000097969900']
[INFO](mbed-flasher): method used for reset: pyocd
[INFO](mbed-flasher): erasing device
INFO:mbed-flasher:erasing device
[INFO](mbed-flasher): erase completed
INFO:mbed-flasher:erase completed

C:\>
```

#### Erasing with a prefix using pyOCD

```batch
C:\>mbedflash erase --tid 024000002 pyocd
WARNING:root:K64F in secure state: will try to unlock via mass erase
WARNING:root:K64F secure state: unlocked successfully
INFO:mbed-flasher:erasing device
INFO:mbed-flasher:erase completed

C:\>
```

#### Erasing all devices using pyOCD

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

### Resetting

#### Resetting a single device

```batch
C:\>mbedflash reset --tid 0240000028884e450051700f6bf000128021000097969900

C:\>
````

#### Resetting a single device with verbose output

```batch
c:\>mbedflash -vvv reset --tid 0240000028884e450051700f6bf000128021000097969900
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting reset for target_id ['0240000028884e450051700f6bf000128021000097969900']
[INFO](mbed-flasher): Method for reset: simple
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed

C:\>
```

#### Resetting a single device using pyOCD

```batch
C:\>mbedflash reset --tid 0240000028884e450051700f6bf000128021000097969900 pyocd
INFO:mbed-flasher:resetting device
INFO:mbed-flasher:reset completed

C:\>
```

#### Resetting with a prefix with verbose output

```batch
C:\>mbedflash -vvv reset --tid 024000002
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting reset for target_id ['0240000028884e450051700f6bf000128021000097969900']
[INFO](mbed-flasher): Method for reset: simple
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed

C:\>
```

#### Resetting all devices with verbose output

```batch
C:\>mbedflash -vvv reset --tid all
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, NRF51_DK, NUCLEO_F401RE
[INFO](mbed-flasher): Starting reset for target_id all
[INFO](mbed-flasher): Method for reset: simple
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed

C:\>
```

