import platform
import os_devices
OS_WIN = 0
OS_MAC = 1
OS_NIX = 2
OS_JVA = 3

OS_CLASS_MAP = {
                 OS_WIN: os_devices.WinDevices,
                 OS_MAC: os_devices.OsXDevices,
                 OS_NIX: os_devices.NixDevices,
                 OS_JVA: os_devices.JvaDevices,
                }


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class FabricBlockDev(object):
    __metaclass__ = Singleton
    issued_object = None
    _instance = None

    @staticmethod
    def os_type():
        return set(platform.win32_ver()[0]) and OS_WIN or (
                   set(platform.mac_ver()[0]) and OS_MAC or (
                       set(platform.libc_ver()[0]) and OS_NIX or (
                           set(platform.java_ver()[0]) and OS_JVA or
                           None
                       )))

    def build_object(self, args):
        if self.issued_object:
            return self.issued_object
        obj_class = OS_CLASS_MAP.get(self.os_type(), None)
        if obj_class:
            self.issued_object = obj_class(args)
            return self.issued_object
        else:
            raise Exception('No implemented in this OS')
