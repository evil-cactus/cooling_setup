import matplotlib.pyplot as plt
import sqlite3
import pandas as pd
import numpy as np
import serial
from serial.tools.list_ports import comports
import datetime
import os
import platform
import pyvisa
from hmp4040 import hmp4040
from miniterm import ask_for_port
'''
with serial.Serial('COM6', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1.0) as ser:
    ser.reset_output_buffer()
    ser.reset_input_buffer()
    set_string = 'VSET:1.01\n'
    ser.write(set_string.encode())
    ser.write('ISET:10\n'.encode())
'''
# ports = ['/dev/ttyACM0','/dev/ttyACM1','/dev/ttyACM2','/dev/ttyUSB0']
# KWR103, ARD1_COM4, ARD2_COM3, HMP4040

print(ask_for_port())

with serial.Serial('/dev/ttyACM1', 9600, timeout=1.0) as ser:
            for a in range(2):
                line = ser.read_until('\r\n'.encode())
                line = line.decode("utf-8")
                print(line)

"""
with serial.Serial('/dev/ttyACM0', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=2.0) as ser:
                ser.reset_output_buffer()
                ser.reset_input_buffer()
                # ser.write("VSET:6.4\n".encode()) #implement the psu.py functionality
                ser.write('VOUT?\n'.encode())
                output = ser.read_until('\n')
                output = output.decode("utf-8")
                value = round(float(output[0:5]),2)
                print(value)
"""
