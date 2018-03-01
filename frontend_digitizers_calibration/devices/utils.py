import numpy

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.smooth_minmax import find_minmax

SUFFIX_CHANNEL_DATA_SUM = "-DATA-SUM"
SUFFIX_CHANNEL_BG_DATA_SUM = "-BG-DATA-SUM"
SUFFIX_CHANNEL_DATA_CALIBRATED = "-DATA-CALIBRATED"
SUFFIX_CHANNEL_BG_DATA_CALIBRATED = "-BG-DATA-CALIBRATED"
SUFFIX_CHANNEL_DATA_MIN = "-DATA-MIN"
SUFFIX_CHANNEL_DATA_MAX = "-DATA-MAX"
SUFFIX_CHANNEL_BG_DATA_MIN = "-BG-DATA-MIN"
SUFFIX_CHANNEL_BG_DATA_MAX = "-BG-DATA-MAX"

SUFFIX_DEVICE_INTENSITY = "INTENSITY-CAL"
SUFFIX_DEVICE_XPOS = "XPOS"
SUFFIX_DEVICE_YPOS = "YPOS"


# Gain setting is epics enum (DBF_ENUM). Only the integer value of the enum is passed on in the stream.
# The same gain setting can be achieved with different gain configurations, this is why some gains
# are listed twice. Faktor C1 from the table is used: Vin = Vcalib * C1

VOLTAGE_GAIN_MAPPING_PDIM = {
    0: 2.8481E-01,   # 0 -18 dB
    1: 1.4275E-01,   # 1 -12 dB
    2: 7.1542E-02,   # 2 -6 dB
    3: 3.5856E-02,   # 3 0 dB
    4: 2.8481E-02,   # 4 +2 dB
    5: 1.4275E-02,   # 5 +8 dB
    6: 7.1542E-03,   # 6 +14 dB
    7: 3.5856E-03,   # 7 +20 dB
    8: 2.8481E-03,   # 8 +22 dB
    9: 1.4275E-03,   # 9 +28 dB
    10: 7.1542E-04,  # 10 +34 dB
    11: 3.5856E-04,  # 11 +40 dB
    12: 7.1542E-02,  # 12 +2 dB
    13: 1.4275E-02,  # 13 +8 dB
    14: 7.1542E-03,  # 14 +14 dB
    15: 3.5856E-03   # 15 +20 dB
}


def calibrate_channel(message, data_to_send, pv_prefix, channel_number, pv_names, calibration_data,
                      gain_mapping=VOLTAGE_GAIN_MAPPING_PDIM):

    # Read from bsread message.
    data = message.data.data[pv_names[config.CONFIG_CHANNEL_ORDER_DATA]].value
    background = message.data.data[pv_names[config.CONFIG_CHANNEL_ORDER_BG_DATA]].value
    data_trigger_cell = message.data.data[pv_names[config.CONFIG_CHANNEL_ORDER_DATA_TRIG]].value
    background_trigger_cell = message.data.data[pv_names[config.CONFIG_CHANNEL_ORDER_BG_DATA_TRIG]].value
    gain_setting = message.data.data[pv_names[config.CONFIG_CHANNEL_ORDER_WD_GAIN]].value

    # Offset and scale
    background = (background.astype(numpy.float32) - 2048) / 4096
    data = (data.astype(numpy.float32) - 2048) / 4096

    # Calibrate
    background = calibration_data.calibrate(background, background_trigger_cell, channel_number)
    data = calibration_data.calibrate(data, data_trigger_cell, channel_number)

    # reverse gain
    background *= gain_mapping[gain_setting]
    data *= gain_mapping[gain_setting]

    # background subtraction
    data -= background

    # integration
    data_sum = data.sum()
    background_sum = background.sum()

    # min max
    [min, max] = find_minmax(data)
    [bg_min, bg_max] = find_minmax(background)

    data_to_send[pv_prefix + SUFFIX_CHANNEL_DATA_SUM] = data_sum
    data_to_send[pv_prefix + SUFFIX_CHANNEL_BG_DATA_SUM] = background_sum
    data_to_send[pv_prefix + SUFFIX_CHANNEL_DATA_CALIBRATED] = data
    data_to_send[pv_prefix + SUFFIX_CHANNEL_BG_DATA_CALIBRATED] = background
    data_to_send[pv_prefix + SUFFIX_CHANNEL_DATA_MIN] = min
    data_to_send[pv_prefix + SUFFIX_CHANNEL_DATA_MAX] = max
    data_to_send[pv_prefix + SUFFIX_CHANNEL_BG_DATA_MIN] = bg_min
    data_to_send[pv_prefix + SUFFIX_CHANNEL_BG_DATA_MAX] = bg_max

    return data_to_send


def calculate_intensity_and_position(message, data_to_send, channel_names, device_name, device_definition,
                                     intensity_scaling_factor=1):

    x_scaling_offset = device_definition["x_scaling_offset"]
    y_scaling_offset = device_definition["y_scaling_offset"]
    x_scaling_factor = device_definition["x_scaling_factor"]
    y_scaling_factor = device_definition["y_scaling_factor"]

    # intensity and position calculations
    channel1_sum = data_to_send[channel_names[0] + SUFFIX_CHANNEL_DATA_SUM]
    channel2_sum = data_to_send[channel_names[1] + SUFFIX_CHANNEL_DATA_SUM]
    channel3_sum = data_to_send[channel_names[2] + SUFFIX_CHANNEL_DATA_SUM]
    channel4_sum = data_to_send[channel_names[3] + SUFFIX_CHANNEL_DATA_SUM]

    intensity = (channel1_sum + channel2_sum + channel3_sum + channel4_sum) * intensity_scaling_factor
    intensity = abs(intensity)

    x_position = ((channel1_sum - channel2_sum) / (channel1_sum + channel2_sum))
    y_position = ((channel3_sum - channel4_sum) / (channel3_sum + channel4_sum))

    # Scaling.
    x_position = (x_position * x_scaling_factor) + x_scaling_offset
    y_position = (y_position * y_scaling_factor) + y_scaling_offset

    data_to_send[device_name + SUFFIX_DEVICE_INTENSITY] = intensity
    data_to_send[device_name + SUFFIX_DEVICE_XPOS] = x_position
    data_to_send[device_name + SUFFIX_DEVICE_YPOS] = y_position
