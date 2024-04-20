from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import socket
from datetime import datetime
import json
import threading
import os


UDP_IP = '127.0.0.1'
UDP_PORT = 5000

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path).path
        print(pr_url)
        if pr_url == '/':
            self.send_html_file('index.html')
        elif pr_url == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url[1:]).exists():
                self.send_static()
            else:                
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        send_to_socket(data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, file_name, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(file_name, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as f:
            self.wfile.write(f.read())


def send_to_socket(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (UDP_IP, UDP_PORT))
    sock.close()

def append_to_json(file_path, new_data):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump({}, file)

    with open(file_path, 'r+') as file:
        try:
            data = json.load(file)
        except json.decoder.JSONDecodeError:
            data = {}

        data.update(new_data)
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()


def run_socket(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, _ = sock.recvfrom(1024)
            decoded_data = data.decode()
            data_dict = {key: value for key, value in [el.split('=') for el in decoded_data.split('&')]}
            formatted_data = {str(datetime.now()): data_dict}
            append_to_json('storage/data.json', formatted_data)

    except KeyboardInterrupt:
        print("Closing socket")

    finally:
        sock.close()

def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    http_server_thread = threading.Thread(target=run_http_server)
    socket_thread = threading.Thread(target=run_socket,args=(UDP_IP,UDP_PORT))
    
    http_server_thread.start()
    socket_thread.start()

    http_server_thread.join()
    socket_thread.join()
