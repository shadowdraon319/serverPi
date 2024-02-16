#!/usr/bin/env python3

import RPi.GPIO as GPIO
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import time

# InfluxDB Configuration
token = os.environ.get("INFLUXDB_TOKEN")
org = "sabresmedia"
bucket = "sabresmedia"
url = "http://10.2.8.225:8086"

# Setup InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)

def log_led_state(state):
    """
    Log the LED state to InfluxDB.
    """
    try:
        print(f"Attempting to log LED state: {state}")
        point = Point("led_state") \
            .tag("device", "raspberrypi") \
            .field("state", state) \
            .time(time.time_ns(), WritePrecision.NS)
        write_api.write(bucket=bucket, org=org, record=point)
        print("LED state logged successfully.")
    except Exception as e:
        print(f"Failed to log LED state: {e}")

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
           <h1>Welcome to my Raspberry Pi LED Controller</h1>
           <form action="/" method="POST">
               Turn LED:
               <input type="submit" name="submit" value="On">
               <input type="submit" name="submit" value="Off">
           </form>
           </body>
           </html>
        '''
        self.do_HEAD()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode("utf-8")
        post_data = post_data.split("=")[1]

        if post_data == 'On':
            GPIO.output(18, GPIO.HIGH)
            log_led_state(1)
        else:
            GPIO.output(18, GPIO.LOW)
            log_led_state(0)

        print(f"LED is {post_data}")
        self._redirect('/')  # Redirect back to the root url

if __name__ == '__main__':
    host_name = '10.2.8.225'  # Listen on all interfaces
    host_port = 8000

    http_server = HTTPServer((host_name, host_port), MyServer)
    print(f"Server Starts - {host_name}:{host_port}")

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass

    http_server.server_close()
    GPIO.cleanup()  # Clean up GPIO
    client.close()  # Close InfluxDB client
    print("Server Stopped.")
