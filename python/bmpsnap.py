#!/usr/bin/env python3
'''
bmpsnap.py : save a single frame of BMP data from Arducam Mini

Copyright (C) Simon D. Levy 2017

This file is part of BreezyArduCAM.

BreezyArduCAM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
BreezyArduCAM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with BreezyArduCAM.  If not, see <http://www.gnu.org/licenses/>.
'''

import time
import serial
from sys import stdout

# Modifiable params --------------------------------------------------------------------

PORT = '/dev/ttyACM0' # Ubuntu
#PORT = 'COM4'         # Windows

BAUD = 921600   # Arduino Uno

#SIZE = 0  # 160x120
#SIZE = 1  # 176x144
SIZE = 2  # 320x240
#SIZE = 3  # 352x288
#SIZE = 4  # 640x480
#SIZE = 5  # 800x600
#SIZE = 6  # 1024x768
#SIZE = 7  # 1280x960
#SIZE = 8  # 1600x1200

# helpers ---------------------------------------------------------------------------

def getack(port):
    stdout.write(port.readline().decode())

def sendbyte(port, value):
    port.write(bytearray([value]))

def sendwithack(port, value):
    sendbyte(port, value)
    getack(port)

# main ------------------------------------------------------------------------------

if __name__ == '__main__':

    # Open connection to Arduino
    port = serial.Serial(PORT, BAUD, timeout=2)

    # Validate startup messages
    getack(port)
    getack(port)
    getack(port)

    # Wait a spell
    time.sleep(0.2)

    # Request BMP data
    #sendwithack(port, 0x31)

    # Request single-frame capture
    sendwithack(port, 0x30);

    # Get capture-done message
    getack(port)
    getack(port)

    stdout.write('Writing file ...')
    stdout.flush()

    # Open output file
    outfile = open('test.bmp', 'wb')

    # Read and write bytes until EOF
    while True:
        c = port.read()
        if len(c) == 0:
            break
        outfile.write(c)

    # Close output file
    outfile.close()

    print('\nDone')

