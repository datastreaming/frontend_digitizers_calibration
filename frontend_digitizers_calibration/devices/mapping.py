from frontend_digitizers_calibration.devices.pbpg import process_pbpg
from frontend_digitizers_calibration.devices.pbps import process_pbps
from frontend_digitizers_calibration.devices.single_channel import process_single_channel

device_type_processing_function_mapping = {
    "pbps": process_pbps,
    "pbpg": process_pbpg,
    "single_channel": process_single_channel
}
