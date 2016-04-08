# TC for testing basic flashing via daplink. Test for CI job for mbed flasher with two K64F
# Needs dumy binariny which doesn't answer for help command and then binary which 
# has echo string in the help

import os
import serial
import time
import platform
from mbed_flasher.flash import Flash
import mbed_lstools
import sys



# function for checking that mbedls sees mounted devices
def is_devices_mounted():

    mbeds = mbed_lstools.create()
    mbedls_output = mbeds.list_mbeds()
    devicelist = str(mbedls_output).strip('[{}]')
    devices = ["/dev/ttyACM0", "/dev/ttyACM1"]

    if all(serial_port_ in devicelist for serial_port_ in devices):
        print "PASS: Two devices mounted"
    else:
        print "ERROR: Two devices not found/mounted" 
        sys.exit()

# function for verifying the flashing. If first time fails, its tries verity one more
def verify_flashing():

    mode = None
    mode = os.popen('ls -lart /dev/serial/by-id/').read().splitlines()

    com = []

    for line in mode:
        if line.find('/') != -1:
                com.append('/dev/' + line.split('/')[-1])

    print com
    print 'Inspecting %d SERIAL devices' % len(com)
    count = 0
    for item in com:
        ser = serial.Serial(
            port=item,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        if ser.isOpen():
            time.sleep(0.2)
            ser.write('help\n\r')
            out = ''
            time.sleep(0.5)
            while ser.inWaiting() > 0:
                out += ser.read(1)
            if out.find('echo') != -1:
                print '%s PASS' % item
                count += 1
            else:
                print 'replying help command for %s, because first try failed' % item
                ser.close()
                time.sleep(0.5)
                ser = serial.Serial(
                    port=item,
                    baudrate=115200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS
                )
                time.sleep(0.2)
                if ser.isOpen():
                    ser.write('help\n\r')
                    out = ''
                    time.sleep(0.5)
                    out += ser.read(1)
                    if out.find('echo') != -1:
                        print '%s PASS' % item
                    else:
                        print '%s FAIL: no reply to help' % item 
                        print 'print from serial: ' + out
            ser.close()
    print '%d of %d devices verified' % (count, len(com))



# First check that there are two devices mounted for ACM0 and ACM1
is_devices_mounted()


# flash the devices with dummy bin
flasher = Flash()
flasher.flash(build='helloworld.bin', platform_name='K64F', target_id='ALL')
time.sleep(0.5)
is_devices_mounted()

# flash the devices with bin, which respons to "help" command
flasher.flash(build='testapp.bin', platform_name='K64F', target_id='ALL')
time.sleep(0.5)
is_devices_mounted() 
verify_flashing()



# do this flashing multiple times
i=0
while i < 10:
    flasher.flash(build='helloworld.bin', platform_name='K64F', target_id='ALL')
    time.sleep(0.5)
    is_devices_mounted()
    flasher.flash(build='testapp.bin', platform_name='K64F', target_id='ALL')
    time.sleep(0.5)
    is_devices_mounted()
    verify_flashing()
    i+=1

