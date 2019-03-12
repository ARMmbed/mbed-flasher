# mbed-flasher

## Description

mbed-flasher is a simple Python-based tool for flashing boards.
It provides a simple Command Line Interface and Python API for flashing.

The purpose is to provide a clean and simple library that is easy to integrate to other tools.
It can be easily developed further to support flashing in mbed OS and other platforms.
Developers can also use it as a standalone tool for flashing their development boards.


## Installation

To install the flasher, use:

`python setup.py install`

To install the flasher in development mode:

`python setup.py develop`

## Usage

This tool has been tested and verified to work with Windows 10 and Ubuntu (16.04 LTS) Linux.

Devices used in verification: NXP K64F.

See the actual usage documentation [here](doc/usage.md).

## Help

**Main help**

```
/> mbedflash --help
usage: mbedflash [-h] [-v] [-s] <command> ...

For specific command help, run: mbedflash <command> --help

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Verbose level... repeat up to three times.
  -s, --silent   Silent - only errors will be printed.

command:
  <command>      command help
    version      Display version information
    flash        Flash given resource
    reset        Reset given resource
    erase        Erase given resource

```

**Flash help**

```
/>mbedflash flash --help
usage: mbedflash flash [-h] [-i INPUT] [--tid TARGET_ID] [--no-reset] [method]

positional arguments:
  method                <simple>, used for flashing

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Binary input to be flashed.
  --tid TARGET_ID, --target_id TARGET_ID
                        Target to be flashed.
  --no-reset            Do not reset device before or after flashing

```

**Erase help**

```
c:\>mbedflash erase --help
usage: mbedflash erase [-h] [--tid TARGET_ID] [--no-reset] [method]

positional arguments:
  method                <simple>, used for erase

optional arguments:
  -h, --help            show this help message and exit
  --tid TARGET_ID, --target_id TARGET_ID
                        Target to be erased.
  --no-reset            Do not reset device after erase
```

**Reset help**

```
c:\>mbedflash reset --help
usage: mbedflash reset [-h] [--tid TARGET_ID] [method]

positional arguments:
  method                <simple>, used for reset

optional arguments:
  -h, --help            show this help message and exit
  --tid TARGET_ID, --target_id TARGET_ID
                        Target to be reset.
```

## Running unit tests

Required pre-installed packages: coverage, mock

```
sudo pip install coverage mock
```

Execute all tests:
```
coverage run -m unittest discover -s test
```
Execute hardware tests:
```
coverage run -m unittest discover -s test.hardware
```
Execute non-hardware tests:
```
coverage run -m unittest discover -s test.non_hardware
```



Generate a coverage report:

```
coverage html
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
