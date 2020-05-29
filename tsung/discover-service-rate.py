import requests
import random
import os
import time
import statistics

with open("test_transactions_one.data", "r") as f:
    f.seek(0, os.SEEK_END)
    size = f.tell()
    line_size = 64


    def random_tx():
        rnd = random.randint(0, size // (line_size + 1) - 1)
        f.seek(rnd * (line_size + 1))
        return f.readline().strip()


    times = []
    for i in range(200):
        tx = random_tx()
        print(f"{i}/200 Requesting " + tx + "...", end="", flush=True)
        try:
            home = requests.get('http://192.168.1.9:8081')
            response = requests.get(f'http://192.168.1.9:8081/search?tx_id={tx}')
        except Exception as e:
            print("Exception " + str(e))
            break
        tot_time = home.elapsed.total_seconds() + response.elapsed.total_seconds()
        times.append(tot_time)
        print(f'{response.status_code}, took {tot_time}')
        #time.sleep(1)

    if len(times) > 0:
        avg = sum(times) / len(times)
        print("Average response time: " + str(avg))
        print("Variance: " + str(statistics.variance(times)))
