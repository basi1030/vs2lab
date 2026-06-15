# Task sink
# Binds PULL socket to tcp://localhost:5558
# Collects results from workers via that socket
#
# reducer1.py

import sys
import time
import zmq


context = zmq.Context()

# Socket to receive messages on
receiver = context.socket(zmq.PULL)
receiver.bind("tcp://*:5559")

# Wörter zählen
word_count = {}

while True:
    # Wort empfangen
    word = receiver.recv_string()

    if not word in word_count:
        word_count[word] = 1
    else:
        word_count[word] += 1

    print(f"{word}: {word_count[word]}")


