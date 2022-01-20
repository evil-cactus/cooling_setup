import matplotlib.pyplot as plt
import sqlite3
import pandas as pd
import numpy as np

x = np.linspace(0,100,100)
y = np.random.random(100)
cmap = plt.get_cmap('RdYlBu')
plt.figure(figsize=(10,4), dpi=200)
plt.scatter(x,y,c=y, cmap=cmap)
plt.show()

text = 'adfjofug4irnldjvnkj'
print(text[0:4])
print(text['0:4'])
