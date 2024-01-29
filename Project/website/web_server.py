from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading


EXIT_EVENT = threading.Event()

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Specify the custom path for your index.html file
        if self.path == '/':
            # Your custom logic to serve the index.html file
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Open and read the content of your index.html file
            with open('Project/website/index.html', 'rb') as file:
                content = file.read()

            # Send the content as the response
            self.wfile.write(content)
        else:
            # If the path doesn't match, fall back to the default behavior
            super().do_GET()

SERVER_ADDRESS = ('', 8765)
HTTPD = HTTPServer(SERVER_ADDRESS, CustomHandler)
HTTPD.timeout = 15

def run_threaded_web_server():
    while not EXIT_EVENT.is_set():
        print('Before handle request')
        HTTPD.handle_request()
        print('After handle request')

def web_server():
    flag = True
    web_thread = threading.Thread(target=run_threaded_web_server)
    web_thread.start()

    while flag:
        user_input = input()
        if user_input == 'exit':
            flag = False

    EXIT_EVENT.set()
    web_thread.join()

if __name__=='__main__':
    print('Starting the web server')
    web_server()
    print('Shutting down the web server')
