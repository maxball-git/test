from abc import ABCMeta, abstractmethod
import subprocess
import shlex
import re
import time


class AbstractBLOCKDEV(object):
    __metaclass__ = ABCMeta

    def __init__(self, args):
        self.argument = args.device

    def execute(self):
        if self.argument is None:
            self.show_devices(self.get_devices())
        else:
            devices = self.get_devices()
            if len(devices) >= self.argument:
                devices = filter(lambda d: int(d.get('index', '1')) == self.argument, devices)
                if len(devices) > 0:
                    device = dict(devices[0])  # PEP8
                    partitions = self.get_partitions(device)
                    self.show_partitions(device, partitions)
            else:
                raise Exception('Index out of range')

    @staticmethod
    def show_partitions(device, partitions):
        """write partition list to stdout"""
        print('{0}. Device: {1}, Size: {2}'.format(
            int(device.get('index')),
            device.get('name', 'n/a'),
            format_size(device.get('size', 0))))
        for part in partitions:
            print('   Partition: {0}, Size: {1}'.format(part.get('name', 'n/a'), format_size(part.get('size', 0))))

    @staticmethod
    def show_devices(devices):
        """write devices list to stdout"""
        for dev in devices:
            print('{0}. Device: {1}, Size: {2}'.format(
                int(dev.get('index')),
                dev.get('name', 'n/a'),
                format_size(dev.get('size', 0))))

    @abstractmethod
    def get_devices(self):
        """get devices list"""
        # This fields are required
        return list({"name": "n/a", "size": 0, 'index': 1})

    @abstractmethod
    def get_partitions(self, device):
        """get partition list"""
        # This fields are required
        return list({"name": "n/a", "size": 0})


size_names = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]


def format_size(num, suffix='B'):
    if isinstance(num, int):
        for unit in size_names:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Yi', suffix)
    else:
        return num


class NixDevices(AbstractBLOCKDEV):
    @staticmethod
    def key_value_to_dict(text, start_index=None):
        si = start_index and start_index or 0
        r = [dict(token.split('=') for token in shlex.split(s.lower() +
                                                            (start_index and ' index={}'.format(i) or '')))
             for i, s in enumerate(text, start=si)]

        for i in r:
            if i.get('size'):
                try:
                    i['size'] = int(i['size'])
                except ValueError:
                    pass
        return r

    def get_devices(self):
        out = subprocess.check_output(["lsblk", "-dbPp"]).strip().split('\n')
        devices = self.key_value_to_dict(out, 1)
        devices = filter(lambda x: x.get('type') == 'disk', devices)
        return devices

    def get_partitions(self, device):
        """get partition list"""
        out = subprocess.check_output(["lsblk", "-bPp", device['name']]).strip().split('\n')
        partitions = self.key_value_to_dict(out)
        partitions = filter(lambda x: x.get('type') == 'part', partitions)
        return partitions


AbstractBLOCKDEV.register(NixDevices)


class WinDevices(AbstractBLOCKDEV):
    @staticmethod
    def out_normalization(txt):
        text = txt.split('\n')
        while not str(text[0]).strip().startswith('-'):
            text.__delitem__(0)
        text = text[0:text.index(u'')]
        shift = len(text[0].partition('-')[0])
        cols_widths = [len(x) for x in text[0].split()]
        sum_col = 0
        cols = list()
        for i, col in enumerate(cols_widths,0):
            sum_col += shift
            cols.append({'start': sum_col, 'end': sum_col+col})
            sum_col += col
        text.__delitem__(0)
        text = [{'name': s[cols[0]['start']: cols[0]['end']].strip(),
                 'info': s[cols[1]['start']: cols[1]['end']].strip(),
                 'size': s[cols[2]['start']: cols[2]['end']].strip(),
                 'index': i
                 }
                for i, s in enumerate(text, start=1) if s]
        return text

    def get_devices(self):
        """get devices list"""
        p = subprocess.Popen(["diskpart"],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        out = p.communicate(input=b'list disk\nexit')[0].decode()
        devices = self.out_normalization(out)
        return devices

    def get_partitions(self, device):
        """get partition list"""
        p = subprocess.Popen(["diskpart"],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        s = b'select disk {}'.format(device['name'].split()[1].strip())
        out = p.communicate(input=b'select disk 0\nlist partition\nexit')[0].decode()
        partitions = self.out_normalization(out)
        return partitions


AbstractBLOCKDEV.register(WinDevices)


class OsXDevices(AbstractBLOCKDEV):
    def get_devices(self):
        """get devices list"""
        out = subprocess.check_output(['diskutil', 'list']).strip().splitlines()
        devices = list()
        i = 1
        name = ''
        index = 0
        for s in out:
            if str(s).startswith('/'):
                index = i
                name = s.strip()
                i += 1
            if str(s).find('*') > 0:
                t = str(s).split('*')[1].split(' ')
                size = t[0] + ' ' + t[1]
                devices.append({'name': name, 'size': size, 'index': index})
        return devices

    def get_partitions(self, device):
        """get partition list"""
        out = subprocess.check_output(['diskutil', 'list'])
        partitions = list()
        out = out.partition(device.get('name'))[2]
        out = out.split('/')[0].strip().splitlines()
        out.__delitem__(0)

        for s in out:
            name = re.search("\s+\d+:(.*) [*\d.]", s).group(1).strip()
            size = re.search("(\d+\.\d+\s*\w*)", s).group(1)
            partitions.append({'name': name, 'size': size})
        return partitions


AbstractBLOCKDEV.register(OsXDevices)


class JvaDevices(AbstractBLOCKDEV):
    def get_devices(self):
        """get devices list"""
        raise Exception('Not applied on this environment')

    def get_partitions(self, argument):
        """get partition list"""
        raise Exception('Not applied on this environment')


AbstractBLOCKDEV.register(JvaDevices)
