from bsread import source
from collections import deque
import numpy
import time
import epics

from epics import caget, caput
from drs_vcal_tcal import tcal_class, vcal_class
calibration_data = vcal_class('comb006-2498.vcal')


# trigger_cell between 0 and 1023
# trigger_cell = 0
# channel = 15
channel1 = 15
channel2 = 14
channel3 = 13
channel4 = 12
queue = deque(maxlen=240)

with source(host='SARFE10-CVME-PHO6211', port=9999) as stream:
    while True:

        message = stream.receive()
# get data from stream
        data1 = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch15-DATA'].value
        background1 = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DATA'].value
        data1_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch15-DRS_TC'].value
        background1_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DRS_TC'].value

        data2 = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch14-DATA'].value
        background2 = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch14-BG-DATA'].value
        data2_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch14-DRS_TC'].value
        background2_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch14-BG-DRS_TC'].value

        data3 = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch13-DATA'].value
        background3 = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch13-BG-DATA'].value
        data3_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch13-DRS_TC'].value
        background3_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch13-BG-DRS_TC'].value

        data4 = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch12-DATA'].value
        background4 = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch12-BG-DATA'].value
        data4_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch12-DRS_TC'].value
        background4_trigger_cell = message.data.data['SARFE10-CVME-PHO6211:Lnk9Ch12-BG-DRS_TC'].value

        pulse_id = message.data.pulse_id

# offset and scaling
        background1 = (background1.astype(numpy.float32)-0x800)/4096
        data1 = (data1.astype(numpy.float32)-0x800)/4096

        background2 = (background2.astype(numpy.float32)-0x800)/4096
        data2 = (data2.astype(numpy.float32)-0x800)/4096

        background3 = (background3.astype(numpy.float32)-0x800)/4096
        data3 = (data3.astype(numpy.float32)-0x800)/4096

        background4 = (background4.astype(numpy.float32)-0x800)/4096
        data4 = (data4.astype(numpy.float32)-0x800)/4096

# calibration
        background1 = calibration_data.calibrate(background1, background1_trigger_cell, channel1)
        data1 = calibration_data.calibrate(data1, data1_trigger_cell, channel1)
        caput('SARFE10-CVME-PHO6211:Lnk9Ch15-DATA-CALIBRATED',data1)
        caput('SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DATA-CALIBRATED',background1)

        background2 = calibration_data.calibrate(background2, background2_trigger_cell, channel2)
        data2 = calibration_data.calibrate(data2, data2_trigger_cell, channel2)
        caput('SARFE10-CVME-PHO6211:Lnk9Ch14-DATA-CALIBRATED',data2)
        caput('SARFE10-CVME-PHO6211:Lnk9Ch14-BG-DATA-CALIBRATED',background2)

        background3 = calibration_data.calibrate(background3, background3_trigger_cell, channel3)
        data3 = calibration_data.calibrate(data3, data3_trigger_cell, channel3)
        caput('SARFE10-CVME-PHO6211:Lnk9Ch13-DATA-CALIBRATED',data3)
        caput('SARFE10-CVME-PHO6211:Lnk9Ch13-BG-DATA-CALIBRATED',background3)

        background4 = calibration_data.calibrate(background4, background4_trigger_cell, channel4)
        data4 = calibration_data.calibrate(data4, data4_trigger_cell, channel4)
        caput('SARFE10-CVME-PHO6211:Lnk9Ch12-DATA-CALIBRATED',data4)
        caput('SARFE10-CVME-PHO6211:Lnk9Ch12-BG-DATA-CALIBRATED',background4)

# background susbstracion
        data1 -= background1
        data2 -= background2
        data3 -= background3
        data4 -= background4

# integration
        data1 = data1.sum()
        caput('SARFE10-CVME-PHO6211:Lnk9Ch15-DATA-SUM',data1)
        data2 = data2.sum()
        caput('SARFE10-CVME-PHO6211:Lnk9Ch14-DATA-SUM',data1)
        data3 = data3.sum()
        caput('SARFE10-CVME-PHO6211:Lnk9Ch13-DATA-SUM',data1)
        data4 = data4.sum()
        caput('SARFE10-CVME-PHO6211:Lnk9Ch12-DATA-SUM',data1)

# intensity and position calculations
        intensity = (data1 + data2 + data3 + data4)/(-2)
#        position1 = ((data1 - data2)/(data1 + data2))
        position1 = ((((data1 - data2)/(data1 + data2))-(-0.2115))/-0.0291)-0.4
#        position2 = ((data3 - data4)/(data3 + data4))
        position2 = ((((data3 - data4)/(data3 + data4))-(-0.1632))/0.0161)+0.2

        caput('SARFE10-PBPG050:HAMP-XPOS', position1)
        caput('SARFE10-PBPG050:HAMP-YPOS', position2)

        caput('SARFE10-PBPG050:HAMP-INTENSITY', intensity)
        queue.append(intensity)
#        print(queue)
        intensity_average = sum(queue)/len(queue)
        caput('SARFE10-PBPG050:HAMP-INTENSITY-AVG',intensity_average)
#        print(intensity_sum)
#        print(intensity_sum)
        print(pulse_id)
