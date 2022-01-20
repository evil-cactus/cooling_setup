import numpy as np
import pandas as pd
import streamlit as st
import time
import datetime
import math
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3
#small changes to the website itself
st.set_page_config(
    page_title='SinglePTSD4MoMi'
)
#list_of_colors=['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33']
list_of_colors=['#e31a1c','#fdbf6f','#ff7f00','#6a3d9a','#ffff99','#b15928','#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99']
#connect to the database and create table sensors, if not there
conn = sqlite3.connect('./database/first.db')
c = conn.cursor()

c.execute("SELECT * FROM sensors")
lst = c.fetchall()
type_sensor = []
for i in range(len(lst)):
    type_sensor.append(lst[i][3])
type_sensor_ids = []
for type in type_sensor:
    c.execute("SELECT * FROM sensors")
    lst = c.fetchall()
    ids,sub,col = [],[],[]
    ids.append(type)
    for i in range(len(lst)):
        if (lst[i][3] == type):
            sub.append(lst[i][0])
    ids.append(sub)
    type_sensor_ids.append(ids)


#Let's start!
st.title('Python Testbench-SingleSensor Display for Monitoring MightyPix (PTSD4MoMi)')
st.header('...just call it MoMi')
st.subheader('by Henry Schumacher')
st.text('Work in Progress...')

st.subheader('Current database of sensors:')
data = pd.read_sql('SELECT * FROM sensors ORDER BY sens_id ASC', conn)
st.dataframe(data)
#this Button is just to refresh, which it only does implicitely lol
refresh = st.button('refresh')

sel_sens = st.selectbox('Which sensor would you like to see?', type_sensor)

for i in range(0,len(lst)):
    if (sel_sens == lst[i][3]):
        sens_id = lst[i][0]
        sens_type = lst[i][1]

st.subheader('Graphical Monitoring Interface')
st.warning('UTC-timestamp')
graph = st.empty()#create the graph container
if (len(type_sensor) != 0):
    #the monitoring loop
    #doit = st.button('Do it again!')
    if sel_sens:
        ax = plt.figure(figsize=(12,5), dpi=150)
        c.execute('SELECT * FROM measurement WHERE sensor_id=:id ORDER BY time ASC',{'id':sens_id})
        df = pd.DataFrame(c.fetchall(),columns=['time','value','sens_id'])
        df['time'] = pd.to_datetime(df['time'],unit='s')
        px.defaults.color_continuous_scale = px.colors.sequential.Blackbody
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(df.time), y=list(df.value), hoveron='points+fills', name=sel_sens))
        fig.update_layout(xaxis=dict(rangeslider=dict(visible=True),type="date"))
        graph.plotly_chart(fig)
