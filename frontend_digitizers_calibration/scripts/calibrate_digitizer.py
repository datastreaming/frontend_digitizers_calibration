import argparse
import logging

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.stream import start_stream

_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Arturo will fill this out.')

    parser.add_argument("config_file_name", type=str, help="Host of the ioc to connect to.")
    parser.add_argument("--input_stream_port", type=int, default=config.DEFAULT_INPUT_STREAM_PORT,
                        help="Port to run the output stream on.")
    parser.add_argument("--output_stream_port", type=int, default=config.DEFAULT_OUTPUT_STREAM_PORT,
                        help="Port to run the output stream on.")
    parser.add_argument("--config_folder", type=str, default=config.DEFAULT_CONFIG_FOLDER,
                        help="Folder where the configuration files are.")
    parser.add_argument("--log_level", default="INFO", choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")
    parser.add_argument("--non_blocking", action='count',
                        help="Send bsread stream in non blocking mode")
    arguments = parser.parse_args()

    logging.basicConfig(level=arguments.log_level, format='[%(levelname)s] %(message)s')

    start_stream(config_folder=arguments.config_folder,
                 config_file=arguments.config_file_name,
                 input_stream_port=arguments.input_stream_port,
                 output_stream_port=arguments.output_stream_port,
                 non_blocking=arguments.non_blocking)


if __name__ == "__main__":
    main()
