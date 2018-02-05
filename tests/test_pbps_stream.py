import unittest
from threading import Thread
from time import sleep

import os

import numpy
from bsread import source, PULL, PUSH
from mflow.utils.replay import reply_folder
from multiprocessing import Process

# Patch the notify epics method. It needs to happen before 'import process_pbps'
from tests.utils import mock_notify_epics
import frontend_digitizers_calibration.utils
frontend_digitizers_calibration.utils.notify_epics = mock_notify_epics

from frontend_digitizers_calibration.stream import start_stream


class TestPbpsStream(unittest.TestCase):
    def setUp(self):
        current_folder = os.path.dirname(os.path.abspath(__file__))
        self.dump_folder = os.path.join(current_folder, "data/SAROP21-CVME-PBPS2_ioc_dump/")
        self.config_folder = os.path.join(current_folder, "data/configs/")

        self.stream_process = None

    def tearDown(self):
        if self.stream_process:
            self.stream_process.terminate()

    def reply_dump(self):

        def reply():
            reply_folder(bind_address="tcp://0.0.0.0:9999",
                         folder=self.dump_folder,
                         mode=PUSH)

        reply_thread = Thread(target=reply)

        reply_thread.start()

        sleep(0.5)

    def test_pbpg_device(self):

        self.reply_dump()

        # Collect raw data from the dump.
        with source(host="0.0.0.0", mode=PULL) as input_stream:
            raw_message = input_stream.receive()
            raw_data = raw_message.data.data
            raw_global_timestamp = raw_message.data.global_timestamp
            raw_global_timestamp_offset = raw_message.data.global_timestamp_offset

        self.reply_dump()

        def process_stream():
            start_stream(config_folder=self.config_folder,
                         config_file="test_SAROP21-CVME-PBPS2.json",
                         input_stream_port=9999,
                         output_stream_port=10000)

        self.stream_process = Process(target=process_stream)
        self.stream_process.start()

        # Collect calculated data from the dump.
        with source(host="0.0.0.0", port=10000, mode=PULL) as input_stream:
            calculated_message = input_stream.receive()
            calculated_data = calculated_message.data.data
            calculated_global_timestamp = calculated_message.data.global_timestamp
            calculated_global_timestamp_offset = calculated_message.data.global_timestamp_offset

        # Check if the message timestamps are the same.
        self.assertEqual(raw_global_timestamp, calculated_global_timestamp)
        self.assertEqual(raw_global_timestamp_offset, calculated_global_timestamp_offset)

        # Verify if all the input data is also in the output, and that the data is equal.
        for key_name in raw_data.keys():
            raw_value = raw_data[key_name].value
            calculated_value = calculated_data[key_name].value
            received_channel_timestamp = calculated_data[key_name].timestamp
            received_channel_timestamp_offset = calculated_data[key_name].timestamp_offset

            # The message timestamp is propagated as the channel timestamp for all channels.
            self.assertEqual(received_channel_timestamp, raw_global_timestamp)
            self.assertEqual(received_channel_timestamp_offset, raw_global_timestamp_offset)

            # Use numpy comparison for ndarray types.
            if isinstance(raw_value, numpy.ndarray):
                numpy.testing.assert_array_equal(raw_value, calculated_value)

            else:
                self.assertEqual(raw_value, calculated_value)




