#by Henry Schumacher - 2022
import numpy as np
import pandas as pd
import streamlit as st
import time
import datetime
import math
import serial
import os
import platform
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3
import pyvisa
from hmp4040 import hmp4040
from psu import psu_voltage_driver

# This program is used to generate an GUI for the measurement of the MoMi-Testbench.
# It uses Arduino Nano Every microcontrollers to read out two SHT31 sensors as well es two PT1000 thermo-resistors.
# Furthermore does it measure and controll the two PSUs with their respective currents and voltages.
# Every command starting with "st." is a function from the package "streamlit" which is used to create a locally hosted webpage.
# To start the program open a terminal, move to this files directory and type in "streamlit run input_gui.py". It will take a couple of seconds and will then open a new tab in the browser.


if (platform.system() == 'Linux'): # This is the path to the database in which the measurements are stored.
    db_path = '/home/momipi/cooling_setup/sens/database/2022.db'
    port_KWR103 = '/dev/ttyACM0'
    port_COM3_equiv = '/dev/ttyACM2'
    port_COM4_equiv = '/dev/ttyACM1'
else:
    db_path = 'C:\\Users\\schum\\Documents\\github\\cooling_setup\\sens\\database\\2022.db'


#small changes to the website itself
st.set_page_config(
    page_title='MoMi-Input'
)

list_of_colors=['#e31a1c','#ff7f00','#6a3d9a','#ffff99','#b15928','#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99']

conn = sqlite3.connect(db_path)  # Connect to the database and create table sensors, if not there.
c = conn.cursor()
c.execute(""" CREATE TABLE IF NOT EXISTS sensors (
    sens_id integer,
    sens_type text,
    sens_unit text,
    sens_des text
    )""")

st.title('Input-GUI for MoMi')
st.subheader('by Henry Schumacher')
st.text('Work in Progress...')

st.sidebar.subheader('Current database of sensors:')#st.subheader('Current database of sensors:')
data = pd.read_sql('SELECT * FROM sensors ORDER BY sens_id ASC', conn)
st.sidebar.dataframe(data)#st.dataframe(data)
if (len(data) != 0):
    last_id = data.iloc[-1:]
    last_id = int(last_id.values.tolist()[0][0])
else:
    last_id = 0
c.close()

refresh = st.sidebar.button('refresh') # This Button is just to refresh, which it only does implicitely.

##MEASUREMENT MAIN APP##
st.subheader('Measurement')


##SETTINGS SIDEBAR##
st.sidebar.subheader('Settings')
connections = []
duration = float(st.sidebar.text_input('Duration of measurement in minutes:',0))
if (platform.system() == 'Linux'):
    connections = [port_COM3_equiv,port_COM4_equiv ]
else:
    connections = ['COM3', 'COM4']
usable_conns = []
for connection in connections:
    try:
        with serial.Serial(str(connection), 9600, timeout=0.5) as ser: # simple connection check
            name = ser.name
            state = ser.is_open
            line = ser.readline()
            if (state == True):
                usable_conns.append(connection)
            ser.close()
        continue
    except serial.serialutil.SerialException:
        continue
# selected_conns = st.sidebar.multiselect('Choose connections:', usable_conns) # This is a stub. This selector is no longer in use.
if (len(connections) != 0):
    st.info('Usable connections are: ' + str(usable_conns)[1:-1])
else:
    st.warning('There are no usable connections. Check USB-connections!')
com3_connect = st.sidebar.checkbox('COM3/ACM2 is connected to SHT31 & PT1000') # how much will have to be read out
com4_connect = st.sidebar.checkbox('COM4/ACM1 is connected to SHT31 & PT1000') # how much will have to be read out

psu_auto_butt = st.checkbox('automate PSU?') # Enable the options for setting a routine up to step through a range of voltages.
# For the peltier-elements voltage is the important metric, therefore it is not supported to range through currents.
timmin_psu_103 = 0 # The KORAD KWR103 is the "time keeper". For my tests they changed in sync.
if (psu_auto_butt == True):
    step = -1
    voltages_103,timmin_psu_103 = psu_voltage_driver(low_103,high_103,steps_103) # Creates lists of voltages which the PSU will be set to. Also total run time is calculated. See psu.py.
    voltages_4040,timmin_psu_4040 = psu_voltage_driver(low_4040,high_4040,steps_4040) # Same as above, just for the other PSU.
    duration = timmin_psu_103 # Overwrites the set duration from the interface above.

