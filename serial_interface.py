from __future__ import annotations

import threading
import time

from gcadapter import GCAdapter, GCControllerStatus


class SerialInterface:
    def __init__(self):
        self.statuses: list[GCControllerStatus] = []
        self.origins: list[GCControllerStatus] = []

        try:
            self.adapter = GCAdapter()
        except IOError:
            raise

        self.adapter.start_polling()

        self.poll_thread = threading.Thread(target=self._poll).start()

    def _poll(self) -> None:
        while True:
            self.statuses = self.adapter.get_status()
            # yield
            time.sleep(0)

    def get_origin(self, chan: int) -> GCControllerStatus:
        return self.origins[chan]

    def get_status(self, chan: int) -> GCControllerStatus:
        return self.statuses[chan]
