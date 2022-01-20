import numpy as np
import pandas as pd
import streamlit as st
import time
import datetime
import math
import serial
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3

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
#this Button is just to refresh, which it only does implicitely lol
#refresh = st.button('refresh')

##MEASUREMENT MAIN APP##
st.subheader('Measurement')
start = st.button('start')

##SETTINGS SIDEBAR##
st.sidebar.subheader('Settings')
connections = []
duration = float(st.sidebar.text_input('Duration of measurement in minutes:',0))
connections = ['COM3', 'COM4', 'COM5']
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


## MEASUREMENTS ##
if (start == True):
    dp,dp_old = 0,0
    t_max = int(duration*60)
    t_max_f = float(duration*60)
    t_start = int(datetime.datetime.timestamp(datetime.datetime.now()))
    t_start_f = float(datetime.datetime.timestamp(datetime.datetime.now()))
    t_elapsed = 0
    counter_col = st.columns(2)
    dp_counter = counter_col[0].empty()
    timer = counter_col[1].empty()
    metrics = st.empty()
    sections = [[12,17],[19,24],[26,30],[32,37],[39,43],[45,50]]
    values = [0,0,0,0,0,0]
    delta_values = [0,0,0,0,0,0]
    while (t_elapsed < (t_start + t_max)):
        dp_counter.metric(label='Datapoints taken:',value=dp,delta=dp-dp_old)
        for port in usable_conns:
            with serial.Serial(port, 9600, timeout=0.5) as ser:
                line = ser.read_until('\n')
                line = line.decode("utf-8")
                #print(line)
                # print(line[0:10]) #SHT31 test
                if (usable_conns[0] == port):
                    for a in range(len(sections)):
                        value = round(float(line[sections[a][0]:sections[a][1]]),4)
                        delta_values[a] = round(values[a] - value,4)
                        values[a] = value
                    dp_old = dp
                    dp += 6

                # else:
                #     value_7 = str(line[11:19]) + ' °C' # SHT31 temp_data
                #     value_8 = str(line[19:24]) + ' rel.hum.'# SHT31 hum_data
                #     # value_9 = str(line[24:31]) + ' V'# PT1000_1 V
                #     # value_10 = str(line[31:39]) + ' °C'# PT1000_1 T
                #     # value_11 = str(line[39:45]) + ' V'#PT1000_2 V
                #     # value_12 = str(line[45:51]) + ' °C'# PT1000_2 T
## METRICS ##
                with metrics.container():
                    if (len(usable_conns) == 1):
                        col = st.columns(6)
                        col[0].metric(label='SHT31_1',value=values[0], delta=delta_values[0])
                        col[1].metric(label='SHT31_1',value=values[1], delta=delta_values[1])
                        col[2].metric(label='PT1000_1',value=values[2], delta=delta_values[2])
                        col[3].metric(label='PT1000_1',value=values[3], delta=delta_values[3])
                        col[4].metric(label='PT1000_2',value=values[4], delta=delta_values[4])
                        col[5].metric(label='PT1000_2',value=values[5], delta=delta_values[5])
                    else:
                        col = st.columns(4)
                        col[0].metric(label='SHT31_1',value=str(value_1) + ' °C', delta=0)
                        col[0].metric(label='SHT31_1',value=str(value_2) + ' rel.hum.', delta=0)
                        col[1].metric(label='SHT31_2',value=value_7, delta=0)
                        col[1].metric(label='SHT31_2',value=value_8, delta=0)
                        col[2].metric(label='PT1000_1',value=value_3, delta=0)
                        col[2].metric(label='PT1000_1',value=value_4, delta=0)
                        col[3].metric(label='PT1000_2',value=value_5, delta=0)
                        col[3].metric(label='PT1000_2',value=value_6, delta=0)
                    t_elapsed = int(datetime.datetime.timestamp(datetime.datetime.now()))
                    t_elapsed_f = float(datetime.datetime.timestamp(datetime.datetime.now()))
                    tim = round(float((t_start_f + t_max_f)-t_elapsed_f),2)
                    if (tim > 0):
                        timer.metric(label='remaining',value=str(tim) + 's')
                    else:
                        timer.metric(label='remaining',value='Done!')
