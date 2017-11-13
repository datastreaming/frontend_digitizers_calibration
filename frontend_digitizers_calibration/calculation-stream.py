
from bsread import source
import numpy
import time
import epics

from epics import caget, caput
from frontend_digitizers_calibration.drs_vcal_tcal import tcal_class, vcal_class
calibration_data = vcal_class('comb006-2498.vcal')
tcalibration_data =  tcal_class('comb006-2498.tcal')


# trigger_cell between 0 and 1023
# trigger_cell = 0
# channel = 15
channel = 15

with source(channels=['SARFE10-CVME-PHO6211:Lnk9Ch15-DATA', 'SARFE10-CVME-PHO6211:Lnk9Ch15-DRS_TC','SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DATA', 'SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DRS_TC']) as stream:
    while True:

        message = stream.receive()
        data = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch15-DATA'].value
        background = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DATA'].value
        data_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch15-DRS_TC'].value
        background_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DRS_TC'].value

        print (data)
        print (background)

        pulse_id = message.data.pulse_id

        background = background.astype(numpy.float32)
        data = data.astype(numpy.float32)

        background = calibration_data.calibrate(background, background_trigger_cell, channel)
        data = calibration_data.calibrate(data, data_trigger_cell, channel)

        data -= background

        data = data.sum()

        caput('SARFE10-PBPG050:HAMP-INTENSITY', data)

        print (data, pulse_id)
