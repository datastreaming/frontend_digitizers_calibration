import os

import time

import sys

from frontend_digitizers_calibration.calibration import VoltageCalibration, WD_N_CHANNELS, WD_N_CELLS
from tests.utils import generate_test_message


def main():
    try:
        from line_profiler import LineProfiler
    except ImportError:
        return

    n_measurements = 1

    message = generate_test_message(WD_N_CHANNELS)
    data = message.data.data["channel1_prefix-DATA"].value

    current_folder = os.path.dirname(os.path.abspath(__file__))

    calibration_load_start = time.time()
    calibration_data = VoltageCalibration(current_folder + "/data/configs/wd135-5120.vcal")
    calibration_load_end = time.time()

    profiler = LineProfiler()
    calibrate_wrapper = profiler(calibration_data.calibrate)

    data = data.astype("float32")

    for _ in range(n_measurements):
        for channel_number in range(WD_N_CHANNELS):
            for offset_number in range(WD_N_CELLS):
                # Constants were taken out of the SAROP21-CVME-PBPS1 dump.
                calibrate_wrapper(data, offset_number, channel_number)

    profiler.print_stats()
    print("Time for loading the calibration (in seconds): ", calibration_load_end - calibration_load_start)

if __name__ == "__main__":
    main()
