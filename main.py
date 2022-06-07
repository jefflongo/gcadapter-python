import threading
import time
import sys

from gcadapter import GCAdapter, GCControllerStatus, GCControllerOrigin

POLL_RATE_HZ = 1


def set_rumble(enable: bool) -> None:
    pass


def get_status() -> GCControllerStatus:
    pass


try:
    adapter = GCAdapter()
except IOError:
    sys.exit("Could not connect to adapter")

adapter.start_polling()

while True:

    time.sleep(1 / POLL_RATE_HZ)
