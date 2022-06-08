import threading
import time
import sys

from gcadapter import GCAdapter, GCControllerStatus

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
    adapter.stop_polling()
    ret = adapter.get_origins()
    adapter.start_polling()
    adapter.get_status()
    time.sleep(1 / POLL_RATE_HZ)
