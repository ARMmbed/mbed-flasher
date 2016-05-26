# Usage documentation

## Table of Contents
* [Python API](#python-api)
    * [Basic usage](#basic-usage)
        * [Setup](#setup)
        * [Querying available flashers](#querying-available-flashers)
        * [Querying supported targets](#querying-supported-targets)
        * [Querying attached devices](#querying-attached-devices)
        * [Flashing a single device](#flashing-a-single-device)
        * [Flashing devices with prefix](#flashing-devices-with-prefix)
        * [Flashing all devices by platform](#flashing-all-devices-by-platform)
        * [Flashing a device using pyOCD](#flashing-a-device-using-pyocd)
        
* [Command Line Interface](#command-line-interface)
    * [Running mbedflash without input](#running-mbedflash-without-input)
    * [Running mbedflash to list supported devices](#running-mbedflash-to-list-supported-devices)
    * [Running mbedflash to list supported flashers](#running-mbedflash-to-list-supported-flashers)
    * [Flashing a single device](#flashing-a-single-device-1)
    * [Flashing with prefix](#flashing-with-prefix)
    * [Flashing all devices by platform](#flashing-all-devices-by-platform-1)
    * [Flashing a single device with verbose output](#flashing-a-single-device-with-verbose-output)
    * [Flashing a device using pyOCD](#flashing-a-device-using-pyocd-1)
    * [Flashing multiple devices using pyocd](#flashing-multiple-devices-using-pyocd)
    
## Python API

### Basic usage

Typically we would use mbed-flasher as follows:

1. Find out what devices are available
2. Select the devices we would like to flash
3. Flash the selected devices

#### Setup

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
>>> flasher.flash(build="C:\\path_to_file\\myfile.bin", target_id="0240000028884e450019700f6bf0000f8021000097969900", platform_name="K64F", pyocd=True)
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

## Command Line Interface

#### Running mbedflash without input

```batch
C:\>mbedflash
No input, nothing to do.
Try mbedflash --help
```

#### Running mbedflash to list supported devices

```batch
C:\>mbedflash -l
["NRF51822", "K64F", "SAM4E", "NRF51_DK", "NUCLEO_F401RE"]
```

#### Running mbedflash to list supported flashers

```batch
C:\>mbedflash --flashers
["Mbed", "Atprogram"]
```

#### Flashing a single device

```batch
C:\>mbedflash -i c:\path_to_file\myfile.bin --tid 0240000028884e450019700f6bf0000f8021000097969900 -t K64F

C:\Temp>
```

#### Flashing with prefix

```batch
C:\>mbedflash -i Temp\helloworld_k64f.bin --tid 02400 -t K64F
Going to flash following devices:
0240000028884e450019700f6bf0000f8021000097969900
0240000033514e45003f500585d4000ae981000097969900

C:\>
```

#### Flashing all devices by platform

```batch
C:\>mbedflash -i Temp\helloworld_k64f.bin --tid all -t K64F
Going to flash following devices:
0240000028884e450019700f6bf0000f8021000097969900
0240000033514e45003f500585d4000ae981000097969900

C:\>
```

#### Flashing a single device with verbose output

```batch
C:\>mbedflash -i C:\path_to_file\myfile.bin --tid 0240000028884e450019700f6bf0000f8021000097969900 -t K64F -vvv
[DEBUG](mbed-flasher): Supported targets: NRF51822, K64F, SAM4E, NRF51_DK, NUCLEO_F401RE
[DEBUG](mbed-flasher): atprogram location: C:\Program Files (x86)\Atmel\Studio\7.0\atbackend\atprogram.exe
[DEBUG](mbed-flasher): Connected atprogrammer supported devices: []
[DEBUG](mbed-flasher): [{'target_id_mbed_htm': '0240000028884e450019700f6bf0000f8021000097969900', 'mount_point': 'X:', 'target_id': '0240000028884e450019700f6bf0000f8021000097969900', 'serial_port': u'COM36', 'target_id_usb_id': '0240000028884e450019700f6bf0000f8021000097969900', 'platform_name': 'K64F'}]
[DEBUG](mbed-flasher): Flashing: 0240000028884e450019700f6bf0000f8021000097969900
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed
[DEBUG](mbed-flasher): SHA1: abababababababababababababababababababab
[DEBUG](mbed-flasher): copying file: path_to_file\myfile.bin to X:\image.bin
[DEBUG](mbed-flasher): copy finished
[INFO](mbed-flasher): sendBreak to device to reboot
[INFO](mbed-flasher): reset completed
[DEBUG](mbed-flasher): verifying flash
[DEBUG](mbed-flasher): ready
[INFO](mbed-flasher): flash ready

C:\>
```

#### Flashing a device using pyOCD

```batch
C:\>mbedflash -i C:\path_to_file\myfile.bin --tid 0240000033514e45003f500585d4000ae981000097969900 -t K64F --pyocd
DEBUG:mbed-flasher:resetting device: 0240000033514e45003f500585d4000ae981000097969900
DEBUG:mbed-flasher:flashing device: 0240000033514e45003f500585d4000ae981000097969900
DEBUG:mbed-flasher:resetting device: 0240000033514e45003f500585d4000ae981000097969900
INFO:mbed-flasher:flash ready

C:\>
```

#### Flashing multiple devices using pyocd

```batch
C:\>mbedflash -i C:\path_to_file\myfile.bin --tid all -t K64F --pyocd
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