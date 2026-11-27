"""Exercise EOF framing through a real TCP connection."""
import http.client
import socket
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from transitweave.server import Handler


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


class RequestFraming(unittest.TestCase):
    def test_complete_json_must_match_declared_length(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        server.gate = threading.BoundedSemaphore(1)
        server.config = {}
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch('transitweave.server.run_case', return_value={'ok': True}) as calculate:
                for extra in (5, 0):
                    with self.subTest(extra_bytes=extra):
                        calculate.reset_mock()
                        body = b'{}'
                        with socket.create_connection(server.server_address, timeout=2) as connection:
                            headers = ('POST /api/run HTTP/1.0\r\nContent-Type: application/json\r\n'
                                       f'Content-Length: {len(body) + extra}\r\n\r\n').encode()
                            connection.sendall(headers + body)
                            connection.shutdown(socket.SHUT_WR)
                            response = http.client.HTTPResponse(connection)
                            response.begin()
                            self.assertEqual(response.status, 400 if extra else 200)
                            response.read()
                        if extra:
                            calculate.assert_not_called()
                        else:
                            calculate.assert_called_once()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
