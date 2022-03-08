import sqlite3

conn = sqlite3.connect('C:\\Users\\schum\\Documents\\github\\cooling_setup\\sens\\database\\2022.db')
#conn = sqlite3.connect('C:\Users\schum\ownCloud\UNi-Materialien\Bachelor\Arbeit\code\monitoring')
c = conn.cursor()
c.execute("DROP TABLE sensors")
# c.execute("DROP TABLE measurement")
conn.commit()
c.close()
