import argparse
import logging

from frontend_digitizers_calibration import config
from frontend_digitizers_calibration.drs_vcal_tcal import vcal_class
from frontend_digitizers_calibration.processing import process_pbps
from frontend_digitizers_calibration.utils import start_stream

_logger = logging.getLogger(__name__)

# Template to generate PV name
IOC_PV_TEMPLATE = ':Lnk%dCh%d'

channel_suffixes = {"data": "-DATA",
                    "bg_data": '-BG-DATA',
                    "data_trigger": '-DRS_TC',
                    "bg_data_trigger": '-BG-DRS_TC'}


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
    arguments = parser.parse_args()

    logging.basicConfig(level=arguments.log_level, format='[%(levelname)s] %(message)s')

    start_stream(config_folder=arguments.config_folder,
                 config_file=arguments.config_file_name,
                 input_stream_port=config.input_stream_port,
                 output_stream_port=config.output_stream_port,
                 processing_function=process_pbps)

if __name__ == "__main__":
    main()
