from cmath import inf
from doctest import ELLIPSIS_MARKER
from optparse import Values
from traceback import print_tb
import numpy as np
import pandas as pd
import streamlit as st
import time
from datetime import datetime
import math
import serial
import os
import platform
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3
import pyvisa
import re
from hmp4040 import hmp4040
from psu import psu_voltage_driver
import serial.tools.list_ports


### usefull methods ###

def find_ports():
    all_ports = ""
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
            #print("{}: {} [{}]".format(port, desc, hwid))
            ports_line = "{}: {} [{}] \n".format(port, desc, hwid)
            all_ports += ports_line
    return(all_ports)
   

def compile_and_upload():
    pass
    # arduino-cli compile -b arduino:megaavr:nona4809 -p /dev/ttyACM0 i2c_sht31.ino
    # arduino-cli upload -b arduino:megaavr:nona4809 -p /dev/ttyACM0 i2c_sht31.ino


## initialize data frame
def df_initialization(sensor_id):
    row, col = [], []
    port_id_l = []
    index_id_l = []
    # print(sensor_id,port_d)

    for i,key in enumerate(port_d):
        for j in range(len(sensor_id)):
            if port_d[key][0] == sensor_id[j][0]:
                row.append([sensor_id[j][0],sensor_id[j][1],sensor_id[j][2],0])
                # index_id_l.append(sensor_id[j][-1])
                # port_id_l.append(sensor_id[j][0])
                #print(row, col)

    df = pd.DataFrame(row, columns = ["Port","Channel", "Index", "Value"])
    return(df)


def df_to_table_to_gui(value):
    table = st.empty()
    with st.empty():
        for j in range(len(sensor_id)):
            if sensor_id[j][0] == port_d[key][0] and sensor_id[j][1] in list(value.keys()):
                for i in range(2):
                    time_now=datetime.now()
                    time_data = datetime.timestamp(time_now)
                    # print("time", datetime.timestamp(time_data))
                    print("check values",(sensor_id[j][0],sensor_id[j][1],i), value[sensor_id[j][1]][i])
                    i_sensor_id=sensor_id.index((sensor_id[j][0],sensor_id[j][1],i))
                    df.loc[(df["Index"] == i) & (df["Channel"] == sensor_id[j][1]) & (df["Port"] == sensor_id[j][0]),"Value" ] =  value[sensor_id[j][1]][i]
                    table.dataframe(df)
                    c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data, 'value': value[sensor_id[j][1]][i], 'id':i_sensor_id})
                conn.commit()
    time.sleep(0.75)
    table.empty()

def hameg_values(dev_id, device):
    for slot_i in range(1,5):
            # print(slot_i)
            device.write(f'INST OUT{slot_i}')
            device.write(f'OUTP:SEL{slot_i}')
            device.write(f'OUTP {slot_i}')    
            value_V = float(device.query('MEAS:VOLT?'))
            value_I = float(device.query('MEAS:CURR?'))
            value_HAMEG[slot_i] = (value_V,value_I)
    return(value_HAMEG)

def Korad_values(dev_id,device):
    device.reset_output_buffer()
    device.reset_input_buffer()
    # ser.write("VSET:6.4\n".encode()) #implement the psu.py functionality
    device.write('VOUT?\n'.encode())
    output = device.read_until('\n')
    output = output.decode("utf-8")
    if (output[0] == '0'):
        value_V = float(output[1:5])
    else:
        value_V = float(output[0:5])
    device.write('IOUT?\n'.encode())
    output = device.read_until('\n')
    output = output.decode("utf-8")
    if (output[0] == '0'):
        value_I = float(output[1:5])
    else:
        value_I = float(output[0:5])
        
    value_Korad[1] = (value_V, value_I)
    return(value_Korad)


