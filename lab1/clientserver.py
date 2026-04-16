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
                    name = data.decode('UTF-8')
                    self._logger.info("GET-Request received for "+ name + ".")
                    connection.send(response.encode('UTF-8')) 
                    self._logger.info("GET-Response sent for "+ name + ".")
                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self._logger.info("Server down.")
        
    def getData(self, data):
        decodedData = data.decode("UTF-8")
        if(decodedData == "GETALL"):
            return str(self.telefon_verzeichnis)
        if decodedData in self.telefon_verzeichnis:
            return self.telefon_verzeichnis[decodedData]
        else:
            return "Der Name " + decodedData + " befindet sich nicht im Telefonverzeichnis."

class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def call(self, msg_in):
        """ Call server """
        self.sock.send(msg_in.encode('UTF-8'))  # send encoded string as data
        self.logger.info("GET-Request sent for "+ msg_in + ".")
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('UTF-8')
        self.logger.info("GET-Response received for "+ msg_in + ".")
        print(msg_in + ": ", msg_out)  # print the result
        return msg_out

    def close(self):
        """ Close socket """
        self.logger.info("Client down. Socket closed.")
        self.sock.close()

    def get(self, name):
        response = self.call(name)
        return response

    def getall(self):
        response = self.call("GETALL")
        return response
        
