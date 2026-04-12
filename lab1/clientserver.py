"""
Client and server using classes
"""

import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# pylint: disable=logging-not-lazy, line-too-long

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True
    telefon_verzeichnis = {
    "Simi": "+491745789846",
    "Joline": "+4915141212280",
    "Lisa": "+49123456789"
    }
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))

    def serve(self):
        """ Serve echo """
        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    if not data:
                        break  # stop if client stopped
                    response = self.getData(data)
                    connection.send(response.encode('ascii')) 
                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self._logger.info("Server down.")
        
    def getData(self, data):
        decodedData = data.decode("ascii")
        if(decodedData == "GETALL"):
            return str(self.telefon_verzeichnis)
        if decodedData in self.telefon_verzeichnis:
            return self.telefon_verzeichnis[decodedData]
        else:
            return "Der Name " + data + " befindet sich nicht im Telefonverzeichnis."
        return "Fehlermeldung"

class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def call(self, msg_in):
        """ Call server """
        self.sock.send(msg_in.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('ascii')
        print(msg_in + ": ", msg_out)  # print the result
        self.logger.info("Client down.")
        return msg_out

    def close(self):
        """ Close socket """
        self.sock.close()

    def get(self, name):
        response = self.call(name)
        return response

    def getall(self):
        response = self.call("GETALL")
        return response
        
