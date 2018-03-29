# Runner script default parameters.
DEFAULT_CONFIG_FOLDER = "/configuration"
DEFAULT_INPUT_STREAM_PORT = 9999
DEFAULT_OUTPUT_STREAM_PORT = 9999

# This should be enough for 10 seconds of processing - 1 second for each file change.
INPUT_STREAM_QUEUE_SIZE = 1000

# Configuration section names.
CONFIG_SECTION_FREQUENCY_MAPPING = "frequency_mapping"
CONFIG_SECTION_TIME_FREQUENCY_MAPPING = "time_calibration_frequency_mapping"
CONFIG_SECTION_FREQUENCY = "frequency"
CONFIG_SECTION_DEVICES = "devices"

# Device property names.
CONFIG_DEVICE_TYPE = "device_type"
CONFIG_DEVICE_CHANNELS = "channels"
CONFIG_DEVICE_X_SCALING_FACTOR = "x_scaling_factor"
CONFIG_DEVICE_X_SCALING_OFFSET = "x_scaling_offset"
CONFIG_DEVICE_Y_SCALING_FACTOR = "y_scaling_factor"
CONFIG_DEVICE_Y_SCALING_OFFSET = "y_scaling_offset"
CONFIG_DEVICE_KEITHLEY_INTENSITY = "keithley_intensity"

# Channel property names.
CONFIG_CHANNEL_PV_PREFIX = "pv_prefix"
CONFIG_CHANNEL_NUMBER = "channel_number"
CONFIG_CHANNEL_PVS = "channel_pvs"
