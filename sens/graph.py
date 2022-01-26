import matplotlib.pyplot as plt
import sqlite3
import pandas as pd
import numpy as np
import serial
import datetime


with serial.Serial('COM6', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1.0) as ser:
    ser.reset_output_buffer()
    ser.reset_input_buffer()
    set_string = 'VSET:1.01\n'
    ser.write(set_string.encode())
    ser.write('ISET:10\n'.encode())



import time
import pyvisa
from hmp4040 import hmp4040

rm = pyvisa.ResourceManager()
hmp4040_ps = rm.open_resource('ASRL5::INSTR')
hmp4040 = hmp4040(pyvisa_instr=hmp4040_ps)


#hmp4040_ps.write('*RST')
hmp4040_ps.write('INST OUT1')
hmp4040_ps.write('VOLT 5.8')
hmp4040_ps.write('CURR 10')
hmp4040_ps.write('OUTP:SEL 1')
hmp4040_ps.write('OUTP 1')
print(float(hmp4040_ps.query('MEAS:CURR?')))
# print(hmp4040_ps.query('*IDN?'))
# time.sleep(2)
rm.close()
