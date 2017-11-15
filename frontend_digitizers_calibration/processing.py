from collections import deque

import numpy

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.utils import load_calibration_data, notify_epics, append_message_data

# Suffixes to use for appending calculated data.
SUFFIX_CHANNEL_DATA_SUM = "-DATA-SUM"
SUFFIX_CHANNEL_BG_DATA_SUM = "-BG-DATA-SUM"
SUFFIX_CHANNEL_DATA_CALIBRATED = "-DATA-CALIBRATED"
SUFFIX_CHANNEL_BG_DATA_CALIBRATED = "-BG-DATA-CALIBRATED"
SUFFIX_DEVICE_INTENSITY = "INTENSITY-CAL"
SUFFIX_DEVICE_XPOS = "XPOS"
SUFFIX_DEVICE_YPOS = "YPOS"


def process_single_channel(message, data_to_send, pv_prefix, channel_number, pv_names, calibration_data):

    # Read from bsread message.
    data = message.data.data[pv_names[config.CONFIG_CHANNEL_ORDER_DATA]].value
    background = message.data.data[pv_names[config.CONFIG_CHANNEL_ORDER_BG_DATA]].value
    data_trigger_cell = message.data.data[pv_names[config.CONFIG_CHANNEL_ORDER_DATA_TRIG]].value
    background_trigger_cell = message.data.data[pv_names[config.CONFIG_CHANNEL_ORDER_BG_DATA_TRIG]].value

    # Offset and scale
    background = (background.astype(numpy.float32) - 0x800) / 4096
    data = (data.astype(numpy.float32) - 0x800) / 4096

    # Calibrate
    background = calibration_data.calibrate(background, background_trigger_cell, channel_number)
    data = calibration_data.calibrate(data, data_trigger_cell, channel_number)

    # background subtraction
    data -= background

    # integration
    data_sum = data.sum()
    background_sum = background.sum()

    data_to_send[pv_prefix + SUFFIX_CHANNEL_DATA_SUM] = data_sum
    data_to_send[pv_prefix + SUFFIX_CHANNEL_BG_DATA_SUM] = background_sum
    data_to_send[pv_prefix + SUFFIX_CHANNEL_DATA_CALIBRATED] = data
    data_to_send[pv_prefix + SUFFIX_CHANNEL_BG_DATA_CALIBRATED] = background

    return data_to_send


def process_pbps(message, device_name, device_definition, channels_definition, sampling_frequency, frequency_files):
    calibration_data = load_calibration_data(sampling_frequency, frequency_files)

    data_to_send = {}

    x_scaling_offset = device_definition["x_scaling_offset"]
    y_scaling_offset = device_definition["y_scaling_offset"]
    x_scaling_factor = device_definition["x_scaling_factor"]
    y_scaling_factor = device_definition["y_scaling_factor"]

    for channel in channels_definition:
        pv_prefix = channel[config.CONFIG_CHANNEL_PV_PREFIX]
        channel_number = channel[config.CONFIG_CHANNEL_NUMBER]
        pv_names = channel[config.CONFIG_CHANNEL_PVS]

        process_single_channel(message=message,
                               data_to_send=data_to_send,
                               pv_prefix=pv_prefix,
                               channel_number=channel_number,
                               pv_names=pv_names,
                               calibration_data=calibration_data)

    # Retrieve the channel names in the correct order.
    channel_names = [channel[config.CONFIG_CHANNEL_PV_PREFIX] for channel in channels_definition]

    # intensity and position calculations
    channel1_sum = data_to_send[channel_names[0] + SUFFIX_CHANNEL_DATA_SUM]
    channel2_sum = data_to_send[channel_names[1] + SUFFIX_CHANNEL_DATA_SUM]
    channel3_sum = data_to_send[channel_names[2] + SUFFIX_CHANNEL_DATA_SUM]
    channel4_sum = data_to_send[channel_names[3] + SUFFIX_CHANNEL_DATA_SUM]

    intensity = (channel1_sum + channel2_sum + channel3_sum + channel4_sum) / 2
    intensity = abs(intensity)

    x_position = ((channel1_sum - channel2_sum) / (channel1_sum + channel2_sum))
    y_position = ((channel3_sum - channel4_sum) / (channel3_sum + channel4_sum))

    # Scaling.
    x_position = (x_position * x_scaling_factor) + x_scaling_offset
    y_position = (y_position * y_scaling_factor) + y_scaling_offset

    data_to_send[device_name + SUFFIX_DEVICE_INTENSITY] = intensity
    data_to_send[device_name + SUFFIX_DEVICE_XPOS] = x_position
    data_to_send[device_name + SUFFIX_DEVICE_YPOS] = y_position

    # Notify EPICS channels with the new calculated data.
    notify_epics(data_to_send)

    return data_to_send

