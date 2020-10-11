import numpy as np
import RPi.GPIO as GPIO
from time import sleep
import lcddriver, threading, gps
import pprint

display = lcddriver.lcd()

zero_coords = np.array([0,0])
gps_log = [[0,0,0]]

# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)



def log_coords():
   global gps_log
   while True:
       
       try:
           report = session.next()
           # print(report)
           if report['class'] == 'TPV':
               if hasattr(report, 'time'):
                   timestamp = report.time
               if hasattr(report, 'lat'):
                   lat = round(report.lat, 6)
#                    display.lcd_display_string(f'lat: {lat}', 1)
               if hasattr(report, 'lon'):
                   lon = round(report.lon, 6)
#                    display.lcd_display_string(f'lon: {lon}', 2)
                   gps_log.append([timestamp, lat, lon])
       except KeyError:
           pass
        
def button_callback(channel):
    global zero_coords
    display.lcd_clear()
    zero_coords = np.array([gps_log[-1][1], gps_log[-1][2]])
    

def measure_distance(zero_coords, cur_coords):
    delta = cur_coords - zero_coords # units: degrees
    degrees_to_meters_conversion = np.array([111190, 74625]) #only at lattitudes near everett.
    delta_m = delta * degrees_to_meters_conversion # units: meters
    distance = np.hypot(delta_m[0], delta_m[1]) 
    return(distance)


thread_object = threading.Thread(target=log_coords)
thread_object.start()

print('GPS log thread started.')
# sleep(5)
# print('Five. Seconds. Later.')

GPIO.add_event_detect(25, GPIO.FALLING, callback = button_callback)

while True:
    cur_coords = np.array([gps_log[-1][1], gps_log[-1][2]])
    distance = (measure_distance(zero_coords, cur_coords))
    display.lcd_display_string(f'{int(distance)} m {int(distance % 1 * 100)} cm        ', 1)
    sleep(.5)

# thread_object.join()
# print('All finished')
# pprint.pprint(gps_log)
#display.lcd_clear()
message = input('press enter to quit.\n')

GPIO.cleanup()
