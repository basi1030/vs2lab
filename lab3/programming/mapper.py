# Task worker
# Connects PULL socket to tcp://localhost:5557
# Collects workloads from ventilator via that socket
# Connects PUSH socket to tcp://localhost:5558
# Sends results to sink via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>

import sys
import time
import zmq
import re
import hashlib

context = zmq.Context()
me = str(sys.argv[1])

# Socket to receive messages on
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:5557")

sender1 = context.socket(zmq.PUSH)
sender1.connect("tcp://localhost:5558")

sender2 = context.socket(zmq.PUSH)
sender2.connect("tcp://localhost:5559")

time.sleep(1) 

print("{} started".format(me))

def stable_hash(word):
    return int(hashlib.md5(word.encode()).hexdigest(), 16)

while True:
    # Satz empfangen
    sentence = receiver.recv_string()

    # In Wörter splitten
    words = re.findall(r'\b\w+\b', sentence.lower())

    for word in words:

        # Entscheiden welcher Reducer
        reducer = stable_hash(word) % 2

        if reducer == 0:
            sender1.send_string(word)
        else:
            sender2.send_string(word)

    # Fortschritt
    sys.stdout.write(".")
    sys.stdout.flush()