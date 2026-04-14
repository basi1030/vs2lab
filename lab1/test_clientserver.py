"""
Simple client server unit test
"""

import logging
import threading
import unittest

import clientserver
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestEchoService(unittest.TestCase):
    """The test"""
    _server = clientserver.Server()  # create single server in class variable
    _server_thread = threading.Thread(target=_server.serve)  # define thread for running server

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = clientserver.Client()  # create new client for each test

    def tearDown(self):
        self.client.close()  # terminate client after each test
        
    def test_get_existing(self):
        """Test GET mit vorhandenem Namen"""
        result = self.client.get("Simi")
        self.assertEqual(result, "+491745789846")

    def test_get_not_existing(self):
        """Test GET mit unbekanntem Namen"""
        result = self.client.get("Max")
        self.assertEqual("Der Name Max befindet sich nicht im Telefonverzeichnis.", result)

    def test_getall(self):
        """Test GETALL"""
        result = self.client.getall()
        self.assertIn("Simi", result)
        self.assertIn("Lisa", result)
        self.assertIn("Joline", result)

    def test_backend_get(self):
        result = self._server.getData(b"Simi")
        self.assertEqual(result, "+491745789846")

    def test_backend_getall(self):
        result = self._server.getData(b"GETALL")
        self.assertIn("Simi", result)
        self.assertIn("Lisa", result)
        self.assertIn("Joline", result)
        
    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
