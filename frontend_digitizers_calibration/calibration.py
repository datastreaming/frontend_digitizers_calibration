import os
import ctypes
import numpy as np

WD_N_CHANNELS = 18
WD_N_CELLS = 1024


class VoltageCalibration(object):
    """
    Voltage Calibration Class
    """

    class VoltageCalibrationBinaryData(ctypes.Structure):
        _fields_ = [
            ('version_id', ctypes.c_char * 4),
            ('crc', ctypes.c_int),
            ('sampling_frequency', ctypes.c_short),
            ('padding', ctypes.c_short),
            ('temperature', ctypes.c_float),
            ('wf_offset1', ctypes.c_float * 1024 * 18),
            ('wf_offset2', ctypes.c_float * 1024 * 18),
            ('wf_gain1', ctypes.c_float * 1024 * 18),
            ('wf_gain2', ctypes.c_float * 1024 * 18),
            ('drs_offset_range0', ctypes.c_float * 16),
            ('drs_offset_range1', ctypes.c_float * 16),
            ('drs_offset_range2', ctypes.c_float * 16),
            ('adc_offset_range0', ctypes.c_float * 16),
            ('adc_offset_range1', ctypes.c_float * 16),
            ('adc_offset_range2', ctypes.c_float * 16)
        ]

    def __init__(self, filename=None):
        if filename is None:
            self.valid = False
        else:
            self.valid = self.load(filename)

    def unroll_calibration(self, n_channels=WD_N_CHANNELS, max_offset=WD_N_CELLS):
        self.unrolled_wf_offset1 = []
        self.unrolled_wf_gain1 = []
        self.unrolled_wf_gain2 = []

        # For each channel.
        for channel_number in range(n_channels):
            channel_wf_offset1 = []
            channel_wf_gain1 = []
            channel_wf_gain2 = []

            # For each offset.
            for offset_number in range(max_offset):
                channel_wf_offset1.append(np.roll(self.wf_offset1[channel_number], -offset_number))
                channel_wf_gain1.append(np.roll(self.wf_gain1[channel_number], -offset_number))
                channel_wf_gain2.append(np.roll(self.wf_gain2[channel_number], -offset_number))

            self.unrolled_wf_offset1.append(channel_wf_offset1)
            self.unrolled_wf_gain1.append(channel_wf_gain1)
            self.unrolled_wf_gain2.append(channel_wf_gain2)

    def load(self, filename):
        # check file size
        if os.path.getsize(filename) != ctypes.sizeof(self.VoltageCalibrationBinaryData):
            print("Voltage Cal: %s has wrong file size!" % filename)
            return False

        cbd = self.VoltageCalibrationBinaryData()

        with open(filename, 'rb') as file:
            file.readinto(cbd)

        if cbd.version_id != b"CAL2":
            print("Voltage Cal: %s has wrong version!" % filename)
            return False

        self.version_id = str(cbd.version_id)
        self.crc = int(cbd.crc)
        self.sampling_frequency = float(cbd.sampling_frequency)
        self.temperature = float(cbd.temperature)
        self.wf_offset1 = np.ctypeslib.as_array(cbd.wf_offset1)
        self.wf_offset2 = np.ctypeslib.as_array(cbd.wf_offset2)
        self.wf_gain1 = np.ctypeslib.as_array(cbd.wf_gain1)
        self.wf_gain2 = np.ctypeslib.as_array(cbd.wf_gain2)
        self.drs_offset_range0 = np.ctypeslib.as_array(cbd.drs_offset_range0)
        self.drs_offset_range1 = np.ctypeslib.as_array(cbd.drs_offset_range1)
        self.drs_offset_range2 = np.ctypeslib.as_array(cbd.drs_offset_range2)
        self.adc_offset_range0 = np.ctypeslib.as_array(cbd.adc_offset_range0)
        self.adc_offset_range1 = np.ctypeslib.as_array(cbd.adc_offset_range1)
        self.adc_offset_range2 = np.ctypeslib.as_array(cbd.adc_offset_range2)

        self.unroll_calibration()

        return True

    def dump(self):
        print("Voltage Cal Version %-4s  CRC=0x%08x  Freq: %4d  Temperature %.2f deg. C" % (
            self.version_id, self.crc, self.sampling_frequency, self.temperature))

        for ch in range(WD_N_CHANNELS):
            for cell in range(1024):
                print("ch %2d - cell %4d :  offset1: %10.6f   offset2: %10.6f   gain1: %10.6f   gain2: %10.6f" % (
                    ch, cell, self.wf_offset1[ch][cell], self.wf_offset2[ch][cell], self.wf_gain1[ch][cell],
                    self.wf_gain2[ch][cell]))

        for ch in range(WD_N_CHANNELS - 2):
            print("ch %2d :  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f" % (
                ch, self.drs_offset_range0[ch], self.drs_offset_range1[ch], self.drs_offset_range2[ch],
                self.adc_offset_range0[ch], self.adc_offset_range1[ch], self.adc_offset_range2[ch]))

    def calibrate(self, data, trigger_cell, channel):

        # cell-by-cell offset calibration
        data -= self.unrolled_wf_offset1[channel][trigger_cell]

        # start-to-end offset calibration
        data -= self.wf_offset2[channel]

        # gain calibration
        msk_gtz = data > 0  # create boolean mask vector for selection

        gain_correction = np.copy(self.unrolled_wf_gain2[channel][trigger_cell])
        gain_correction[msk_gtz] = self.unrolled_wf_gain1[channel][trigger_cell][msk_gtz]
        data /= gain_correction

        return data


