from multiprocessing import Process, Value, Queue
import os
from time import sleep
import random

def loopy(id,v,queue):
    while not v.value:
        #print(id, "is awake", v.value)
        sleep(1)
    print(id, "is dead")
    stringa = "I'm dead"+ str(id)
    if(id == 5):
        queue.put([stringa])
    return "I'm dead"+ str(id)

def stop(v):
    t_stop = random.randint(2,5)
    print("TSTOP -------", t_stop )
    sleep(t_stop)
    v.value = True
    print("Ho finito --------")



if __name__ == '__main__':
    p = {} 
    v = Value("b",False, lock=True)
    print("[BEGIN] SHARED VALUE:",v.value)
    q = Queue()

    p2 =  Process(target=stop,args=(v,))
    p2.start()
    
    for i in range(1,10):
        p[i] = Process(target=loopy, args=(i,v,q,))
        p[i].start()
    p2.join() 
    for i in range(1,10):
        p[i].join()

    print("[END] SHARED VALUE:",v.value)
    print("GET FROM QUEUE:",q.get())
    