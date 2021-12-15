import numpy as np
import sqlite3
import pandas as pd
import serial
import datetime
import time
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.ticker import FuncFormatter

conn = sqlite3.connect('C:\\Users\\schum\\github\\cooling_setup\\sens\\database\\first.db')
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

single_run_data, run_date_short = single_run_readout('10:50', '08/12/2021', 30)
quick_graph(single_run_data, run_date_short)
