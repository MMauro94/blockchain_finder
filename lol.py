import time
import os
import redis
import pickle

from collections import deque
from blockchain_parser.blockchain import Blockchain


def a_tx():
	blockchain = Blockchain("datas")

	for block in blockchain.get_ordered_blocks(
		"datas/index", end=545287, start=545288, cache="index-cache-diolampadina.pickle"
	):
		for tx in block.transactions:
			return tx



time1 = time.time()
tx = a_tx()
time2 = time.time()
print(tx)
print('function took {:.3f} ms'.format((time2-time1)*1000.0))

