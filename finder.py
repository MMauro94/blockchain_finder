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
NUM_PROCESSES = 1

# first transaction 4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b
app = Flask(__name__)
red = redis.Redis(host="localhost", port=6379, db=0)


@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)


def all_transactions(p_id,num_proc):
    blockchain = Blockchain("datas")
    
    #Calculate the process research boundaries
    delta_proc = math.ceil((545289 - 542000)/num_proc)
    proc_start = 542000 + (p_id+1) * delta_proc
    proc_end = 542000 + p_id * delta_proc

    for block in blockchain.get_ordered_blocks(
        "datas/index", end=proc_end, start=proc_start, cache="index-cache.pickle"
    ):
        for tx in block.transactions:
            yield tx


# return transaction and list of the near ones
def load_transaction(transaction_id, p_id , num_proc, global_found, result_queue):
    cached_values = deque()
    found = None
    iter_transaction = all_transactions(p_id,num_proc)

    for tx in iter_transaction:
        if len(cached_values) > CACHE_RANGE // 2:
            cached_values.popleft()
        cached_values.append(tx)
        if global_found.value == True: #Someone else found the result
            return None
        if tx.hash == transaction_id:
            found = tx 
            break
    tx_index = 0

    if found is None:
        return None

    while tx_index < CACHE_RANGE // 2 and iter_transaction:
        cached_values.append(next(iter_transaction))
        tx_index += 1
    
    global_found.value = True #Notify all other processes
    result_queue.put([found, cached_values]) #Push value into shared Queue

    return found, cached_values


def redis_get(key):
    try:
        redis_value = red.get(key)
    except redis.exceptions.ConnectionError as err:
        redis_value = None

    return redis_value

def redis_set(key, value):
    try:
        red.set(key, value)
    except redis.exceptions.ConnectionError as err:
        pass

def find_transaction(transaction_id):
    # Instantiate the Blockchain by giving the path to the directory
    # containing the .blk files created by bitcoind
    redis_key = str(transaction_id)
    redis_value = redis_get(redis_key)

    if redis_value == b"":
        return None
    elif redis_value is not None:
        return pickle.loads(redis_value)
    
    #COMINCIAMO A PARALLELIZZARE QUA
    global_found = Value("b",False, lock=True)  #Used for interprocess notification 
    result_queue = Queue()                      #Used to store the returned value of "founder" process

    processes = []
    for i in range(0,4):
        processes[i] = Process(target=load_transaction,args=(transaction_id,i,NUM_PROCESSES,global_found, result_queue,))
        processes[i].start()

    #res = load_transaction(transaction_id,portion=1, num_portions = 1)

    for i in range(0,4):
        processes[i].join()

    res = None
    if(global_found.value == 1):
        res = result_queue.get() #Get shared result and put into res
    
    if res is None: 
        redis_set(redis_key, "")
        return None
    else:
        found, to_be_cached = res
        for tx in to_be_cached:
            marshaled_tx = pickle.dumps(tx)
            redis_set(tx.hash, marshaled_tx)
        return found


@app.route("/")
def hello():
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def print_transaction_view():
    t = request.values.get("t", 0)
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
