# Complete project details at https://RandomNerdTutorials.com

import time
from umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import network
import esp
esp.osdebug(None)
import gc
gc.collect()

ssid = 'your ssid'
password = 'your passphrase'
mqtt_server = 'your broker ip address'

client_id = ubinascii.hexlify(machine.unique_id())
topic_sub = b'notification'
topic_pub = b'SQM'
topic_pub_time = b'DateTime'

last_message = 0
message_interval = 5

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
    print(".", end="")
    time.sleep(1)

print('Connection successful')
print(station.ifconfig())

from ntptime import settime
settime()



