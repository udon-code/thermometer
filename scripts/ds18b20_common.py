""" SensorData Common 
"""
from datetime import datetime
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "generated"))
import sensor_data_pb2


class SensorDataBase:
    MESSAGE_FORMAT = {
        'value': lambda x: f"{x[0]: .3f}",
        'timestamp_us': lambda x: str(datetime.fromtimestamp(x/1E6)),
    }

    MESSAGE_VALUE = {
        'HostTime': lambda x: datetime.fromisoformat(x),
        'value': lambda x: float(x),
        'timestamp_us': lambda x: datetime.fromisoformat(x),
    }

    def __init__(self, name_=None, uid_=None, type_=None, index_=None):
        self.sensor_msg = sensor_data_pb2.SensorData()

        if name_:
            self.sensor_msg.name = name_
        if uid_:
            self.sensor_msg.uid = uid_
        if type_:
            self.sensor_msg.type = sensor_data_pb2.SensorData.SensorType.Value(type_)
        if index_:
            self.sensor_msg.index = index_

        self.update_formatter()

    def update_formatter(self):
        """Add default fomatter for undefined field
        """
        for field in self.sensor_msg.DESCRIPTOR.fields:
            if field.name not in self.MESSAGE_FORMAT:
                self.MESSAGE_FORMAT[field.name] = lambda v: str(v)
            if field.name not in self.MESSAGE_VALUE:
                self.MESSAGE_VALUE[field.name] = lambda v: v

    def csv_header_elems(self):
        return ['HostTime'] + [k.name for k in self.sensor_msg.DESCRIPTOR.fields]

    def get_csv_header(self):
        return ', '.join(self.csv_header_elems())

    def new_csv_line(self):
        """Return a string for new csv line"""
        return ', '.join([str(datetime.now())] + [self.MESSAGE_FORMAT[k.name](v) for k, v in self.sensor_msg.ListFields()])

    def current_data(self):
        return [datetime.now()] + [v for _, v in self.sensor_msg.ListFields()]

    def read_input(self, path_list, sensors=None):
        result = {}
        name_idx = self.csv_header_elems().index('name')
        time_idx = self.csv_header_elems().index('HostTime')

        for path in path_list:
            f = open(path, 'r')
            fitr = iter(f.readlines())
            f.close()

            next(fitr)  # skip header
            for line in fitr:
                line_elems = [k.strip() for k in line.strip().split(',')]
                name = line_elems[name_idx]
                if sensors and name not in sensors:
                    continue
                if name not in result:
                    result[name] = {k: [] for k in self.csv_header_elems()}
                assert(len(line_elems) == len(self.csv_header_elems()))
                for idx, elem in enumerate(self.csv_header_elems()):
                    result[name][elem].append(self.MESSAGE_VALUE[elem](line_elems[idx]))

        return result

    def parse_data(self, data):
        self.sensor_msg.ParseFromString(data)
        new_data = self.current_data()
        name_idx = self.csv_header_elems().index('name')
        return (new_data[name_idx], new_data)
