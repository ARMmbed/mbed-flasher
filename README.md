# mbed-flasher
mbed-flasher is simple python tool to flash single or multiple mbed boards.
It provide simple Command Line Interface and python API for flashing.

## Installation

`python setup.py install`

## Usage with CLI

Flash single board by id:

`mbedflash -i myfile.bin --tid 123456`

Flash single board by platform_name:

`mbedflash -i myfile.bin -t K64F`

## Usage with python API

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
usage: mbedflash-script.py [-h] [-v] [-s] [--version] [-i INPUT]
                           [-m DEVICE_MAPPING_TABLE] [-l] [--flashers]
                           [--tid TARGET_ID] [-t PLATFORM_NAME]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbose level... repeat up to three times.
  -s, --silent          Silent - only errors will be printed
  --version             Prints package version and exits
  -i INPUT, --input INPUT
                        Binary input to be flash
  -m DEVICE_MAPPING_TABLE, --mapping DEVICE_MAPPING_TABLE
                        Device mapping table
  -l, --list            Prints list of supported platforms
  --flashers            Prints list of supported flashers
  --tid TARGET_ID, --target_id TARGET_ID
                        Target to be flash
  -t PLATFORM_NAME, --platform_name PLATFORM_NAME
                        Platform/Target name to be flashed

```

## Releasing

### Windows installer

