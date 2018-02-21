import logging

from bsread import source
from bsread.sender import sender

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.devices.mapping import device_type_processing_function_mapping
from frontend_digitizers_calibration.utils import load_ioc_host_config, load_frequency_mapping, append_message_data, \
    load_calibration_data

_logger = logging.getLogger(__name__)


def process_message(message, devices, frequency_value_name, frequency_files):
    sampling_frequency = message.data.data[frequency_value_name].value
    calibration_data = load_calibration_data(sampling_frequency, frequency_files)

    if calibration_data is None:
        return None

    _logger.debug("Sampling frequency '%s'.", sampling_frequency)

    data_to_send = {}

    for device_name, device_definition in devices.items():
        device_type = device_definition[config.CONFIG_DEVICE_TYPE]
        channels_definition = device_definition[config.CONFIG_DEVICE_CHANNELS]

        _logger.debug("Processing device_type '%s'.", device_type)

        processing_function = device_type_processing_function_mapping[device_type]

        processed_data = processing_function(message=message,
                                             device_name=device_name,
                                             device_definition=device_definition,
                                             channels_definition=channels_definition,
                                             calibration_data=calibration_data)

        data_to_send.update(processed_data)

    # Append the data from the original message.
    append_message_data(message, data_to_send)

    return data_to_send


def no_client_function():
        _logger.info("No clients connected")


def start_stream(config_folder, config_file, input_stream_port, output_stream_port, non_blocking=False):
    ioc_host, ioc_host_config = load_ioc_host_config(config_folder=config_folder, config_file_name=config_file)
    _logger.info("Configuration defines ioc_host '%s'.", ioc_host)

    frequency_files = load_frequency_mapping(ioc_host_config=ioc_host_config, config_folder=config_folder)
    _logger.info("Configuration defined frequency_files: %s", frequency_files)

    devices = ioc_host_config[config.CONFIG_SECTION_DEVICES]
    _logger.info("Configuration defined devices: %s", list(devices.keys()))

    frequency_value_name = ioc_host_config[config.CONFIG_SECTION_FREQUENCY]
    _logger.info("Configuration defines frequency value name '%s'.", frequency_value_name)

    try:
        with source(host=ioc_host, port=input_stream_port, queue_size=config.INPUT_STREAM_QUEUE_SIZE) as input_stream:
            with sender(port=output_stream_port, block=(not non_blocking)) as output_stream:
                while True:
                    message = input_stream.receive()

                    _logger.debug("Received message with pulse_id '%s'.", message.data.pulse_id)

                    data = process_message(message=message,
                                           devices=devices,
                                           frequency_value_name=frequency_value_name,
                                           frequency_files=frequency_files)
                    if data is None:
                        _logger.debug("Message with pulse_id '%s' processed.", message.data.pulse_id)
                        continue

                    _logger.debug("Message with pulse_id '%s' processed.", message.data.pulse_id)

                    output_stream.send(timestamp=(message.data.global_timestamp, message.data.global_timestamp_offset),
                                       pulse_id=message.data.pulse_id,
                                       data=data)

                    _logger.debug("Message with pulse_id '%s' sent out, if someone is listening", message.data.pulse_id)

    except KeyboardInterrupt:
        _logger.info("Terminating due to user request.")
