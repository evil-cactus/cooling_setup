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


if (platform.system() == 'Linux'):
    db_path = '/home/momipi/cooling_setup/sens/database/2022.db'
else:
    db_path = 'C:\\Users\\schum\\Documents\\github\\cooling_setup\\sens\\database\\2022.db'


#small changes to the website itself
st.set_page_config(
    page_title='MoMi-Input'
)
#list_of_colors=['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33']
list_of_colors=['#e31a1c','#ff7f00','#6a3d9a','#ffff99','#b15928','#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99']
#connect to the database and create table sensors, if not there
conn = sqlite3.connect(db_path)
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
# this Button is just to refresh, which it only does implicitely lol
refresh = st.sidebar.button('refresh')

##MEASUREMENT MAIN APP##
st.subheader('Measurement')


##SETTINGS SIDEBAR##
st.sidebar.subheader('Settings')
connections = []
duration = float(st.sidebar.text_input('Duration of measurement in minutes:',0))
if (platform.system() == 'Linux'):
    connections = ['/dev/ttyACM2','/dev/ttyACM1' ]
else:
    connections = ['COM3', 'COM4']
usable_conns = []
for connection in connections:
    try:
        with serial.Serial(str(connection), 9600, timeout=0.5) as ser:
            name = ser.name
            state = ser.is_open
            line = ser.readline()
            if (state == True):
                usable_conns.append(connection)
            ser.close()
        continue
    except serial.serialutil.SerialException:
        continue
selected_conns = st.sidebar.multiselect('Choose connections:', usable_conns)
if (len(connections) != 0):
    st.info('Usable connections are: ' + str(usable_conns)[1:-1])
else:
    st.warning('There are no usable connections. Check USB-connections!')
com3_connect = st.sidebar.checkbox('COM3/ACM2 is connected to SHT31 & PT1000')
com4_connect = st.sidebar.checkbox('COM4/ACM1 is connected to SHT31 & PT1000')

psu_auto_butt = st.checkbox('automate PSU?')
timmin_psu_103 = 0
if (psu_auto_butt == True):
    psu_cont = st.empty()
    with psu_cont.container():
        st.subheader('KORAD KWR103 Settings (lower peltier)')
        low_103 = st.number_input('initial voltage for KW103')
        high_103 = st.number_input('target voltage for KW103')
        steps_103 = st.number_input('voltage steps for KW103')
        # st.text('suggested number of steps: ' + str(int((high_103-low_103)*5 + 1)))
        st.subheader('R&S HMP4040 Settings (upper peltier)')
        low_4040 = st.number_input('initial voltage for HMP4040')
        high_4040 = st.number_input('target voltage for HMP4040')
        steps_4040 = st.number_input('voltage steps for HMP4040')
        # st.text('suggested number of steps: ' + str(int((high_4040-low_4040)*5 + 1)))
    step = -1
    voltages_103,timmin_psu_103 = psu_voltage_driver(low_103,high_103,steps_103)
    voltages_4040,timmin_psu_4040 = psu_voltage_driver(low_4040,high_4040,steps_4040)
    duration = timmin_psu_103

