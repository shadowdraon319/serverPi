#!/usr/bin/env python3

import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import grovepi

# GrovePi setup
led = 5  # LED connected to D5
grovepi.pinMode(led, "OUTPUT")

host_name = '10.0.0.184'  # IP Address of Raspberry Pi
host_port = 8000

def getTemperature():
    temp = os.popen("/opt/vc/bin/vcgencmd measure_temp").read()
    return temp

class MyServer(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def do_GET(self):
        html = '''
           <html>
           <body style="width:960px; margin: 20px auto;">
           <h1>Welcome to my Raspberry Pi</h1>
           <p>Current GPU temperature is {}</p>
           <form action="/" method="POST">
               Turn LED :
               <input type="submit" name="submit" value="On">
               <input type="submit" name="submit" value="Off">
           </form>
           </body>
           </html>
        '''
        temp = getTemperature()
        self.do_HEAD()
        self.wfile.write(html.format(temp[5:]).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # Gets the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")  # Gets the data itself
        post_data = post_data.split("=")[1]  # Parses the data

        if post_data == 'On':
            grovepi.digitalWrite(led, 1)  # Turn LED on
        else:
            grovepi.digitalWrite(led, 0)  # Turn LED off

        print("LED is {}".format(post_data))
        self._redirect('/')  # Redirect back to the root url

# Main
if __name__ == '__main__':
    http_server = HTTPServer((host_name, host_port), MyServer)
    print("Server Starts - %s:%s" % (host_name, host_port))

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
