#!/usr/bin/env bash
pylint --rcfile=.pylintrc --output-format=parseable ./setup.py ./mbed_flasher ./test
