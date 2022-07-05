from __future__ import annotations

import usb.core
import usb.util


class GCControllerStatus:
    STICK_DEFAULT_VALUE = 0x80
    SHOULDER_DEFAULT_VALUE = 0

    def __init__(self):
        self.connected: bool = False
        self.get_origin: bool = False

        self.a: bool = False
        self.b: bool = False
        self.x: bool = False
        self.y: bool = False
        self.start: bool = False
        self.d_left: bool = False
        self.d_right: bool = False
        self.d_down: bool = False
        self.d_up: bool = False
        self.z: bool = False
        self.r: bool = False
        self.l: bool = False

        self.joystick_x: int = self.STICK_DEFAULT_VALUE
        self.joystick_y: int = self.STICK_DEFAULT_VALUE
        self.c_stick_x: int = self.STICK_DEFAULT_VALUE
        self.c_stick_y: int = self.STICK_DEFAULT_VALUE
        self.l_analog: int = self.SHOULDER_DEFAULT_VALUE
        self.r_analog: int = self.SHOULDER_DEFAULT_VALUE


class GCAdapter:
    MAX_CONTROLLERS = 4
    DEFAULT_TIMEOUT = 16

    def __init__(self):
        self.polling = False
        self.dev: usb.core.Device = usb.core.find(idVendor=0x057E, idProduct=0x0337)

        if self.dev is None:
            raise IOError("Could not find device")

        # adapter has one configuration descriptor - claim it
        if self.dev.is_kernel_driver_active(0):
            try:
                self.dev.detach_kernel_driver(0)
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
        if self.out_ep.write([0x13], timeout=self.DEFAULT_TIMEOUT) != 1:
            raise IOError

        self.polling = True

    def stop_polling(self) -> None:
        if self.out_ep.write([0x14], timeout=self.DEFAULT_TIMEOUT) != 1:
            raise IOError

        bytes = self.in_ep.read(self.in_ep.wMaxPacketSize, timeout=self.DEFAULT_TIMEOUT)
        if (len(bytes)) != 2 or bytes[0] != 0x24:
            raise IOError

        self.polling = False

    def get_origins(self) -> list[GCControllerStatus]:
        polling: bool = self.polling
        self.stop_polling()

        if self.out_ep.write([0x12], timeout=self.DEFAULT_TIMEOUT) != 1:
            raise IOError

        bytes = self.in_ep.read(self.in_ep.wMaxPacketSize, timeout=self.DEFAULT_TIMEOUT)
        if len(bytes) != 25 or bytes[0] != 0x22:
            raise IOError

        if polling:
            self.start_polling()

        origins = [
            GCControllerStatus(),
            GCControllerStatus(),
            GCControllerStatus(),
            GCControllerStatus(),
        ]
        for chan in range(self.MAX_CONTROLLERS):
            origins[chan].joystick_x = bytes[1 + (chan * 6)]
            origins[chan].joystick_y = bytes[1 + (chan * 6) + 1]
            origins[chan].c_stick_x = bytes[1 + (chan * 6) + 2]
            origins[chan].c_stick_y = bytes[1 + (chan * 6) + 3]
            origins[chan].l_analog = bytes[1 + (chan * 6) + 4]
            origins[chan].r_analog = bytes[1 + (chan * 6) + 5]

        return origins

    def get_status(self) -> list[GCControllerStatus]:
        bytes = self.in_ep.read(self.in_ep.wMaxPacketSize, timeout=self.DEFAULT_TIMEOUT)
        if len(bytes) != self.in_ep.wMaxPacketSize or bytes[0] != 0x21:
            raise IOError

        statuses = [
            GCControllerStatus(),
            GCControllerStatus(),
            GCControllerStatus(),
            GCControllerStatus(),
        ]
        for chan in range(self.MAX_CONTROLLERS):
            statuses[chan].connected = ((bytes[1 + (9 * chan)] >> 4) & 0x03) > 0

            buttons: int = (
                bytes[(1 + (9 * chan) + 1)] | bytes[(1 + (9 * chan) + 2)] << 8
            )
            statuses[chan].a = (buttons & (1 << 0)) != 0
            statuses[chan].b = (buttons & (1 << 1)) != 0
            statuses[chan].x = (buttons & (1 << 2)) != 0
            statuses[chan].y = (buttons & (1 << 3)) != 0
            statuses[chan].d_left = (buttons & (1 << 4)) != 0
            statuses[chan].d_right = (buttons & (1 << 5)) != 0
            statuses[chan].d_down = (buttons & (1 << 6)) != 0
            statuses[chan].d_up = (buttons & (1 << 7)) != 0
            statuses[chan].start = (buttons & (1 << 8)) != 0
            statuses[chan].z = (buttons & (1 << 9)) != 0
            statuses[chan].r = (buttons & (1 << 10)) != 0
            statuses[chan].l = (buttons & (1 << 11)) != 0

            statuses[chan].joystick_x = bytes[1 + (9 * chan) + 3]
            statuses[chan].joystick_y = bytes[1 + (9 * chan) + 4]
            statuses[chan].c_stick_x = bytes[1 + (9 * chan) + 5]
            statuses[chan].c_stick_y = bytes[1 + (9 * chan) + 6]
            statuses[chan].l_analog = bytes[1 + (9 * chan) + 7]
            statuses[chan].r_analog = bytes[1 + (9 * chan) + 8]

        return statuses

    def set_rumble(self, r1: bool, r2: bool, r3: bool, r4: bool) -> None:
        if (
            self.out_ep.write(
                [0x11, 1 if r1 else 0, 1 if r2 else 0, 1 if r3 else 0, 1 if r4 else 0]
            )
            != 1
        ):
            raise IOError
