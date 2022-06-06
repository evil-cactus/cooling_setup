#!/usr/bin/python

from cProfile import run
from turtle import pos, position
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
import timeit
from random import randint
import matplotlib.patches as mpatches

# @st.experimental_singleton
def get_database_connection(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    # c = self.conn.cursor()
    return conn

def page_config(conn):
    st.set_page_config(
        page_title='PTSD4MoMi'
    )
    st.title('Online Monitoring')
    st.subheader('Current database of sensors:')
    #connect to the database and create table sensors, if not there
    c = conn.cursor()
    data = pd.read_sql("""SELECT sens_id ,
                sens_type ,
                sens_unit ,
                sens_des ,
                sens_name 
                FROM sensors as s1  
        WHERE NOT EXISTS(
            SELECT *
            FROM sensors AS s2
            WHERE s2.sens_id = s1.sens_id
            AND s2.valid_from > s1.valid_from
        )
        ORDER BY sens_id ASC""", conn)
    st.dataframe(data)
    if (len(data) != 0):
        last_id = data.iloc[-1:]
        last_id = int(last_id.values.tolist()[0][0])
    else:
        last_id = 0
    c.close()
    return(data)
  
  
def sensor_selection(conn, data):
    sensor_type = st.multiselect(
            'What kind of sensor are you adding?',
            ('Temperature/Humidity', 'Voltage/Current'),default=('Temperature/Humidity', 'Voltage/Current')
        )
    sens_pos_l = []
    for j in range(len(sensor_type)):
        for i in range(len(data)):
            if data["sens_type"][i] in  sensor_type[j]:
                sens_pos = data["sens_des"][i]
                if sens_pos not in sens_pos_l:
                    sens_pos_l.append(sens_pos)

    sens_chos = st.multiselect('Which sensors?', sens_pos_l,default=sens_pos_l)
    sens_title_l = []
    if sens_chos:
        sens_title_l = []
        sens_title_def = {}
        for sens_chos_i in range(len(sens_chos)):
            c = conn.cursor()
            c.execute("""SELECT * FROM sensors as s1  
                        WHERE NOT EXISTS(
                            SELECT *
                            FROM sensors AS s2
                            WHERE s2.sens_id = s1.sens_id
                            AND s2.valid_from > s1.valid_from
                        )
                        ORDER BY sens_id ASC""")
            rows = c.fetchall()
            last_valid=0
            for row in rows:
                if sens_chos[sens_chos_i] == row[3]:
                    sens_title_def[sens_chos[sens_chos_i]] = row[-2]
                    last_valid=row[-1]
            sens_title = st.text_input(f'How should {sens_chos[sens_chos_i]} be called?', f'{sens_title_def[sens_chos[sens_chos_i]]}')
            sens_title_l.append(sens_title) 
            conn.cursor().execute( "UPDATE sensors SET sens_name = ? where sens_des = ? and valid_from = ?", ( sens_title,sens_chos[sens_chos_i],last_valid))
            conn.commit()
            # sens_correct()
    else:
        st.info("Please choose at least one sensor!!")
    
    meas_time = st.number_input("How long do you want to look back in time (in sec)?",240)

    return(sens_chos, meas_time, sens_title_l, sensor_type)



#creating a unique list of sensor types for later use
# @st.cache
def sens_correct(conn, sens_chos, sens_title_l):
    c = conn.cursor()
    c.execute("""SELECT 
                sens_id ,
                sens_type ,
                sens_unit ,
                sens_des ,
                sens_name 
                FROM sensors as s1  
                WHERE NOT EXISTS(
                    SELECT *
                    FROM sensors AS s2
                    WHERE s2.sens_id = s1.sens_id
                    AND s2.valid_from > s1.valid_from
                )
                ORDER BY sens_id ASC""")  
    lst = c.fetchall()
    corr_sensor = []
    type_sensor = []
    for sens_chos_i in range(len(sens_chos)):
        color = '#%06X' % randint(0, 0xFFFFFF)
        for i in range(len(lst)):

            if lst[i][-2] == sens_chos[sens_chos_i]: ##check for correct sensor
                if (lst[i][1]) not in type_sensor:
                    type_sensor.append((lst[i][1]))    
                corr_sensor.append((lst[i][1],lst[i][4], lst[i][3],f"{color}"))
    c.close()
    return corr_sensor, type_sensor

# @st.cache(allow_output_mutation=True)
def plots_style(fig, ax, pos, meas_time):
    now = int(datetime.datetime.now().timestamp())
    meas_time_unit = "s"
    if meas_time:
        ax[pos].set_xticks((now, now-(meas_time/2), now-(meas_time/10), now-meas_time), ('now', f'now-{meas_time/2}{meas_time_unit}',f'now-{meas_time/10}{meas_time_unit}',f'now-{meas_time}{meas_time_unit}'))
        ax[pos].set_xlim(now-meas_time,now)
    else:
        ax[pos].set_xticks((now, now-15, now-30, now-45, now-60, now-90, now-120), ('now', 'now-15s', 'now-30s', 'now-45s', 'now-60s', 'now-90s', 'now-120s'))
        ax[pos].set_xlim(now-120,now)

    # return(fig, ax)

# @st.cache
def get_initial_fig(type_sensor,corr_sensor):
    col = 1
    row = len(type_sensor)  
    fig, ax = plt.subplots(row, col, figsize=(12,12))
    for type in range(len(type_sensor)):
        for i, sens in enumerate(range(len(corr_sensor))):
            if type_sensor[type] == corr_sensor[sens][0]:
                ax[type].grid(which='both',color='black')
                ax[type].set_facecolor('white')
                ax[type].set_title(str(type_sensor[type])+'-sensors')
                ax[type].set_ylabel(str(type_sensor[type]))
    return fig, ax

def graphical_mon(conn, corr_sensor, type_sensor, meas_time, sens_chos):
    st.subheader('Graphical Monitoring Interface')
    graph = st.empty()#create the graph container
    c = conn.cursor() 
    legend_label = []
    color_l = []
    fig, ax = get_initial_fig(type_sensor, corr_sensor)
    while True:
        for type in range(len(type_sensor)):
            ref_time=datetime.datetime.now()-datetime.timedelta(seconds=meas_time)
            plots_style(fig, ax , type , meas_time)
            for i, sens in enumerate(range(len(corr_sensor))):
                if type_sensor[type] == corr_sensor[sens][0]:
                    sens_name = corr_sensor[sens][1]
                    sens_title = corr_sensor[sens][-3]
                    # print("timestamp: ",datetime.datetime.timestamp(ref_time))
                    # print("datetime: ",ref_time)
                    c.execute('SELECT time,value FROM measurement WHERE sensor_id=:id and time >:ref_time ORDER BY time ASC',{'id':i,'ref_time':datetime.datetime.timestamp(ref_time)})
                    # c.execute('SELECT time,value FROM measurement WHERE sensor_id=:id and time >:ref_time ORDER BY time ASC',{'id':i,'ref_time':ref_time})
                    # c.execute('SELECT time,value FROM measurement WHERE sensor_id=:id ORDER BY time ASC',{'id':i})
                    #c.execute('SELECT value FROM measurement where sensor_id=:id ORDER by time ASC', {'id':i})
                    #print(c)
                    # print(c.fetchall())
                    df = pd.DataFrame(c.fetchall(),columns=['time','value'])
                    #df = pd.DataFrame(c.fetchall(), columns = ['value'])
                    # print(i,sens,sens_name)
                    print(corr_sensor[sens])

                    ax[type].plot(df['time'],df['value'], color=corr_sensor[sens][-1], lw=0.8)                    
                    ax[type].scatter(df['time'], df['value'], color=corr_sensor[sens][-1], lw=1.2,label=str(sens_title))
                    #print(df['value'])
                    patch = mpatches.Patch(color = corr_sensor[sens][-1], label = str(sens_title))
                    if sens_title not in legend_label:
                        #print(corr_sensor[sens][-1])
                        legend_label.append(sens_title)  
                        color_l.append(patch)
    
            fig.legend(handles = color_l)
            # plt.tight_layout()
            graph.pyplot(fig)
            time.sleep(0.1)
            plt.close()
    
    

def IV_scan(conn, corr_sensor, type_sensor, meas_time, sens_type):
    # print("test")
    # graph2 = st.empty()#create the graph container
    c = conn.cursor()
    fig, ax  = plt.subplots(1,1, figsize =(12,12))
    now = int(datetime.datetime.now().timestamp())
    # meas_time_unit = "s"
    # ax.set_xticks((now, now-(meas_time/2), now-(meas_time/10), now-meas_time), ('now', f'now-{meas_time/2}{meas_time_unit}',f'now-{meas_time/10}{meas_time_unit}',f'now-{meas_time}{meas_time_unit}'))
    # ax.set_xlim(now-meas_time,now)
    voltage, current = [], []
    if "Voltage/Current" in sens_type:
        IV_sens = [sens for sens in corr_sensor if sens[0] == "Voltage" or sens[0]== "Current"]
        while True:
            for IV_sens_i in IV_sens:
                ref_time=datetime.datetime.now()-datetime.timedelta(seconds=meas_time)
                c.execute('SELECT * FROM sensors WHERE sens_type =?', (IV_sens_i[0],))
                rows = c.fetchall()
                for row in rows:
                    # c.execute('SELECT * FROM measurement WHERE sensor_id=:id and time >:ref_time ORDER BY time ASC',{'id':row[0],'ref_time':datetime.datetime.timestamp(ref_time)})
                    c.execute('SELECT * FROM measurement WHERE sensor_id=:id ORDER BY time ASC',{'id':row[0]})
                    print(row[1])
                    if row[1] == "Current":
                        df_I = pd.DataFrame(c.fetchall(),columns=['time','value','sens_id'])
                        current = df_I['value'].values.tolist()
                    elif row[1] == "Voltage":
                        df_V = pd.DataFrame(c.fetchall(),columns=['time','value','sens_id'])
                        voltage = df_V['value'].values.tolist()
                
                # print(voltage, current)
                # if (len(current) and len(voltage)) > 0:
                # print(voltage, current)
                ax.scatter(voltage, current)
                ax.legend()
                # # plt.show()
                # plt.tight_layout()
                st.pyplot(fig)
                # time.sleep(0.2)
                    # plt.close()

def main():
    connection = get_database_connection("database/2022_Desy_debug2.db")
    data = page_config(connection)
    sens_chos, meas_time, sens_title_l, sens_type = sensor_selection(connection, data)
    corr_sens, type_sens = sens_correct(connection, sens_chos, sens_title_l)
    # IV_scan(connection, corr_sens, type_sens, meas_time, sens_type)
    graphical_mon(connection, corr_sens, type_sens, meas_time, sens_chos)

    # if "Voltage/Current" in sens_chos:
    #     IV_scan(connection, corr_sens, type_sens, meas_time)
   

    #matplotlib shut up!
    plt.rcParams.update({'figure.max_open_warning': 0})

if __name__ == "__main__":
    main()
