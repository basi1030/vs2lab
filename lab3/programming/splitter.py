# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>

import zmq
import random
import time
from pathlib import Path
from pypdf import PdfReader
import spacy

nlp = spacy.load("de_core_news_sm")

pdf_path = Path(__file__).parent / "aschenputtel.pdf"

context = zmq.Context()

# Socket to send messages on
sender = context.socket(zmq.PUSH)
sender.bind("tcp://*:5557")

print("Press Enter when the workers are ready: ")
_ = input()
print("Sending tasks to workers...")

reader = PdfReader(pdf_path)
text = ""
for page in reader.pages:
    page_text = page.extract_text()
    if page_text:
        text += page_text + " "

doc = nlp(text)

for i, sent in enumerate(doc.sents, start=1):
    sender.send_string(f"{sent}")
# Give 0MQ time to deliver
time.sleep(1)