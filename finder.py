import time

import os
import redis
import pickle

from collections import deque
from flask import Flask, request, render_template, g
from blockchain_parser.blockchain import Blockchain

CACHE_RANGE = 200

# first transaction 4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b
app = Flask(__name__)
red = redis.Redis(host="localhost", port=6379, db=0)


@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)


def all_transactions():
    blockchain = Blockchain("datas")

    for block in blockchain.get_unordered_blocks():
        for tx in block.transactions:
            yield tx


# return transaction and list of the near ones
def load_transaction(transaction_id):
    cached_values = deque()
    found = None
    iter_transaction = all_transactions()

    for tx in iter_transaction:
        if len(cached_values) > CACHE_RANGE // 2:
            cached_values.popleft()
        cached_values.append(tx)
        if tx.hash == transaction_id:
            found = tx
            break
    tx_index = 0

    if found is None:
        return None

    while tx_index < CACHE_RANGE // 2 and iter_transaction:
        cached_values.append(next(iter_transaction))
        tx_index += 1
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

    res = load_transaction(transaction_id)

    if res is None:
        redis_set(redis_key, "")
        return None
    else:
        found, to_be_cached = res
        for tx in to_be_cached:
            marshaled_tx = pickle.dumps(tx)
            redis_set(tx.hash, marshaled_tx)
        return found


def find_transaction_ordered(transaction_id):
    # Instantiate the Blockchain by giving the path to the directory
    # containing the .blk files created by bitcoind
    blockchain = Blockchain("datas")
    for block in blockchain.get_ordered_blocks("datas/index", end=0, start=8888888888):
        for tx in block.transactions:
            if tx.hash == transaction_id:
                return tx
    return None


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
