# mbed-flasher 

## Description

mbed-flasher is a simple Python-based tool for flashing single or multiple boards.
It provides a simple Command Line Interface and Python API for flashing. 

The purpose is to provide a clean and simple library that is easy to integrate to other tools
and that can be easily developed further to support flashing in mbed OS and other platforms.
Developers can also use it as a standalone tool for flashing their development boards.


## Installation

To install the flasher, use:

`python setup.py install`

To install the flasher in development mode:

`python setup.py develop`

## Usage with CLI

This tool has been tested to work with Windows 7 and Ubuntu(14.04 LTS) Linux.

To flash a single board by ID:

`mbedflash -i myfile.bin --tid 123456`

To flash a single board by platform_name:

`mbedflash -i myfile.bin -t K64F`

To flash all connected boards by platform_name:

`mbedflash -i myfile.bin -t K64F --tid ALL`

## Usage with Python API

```python
from mbed_flasher import Flash
flasher = Flash()

# flash single board by id
flasher.flash( source='myfile.bin', target_id='123456')

# flash single board by platform_name
flasher.flash( source='myfile.bin', platform_name='K64F')
```

## Help
```
/> mbedflash --help
usage: mbedflash [-h] [-v] [-s] [--version] [-i INPUT]
                 [-m DEVICE_MAPPING_TABLE] [-l] [--flashers]
                 [--tid TARGET_ID] [-t PLATFORM_NAME]

optional arguments:
  -h, --help            Show this help message and exit.
  -v, --verbose         Verbose level... repeat up to three times.
  -s, --silent          Silent - only errors will be printed.
  --version             Prints the package version and exits.
  -i INPUT, --input INPUT
                        Binary input to be flashed.
  -m DEVICE_MAPPING_TABLE, --mapping DEVICE_MAPPING_TABLE
                        Device mapping table.
  -l, --list            Prints a list of supported platforms.
  --flashers            Prints s list of supported flashers.
  --tid TARGET_ID, --target_id TARGET_ID
                        Target to be flashed.
  -t PLATFORM_NAME, --platform_name PLATFORM_NAME
                        Platform/target name to be flashed.

```

## Creating the installer

**For Windows:**
```
python setup.py build
python setup.py bdist_msi
```

**For Linux:**
```
python setup.py build
//for rpm package
python setup.py bdist_rpm
```
Read [more on installers](https://docs.python.org/2/distutils/builtdist.html).
