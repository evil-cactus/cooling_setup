import numpy as np
import pandas as pd
import streamlit as st
import time
import datetime
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3
#small changes to the website itself
st.set_page_config(
    page_title='PTSD4MoMi'
)
#list_of_colors=['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33']
list_of_colors=['#e31a1c','#fdbf6f','#ff7f00','#6a3d9a','#ffff99','#b15928','#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99']
#connect to the database and create table sensors, if not there
conn = sqlite3.connect('./database/first.db')
c = conn.cursor()
c.execute(""" CREATE TABLE IF NOT EXISTS sensors (
    sens_id integer,
    sens_type text,
    sens_unit text,
    sens_des text
    )""")

#Let's start!
#st.title('Monitoring-User-Interface for MightyPix Testbench (MUI4MPT)')
st.title('Python Testbench-Sensor Display for Monitoring MightyPix (PTSD4MoMi)')
st.header('...just call it MoMi')
st.subheader('by Henry Schumacher')
st.text('Work in Progress...')

st.subheader('Current database of sensors:')
data = pd.read_sql('SELECT * FROM sensors ORDER BY sens_id ASC', conn)
st.dataframe(data)
if (len(data) != 0):
    last_id = data.iloc[-1:]
    last_id = int(last_id.values.tolist()[0][0])
else:
    last_id = 0
c.close()
#this Button is just to refresh, which it only does implicitely lol
refresh = st.button('refresh')

#create the sensors
sensor_type = st.radio(
    'What kind of sensor are you adding?',
    ('temperature', 'humidity', 'voltage', 'current', 'other')
)

if (sensor_type == "temperature"):
    sensor_unit = st.radio('Choose unit of sensor:', ('Kelvin', 'Degrees Celsius', 'Freedom Units'))
elif (sensor_type == "humidity"):
    sensor_unit = 'feucht'
    st.info('Unit of humidity-sensor does not need to be specified. It has been set automatically.')
elif (sensor_type == 'voltage'):
    sensor_unit = st.radio('Choose unit of sensor:', ('V', 'mV', 'µV', 'nV'))
elif (sensor_type == 'current'):
    sensor_unit = st.radio('Choose unit of sensor:', ('A', 'mA', 'µA', 'nA'))
elif (sensor_type == 'other'):
    sensor_type = st.text_input('Name type of sensor:')
    sensor_unit = st.text_input('Name unit of sensor measurement:')

if (sensor_unit == 'µA'):
    sensor_unit = 'uA'
elif (sensor_unit == 'µV'):
    sensor_unit = 'uV'

sensor_name = st.text_input('Name of new sensor:')

sensor_id = last_id + 1
sensor_des = sensor_name
#
st.info('Please check before submission! You will add a ' + str(sensor_type) + '-sensor with the name \n"' + str(sensor_name) + '" to the database. Its ID will be: ' + str(sensor_id) + '.')
#now, all the information about the sensor are there and it can be submitted


if st.button('submit to database'):
    conn = sqlite3.connect('./database/first.db')
    c = conn.cursor()
    c.execute("INSERT INTO sensors VALUES (:id, :type, :unit, :desc)", {'id':sensor_id, 'type':sensor_type, 'unit':sensor_unit, 'desc':sensor_des})
    conn.commit()
    c.close()
    st.success('Your input has been adopted into the database!')
else:
    st.warning('Nothing has been submitted yet!')
#input complete

#matplotlib shut up!
plt.rcParams.update({'figure.max_open_warning': 0})

#reconnecting for monitoring
conn = sqlite3.connect('./database/first.db')
c = conn.cursor()

#setup of sensor things
c.execute("SELECT * FROM sensors ORDER BY sens_id ASC")
list_sensor = c.fetchall()
df_list_sensor = pd.DataFrame(list_sensor, columns=['sens_id','sens_type','sens_unit','sens_des'])
numb_sensor = len(list_sensor)

#creating a unique list of sensor types for later use
c.execute("SELECT * FROM sensors")
lst = c.fetchall()
type_sensor = []
for i in range(len(lst)):
    type_sensor.append(lst[i][1])
type_sensor = list(set(type_sensor))
type_sensor_ids = []
for type in type_sensor:
    c.execute("SELECT * FROM sensors")
    lst = c.fetchall()
    ids,sub,col = [],[],[]
    ids.append(type)
    for i in range(len(lst)):
        if (lst[i][1] == type):
            sub.append(lst[i][0])
    ids.append(sub)
    for i in range(len(sub)):
        if i > len(list_of_colors):
            i = i%list_of_colors
        col.append(list_of_colors[i])
    ids.append(col)
    type_sensor_ids.append(ids)

st.subheader('Graphical Monitoring Interface')
graph = st.empty()#create the graph container
if (len(type_sensor) != 0):
    #the monitoring loop
    while True:
        now = int(datetime.datetime.now().timestamp())
        fig, ax = plt.subplots(nrows=len(type_sensor),ncols=1, figsize=(12,12), sharex=True)
        for t in range(len(type_sensor)):
            tx = type_sensor[t]
            sens,col = [],[]
            for i in range(len(type_sensor_ids)):
                if (tx == type_sensor_ids[i][0]):
                    sens = type_sensor_ids[i][1]
                    col = type_sensor_ids[i][2]
            for j in range(0,len(sens)):
                c.execute('SELECT * FROM measurement WHERE sensor_id=:id ORDER BY time ASC',{'id':sens[j]})
                df = pd.DataFrame(c.fetchall(),columns=['time','value','sens_id'])
                df['date'] = pd.to_datetime(df['time'],unit='ms')
                ax[t].plot(df['date'],df['value'], color=col[j], lw=0.8)
                ax[t].scatter(df['date'], df['value'], color=col[j], lw=1.2,label=str(tx)+'-'+str(j))
        for n in range(0,len(type_sensor)):
            ax[n].grid(which='both',color='black')
            ax[n].set_facecolor('white')
            ax[n].set_ylabel(str(type_sensor[n])+'-sensors')
            ax[n].set_ylim(0,1)
            ax[n].legend(loc='upper left')
        plt.xlim(now-100,now)
        plt.tight_layout()
        graph.pyplot(fig)
        time.sleep(0.5)
else:
    st.warning('You\'re missing sensors to be shown here. Maybe add some above.')