pbpg_queue = deque(maxlen=240)


def process_pbpg(message, device_name, device_definition, channels_definition, sampling_frequency, frequency_files):
    calibration_data = load_calibration_data(sampling_frequency, frequency_files)
    keithley_intensity = device_definition["keithley_intensity"]

    data = []
    background = []

    data_to_send = {}

    x_scaling_offset = device_definition["x_scaling_offset"]
    y_scaling_offset = device_definition["y_scaling_offset"]
    x_scaling_factor = device_definition["x_scaling_factor"]
    y_scaling_factor = device_definition["y_scaling_factor"]

    for channel in channels_definition:
        pv_prefix = channel[config.CONFIG_CHANNEL_PV_PREFIX]
        channel_number = channel[config.CONFIG_CHANNEL_NUMBER]
        pv_names = channel[config.CONFIG_CHANNEL_PVS]

        process_single_channel(message=message,
                               data_to_send=data_to_send,
                               pv_prefix=pv_prefix,
                               channel_number=channel_number,
                               pv_names=pv_names)

        data.append(data_to_send[pv_prefix + SUFFIX_CHANNEL_DATA_CALIBRATED])
        background.append(data_to_send[pv_prefix + SUFFIX_CHANNEL_BG_DATA_CALIBRATED])

    # intensity and position calculations
    intensity = (data[0] + data[1] + data[2] + data[3]) / 2
    intensity = abs(intensity)

    x_position = ((((data[0] - data[1]) / (data[0] + data[1])) - (-0.2115)) / -0.0291) - 0.4
    y_position = ((((data[2] - data[3]) / (data[2] + data[3])) - (-0.1632)) / 0.0161) + 0.2

    data_to_send[device_name + SUFFIX_DEVICE_INTENSITY] = intensity
    data_to_send[device_name + SUFFIX_DEVICE_XPOS] = x_position
    data_to_send[device_name + SUFFIX_DEVICE_YPOS] = y_position

    pbpg_queue.append(intensity)
    # average last 240 intensities
    intensity_average = sum(pbpg_queue) / len(pbpg_queue)

    data_to_send['SARFE10-PBPG050:HAMP-INTENSITY-AVG'] = intensity_average

    intensity_cal = intensity * (keithley_intensity / intensity_average)
    data_to_send['SARFE10-PBPG050:HAMP-INTENSITY-CAL'] = intensity_cal

    return data_to_send


def process(message, devices, frequency_value_name, frequency_files):
    sampling_frequency = message.data.data[frequency_value_name].value

    for device_name, device_definition in devices.items():
        device_type = device_definition["device_type"]
        channels_definition = device_definition["channels"]

        data_to_send = process_pbps(message=message,
                                    device_name=device_name,
                                    device_definition=device_definition,
                                    channels_definition=channels_definition,
                                    sampling_frequency=sampling_frequency,
                                    frequency_files=frequency_files)

    # Append the data from the original message.
    append_message_data(message, data_to_send)

    return data_to_send
