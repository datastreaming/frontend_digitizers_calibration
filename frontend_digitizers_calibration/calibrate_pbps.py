import argparse
import logging
import numpy

from bsread import source
from bsread.sender import sender, PUB
from epics import caget, caput
from frontend_digitizers_calibration.drs_vcal_tcal import vcal_class

_logger = logging.getLogger(__name__)

# Template to generate PV name
IOC_PV_TEMPLATE = ':Lnk%dCh%d'

channel_suffixes = {"data": "-DATA",
                    "bg_data": '-BG-DATA',
                    "data_trigger": '-DRS_TC',
                    "bg_data_trigger": '-BG-DRS_TC'}


# TODO: We might want to remove this.
def notify_epics(data_to_send):
    """
    Notify epics channels from the data.
    :param data_to_send: Dictionary with PV_name: Value to set the channels to.
    """
    for name, value in data_to_send.items():
        _logger.debug("Setting epics channel '%s' to value '%s'.", name, value)
        caput(name, value)


def process_messages(message, calibration_data, channel_names, device_name, first_channel_number):
    data_to_send = {}

    for channel_name in channel_names:
        # Read from bsread message.
        data = message.data.data[channel_name + channel_suffixes["data"]].value
        background = message.data.data[channel_name + channel_suffixes["bg_data"]].value
        data_trigger_cell = message.data.data[channel_name + channel_suffixes["data_trigger"]].value
        background_trigger_cell = message.data.data[channel_name + channel_suffixes["bg_data_trigger"]].value

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

        data_to_send[channel_name + '-DATA-SUM'] = data_sum
        data_to_send[channel_name + '-DATA-CALIBRATED'] = data
        data_to_send[channel_name + '-BG-DATA-CALIBRATED'] = background

    # intensity and position calculations
    data1_sum = data_to_send[channel_names[0] + '-DATA-SUM']
    data2_sum = data_to_send[channel_names[1] + '-DATA-SUM']
    data3_sum = data_to_send[channel_names[2] + '-DATA-SUM']
    data4_sum = data_to_send[channel_names[3] + '-DATA-SUM']

    intensity = (data1_sum + data2_sum + data3_sum + data4_sum) / (2)
    position1 = ((data1_sum - data2_sum) / (data1_sum + data2_sum))
    position2 = ((data3_sum - data4_sum) / (data3_sum + data4_sum))

    data_to_send[device_name + "INTENSITY-CAL"] = intensity
    data_to_send[device_name + "XPOS"] = position1
    data_to_send[device_name + "YPOS"] = position2

    notify_epics(data_to_send)

    return data_to_send


def start_stream(ioc_host, calibration_file, link_number, device_name, first_channel_number):

    _logger.info("Using device name '%s'.", device_name)

    # Channel numbers can start at a random integer, of course.
    channel_mapping = []
    for i in range(4):
        channel_mapping.append(first_channel_number-i)
    _logger.info("Using channel numbers '%s'.", channel_mapping)

    try:
        # Data to be used for calibration.
        _logger.info("Using calibration file '%s'.", calibration_file)
        calibration_data = vcal_class(calibration_file)

        # Channel prefixes to read from the dispatching layer.
        _logger.info("Generating PVs for ioc_host '%s'.", ioc_host)
        channel_names = []
        for channel_number in channel_mapping:
            channel_names.append(ioc_host + IOC_PV_TEMPLATE % (link_number, channel_number))

        dispatching_layer_request_channels = []
        for channel in channel_names:
            for suffix in channel_suffixes.values():
                dispatching_layer_request_channels.append(channel + suffix)
        _logger.info("Requesting channels from dispatching layer '%s'.", dispatching_layer_request_channels)

        with source(channels=dispatching_layer_request_channels) as input_stream:
            with sender(mode=PUB) as output_stream:
                while True:
                    message = input_stream.receive()
                    _logger.debug("Received message with pulse_id '%s'.", message.data.pulse_id)

                    data = process_messages(message=message,
                                            calibration_data=calibration_data,
                                            channel_names=channel_names,
                                            device_name=device_name,
                                            first_channel_number=first_channel_number)
                    _logger.debug("Message with pulse_id '%s' processed.", message.data.pulse_id)

                    output_stream.send(timestamp=(message.data.global_timestamp, message.data.global_timestamp_offset),
                                       pulse_id=message.data.pulse_id,
                                       data=data)
                    _logger.debug("Message with pulse_id '%s' sent out.", message.data.pulse_id)

    except KeyboardInterrupt:
        _logger.info("Terminating due to user request.")


def main():
    parser = argparse.ArgumentParser(description='Arturo will fill this out.')

    parser.add_argument("ioc_host", type=str, help="Host of the ioc to connect to.")
    parser.add_argument("calibration_file", type=str, help="Calibration file to use.")
    parser.add_argument("link_number", type=int, help="Number of the link to use.")
    parser.add_argument("first_channel_number", type=int, help="Number of the first channel to use.")
    parser.add_argument("device_name", type=str, help="Name of the device - ask Arturo.")
    parser.add_argument("--log_level", default="INFO", choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")
    arguments = parser.parse_args()

    logging.basicConfig(level=arguments.log_level, format='[%(levelname)s] %(message)s')

    start_stream(ioc_host=arguments.ioc_host,
                 calibration_file=arguments.calibration_file,
                 link_number=arguments.link_number,
                 device_name=arguments.device_name,
                 first_channel_number=arguments.first_channel_number)


if __name__ == "__main__":
    main()
