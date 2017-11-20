from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.devices.utils import calibrate_channel, SUFFIX_CHANNEL_DATA_SUM
from frontend_digitizers_calibration.utils import notify_epics


SUFFIX_DEVICE_SCALED_DATA_SUM = "SCALED-DATA-SUM"


def process_single_channel(message, device_name, device_definition, channels_definition, calibration_data):

    scaling_offset = device_definition["scaling_offset"]
    scaling_factor = device_definition["scaling_factor"]

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

    if not pv_prefix:
        raise ValueError("pv_prefix not available - are channels defined for device '%s'?" % device_name)

    # The data sum for the single channel should be scaled.
    data_sum = data_to_send[pv_prefix + SUFFIX_CHANNEL_DATA_SUM]
    scaled_data_sum = (data_sum * scaling_factor) + scaling_offset
    data_to_send[device_name + SUFFIX_DEVICE_SCALED_DATA_SUM] = scaled_data_sum

    # Notify EPICS channels with the new calculated data.
    notify_epics(data_to_send)

    return data_to_send