class TimeCalibration(object):
    """
    Timing Calibration Class
    """

    class TimeCalibrationBinaryData(ctypes.Structure):
        _fields_ = [
            ('version_id', ctypes.c_char * 4),
            ('crc', ctypes.c_int),
            ('sampling_frequency', ctypes.c_float),
            ('temperature', ctypes.c_float),
            ('dt', ctypes.c_float * 1024 * 18),
            ('period', ctypes.c_float * 1024 * 18),
            ('offset', ctypes.c_float * 18)
        ]

    def __init__(self, filename=None):
        if filename is None:
            self.valid = False
        else:
            self.valid = self.load(filename)

    def load(self, filename):
        # check file size
        if os.path.getsize(filename) != ctypes.sizeof(self.TimeCalibrationBinaryData):
            print("Timing Cal: %s has wrong file size!" % filename)
            return False

        cbd = self.TimeCalibrationBinaryData()

        with open(filename, 'rb') as file:
            file.readinto(cbd)

        if cbd.version_id != b"CAL2":
            print("Timing Cal: %s has wrong version!" % filename)
            return False

        self.version_id = str(cbd.version_id)
        self.crc = int(cbd.crc)
        self.sampling_frequency = float(cbd.sampling_frequency)
        self.temperature = float(cbd.temperature)
        self.dt = np.ctypeslib.as_array(cbd.dt)
        self.period = np.ctypeslib.as_array(cbd.period)
        self.offset = np.ctypeslib.as_array(cbd.offset)

        # variant 2 : with numpy functions instead of iterations:
        dt_zero_pad_tile = np.pad(np.tile(self.dt, 2)[:, :-2], [(0, 0), (1, 0)], mode='constant')
        self.t = np.cumsum(dt_zero_pad_tile, axis=1)

        return True

    def dump(self):
        print("Timing Cal Version %-4s  CRC=0x%08x  Freq: %.0f  Temperature %.2f deg. C" % (
            self.version_id, self.crc, self.sampling_frequency, self.temperature))

        for ch in range(WD_N_CHANNELS):
            for cell in range(1024):
                print("ch %2d - cell %4d :  dt: %10.6f ns  period: %10.6f ns" % (
                    ch, cell, self.dt[ch][cell] * 1e9, self.period[ch][cell] * 1e9))

        for ch in range(WD_N_CHANNELS):
            print("ch %2d :  offset: %10.6f ns" % (ch, self.offset[ch] * 1e9))
