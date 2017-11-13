from bsread import source
from bsread.sender import sender, PUB

from collections import deque
import numpy

from epics import caget, caput
from frontend_digitizers_calibration.drs_vcal_tcal import vcal_class


def process_message(message, channel_numbers, calibration_data, keithley_intensity, queue):

    data = []
    background = []

    data_to_send = {}

    for index, channel_number in enumerate(channel_numbers):
        channel_data = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch%d-DATA' % channel_number].value
        channel_background = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch%d-BG-DATA' % channel_number].value
        channel_data_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch%d-DRS_TC' % channel_number].value
        channel_background_trigger_cell = message.data.data[
            'SARFE10-CVME-PHO6211:Lnk9Ch%d-BG-DRS_TC' % channel_number].value

        # offset and scaling
        channel_data = (channel_data.astype(numpy.float32) - 0x800) / 4096
        channel_background = (channel_background.astype(numpy.float32) - 0x800) / 4096

        # calibration
        channel_data = calibration_data.calibrate(channel_data, channel_data_trigger_cell, channel_number)
        channel_background = calibration_data.calibrate(channel_background, channel_background_trigger_cell,
                                                        channel_number)

        data_to_send['SARFE10-CVME-PHO6211:Lnk9Ch%d-DATA-CALIBRATED' % channel_number] = channel_data
        data_to_send['SARFE10-CVME-PHO6211:Lnk9Ch%d-BG-DATA-CALIBRATED' % channel_number] = channel_background

        # background susbstracion
        channel_data -= channel_background

        # integration
        channel_data = channel_data.sum()

        data_to_send['SARFE10-CVME-PHO6211:Lnk9Ch%d-DATA-SUM' % channel_number] = channel_data

        data.append(channel_data)
        background.append(channel_background)

    # intensity and position calculations
    intensity = (data[0] + data[1] + data[2] + data[3]) / (-2)
    position1 = ((((data[0] - data[1]) / (data[0] + data[1])) - (-0.2115)) / -0.0291) - 0.4
    position2 = ((((data[2] - data[3]) / (data[2] + data[3])) - (-0.1632)) / 0.0161) + 0.2

    data_to_send['SARFE10-PBPG050:HAMP-XPOS'] = position1
    data_to_send['SARFE10-PBPG050:HAMP-YPOS'] = position2
    data_to_send['SARFE10-PBPG050:HAMP-INTENSITY'] = intensity

    queue.append(intensity)
    # average last 240 intensities
    intensity_average = sum(queue) / len(queue)

    data_to_send['SARFE10-PBPG050:HAMP-INTENSITY-AVG'] = intensity_average

    intensity_cal = intensity * (keithley_intensity / intensity_average)
    data_to_send['SARFE10-PBPG050:HAMP-INTENSITY-CAL'] = intensity_cal

    return data_to_send


def main(update_epics=True):

    calibration_data = vcal_class('docker/cfg/comb006-5120.vcal')
    channel_numbers = [15, 14, 13, 12]
    queue = deque(maxlen=240)

    required_channels = []
    for n in channel_numbers:
        required_channels.append("SARFE10-CVME-PHO6211:Lnk9Ch%d-DATA" % n)
        required_channels.append("SARFE10-CVME-PHO6211:Lnk9Ch%d-BG-DATA" % n)
        required_channels.append("SARFE10-CVME-PHO6211:Lnk9Ch%d-DRS_TC" % n)
        required_channels.append("SARFE10-CVME-PHO6211:Lnk9Ch%d-BG-DRS_TC" % n)

    with source(channels=required_channels) as stream:
        with sender(mode=PUB) as output_stream:
            while True:

                # scaling
                intensity_ds = caget('SARFE10-PBPG050:PHOTON-ENERGY-PER-PULSE-DS')
                intensity_us = caget('SARFE10-PBPG050:PHOTON-ENERGY-PER-PULSE-US')
                keithley_intensity = (intensity_ds + intensity_us) / 2

                message = stream.receive()
                pulse_id = message.data.pulse_id

                data_to_send = process_message(message, channel_numbers, calibration_data, keithley_intensity, queue)

                # Push results to epics
                if update_epics:
                    for key, value in data_to_send.items():
                        caput(key, value)

                output_stream.send(timestamp=(message.data.global_timestamp, message.data.global_timestamp_offset),
                                   pulse_id=message.data.pulse_id,
                                   data=data_to_send)

                print(pulse_id)


if __name__ == '__main__':
    main()
