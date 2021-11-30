import numpy as np
import sqlite3
import pandas as pd
import serial
import datetime
import time
import matplotlib.pyplot as plt

conn = sqlite3.connect('C:\\Users\\schum\\github\\cooling_setup\\sens\\database\\first.db')
c = conn.cursor()
