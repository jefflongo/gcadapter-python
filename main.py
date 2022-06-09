from __future__ import annotations

from serial_interface import SerialInterface, GCControllerStatus
import time


POLL_RATE_HZ = 1

si = SerialInterface()
origins: list[GCControllerStatus] = [
    GCControllerStatus(),
    GCControllerStatus(),
    GCControllerStatus(),
    GCControllerStatus(),
]

while True:
    for chan in range(4):
        status: GCControllerStatus = si.get_status(chan)
        if status.get_origin:
            origins[chan] = si.get_origin(chan)

    time.sleep(1 / POLL_RATE_HZ)
