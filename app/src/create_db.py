import os
import sys
import signal
import plyvel
import time
from blockchain_parser.blockchain import Blockchain

block_height = 0


def write_last_block(last_block):
    with open('/blockchain/tx_to_block/last_block_leveldb.txt', 'w') as f:
        f.write(str(last_block))


def handler(a, b):
    print("HANDLER CALLED")
    write_last_block(block_height - 1)
    sys.exit(1)


signal.signal(signal.SIGINT, handler)

if os.path.exists('/blockchain/tx_to_block/last_block_leveldb.txt'):
    with open('/blockchain/tx_to_block/last_block_leveldb.txt', 'r') as f:
        last_block = int(f.readline())
else:
    last_block = -1

print("Last written block:", last_block)

if not os.path.exists("/blockchain/tx_to_block"):
    db = plyvel.DB('/blockchain/tx_to_block', create_if_missing=True)
    blockchain = Blockchain(os.path.expanduser('/blockchain/blocks'))
    total_tx = 0
    tm = time.time()
    tx_in_time_slot = 0
    tx_per_sec = 0
    for block in blockchain.get_ordered_blocks('/blockchain/blocks/index', start=last_block + 1):
        block_height = block.height
        block_height_bytes = str(block_height).encode()
        block_tx = 0
        with db.write_batch() as batch:
            for tx in block.transactions:
                block_tx += 1
                batch.put(tx.hash.encode(), block_height_bytes)
        total_tx += block_tx
        write_last_block(block_height)
        if time.time() - tm < 1:
            tx_in_time_slot += block_tx
        else:
            tm = time.time()
            tx_per_sec = tx_in_time_slot / 60
            tx_in_time_slot = 0
        print("Block", block_height, "(", total_tx, " transactions),", tx_per_sec, "tx/sec")
    db.close()
    print("Finished")
