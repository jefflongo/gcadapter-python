from typing import NamedTuple

import usb.core
import usb.util


class GCControllerOrigin(NamedTuple):
    STICK_DEFAULT_VALUE = 0x80

    a: bool = False
    b: bool = False
    x: bool = False
    y: bool = False
    start: bool = False
    d_left: bool = False
    d_right: bool = False
    d_down: bool = False
    d_up: bool = False
    z: bool = False
    r: bool = False
    l: bool = False

    joystick_x: int = STICK_DEFAULT_VALUE
    joystick_y: int = STICK_DEFAULT_VALUE
    c_stick_x: int = STICK_DEFAULT_VALUE
    c_stick_y: int = STICK_DEFAULT_VALUE
    l_analog: int = 0
    r_analog: int = 0


class GCControllerStatus(GCControllerOrigin):
    connected: bool = False

    use_origin: bool = False
    get_origin: bool = False
    err_stat: bool = False
    err_latch: bool = False


class GCAdapter:
    DEFAULT_TIMEOUT = 16

    def __init__(self):
        self.dev: usb.core.Device = usb.core.find(idVendor=0x057E, idProduct=0x0337)

        if self.dev is None:
            raise IOError("Could not find device")

        # adapter has one configuration descriptor - claim it
        if self.dev.is_kernel_driver_active(0):
            try:
                self.dev.detach_kernel_driver(0)
                print("kernel driver detached")
            except usb.core.USBError as e:
                raise IOError("Could not detach kernel driver: %s" % str(e)) from e
        self.dev.reset()
        self.dev.set_configuration()
        cfg: usb.core.Configuration = self.dev.get_active_configuration()

        # configuration has one interface descriptor - get it
        intf: usb.core.Interface = cfg[(0, 0)]

        # the interface descriptor exposes two endpoints - one for writing and one for reading
        # get a handle to both
        self.out_ep: usb.core.Endpoint = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_OUT,
        )

        self.in_ep: usb.core.Endpoint = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_IN,
        )

        if self.out_ep is None or self.in_ep is None:
            raise IOError("Could not find endpoints")

    def start_polling(self) -> None:
        self.out_ep.write([0x13], timeout=self.DEFAULT_TIMEOUT)

    def stop_polling(self) -> None:
        self.out_ep.write([0x14], timeout=self.DEFAULT_TIMEOUT)
        return self.in_ep.read(self.in_ep.wMaxPacketSize, timeout=self.DEFAULT_TIMEOUT)

    def get_origins(self):
        self.out_ep.write([0x12], timeout=self.DEFAULT_TIMEOUT)
        bytes = self.in_ep.read(self.in_ep.wMaxPacketSize, timeout=self.DEFAULT_TIMEOUT)
        origins = [
            GCControllerOrigin(),
            GCControllerOrigin(),
            GCControllerOrigin(),
            GCControllerOrigin(),
        ]
        for chan in range(4):
            origins[chan].joystick_x = bytes[1 + chan * 6]
            origins[chan].joystick_y = bytes[1 + chan * 6 + 1]
            origins[chan].c_stick_x = bytes[1 + chan * 6 + 2]
            origins[chan].c_stick_y = bytes[1 + chan * 6 + 3]
            origins[chan].l_analog = bytes[1 + chan * 6 + 4]
            origins[chan].r_analog = bytes[1 + chan * 6 + 5]

        return origins

    def get_status(self):
        bytes = self.in_ep.read(self.in_ep.wMaxPacketSize, timeout=self.DEFAULT_TIMEOUT)
        statuses = [
            GCControllerStatus(),
            GCControllerStatus(),
            GCControllerStatus(),
            GCControllerStatus(),
        ]
        for chan in range(4):
            buttons: int = bytes[(1 + 9 * chan + 1)] | bytes[(1 + 9 * chan + 1)] << 8
            statuses[chan].a = buttons & (1 << 0)
            statuses[chan].b = buttons & (1 << 1)
            statuses[chan].x = buttons & (1 << 2)
            statuses[chan].y = buttons & (1 << 3)
            statuses[chan].start = buttons & (1 << 4)
            statuses[chan].get_origin = buttons & (1 << 5)
            statuses[chan].err_latch = buttons & (1 << 6)
            statuses[chan].err_stat = buttons & (1 << 7)
            statuses[chan].d_left = buttons & (1 << 8)
            statuses[chan].d_right = buttons & (1 << 9)
            statuses[chan].d_down = buttons & (1 << 10)
            statuses[chan].d_up = buttons & (1 << 11)
            statuses[chan].z = buttons & (1 << 12)
            statuses[chan].r = buttons & (1 << 13)
            statuses[chan].l = buttons & (1 << 14)
            statuses[chan].use_origin = buttons & (1 << 15)
            statuses[chan].joystick_x = bytes[1 + 9 * chan + 3]
            statuses[chan].joystick_y = bytes[1 + 9 * chan + 3]
            statuses[chan].c_stick_x = bytes[1 + 9 * chan + 4]
            statuses[chan].c_stick_y = bytes[1 + 9 * chan + 5]
            statuses[chan].l_analog = bytes[1 + 9 * chan + 7]
            statuses[chan].r_analog = bytes[1 + 9 * chan + 8]

        return statuses

    def set_rumble(self, r1, r2, r3, r4) -> None:
        self.out_ep.write(
            [0x11, 1 if r1 else 0, 1 if r2 else 0, 1 if r3 else 0, 1 if r4 else 0]
        )


if __name__ == "__main__":
    import time

    adapter = GCAdapter()
    adapter.start_polling()
    time.sleep(1)
    adapter.get_status()
    time.sleep(1)
    ret = adapter.stop_polling()
    ret = adapter.get_origins()
