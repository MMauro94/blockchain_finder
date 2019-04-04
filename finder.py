import time

import os
import redis
import pickle

from multiprocessing import Process, Value, Queue
import math

from collections import deque
from flask import Flask, request, render_template, g
from blockchain_parser.blockchain import Blockchain

CACHE_RANGE = 200
NUM_PROCESSES = 3

# Limits the search only in this range (to test speedly and don't wait much time)
START_BLOCK = 545287
END_BLOCK = 542000


# first transaction 4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b
app = Flask(__name__)
red = redis.Redis(host="localhost", port=6379, db=0)
red.flushall()

@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)


def all_transactions(p_id):
    # Init the blockchain data with library function
    blockchain = Blockchain("datas")

    # Perform the range to give at process p_id
    r = next(x for i,x in enumerate(split(range(START_BLOCK+1, END_BLOCK, -1), NUM_PROCESSES)) if i == p_id)
    print("Process: " + str(p_id) + ", start=" + str(r.start) + ", stop=" + str(r.stop))

    # For each block in the range (taken them sorted) indecing it
    for block in blockchain.get_ordered_blocks(
        "datas/index", end=r.stop, start=r.start, cache="index-cache{}-{}.pickle".format(p_id, NUM_PROCESSES)
    ):
        print("BLOCK", block.height)
        for i, tx in enumerate(block.transactions):
            yield tx

# Splits the given range a in n parts of same size where n is given by the numbers of process
def split(a, n):
    # Divide a in n parts. k is the length of each part and m the remainder of division
    k, m = divmod(len(a), n)
    
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


# Returns transaction and list of the near ones
def load_transaction(transaction_id, iter_transaction, global_found, result_queue):
    cached_values = deque()
    found = None

    # For each transaction, checks if exist
    for tx in iter_transaction:
        # LRU operations
        # If overcome the middle of cache range, remove the oldest record
        if len(cached_values) > CACHE_RANGE // 2:
            cached_values.popleft()

        # Adds the current transaction to the cache
        cached_values.append(tx)
        # Checks if someother found the transaction, if true exit
        if global_found.value == True: # Someone else found the results
            return None
        # If finds the transaction, break the curret flow and save the transaction
        if tx.hash == transaction_id:
            found = tx 
            break
    tx_index = 0

    # If it hasn't find it, return None
    if found is None:
        return None
    
    # Notify all other processes that the record has been find
    global_found.value = True
    # Push result into shared Queue
    result_queue.put(found)

    # For each transaction in the cached transactions, compress the tx and put it in redis (cached)
    for tx in cached_values:
        marshaled_tx = pickle.dumps(tx)
        redis_set(tx.hash, marshaled_tx)

    # Until has some space in cache and there are transaction to visit, compress them and put them in redis
    while tx_index < CACHE_RANGE // 2 and iter_transaction:
        marshaled_tx = pickle.dumps(next(iter_transaction))
        redis_set(tx.hash, marshaled_tx)
        tx_index += 1

# Returns the value associated to the key passed as parameter. None if not exist
def redis_get(key):
    try:
        redis_value = red.get(key)
    except redis.exceptions.ConnectionError as err:
        redis_value = None

    return redis_value

# Set a new value in the cache with key and value
def redis_set(key, value):
    try:
        red.set(key, value)
    except redis.exceptions.ConnectionError as err:
        pass

# Value generator to fix library issue
def start_iterator(first_val, iterator):
    yield first_val
    yield from iterator

# Main function. Gets a transaction id and returns all the transactions linket to its
def find_transaction(transaction_id):
    # Instantiate the Blockchain by giving the path to the directory
    # containing the .blk files created by bitcoind

    # key to find from redis
    redis_key = str(transaction_id)
    # Gets the redis value linked to the key
    redis_value = redis_get(redis_key)

    # If not found return None
    if redis_value == b"":
        return None
    # If exist in the cache, return the value/s
    elif redis_value is not None:
        return pickle.loads(redis_value)
    
    # Parallelization
    # ---------------------------------------------------------

    # If a thread find a result it communicate with this element
    global_found = Value("b",False, lock=True)  # Used for interprocess notification 
    result_queue = Queue()                      # Used to store the returned value of "founder" process

    # Process list
    processes = []

    for i in range(0,NUM_PROCESSES):
        # Gets all transactions
        all_it = all_transactions(i)
        try:
            # Gets the first transaction
            val = next(all_it)
        except StopIteration:
            continue

        # Makes an iterator on the values
        iterator = start_iterator(val, all_it)
        # Makes a process that gets its assigned transactions, the transaction id to search, the iterator
        # to scan the list, the notifier and the queue where put the results
        p = Process(target=load_transaction,args=(transaction_id, iterator, global_found, result_queue))
        
        # Adds the process to process list
        processes.append(p)

        # Starts the process
        p.start()
        print("process " + str(i) + " started")

    #res = load_transaction(transaction_id,portion=1, num_portions = 1)

    # Join all process
    for i, p in enumerate(processes):
        print("process " + str(i) + " joining")
        print(p)
        p.join()
        print("process " + str(i) + " joined")
    

    res = None
    # If someone has found a result, get it from the result list
    if global_found.value == 1:
        res = result_queue.get() #Get shared result and put into res
    
    # If the cache is null, cache from current key
    if res is None: 
        redis_set(redis_key, "")
        return None
    # Else ?
    else:
        found = pickle.dumps(res)
        redis_set(res.hash, found)
        return res


@app.route("/")
def hello():
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def print_transaction_view():
    id_tx = request.args.get("tx_id")
    if id_tx is None:
        return "Error"
    res = find_transaction(id_tx)
    return render_template("output.html", tx=res, enumerate=enumerate)


# @app.route("/search_ordered", methods=["GET"])
# def print_transaction_view():
#     id_tx = request.args.get("tx_id")
#     res = find_transaction_ordered(id_tx)

#     return print_transaction(res)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
