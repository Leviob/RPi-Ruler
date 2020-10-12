#!/usr/bin/env python3

import numpy as np
import RPi.GPIO as GPIO
from time import sleep
import lcddriver
import threading
import gps
import pprint

display = lcddriver.lcd()
zero_coords = np.array([0, 0])
gps_log = [[0, 0, 0]]

# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

#RPi GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Save time and position data to gps_log
def log_coords():
    global gps_log
    while True:
        try:
            report = session.next()
            # print(report) # Includes all GPS Data
            if report['class'] == 'TPV':
                if hasattr(report, 'time'):
                    timestamp = report.time
                if hasattr(report, 'lat'):
                    lat = round(report.lat, 6)
                if hasattr(report, 'lon'):
                    lon = round(report.lon, 6)
                    gps_log.append([timestamp, lat, lon])
        except KeyError:
            pass

# on RPi button press, sets zero point to measure from. 
def button_callback(channel):
    global zero_coords
    display.lcd_clear()
    zero_coords = np.array([gps_log[-1][1], gps_log[-1][2]])

# Converts difference of degrees latitude and longitude to meters
def measure_distance(zero_coords, cur_coords):
    delta = cur_coords - zero_coords  # units: degrees
    degrees_to_meters_conversion = np.array([111190, 74625]) # only at latitudes near Seattle.
    delta_m = delta * degrees_to_meters_conversion  # units: meters
    distance = np.hypot(delta_m[0], delta_m[1])
    return(distance)

thread_object = threading.Thread(target=log_coords)
thread_object.start()
print('GPS log thread started.')

# Detect RPi button press
GPIO.add_event_detect(25, GPIO.FALLING, callback=button_callback)

# Update distance constantly
while True:
    cur_coords = np.array([gps_log[-1][1], gps_log[-1][2]])
    distance = (measure_distance(zero_coords, cur_coords))
    # Displays distance in meters and cm with padding.
    display.lcd_display_string(
        f'{str(int(distance)).rjust(4, " ")} m {str(int(distance % 1 * 100)).rjust(2, " ")} cm        ', 1)
    sleep(.5)
