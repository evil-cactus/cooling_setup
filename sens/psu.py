import pandas as pd
import numpy as np
import serial
import datetime
import os
import sqlite3
import platform


print(platform.system())


# with serial.Serial('COM6', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=2.0) as ser:
#     ser.reset_output_buffer()
#     ser.reset_input_buffer()
#     # ser.write("VSET:1.0\n".encode())
#     # ser.write("VSET:1\n".encode())
#     # ser.write("VSET:2\n".encode())
#     ser.write("VSET:6.4\n".encode())
#     ser.write('VSET?\n'.encode())
#     # ser.write('*IDN?'.encode())
#     output = ser.readline()
#     #print(output)

def psu_voltage_driver(low_volt, high_volt, steps):
    voltages = np.array(np.linspace(float(low_volt),float(high_volt),int(steps)))
    time = steps+1*2*60 #in seconds #change back to 5
    timmin = steps*2 #in minutes#change back to 5
    # print(voltages)
    # print(time, timmin)
    return voltages,timmin





