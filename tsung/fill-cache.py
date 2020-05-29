import requests

with open("test_transactions_one.data", "r") as f:
    i = 0
    for tx in f:
        i += 1
        tx = tx.strip()
        print(str(i) + "/10000 Requesting " + tx + "...", end="", flush=True)
        try:
            response = requests.get('http://192.168.1.9:8081/search?tx_id=' + tx)
        except Exception as e:
            print("Exception " + str(e))
            break
