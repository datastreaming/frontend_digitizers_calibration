
from bsread import source
with source(channels=['YOUR_CHANNEL', 'YOUR_SECOND_CHANNEL']) as stream:
    while True:
        message = stream.receive()
        print(message.data.data['YOUR_CHANNEL'].value)
