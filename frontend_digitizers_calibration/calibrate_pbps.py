import argparse
import logging
import numpy

from bsread import source
from bsread.sender import, sender
from epics import caget, caput
from frontend_digitizers_calibration.drs_vcal_tcal import vcal_class

_logger = logging.getLogger(__name__)



# trigger_cell between 0 and 1023
# trigger_cell = 0
# channel = 15
channel1 = 15
channel2 = 14
channel3 = 13
channel4 = 12

data1_channel_name = ':Lnk9Ch%d' % channel1
data2_channel_name = ':Lnk9Ch%d' % channel2
data3_channel_name = ':Lnk9Ch%d' % channel3
data4_channel_name = ':Lnk9Ch%d' % channel4


# queue = deque(maxlen=240)

# TODO: We might want to remove this.
def notify_epics(data_to_send):
    """
    Notify epics channels from the data.
    :param data_to_send: Dictionary with PV_name: Value to set the channels to.
    """
    for name, value in data_to_send.items():
        caput(name, value)


def process_messages(message, ioc_prefix, calibration_data):

        def get_channel_data(input_data, channel_name):

            data = input_data.data.data[channel_name + "-DATA"].value
            background = input_data.data.data[channel_name + '-BG-DATA'].value
            data_trigger_cell = input_data.data.data[channel_name + '-DRS_TC'].value
            background_trigger_cell = input_data.data.data[channel_name + '-BG-DRS_TC'].value

            return data, background, data_trigger_cell, background_trigger_cell

        # get data from stream
        data1, background1, data1_trigger_cell, background1_trigger_cell = \
            get_channel_data(message, ioc_prefix+data1_channel_name)

        data2, background2, data2_trigger_cell, background2_trigger_cell = \
            get_channel_data(message, ioc_prefix + data2_channel_name)

        data3, background3, data3_trigger_cell, background3_trigger_cell = \
            get_channel_data(message, ioc_prefix + data3_channel_name)

        data4, background4, data4_trigger_cell, background4_trigger_cell = \
            get_channel_data(message, ioc_prefix + data4_channel_name)

        def offset_and_scale(background, data):

            background = (background.astype(numpy.float32) - 0x800) / 4096
            data = (data.astype(numpy.float32) - 0x800) / 4096

            return background, data

        background1, data1 = offset_and_scale(background1, data1)
        background2, data2 = offset_and_scale(background2, data2)
        background3, data3 = offset_and_scale(background3, data3)
        background4, data4 = offset_and_scale(background4, data4)

        # calibration
        background1 = calibration_data.calibrate(background1, background1_trigger_cell, channel1)
        data1 = calibration_data.calibrate(data1, data1_trigger_cell, channel1)

        background2 = calibration_data.calibrate(background2, background2_trigger_cell, channel2)
        data2 = calibration_data.calibrate(data2, data2_trigger_cell, channel2)

        background3 = calibration_data.calibrate(background3, background3_trigger_cell, channel3)
        data3 = calibration_data.calibrate(data3, data3_trigger_cell, channel3)

        background4 = calibration_data.calibrate(background4, background4_trigger_cell, channel4)
        data4 = calibration_data.calibrate(data4, data4_trigger_cell, channel4)

        # background subtraction
        data1 -= background1
        data2 -= background2
        data3 -= background3
        data4 -= background4

        # integration
        data1_sum = data1.sum()
        data2_sum = data2.sum()
        data3_sum = data3.sum()
        data4_sum = data4.sum()

        data_to_send = {
            ioc_prefix + data1_channel_name + '-DATA-SUM': data1_sum,
            ioc_prefix + data1_channel_name + '-DATA-CALIBRATED': data1,
            ioc_prefix + data1_channel_name + '-BG-DATA-CALIBRATED': background1,

            ioc_prefix + data2_channel_name + '-DATA-SUM': data2_sum,
            ioc_prefix + data2_channel_name + '-DATA-CALIBRATED': data2,
            ioc_prefix + data2_channel_name + '-BG-DATA-CALIBRATED': background2,

            ioc_prefix + data3_channel_name + '-DATA-SUM': data3_sum,
            ioc_prefix + data3_channel_name + '-DATA-CALIBRATED': data3,
            ioc_prefix + data3_channel_name + '-BG-DATA-CALIBRATED': background3,

            ioc_prefix + data4_channel_name + '-DATA-SUM': data4_sum,
            ioc_prefix + data4_channel_name + '-DATA-CALIBRATED': data4,
            ioc_prefix + data4_channel_name + '-BG-DATA-CALIBRATED': background4,
        }

        notify_epics(data_to_send)

        # intensity and position calculations
        intensity = (data1_sum + data2_sum + data3_sum + data4_sum) / (2)
        position1 = ((data1_sum - data2_sum) / (data1_sum + data2_sum))
        position2 = ((data3_sum - data4_sum) / (data3_sum + data4_sum))

        data_to_send[ioc_prefix + ":intensity"] = intensity
        data_to_send[ioc_prefix + ":position1"] = position1
        data_to_send[ioc_prefix + ":position2"] = position2

        return data_to_send


def start_stream(ioc_host, calibration_file):
    try:
        _logger.info("Connecting to ioc %s.", ioc_host)

        calibration_data = vcal_class(calibration_file)
        with source(host=ioc_host, port=9999) as input_stream:
            with sender() as output_stream:
                while True:
                    message = input_stream.receive()

                    data = process_messages(message, ioc_host, calibration_data)

                    output_stream.send(timestamp=(message.data.global_timestamp, message.data.global_timestamp_offset),
                                       pulse_id=message.data.pulse_id,
                                       data=data)
    except KeyboardInterrupt:
        _logger.info("Terminating due to user request.")


def main():
    parser = argparse.ArgumentParser(description='Arturo will fill this out.')

    parser.add_argument("ioc_host", type=str, help="Host of the ioc to connect to.")
    parser.add_argument("calibration_file", type=str, help="Calibration file to use.")
    parser.add_argument("--log_level", default="DEBUG", choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")
    arguments = parser.parse_args()

    logging.basicConfig(level=arguments.log_level, format='[%(levelname)s] %(message)s')

    start_stream(ioc_host=arguments.ioc_host, calibration_file=arguments.calibration_file)


if __name__ == "__main__":
    main()
