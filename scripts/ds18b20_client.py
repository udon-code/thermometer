#!/usr/bin/python3
""" DS18B20 Sensor Logger Client

This logger client has following features
 - Receive a protobuf UDP message from multiple logger
"""
import argparse
from datetime import datetime, date, timedelta
import os
import pprint
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import numpy as np
import re
import socket
import struct
import sys
import time

from ds18b20_common import SensorDataBase


class LoggerClient(SensorDataBase):
    def __init__(self, ip_addr='0.0.0.0', port=28012, csv=None, ifile=None,
                 sensors=None, plot=False, plot_by_date=False):
        super().__init__()
        self.rx_ip_addr = ip_addr
        self.port = port
        self.plot = plot or (ifile is not None and len(ifile) > 0)

        self.socket = None
        self.csv_of = None
        self.data = {}
        self.start_time = datetime(2038, 1, 1)
        self.end_time = datetime(1980, 1, 1)
        self.min_val = 10000   # large enough against temperature
        self.max_val = -10000  # small enough against temperature

        self.sensors = sensors
        self.plot_by_date = plot_by_date

        if ifile is not None and len(ifile) > 0:
            self.data = self.read_input(ifile, sensors)
            if plot_by_date:
                self.data = self.convert_to_plot_by_date(self.data)
        else:
            self.create_socket()
            if csv is not None:
                self.initialize_csv(csv)

    def create_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.rx_ip_addr, self.port))

    def start(self):
        if self.socket is None:
            self.create_fig()
            return

        if self.plot:
            self.create_fig()
        else:
            while True:
                self.receive_socket()

    def receive_socket(self):
        data, addr = self.socket.recvfrom(8192)
        name, new_data = self.parse_data(data)

        if name not in self.data:
            self.data[name] = {k: [] for k in self.csv_header_elems()}

        for idx, elem in enumerate(self.csv_header_elems()):
            self.data[name][elem].append(new_data[idx])

        self.min_val = min(self.min_val, self.sensor_msg.value[0])
        self.max_val = max(self.max_val, self.sensor_msg.value[0])

        if new_data[0] < self.start_time:
            self.start_time = new_data[0]
        if new_data[0] > self.end_time:
            self.end_time = new_data[0]

        if self.csv_of:
            self.output_csv()

        print(self.new_csv_line())

    def initialize_csv(self, csv_path):
        if os.path.exists(csv_path):
            print(f"[Warning] Overwrite existing file '{csv_path}'")

        self.csv_of = open(csv_path, 'w')
        self.csv_of.write(self.get_csv_header() + '\n')

    def output_csv(self):
        assert(self.csv_of is not None)
        new_line = self.new_csv_line()
        self.csv_of.write(new_line + '\n')
        self.csv_of.flush()

    def create_fig(self):
        self.fig, self.ax = plt.subplots()
        self.ln = {}

        self.ax.grid()
        if self.socket is not None:
            repeat = True
            frames = None
        else:
            repeat = False
            frames = []

        self.ani = FuncAnimation(self.fig, self.update_plot, frames=frames,
                                 init_func=self.init_fig, repeat=repeat)
        plt.show()

    def init_fig(self):
        """Initialize function for FuncAnimation class"""

        for sensor_name, sensor_data in self.data.items():
            self.ln[sensor_name], = self.ax.plot(sensor_data['HostTime'], sensor_data['value'], label=sensor_name)
            self.min_val = min([self.min_val] + sensor_data['value'])
            self.max_val = max([self.max_val] + sensor_data['value'])
            self.start_time = min([self.start_time] + sensor_data['HostTime'])
            self.end_time = max([self.end_time] + sensor_data['HostTime'])

        if len(self.data) > 0 and self.plot_by_date:
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

        self.ax.set_ylim(int(self.min_val-0.5), int(self.max_val+1.5))

        period = self.end_time - self.start_time

        self.ax.set_xlim(self.start_time - period*0.1, self.end_time + period*0.1)

        self.ax.legend()
        self.ax.figure.canvas.draw()

        return self.ln.values()

    def update_plot(self, frame):
        assert(self.socket is not None)
        self.receive_socket()

        delta = abs(self.max_val - self.min_val)
        self.ax.set_ylim(math.floor(self.min_val-delta*0.1), math.ceil(self.max_val+delta*0.1))
        period = self.end_time - self.start_time
        self.ax.set_xlim(self.start_time - period*0.1, self.end_time + period*0.1)

        for sensor_name, sensor_data in self.data.items():
            if sensor_name not in self.ln:
                self.ln[sensor_name], = self.ax.plot(sensor_data['HostTime'], sensor_data['value'], label=sensor_name)
                self.ax.legend()
            else:
                self.ln[sensor_name].set_data(sensor_data['HostTime'], sensor_data['value'])

        self.ax.figure.canvas.draw()

        return self.ln.values()

    def convert_to_plot_by_date(self, data):
        new_data = {}
        for sensor_name, sensor_data in data.items():
            for idx, host_time in enumerate(sensor_data['HostTime']):
                date_str = host_time.strftime('%Y-%m-%d')
                new_name = f'{sensor_name}_{date_str}'
                if new_name not in new_data:
                    new_data[new_name] = {k: [] for k in sensor_data.keys()}
                for k in sensor_data.keys():
                    if k == 'HostTime':
                        new_data[new_name][k].append(datetime.combine(date.today(), host_time.time()))
                    else:
                        new_data[new_name][k].append(sensor_data[k][idx])

        return new_data


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', action='append',
                        help='Read a recorded data instead of UDP (UDP option is disabled)',
                        default=[],
                        metavar='File')

    parser.add_argument('-p', '--plot', action='store_true',
                        help='Plot sensed values')
    parser.add_argument('--plot_by_date', action='store_true',
                        help='Plot by date')

    parser.add_argument('--csv', action='store',
                        help='Output to CSV file',
                        metavar='File')

    parser.add_argument('--udp_ip', action='store',
                        help='UDP destination IP (0.0.0.0 means any)',
                        default='0.0.0.0',
                        metavar='IP')
    parser.add_argument('--udp_port', action='store',
                        help='UDP destination port',
                        type=int,
                        default=28012,
                        metavar='Port')

    parser.add_argument('--sensors', action='append', default=None,
                        metavar='Name',
                        help='Use only specified sensor name')

    args = parser.parse_args()

    client = LoggerClient(ip_addr=args.udp_ip, port=args.udp_port,
                          csv=args.csv,
                          ifile=args.input,
                          sensors=args.sensors,
                          plot=args.plot,
                          plot_by_date=args.plot_by_date)

    client.start()


if __name__ == "__main__":
    main()
