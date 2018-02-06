from collections import deque

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.devices.utils import calibrate_channel, calculate_intensity_and_position, \
    SUFFIX_DEVICE_INTENSITY
from frontend_digitizers_calibration.utils import notify_epics

SUFFIX_DEVICE_INTENSITY_AVG = "INTENSITY-AVG"
SUFFIX_DEVICE_INTENSITY_CAL = "INTENSITY-CAL"
SUFFIX_DEVICE_INTENSITY_PBPG = "INTENSITY"

pbpg_queue = deque(maxlen=240)

# Gain setting is epics enum (DBF_ENUM). Only the integer value of the enum is passed on in the stream.
# The same gain setting can be achieved with different gain configurations, this is why some gains
# are listed twice. Faktor C1 from the table is used: Vin = Vcalib * C1

VOLTAGE_GAIN_MAPPING_PBPG = {
    0: 2.8481E-01,     # 0 -18 dB
    1: 1.4275E-01,     # 1 -12 dB
    2: 7.1542E-02,     # 2 -6 dB
    3: 3.5856E-02,     # 3 0 dB
    4: 2.8481E-02,     # 4 +2 dB
    5: 1.4275E-02,     # 5 +8 dB
    6: 7.1542E-03,     # 6 +14 dB
    7: 3.5856E-03,     # 7 +20 dB
    8: 2.8481E-03,     # 8 +22 dB
    9: 1.4275E-03,     # 9 +28 dB
    10: 7.1542E-04,    # 10 +34 dB
    11: 3.5856E-04,    # 11 +40 dB
    12: 7.1542E-02,    # 12 +2 dB
    13: 1.4275E-02,    # 13 +8 dB
    14: 7.1542E-03,    # 14 +14 dB
    15: 3.5856E-03     # 15 +20 dB
}


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
                          calibration_data=calibration_data,
                          gain_mapping=VOLTAGE_GAIN_MAPPING_PBPG)

    # Retrieve the channel names in the correct order.
    channel_names = [channel[config.CONFIG_CHANNEL_PV_PREFIX] for channel in channels_definition]

    calculate_intensity_and_position(message, data_to_send, channel_names, device_name, device_definition)

    # Retrieve intensity for more calculations.
    intensity = data_to_send[device_name + SUFFIX_DEVICE_INTENSITY]
    data_to_send[device_name + SUFFIX_DEVICE_INTENSITY_PBPG] = intensity

    pbpg_queue.append(intensity)
    # average last 240 intensities
    intensity_average = sum(pbpg_queue) / len(pbpg_queue)
    data_to_send[device_name + SUFFIX_DEVICE_INTENSITY_AVG] = intensity_average

    keithley_intensity = message.data.data[device_definition[config.CONFIG_DEVICE_KEITHLEY_INTENSITY]].value
    intensity_cal = intensity * (keithley_intensity / intensity_average)
    data_to_send[device_name + SUFFIX_DEVICE_INTENSITY_CAL] = intensity_cal

    # Notify EPICS channels with the new calculated data.
    notify_epics(data_to_send)

    return data_to_send
