import os

from frontend_digitizers_calibration.calibration import VoltageCalibration
from tests.utils import generate_test_message


def main():
    try:
        from line_profiler import LineProfiler
    except ImportError:
        return

    n_measurements = 1000

    message = generate_test_message(1)
    data = message.data.data["channel1_prefix-DATA"].value

    current_folder = os.path.dirname(os.path.abspath(__file__))
    calibration_data = VoltageCalibration(current_folder + "/data/configs/wd135-5120.vcal")

    profiler = LineProfiler()
    calibrate_wrapper = profiler(calibration_data.calibrate)

    data = data.astype("float32")

    for _ in range(n_measurements):
        # Constants were taken out of the SAROP21-CVME-PBPS1 dump.
        calibrate_wrapper(data, 167, 12)

    profiler.print_stats()

if __name__ == "__main__":
    main()
