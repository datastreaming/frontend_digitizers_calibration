import random

import numpy
from bsread.handlers.compact import Message, Value


class MockCalibrationData(object):
    @staticmethod
    def calibrate(data, trigger_cell, channel_number):
        return data


def mock_notify_epics(data):
    print(data)


def generate_test_message(n_channels):
    message = Message()
    message.data.data = {}

    for i in range(1, n_channels + 1):
        data_values = random.sample(list(range(1800, 2100))*20, 1024)
        background_data_values = random.sample(list(range(1900, 2000))*20, 1024)

        message.data.data["channel%d_prefix-DATA" % i] = Value(numpy.array(data_values, dtype=">i2"))
        message.data.data["channel%d_prefix-BG-DATA" % i] = Value(numpy.array(background_data_values, dtype=">i2"))
        message.data.data["channel%d_prefix-DRS_TC" % i] = Value(134)
        message.data.data["channel%d_prefix-BG-DRS_TC" % i] = Value(112)
        message.data.data["channel%d_prefix-WD-gain-RBa" % i] = Value(145)

    return message


def generate_test_channels_definition(n_channels):
    channels_definition = []
    for i in range(1, n_channels + 1):
        channels_definition.append({
            "pv_prefix": "channel%d_prefix" % i,
            "channel_number": i,
            "channel_pvs": ["channel%d_prefix-DATA" % i,
                            "channel%d_prefix-BG-DATA" % i,
                            "channel%d_prefix-DRS_TC" % i,
                            "channel%d_prefix-BG-DRS_TC" % i,
                            "channel%d_prefix-WD-gain-RBa" % i
                            ]
        })

    return channels_definition
