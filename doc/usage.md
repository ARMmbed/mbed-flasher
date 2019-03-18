# Usage documentation

## Table of Contents
* [Python API](#python-api)
    * [Flash API](#flash-api)
        * [Flash setup](#flash-setup)
        * [Flashing a single device](#flashing-a-single-device)
    * [Erase API](#erase-api)
        * [Erase setup](#erase-setup)
        * [Erasing a single device](#erasing-a-single-device)
    * [Reset API](#reset-api)
        * [Reset setup](#reset-setup)
        * [Resetting a single device](#resetting-a-single-device)

* [Command Line Interface](#command-line-interface)
    * [Running mbed-flasher without input](#running-mbed-flasher-without-input)
    * [Flashing](#flashing)
        * [Flashing a single device](#flashing-a-single-device-1)
    * [Erasing](#erasing)
        * [Erasing a single device](#erasing-a-single-device-1)
    * [Resetting](#resetting)
        * [Resetting a single device](#resetting-a-single-device-1)
* [Exit codes](#exit-codes)

## Python API

### Flash API

#### Flash retry

Mbed-flasher has a mechanism that will retry flashing on specific failure cases where retrying
could be beneficial. The mechanism is only used by the FlasherMbed drag'n'drop flash. Other
flashers do not have retry mechanism in mbed-flasher.

Flash is tried at most five times with an exponential interval (1, 4, 9, 16 seconds) in between
rounds.

Flash is retried on these failure reasons:
* Any python OSError or IOError
* Any of the following errors reported by daplink through FAIL.TXT:
  * An internal error has occurred
  * End of stream has been reached
  * End of stream is unknown
  * An error occurred during the transfer
  * Possible mismatch between file size and size programmed
  * File sent out of order by PC. Target might not be programmed correctly.
  * An error has occurred

#### Flash setup

To import the mbed-flasher module:

```python
>>> from mbed_flasher.flash import Flash
>>> flasher = Flash()
```

#### Flashing a single device

```python
>>> flasher.flash(build="C:\\path_to_file\\myfile.bin", target_id="0240000028884e450019700f6bf0000f8021000097969900")
0
```

### Erase API

To erase a device you can use simple erasing. Simple erasing is still experimental. It uses [DAPLINK](https://github.com/mbedmicro/DAPLink/blob/master/docs/ENABLE_AUTOMATION.md) erasing and requires the device to be in automation mode.

#### Erase setup

To import the mbed-flasher module:

```python
>>> from mbed_flasher.erase import Erase
>>> eraser = Erase()
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

### Reset API

The reset uses serial reset.

#### Reset setup

To import the mbed-flasher module:

```python
>>> from mbed_flasher.reset import Reset
>>> resetter = Reset()
```

#### Resetting a single device

```python
>>> resetter.reset(target_id='0240000028884e450051700f6bf000128021000097969900', method='simple')
0
>>>
```

## Command Line Interface

#### Running mbed-flasher without input

```batch
usage: mbedflash [-h] [-v] [-s] <command> ...
mbedflash: error: too few arguments
```

### Flashing

#### Flashing a single device

```batch
C:\>mbedflash flash -i C:\path_to_file\myfile.bin --tid 0240000028884e450019700f6bf0000f8021000097969900

C:\>
```

#### Flashing a single device with verbose output

```batch
C:\>mbedflash -vvv flash -i C:\path_to_file\myfile.bin --tid 0240000033514e45000b500585d40029e981000097969900
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

### Erasing

#### Erasing a single device

<span class="notes">**Note:** This functionality experimental. You need to activate the automation mode to make the [DAPLINK](https://github.com/mbedmicro/DAPLink/blob/master/docs/ENABLE_AUTOMATION.md) work.</span>

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

### Resetting

#### Resetting a single device

```batch
C:\>mbedflash reset --tid 0240000028884e450051700f6bf000128021000097969900

C:\>
````

## Exit codes

`0` exit code means success and other failures.

See all exit codes from [here](exit_codes.md)