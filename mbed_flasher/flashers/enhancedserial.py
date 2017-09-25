#!/usr/bin/env python
"""Enhanced Serial Port class
part of pyserial (http://pyserial.sf.net)  (C)2002 cliechti@gmx.net

another implementation of the readline and readlines method.
this one should be more efficient because a bunch of characters are read
on each access, but the drawback is that a timeout must be specified to
make it work (enforced by the class __init__).

this class could be enhanced with a read_until() method and more
like found in the telnetlib.
"""
import re
from time import sleep
import pkg_resources
from serial import Serial, SerialException, SerialTimeoutException


class EnhancedSerial(Serial): # pylint: disable=too-many-ancestors, too-many-instance-attributes
    '''
    EnhancedSerial module
    '''
    def __init__(self, *args, **kwargs):
        # ensure that a reasonable timeout is set
        timeout = kwargs.get('timeout', 0.1)
        if timeout < 0.01:
            timeout = 0.1
        kwargs['timeout'] = timeout
        Serial.__init__(self, *args, **kwargs)
        self.buf = ''
        self.pyserial_version = self.get_pyserial_version()
        self.is_pyserial_v3 = self.pyserial_version >= 3.0

    def get_pyserial_version(self):
        """! Retrieve pyserial module version
        @return Returns float with pyserial module number
        """
        # pylint: disable = anomalous-backslash-in-string
        self.re_float = re.compile("^\d+\.\d+")
        pyserial_version = pkg_resources.require("pyserial")[0].version
        version = 3.0
        match = self.re_float.search(pyserial_version)
        if match:
            try:
                version = float(match.group(0))
            except ValueError:
                version = 3.0   # We will assume you've got latest (3.0+)
        return version

    def safe_send_break(self):
        """! Closure for pyserial version dependant API calls
        """
        if self.is_pyserial_v3:
            return self._safe_send_break_v3_0()
        return self._safe_send_break_v2_7()

    # pylint: disable=bare-except
    def _safe_send_break_v2_7(self):
        """! pyserial 2.7 API implementation of sendBreak/setBreak
        @details
        Below API is deprecated for pyserial 3.x versions!
        http://pyserial.readthedocs.org/en/latest/pyserial_api.html#serial.Serial.sendBreak
        http://pyserial.readthedocs.org/en/latest/pyserial_api.html#serial.Serial.setBreak
        """
        result = True
        try:
            self.sendBreak()
        except:
            # In Linux a termios.error is raised in sendBreak and in setBreak.
            # The following setBreak() is needed to release the reset signal on the
            # target mcu.
            try:
                sleep(1)
                self.setBreak(False)
                sleep(1)
            except:
                result = False
        return result

    def _safe_send_break_v3_0(self):
        """! pyserial 3.x API implementation of send_brea / break_condition
        @details
        http://pyserial.readthedocs.org/en/latest/pyserial_api.html#serial.Serial.send_break
        http://pyserial.readthedocs.org/en/latest/pyserial_api.html#serial.Serial.break_condition
        """
        result = True
        try:
            self.send_break()
        except:
            # In Linux a termios.error is raised in sendBreak and in setBreak.
            # The following break_condition = False is needed to release the reset signal
            # on the target mcu.
            self.break_condition = False
        return result

    def readline(self, timeout=1.0):
        """
        :param timeout: timeout in seconds is the max time that is way for a complete line
        """
        tries = 0
        while 1:
            try:
                block = self.read(512)
                if isinstance(block, bytes):
                    block = str(block.decode())
                elif not isinstance(block, str):
                    raise ValueError("Unknown data")
            except SerialTimeoutException:
                # Exception that is raised on write timeouts.
                block = ''
            except SerialException:
                # In case the device can not be found or can not be configured.
                block = ''
            except ValueError:
                # Raised when parameter are out of range, e.g. baud rate, data bits.
                # UnicodeError-Raised when a Unicode-related encoding or decoding
                # error occurs.
                # It is a subclass of ValueError.
                block = ''
            self.buf += block
            pos = self.buf.find('\n')
            if pos >= 0:
                line, self.buf = self.buf[:pos+1], self.buf[pos+1:]
                return line
            tries += 1
            if tries * self.timeout > timeout:
                break
        line, self.buf = self.buf, ''
        return line

    def readlines(self, timeout=1.0):
        """read all lines that are available. abort after timout
        when no more data arrives."""
        lines = []
        while 1:
            line = self.readline(timeout=timeout)
            if line:
                lines.append(line)
            if not line or line[-1:] != '\n':
                break
        return lines

if __name__ == '__main__':
    # do some simple tests with a Loopback HW (see test.py for details)
    PORT = 0
    # test, only with Loopback HW (shortcut RX/TX pins (3+4 on DSUB 9 and 25) )
    S = EnhancedSerial(PORT)
    # write out some test data lines
    S.write('\n'.join("hello how are you".split()))
    # and read them back

    # python 3 compatibility
    # pylint: disable=superfluous-parens
    print(S.readlines())
    # this one should print an empty list
    print(S.readlines(timeout=0.4))
