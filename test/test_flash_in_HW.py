# TC for testing basic flashing via daplink. Test for CI job for mbed flasher with X K64F
# Needs dummy binariny which doesn't answer for help command and then a binary which
# has echo string in the help

import os
import serial
import time
import platform
from mbed_flasher.flash import Flash
import mbed_lstools


class VerifyFlashing():
    def __init__(self):
        pass

    #function to gather all mbed serial ports from system
    def gather_all_devices_from_system(self):
        if platform.system() == 'Windows':
            mode = os.popen('mode').read().splitlines()
        else:
            mode = os.popen('ls -lart /dev/serial/by-id/').read().splitlines()

        com = []
        for line in mode:
            if platform.system() == 'Windows':
                if line.find('COM') != -1:
                    com.append(line.split(' ')[3][:-1])
            else:
                if line.find('/') != -1:
                    com.append('/dev/' + line.split('/')[-1])
        return com
    # function to gather all devices with mbedls
    def gather_all_devices_from_mbedls(self):
        mbeds = mbed_lstools.create()
        mbedls_output = mbeds.list_mbeds()
        return mbedls_output

    # function for checking that mbedls sees mounted devices
    def are_devices_mounted(self, number_of_devices):

        mbeds = mbed_lstools.create()
        mbedls_output = mbeds.list_mbeds()
        if len(mbedls_output) == number_of_devices:
            return True
        else:
            return False

    # function to verify single serial port
    def verify_output_per_device(self, serial_port, command, output):
        print 'Inspecting %s SERIAL devices' % serial_port
        ser = serial.Serial(
            port=serial_port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        if ser.isOpen():
            time.sleep(0.2)
            ser.write('%s\n\r' % command)
            out = ''
            time.sleep(0.5)
            while ser.inWaiting() > 0:
                out += ser.read(1)
            if out.find(output) != -1:
                #print '%s PASS' % serial_port
                ser.close()
                return True
            else:
                ser.close()
                return False

def main():

    v = VerifyFlashing()
    devices_on_system = v.gather_all_devices_from_system()
    devices_from_mbedls = v.gather_all_devices_from_mbedls()
    if len(devices_on_system) == len(devices_from_mbedls):
        print "All devices attached to system are visible in mbedls"
    else:
        raise SystemError("All of the attached devices are not seen with mbedls")

    # First check that all devices are mounted
    v.are_devices_mounted(len(devices_on_system))

    result =[]
    # flash the devices with dummy bin
    flasher = Flash()
    status = flasher.flash(build='helloworld.bin', platform_name='K64F', target_id='ALL')
    if status == 0:
        time.sleep(0.5)
        if v.are_devices_mounted(len(devices_on_system)):
            for device in devices_from_mbedls:
                if v.verify_output_per_device(device['serial_port'], 'help', 'echo'):
                    raise SystemError("Flashing failed, got response with dummy binary")
                else:
                    print "Got no response, as expected"
        else:
            raise SystemError("Flashing failed, Device missing")
    else:
        raise SystemError("Dummy binary flashing failed")
    result.append('First Dummy binary flash:\tPASS')

    # flash the devices with bin, which responses to "help" command
    status = flasher.flash(build='testapp.bin', platform_name='K64F', target_id='ALL')
    if status == 0:
        time.sleep(0.5)
        if v.are_devices_mounted(len(devices_on_system)):
            for device in devices_from_mbedls:
                if v.verify_output_per_device(device['serial_port'], 'help', 'echo'):
                    print "Got response, as expected"
                else:
                    if v.verify_output_per_device(device['serial_port'], 'help', 'echo'):
                        print "Got response with second try"
                    else:
                        raise SystemError("Flashing failed, got no response with working binary")
    else:
        raise SystemError("Working binary flashing failed")
    result.append('Working binary flash:\t\tPASS')

    # flash the devices with dummy bin
    status = flasher.flash(build='helloworld.bin', platform_name='K64F', target_id='ALL')
    if status == 0:
        time.sleep(0.5)
        if v.are_devices_mounted(len(devices_on_system)):
            for device in devices_from_mbedls:
                if v.verify_output_per_device(device['serial_port'], 'help', 'echo'):
                    raise SystemError("Flashing failed, got response with dummy binary")
                else:
                    print "Got no response, as expected"
        else:
            raise SystemError("Flashing failed, Device missing")
    else:
        raise SystemError("Dummy binary flashing failed")
    result.append('Second Dummy binary flash:\tPASS')
    
    print "\nTested %d mbed boards" % len(devices_from_mbedls)
    for item in result:
        print item

if __name__ == "__main__":
    main()