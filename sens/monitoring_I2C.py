import numpy as np
import pandas as pd
import streamlit as st
import time
import datetime
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3
import platform
import os

pltf = platform.system()

if (pltf == 'Linux'):
    # db_path = 'database/2022.db'
    db_path = 'database/2022_1.db'
else:
    db_path = 'C:\\Users\\schum\\Documents\\github\\cooling_setup\\sens\\database\\2022.db'


#small changes to the website itself
st.set_page_config(
    page_title='PTSD4MoMi'
)
#list_of_colors=['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33']
list_of_colors=['#e31a1c','#ff7f00','#6a3d9a','#7cd9b4','#b15928','#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99']

#Let's start!
#st.title('Monitoring-User-Interface for MightyPix Testbench (MUI4MPT)')
st.title('Python Testbench-Sensor Display for Monitoring MightyPix (PTSD4MoMi)')
# st.header('...just call it MoMi')
# st.subheader('by Henry Schumacher')
st.text('Work in Progress...')

st.subheader('Current database of sensors:')
#connect to the database and create table sensors, if not there
conn = sqlite3.connect(db_path)
c = conn.cursor()
data = pd.read_sql('SELECT * FROM sensors ORDER BY sens_id ASC', conn)
st.dataframe(data)
if (len(data) != 0):
    # print(data.iloc[-1:])
    last_id = data.iloc[-1:]
    last_id = int(last_id.values.tolist()[0][0])
else:
    last_id = 0
c.close()

## select your sensors
sensor_type = st.multiselect(
        'What kind of sensor are you adding?',
        ('Temperature', 'Humidity', 'Voltage', 'Current')
    )

sens_pos_l = []
for j in range(len(sensor_type)):
    for i in range(len(data)):
        if data["sens_type"][i] == sensor_type[j]:
            sens_pos = data["sens_des"][i]
            if sens_pos not in sens_pos_l:
                sens_pos_l.append(sens_pos)

sens_chos = st.multiselect('Which sensors?', sens_pos_l)
    
if sens_chos:
    sens_title_l = []
    for sens_chos_i in range(len(sens_chos)):
        sens_title = st.text_input(f'How should {sens_chos[sens_chos_i]} be called?', '')
        sens_title_l.append(sens_title)
else:
    st.info("Please choose at least one sensor!!")

#this Button is just to refresh, whih it only does implicitely lol
refresh = st.button('refresh')

#matplotlib shut up!
plt.rcParams.update({'figure.max_open_warning': 0})

#reconnecting for monitoring
conn = sqlite3.connect(db_path)
c = conn.cursor()
#setup of sensor things
c.execute("SELECT * FROM sensors ORDER BY sens_id ASC")
list_sensor = c.fetchall()
df_list_sensor = pd.DataFrame(list_sensor, columns=['sens_id','sens_type','sens_unit','sens_des'])
# print(df_list_sensor)
print(list_sensor)
numb_sensor = len(list_sensor)

#creating a unique list of sensor types for later use
c.execute("SELECT * FROM sensors")
lst = c.fetchall()
# print("list", lst, "sene",sens_chos)
type_sensor,names = [],[]
for sens_chos_i in range(len(sens_chos)):
    for i in range(len(lst)):
        if lst[i][-1] == sens_chos[sens_chos_i]:
            print( lst[i][-1])
            type_sensor.append(lst[i][1])
            names.append([lst[i][0],lst[i][3]])
type_sensor = list(set(type_sensor))
type_sensor_ids = []
for type in type_sensor:
    c.execute("SELECT * FROM sensors")
    lst = c.fetchall()
    ids,sub,col = [],[],[]
    ids.append(type)
    # print(len(lst))
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
print("ids", type_sensor_ids)

st.subheader('Graphical Monitoring Interface')
graph = st.empty()#create the graph container
if (len(type_sensor) != 0):
    #the monitoring loop
    st.sidebar.subheader('Y-axis scaling')
    nmb_col = st.sidebar.columns(2)
    diag_1_low = nmb_col[0].number_input('1 lower bound',0.)
    diag_1_hgh = nmb_col[1].number_input('1 upper bound',1.)
    diag_2_low = nmb_col[0].number_input('2 lower bound',0.)
    diag_2_hgh = nmb_col[1].number_input('2 upper bound',1.)
    diag_3_low = nmb_col[0].number_input('3 lower bound',0.)
    diag_3_hgh = nmb_col[1].number_input('3 upper bound',1.)
    diag_4_low = nmb_col[0].number_input('4 lower bound',0.)
    diag_4_hgh = nmb_col[1].number_input('4 upper bound',1.)
    scale_change = st.sidebar.button('update y-axis scales')#
    if (scale_change == True):
        diagram_yaxis = [(diag_1_low,diag_1_hgh),(diag_2_low,diag_2_hgh),(diag_3_low,diag_3_hgh),(diag_4_low,diag_4_hgh)]
    else:
        diagram_yaxis = [(diag_1_low,diag_1_hgh),(diag_2_low,diag_2_hgh),(diag_3_low,diag_3_hgh),(diag_4_low,diag_4_hgh)]
    while True:
        now = int(datetime.datetime.now().timestamp())
        fig, ax = plt.subplots(nrows=len(type_sensor),ncols=1, figsize=(12,12), sharex=True)
        for t in range(len(type_sensor)):
            tx = type_sensor[t]
            sens,col = [],[]
            # print(type_sensor_ids)
            for i in range(len(type_sensor_ids)):
                if (tx == type_sensor_ids[i][0]):
                    sens = type_sensor_ids[i][1]
                    # print("sensids",type_sensor_ids)
                    col = type_sensor_ids[i][2]
                    # print("hier", sens, col)
            # print(len(sens))
            for j in range(0,len(sens)):
                for k in range(len(names)):
                    # print("go", sens, sens[j], names[k])
                    if (int(names[k][0]) == sens[j]):
                        sens_name = names[k][1]
                        c.execute('SELECT * FROM measurement WHERE sensor_id=:id ORDER BY time ASC',{'id':sens[j]})
                        df = pd.DataFrame(c.fetchall(),columns=['time','value','sens_id'])
                        ax[t].plot(df['time'],df['value'], color=col[j], lw=0.8)
                        ax[t].scatter(df['time'], df['value'], color=col[j], lw=1.2,label=str(sens_name))
        for n in range(0,len(type_sensor)):
            #for label in ax[n].get_xticklabels(which='major'):
            #    label.set(rotation=30, horizontalalignment='right')
            ax[n].grid(which='both',color='black')
            ax[n].axvline(x=now)
            ax[n].set_facecolor('white')
            ax[n].set_title(str(type_sensor[n])+'-sensors')
            #ax[n].set_ylabel(str(type_sensor[n])+'-sensors')
            # ax[n].set_ylim(diagram_yaxis[n])
            if sens_title and len(sens_title_l) > 0:
                ax[n].legend(loc='upper left', labels = sens_title_l)
            else:
                ax[n].legend(loc='upper left')
        plt.xticks((now, now-15, now-30, now-45, now-60, now-90, now-120), ('now', 'now-15s', 'now-30s', 'now-45s', 'now-60s', 'now-90s', 'now-120s'))
        # plt.xticks((now+1000, now-100000), ('now', 'now-1000s'))
        plt.xlim(now-120,now+10)
        plt.tight_layout()
        
        # plt.show()
        graph.pyplot(fig)
        time.sleep(0.2)
        plt.close()
else:
    st.warning('You\'re missing sensors to be shown here. Maybe add some above.')
