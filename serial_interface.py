from __future__ import annotations

import threading
import time

from gcadapter import GCAdapter, GCControllerStatus


class SerialInterface:
    def __init__(self):
        self.statuses: list[GCControllerStatus] = []
        self.origins: list[GCControllerStatus] = []
        self.rumble = [False, False, False, False]
        self.rumble_needs_update = threading.Event()

        try:
            self.adapter = GCAdapter()
        except IOError:
            raise

        self.adapter.start_polling()

        self.poll_thread = threading.Thread(target=self._poll).start()
        self.rumble_thread = threading.Thread(target=self._update_rumble).start()

    def _poll(self) -> None:
        while True:
            self.statuses = self.adapter.get_status()
            # yield
            time.sleep(0)

    def _update_rumble(self) -> None:
        self.rumble_needs_update.wait()
        self.adapter.set_rumble(*self.rumble)

    def get_origin(self, chan: int) -> GCControllerStatus:
        return self.origins[chan]

    def get_status(self, chan: int) -> GCControllerStatus:
        return self.statuses[chan]

    def set_rumble(self, chan: int, value: bool) -> None:
        self.rumble[chan] = value
        self.rumble_needs_update.set()
