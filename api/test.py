from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {
            'message': 'Hello from Python function!',
            'status': 'working',
            'method': 'GET'
        }
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {
            'message': 'Hello from Python function!',
            'status': 'working',
            'method': 'POST'
        }
        self.wfile.write(json.dumps(response).encode())
