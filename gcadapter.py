import usb.core
import usb.util

import sys


class GCAdapter:
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
                sys.exit("Could not detach kernel driver: %s" % str(e))
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
        self.out_ep.write([0x13])

    def stop_polling(self) -> None:
        self.out_ep.write([0x14])
        return self.in_ep.read(self.in_ep.wMaxPacketSize)

    def get_origins(self):
        self.out_ep.write([0x12])
        return self.in_ep.read(self.in_ep.wMaxPacketSize)

    def get_status(self):
        return self.in_ep.read(self.in_ep.wMaxPacketSize)


if __name__ == "__main__":
    import time

    adapter = GCAdapter()
    adapter.start_polling()
    time.sleep(1)
    adapter.get_status()
    time.sleep(1)
    ret = adapter.stop_polling()
    ret = adapter.get_origins()
