import time

import os
import redis
import pickle
import plyvel

from collections import deque
from flask import Flask, request, render_template, g
from blockchain_parser.blockchain import Blockchain

CACHE_RANGE = 200

# first transaction 4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b
app = Flask(__name__)
red = redis.Redis(host="redis", port=6379, db=0)
red.flushall()

blockchain = Blockchain("/blockchain/blocks")

# force the creation of the index
if os.path.exists("super-big-index.pickle"):
    os.remove("super-big-index.pickle")

print("Creating index")
next(blockchain.get_ordered_blocks("/blockchain/blocks/index", cache="super-big-index.pickle"))
print("Index created")

pldb = plyvel.DB('/blockchain/tx_to_block/', create_if_missing=False)


class IllegalState(Exception):
    pass


@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)


def get_block_transactions(block_height):
    for block in blockchain.get_ordered_blocks(
            "/blockchain/blocks/index",
            end=block_height,
            start=block_height + 1,
            cache="super-big-index.pickle",
    ):
        print(block.height)
        for tx in block.transactions:
            yield tx


# return transaction and list of the near ones
def load_transaction(transaction_id):
    block_height = pldb.get(transaction_id.encode())

    if block_height is None:
        return None
    block_it = get_block_transactions(int(block_height))

    found = None
    for tx in block_it:
        marshaled_tx = pickle.dumps(tx)
        redis_set(tx.hash, marshaled_tx)

        if tx.hash == transaction_id:
            found = tx

    if found is None:
        raise IllegalState
    return found


def redis_get(key):
    try:
        redis_value = red.get(key)
    except redis.exceptions.ConnectionError:
        redis_value = None

    return redis_value


def redis_set(key, value):
    try:
        red.set(key, value)
    except redis.exceptions.ConnectionError:
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

    return load_transaction(transaction_id)


@app.route("/")
def hello():
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def print_transaction_view():
    id_tx = request.args.get("tx_id")
    print(id_tx)
    if id_tx is None:
        return "Error"
    res = find_transaction(id_tx)
    if res is None:
        http_code = 404
    else:
        http_code = 200
    return render_template("output.html", tx=res, enumerate=enumerate), http_code


@app.route("/sample", methods=["GET"])
def print_one():
    for block in blockchain.get_unordered_blocks():
        for tx in block.transactions:
            return tx.hash


# @app.route("/search_ordered", methods=["GET"])
# def print_transaction_view():
#     id_tx = request.args.get("tx_id")
#     res = find_transaction_ordered(id_tx)

#     return print_transaction(res)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
