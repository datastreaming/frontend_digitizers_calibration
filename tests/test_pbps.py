import unittest

# Patch the notify epics method. It needs to happen before 'import process_pbps'
from tests.utils import mock_notify_epics, generate_test_message, generate_test_channels_definition
import frontend_digitizers_calibration.utils
frontend_digitizers_calibration.utils.notify_epics = mock_notify_epics


from frontend_digitizers_calibration.devices.utils import SUFFIX_CHANNEL_DATA_SUM, SUFFIX_CHANNEL_BG_DATA_SUM, \
    SUFFIX_CHANNEL_DATA_CALIBRATED, SUFFIX_CHANNEL_BG_DATA_CALIBRATED, SUFFIX_DEVICE_INTENSITY, SUFFIX_DEVICE_XPOS, \
    SUFFIX_DEVICE_YPOS, SUFFIX_CHANNEL_DATA_MIN, SUFFIX_CHANNEL_DATA_MAX, SUFFIX_CHANNEL_BG_DATA_MIN, \
    SUFFIX_CHANNEL_BG_DATA_MAX

from frontend_digitizers_calibration.devices.pbps import process_pbps
from tests.utils import MockCalibrationData


class TestPbps(unittest.TestCase):
    def test_process_pbps(self):

        n_channels = 4

        message = generate_test_message(n_channels)
        channels_definition = generate_test_channels_definition(n_channels)

        device_name = "test_device-"

        device_definition = {"device_type": "pbpg",
                             "x_scaling_offset": 0,
                             "y_scaling_offset": 0,
                             "x_scaling_factor": 1,
                             "y_scaling_factor": 1}

        calibration_data = MockCalibrationData

        result = process_pbps(message, device_name, device_definition, channels_definition, calibration_data)

        expected_data = set()
        # Per channel data.
        for pv_prefix in [channel["pv_prefix"] for channel in channels_definition]:
            expected_data.add(pv_prefix + SUFFIX_CHANNEL_DATA_SUM)
            expected_data.add(pv_prefix + SUFFIX_CHANNEL_BG_DATA_SUM)
            expected_data.add(pv_prefix + SUFFIX_CHANNEL_DATA_CALIBRATED)
            expected_data.add(pv_prefix + SUFFIX_CHANNEL_BG_DATA_CALIBRATED)
            expected_data.add(pv_prefix + SUFFIX_CHANNEL_DATA_MIN)
            expected_data.add(pv_prefix + SUFFIX_CHANNEL_DATA_MAX)
            expected_data.add(pv_prefix + SUFFIX_CHANNEL_BG_DATA_MIN)
            expected_data.add(pv_prefix + SUFFIX_CHANNEL_BG_DATA_MAX)

        # Per device data.
        expected_data.add(device_name+SUFFIX_DEVICE_INTENSITY)
        expected_data.add(device_name+SUFFIX_DEVICE_XPOS)
        expected_data.add(device_name+SUFFIX_DEVICE_YPOS)

        self.assertSetEqual(expected_data, set(result.keys()))
