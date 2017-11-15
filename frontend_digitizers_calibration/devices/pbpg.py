from collections import deque

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.devices.utils import calibrate_channel, calculate_intensity_and_position, \
    SUFFIX_DEVICE_INTENSITY

pbpg_queue = deque(maxlen=240)

SUFFIX_DEVICE_INTENSITY_AVG = "-INTENSITY-AVG"
SUFFIX_DEVICE_INTENSITY_CAL = "-INTENSITY-CAL"


def process_pbpg(message, device_name, device_definition, channels_definition, calibration_data):

    data_to_send = {}

    for channel in channels_definition:
        pv_prefix = channel[config.CONFIG_CHANNEL_PV_PREFIX]
        channel_number = channel[config.CONFIG_CHANNEL_NUMBER]
        pv_names = channel[config.CONFIG_CHANNEL_PVS]

        calibrate_channel(message=message,
                          data_to_send=data_to_send,
                          pv_prefix=pv_prefix,
                          channel_number=channel_number,
                          pv_names=pv_names,
                          calibration_data=calibration_data)

    # Retrieve the channel names in the correct order.
    channel_names = [channel[config.CONFIG_CHANNEL_PV_PREFIX] for channel in channels_definition]

    calculate_intensity_and_position(message, data_to_send, channel_names, device_name, device_definition)

    # Retrieve intensity for more calculations.
    intensity = data_to_send[device_name + SUFFIX_DEVICE_INTENSITY]

    pbpg_queue.append(intensity)
    # average last 240 intensities
    intensity_average = sum(pbpg_queue) / len(pbpg_queue)
    data_to_send[device_name + SUFFIX_DEVICE_INTENSITY_AVG] = intensity_average

    keithley_intensity = message.data.data[device_definition[config.CONFIG_DEVICE_KEITHLEY_INTENSITY]].value
    intensity_cal = intensity * (keithley_intensity / intensity_average)
    data_to_send[device_name + SUFFIX_DEVICE_INTENSITY_CAL] = intensity_cal

    return data_to_send
