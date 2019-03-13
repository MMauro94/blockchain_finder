import os
from flask import Flask, request
from blockchain_parser.blockchain import Blockchain


app = Flask(__name__)


def find_transaction(transaction_id):
    # Instantiate the Blockchain by giving the path to the directory
    # containing the .blk files created by bitcoind
    blockchain = Blockchain("datas")
    for block in blockchain.get_unordered_blocks():
        for tx in block.transactions:
            if tx.hash == transaction_id:
                return tx
    return None


def print_transaction(tx):
    res = ""
    for no, output in enumerate(tx.outputs):
        res += "tx=%s outputno=%d type=%s value=%s" % (
            tx.hash,
            no,
            output.type,
            output.value,
        )
    return res


@app.route("/")
def hello():
    with open("index.html") as file:
        return file.read()


@app.route("/search", methods=["GET"])
def print_transaction_view():
    id_tx = request.args.get("tx_id")
    res = find_transaction(id_tx)

    return print_transaction(res)


if __name__ == "__main__":
    app.run()
