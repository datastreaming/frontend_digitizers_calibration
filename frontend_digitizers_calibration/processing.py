# Data to be used for calibration.
import numpy

from frontend_digitizers_calibration import config



SUFFIX_DATA_SUM = "-DATA-SUM"
SUFFIX_DATA_CALIBRATED = "-DATA-CALIBRATED"
SUFFIX_BG_DATA_CALIBRATED = "-BG-DATA-CALIBRATED"

def process_pbps(message, devices, frequency_value_name, frequency_files):
    data_to_send = {}

    sampling_frequency = message.data.data[frequency_value_name].value

    calibration_data = load_calibration_data(sampling_frequency, frequency_files)

    for device_name, channels in devices.items():

        for channel_name, pv_names in channels.items():

            # Read from bsread message.
            data = message.data.data[pv_names[config.CONFIG_ORDER_CHANNEL_DATA]].value
            background = message.data.data[pv_names[config.CONFIG_ORDER_CHANNEL_BG_DATA]].value
            data_trigger_cell = message.data.data[pv_names[config.CONFIG_ORDER_CHANNEL_DATA_TRIG]].value
            background_trigger_cell = message.data.data[pv_names[config.CONFIG_ORDER_CHANNEL_BG_DATA_TRIG]].value

            # Offset and scale
            background = (background.astype(numpy.float32) - 0x800) / 4096
            data = (data.astype(numpy.float32) - 0x800) / 4096

            # Calibrate
            background = calibration_data.calibrate(background, background_trigger_cell, first_channel_number)
            data = calibration_data.calibrate(data, data_trigger_cell, first_channel_number)

            # background subtraction
            data -= background

            # integration
            data_sum = data.sum()

            data_to_send[device_name + SUFFIX_DATA_SUM] = data_sum
            data_to_send[device_name + SUFFIX_DATA_CALIBRATED] = data
            data_to_send[device_name + SUFFIX_BG_DATA_CALIBRATED] = background

    # intensity and position calculations
    data1_sum = data_to_send[channel_names[0] + SUFFIX_DATA_SUM]
    data2_sum = data_to_send[channel_names[1] + SUFFIX_DATA_SUM]
    data3_sum = data_to_send[channel_names[2] + SUFFIX_DATA_SUM]
    data4_sum = data_to_send[channel_names[3] + SUFFIX_DATA_SUM]

    intensity = (data1_sum + data2_sum + data3_sum + data4_sum) / 2
    intensity = abs(intensity)

    position1 = ((data1_sum - data2_sum) / (data1_sum + data2_sum))
    position2 = ((data3_sum - data4_sum) / (data3_sum + data4_sum))

    data_to_send[device_name + "INTENSITY-CAL"] = intensity
    data_to_send[device_name + "XPOS"] = position1
    data_to_send[device_name + "YPOS"] = position2

    notify_epics(data_to_send)

    return data_to_send
