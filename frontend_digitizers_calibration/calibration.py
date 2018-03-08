import os
import ctypes
import numpy as np
from frontend_digitizers_calibration import config
import logging

WD_N_CHANNELS = 18
WD_N_CELLS = 1024

_logger = logging.getLogger(__name__)

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

    def load_default(self, frequency_MHz):
        # just calculate time axis from the period of the sampling frequency
        dt_zero_pad_tile = np.full((WD_N_CHANNELS, WD_N_CELLS*2), 1 / (frequency_MHz*1e6), dtype='float32')
        self.time = np.cumsum(dt_zero_pad_tile, axis=1)
        self.unroll_calibration()

    def unroll_calibration(self, n_channels=WD_N_CHANNELS, max_offset=WD_N_CELLS):
        # will contain a list of nd arrays holding time axis in ns [channel][trigger_cell][sample]
        self.unrolled_time_ns=[]

        # For each channel.
        for channel_number in range(n_channels):
            channel_unrolled_time = []

            # For each offset.
            for trigger_cell in range(max_offset):
                channel_unrolled_time.append((self.time[channel_number][trigger_cell:trigger_cell+max_offset]
                                             - self.time[channel_number][trigger_cell])*1e9)

            self.unrolled_time_ns.append(channel_unrolled_time)

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

        # bulid integrated time vector t
        # variant 1 : iterations
        #   self.t = np.zeros([WD_N_CHANNELS, 2047], dtype='float32')
        #   for ch in range(WD_N_CHANNELS):
        #     for i in range(1,WD_N_CELLS*2-1):
        #        self.t[ch][i] = self.t[ch][i-1] + self.dt[ch][(i-1)%WD_N_CELLS]

        # variant 2 : with numpy functions instead of iterations:
        # make an copy of an array of dts (axis 1) and append it to the original one, remove last element
        dt_zero_pad_tile = np.tile(self.dt, 2)[:, :-1]
        # prepend an element of with 0 at the beginning of each array (axis 1)
        dt_zero_pad_tile = np.pad(dt_zero_pad_tile, [(0, 0), (1, 0)], mode='constant')
        # calculate running time with the cumulative sum along axis 1
        # time now contains time axis starting from cell 0
        self.time = np.cumsum(dt_zero_pad_tile, axis=1)

        self.unroll_calibration()

        return True

    def get_time_axis(self, trigger_cell, channel):
        return self.unrolled_time_ns[channel][trigger_cell]

    def dump(self):
        print("Timing Cal Version %-4s  CRC=0x%08x  Freq: %.0f  Temperature %.2f deg. C" % (
            self.version_id, self.crc, self.sampling_frequency, self.temperature))

        for ch in range(WD_N_CHANNELS):
            for cell in range(1024):
                print("ch %2d - cell %4d :  dt: %10.6f ns  period: %10.6f ns, t: %10.6f" % (
                    ch, cell, self.dt[ch][cell] * 1e9, self.period[ch][cell] * 1e9, self.t[ch][cell] * 1e9))

        for ch in range(WD_N_CHANNELS):
            print("ch %2d :  offset: %10.6f ns" % (ch, self.offset[ch] * 1e9))


class CalibrationManager(object):

    def __init__(self, ioc_host_config, config_folder):
        self.vcal = VoltageCalibration()
        self.tcal = TimeCalibration()
        self.vcal_found = False
        self.tcal_found = False

        self.vcal_files = CalibrationManager.load_frequency_mapping(ioc_host_config, config_folder,
                                                                    config.CONFIG_SECTION_FREQUENCY_MAPPING)
        self.tcal_files = CalibrationManager.load_frequency_mapping(ioc_host_config, config_folder,
                                                                    config.CONFIG_SECTION_TIME_FREQUENCY_MAPPING)

        self.last_sampling_frequency = 0

    def load_calibration_data(self, sampling_frequency):
        tcal_file_name = ""
        vcal_file_name = ""

        # Check if we already have this calibration file loaded.
        if sampling_frequency != self.last_sampling_frequency:

            if sampling_frequency not in self.vcal_files:
                _logger.debug("No calibration file found for frequency '%s'.", sampling_frequency)
                self.vcal_found = False
                if sampling_frequency != self.last_sampling_frequency:
                    _logger.info("No calibration file found for frequency '%s'.", sampling_frequency)
                self.last_sampling_frequency = sampling_frequency
            else:
                vcal_file_name = self.vcal_files[sampling_frequency]
                if not os.path.exists(vcal_file_name):
                    self.vcal_found = False
                    _logger.debug("The specified calibration file '%s' for frequency '%s' does not exist.",
                                  vcal_file_name, sampling_frequency)
                    if sampling_frequency != self.last_sampling_frequency:
                        _logger.info("The specified calibration file '%s' for frequency '%s' does not exist.",
                                     vcal_file_name, sampling_frequency)
                    self.last_sampling_frequency = sampling_frequency
                else:
                    self.vcal_found = True

            # time calibration

            if sampling_frequency not in self.tcal_files:
                self.tcal_found = False
                _logger.debug("No time calibration file found for frequency '%s'.", sampling_frequency)
                if sampling_frequency != self.last_sampling_frequency:
                    _logger.info("No time calibration file found for frequency '%s'.", sampling_frequency)

            else:
                tcal_file_name = self.tcal_files[sampling_frequency]
                if not os.path.exists(tcal_file_name):
                    self.tcal_found = False
                    _logger.debug("The specified time calibration file '%s' for frequency '%s' does not exist.",
                                  tcal_file_name, sampling_frequency)
                    if sampling_frequency != self.last_sampling_frequency:
                        _logger.info("The specified time calibration file '%s' for frequency '%s' does not exist.",
                                     tcal_file_name, sampling_frequency)
                else:
                    self.tcal_found = True

            if self.tcal_found:
                _logger.debug("Loading calibration file '%s'.", tcal_file_name)
                self.tcal.load(tcal_file_name)
            else:
                _logger.info("Loading default time axis for '%s'.", sampling_frequency)
                self.tcal.load_default(sampling_frequency)

            if self.vcal_found:
                _logger.debug("Loading calibration file '%s'.", vcal_file_name)
                self.vcal.load(vcal_file_name)

        self.last_sampling_frequency = sampling_frequency
        return self.vcal_found



    @staticmethod
    def load_frequency_mapping(ioc_host_config, config_folder, config_section):
        frequency_map = ioc_host_config[config_section]

        frequency_files = {}

        # Convert the frequency string and relative path to an int and absolute path.
        for frequency, relative_file_path in frequency_map.items():
            actual_frequency = int(frequency)
            abs_file_path = os.path.join(config_folder, relative_file_path)

            frequency_files[actual_frequency] = abs_file_path

        return frequency_files