import json
import logging
import os

from epics import PV, caput

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.calibration import *

_logger = logging.getLogger(__name__)
_PVs = {}


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


def pv_connection_callback(pvname, conn, **kws):
    """
    Notify about pv connection status
    :param pvname: PV_name
    :param conn: bool, connection status
    """
    if conn:
        _logger.info("PV '%s' is now connected", pvname)
    else:
        _logger.info("PV '%s' is disconnected", pvname)


def notify_epics(data_to_send):
    """
    Notify epics channels from the data.
    :param data_to_send: Dictionary with PV_name: Value to set the channels to.
    """
    for name, value in data_to_send.items():
        _logger.debug("Setting epics channel '%s' to value '%s'.", name, value)
        if name not in _PVs:
            _PVs[name] = PV(name, connection_callback=pv_connection_callback)

        _PVs[name].put(value)




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
