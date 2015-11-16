#!/bin/sh
pylint --rcfile pylintrc -f parseable -r n mbed_utf > pylint.log || exit 0
