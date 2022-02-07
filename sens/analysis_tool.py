import numpy as np
import sqlite3
import pandas as pd
import serial
import datetime
import time
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.ticker import FuncFormatter

conn = sqlite3.connect('C:\\Users\\schum\\Documents\\github\\cooling_setup\\sens\\database\\2022.db')
c = conn.cursor()



def single_run_readout(start_time, start_date, duration):
    #start_time = input('Time of measurement start in UTC [xx:xx]:')
    hour = str(start_time[0:2])
    minute = str(start_time[3:5])
    # print(hour, minute)
    #start_date = input('Date of measurement start [dd/mm/yyyy]:')
    day = str(start_date[0:2])
    month = str(start_date[3:5])
    year = str(start_date[6:10])
    # print(day,month,year)
    #duration = int(input('How long did the run last [in minutes]:'))
    run_date = str(year) + '-' + str(month) + '-' + str(day) + ' ' + str(hour) + ':' + str(minute)
    run_date_short = str(year) + '-' + str(month) + '-' + str(day)
    # print(run_date)
    run_date_ts = datetime.datetime.timestamp(datetime.datetime.strptime(run_date, '%Y-%m-%d %H:%M')) + 3600
    c.execute("SELECT * FROM measurement ORDER BY time ASC")
    df = pd.DataFrame(c.fetchall(),columns=['time','value','sens_id'])
    df['date'] = pd.to_datetime(df['time'], unit='s')
    # df.to_excel('C:\\Users\\schum\\github\\cooling_setup\\sens\\test.xlsx')
    # print(run_date_ts)
    single_run_data = []
    for i in range(len(df)):
        if (run_date_ts <= df.at[i, 'time'] <= run_date_ts+duration*60):
            single_run_data.append([df.at[i, 'value'], df.at[i, 'date'] ,df.at[i, 'sens_id']])
            # print(df.at[i, 'value'], df.at[i, 'sens_id'])
    # print(df)
    print('run data has been loaded')
    return single_run_data, run_date_short

# fig, ax = plt.subplots(nrows=len(sens_set),ncols=1, figsize=(8,8), sharex=True)

def logistic(a,b,x):
    return a/(b + np.exp(-x))

