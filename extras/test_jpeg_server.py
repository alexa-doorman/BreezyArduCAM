#!/usr/bin/env python3
'''
jpgstream.py : display live ArduCAM JPEG images using OpenCV

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
from io import StringIO
from io import BytesIO
from datetime import datetime
import os

import serial

from flask import Flask, Response, send_file

app = Flask(__name__)

from helpers import *

# Modifiable params --------------------------------------------------------------------

PORT = os.environ.get('SERIAL_PORT', '/dev/ttyACM0')

BAUD = 921600       # Change to 115200 for Due
port = None


@app.before_first_request
def spin():
    global port
    port = serial.Serial(PORT, BAUD, timeout=2)

    flush(port)


def flush(port):
    sendbyte(port, 0)
    print('Flushing...')
    while True:
        b = port.read()

        if len(b) < 1:
            break
    print('Flush complete!')


@app.route('/frame')
def frame():
    # Send start flag
    sendbyte(port, 1)

    # We'll report frames-per-second
    start = time.time()
    count = 0

    # Loop over images user hits ESC
    done = False
    while not done:

        # Open a temporary file that we'll write to and read from
        tmpfile = BytesIO()
        # Loop over bytes from Arduino for a single image
        written = False
        prevbyte = None
        while not done:

            # Read a byte from Arduino
            currbyte = port.read(1)

            # If we've already read one byte, we can check pairs of bytes
            if prevbyte:

                # Start-of-image sentinel bytes: write previous byte to temp file
                if ord(currbyte) == 0xd8 and ord(prevbyte) == 0xff:
                    tmpfile.write(prevbyte)
                    written = True

                # Inside image, write current byte to file
                if written:
                    tmpfile.write(currbyte)

                # End-of-image sentinel bytes: close temp file and display its contents
                if ord(currbyte) == 0xd9 and ord(prevbyte) == 0xff:
                    # tmpfile.close()
                    tmpfile.seek(0)
                    # Report FPS
                    elapsed = time.time() - start
                    print('%d frames in %2.2f seconds = %2.2f frames per second' %
                          (count, elapsed, count / elapsed))
                    sendbyte(port, 0)

                    return send_file(tmpfile,
                                     attachment_filename="tmp.jg",
                                     mimetype='image/jpeg')

            # Track previous byte
            prevbyte = currbyte


def stream():
    # Open connection to Arduino with a timeout of two seconds

    # Send start flag
    sendbyte(port, 1)
    print('sent start')

    # We'll report frames-per-second
    start = time.time()
    count = 0

    # Loop over images user hits ESC
    done = False
    while not done:

        # Open a temporary file that we'll write to and read from
        # Loop over bytes from Arduino for a single image
        written = False
        prevbyte = None
        tmpfile = BytesIO()
        while not done:
            # Read a byte from Arduino
            currbyte = port.read(1)

            # If we've already read one byte, we can check pairs of bytes
            if prevbyte and currbyte:
                # Start-of-image sentinel bytes: write previous byte to temp file
                if ord(currbyte) == 0xd8 and ord(prevbyte) == 0xff:
                    tmpfile.write(prevbyte)
                    written = True

                # Inside image, write current byte to file
                if written:
                    tmpfile.write(currbyte)

                # End-of-image sentinel bytes: close temp file and display its contents
                if ord(currbyte) == 0xd9 and ord(prevbyte) == 0xff:
                    # tmpfile.close()
                    tmpfile.seek(0)

                    if tmpfile.getbuffer().nbytes < 1000:  # expect at least 3kb file
                        print('file skipped')
                        count += 1
                        break

                    try:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + tmpfile.getvalue() + b'\r\n\r\n')
                    except:
                        pass
                    count += 1
                    break

            # Track previous byte
            prevbyte = currbyte

    # Send stop flag
    sendbyte(port, 0)

    # Report FPS
    elapsed = time.time() - start
    print('%d frames in %2.2f seconds = %2.2f frames per second' %
          (count, elapsed, count / elapsed))


@app.route('/')
def video_feed():
    try:
        return Response(stream(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    except:
        flush(port)
        return Response(stream(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
