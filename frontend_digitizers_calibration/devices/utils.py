import numpy

from frontend_digitizers_calibration import config

SUFFIX_CHANNEL_DATA_SUM = "DATA-SUM"
SUFFIX_CHANNEL_BG_DATA_SUM = "BG-DATA-SUM"
SUFFIX_CHANNEL_DATA_CALIBRATED = "DATA-CALIBRATED"
SUFFIX_CHANNEL_BG_DATA_CALIBRATED = "BG-DATA-CALIBRATED"
SUFFIX_DEVICE_INTENSITY = "INTENSITY-CAL"
SUFFIX_DEVICE_XPOS = "XPOS"
SUFFIX_DEVICE_YPOS = "YPOS"


def calibrate_channel(message, data_to_send, pv_prefix, channel_number, pv_names, calibration_data):

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


def calculate_intensity_and_position(message, data_to_send, channel_names, device_name, device_definition):

    x_scaling_offset = device_definition["x_scaling_offset"]
    y_scaling_offset = device_definition["y_scaling_offset"]
    x_scaling_factor = device_definition["x_scaling_factor"]
    y_scaling_factor = device_definition["y_scaling_factor"]

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
