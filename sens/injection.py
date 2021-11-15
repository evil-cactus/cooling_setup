import sqlite3
import datetime
import time
import pandas as pd
import numpy as np

conn = sqlite3.connect('test.db')
c = conn.cursor()
c.execute(""" CREATE TABLE IF NOT EXISTS measurement (
    time datetime,
    value float,
    sensor_id integer,
    PRIMARY KEY (time),
    FOREIGN KEY (sensor_id) REFERENCES sensors(sens_id)
    )""")

#sensors = pd.read_sql('SELECT * FROM sensors ORDER BY sens_id ASC', conn)
now = datetime.datetime.now().timestamp()

for i in range(0,250):
    data_time = datetime.datetime.now().timestamp()
    data_value = round(np.random.random(),3)
    data_id = np.random.randint(low=1, high=11)
    #print(data_time, data_value, data_id)
    c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {'time':data_time, 'value':data_value, 'id':data_id})
    conn.commit()
    time.sleep(data_value)

test = pd.read_sql('SELECT * FROM measurement ORDER BY time ASC', conn)
print(test)
c.close()