start = st.button('start')
## MEASUREMENTS ##
if (start == True):
    dp,dp_old = 0,0
    t_max = int(duration*60)
    t_max_f = float(duration*60)
    t_start = int(datetime.datetime.timestamp(datetime.datetime.now()))
    t_start_f = float(datetime.datetime.timestamp(datetime.datetime.now()))
    t_elapsed = 0
    t_since_last_step = 0
    t_last_step = t_start_f
    counter_col = st.columns(3)
    dp_counter = counter_col[0].empty()
    timer = counter_col[1].empty()
    timer_min = counter_col[2].empty()
    metrics = st.empty()
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
        for port in usable_conns:
            with serial.Serial(port, 9600, timeout=1.0) as ser:
                #print(line)
                # print(line[0:10]) #SHT31 test
                if ((port == 'COM3' or port == '/dev/ttyACM2') and com3_connect == True):
                    for a in range(6):
                        line = ser.read_until('\r\n'.encode())
                        line = line.decode("utf-8")
                        try:
                            value = round(float(line),4)
                            delta_values[a] = round(value - values[a],4)
                            values[a] = value
                        except:
                            continue
                    dp_old = dp
                    dp += 6
                elif ((port == 'COM4' or port == '/dev/ttyACM1') and com4_connect == True):
                    for a in range(6):
                        line = ser.read_until('\r\n'.encode())
                        line = line.decode("utf-8")
                        try:
                            value = round(float(line),4)
                            delta_values[a] = round(value - values[a],4)
                            values[a] = value
                        except:
                            continue
                    dp_old = dp
                    dp += 6
                if ((port == 'COM3' or port == '/dev/ttyACM2') and com3_connect == False):
                    for a in range(2):
                        line = ser.read_until('\r\n'.encode())
                        line = line.decode("utf-8")
                        try:
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
                elif ((port == 'COM4' or port == '/dev/ttyACM1') and com4_connect == False):
                    for a in range(2):
                        line = ser.read_until('\r\n'.encode())
                        line = line.decode("utf-8")
                        try:
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
        for v in range(len(values)-2):
            time_data = float(datetime.datetime.timestamp(datetime.datetime.now())) + (0.1*(v-1))
            c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data, 'value':values[v], 'id':v+1})
            conn.commit()
        t_since_last_step = round(float(datetime.datetime.timestamp(datetime.datetime.now())) - t_last_step,2)
        if ((psu_auto_butt == True and t_since_last_step >= 300) or (psu_auto_butt == True and step == -1)):
            step += 1
            t_last_step = float(datetime.datetime.timestamp(datetime.datetime.now()))
            ### HMP4040 ###
            rm = pyvisa.ResourceManager()
            if(platform.system() == 'Linux'):
                hmp4040_ps = rm.open_resource('ASRL/dev/ttyUSB0::INSTR')
            else:
                hmp4040_ps = rm.open_resource('ASRL5::INSTR')
            # hmp4040 = hmp4040(pyvisa_instr=hmp4040_ps)
            hmp4040_ps.write('INST OUT1')
            set_string = 'VOLT ' + str(voltages_4040[step])
            hmp4040_ps.write(set_string)
            hmp4040_ps.write('CURR 10')
            hmp4040_ps.write('OUTP:SEL1')
            hmp4040_ps.write('OUTP 1')
            V_out_4040 = float(hmp4040_ps.query('MEAS:VOLT?'))
            value = V_out_4040
            delta_values[10] = round(value - values[10],2)
            values[10] = value
            I_out_4040 = float(hmp4040_ps.query('MEAS:CURR?'))
            value = I_out_4040
            delta_values[11] = round(value - values[11],2)
            values[11] = value
            rm.close()
            ### KW103 ###
            if(platform.system() == 'Linux'):
                port_KWR103 = '/dev/ttyAMC0'
            else:
                port_KWR103 = 'COM6'
            with serial.Serial(port, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1.0) as ser:
                ser.reset_output_buffer()
                ser.reset_input_buffer()
                set_string = 'VSET:'+str(voltages_103[step])+'\n'
                ser.write(set_string.encode())
                ser.write('ISET:10\n'.encode())
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
        else:
            rm = pyvisa.ResourceManager()
            if(platform.system() == 'Linux'):
                hmp4040_ps = rm.open_resource('ASRL/dev/ttyUSB0::INSTR')
            else:
                hmp4040_ps = rm.open_resource('ASRL5::INSTR')
            # hmp4040 = hmp4040(pyvisa_instr=hmp4040_ps)
            V_out_4040 = float(hmp4040_ps.query('MEAS:VOLT?'))
            value = V_out_4040
            delta_values[10] = round(value - values[10],2)
            values[10] = value
            I_out_4040 = float(hmp4040_ps.query('MEAS:CURR?'))
            value = I_out_4040
            delta_values[11] = round(value - values[11],2)
            values[11] = value
            rm.close()
            if(platform.system() == 'Linux'):
                port_KWR103 = '/dev/ttyAMC0'
            else:
                port_KWR103 = 'COM6'
            with serial.Serial(port, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1.0) as ser:
                ser.reset_output_buffer()
                ser.reset_input_buffer()
                # ser.write("VSET:6.4\n".encode()) #implement the psu.py functionality
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
                if (tim > 0):
                    timer.metric(label='remaining',value=str(tim) + 's')
                    timer_min.metric(label='remaining',value=str(timmin) + ' min')
                else:
                    timer.metric(label='remaining',value='Done!')

    conn.close()
