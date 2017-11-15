import logging

from bsread import source
from bsread.sender import sender

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.utils import load_ioc_host_config, load_frequency_mapping

_logger = logging.getLogger(__name__)


def start_stream(config_folder, config_file, input_stream_port, output_stream_port, processing_function):

    ioc_host, ioc_host_config = load_ioc_host_config(config_folder=config_folder, config_file_name=config_file)
    _logger.info("Configuration defines ioc_host '%s'.", ioc_host)

    frequency_files = load_frequency_mapping(ioc_host_config=ioc_host_config, config_folder=config_folder)
    _logger.info("Configuration defined frequency_files: %s", frequency_files)

    devices = ioc_host_config[config.CONFIG_SECTION_DEVICES]
    _logger.info("Configuration defined devices: %s", devices)

    frequency_value_name = ioc_host_config[config.CONFIG_SECTION_FREQUENCY]
    _logger.info("Configuration defines frequency value name '%s'.", frequency_value_name)

    try:
        with source(host=ioc_host, port=input_stream_port) as input_stream:
            with sender(port=output_stream_port) as output_stream:
                while True:
                    message = input_stream.receive()

                    _logger.debug("Received message with pulse_id '%s'.", message.data.pulse_id)

                    data = processing_function(message=message,
                                               devices=devices,
                                               frequency_value_name=frequency_value_name,
                                               frequency_files=frequency_files)

                    _logger.debug("Message with pulse_id '%s' processed.", message.data.pulse_id)

                    output_stream.send(timestamp=(message.data.global_timestamp, message.data.global_timestamp_offset),
                                       pulse_id=message.data.pulse_id,
                                       data=data)

                    _logger.debug("Message with pulse_id '%s' sent out.", message.data.pulse_id)

    except KeyboardInterrupt:
        _logger.info("Terminating due to user request.")
