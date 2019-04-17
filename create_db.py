import os
import mysql.connector
from blockchain_parser.blockchain import Blockchain

conn = mysql.connector.connect(
         host="127.0.0.1",
         user="root",
         password="toor",
         auth_plugin="mysql_native_password"
         )


cursor = conn.cursor()

cursor.execute('CREATE DATABASE IF NOT EXISTS Blockchain')

conn = mysql.connector.connect(
         host="localhost",
         user="root",
         database="Blockchain",
         passwd="toor",
         auth_plugin="mysql_native_password"
         )
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS transaction (
     id VARCHAR(70) PRIMARY KEY,
     block MEDIUMINT UNSIGNED NOT NULL
     )''')

add_transaction = ("INSERT ignore INTO transaction "
               "(id, block) "
               "VALUES (%s, %s)")

blockchain = Blockchain(os.path.expanduser('./datas'))
conn.autocommit=False
total_tx=0
for block in blockchain.get_ordered_blocks('./datas/index', start=541999, end=545288):
     block_height = block.height
     tx_list = [(tx.hash,block_height) for tx in block.transactions]
     total_tx += len(tx_list)
     cursor.executemany(add_transaction,tx_list)
     if(total_tx > 50000):
          total_tx=0
          print("Commit...")
          conn.commit()
          print("Committed")
     print("Block", block_height, "(", total_tx, " transactions)")
conn.commit()
conn.autocommit=True
print("Finished")

# try:
#      cursor.execute(add_transaction,('bb02282e8765482df5f6b15f5e9b187fac657a1920e7743cf1c420c9d6333bf1',545285))
#      conn.commit()
# except mysql.connector.errors.IntegrityError: # Duplicate entry
#      pass

cursor.execute("SELECT block FROM transaction WHERE id = 'bb02282e8765482df5f6b15f5e9b187fac657a1920e7743cf1c420c9d6333bf1'")
res = cursor.fetchone()[0] # fetch ritorna tuple
assert res == 545285
print("ok")

     