start = st.button('start')
## MEASUREMENTS ##
if (start == True):
    dp,dp_old = 0,0 # datapoint counters
    t_max = int(duration*60) # total run time in seconds
    t_max_f = float(duration*60) # as above and floatpoint value
    t_start = int(datetime.datetime.timestamp(datetime.datetime.now())) # time of start as reference
    t_start_f = float(datetime.datetime.timestamp(datetime.datetime.now())) # as above and in floatpoint value
    t_elapsed = 0 # passed time counter
    t_since_last_step = 0 # time counter since last change of voltage
    t_last_step = t_start_f # initial time of above is equal to start time
    counter_col = st.columns(3) # visual item for showing datapoint counter and time
    dp_counter = counter_col[0].empty() # part of above
    timer = counter_col[1].empty() # part of above
    timer_min = counter_col[2].empty() # part of above
    metrics = st.empty() # visual item for showing metrics
    values = [0,0,0,0,0,0,0,0,0,0,0,0]
    delta_values = [0,0,0,0,0,0,0,0,0,0,0,0]
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(""" CREATE TABLE IF NOT EXISTS measurement (
        time datetime,
        value float,
        sensor_id integer,
        PRIMARY KEY (time),
        FOREIGN KEY (sensor_id) REFERENCES sensors(sens_id)
        )""")
    while (t_elapsed < (t_start + t_max)):
        dp_counter.metric(label='Datapoints taken:',value=dp,delta=dp-dp_old)
        for port in usable_conns: # cycle through connected ARDUINOs
            with serial.Serial(port, 9600, timeout=1.0) as ser:
                # If a comX_connect variable is set to TRUE the corresponding
                # ARDUINO is connected to three sensors and all lines of the
                # output are useful.
                if ((port == 'COM3' or port == '/dev/ttyACM2') and com3_connect == True):
                    for a in range(6):
                        line = ser.read_until('\r\n'.encode()) # This only works while using the SHT31_read.ino file provided in this repo.
                        line = line.decode("utf-8")
                        try:
                            line = line.decode("utf-8")
                            value = round(float(line),4)
                            delta_values[a] = round(value - values[a],4) # Only used for the visual metrics
                            values[a] = value # Sets the list-item to be the value later sent to the database.
                        except:
                            continue
                    dp_old = dp
                    dp += 6
                elif ((port == 'COM4' or port == port_COM4_equiv) and com4_connect == True):
                    for a in range(6):
                        line = ser.read_until('\r\n'.encode())
                        try:
                            line = line.decode("utf-8")
                            value = round(float(line),4)
                            delta_values[a] = round(value - values[a],4)
                            values[a] = value
                        except:
                            continue
                    dp_old = dp
                    dp += 6
                elif ((port == 'COM3' or port == port_COM3_equiv) and com3_connect == False):
                    for a in range(2):
                        line = ser.read_until('\r\n'.encode())
                        try:
                            line = line.decode("utf-8")
                            value = round(float(line),4)
                            if (a == 0):
                                delta_values[6] = round(value - values[6],4)
                                values[6] = value
                            if (a == 1):
                                delta_values[7] = round(value - values[7],4)
                                values[7] = value
                        except:
                            continue
                    dp_old = dp
                    dp += 2
                elif ((port == 'COM4' or port == port_COM4_equiv) and com4_connect == False and com3_connect == True):
                    for a in range(2):
                        line = ser.read_until('\r\n'.encode())
                        try:
                            line = line.decode("utf-8")
                            value = round(float(line),4)
                            if (a == 0):
                                delta_values[6] = round(value - values[6],4)
                                values[6] = value
                            if (a == 1):
                                delta_values[7] = round(value - values[7],4)
                                values[7] = value
                        except:
                            continue
                    dp_old = dp
                    dp += 2
        for v in range(len(values)-2): # Index shift due to how pandas dataframes and my indexing of sensors work.
            time_data = float(datetime.datetime.timestamp(datetime.datetime.now())) + (0.1*(v-1)) # Time is key - literally.
            c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data, 'value':values[v], 'id':v+1})
            conn.commit()
        t_since_last_step = round(float(datetime.datetime.timestamp(datetime.datetime.now())) - t_last_step,2)
        # Check if it's time for a voltage step already
        # The second condition is connected to the start of a measurement, where step-list-item 0 is needed.
        if ((psu_auto_butt == True and t_since_last_step >= 300) or (psu_auto_butt == True and step == -1)):
            step += 1
            t_last_step = float(datetime.datetime.timestamp(datetime.datetime.now())) # Save for interval keeping.
            ### HMP4040 ###
            rm = pyvisa.ResourceManager()
            if(platform.system() == 'Linux'):
                hmp4040_ps = rm.open_resource('ASRL/dev/ttyUSB0::INSTR')
            else:
                hmp4040_ps = rm.open_resource('ASRL5::INSTR')
            # hmp4040 = hmp4040(pyvisa_instr=hmp4040_ps)
            hmp4040_ps.write('INST OUT1') # Select output-channel on PSU.
            set_string = 'VOLT ' + str(voltages_4040[step]) # Create the string, which dictates the voltage
            hmp4040_ps.write(set_string) # Set the voltage.
            hmp4040_ps.write('CURR 10') # Set the current to a value above the maximum expected value.
            hmp4040_ps.write('OUTP:SEL1') # Select Channel 1 for next operation.
            hmp4040_ps.write('OUTP 1') # Activate Channel.
            V_out_4040 = float(hmp4040_ps.query('MEAS:VOLT?')) # Query the current voltage-value applied.
            value = V_out_4040
            delta_values[10] = round(value - values[10],2)
            values[10] = value
            I_out_4040 = float(hmp4040_ps.query('MEAS:CURR?'))  # Query the current-value applied at the moment
            value = I_out_4040
            delta_values[11] = round(value - values[11],2)
            values[11] = value
            rm.close()
            ### KW103 ###
            if(platform.system() == 'Windows'):
                port_KWR103 = 'COM6'
            with serial.Serial(port_KWR103, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1.0) as ser:
                ser.reset_output_buffer()
                ser.reset_input_buffer()
                set_string = 'VSET:'+str(voltages_103[step])+'\n' # Create the string, which dictates the voltage
                ser.write(set_string.encode()) # Set the voltage.
                ser.write('ISET:10\n'.encode()) # Set the current to a value above the maximum expected value.
                ser.write('VOUT?\n'.encode()) # Query the current voltage-value applied.
                output = ser.read_until('\n')
                output = output.decode("utf-8")
                if (output[0] == '0'):
                    value = round(float(output[1:5]),2)
                    delta_values[8] = round(value - values[8],2)
                    values[8] = value
                else:
                    value = round(float(output[0:5]),2)
                    delta_values[8] = round(value - values[8],2)
                    values[8] = value
                ser.write('IOUT?\n'.encode()) # Query the current-value applied at the moment
                output = ser.read_until('\n')
                output = output.decode("utf-8")
                if (output[0] == '0'):
                    value = round(float(output[1:5]),2)
                    delta_values[9] = round(value - values[9],2)
                    values[9] = value
                else:
                    value = round(float(output[0:5]),2)
                    delta_values[9] = round(value - values[9],2)
                    values[9] = value
                dp_old = dp
                dp += 4
        else:
            # This is the same as before, just with no voltage adjustment.
            rm = pyvisa.ResourceManager()
            if(platform.system() == 'Linux'):
                hmp4040_ps = rm.open_resource('ASRL/dev/ttyUSB0::INSTR')
            else:
                hmp4040_ps = rm.open_resource('ASRL5::INSTR')
            # hmp4040 = hmp4040(pyvisa_instr=hmp4040_ps)
            try:
                V_out_4040 = float(hmp4040_ps.query('MEAS:VOLT?'))
                value = V_out_4040
                delta_values[10] = round(value - values[10],2)
                values[10] = value
                I_out_4040 = float(hmp4040_ps.query('MEAS:CURR?'))
                value = I_out_4040
                delta_values[11] = round(value - values[11],2)
                values[11] = value
                rm.close()
            except:
                continue
            if(platform.system() == 'Windows'):
                port_KWR103 = 'COM6'
            with serial.Serial(port_KWR103, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=2.0) as ser:
                ser.reset_output_buffer()
                ser.reset_input_buffer()
                ser.write('VOUT?\n'.encode())
                output = ser.read_until('\n')
                output = output.decode("utf-8")
                if (output[0] == '0'):
                    value = round(float(output[1:5]),2)
                    delta_values[8] = round(value - values[8],2)
                    values[8] = value
                else:
                    value = round(float(output[0:5]),2)
                    delta_values[8] = round(value - values[8],2)
                    values[8] = value
                ser.write('IOUT?\n'.encode())
                output = ser.read_until('\n')
                output = output.decode("utf-8")
                if (output[0] == '0'):
                    value = round(float(output[1:5]),2)
                    delta_values[9] = round(value - values[9],2)
                    values[9] = value
                else:
                    value = round(float(output[0:5]),2)
                    delta_values[9] = round(value - values[9],2)
                    values[9] = value
                dp_old = dp
                dp += 4
                ## SQL ##
        for v in {8,9,10,11}:
            time_data = float(datetime.datetime.timestamp(datetime.datetime.now())) + 0.1 + v * 0.01
            c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data, 'value':values[v], 'id':v+1})
            conn.commit()
            ## METRICS ##
            # Update the visual metrics for easy checking of the current measurements.
            with metrics.container():
                if (len(usable_conns) == 1):
                    col = st.columns(5)
                    col[0].metric(label='SHT31_1',value=str(values[0]) + ' °C', delta=str(delta_values[0]) + ' °C', delta_color='inverse')
                    col[0].metric(label='SHT31_1',value=str(values[1]) + ' %', delta=str(delta_values[1]) + ' %', delta_color='inverse')
                    col[1].metric(label='PT1000_1',value=str(values[2]) + ' V', delta=str(delta_values[2]) + ' V')
                    col[1].metric(label='PT1000_1',value=str(values[3]) + ' °C', delta=str(delta_values[3]) + ' °C')
                    col[2].metric(label='PT1000_2',value=str(values[4]) + ' V', delta=str(delta_values[4]) + ' V')
                    col[2].metric(label='PT1000_2',value=str(values[5]) + ' °C', delta=str(delta_values[5]) + ' °C')
                    col[3].metric(label='PSU_KWR103',value=str(values[8]) + ' V', delta=str(delta_values[8]) + ' V')
                    col[3].metric(label='PSU_KWR103',value=str(values[9]) + ' A', delta=str(delta_values[9]) + ' A')
                    col[4].metric(label='PSU_HMP4040',value=str(values[10]) + ' V', delta=str(delta_values[10]) + ' V')
                    col[4].metric(label='PSU_HMP4040',value=str(values[11]) + ' A', delta=str(delta_values[11]) + ' A')
                else:
                    col = st.columns(4)
                    col[0].metric(label='SHT31_1',value=str(values[0]) + ' °C', delta=str(delta_values[0]) + ' °C', delta_color='inverse')
                    col[0].metric(label='SHT31_1',value=str(values[1]) + ' %', delta=str(delta_values[1]) + ' %', delta_color='inverse')
                    col[1].metric(label='SHT31_2',value=str(values[6]) + ' °C', delta=str(delta_values[6]) + ' °C', delta_color='inverse')
                    col[1].metric(label='SHT31_2',value=str(values[7]) + ' %', delta=str(delta_values[7]) + ' %', delta_color='inverse')
                    col[2].metric(label='PT1000_1',value=str(values[2]) + ' V', delta=str(delta_values[2]) + ' V')
                    col[2].metric(label='PT1000_1',value=str(values[3]) + ' °C', delta=str(delta_values[3]) + ' °C')
                    col[2].metric(label='PT1000_2',value=str(values[4]) + ' V', delta=str(delta_values[4]) + ' V')
                    col[2].metric(label='PT1000_2',value=str(values[5]) + ' °C', delta=str(delta_values[5]) + ' °C')
                    col[3].metric(label='PSU_KWR103',value=str(values[8]) + ' V', delta=str(delta_values[8]) + ' V')
                    col[3].metric(label='PSU_KWR103',value=str(values[9]) + ' A', delta=str(delta_values[9]) + ' A')
                    col[3].metric(label='PSU_HMP4040',value=str(values[10]) + ' V', delta=str(delta_values[10]) + ' V')
                    col[3].metric(label='PSU_HMP4040',value=str(values[11]) + ' A', delta=str(delta_values[11]) + ' A')
                t_elapsed = int(datetime.datetime.timestamp(datetime.datetime.now()))
                t_elapsed_f = float(datetime.datetime.timestamp(datetime.datetime.now()))
                tim = round(float((t_start_f + t_max_f)-t_elapsed_f),2)
                timmin = round(tim/60,1)
                # Update timer.
                if (tim > 0):
                    timer.metric(label='remaining',value=str(tim) + 's')
                    timer_min.metric(label='remaining',value=str(timmin) + ' min')
                else:
                    timer.metric(label='remaining',value='Done!')

    conn.close()
