#!/usr/bin/python

from streamlit.scriptrunner import add_script_run_ctx
import streamlit as st
import time
import sqlite3
import re
from queue import Queue
from threading import Thread, Event
import threading
import serial.tools.list_ports
import logging
import pyvisa
import platform
from keithley2400 import Keithley2400
from datetime import datetime, timedelta
import pandas as pd
import numpy as np



logging.basicConfig(
    level=logging.DEBUG,
    format="(%(threadName)-9s) %(levelname)s-  %(message)s",
)
inserter = None


def storeInQueue(f):
    def wrapper(*args):
        result_queue.put(f(*args))

    return wrapper


def main():
    inserter = get_class()
    inserter.run()



@st.experimental_singleton
def get_class():
    inserter = Data_Inserter()
    print("All in all were just..")
    inserter.init()
    inserter.setup()
    return inserter


## initialize data frame
@st.cache(allow_output_mutation=True)
def df_initialization(port_d, sensor_id,saved_sensors):
    row = []
    for i, key in enumerate(port_d):
        for j in range(len(sensor_id)):
            if port_d[key][0] == sensor_id[j][0]:
                row.append([sensor_id[j][0], sensor_id[j][1], sensor_id[j][2], 0.0,str(saved_sensors["sens_type"].values[j]),key ])
    df = pd.DataFrame(row, columns=["Port", "Channel", "Index", "Value", "Prob. Type", "Device"])
    return df

def table_update(inserter):
    return(df_initialization(inserter.port_d, inserter.sensor_id, inserter.current_saved_sensors))

