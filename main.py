from serial_interface import SerialInterface
import time


POLL_RATE_HZ = 1

si = SerialInterface()

while True:
    si.get_status()
    time.sleep(1 / POLL_RATE_HZ)
