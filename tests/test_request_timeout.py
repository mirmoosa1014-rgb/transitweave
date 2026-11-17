import http.client,socket,threading
from http.server import ThreadingHTTPServer
from transitweave.server import Handler

class ShortTimeoutHandler(Handler):
    timeout=.1
    def log_message(self,*args):pass

def test_incomplete_request_returns_408():
    server=ThreadingHTTPServer(('127.0.0.1',0),ShortTimeoutHandler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with socket.create_connection(server.server_address,timeout=2) as connection:
            connection.sendall(b'POST /api/run HTTP/1.0\r\nContent-Type: application/json\r\nContent-Length: 10\r\n\r\n{')
            response=http.client.HTTPResponse(connection);response.begin()
            assert response.status==408
    finally:server.shutdown();server.server_close();thread.join()
