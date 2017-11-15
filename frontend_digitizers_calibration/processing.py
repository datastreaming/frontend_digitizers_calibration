import numpy

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.utils import load_calibration_data, notify_epics, append_message_data

# Suffixes to use for appending calculated data.
SUFFIX_CHANNEL_DATA_SUM = "-DATA-SUM"
SUFFIX_CHANNEL_DATA_CALIBRATED = "-DATA-CALIBRATED"
SUFFIX_CHANNEL_BG_DATA_CALIBRATED = "-BG-DATA-CALIBRATED"
SUFFIX_DEVICE_INTENSITY = "INTENSITY-CAL"
SUFFIX_DEVICE_XPOS = "XPOS"
SUFFIX_DEVICE_YPOS = "YPOS"


def process_pbps(message, devices, frequency_value_name, frequency_files):
    data_to_send = {}

    sampling_frequency = message.data.data[frequency_value_name].value

    calibration_data = load_calibration_data(sampling_frequency, frequency_files)

    for device_name, channels_definition in devices.items():

        for channel in channels_definition:

            channel_name = channel[config.CONFIG_CHANNEL_NAME]
            channel_number = channel[config.CONFIG_CHANNEL_NUMBER]
            pv_names = channel[config.CONFIG_CHANNEL_PVS]

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

            data_to_send[channel_name + SUFFIX_CHANNEL_DATA_SUM] = data_sum
            data_to_send[channel_name + SUFFIX_CHANNEL_DATA_CALIBRATED] = data
            data_to_send[channel_name + SUFFIX_CHANNEL_BG_DATA_CALIBRATED] = background

        # Retrieve the channel names in the correct order.
        channel_names = [channel[config.CONFIG_CHANNEL_NAME] for channel in channels_definition]

        # intensity and position calculations
        channel1_sum = data_to_send[channel_names[0] + SUFFIX_CHANNEL_DATA_SUM]
        channel2_sum = data_to_send[channel_names[1] + SUFFIX_CHANNEL_DATA_SUM]
        channel3_sum = data_to_send[channel_names[2] + SUFFIX_CHANNEL_DATA_SUM]
        channel4_sum = data_to_send[channel_names[3] + SUFFIX_CHANNEL_DATA_SUM]

        intensity = (channel1_sum + channel2_sum + channel3_sum + channel4_sum) / 2
        intensity = abs(intensity)

        x_position = ((channel1_sum - channel2_sum) / (channel1_sum + channel2_sum))
        y_position = ((channel3_sum - channel4_sum) / (channel3_sum + channel4_sum))

        data_to_send[device_name + SUFFIX_DEVICE_INTENSITY] = intensity
        data_to_send[device_name + SUFFIX_DEVICE_XPOS] = x_position
        data_to_send[device_name + SUFFIX_DEVICE_YPOS] = y_position

    # Notify EPICS channels with the new calculated data.
    notify_epics(data_to_send)

    # Append the data from the original message.
    append_message_data(message, data_to_send)

    return data_to_send
