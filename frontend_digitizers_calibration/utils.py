import json
import logging
import os

from epics import caput

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.calibration import *

_logger = logging.getLogger(__name__)


def load_ioc_host_config(config_folder, config_file_name):

    config_file_path = os.path.join(config_folder, config_file_name)

    if not os.path.exists(config_file_path):
        _logger.error("Configuration file '%s' does not exist.", config_file_path)
        exit()

    with open(config_file_path, 'r') as config_file:
        configuration = json.load(config_file)
        _logger.info("Configuration file '%s' loaded.", config_file_path)

    if len(configuration.keys()) > 1:
        _logger.error("Only one ioc_host per configuration file permitted, but '%s' were found in '%s'.",
                      configuration.keys(), config_file_path)
        exit()

    ioc_host = list(configuration.keys())[0]

    return ioc_host, configuration[ioc_host]


def load_frequency_mapping(ioc_host_config, config_folder):

    frequency_map = ioc_host_config[config.CONFIG_SECTION_FREQUENCY_MAPPING]

    frequency_files = {}

    # Convert the frequency string and relative path to an int and absolute path.
    for frequency, relative_file_path in frequency_map.items():
        actual_frequency = int(frequency)
        abs_file_path = os.path.join(config_folder, relative_file_path)

        frequency_files[actual_frequency] = abs_file_path

    return frequency_files


def load_time_calib_freq_mapping(ioc_host_config, config_folder):

    frequency_map = ioc_host_config[config.CONFIG_SECTION_TIME_FREQUENCY_MAPPING]

    frequency_files = {}

    # Convert the frequency string and relative path to an int and absolute path.
    for frequency, relative_file_path in frequency_map.items():
        actual_frequency = int(frequency)
        abs_file_path = os.path.join(config_folder, relative_file_path)

        frequency_files[actual_frequency] = abs_file_path

    return frequency_files

def load_calibration_data(sampling_frequency, frequency_files, time_calib_freq_files):

    if sampling_frequency not in frequency_files:
        _logger.debug("No calibration file found for frequency '%s'.", sampling_frequency)
        if sampling_frequency != load_calibration_data.last_sampling_frequency:
            _logger.info("No calibration file found for frequency '%s'.", sampling_frequency)
        load_calibration_data.last_sampling_frequency = sampling_frequency
        return None

    calibration_file_name = frequency_files[sampling_frequency]
    if not os.path.exists(calibration_file_name):
        _logger.debug("The specified calibration file '%s' for frequency '%s' does not exist.",
                      calibration_file_name, sampling_frequency)
        if sampling_frequency != load_calibration_data.last_sampling_frequency:
            _logger.info("The specified calibration file '%s' for frequency '%s' does not exist.",
                         calibration_file_name, sampling_frequency)
        load_calibration_data.last_sampling_frequency = sampling_frequency
        return None

    # time calibration

    if sampling_frequency not in time_calib_freq_files:
        _logger.debug("No time calibration file found for frequency '%s'.", sampling_frequency)
        if sampling_frequency != load_calibration_data.last_sampling_frequency:
            _logger.info("No time calibration file found for frequency '%s'.", sampling_frequency)
        # todo load default

    time_calibration_file_name = time_calib_freq_files[sampling_frequency]
    if not os.path.exists(calibration_file_name):
        _logger.debug("The specified time calibration file '%s' for frequency '%s' does not exist.",
                      calibration_file_name, sampling_frequency)
        if sampling_frequency != load_calibration_data.last_sampling_frequency:
            _logger.info("The specified time calibration file '%s' for frequency '%s' does not exist.",
                         calibration_file_name, sampling_frequency)
        # todo load default

    # Check if we already have this calibration file loaded.
    if calibration_file_name == load_calibration_data.last_loaded_file_name:
        return load_calibration_data.last_loaded_calibration

    _logger.debug("Loading calibration file '%s'.", calibration_file_name)
    _logger.debug("Loading calibration file '%s'.", time_calibration_file_name)
    calibration_data = (VoltageCalibration(calibration_file_name), TimeCalibration(time_calibration_file_name))

    load_calibration_data.last_loaded_file_name = calibration_file_name
    load_calibration_data.last_loaded_calibration = calibration_data
    load_calibration_data.last_sampling_frequency = sampling_frequency

    return calibration_data


# Store info about last loaded calibration file.
load_calibration_data.last_loaded_file_name = None
load_calibration_data.last_loaded_calibration = None
load_calibration_data.last_sampling_frequency = None


def notify_epics(data_to_send):
    """
    Notify epics channels from the data.
    :param data_to_send: Dictionary with PV_name: Value to set the channels to.
    """
    for name, value in data_to_send.items():
        _logger.debug("Setting epics channel '%s' to value '%s'.", name, value)
        caput(name, value, timeout=1)


def append_message_data(message, destination):
    """
    Append the data from the original bsread message to the destination dictionary.
    :param message: Original bsread message to parse.
    :param destination: Destination dictionary - where to copy the data to.
    :return:
    """
    for value_name, bsread_value in message.data.data.items():
        _logger.debug("Passing parameter '%s' with value '%s' to output stream.", value_name, bsread_value.value)
        destination[value_name] = bsread_value.value
