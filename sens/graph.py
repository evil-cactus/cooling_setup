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
'''
with serial.Serial('COM6', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1.0) as ser:
    ser.reset_output_buffer()
    ser.reset_input_buffer()
    set_string = 'VSET:1.01\n'
    ser.write(set_string.encode())
    ser.write('ISET:10\n'.encode())
'''
ports = ['/dev/ttyAMC0','/dev/ttyAMC1','/dev/ttyAMC2','/dev/ttyUSB0']
# KWR103, ARD1_COM4, ARD2_COM3, HMP4040

rm = pyvisa.ResourceManager()
hmp4040_ps = rm.open_resource('ASRL/dev/ttyUSB0::INSTR')
hmp4040 = hmp4040(pyvisa_instr=hmp4040_ps)
hmp4040_ps.write('INST OUT1')
set_string = 'VOLT 4.2'
hmp4040_ps.write(set_string)
hmp4040_ps.write('CURR 10')
hmp4040_ps.write('OUTP:SEL1')
hmp4040_ps.write('OUTP 1')
V_out_4040 = float(hmp4040_ps.query('MEAS:VOLT?'))
print(V_out_4040)


with serial.Serial('/dev/ttyAMC0', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1.0) as ser:
                ser.reset_output_buffer()
                ser.reset_input_buffer()
                # ser.write("VSET:6.4\n".encode()) #implement the psu.py functionality
                ser.write('VOUT?\n'.encode())
                output = ser.read_until('\n')
                output = output.decode("utf-8")
