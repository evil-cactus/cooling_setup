import sqlite3

conn = sqlite3.connect('./test.db')
c = conn.cursor()
c.execute("DROP TABLE sensors")
c.execute("DROP TABLE measurement")
conn.commit()
c.close()
