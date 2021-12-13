import numpy as np
import sqlite3
import pandas as pd
import serial
import datetime
import time



def take_data_single():
    conn = sqlite3.connect('C:\\Users\\schum\\github\\cooling_setup\\sens\\database\\first.db')
    c = conn.cursor()
    c.execute(""" CREATE TABLE IF NOT EXISTS measurement (
        time datetime,
        value float,
        sensor_id integer,
        PRIMARY KEY (time),
        FOREIGN KEY (sensor_id) REFERENCES sensors(sens_id)
        )""")
    t_max = int(float(input('Measurement length (in minutes): '))*60)
    t_start = int(datetime.datetime.timestamp(datetime.datetime.now()))
    t_elapsed = 0
    with serial.Serial('COM4', 9600, timeout=1) as ser:
        while (t_elapsed <= (t_start + t_max)):
            line = ser.readlines()
            try:
                temp_data = float(line[2][10:-2])
                hum_data = float(line[3][9:-2])
            except:
                continue
            print(temp_data, hum_data)
            time_data_temp = datetime.datetime.timestamp(datetime.datetime.now())
            c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_temp, 'value':temp_data, 'id':3})
            conn.commit()
            time_data_hum = float(time_data_temp)+0.1
            c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_hum, 'value':hum_data, 'id':4})
            conn.commit()
            t_elapsed = int(datetime.datetime.timestamp(datetime.datetime.now()))
            if (t_start + t_max - t_elapsed < 0):
                print('measurement finished!')
            else:
                print('time until end: '+ str(t_start + t_max - t_elapsed) + ' seconds')
            time.sleep(0.5)
        c.close()

def take_data_double():
    conn = sqlite3.connect('C:\\Users\\schum\\github\\cooling_setup\\sens\\database\\first.db')
    c = conn.cursor()
    c.execute(""" CREATE TABLE IF NOT EXISTS measurement (
        time datetime,
        value float,
        sensor_id integer,
        PRIMARY KEY (time),
        FOREIGN KEY (sensor_id) REFERENCES sensors(sens_id)
        )""")
    t_max = int(float(input('Measurement length (in minutes): '))*60)
    t_start = int(datetime.datetime.timestamp(datetime.datetime.now()))
    t_elapsed = 0
    while (t_elapsed <= (t_start + t_max)):
        with serial.Serial('COM3', 9600, timeout=1) as ser: #copper
            line = ser.readlines()
            if (len(line) != 0):
                try:
                    temp_data = float(line[2][10:-2])
                    hum_data = float(line[3][9:-2])
                except:
                    continue
                print(temp_data, hum_data)
                time_data_temp = datetime.datetime.timestamp(datetime.datetime.now())
                c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_temp, 'value':temp_data, 'id':3})
                conn.commit()
                time_data_hum = float(time_data_temp)+0.1
                c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_hum, 'value':hum_data, 'id':4})
                conn.commit()
            else:
                time.sleep(0.25)
                try:
                    temp_data = float(line[2][10:-2])
                    hum_data = float(line[3][9:-2])
                except:
                    continue
                print(temp_data, hum_data)
                time_data_temp = datetime.datetime.timestamp(datetime.datetime.now())
                c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_temp, 'value':temp_data, 'id':5})
                conn.commit()
                time_data_hum = float(time_data_temp)+0.1
                c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_hum, 'value':hum_data, 'id':6})
                conn.commit()
                t_elapsed = int(datetime.datetime.timestamp(datetime.datetime.now()))
        with serial.Serial('COM4', 9600, timeout=1) as ser: #outside
            line = ser.readlines()
            if (len(line) != 0):
                try:
                    temp_data = float(line[2][10:-2])
                    hum_data = float(line[3][9:-2])
                except:
                    continue
                print(temp_data, hum_data)
                time_data_temp = datetime.datetime.timestamp(datetime.datetime.now())
                c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_temp, 'value':temp_data, 'id':5})
                conn.commit()
                time_data_hum = float(time_data_temp)+0.1
                c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_hum, 'value':hum_data, 'id':6})
                conn.commit()
                t_elapsed = int(datetime.datetime.timestamp(datetime.datetime.now()))
            else:
                time.sleep(0.25)
                try:
                    temp_data = float(line[2][10:-2])
                    hum_data = float(line[3][9:-2])
                except:
                    continue
                print(temp_data, hum_data)
                time_data_temp = datetime.datetime.timestamp(datetime.datetime.now())
                c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_temp, 'value':temp_data, 'id':5})
                conn.commit()
                time_data_hum = float(time_data_temp)+0.1
                c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':time_data_hum, 'value':hum_data, 'id':6})
                conn.commit()
                t_elapsed = int(datetime.datetime.timestamp(datetime.datetime.now()))
        if (t_start + t_max - t_elapsed < 0):
            print('measurement finished!')
        else:
            print('time until end: '+ str(t_start + t_max - t_elapsed) + ' seconds')
        time.sleep(1)
    c.close()

# take_data_single()
take_data_double()