class Data_Inserter:
    ## scan all ports and save the ones found
    def find_ports(self):
        all_ports = ""
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            # print("{}: {} [{}]".format(port, desc, hwid))
            ports_line = "{}: {} [{}] \n".format(port, desc, hwid)
            all_ports += ports_line
        print(f"Find Ports Done {all_ports}")
        return all_ports

    # @st.cache(hash_funcs={sqlite3.Connection: lambda _: None, serial.serialposix.Serial: lambda _: None})
    def get_database_connection(self, db_path):
        conn = sqlite3.connect(db_path, check_same_thread=False)
        # c = self.conn.cursor()
        return conn

    def get_data_keythley(self, device):
        value = {}
        for slot_i in range(1, 5):
            try:
                value_V = keithley.query("MEAS:VOLT?").split(",")[0]
                value_I = keithley.query("MEAS:CURR?").split(",")[1]
            except:
                value_V = None
                value_I = None
            value[slot_i] = (value_V, value_I)
        return value

    def keythley(self, q, connection, port_d, sensor_id):
        while not self.stop_event.is_set():
            if self.stop_event.is_set():
                break
            for i, key in enumerate(port_d):
                for sens_i in sensor_id:
                    if list(port_d.keys())[i] == "KEYTHLEY" and port_d[key][0] in sens_i:
                        dev_id_H = port_d.get(key)[0]
                        device_H = self.serial_open[dev_id_H]
                        value = self.get_data_keythley(device_H)
                        self.order_data((dev_id_H, value), self.current_table)
                        self.insert_into_db(connection, value, sens_i, port_d.get(key))


    def get_data_hameg(self, device):
        value_HAMEG = {}
        for slot_i in range(1, 5):
            try:
                device.write(f'INST OUT{slot_i}')
                value_V = float(device.query("MEAS:VOLT?"))
                value_I = float(device.query("MEAS:CURR?"))
            except:
                # print("HAMEG ",e)
                value_V = None
                value_I = None
            value_HAMEG[slot_i] = (value_V, value_I)
        return value_HAMEG


    def hameg(self, q, connection, port_d, sensor_id):
        while not self.stop_event.is_set():
            if self.stop_event.is_set():
                break
            for i, key in enumerate(port_d):
                for sens_i in sensor_id:
                    if list(port_d.keys())[i] == "HAMEG" and port_d[key][0] in sens_i:
                        dev_id_H = port_d.get(key)[0]
                        device_H = self.serial_open[dev_id_H]
                        # with self._lock:
                        value_HAMEG = self.get_data_hameg(device_H)
                        # rm.close()
                        # "Port", "Channel", "Index", "Value"
                        # q.put((dev_id_H, value_HAMEG))
                        self.order_data((dev_id_H, value_HAMEG), self.current_table)
                        self.insert_into_db(connection, value_HAMEG, sens_i, port_d.get(key))
                        # if q.qsize()>4:
                        #     q.task_done()

    ## get values from korad
    def korad_values(self, device):
        value_Korad = {}
        device.reset_output_buffer()
        device.reset_input_buffer()
        # ser.write("VSET:6.4\n".encode()) #implement the psu.py functionality
        device.write("VOUT?\n".encode())
        output = device.read_until("\n")
        output = output.decode("utf-8")
        if output[0] == "0":
            value_V = float(output[1:5])
        else:
            value_V = float(output[0:5])
        device.write("IOUT?\n".encode())
        output = device.read_until("\n")
        output = output.decode("utf-8")
        if output[0] == "0":
            value_I = float(output[1:5])
        else:
            value_I = float(output[0:5])

        value_Korad[1] = (value_V, value_I)
        return value_Korad

    # @storeInQueue
    def korad(self, q, connection, port_d, sensor_id, serial_open):
        while not self.stop_event.is_set():
            if self.stop_event.is_set():
                break
            for i, key in enumerate(port_d):
                for sens_i in sensor_id:
                    # ## KORAD
                    if list(port_d.keys())[i] == "KORAD" and port_d[key][0] in sens_i:
                        dev_id_K = port_d.get(key)[0]
                        ser_K = serial_open[dev_id_K]
                        if ser_K.isOpen() == False:
                            ser_K.open()
                        dev_id_K = port_d.get(key)[0]
                        ser_K.write("VOUT?\n".encode())
                        output = ser_K.read_until("\n")
                        output = output.decode("utf-8")
                        value_Korad = self.korad_values(ser_K)
                        # q.put((dev_id_K, value_Korad))
                        self.order_data((dev_id_K, value_Korad), self.current_table)
                        self.insert_into_db(connection, value_Korad, sens_i, port_d.get(key))
                        # if q.qsize()>4:
                        #     q.task_done()

    ## get values from arduino
    def arduino_values(self, device, slot_nr_old):
        value_Arduino = {}
        count = 0
        while True:
            try:
                line = device.read_until("\r\n".encode()).decode("utf-8")
            except UnicodeDecodeError as e:
                logging.error(str(e))
                line=""
            if "1 " == line[0:2] or count > 10:
                break
            count += 1
        info_all = re.findall("-?\d*\.?\d+", line)
        if len(info_all) >= 4:
            slot_nr = int(info_all[1])
            if slot_nr != slot_nr_old:
                value_T = info_all[2]
                value_H = info_all[3]
                value_Arduino[slot_nr] = (float(value_T), float(value_H))
                slot_nr_old = slot_nr
        # print(f"Current arduino values: {value_Arduino}")
        return value_Arduino

    # @storeInQueue
    def arduino(self, q, connection, port_d, sensor_id, serial_open):
        slot_nr_old = 0
        while not self.stop_event.is_set():
            # while (t_test <0 or t_elapsed < (t_start + t_max)):
            t_elapsed = float(datetime.timestamp(datetime.now()))
            if self.stop_event.is_set():
                break
            for i, key in enumerate(port_d):
                for sens_i in sensor_id:
                    ## Arduino
                    if list(port_d.keys())[i] == "Arduino" and port_d[key][0] in sens_i:
                        dev_id_A = port_d.get(key)[0]
                        ser = serial_open[dev_id_A]
                        value_arduino = self.arduino_values(ser, slot_nr_old)
                        info = (dev_id_A, value_arduino)
                        # q.put((dev_id_A, value_arduino))
                        self.order_data((dev_id_A, value_arduino), self.current_table)
                        self.insert_into_db(connection, value_arduino, sens_i, port_d.get(key))
                        # if q.qsize()>4:
                        #     q.task_done()

    def switch_off(self,dev,channel=1):
        if type(channel==int):
            dev_id = self.port_d.get(dev)[0]
        else:
            dev_id=channel[0]
            channel=channel[1]

        with self._lock:
            ser = self.serial_open[dev_id]
            if dev=="KORAD":
                ser.write("OUT:0\n".encode())
            elif dev=="HAMEG":
                ser.write(f'INST OUT{channel}')
                ser.write(f'OUTP:SEL OFF')
    
    
    def set_voltage_keithley(self, voltage, switch_on=False):
        dev_id_K = self.port_d["KEITHLEY"][0]
        with self._lock:
            ser = self.serial_open[dev_id_K]
            if ser.isOpen() == False:
                ser.open()
            ser.write(f':SOUR:VOLT:LEV {voltage}')
    
    def set_voltage_103(self, voltage, switch_on=False):
        dev_id_K = self.port_d["KORAD"][0]
        with self._lock:
            ser = self.serial_open[dev_id_K]
            if ser.isOpen() == False:
                ser.open()
            ser.write(f"VSET:{voltage}\n".encode())
            # ser.write("OUT:1\n".encode())
            if switch_on:
                ser.write("OUT:1\n".encode())

    def set_voltage_4040(self, voltage, channel, switch_on=False):
        if type(channel==int):
            dev_id = self.port_d.get("HAMEG")[0]
        else:
            dev_id=channel[0]
            channel=channel[1]
        device = self.serial_open[dev_id]
        with self._lock:
            device.write(f'INST OUT{channel}')
            device.write(f'VOLT {voltage}')
            if switch_on:
                device.write(f'OUTP:SEL 1')
                

    def scan_thread(self):
        delta_steptime_103 = timedelta(minutes=self.steptime_103)

        voltages_103 = None
        if self.steps_103 > 0:
            voltages_103 = np.array(np.linspace(float(self.low_103), float(self.high_103), int(self.steps_103)))
        voltages_4040 = {}
        current_step_4040 = {}
        time_last_step_4040 = {}
        delta_steptime_4040 = {}
        max_time=[]
        if voltages_103 is not None:
            max_time.append(len(voltages_103)*delta_steptime_103)
        for i_channel in self.low_4040:
            voltages_4040[i_channel] = np.array(np.linspace(float(self.low_4040[i_channel]), float(self.high_4040[i_channel]), int(self.steps_4040[i_channel])))
            current_step_4040[i_channel] = 0
            time_last_step_4040[i_channel] = datetime.now()
            delta_steptime_4040[i_channel] = timedelta(minutes=self.steptime_4040[i_channel])
            max_time.append(len(voltages_4040[i_channel])*delta_steptime_4040[i_channel])

        total_time=max(max_time)

        time_start = datetime.now()
        time_last_step_103 = datetime.now()

        current_step_103 = 0
        self.fraction_done=0.

        while True:
            now = datetime.now()
            not_finished = []
            if voltages_103 is not None:
                if now - time_last_step_103 > delta_steptime_103:
                    current_step_103 += 1
                    time_last_step_103 = now
                    if len(voltages_103) > current_step_103:
                        self.set_voltage_103(voltages_103[current_step_103],switch_on=True)
                        not_finished.append(1)
                else:
                    not_finished.append(1)

            for i_channel in self.low_4040:
                if now - time_last_step_4040[i_channel] > delta_steptime_4040[i_channel]:
                    current_step_4040[i_channel] += 1
                    time_last_step_4040[i_channel] = now
                    if len(voltages_4040[i_channel]) > current_step_4040[i_channel]:
                        self.set_voltage_4040(voltages_4040[i_channel][current_step_4040[i_channel]], i_channel)
                        not_finished.append(1)
                else:
                    not_finished.append(1)
            self.fraction_done=min((now -time_start)/total_time,1.)
            time.sleep(1)
            
            if sum(not_finished) == 0 or self.stop_scan_event.is_set():
                break

    def insert_into_db(self, conn, value, sensor_id, dev_id):
        # logging.info(f"{conn} {value} {sensor_id} {dev_id} sensor id || {self.sensor_id}")
        time_data = datetime.timestamp(datetime.now())

        c = conn.cursor()
        for j in value:
            for i in range(2):
                try:
                    with self._lock:
                        i_sensor_id = self.sensor_id.index((sensor_id[0], j, i))
                        c.execute("INSERT INTO measurement VALUES (:time, :value, :id)", {"time": time_data, "value": value[j][i], "id": i_sensor_id})
                        conn.commit()
                except ValueError as e:
                    logging.error(str(e))
        c.close()

    # @st.cache
    def get_working_ports(self):
        port_d = {}
        devices = ["Arduino", "KORAD", "HAMEG","KEITHLEY"]
        try:
            found_ports = self.find_ports()
            for i in range(len(devices)):
                for l in found_ports.splitlines():
                    if devices[i] in l or ("USB2.0-Ser!" in l and devices[i]=="KEITHLEY") or ("HO732" in l and devices[i]=="HAMEG") :
                        dev_id_l = re.findall("/[a-zA-Z]+/[a-zA-Z]+\d", l)
                        dev_id = dev_id_l[0]
                        #print(dev_id)
                        if devices[i] in ["Arduino", "KORAD"]:
                            port_d[devices[i]] = [dev_id, i, "serial"]
                        else:
                            port_d[devices[i]] = [dev_id, i, "visa"]
        except:
            logging.error("No USB self.connections found")
        print(f"These are the ports {port_d}")
        return port_d

    # @st.cache(hash_funcs={sqlite3.Connection: lambda _: None, serial.serialposix.Serial: lambda _: None})
    def get_unique_sensor_id(self):
        sensor_id = []
        serial_open = {}
        ## get unique sensor/device id
        counter = 0
        with self._lock:
            for i, key in enumerate(self.port_d):
                list_values = self.port_d[key]
                print("check",list_values,key)
                if "visa" in list_values and key == "HAMEG":
                    dev_id = self.port_d.get(key)[0]
                    rm = pyvisa.ResourceManager()
                    if platform.system() == "Linux":
                        hmp4040_ps = rm.open_resource("ASRL" + dev_id + "::INSTR")
                    else:
                        ## TODO: check this
                        hmp4040_ps = rm.open_resource("ASRL5::INSTR")
                    for i in range(1, 5):
                        hmp4040_ps.write(f"INST OUT{i}")
                        # hmp4040_ps.write(f"OUTP:SEL{i}i")
                        # hmp4040_ps.write(f"OUTP {i}")
                        sensor_id.append((dev_id, i, 0))
                        sensor_id.append((dev_id, i, 1))
                    serial_open[dev_id] = hmp4040_ps
                    # print("hameg", serial_open[dev_id])
                
                # now the keithley is on the /dev/ttyUSB1: USB2.0-Ser!
                if "visa" in list_values and key == "KEITHLEY":
                    dev_id = self.port_d.get(key)[0]

                    rm = pyvisa.ResourceManager()
                    keithley = rm.open_resource("ASRL" + dev_id + "::INSTR")
                    # keithley.write("*RST")
                    sensor_id.append((dev_id, 1, 0))
                    sensor_id.append((dev_id, 1, 1))
                    serial_open[dev_id] = keithley
                    # value_V = keithley.query("MEAS:VOLT?").split(",")[0]
                    # value_I = keithley.query("MEAS:CURR?").split(",")
                    # keithley.write(f':SOUR:VOLT:LEV 0.5')
                    # print(value_V,value_I)
                    # print("keythley", serial_open[dev_id])

                elif "serial" in list_values and key == "Arduino":
                    dev_id = self.port_d.get(key)[0]
                    ser = serial.Serial(dev_id, 9600, timeout=5)
                    serial_open[dev_id] = ser
                    # print("ardu", serial_open[dev_id])
                    debug_setup = ""
                    count=0
                    while True:
                        count+=1
                        if count>100:
                            break
                        line=""
                        try:
                            line = ser.read_until("\r\n".encode()).decode("utf-8")
                        except UnicodeDecodeError as e:
                            # This means that we got gibberish back, lets try it again
                            continue
                        except serial.serialutil.SerialException as e:
                            logging.error("Something is wrong no serial connection")
                            logging.error(e)
                            continue
                        debug_setup += line
                        # try:
                        if "1 " == line[0:2]:
                            # 1 4,3.93T,66.11H
                            # /Port #(\d+) Found I2C 0x(\d\d)/gm
                            # TCA Port #3 Found I2C 0x44  --> Found SHT31 Temperature and Humidity Sensor!!
                            info_addr = re.findall("1 \d,.*", line)
                            # info_all = re.findall("Port #\d+ Found I2C 0x\d\d", line)
                            if len(info_addr) == 0:
                                logging.error(f"No result for line {line}")
                                continue
                            slot_nr = int(info_addr[0].split(",")[0].split(" ")[-1])
                            if (dev_id, slot_nr, 0) in sensor_id:
                                break
                            sensor_id.append((dev_id, slot_nr, 0))
                            sensor_id.append((dev_id, slot_nr, 1))
                    print(f"Arduino sensor_id {sensor_id}")
                    # print(debug_setup)
                        # except Exception as e:
                        #     logging.error("Exception " + str(e))
                        #     continue

                elif "serial" in list_values and key == "KORAD":
                    logging.debug("Korad communication starts")
                    dev_id = self.port_d.get(key)[0]
                    ser_K = serial.Serial(dev_id, 115200, timeout=1.0)
                    serial_open[dev_id] = ser_K
                    # with serial.Serial(dev_id, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=2.0) as ser_K:
                    with ser_K as ser_K_o:
                        sensor_id.append((dev_id, 1, 0))
                        sensor_id.append((dev_id, 1, 1))
                else:
                    logging.error("No ports available")
        return sensor_id, serial_open

    def order_data(self, result, df):
        for i_channel in result[1]:
            for i_index in range(2):
                with self._lock:
                    df.loc[(df["Port"] == result[0]) & (df["Channel"] == i_channel) & (df["Index"] == i_index), "Value"] = result[1][i_channel][i_index]

    def __init__(self):
        self.db_path = "database/2022_Desy_debug2.db"
        self.result_queue = Queue()
        self._lock = threading.Lock()
        self.stop_event = Event()
        self.stop_scan_event = Event()
        self.conn = self.get_database_connection(self.db_path)
        self.port_d = self.get_working_ports()
        self.sensor_id, self.serial_open = self.get_unique_sensor_id()
        self.low_103 = 0.0
        self.high_103 = 0.0
        self.steps_103 = 0.0
        self.steptime_103 = 0.0
        self.low_keithley = 0.0
        self.high_keithley = 0.0
        self.steps_keithley = 0.0
        self.steptime_keithley = 0.0
        # st.text('suggested number of steps: ' + str(int((high_103-low_103)*5 + 1)))
        self.low_4040 = {}
        self.high_4040 = {}
        self.steps_4040 = {}
        self.steptime_4040 = {}
        self.current_saved_sensors=None
        self.fraction_done=0.
        self.count = 0

    # @st.cache(hash_funcs={sqlite3.Connection: lambda _: None, serial.serialposix.Serial: lambda _: None})
    def init(self):
        print("An other brick in the wall")
        c = self.conn.cursor()
        c.execute(
            """ CREATE TABLE IF NOT EXISTS sensors (
            sens_id integer,
            sens_type text,
            sens_unit text,
            sens_des text,
            sens_name text,
            valid_from datetime
            )"""
        )
        c.execute(
            """ CREATE TABLE IF NOT EXISTS measurement (
            time datetime,
            value float,
            sensor_id integer,
            FOREIGN KEY (sensor_id) REFERENCES sensors(sens_id)
            )"""
        )
        self.conn.commit()
        c.close()
        self.list_of_colors = ["#e31a1c", "#ff7f00", "#6a3d9a", "#ffff99", "#b15928", "#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#fb9a99"]

    # @st.cache(hash_funcs={sqlite3.Connection: lambda _: None, serial.serialposix.Serial: lambda _: None})
    def setup(self):
        pass
        self.port_d = self.get_working_ports()
        self.sensor_id, serial_open = self.get_unique_sensor_id()
        valid_time=datetime.now()

        # get sensor info for sensor table
        for j, sens_i in enumerate(self.sensor_id):
            c = self.conn.cursor()
            i_sensor_id = self.sensor_id.index((self.sensor_id[j][0], self.sensor_id[j][1], self.sensor_id[j][-1]))
            for i, key in enumerate(self.port_d.keys()):
                if self.sensor_id[j][0] == self.port_d.get(key)[0]:
                    sensor_des = f"{key}_{self.sensor_id[j][1]}"
                    if key == "HAMEG" or key == "KORAD" or key == "KEITHLEY":
                        if self.sensor_id[j][-1] == 0:
                            sensor_type = "Voltage"
                            sensor_unit = "V"
                        else:
                            sensor_type = "Current"
                            sensor_unit = "A"
                    elif key == "Arduino":
                        if self.sensor_id[j][-1] == 0:
                            sensor_type = "Temperature"
                            sensor_unit = "°C"
                        else:
                            sensor_type = "Humidity"
                            sensor_unit = "%"
            try:
                # print("test",i_sensor_id,sensor_type, sensor_unit,  sensor_des)
                c.execute("INSERT INTO sensors VALUES (:id, :type, :unit, :desc, :name, :valid_time)", {"id": i_sensor_id, "type": sensor_type, "unit": sensor_unit, "desc": sensor_des, "name": sensor_des, "valid_time":valid_time})
            except sqlite3.OperationalError as e:
                logging.error(str(e))
                u_dict = {"id": i_sensor_id, "type": sensor_type, "unit": sensor_unit, "desc": sensor_des, "name": sensor_des,"valid_time":valid_time}
                logging.error(f"Will skip: {u_dict}")
                print(pd.read_sql("SELECT * FROM sensors ORDER BY sens_id ASC", self.conn))

                self.conn.commit()
            c.close()
            self.get_sidebar_info()

    def get_sidebar_info(self):
        data = pd.read_sql("""SELECT * FROM sensors as s1  
        WHERE NOT EXISTS(
            SELECT *
            FROM sensors AS s2
            WHERE s2.sens_id = s1.sens_id
            AND s2.valid_from > s1.valid_from
        )
        ORDER BY sens_id ASC
        """, self.conn)  ##database is read into dataframe
        self.current_saved_sensors=data
    def run(self):
        self.all_measurement_threads = []
        t_hameg = Thread(
            target=self.hameg,
            name="t_hameg",
            args=(self.result_queue, self.conn, self.port_d, self.sensor_id),
            daemon=True,
        )
        self.all_measurement_threads.append(t_hameg)
        t_keythley = Thread(
            target=self.keythley,
            name="t_keythley",
            args=(self.result_queue, self.conn, self.port_d, self.sensor_id),
            daemon=True,
        )
        self.all_measurement_threads.append(t_keythley)
        t_arduino = Thread(
            target=self.arduino,
            name="t_arduino",
            args=(self.result_queue, self.conn, self.port_d, self.sensor_id, self.serial_open),
            daemon=True,
        )
        self.all_measurement_threads.append(t_arduino)
        t_korad = Thread(
            target=self.korad,
            name="t_korad",
            args=(self.result_queue, self.conn, self.port_d, self.sensor_id, self.serial_open),
            daemon=True,
        )
        self.all_measurement_threads.append(t_korad)

        t_scan_tread = Thread(
            target=self.scan_thread,
            name="scan",
            # daemon=True,
        )

        ## sidebar settings
        # c = self.conn.cursor()
        st.sidebar.subheader("Current database of sensors:")  # st.subheader('Current database of sensors:')
        
        # last_ts=data[]
        st.sidebar.dataframe(self.current_saved_sensors)  # st.dataframe(data)
        if len(self.current_saved_sensors) != 0:
            last_id = self.current_saved_sensors.iloc[-1:]
            last_id = int(last_id.values.tolist()[0][0])
        else:
            last_id = 0
        
        # duration = float(st.sidebar.number_input("Duration of measurement in minutes:"))
        # c.close()
        st.sidebar.subheader("Direct PS control:")
        option=st.sidebar.selectbox("Which device do you want to set the voltage for?",["Please select"]+list(self.port_d.keys()))
        if option!="Please select":
            # get only devices that match the selected input and use index 0 to avoid duplicates
            # FIXME this assumes only one ps at of one kind is connected!
            dev_addr=self.port_d[option][0]
            filtered = list(filter(lambda elem: elem[0]==dev_addr and elem[2]==0, self.sensor_id))
            channel=1
            if len(filtered)>1:
                channel = st.sidebar.selectbox("Which channel do you want to set the voltage for?",["Please select"]+filtered)[1]
            voltage = st.sidebar.number_input('Set to Voltage')
            if st.sidebar.button("Apply Voltage"):
                if option=="HAMEG":
                    self.set_voltage_4040(voltage, channel,switch_on=True)
                elif option=="KORAD":
                    self.set_voltage_103(voltage,switch_on=True)
            if st.sidebar.button("switch channel off"):
                self.switch_off(option,channel=channel)

        st.subheader("Measurement")
        ## TODO: auto settings!!
        timmin_psu_103 = 0
        with st.expander(label="PSU automation"):
            psu_auto_butt = st.checkbox("Check for automation.")

            st.subheader("KORAD KWR103 Settings")
            self.low_103 = st.number_input("initial voltage for KW103 (V)")
            self.high_103 = st.number_input("target voltage for KW103 (V)")
            self.steps_103 = st.number_input("voltage steps for KW103")
            self.steptime_103 = st.number_input("time per step (min)")
            # st.text('suggested number of steps: ' + str(int((high_103-low_103)*5 + 1)))
            if "HAMEG" in self.port_d:
                st.subheader("R&S HMP4040 Settings")
                dev_addr=self.port_d["HAMEG"][0]
                possible_channels = list(filter(lambda elem: elem[0]==dev_addr and elem[2]==0, self.sensor_id))
                channel_4040 = st.multiselect("Channel", possible_channels)
                if channel_4040:
                    for channel_i in range(len(channel_4040)):
                        self.low_4040[channel_i] = st.number_input(f"initial voltage for HMP4040 for channel{channel_4040[channel_i]}")
                        self.high_4040[channel_i] = st.number_input(f"target voltage for HMP4040 for channel{channel_4040[channel_i]}")
                        self.steps_4040[channel_i] = st.number_input(f"voltage steps for HMP4040 for channel{channel_4040[channel_i]}")
                        self.steptime_4040[channel_i] = st.number_input(f"time per step (min) for channel{channel_4040[channel_i]}")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Start measurement"):
                self.stop_event.clear()
                for thread in self.all_measurement_threads:
                    thread_running = False
                    for active_thread in threading.enumerate():
                        # print(active_thread.name, thread.name)
                        if active_thread.name == thread.name:
                            logging.info(f"Thread already running! {thread.name}")
                            thread_running = True
                    if not thread_running:
                        thread.start()
        with col2:
                if st.button("Stop measurement"):
                    start_m = False
                    self.stop_event.set()
                    for thread in threading.enumerate():
                        if "t_" in thread.name and thread.is_alive():
                            thread.join()
        with col3:
            self.count = 0
            for thread in threading.enumerate():
                # logging.info(f"These threads are running: {thread.name}")
                self.count += 1
            is_running = False
            for thread in threading.enumerate():
                if "t_" in thread.name and thread.is_alive():
                    is_running = True
                    break
            if is_running:
                # st.title("We are taking data!")
                # st.image(self.image, caption='We are running!')
                st.image('tumblr_m25q7ciDgA1r5ur0ho1_r2_400.gif')
                st.markdown("""We are running!
                <sup><sub>[source](https://batmanrunningawayfromshit.tumblr.com/post/20707879780)</sub></sup>""",unsafe_allow_html=True)
            else:
                st.title("We are not taking data!")
            st.metric("Number of active threads",self.count)

        if st.button("Start scan"):
            thread_running = False
            for active_thread in threading.enumerate():
                # print(active_thread.name, thread.name)
                if active_thread.name == t_scan_tread.name:
                    logging.info(f"Thread already running! {t_scan_tread.name}")
                    thread_running = True
            if not thread_running:
                t_scan_tread.start()
        if self.fraction_done and self.fraction_done<1:
            if st.button("Stop Scan"):
                self.stop_scan_event.set()
            scan_bar = st.progress(0)
            scan_bar.progress(self.fraction_done)
            if self.fraction_done>=1:
                st.write("Scan Complete")
       
        container = st.container()
        placeholder= st.empty()
        
        self.current_table=table_update(self)

        df_chart = placeholder.dataframe(self.current_table, 1500, 800)
        count = 0
        while True:
            count += 1
            df_chart = placeholder.dataframe(self.current_table, 1500, 800)
            time.sleep(0.1)
            if count > 50:
                break
        st.experimental_rerun()
        # with st.container():
        #     with st.empty():
        #         table_update(self.result_queue, self)
                


if __name__ == "__main__":
    main()
