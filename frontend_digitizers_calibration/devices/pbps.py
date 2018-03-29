from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.devices.utils import calibrate_channel, \
    calculate_intensity_and_position
from frontend_digitizers_calibration.utils import notify_epics


def process_pbps(message, device_name, device_definition, channels_definition, calibration_data):

    data_to_send = {}

    for channel in channels_definition:
        pv_prefix = channel[config.CONFIG_CHANNEL_PV_PREFIX]
        channel_number = channel[config.CONFIG_CHANNEL_NUMBER]

        calibrate_channel(message=message,
                          data_to_send=data_to_send,
                          pv_prefix=pv_prefix,
                          channel_number=channel_number,
                          calibration_data=calibration_data)

    # Retrieve the channel names in the correct order.
    channel_names = [channel[config.CONFIG_CHANNEL_PV_PREFIX] for channel in channels_definition]

    calculate_intensity_and_position(message, data_to_send, channel_names, device_name, device_definition)

    # Notify EPICS channels with the new calculated data.
    notify_epics(data_to_send)

    return data_to_send