def quick_graph(data, date):
    values,times,sensor = [],[],[]
    for i in range(len(data)):
        values.append(data[i][0])
        times.append(data[i][1])
        sensor.append(data[i][2])
    sens_set = set(sensor)
    t0 = datetime.datetime.fromtimestamp(datetime.datetime.timestamp(times[0]) - 60)
    t1 = datetime.datetime.fromtimestamp(datetime.datetime.timestamp(times[-1]) + 60)
    a = int((datetime.datetime.timestamp(times[-1])-datetime.datetime.timestamp(times[0]))/(300))
    b = 6
    print(a,b)
    fig, ax = plt.subplots(nrows=1,ncols=1, figsize=(a,b), sharex=True)
    ax.scatter(times, values, c=sensor)
    ax.grid(True, which='both', linestyle='--', lw=0.5)
    ax.xaxis.set_minor_locator(dates.MinuteLocator(interval=2))
    ax.xaxis.set_minor_formatter(dates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(dates.HourLocator(interval=10))
    ax.xaxis.set_major_formatter(dates.DateFormatter('\n\n%H:%M'))
    ax.set_xlim(t0, t1)
    # ax.tick_params(axis='y', labelcolor=color)
    # ax2 = ax.twinx()
    ax.set_xlabel('Time (UTC) on ' + str(date))
    ax.set_ylabel('Temperature in °C / Humidity in %')
    for label in ax.get_xticklabels(which='minor'):
       label.set(rotation=90, horizontalalignment='right', fontsize=8)
    for label in ax.get_xticklabels(which='major'):
       label.set(rotation=90, horizontalalignment='right', fontsize=0)
    # ax.legend(loc='best')
    plt.savefig('.\\figs\\test.jpg')
    plt.show()

# single_run_data, run_date_short = single_run_readout('10:50', '08/12/2021', 30)
# quick_graph(single_run_data, run_date_short)


def analysis_get_data():
    print('PROGRESS: Getting data... ')
    for id in range(1,13):
        c.execute("SELECT * FROM measurement WHERE sensor_id=:id ORDER BY time ASC",{'id':id})
        df = pd.DataFrame(c.fetchall(),columns=['time','value','sens_id'])
        df['date'] = pd.to_datetime(df['time'], unit='s')
        df.to_excel('.\\figs\\data_sensor_' + str(id) + '.xlsx')
        print('STATUS: Measurement data for sensor ' + str(id) + ' is extracted. ' + str(round((id/13)*100,2)) + '% done')

def full_single_sensor_plotting(sensor, SHT_YN, PSU_KW):
    print('PROGRESS: Accessing data... ')
    if (SHT_YN == True):
        df_t = pd.read_excel('.\\figs\\data_sensor_' + str(sensor) + '.xlsx', header=0)
        df_h = pd.read_excel('.\\figs\\data_sensor_' + str(sensor+1) + '.xlsx', header=0)
    if(PSU_KW == 'K'):
        df_v = pd.read_excel('.\\figs\\data_sensor_' + str(9) + '.xlsx', header=0)
        df_c = pd.read_excel('.\\figs\\data_sensor_' + str(10) + '.xlsx', header=0)
    elif(PSU_KW == 'H'):
        df_v = pd.read_excel('.\\figs\\data_sensor_' + str(11) + '.xlsx', header=0)
        df_c = pd.read_excel('.\\figs\\data_sensor_' + str(12) + '.xlsx', header=0)
    print('PROGRESS: Checking data for run markers... ')
    runs_t_start,runs_t_stop,runs_h,runs_v,runs_c = [],[],[],[],[]
    for i in range(1,len(df_t)):
        if (i != len(df_t)-1):
            if ((int(df_t.at[i,'time']) - int(df_t.at[i-1,'time']) < 60) and (int(df_t.at[i+1,'time']) - int(df_t.at[i,'time']) < 60) ):
                runs_t_start.append(i-1)
            elif ((int(df_t.at[i,'time']) - int(df_t.at[i-1,'time']) < 60) and (int(df_t.at[i+1,'time']) - int(df_t.at[i,'time']) > 60) ):
                runs_t_stop.append(i)
        else:
            runs_t_stop.append(i)
    print('PROGRESS: Checking data for run markers... 25% done')
    for i in range(1,len(df_h)):
        if (df_h.at[i,'time'] - df_h.at[i-1,'time'] > 60):
            runs_h.append(i-1)
    print('PROGRESS: Checking data for run markers... 50% done')
    for i in range(1,len(df_v)):
        if (df_v.at[i,'time'] - df_v.at[i-1,'time'] > 60):
            runs_v.append(i-1)
    print('PROGRESS: Checking data for run markers... 75% done')
    for i in range(1,len(df_c)):
        if (df_c.at[i,'time'] - df_c.at[i-1,'time'] > 60):
            runs_c.append(i-1)
    print('PROGRESS: Checking data for run markers... 100% done')
    print(runs_t_start)
    for i in range(len(runs_t_stop)):
        DF_T = df_t.values.tolist()
        temp_val, temp_time = [],[]
        for j in range(runs_t_start[i],runs_t_stop[i]):
            temp_val.append(DF_T[j][2])
            temp_time.append(DF_T[j][4])
    # for i in range(len(runs_t)):
    #     # t_run_end = runs_t[i]
    #     h_run_end = runs_h[i]
    #     v_run_end = runs_v[i]
    #     c_run_end = runs_c[i]
    #     if (i == 0):
    #         t_run_start, h_run_start, v_run_start, c_run_start = 0,0,0,0
    #     else:
    #         # t_run_start = runs_t[i-1]
    #         h_run_start = runs_h[i-1]
    #         v_run_start = runs_v[i-1]
    #         c_run_start = runs_c[i-1]
    #     temp_time_t = []
    #     temp_val_t = []
    #     temp_time_h = []
    #     temp_val_h = []
    #     temp_time_v = []
    #     temp_val_v = []
    #     temp_time_c = []
    #     temp_val_c = []
    #     for j in range(t_run_start,t_run_end):
    #         temp_time_t.append(df_t.at[j,'date'])
    #         temp_val_t.append(df_t.at[j,'value'])
    #     for j in range(h_run_start,h_run_end):
    #         temp_time_h.append(df_h.at[j,'date'])
    #         temp_val_h.append(df_h.at[j,'value'])
    #     for j in range(v_run_start,v_run_end):
    #         temp_time_v.append(df_v.at[j,'date'])
    #         temp_val_v.append(df_v.at[j,'value'])
    #     for j in range(c_run_start,c_run_end):
    #         temp_time_c.append(df_c.at[j,'date'])
    #         temp_val_c.append(df_c.at[j,'value'])

        fig, ax = plt.subplots(nrows=2,ncols=1, figsize=(12,4), sharex=True)
        ax[0].scatter(temp_time,temp_val,lw=0.8,color='blue')
        # ax[0,1].scatter(temp_time_h,temp_val_h,lw=0.8,ls=':',color='deepskyblue')
        # ax[1,0].scatter(temp_time_v,temp_val_v,lw=0.8,ls=':',color='firebrick')
        # ax[1,1].scatter(temp_time_c,temp_val_c,lw=0.8,ls=':',color='orangered')
        ax[0].grid(which='both')
        ax[1].grid(which='both')
        ax[0].xaxis.set_minor_locator(dates.MinuteLocator(interval=4))
        ax[1].xaxis.set_minor_formatter(dates.DateFormatter('%H:%M'))
        # ax.xaxis.set_major_locator(dates.HourLocator(interval=10))
        # ax.xaxis.set_major_formatter(dates.DateFormatter('\n\n%H:%M'))
        plt.show()


def Two_D_plotting(sensor_a, sensor_b):
    df_a = pd.read_excel('.\\figs\\data_sensor_' + str(sensor_a) + '.xlsx', header=0)
    df_b = pd.read_excel('.\\figs\\data_sensor_' + str(sensor_b) + '.xlsx', header=0)


# analysis_get_data()
full_single_sensor_plotting(1,True,'H')