def Arduino_values(line, slot_nr_old):
    info_all = re.findall('\d*\.?\d+', line)
    slot_nr = int(info_all[-4])
    if slot_nr!= slot_nr_old:
        value_T = info_all[-2]
        value_H = info_all[-1]
        value_Arduino[slot_nr]=(float(value_T),float(value_H))
        slot_nr_old = slot_nr
        slot_A.append(slot_nr)
        # #only to check T & H
        # match_T = re.search('Temperature/°C:\s*\d*\.?\d*', line)
        # match_H = re.search('Humidity:\s*\d*\.?\d*', line)
    return(value_Arduino)


### platform settings
pltf = platform.system()
if (pltf == 'Linux'):
    #db_path = 'database/2022.db'
    db_path = 'database/2022_1.db'
    #TODO dynamically
    # port_KWR103 = '/dev/ttyACM0'
    port_COM3_equiv = '/dev/ttyACM2'
    port_COM4_equiv = '/dev/ttyACM1'
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
# c.execute('DROP TABLE IF EXISTS sensors')
conn.commit()
c.execute(""" CREATE TABLE IF NOT EXISTS sensors (
    sens_id integer UNIQUE,
    sens_type text,
    sens_unit text,
    sens_des text
    )""")

st.title('Input-GUI for MoMi')
st.subheader('by Henry Schumacher')
st.text('Work in Progress...')

st.sidebar.subheader('Current database of sensors:')#st.subheader('Current database of sensors:')
data = pd.read_sql('SELECT * FROM sensors ORDER BY sens_id ASC', conn) ##database is read into dataframe
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
    connections = [port_COM3_equiv,port_COM4_equiv ]
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


timmin_psu_103 = 0
with st.expander(label='PSU automation'):
    psu_auto_butt = st.checkbox('Check for automation.')
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
if (psu_auto_butt == True):
    step = -1
    voltages_103,timmin_psu_103 = psu_voltage_driver(low_103,high_103,steps_103)
    voltages_4040,timmin_psu_4040 = psu_voltage_driver(low_4040,high_4040,steps_4040)
    duration = timmin_psu_103


