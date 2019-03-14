import time

import os
from flask import Flask, request, render_template, g
from blockchain_parser.blockchain import Blockchain

# first transaction 4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b
app = Flask(__name__)


@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)


def find_transaction(transaction_id):
    # Instantiate the Blockchain by giving the path to the directory
    # containing the .blk files created by bitcoind
    blockchain = Blockchain("datas")
    for block in blockchain.get_unordered_blocks():
        for tx in block.transactions:
            # if tx.hash == transaction_id:
            if len(tx.outputs) > 2:
                return tx
    return None


def find_transaction_ordered(transaction_id):
    # Instantiate the Blockchain by giving the path to the directory
    # containing the .blk files created by bitcoind
    blockchain = Blockchain("datas")
    for block in blockchain.get_ordered_blocks("datas/index"):
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
    app.run()
