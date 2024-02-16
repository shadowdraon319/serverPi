#!/usr/bin/env python3

import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import grovepi
import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# GrovePi setup
led = 5  # LED connected to D5
grovepi.pinMode(led, "OUTPUT")

host_name = '10.2.8.225'  # IP Address of Raspberry Pi
host_port = 8000

# Initialize variables to track LED state and time
led_state = False
start_time = 0
duration = 0  # Duration for which the LED was on

# InfluxDB Configuration
token = os.environ.get("INFLUXDB_TOKEN")
org = "sabresmedia"
bucket = "freedomDemo"
url = "http://10.2.8.225:8086"

# Setup InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

def log_led_state(state, duration=0.0):
    """
    Log the LED state ('on' or 'off') and duration to InfluxDB as a float for accuracy.
    
    :param state: The state of the LED ('on' or 'off').
    :param duration: The duration for which the LED was on, in seconds, as a float.
    """
    try:
        # Convert state to an appropriate format for InfluxDB
        state_value = 1 if state == 'on' else 0  # Ensuring data type consistency
        
        print(f"Attempting to log LED state: {state}, Duration: {duration}")
        
        # Creating the data point
        point = Point("led_state") \
            .tag("device", "raspberrypi") \
            .field("state", state_value) \
            .field("duration", float(duration)) \
            .time(time.time_ns(), WritePrecision.NS)
        
        # Writing the data point to InfluxDB
        write_api.write(bucket=bucket, org=org, record=point)
        
        print("LED state logged successfully.")
        
    except Exception as e:
        print(f"Failed to log LED state: {e}")

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
        global duration
        html = f'''
           <html>
           <body style="width:960px; margin: 20px auto;">
           <h1>Welcome to my Raspberry Pi</h1>
           <p>Current GPU temperature is {getTemperature()[5:]}</p>
           <p>LED was on for {duration} seconds.</p>
           <form action="/" method="POST">
               Turn LED :
               <input type="submit" name="submit" value="On">
               <input type="submit" name="submit" value="Off">
           </form>
           </body>
           </html>
        '''
        self.do_HEAD()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        global led_state, start_time, duration
        content_length = int(self.headers['Content-Length'])  # Gets the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")  # Gets the data itself
        post_data = post_data.split("=")[1]  # Parses the data

        if post_data == 'On' and not led_state:
            led_state = True
            start_time = time.time()
            grovepi.digitalWrite(led, 1)  # Turn LED on
            log_led_state("on")  # Log LED state as on
        elif post_data == 'Off' and led_state:
            led_state = False
            end_time = time.time()
            duration = round(end_time - start_time, 2)  # Calculate duration in seconds
            grovepi.digitalWrite(led, 0)  # Turn LED off
            log_led_state("off", duration)  # Log LED state as off and duration

        print(f"LED is {post_data}")
        print(f"LED was on for {duration} seconds.") if duration else print("")
        self._redirect('/')  # Redirect back to the root url

# Main
if __name__ == '__main__':
    http_server = HTTPServer((host_name, host_port), MyServer)
    print("Server Starts - %s:%s" % (host_name, host_port))

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