start = st.button('start')
## MEASUREMENTS ##
if (start == True):
    dp,dp_old = 0,0
    if duration<0:
        t_max=-1
    else:
        t_max = int(duration*60)
    t_max_f = float(t_max)
    t_start = int(datetime.timestamp(datetime.now()))
    t_start_f = float(datetime.timestamp(datetime.now()))
    t_elapsed = 0
    t_since_last_step = 0
    t_last_step = t_start_f
    
    values = {}
    sensor_id=[]
    power_l = []
    serial_open = {}
    slot_A = []

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(""" CREATE TABLE IF NOT EXISTS measurement (
        time datetime,
        value float,
        sensor_id integer,
        FOREIGN KEY (sensor_id) REFERENCES sensors(sens_id)
        )""")
        # PRIMARY KEY (time),

    ##open USB without explicit naming
    port_d = {}
    devices = ["Arduino", "KORAD", "HAMEG"]
    try:
        found_ports = find_ports()
        for i in range(len(devices)):
            for l in found_ports.splitlines():
                if devices[i] in l:
                    dev_id_l = re.findall('/[a-zA-Z]+/[a-zA-Z]+\d', l)
                    dev_id = dev_id_l[0]
                    if devices[i] == "HAMEG":
                        port_d[devices[i]] = [dev_id,i, "visa"]
                    else:
                        port_d[devices[i]] = [dev_id,i, "serial"]
    except:
        print("No USB connections found")
    
    ## get unique sensor/device id
    counter = 0
    for i,key in enumerate(port_d):
        list_values = port_d[key]
        if "visa" in list_values and key == "HAMEG":
            print("Visa communication starts")
            dev_id = port_d.get(key)[0] 
            rm = pyvisa.ResourceManager()
            # print("All found resources", rm.list_resources())
            if(platform.system() == 'Linux'):
                hmp4040_ps = rm.open_resource("ASRL"+dev_id+"::INSTR")
            else:
                ## TODO: check this
                hmp4040_ps = rm.open_resource('ASRL5::INSTR')
            for i in range(1,5):
                hmp4040_ps.write(f'INST OUT{i}')
                hmp4040_ps.write(f'OUTP:SEL{i}i')
                hmp4040_ps.write(f'OUTP {i}')
                sensor_id.append((dev_id, i, 0))
                sensor_id.append((dev_id, i, 1))   
            rm.close()

        elif "serial" in list_values and key == "Arduino":
            print("Arduino communication starts")
            dev_id = port_d.get(key)[0] 
            ser = serial.Serial(dev_id, 9600, timeout=0.5)
            serial_open[dev_id] = ser
            debug_setup = ""
            while(True):
                line = ser.read_until('\r\n'.encode()).decode("utf-8")
                # print(line)
                debug_setup += line
                try:
                    info_addr = re.findall('\d[a-zA-Z]\d+', line)
                    info_all = re.findall('Port #\d*\.?\d+', line)
                    if info_addr[0] in line and info_all[0] in line and "Found SHT31 Temperature and Humidity Sensor!!" not in line: 
                        slot_nr = int(info_all[0].split('#')[-1])
                        # print(line)

                        if (dev_id,slot_nr,0) in sensor_id:
                            break

                        sensor_id.append((dev_id,slot_nr,0))
                        sensor_id.append((dev_id,slot_nr,1))

                except:
                    continue                
                            
        elif "serial" in list_values and key == "KORAD":
            print("Korad communication starts")
            dev_id = port_d.get(key)[0]
            ser_K = serial.Serial(dev_id, 115200, timeout=2.0)
            serial_open[dev_id] = ser_K 
            # with serial.Serial(dev_id, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=2.0) as ser_K:
            with ser_K as ser_K_o:
                sensor_id.append((dev_id,1, 0))
                sensor_id.append((dev_id,1, 1))
        else:
            print("No ports available")

    ## get sensor info
    for j,sens_i in enumerate(sensor_id):
        c = conn.cursor()
        i_sensor_id=sensor_id.index((sensor_id[j][0],sensor_id[j][1], sensor_id[j][-1]))
        # print("sensid", i_sensor_id, (sensor_id[j][0],sensor_id[j][1], sensor_id[j][-1]))
        for i,key in enumerate(port_d.keys()):
            if sensor_id[j][0] == port_d.get(key)[0]:
                sensor_des = f"{key}_{sensor_id[j][1]}"
                if key == "HAMEG" or key == "KORAD":
                    if sensor_id[j][-1] == 0:
                        sensor_type = "Voltage"
                        sensor_unit = "V"
                    else:
                        sensor_type = "Current"
                        sensor_unit = "A"
                elif key == "Arduino":
                    if sensor_id[j][-1] == 0:
                        sensor_type ="Temperature"
                        sensor_unit = "°C"
                    else:
                        sensor_type ="Humidity"
                        sensor_unit = "%"
        c.execute("INSERT or IGNORE INTO sensors VALUES (:id, :type, :unit, :desc)", {'id':i_sensor_id, 'type':sensor_type, 'unit':sensor_unit, 'desc':sensor_des})
        conn.commit() 
    
    ## get values
    break_counter = 0
    slot_nr_old = 0
    value_Arduino, value_HAMEG, value_Korad = {}, {}, {}

    df = df_initialization(sensor_id)
    # print(df)  
    while (t_max <0 or t_elapsed < (t_start + t_max)):
        for i,key in enumerate(port_d):
            for sens_i in sensor_id:   
                if list(port_d.keys())[i]  == "HAMEG" and port_d[key][0] in sens_i:
                    # print(list(port_d.keys())[i], port_d[key][0],sensor_id[0][0], dev_id )
                    dev_id = port_d.get(key)[0] 
                    rm = pyvisa.ResourceManager()
                    if(platform.system() == 'Linux'):
                        device = rm.open_resource("ASRL"+dev_id+"::INSTR")
                    else:
                        ## TODO: check this
                        device = rm.open_resource('ASRL5::INSTR')

                    value_HAMEG = hameg_values(dev_id, device)
                    df_to_table_to_gui(value_HAMEG)
                    rm.close()

                ## Arduino
                elif list(port_d.keys())[i]  == "Arduino" and port_d[key][0] in sens_i:
                    dev_id = port_d.get(key)[0] 
                    ser = serial_open[dev_id]
                    line = ser.read_until('\r\n'.encode()).decode("utf-8")
                    if "slot" in line:
                    # ser = serial.Serial(dev_id, 9600, timeout=0.5)
                    # time.sleep(0.5)
                        value_Arduino = Arduino_values(line, slot_nr_old)
                        df_to_table_to_gui(value_Arduino)
                    else:
                        continue
                    t_since_last_step = round(float(datetime.timestamp(datetime.now())) - t_last_step,2)

                # ## KORAD
                elif list(port_d.keys())[i]  == "KORAD" and port_d[key][0] in sens_i:
                    dev_id = port_d.get(key)[0] 
                    ser_K = serial_open[dev_id]
                    # print(ser_K.isOpen())
                    if ser_K.isOpen() == False:
                        ser_K.open()
                    value_Korad = Korad_values(dev_id, ser_K)
                    df_to_table_to_gui(value_Korad)

    # # if ((psu_auto_butt == True and t_since_last_step >= 300) or (psu_auto_butt == True and step == -1)):
    # if (psu_auto_butt == True):
    #     rm = pyvisa.ResourceManager()
    #     print("All found resources", rm.list_resources())
    #     if(platform.system() == 'Linux'):
    #         hmp4040_ps = rm.open_resource("ASRL"+hameg_id+"::INSTR")
    #     else:
    #         ## TODO: check this
    #         hmp4040_ps = rm.open_resource('ASRL5::INSTR')

    #     hmp4040_ps.write('INST OUT1')
    #     set_string = 'VOLT ' + str(voltages_4040[step])
    #     hmp4040_ps.write(set_string)
    #     hmp4040_ps.write('CURR 10')
    #     hmp4040_ps.write('OUTP:SEL1')
    #     hmp4040_ps.write('OUTP 1')
    #     V_out_4040 = float(hmp4040_ps.query('MEAS:VOLT?'))
    #     value_V = V_out_4040
    #     I_out_4040 = float(hmp4040_ps.query('MEAS:CURR?'))
    #     value_I = I_out_4040
    #     value_UI = (hameg_id, value_V, value_I)
    #     print("check", value_I, value_V)
    #     rm.close()
    
    # #     ### KW103 ###
    # #     # if(platform.system() == 'Windows'):
    # #         # port_KWR103 = 'COM6'
    #     with serial.Serial(korad_id, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=2.0) as ser:
    #         ser.reset_output_buffer()
    #         ser.reset_input_buffer()
    #         set_string = 'VSET:'+str(voltages_103[step])+'\n'
    #         ser.write(set_string.encode())
    #         ser.write('ISET:12\n'.encode())
    #         ser.write('VOUT?\n'.encode())
    #         output = ser.read_until('\n')
    #         output = output.decode("utf-8")
    #         if (output[0] == '0'):
    #             value_K_V = round(float(output[1:5]),2)
    #         else:
    #             value_K_V = round(float(output[0:5]),2)
    #         ser.write('IOUT?\n'.encode())
    #         output = ser.read_until('\n')
    #         output = output.decode("utf-8")
    #         if (output[0] == '0'):
    #             value_K_I = round(float(output[1:5]),2)
    #         else:
    #             value_K_I = round(float(output[0:5]),2)
    #         value_K_VI = (korad_id,value_K_V, value_K_I)

    
    conn.close()
