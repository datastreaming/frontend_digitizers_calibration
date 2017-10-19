
from bsread import source
import numpy


from drs_vcal_tcal import tcal_class, vcal_class
calibration_data = vcal_class('comb007-5120.vcal')


# trigger_cell between 0 and 1023
trigger_cell = 0
# channel = 15
channel = 15

with source(channels=['SARFE10-PBPG050:HAMP-014-x-h1-DATA', 'SARFE10-PBPG050:HAMP-014-x-h1-BG-DATA']) as stream:
    while True:
        message = stream.receive()
        data = message.data.data['SARFE10-PBPG050:HAMP-014-x-h1-DATA'].value
        background = message.data.data['SARFE10-PBPG050:HAMP-014-x-h1-BG-DATA'].value
        pulse_id = message.data.pulse_id

        data = data.astype(numpy.float32)

        data = calibration_data.calibrate(data, trigger_cell, channel)

        print(data)



