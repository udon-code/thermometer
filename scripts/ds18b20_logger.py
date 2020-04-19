#!/usr/bin/python3
""" DS18B20 Sensor Logger

This logger server has following features
 - Can handle multiple sensors
 - Logging to a local file
 - Sending a measured data via UDP
"""

import argparse
from datetime import datetime
import os
import pprint
import re
import socket
import struct
import sys
import time
import random

from ds18b20_common import SensorDataBase


class Ds18b20(SensorDataBase):
    DEVICE_PATH_ROOT = os.path.join(
        '/', 'sys', 'bus', 'w1', 'devices')

    NETWORK_TEST = False

    @classmethod
    def find_device(cls, device_list):
        if cls.NETWORK_TEST:
            return ['/sys/bus/w1/devices/28-123456789ABCDE',
                    '/sys/bus/w1/devices/28-123456789ABCDF']

        devices = []
        if len(device_list) == 0:  # find all 28- device
            devices.extend([os.path.join(cls.DEVICE_PATH_ROOT, k) for k in
                            filter(lambda x: x[0:3] == '28-',
                                   os.listdir(cls.DEVICE_PATH_ROOT))])
        else:
            for device in device_list:
                if device[0] != '/':
                    devices.append(os.path.join(cls.DEVICE_PATH_ROOT,
                                                device))
                else:
                    devices.append(device)

        assert len(devices) > 0, "Cannot find w1 devices"

        for device in devices:
            assert (os.path.isdir(device)), f'Cannot find {device}'

        return devices

    def __init__(self, device_path):
        self.id = os.path.basename(device_path)
        self.path = device_path
        super().__init__(name_=self.id,
                         uid_=int(re.sub('\-', '', self.id), base=16),
                         type_='Thermometer',
                         index_=0)

    def read(self):
        if self.NETWORK_TEST:
            return float(random.randint(0, 50))

        with open(os.path.join(self.path, 'w1_slave'), 'r') as f:
            lines = f.readlines()

        assert len(lines) == 2
        m = re.search('t=(\-{0,1}\d+)', lines[1])
        if m:
            return float(m.group(1)) / 1000
        return None

    def update_message(self, value=None):
        if value is None:
            value = self.read()

        self.sensor_msg.index = self.sensor_msg.index + 1
        self.sensor_msg.ClearField('value')
        self.sensor_msg.value.append(value)
        self.sensor_msg.timestamp_us = int(time.time() * 1000000)

    def sensor_message(self, value=None):
        return self.sensor_msg

    def print_value(self, value=None):
        if value is None:
            value = self.read()
        return f'[{datetime.now()}] ({self.id:20}): {value:.3f}'


def sudo_init():
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')


def start_sensing(w1_devices, args):
    print("Start DS18B20 logging ... ")
    txt_out = None
    udp_out = None
    udp_message = None

    if args.output:
        txt_out = open(args.output, 'w')
        print(f"Output result to '{args.output}'")

    if args.udp:
        udp_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if args.udp_ip == '<broadcast>':
            udp_out.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print(f"Send result to {args.udp_ip}::{args.udp_port}")

    start_time = time.perf_counter()
    while True:
        loop_start = time.perf_counter()

        for device in w1_devices.values():
            device.update_message()

            if txt_out:
                txt_out.write(device.new_csv_line() + '\n')
                txt_out.flush()
            else:
                print(device.new_csv_line())

            if udp_out:
                udp_out.sendto(device.sensor_msg.SerializeToString(),
                               (args.udp_ip, args.udp_port))

        if ((args.time > 0) and
                (time.perf_counter() - start_time) > args.time):
            break
        else:
            time.sleep(max(0, args.interval - (time.perf_counter() - loop_start)))


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m', '--modprobe',
                        help='modprobe w1-gpio/w1-therm',
                        action='store_true',
                        default=False)
    parser.add_argument('-t', '--time',
                        help='Set logging time (-1: no timeout)',
                        action='store',
                        default=0.1,
                        type=float,
                        metavar='seconds')
    parser.add_argument('-i', '--interval',
                        help='Sampling Time',
                        action='store',
                        default=1,
                        type=int,
                        metavar='seconds')
    parser.add_argument('-o', '--output',
                        help='Text file to be dumpped',
                        action='store',
                        metavar='text_file')
    parser.add_argument('-u', '--udp',
                        help='Enable UDP output',
                        action='store_true')
    parser.add_argument('--udp_ip', action='store',
                        help='UDP destination IP',
                        default='<broadcast>',
                        metavar='IP')
    parser.add_argument('--udp_port', action='store',
                        help='UDP destination port',
                        type=int,
                        default=28012,
                        metavar='Port')
    parser.add_argument('-d', '--device',
                        action='append',
                        default=[],
                        help='DS18B20 ID(s). Find all device descriptors if omitted')
    parser.add_argument('--network_test',
                        help='Run in network test mode',
                        action='store_true')

    args = parser.parse_args()

    if args.modprobe:
        sudo_init()

    if args.network_test:
        Ds18b20.NETWORK_TEST = True

    device_list = Ds18b20.find_device(args.device)
    w1_devices = {os.path.basename(k): Ds18b20(k) for k in device_list}
    print("Found %d DS18B20 devices" % (len(w1_devices)))
    pprint.pprint(list(w1_devices.keys()))

    start_sensing(w1_devices, args)


if __name__ == "__main__":
    main()
