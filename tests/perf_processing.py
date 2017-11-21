import os

# Patch the notify epics method. It needs to happen before 'import process_pbps'

def mock_notify_epics(data):
    pass
import frontend_digitizers_calibration.utils
frontend_digitizers_calibration.utils.notify_epics = mock_notify_epics

from frontend_digitizers_calibration.devices.utils import calibrate_channel
from frontend_digitizers_calibration.calibration import VoltageCalibration
from frontend_digitizers_calibration.devices.pbps import process_pbps
from tests.utils import generate_test_message, generate_test_channels_definition


def main():
    try:
        from line_profiler import LineProfiler
    except ImportError:
        return

    n_channels = 4
    n_measurements = 1000
    current_folder = os.path.dirname(os.path.abspath(__file__))

    message = generate_test_message(n_channels)
    channels_definition = generate_test_channels_definition(n_channels)

    device_name = "test_device-"

    device_definition = {"x_scaling_offset": 0,
                         "y_scaling_offset": 0,
                         "x_scaling_factor": 1,
                         "y_scaling_factor": 1}

    calibration_data = VoltageCalibration(current_folder + "/data/configs/wd135-5120.vcal")

    profiler = LineProfiler()
    process_pbps_wrapper = profiler(process_pbps)
    profiler.add_function(calibrate_channel)

    for _ in range(n_measurements):
        process_pbps_wrapper(message, device_name, device_definition, channels_definition, calibration_data)

    profiler.print_stats()

if __name__ == "__main__":
    main()
